"""
Execution Algorithms for Quantitative Trading Platform
Advanced order execution strategies to minimize market impact and slippage
Based on industry-standard execution algorithms
"""

from typing import Dict, List, Tuple, Optional
from enum import Enum
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .order_management import Order, OrderType, OrderSide


class ExecutionAlgorithm(Enum):
    """Execution algorithm types"""
    VWAP = "vwap"  # Volume Weighted Average Price
    TWAP = "twap"  # Time Weighted Average Price
    PARTICIPATE = "participate"  # Participate according to market volume
    MIN_SLIPPAGE = "min_slippage"  # Minimize slippage
    ICEBERG = "iceberg"  # Iceberge orders


class ExecutionStrategy:
    """
    Base class for execution strategies
    """
    
    def __init__(self, name: str):
        self.name = name
        self.parameters = {}
    
    def execute(self, order: Order, market_data: pd.DataFrame) -> List[Tuple[float, float]]:
        """
        Execute order using this strategy
        Returns list of (quantity, price) tuples for child orders
        """
        raise NotImplementedError(f"{self.name} execution not implemented")


class TWAPStrategy(ExecutionStrategy):
    """
    Time Weighted Average Price Strategy
    Splits large orders into smaller pieces over time
    """
    
    def __init__(self, time_window_minutes: int = 60, slice_interval_minutes: int = 5):
        super().__init__("TWAP")
        self.time_window_minutes = time_window_minutes
        self.slice_interval_minutes = slice_interval_minutes
        self.parameters = {
            'time_window': time_window_minutes,
            'slice_interval': slice_interval_minutes
        }
    
    def execute(self, order: Order, market_data: pd.DataFrame) -> List[Tuple[float, float]]:
        """
        Execute TWAP strategy
        """
        total_quantity = order.quantity
        time_slices = self.time_window_minutes // self.slice_interval_minutes
        slice_quantity = total_quantity / time_slices
        
        # Generate child orders evenly spaced in time
        child_orders = []
        
        for i in range(time_slices):
            # Get market price for this slice (simplified)
            if len(market_data) > i:
                # Use current market price with slight adjustment for realistic execution
                current_price = market_data.iloc[-(i+1)]['close']
                
                # Adjust price based on order side (bid/ask spread consideration)
                if order.side == OrderSide.BUY:
                    execution_price = current_price * 1.0005  # Slightly higher for buys
                else:
                    execution_price = current_price * 0.9995  # Slightly lower for sells
                
                child_orders.append((slice_quantity, execution_price))
            else:
                # If we run out of data, use the last known price
                if len(market_data) > 0:
                    last_price = market_data.iloc[-1]['close']
                    if order.side == OrderSide.BUY:
                        execution_price = last_price * 1.0005
                    else:
                        execution_price = last_price * 0.9995
                    child_orders.append((slice_quantity, execution_price))
        
        return child_orders


class VWAPStrategy(ExecutionStrategy):
    """
    Volume Weighted Average Price Strategy
    Splits orders according to expected volume distribution
    """
    
    def __init__(self, lookback_days: int = 30):
        super().__init__("VWAP")
        self.lookback_days = lookback_days
        self.parameters = {
            'lookback_days': lookback_days
        }
    
    def execute(self, order: Order, market_data: pd.DataFrame) -> List[Tuple[float, float]]:
        """
        Execute VWAP strategy
        """
        if len(market_data) == 0:
            return [(order.quantity, 0.0)]  # Cannot execute without data
        
        # Calculate VWAP from historical data
        df = market_data.copy()
        df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
        df['vwp'] = df['typical_price'] * df['volume']  # Volume-weighted price
        df['cum_vol'] = df['volume'].cumsum()
        df['cum_vwp'] = df['vwp'].cumsum()
        
        # Calculate VWAP
        vwap_values = df['cum_vwp'] / df['cum_vol']
        
        # Get the latest VWAP
        current_vwap = vwap_values.iloc[-1]
        
        # Calculate volume distribution for slicing
        total_volume = df['volume'].sum()
        if total_volume == 0:
            return [(order.quantity, current_vwap)]
        
        # Simple approach: execute based on average volume pattern
        # In practice, this would use intraday volume patterns
        time_slices = min(20, len(df))  # Limit slices for reasonable execution
        slice_quantity = order.quantity / time_slices
        
        child_orders = []
        for i in range(time_slices):
            # Use VWAP as target price with slight adjustment
            if i < len(vwap_values):
                target_price = vwap_values.iloc[i]
            else:
                target_price = current_vwap
            
            # Adjust for order side
            if order.side == OrderSide.BUY:
                execution_price = target_price * 1.0003  # Small premium for buys
            else:
                execution_price = target_price * 0.9997  # Small discount for sells
            
            child_orders.append((slice_quantity, execution_price))
        
        return child_orders


