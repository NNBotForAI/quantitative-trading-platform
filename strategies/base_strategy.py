"""
Base Strategy for Quantitative Trading Platform
Based on Backtrader SignalStrategy pattern
"""

from abc import ABC, abstractmethod
from data_interface_framework import MarketData, Order, Position, AssetType
from typing import Dict, List, Optional
from datetime import datetime


class BaseStrategy(ABC):
    """Base strategy class"""
    
    def __init__(self, name: str, parameters: Dict = None):
        self.name = name
        self.parameters = parameters or {}
        self.positions = {}
        self.trades = []
        self.equity_curve = []
        self.current_equity = 100000.0  # Initial capital
        
    @abstractmethod
    def generate_signals(self, data: List[MarketData]) -> Dict[str, str]:
        """Generate trading signals"""
        pass
    
    @abstractmethod
    def calculate_position_size(self, price: float, account_balance: float) -> float:
        """Calculate position size"""
        pass
    
    @abstractmethod
    def on_data(self, data: List[MarketData]):
        """Data update callback"""
        pass
    
    @abstractmethod
    def on_trade(self, trade_info: Dict):
        """Trade execution callback"""
        pass
    
    @abstractmethod
    def get_performance_metrics(self) -> Dict:
        """Get strategy performance metrics"""
        pass