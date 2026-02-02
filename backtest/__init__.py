"""
Backtest Module for Quantitative Trading Platform
"""

from .engine import BacktestEngine, DataFeed, BaseBacktestStrategy
from .strategy_wrappers import (
    DualMAStrategyWrapper,
    MACDStrategyWrapper,
    RSIStrategy,
    BollingerBandsStrategy
)
from .analyzers import create_analyzers, PerformanceAnalyzer

__all__ = [
    'BacktestEngine',
    'DataFeed',
    'BaseBacktestStrategy',
    'DualMAStrategyWrapper',
    'MACDStrategyWrapper',
    'RSIStrategy',
    'BollingerBandsStrategy',
    'create_analyzers',
    'PerformanceAnalyzer'
]