class ParticipateStrategy(ExecutionStrategy):
    """
    Participate strategy - follows market volume with fixed participation rate
    """
    
    def __init__(self, participation_rate: float = 0.10):  # 10% of market volume
        super().__init__("Participate")
        self.participation_rate = participation_rate
        self.parameters = {
            'participation_rate': participation_rate
        }
    
    def execute(self, order: Order, market_data: pd.DataFrame) -> List[Tuple[float, float]]:
        """
        Execute participate strategy
        """
        if len(market_data) == 0:
            return [(order.quantity, 0.0)]
        
        # Use recent volume data to determine execution size
        df = market_data.tail(20)  # Last 20 periods
        
        avg_volume = df['volume'].mean()
        if avg_volume == 0:
            return [(order.quantity, market_data.iloc[-1]['close'])]
        
        # Calculate how much of the average volume we want to participate in
        desired_participation = avg_volume * self.participation_rate
        
        # Split order into chunks that represent our participation rate
        remaining_quantity = order.quantity
        child_orders = []
        
        while remaining_quantity > 0:
            chunk_size = min(desired_participation, remaining_quantity)
            
            # Use current market price
            current_price = market_data.iloc[-1]['close']
            
            # Adjust for order side
            if order.side == OrderSide.BUY:
                execution_price = current_price * 1.0005
            else:
                execution_price = current_price * 0.9995
            
            child_orders.append((chunk_size, execution_price))
            remaining_quantity -= chunk_size
        
        return child_orders


class MinSlippageStrategy(ExecutionStrategy):
    """
    Minimize slippage strategy - adapts to market conditions
    """
    
    def __init__(self, volatility_lookback: int = 20):
        super().__init__("MinSlippage")
        self.volatility_lookback = volatility_lookback
        self.parameters = {
            'volatility_lookback': volatility_lookback
        }
    
    def execute(self, order: Order, market_data: pd.DataFrame) -> List[Tuple[float, float]]:
        """
        Execute min slippage strategy
        """
        if len(market_data) < self.volatility_lookback:
            # Not enough data, use simple execution
            price = market_data.iloc[-1]['close']
            if order.side == OrderSide.BUY:
                execution_price = price * 1.0005
            else:
                execution_price = price * 0.9995
            return [(order.quantity, execution_price)]
        
        # Calculate volatility
        df = market_data.tail(self.volatility_lookback)
        returns = np.log(df['close'] / df['close'].shift(1)).dropna()
        volatility = returns.std() * np.sqrt(252)  # Annualized volatility
        
        # Adjust execution based on volatility
        if volatility < 0.02:  # Low volatility - more aggressive
            time_slices = max(1, int(order.quantity / 1000))  # Larger chunks
        elif volatility < 0.05:  # Medium volatility - moderate
            time_slices = max(2, int(order.quantity / 500))
        else:  # High volatility - conservative
            time_slices = max(5, int(order.quantity / 100))
        
        slice_quantity = order.quantity / time_slices
        current_price = market_data.iloc[-1]['close']
        
        child_orders = []
        for i in range(time_slices):
            # Adjust price based on volatility and order side
            if order.side == OrderSide.BUY:
                if volatility > 0.05:  # High volatility, be more conservative
                    execution_price = current_price * (1 + 0.001)  # Higher premium
                else:
                    execution_price = current_price * (1 + 0.0003)  # Lower premium
            else:  # SELL
                if volatility > 0.05:  # High volatility, be more conservative
                    execution_price = current_price * (1 - 0.001)  # Higher discount
                else:
                    execution_price = current_price * (1 - 0.0003)  # Lower discount
            
            child_orders.append((slice_quantity, execution_price))
        
        return child_orders


class IcebergStrategy(ExecutionStrategy):
    """
    Iceberg strategy - show only part of the order
    """
    
    def __init__(self, display_size: float = 100.0, refresh_time_seconds: int = 30):
        super().__init__("Iceberg")
        self.display_size = display_size
        self.refresh_time_seconds = refresh_time_seconds
        self.parameters = {
            'display_size': display_size,
            'refresh_time': refresh_time_seconds
        }
    
    def execute(self, order: Order, market_data: pd.DataFrame) -> List[Tuple[float, float]]:
        """
        Execute iceberg strategy
        """
        total_quantity = order.quantity
        displayed_quantity = min(self.display_size, total_quantity)
        remaining_quantity = total_quantity - displayed_quantity
        
        current_price = market_data.iloc[-1]['close']
        
        child_orders = []
        
        # Place initial displayed quantity
        if order.side == OrderSide.BUY:
            execution_price = current_price * 1.0002  # Small premium for visibility
        else:
            execution_price = current_price * 0.9998  # Small discount for visibility
        
        child_orders.append((displayed_quantity, execution_price))
        
        # Additional hidden quantities (simplified implementation)
        hidden_chunks = max(1, int(remaining_quantity / self.display_size))
        for i in range(hidden_chunks):
            if remaining_quantity > 0:
                chunk_size = min(self.display_size, remaining_quantity)
                
                # Slightly worse price to avoid taking liquidity
                if order.side == OrderSide.BUY:
                    execution_price = current_price * 1.0003
                else:
                    execution_price = current_price * 0.9997
                
                child_orders.append((chunk_size, execution_price))
                remaining_quantity -= chunk_size
        
        return child_orders


