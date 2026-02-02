"""
Backtest Engine for Quantitative Trading Platform
Based on Backtrader framework
"""

import backtrader as bt
from datetime import datetime
from typing import Dict, List, Optional, Type
import pandas as pd


class BacktestEngine:
    """Backtest engine based on Backtrader"""
    
    def __init__(self):
        self.cerebro = bt.Cerebro()
        self.results = None
        self.strategies = []
        self.analyzers = []
        
        # Default settings
        self.cerebro.broker.setcash(100000.0)  # Initial capital
        self.cerebro.broker.setcommission(commission=0.001)  # 0.1% commission
        
    def add_strategy(
        self,
        strategy_class: Type[bt.Strategy],
        **kwargs
    ):
        """Add strategy to backtest"""
        self.cerebro.addstrategy(strategy_class, **kwargs)
        self.strategies.append(strategy_class)
        
    def add_data(self, data):
        """Add data to backtest"""
        self.cerebro.adddata(data)
        
    def add_analyzer(self, analyzer_class: Type[bt.Analyzer], **kwargs):
        """Add analyzer to backtest"""
        self.cerebro.addanalyzer(analyzer_class, **kwargs)
        self.analyzers.append(analyzer_class)
        
    def set_cash(self, cash: float):
        """Set initial cash"""
        self.cerebro.broker.setcash(cash)
        
    def set_commission(self, commission: float):
        """Set commission rate"""
        self.cerebro.broker.setcommission(commission=commission)
        
    def run(self) -> Dict:
        """Run backtest"""
        print("\n" + "=" * 60)
        print("开始回测...")
        print("=" * 60)
        
        # Run backtest
        self.results = self.cerebro.run()
        
        print("\n" + "=" * 60)
        print("回测完成！")
        print("=" * 60)
        
        # Extract results
        return self._extract_results()
    
    def _extract_results(self) -> Dict:
        """Extract backtest results"""
        if not self.results or len(self.results) == 0:
            return {}
        
        strat = self.results[0]
        
        # Get final portfolio value
        final_value = self.cerebro.broker.getvalue()
        
        # Get analyzer results
        result_dict = {
            "final_value": final_value,
            "strategies": []
        }
        
        # Extract strategy results
        for strat in self.results:
            strat_dict = {
                "name": strat.__class__.__name__,
                "trades": len(strat._trades),
            }
            
            # Extract analyzer data
            if hasattr(strat, 'analyzers'):
                for analyzer_name, analyzer in strat.analyzers.getitems():
                    try:
                        strat_dict[analyzer_name] = analyzer.get_analysis()
                    except:
                        pass
            
            result_dict["strategies"].append(strat_dict)
        
        return result_dict
    
    def plot(self):
        """Plot backtest results"""
        if self.results:
            self.cerebro.plot()


class DataFeed(bt.feeds.PandasData):
    """Pandas data feed for Backtrader"""
    
    params = (
        ('datetime', None),
        ('open', -1),
        ('high', -1),
        ('low', -1),
        ('close', -1),
        ('volume', -1),
        ('openinterest', -1),
    )


class BaseBacktestStrategy(bt.Strategy):
    """Base strategy for backtesting"""
    
    params = (
        ('printlog', True),
    )
    
    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None
        
    def notify_order(self, order):
        """Order status notification"""
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm)
                )
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log(
                    'SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm)
                )
                self.bar_executed_len += 1
                
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
            
        self.order = None
        
    def notify_trade(self, trade):
        """Trade notification"""
        if not trade.isclosed:
            return
            
        self.log(
            'OPERATION PROFIT, GROSS %.2f, NET %.2f' %
            (trade.pnl, trade.pnlcomm)
        )
        
    def log(self, txt, dt=None):
        """Logging function"""
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))