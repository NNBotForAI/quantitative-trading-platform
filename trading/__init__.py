"""
Trading Execution Module for Quantitative Trading Platform
"""

from .order_management import (
    Order,
    OrderStatus,
    OrderType,
    OrderSide,
    Fill,
    OrderManager,
    ExecutionHandler
)
from .execution_algorithms import (
    ExecutionAlgorithm,
    ExecutionStrategy,
    TWAPStrategy,
    VWAPStrategy,
    ParticipateStrategy,
    MinSlippageStrategy,
    IcebergStrategy,
    ExecutionEngine,
    calculate_expected_slippage,
    estimate_transaction_cost
)

__all__ = [
    # Order Management
    'Order',
    'OrderStatus',
    'OrderType',
    'OrderSide',
    'Fill',
    'OrderManager',
    'ExecutionHandler',
    
    # Execution Algorithms
    'ExecutionAlgorithm',
    'ExecutionStrategy',
    'TWAPStrategy',
    'VWAPStrategy',
    'ParticipateStrategy',
    'MinSlippageStrategy',
    'IcebergStrategy',
    'ExecutionEngine',
    'calculate_expected_slippage',
    'estimate_transaction_cost'
]