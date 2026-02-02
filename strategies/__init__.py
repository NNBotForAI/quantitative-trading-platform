"""
Quantitative Trading Platform - Strategies Module
"""
from .base_strategy import BaseStrategy
from .specific_strategies import DualMACrossStrategy, MACDStrategy

__all__ = [
    'BaseStrategy',
    'DualMACrossStrategy',
    'MACDStrategy'
]