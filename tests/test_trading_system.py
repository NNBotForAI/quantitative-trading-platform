"""
Test Trading Execution System
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from trading import (
    Order,
    OrderType,
    OrderSide,
    OrderManager,
    ExecutionEngine,
    ExecutionAlgorithm,
    TWAPStrategy,
    VWAPStrategy
)


def test_order_management():
    """Test order management system"""
    print("\n" + "=" * 60)
    print("测试订单管理系统")
    print("=" * 60)
    
    # Create order manager
    om = OrderManager()
    
    # Test creating orders
    print("\n1. 测试创建订单")
    order1 = om.create_order(
        symbol="BTC-USDT",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=1.5,
        price=40000.0
    )
    
    order2 = om.create_order(
        symbol="ETH-USDT",
        side=OrderSide.SELL,
        order_type=OrderType.MARKET,
        quantity=5.0
    )
    
    print(f"  已创建订单: {order1.id}, {order2.id}")
    
    # Test modifying order
    print("\n2. 测试修改订单")
    om.modify_order(order1.id, price=41000.0)
    modified_order = om.get_order(order1.id)
    print(f"  修改后价格: ${modified_order.price}")
    
    # Test processing fills
    print("\n3. 测试成交处理")
    fill1 = om.process_fill(order1.id, 0.5, 40500.0, 2.0)  # 0.5 BTC @ $40,500, fee $2
    fill2 = om.process_fill(order1.id, 1.0, 40600.0, 4.0)  # 1.0 BTC @ $40,600, fee $4
    
    if fill1 and fill2:
        print(f"  成交1: {fill1.quantity} @ ${fill1.fill_price}")
        print(f"  成交2: {fill2.quantity} @ ${fill2.fill_price}")
    
    # Test cancelling order
    print("\n4. 测试取消订单")
    order3 = om.create_order(
        symbol="AAPL",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=100,
        price=150.0
    )
    
    om.cancel_order(order3.id)
    cancelled_order = om.get_order(order3.id)
    print(f"  订单状态: {cancelled_order.status.value}")
    
    # Test portfolio summary
    print("\n5. 测试投资组合摘要")
    summary = om.get_portfolio_summary()
    print(f"  活跃订单: {summary['active_orders']}")
    print(f"  总订单数: {summary['total_orders']}")
    print(f"  总成交数: {summary['total_fills']}")
    print(f"  总费用: ${summary['total_fees']:.2f}")
    
    print("\n✓ 订单管理系统测试完成")
    return True


def test_execution_strategies():
    """Test execution strategies"""
    print("\n" + "=" * 60)
    print("测试执行策略")
    print("=" * 60)
    
    # Create sample market data
    dates = pd.date_range(start='2023-01-01', periods=100, freq='1H')
    np.random.seed(42)
    prices = 40000 + np.cumsum(np.random.randn(100) * 100)
    volumes = np.random.randint(100, 1000, 100)
    
    market_data = pd.DataFrame({
        'datetime': dates,
        'open': prices,
        'high': prices + np.random.rand(100) * 50,
        'low': prices - np.random.rand(100) * 50,
        'close': prices,
        'volume': volumes
    })
    
    print(f"\n1. 创建样本市场数据")
    print(f"  数据点数: {len(market_data)}")
    print(f"  价格范围: ${market_data['close'].min():,.0f} - ${market_data['close'].max():,.0f}")
    
    # Test TWAP strategy
    print("\n2. 测试TWAP策略")
    twap = TWAPStrategy(time_window_minutes=60, slice_interval_minutes=15)
    
    large_order = Order(
        id="LARGE_ORDER_001",
        symbol="BTC-USDT",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=2.0,  # Large order
        price=40000.0
    )
    
    twap_orders = twap.execute(large_order, market_data)
    print(f"  大订单: {large_order.quantity} BTC")
    print(f"  TWAP子订单数: {len(twap_orders)}")
    print(f"  子订单数量: {[f'{q:.2f}' for q, p in twap_orders[:5]]}")  # Show first 5
    print(f"  子订单价格: {[f'${p:.0f}' for q, p in twap_orders[:5]]}")  # Show first 5
    
    # Test VWAP strategy
    print("\n3. 测试VWAP策略")
    vwap = VWAPStrategy(lookback_days=1)
    
    vwap_orders = vwap.execute(large_order, market_data)
    print(f"  VWAP子订单数: {len(vwap_orders)}")
    print(f"  VWAP价格范围: ${min(p for q, p in vwap_orders):.0f} - ${max(p for q, p in vwap_orders):.0f}")
    
    # Test execution engine
    print("\n4. 测试执行引擎")
    engine = ExecutionEngine()
    
    # Execute with TWAP
    twap_child_orders = engine.execute_order_with_strategy(
        large_order,
        ExecutionAlgorithm.TWAP,
        market_data,
        time_window_minutes=30,
        slice_interval_minutes=5
    )
    
    print(f"  TWAP执行子订单: {len(twap_child_orders)}")
    print(f"  第一个子订单: {twap_child_orders[0].quantity} @ ${twap_child_orders[0].price}")
    
    # Execute with VWAP
    vwap_child_orders = engine.execute_order_with_strategy(
        large_order,
        ExecutionAlgorithm.VWAP,
        market_data,
        lookback_days=1
    )
    
    print(f"  VWAP执行子订单: {len(vwap_child_orders)}")
    print(f"  第一个子订单: {vwap_child_orders[0].quantity} @ ${vwap_child_orders[0].price}")
    
    print("\n✓ 执行策略测试完成")
    return True


def test_integration():
    """Test integration of order management and execution"""
    print("\n" + "=" * 60)
    print("测试系统集成")
    print("=" * 60)
    
    # Create components
    order_manager = OrderManager()
    execution_engine = ExecutionEngine()
    
    print("\n1. 创建组件")
    print(f"  订单管理器: 初始化")
    print(f"  执行引擎: {len(execution_engine.strategies)} 种策略")
    
    # Create sample market data
    dates = pd.date_range(start='2023-01-01', periods=50, freq='1H')
    np.random.seed(123)
    prices = 50000 + np.cumsum(np.random.randn(50) * 50)
    volumes = np.random.randint(50, 500, 50)
    
    market_data = pd.DataFrame({
        'datetime': dates,
        'open': prices,
        'high': prices + np.random.rand(50) * 30,
        'low': prices - np.random.rand(50) * 30,
        'close': prices,
        'volume': volumes
    })
    
    # Create large order
    large_order = order_manager.create_order(
        symbol="BTC-USDT",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=3.0
    )
    
    print(f"\n2. 创建大订单")
    print(f"  订单ID: {large_order.id}")
    print(f"  数量: {large_order.quantity} BTC")
    print(f"  类型: {large_order.order_type.value}")
    
    # Execute with MinSlippage strategy
    child_orders = execution_engine.execute_order_with_strategy(
        large_order,
        ExecutionAlgorithm.MIN_SLIPPAGE,
        market_data,
        volatility_lookback=20
    )
    
    print(f"\n3. 执行策略")
    print(f"  策略: MinSlippage")
    print(f"  子订单数: {len(child_orders)}")
    print(f"  平均价格: ${sum(o.price * o.quantity for o in child_orders) / sum(o.quantity for o in child_orders):.2f}")
    
    # Process fills for child orders
    print(f"\n4. 处理成交")
    total_filled = 0
    for child_order in child_orders[:3]:  # Process first 3 for demo
        fill = order_manager.process_fill(
            child_order.id,
            child_order.quantity,
            child_order.price,
            fee=child_order.quantity * 0.1  # $0.10 per unit fee
        )
        if fill:
            total_filled += fill.quantity
            print(f"  成交: {fill.quantity} @ ${fill.fill_price:.2f}")
    
    # Show final summary
    print(f"\n5. 最终摘要")
    summary = order_manager.get_portfolio_summary()
    print(f"  活跃订单: {summary['active_orders']}")
    print(f"  总成交数: {summary['total_fills']}")
    print(f"  总费用: ${summary['total_fees']:.2f}")
    
    # Show execution history
    history = execution_engine.get_execution_history()
    print(f"  执行历史: {len(history)} 条记录")
    
    print("\n✓ 系统集成测试完成")
    return True


def run_trading_tests():
    """Run all trading execution tests"""
    print("\n" + "=" * 60)
    print("交易执行系统测试")
    print("=" * 60)
    
    all_passed = True
    
    try:
        # Test order management
        all_passed &= test_order_management()
        
        # Test execution strategies
        all_passed &= test_execution_strategies()
        
        # Test integration
        all_passed &= test_integration()
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    if all_passed:
        print("✓ 所有交易执行系统测试通过！")
        return True
    else:
        print("✗ 部分测试失败")
        return False


if __name__ == "__main__":
    success = run_trading_tests()
    exit(0 if success else 1)