class ExecutionEngine:
    """
    Execution Engine - Coordinates execution strategies and manages order flow
    """
    
    def __init__(self):
        self.strategies = {
            ExecutionAlgorithm.TWAP.value: TWAPStrategy(),
            ExecutionAlgorithm.VWAP.value: VWAPStrategy(),
            ExecutionAlgorithm.PARTICIPATE.value: ParticipateStrategy(),
            ExecutionAlgorithm.MIN_SLIPPAGE.value: MinSlippageStrategy(),
            ExecutionAlgorithm.ICEBERG.value: IcebergStrategy()
        }
        
        self.active_executions = {}
        self.execution_history = []
    
    def execute_order_with_strategy(
        self,
        order: Order,
        strategy_type: ExecutionAlgorithm,
        market_data: pd.DataFrame,
        **kwargs
    ) -> List[Order]:
        """
        Execute an order using specified strategy
        Returns list of child orders
        """
        strategy_name = strategy_type.value
        
        if strategy_name not in self.strategies:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        
        strategy = self.strategies[strategy_name]
        
        # Update strategy parameters if provided
        for param, value in kwargs.items():
            if hasattr(strategy, param):
                setattr(strategy, param, value)
        
        # Generate child orders
        child_orders_data = strategy.execute(order, market_data)
        
        # Create child orders
        child_orders = []
        for i, (quantity, price) in enumerate(child_orders_data):
            child_order = Order(
                id=f"{order.id}_CHILD_{i:03d}",
                symbol=order.symbol,
                side=order.side,
                order_type=OrderType.LIMIT if price > 0 else OrderType.MARKET,
                quantity=quantity,
                price=price if price > 0 else None,
                time_in_force="GTC"
            )
            
            child_orders.append(child_order)
        
        # Record execution
        execution_record = {
            'parent_order_id': order.id,
            'strategy': strategy_name,
            'timestamp': datetime.now().isoformat(),
            'child_orders_count': len(child_orders),
            'total_quantity': order.quantity,
            'strategy_params': strategy.parameters
        }
        
        self.execution_history.append(execution_record)
        
        print(f"✓ {strategy_name.upper()} 策略执行完成")
        print(f"  父订单: {order.id}")
        print(f"  子订单数: {len(child_orders)}")
        print(f"  总数量: {order.quantity}")
        
        return child_orders
    
    def get_strategy(self, strategy_type: ExecutionAlgorithm) -> ExecutionStrategy:
        """Get strategy instance"""
        return self.strategies.get(strategy_type.value)
    
    def get_execution_history(self) -> List[Dict]:
        """Get execution history"""
        return self.execution_history
    
    def get_active_executions(self) -> Dict:
        """Get active executions"""
        return self.active_executions
    
    def cancel_execution(self, parent_order_id: str) -> bool:
        """Cancel all child orders for a parent order"""
        # In a real system, this would cancel all related child orders
        # For now, we'll just mark the execution as cancelled
        for record in self.execution_history:
            if record['parent_order_id'] == parent_order_id:
                record['cancelled'] = True
                print(f"✓ 执行已取消: {parent_order_id}")
                return True
        
        print(f"✗ 找不到执行记录: {parent_order_id}")
        return False


# Utility functions for execution
def calculate_expected_slippage(
    order_size: float,
    market_volume: float,
    avg_spread: float = 0.001
) -> float:
    """
    Calculate expected slippage based on order size and market conditions
    """
    participation_ratio = order_size / market_volume
    
    # Simple model: slippage increases with participation ratio
    expected_slippage = avg_spread + (participation_ratio * 0.002)
    
    return expected_slippage


def estimate_transaction_cost(
    order: Order,
    market_data: pd.DataFrame,
    bid_ask_spread: float = 0.001
) -> Dict:
    """
    Estimate transaction costs for an order
    """
    if len(market_data) == 0:
        return {'expected_cost': 0, 'cost_percent': 0}
    
    current_price = market_data.iloc[-1]['close']
    
    # Calculate expected cost based on order type and market conditions
    if order.order_type == OrderType.MARKET:
        # Market orders typically pay the spread
        expected_cost_per_share = bid_ask_spread * current_price
    else:
        # Limit orders may get better prices but have opportunity cost
        expected_cost_per_share = bid_ask_spread * current_price * 0.5  # Better execution assumed
    
    expected_cost = expected_cost_per_share * order.quantity
    cost_percent = (expected_cost / (current_price * order.quantity)) * 100
    
    return {
        'expected_cost': expected_cost,
        'cost_percent': cost_percent,
        'current_price': current_price
    }