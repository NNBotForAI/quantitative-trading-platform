"""
Performance Analyzers for Backtest Engine
Based on Backtrader analyzers
"""

import backtrader as bt
from typing import Dict, List, Optional
import numpy as np


class PerformanceAnalyzer:
    """Performance analyzer for backtest results"""
    
    def __init__(self, cerebro, results):
        self.cerebro = cerebro
        self.results = results
        self.strat = results[0] if results and len(results) > 0 else None
        
    def get_sharpe_ratio(self) -> float:
        """Get Sharpe ratio"""
        if self.strat is None:
            return 0.0
        
        try:
            sharpe = self.strat.analyzers.sharperatio.get_analysis()
            return sharpe.get('sharperatio', 0.0)
        except:
            return 0.0
    
    def get_drawdown(self) -> Dict:
        """Get drawdown information"""
        if self.strat is None:
            return {}
        
        try:
            drawdown = self.strat.analyzers.drawdown.get_analysis()
            return {
                'max_drawdown': drawdown.get('max', {}).get('drawdown', 0.0),
                'max_drawdown_money': drawdown.get('max', {}).get('moneydown', 0.0)
            }
        except:
            return {}
    
    def get_returns(self) -> Dict:
        """Get return information"""
        if self.strat is None:
            return {}
        
        try:
            returns = self.strat.analyzers.returns.get_analysis()
            return {
                'rtot': returns.get('rtot', 0.0),  # Total return
                'ravg': returns.get('ravg', 0.0),  # Average return
                'rnorm': returns.get('rnorm', 0.0),  # Normalized return
                'rnorm100': returns.get('rnorm100', 0.0)  # Normalized annual return
            }
        except:
            return {}
    
    def get_trades(self) -> Dict:
        """Get trade information"""
        if self.strat is None:
            return {}
        
        try:
            trades = self.strat.analyzers.TradeAnalyzer.get_analysis()
            return {
                'total_trades': trades.get('total', {}).get('total', 0),
                'won_trades': trades.get('won', {}).get('total', 0),
                'lost_trades': trades.get('lost', {}).get('total', 0),
                'win_rate': self._calculate_win_rate(trades)
            }
        except:
            return {}
    
    def _calculate_win_rate(self, trades: Dict) -> float:
        """Calculate win rate"""
        won = trades.get('won', {}).get('total', 0)
        lost = trades.get('lost', {}).get('total', 0)
        total = won + lost
        
        if total == 0:
            return 0.0
        
        return (won / total) * 100
    
    def get_summary(self) -> Dict:
        """Get performance summary"""
        return {
            'sharpe_ratio': self.get_sharpe_ratio(),
            'drawdown': self.get_drawdown(),
            'returns': self.get_returns(),
            'trades': self.get_trades(),
            'final_value': self.cerebro.broker.getvalue(),
            'initial_value': self.cerebro.broker.startingcash,
            'total_return': self._calculate_total_return()
        }
    
    def _calculate_total_return(self) -> float:
        """Calculate total return"""
        initial = self.cerebro.broker.startingcash
        final = self.cerebro.broker.getvalue()
        
        if initial == 0:
            return 0.0
        
        return ((final - initial) / initial) * 100
    
    def print_summary(self):
        """Print performance summary"""
        summary = self.get_summary()
        
        print("\n" + "=" * 60)
        print("回测性能报告")
        print("=" * 60)
        
        print(f"\n初始资金: ${summary['initial_value']:,.2f}")
        print(f"最终资金: ${summary['final_value']:,.2f}")
        print(f"总收益率: {summary['total_return']:.2f}%")
        
        print("\n" + "-" * 60)
        print("风险指标")
        print("-" * 60)
        print(f"夏普比率: {summary['sharpe_ratio']:.2f}")
        print(f"最大回撤: {summary['drawdown'].get('max_drawdown', 0):.2f}%")
        print(f"最大回撤金额: ${summary['drawdown'].get('max_drawdown_money', 0):,.2f}")
        
        print("\n" + "-" * 60)
        print("收益率")
        print("-" * 60)
        returns = summary['returns']
        print(f"总收益率: {returns.get('rtot', 0):.4f}")
        print(f"平均收益率: {returns.get('ravg', 0):.6f}")
        print(f"年化收益率: {returns.get('rnorm100', 0):.2f}%")
        
        print("\n" + "-" * 60)
        print("交易统计")
        print("-" * 60)
        trades = summary['trades']
        print(f"总交易次数: {trades.get('total_trades', 0)}")
        print(f"盈利交易: {trades.get('won_trades', 0)}")
        print(f"亏损交易: {trades.get('lost_trades', 0)}")
        print(f"胜率: {trades.get('win_rate', 0):.2f}%")
        
        print("\n" + "=" * 60)


def create_analyzers(cerebro) -> List[bt.Analyzer]:
    """Create common analyzers"""
    analyzers = [
        bt.analyzers.SharpeRatio,
        bt.analyzers.DrawDown,
        bt.analyzers.Returns,
        bt.analyzers.TradeAnalyzer,
        bt.analyzers.SQN,  # System Quality Number
        bt.analyzers.Transactions
    ]
    
    for analyzer in analyzers:
        cerebro.addanalyzer(analyzer, _name=analyzer.__name__)
    
    return analyzers