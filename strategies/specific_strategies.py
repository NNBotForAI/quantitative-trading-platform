"""
Specific Strategy Implementations for Quantitative Trading Platform
Based on GitHub backtrader examples
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from strategies.base_strategy import BaseStrategy
from indicators import calculate_sma, calculate_macd
from data_interface_framework import MarketData, AssetType
from typing import Dict, List


class DualMACrossStrategy(BaseStrategy):
    """Dual Moving Average Crossover Strategy (Based on Backtrader example)"""
    
    def __init__(self):
        super().__init__(
            name="Dual Moving Average Crossover",
            parameters={
                "short_period": 10,
                "long_period": 30,
                "risk_per_trade": 0.02
            }
        )
        
        self.short_ma_data = []
        self.long_ma_data = []
    
    def generate_signals(self, data: List[MarketData]) -> Dict[str, str]:
        """Generate trading signals"""
        if len(data) < 30:
            return {}
        
        # Calculate short-term MA
        short_prices = [d.close for d in data[-10:]]
        short_ma = sum(short_prices) / 10
        self.short_ma_data.append(short_ma)
        
        # Calculate long-term MA
        long_prices = [d.close for d in data[-30:]]
        long_ma = sum(long_prices) / 30
        self.long_ma_data.append(long_ma)
        
        signals = {}
        latest_data = data[-1]
        
        # Need at least 2 data points to compare
        if len(self.short_ma_data) < 2 or len(self.long_ma_data) < 2:
            return {}
        
        # Golden cross buy signal
        if self.short_ma_data[-2] < self.long_ma_data[-2]:
            signals["BTC-USDT"] = "buy"
            signals["signal"] = f"Golden cross buy (MA{self.parameters['short_period']}: {self.short_ma_data[-2]:,.2f} > MA{self.parameters['long_period']}: {self.long_ma_data[-2]:,.2f})"
        
        # Death cross sell signal
        elif self.short_ma_data[-2] > self.long_ma_data[-2]:
            signals["BTC-USDT"] = "sell"
            signals["signal"] = f"Death cross sell (MA{self.parameters['short_period']}: {self.short_ma_data[-2]:,.2f} < MA{self.parameters['long_period']}: {self.long_ma_data[-2]:,.2f})"
        
        return signals
    
    def calculate_position_size(self, price: float, account_balance: float) -> float:
        """Calculate position size - Fixed 2%"""
        return account_balance * self.parameters["risk_per_trade"]
    
    def on_data(self, data: List[MarketData]):
        """Data update callback"""
        pass
    
    def on_trade(self, trade_info: Dict):
        """Trade execution callback"""
        self.trades.append(trade_info)
    
    def get_performance_metrics(self) -> Dict:
        """Get strategy performance metrics"""
        if len(self.trades) == 0:
            return {
                "total_trades": 0,
                "win_rate": 0,
                "total_return": 0
            }
        
        # Calculate wins/losses
        wins = sum(1 for t in self.trades if t.get("profit", 0) > 0)
        total_trades = len(self.trades)
        win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0
        
        # Calculate total return
        total_return = ((self.current_equity - 100000.0) / 100000.0) * 100
        
        return {
            "total_trades": total_trades,
            "wins": wins,
            "win_rate": win_rate,
            "total_return": total_return
        }


class MACDStrategy(BaseStrategy):
    """MACD Golden Cross Strategy"""
    
    def __init__(self):
        super().__init__(
            name="MACD Strategy",
            parameters={
                "fast_period": 12,
                "slow_period": 26,
                "signal_period": 9,
                "risk_per_trade": 0.03
            }
        )
    
    def generate_signals(self, data: List[MarketData]) -> Dict[str, str]:
        """Generate MACD trading signals"""
        if len(data) < 27:
            return {}
        
        # Calculate MACD
        prices = [d.close for d in data[-26:]]
        macd_result = calculate_macd(prices, 12, 26, 9)
        
        signals = {}
        latest_data = data[-1]
        
        # MACD golden cross buy
        if macd_result["histogram"] > 0 and macd_result["macd"] > macd_result["signal"]:
            signals["BTC-USDT"] = "buy"
            signals["signal"] = "MACD golden cross buy"
        
        # MACD death cross sell
        elif macd_result["histogram"] < 0 and macd_result["macd"] < macd_result["signal"]:
            signals["BTC-USDT"] = "sell"
            signals["signal"] = "MACD death cross sell"
        
        return signals
    
    def calculate_position_size(self, price: float, account_balance: float) -> float:
        """Calculate position size - Fixed 3%"""
        return account_balance * self.parameters["risk_per_trade"]
    
    def on_data(self, data: List[MarketData]):
        """Data update callback"""
        pass
    
    def on_trade(self, trade_info: Dict):
        """Trade execution callback"""
        self.trades.append(trade_info)
    
    def get_performance_metrics(self) -> Dict:
        """Get strategy performance metrics"""
        if len(self.trades) == 0:
            return {
                "total_trades": 0,
                "win_rate": 0,
                "total_return": 0
            }
        
        # Calculate wins/losses
        wins = sum(1 for t in self.trades if t.get("profit", 0) > 0)
        total_trades = len(self.trades)
        win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0
        
        # Calculate total return
        total_return = ((self.current_equity - 100000.0) / 100000.0) * 100
        
        return {
            "total_trades": total_trades,
            "wins": wins,
            "win_rate": win_rate,
            "total_return": total_return
        }