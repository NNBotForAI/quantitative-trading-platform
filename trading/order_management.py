"""
Order Management System for Quantitative Trading Platform
Based on QuantConnect Order Management System
"""

from typing import Dict, List, Optional, Union
from enum import Enum
from datetime import datetime
from dataclasses import dataclass


class OrderStatus(Enum):
    """Order status enumeration"""
    NEW = "new"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    PENDING_CANCEL = "pending_cancel"
    PENDING_NEW = "pending_new"


class OrderType(Enum):
    """Order type enumeration"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class OrderSide(Enum):
    """Order side enumeration"""
    BUY = "buy"
    SELL = "sell"


@dataclass
class Order:
    """
    Order data structure
    """
    id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    filled_quantity: float = 0.0
    average_fill_price: float = 0.0
    status: OrderStatus = OrderStatus.PENDING_NEW
    timestamp: str = ""
    exchange_id: Optional[str] = None
    time_in_force: str = "GTC"  # Good Till Cancelled
    client_order_id: Optional[str] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    @property
    def unfilled_quantity(self) -> float:
        """Get unfilled quantity"""
        return self.quantity - self.filled_quantity
    
    @property
    def is_filled(self) -> bool:
        """Check if order is completely filled"""
        return self.status == OrderStatus.FILLED
    
    @property
    def is_active(self) -> bool:
        """Check if order is still active (not cancelled or filled)"""
        return self.status in [
            OrderStatus.NEW,
            OrderStatus.PARTIALLY_FILLED,
            OrderStatus.PENDING_NEW,
            OrderStatus.PENDING_CANCEL
        ]


class Fill:
    """
    Fill data structure
    """
    def __init__(
        self,
        order_id: str,
        symbol: str,
        side: OrderSide,
        quantity: float,
        fill_price: float,
        fill_time: str,
        fee: float = 0.0
    ):
        self.order_id = order_id
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.fill_price = fill_price
        self.fill_time = fill_time
        self.fee = fee
        self.total_value = fill_price * quantity


class OrderManager:
    """
    Order Management System - Central hub for order processing
    Based on QuantConnect OMS principles
    """
    
    def __init__(self):
        self.orders: Dict[str, Order] = {}
        self.fills: List[Fill] = []
        self.active_orders: Dict[str, Order] = {}
        self.order_counter = 0
        
        # Callbacks for order events
        self.on_order_status_change = []
        self.on_fill = []
        self.on_error = []
    
    def create_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: str = "GTC"
    ) -> Order:
        """
        Create a new order
        """
        self.order_counter += 1
        order_id = f"ORDER_{self.order_counter:06d}"
        
        order = Order(
            id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            time_in_force=time_in_force,
            client_order_id=f"CLIENT_{order_id}"
        )
        
        # Add to orders
        self.orders[order_id] = order
        self.active_orders[order_id] = order
        
        # Set status to NEW
        self._update_order_status(order_id, OrderStatus.NEW)
        
        print(f"✓ 订单已创建: {order_id} - {side.value} {quantity} {symbol}")
        
        return order
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order
        """
        if order_id not in self.active_orders:
            print(f"✗ 订单不存在: {order_id}")
            return False
        
        order = self.active_orders[order_id]
        
        if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED]:
            print(f"✗ 无法取消已结束订单: {order_id}")
            return False
        
        # Update status
        self._update_order_status(order_id, OrderStatus.CANCELLED)
        
        # Remove from active orders
        del self.active_orders[order_id]
        
        print(f"✓ 订单已取消: {order_id}")
        return True
    
    def modify_order(
        self,
        order_id: str,
        quantity: Optional[float] = None,
        price: Optional[float] = None
    ) -> bool:
        """
        Modify an existing order
        """
        if order_id not in self.active_orders:
            print(f"✗ 订单不存在: {order_id}")
            return False
        
        order = self.active_orders[order_id]
        
        if not order.is_active:
            print(f"✗ 无法修改非活跃订单: {order_id}")
            return False
        
        # Update order details
        if quantity is not None:
            order.quantity = quantity
        if price is not None:
            order.price = price
        
        print(f"✓ 订单已修改: {order_id}")
        return True
    
    def process_fill(
        self,
        order_id: str,
        fill_quantity: float,
        fill_price: float,
        fee: float = 0.0
    ) -> Optional[Fill]:
        """
        Process a fill for an order
        """
        if order_id not in self.orders:
            print(f"✗ 订单不存在: {order_id}")
            return None
        
        order = self.orders[order_id]
        
        if not order.is_active:
            print(f"✗ 订单非活跃状态: {order_id}")
            return None
        
        # Calculate actual fill quantity
        available_quantity = order.unfilled_quantity
        actual_fill_qty = min(fill_quantity, available_quantity)
        
        if actual_fill_qty <= 0:
            print(f"✗ 无可填充数量: {order_id}")
            return None
        
        # Update filled quantity and average price
        total_value = (order.average_fill_price * order.filled_quantity) + (fill_price * actual_fill_qty)
        order.filled_quantity += actual_fill_qty
        order.average_fill_price = total_value / order.filled_quantity
        
        # Create fill record
        fill = Fill(
            order_id=order_id,
            symbol=order.symbol,
            side=order.side,
            quantity=actual_fill_qty,
            fill_price=fill_price,
            fill_time=datetime.now().isoformat(),
            fee=fee
        )
        
        self.fills.append(fill)
        
        # Update order status
        if order.filled_quantity >= order.quantity:
            self._update_order_status(order_id, OrderStatus.FILLED)
            # Remove from active orders
            if order_id in self.active_orders:
                del self.active_orders[order_id]
        else:
            self._update_order_status(order_id, OrderStatus.PARTIALLY_FILLED)
        
        print(f"✓ 成交处理: {order_id} - {actual_fill_qty} @ ${fill_price:.2f}")
        
        # Trigger callbacks
        for callback in self.on_fill:
            try:
                callback(fill)
            except Exception as e:
                print(f"Error in fill callback: {e}")
        
        return fill
    
    def _update_order_status(self, order_id: str, new_status: OrderStatus):
        """
        Update order status and trigger callbacks
        """
        if order_id not in self.orders:
            return
        
        order = self.orders[order_id]
        old_status = order.status
        order.status = new_status
        
        print(f"  状态更新: {order_id} {old_status.value} → {new_status.value}")
        
        # Trigger callbacks
        for callback in self.on_order_status_change:
            try:
                callback(order, old_status, new_status)
            except Exception as e:
                print(f"Error in status callback: {e}")
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        return self.orders.get(order_id)
    
    def get_active_orders(self) -> List[Order]:
        """Get all active orders"""
        return list(self.active_orders.values())
    
    def get_order_history(self, symbol: str = None) -> List[Order]:
        """Get order history, optionally filtered by symbol"""
        orders = list(self.orders.values())
        
        if symbol:
            orders = [order for order in orders if order.symbol == symbol]
        
        return sorted(orders, key=lambda x: x.timestamp, reverse=True)
    
    def get_fills_for_order(self, order_id: str) -> List[Fill]:
        """Get all fills for an order"""
        return [fill for fill in self.fills if fill.order_id == order_id]
    
    def get_fill_history(self, symbol: str = None) -> List[Fill]:
        """Get fill history, optionally filtered by symbol"""
        fills = self.fills
        
        if symbol:
            fills = [fill for fill in fills if fill.symbol == symbol]
        
        return sorted(fills, key=lambda x: x.fill_time, reverse=True)
    
    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary based on fills and positions"""
        active_orders = len(self.active_orders)
        total_orders = len(self.orders)
        total_fills = len(self.fills)
        
        # Calculate realized PnL from fills
        realized_pnl = sum(
            fill.quantity * (fill.fill_price - self._get_avg_cost(fill.symbol, fill.order_id))
            if fill.side == OrderSide.BUY
            else fill.quantity * (self._get_avg_cost(fill.symbol, fill.order_id) - fill.fill_price)
            for fill in self.fills
        )
        
        return {
            'active_orders': active_orders,
            'total_orders': total_orders,
            'total_fills': total_fills,
            'realized_pnl': realized_pnl,
            'total_fees': sum(fill.fee for fill in self.fills)
        }
    
    def _get_avg_cost(self, symbol: str, order_id: str) -> float:
        """Helper to get average cost for a symbol (simplified)"""
        # In a real system, this would track position costs
        return 0.0
    
    def register_callback(self, event_type: str, callback):
        """Register callback for events"""
        if event_type == "order_status":
            self.on_order_status_change.append(callback)
        elif event_type == "fill":
            self.on_fill.append(callback)
        elif event_type == "error":
            self.on_error.append(callback)


class ExecutionHandler:
    """
    Execution Handler - Processes orders and sends to exchanges
    """
    
    def __init__(self, order_manager: OrderManager):
        self.order_manager = order_manager
        self.adapters = {}  # Exchange adapters
    
    def register_adapter(self, exchange_name: str, adapter):
        """Register exchange adapter"""
        self.adapters[exchange_name] = adapter
    
    def execute_order(self, order: Order) -> bool:
        """
        Execute an order through appropriate exchange adapter
        """
        # Determine exchange based on symbol
        exchange_name = self._get_exchange_for_symbol(order.symbol)
        
        if exchange_name not in self.adapters:
            print(f"✗ 无可用交易所适配器: {exchange_name}")
            return False
        
        adapter = self.adapters[exchange_name]
        
        try:
            # Submit order to exchange
            result = self._submit_to_exchange(adapter, order)
            
            if result['success']:
                print(f"✓ 订单提交成功: {order.id}")
                
                # Process fills if immediate execution
                if result.get('fills'):
                    for fill_data in result['fills']:
                        self.order_manager.process_fill(
                            order.id,
                            fill_data['quantity'],
                            fill_data['price'],
                            fill_data.get('fee', 0.0)
                        )
                
                return True
            else:
                print(f"✗ 订单提交失败: {order.id} - {result.get('error')}")
                self.order_manager._update_order_status(order.id, OrderStatus.REJECTED)
                return False
                
        except Exception as e:
            print(f"✗ 执行异常: {order.id} - {str(e)}")
            self.order_manager._update_order_status(order.id, OrderStatus.REJECTED)
            return False
    
    def _get_exchange_for_symbol(self, symbol: str) -> str:
        """Determine exchange based on symbol"""
        if symbol.endswith('-USDT') or symbol.endswith('-USD'):
            return 'okx'
        else:
            # Default to stock exchange
            return 'alpaca'
    
    def _submit_to_exchange(self, adapter, order: Order) -> Dict:
        """
        Submit order to exchange adapter
        Returns dict with 'success', 'fills', and optional 'error'
        """
        # This is a simplified implementation
        # In reality, each adapter would have specific methods
        
        try:
            # Map our order to exchange-specific format
            exchange_order = {
                'symbol': order.symbol,
                'side': order.side.value,
                'type': order.order_type.value,
                'quantity': order.quantity,
                'price': order.price,
                'stop_price': order.stop_price,
                'time_in_force': order.time_in_force
            }
            
            # Submit to exchange
            result = adapter.submit_order(exchange_order)
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel order through exchange"""
        order = self.order_manager.get_order(order_id)
        
        if not order:
            return False
        
        exchange_name = self._get_exchange_for_symbol(order.symbol)
        
        if exchange_name not in self.adapters:
            return False
        
        adapter = self.adapters[exchange_name]
        
        try:
            result = adapter.cancel_order(order_id)
            return result.get('success', False)
        except Exception as e:
            print(f"✗ 撤单异常: {order_id} - {str(e)}")
            return False