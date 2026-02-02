"""
Complete End-to-End Test: Full Quantitative Trading System
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from adapters import OKXAdapter
from strategies import DualMACrossStrategy
from backtest import BacktestEngine, DualMAStrategyWrapper
from backtest.analyzers import create_analyzers, PerformanceAnalyzer
from risk import PositionManager, RiskRulesEngine, RiskMonitor
from trading import OrderManager, ExecutionEngine, ExecutionAlgorithm


async def test_complete_system():
    """Test the complete quantitative trading system"""
    print("\n" + "=" * 80)
    print("完整量化交易系统端到端测试")
    print("=" * 80)
    
    # Step 1: Initialize all system components
    print("\n1. 初始化系统组件...")
    
    # Data adapter
    okx_config = {
        "name": "OKX",
        "type": "crypto_okx",
        "credentials": {
            "api_key": "da7e47af-4bb0-400d-b01c-3aa299279629",
            "secret_key": "9237CEEF04C1501D7BA4BFCCBB65200",
            "passphrase": "5683@Sjtu"
        },
        "settings": {
            "exchange": "okx",
            "testnet": True
        }
    }
    
    adapter = OKXAdapter(okx_config)
    connected = await adapter.connect()
    
    if not connected:
        print("✗ OKX连接失败")
        return False
    
    print("✓ 数据适配器初始化完成")
    
    # Risk management
    position_manager = PositionManager(
        initial_capital=100000.0,
        max_position_size=0.3,
        max_risk_per_trade=0.02
    )
    
    risk_rules = RiskRulesEngine()
    risk_rules.create_default_rules(
        max_position_size=30000.0,
        max_daily_loss=10000.0,
        max_drawdown=15.0
    )
    
    risk_monitor = RiskMonitor(position_manager, risk_rules)
    print("✓ 风控系统初始化完成")
    
    # Order management
    order_manager = OrderManager()
    print("✓ 订单管理系统初始化完成")
    
    # Execution engine
    execution_engine = ExecutionEngine()
    print("✓ 执行引擎初始化完成")
    
    # Step 2: Get market data
    print("\n2. 获取市场数据...")
    historical_data = await adapter.get_historical_data("BTC-USDT", "1H", 200)
    
    if len(historical_data) < 100:
        print(f"✗ 历史数据不足: {len(historical_data)}")
        return False
    
    # Convert to pandas DataFrame
    data = pd.DataFrame([{
        'datetime': d.timestamp,
        'open': d.open,
        'high': d.high,
        'low': d.low,
        'close': d.close,
        'volume': d.volume
    } for d in historical_data])
    
    data.set_index('datetime', inplace=True)
    data.sort_index(inplace=True)
    
    print(f"✓ 获取到 {len(data)} 条BTC-USDT历史数据")
    print(f"  价格范围: ${data['close'].min():,.2f} - ${data['close'].max():,.2f}")
    
    # Step 3: Run strategy analysis
    print("\n3. 运行策略分析...")
    
    # Calculate technical indicators
    data['sma_short'] = data['close'].rolling(window=10).mean()
    data['sma_long'] = data['close'].rolling(window=30).mean()
    data['position'] = 0
    data.loc[data['sma_short'] > data['sma_long'], 'position'] = 1
    data.loc[data['sma_short'] < data['sma_long'], 'position'] = -1
    
    # Find recent signals
    recent_signals = data.tail(10)[data['position'] != data['position'].shift(1)]
    print(f"✓ 发现 {len(recent_signals)} 个交易信号")
    
    if len(recent_signals) > 0:
        latest_signal = recent_signals.iloc[-1]
        current_position = latest_signal['position']
        current_price = latest_signal['close']
        
        print(f"  最新信号: {'买入' if current_position == 1 else '卖出'} @ ${current_price:.2f}")
    else:
        print("  无最新交易信号，使用当前价格")
        current_price = data['close'].iloc[-1]
        # Simple logic: buy if above 20-period MA
        ma_20 = data['close'].rolling(20).mean().iloc[-1]
        current_position = 1 if current_price > ma_20 else -1
        print(f"  当前位置: {'买入' if current_position == 1 else '卖出'}")
    
    # Step 4: Run backtest
    print("\n4. 运行回测...")
    engine = BacktestEngine()
    engine.add_strategy(
        DualMAStrategyWrapper,
        short_period=10,
        long_period=30,
        risk_per_trade=0.02
    )
    
    from backtest.engine import DataFeed
    data_feed = DataFeed(dataname=data)
    engine.add_data(data_feed)
    
    create_analyzers(engine.cerebro)
    engine.set_commission(0.001)  # 0.1% commission
    
    results = engine.run()
    
    if results:
        print("✓ 回测完成")
        
        # Get performance analysis
        analyzer = PerformanceAnalyzer(engine.cerebro, engine.results)
        summary = analyzer.get_summary()
        
        print(f"\n回测性能:")
        print(f"  总收益率: {summary['total_return']:.2f}%")
        print(f"  夏普比率: {summary['sharpe_ratio']:.2f}")
        print(f"  最大回撤: {summary['drawdown'].get('max_drawdown', 0):.2f}%")
        print(f"  交易次数: {summary['trades'].get('total', {}).get('total', 0)}")
    else:
        print("✗ 回测失败")
        return False
    
    # Step 5: Generate trading signal and execute
    print("\n5. 生成交易信号并执行...")
    
    # Calculate position size based on risk management
    position_size = position_manager.calculate_position_size(
        "BTC-USDT",
        current_price,
        current_price * (0.95 if current_position == 1 else 1.05)  # Stop loss at 5%
    )
    
    print(f"  计算仓位大小: {position_size:.4f} BTC")
    print(f"  当前价格: ${current_price:.2f}")
    
    if position_size > 0:
        # Create order based on signal
        order_side = 'buy' if current_position == 1 else 'sell'
        
        print(f"  交易方向: {order_side.upper()}")
        
        # Create market order
        order = order_manager.create_order(
            symbol="BTC-USDT",
            side='buy' if current_position == 1 else 'sell',
            order_type='market',
            quantity=position_size
        )
        
        print(f"  订单已创建: {order.id}")
        
        # Execute order using TWAP strategy for large orders
        if position_size > 0.5:  # If order is large, use execution strategy
            print(f"  大订单检测到，使用TWAP执行策略")
            
            # Generate child orders using TWAP
            twap_orders = execution_engine.execute_order_with_strategy(
                order,
                ExecutionAlgorithm.TWAP,
                data,
                time_window_minutes=30,
                slice_interval_minutes=5
            )
            
            print(f"  生成 {len(twap_orders)} 个子订单")
            
            # Process fills for child orders (simulation)
            filled_qty = 0
            avg_fill_price = 0
            
            for i, child_order in enumerate(twap_orders[:3]):  # Process first 3 for demo
                # Simulate fill at current market price with small slippage
                fill_price = current_price * (1.0005 if current_position == 1 else 0.9995)
                order_manager.process_fill(
                    child_order.id,
                    child_order.quantity,
                    fill_price,
                    fee=0.1 * child_order.quantity  # $0.10 per unit fee
                )
                
                filled_qty += child_order.quantity
                avg_fill_price += fill_price * child_order.quantity
                print(f"    子订单 {i+1}: {child_order.quantity:.4f} BTC @ ${fill_price:.2f}")
            
            if filled_qty > 0:
                avg_fill_price /= filled_qty
                print(f"  平均成交价: ${avg_fill_price:.2f}")
        
        else:
            # Process immediate fill for small order
            fill_price = current_price * (1.0005 if current_position == 1 else 0.9995)
            order_manager.process_fill(
                order.id,
                position_size,
                fill_price,
                fee=0.1 * position_size
            )
            print(f"  立即成交: {position_size:.4f} BTC @ ${fill_price:.2f}")
        
        # Update position manager
        if current_position == 1:  # Buy
            position_manager.open_position(
                "BTC-USDT",
                "buy",
                position_size,
                current_price,
                stop_loss=current_price * 0.95,
                take_profit=current_price * 1.10
            )
        else:  # Sell (short in this example)
            print("  注意: 卖空操作需特殊处理")
    
    # Step 6: Monitor risk
    print("\n6. 风险监控...")
    
    # Check risk status
    risk_summary = risk_monitor.get_risk_summary()
    print(f"风险监控摘要:")
    print(f"  24小时告警: {risk_summary['alerts_24h']['total']}")
    print(f"  组合风险比例: {risk_summary['portfolio_risk']['risk_percent']:.2f}%")
    print(f"  组合敞口比例: {risk_summary['portfolio_risk']['exposure_percent']:.2f}%")
    
    # Step 7: Portfolio summary
    print("\n7. 投资组合摘要...")
    portfolio_summary = position_manager.get_summary()
    order_summary = order_manager.get_portfolio_summary()
    
    print(f"仓位管理器:")
    print(f"  当前资本: ${portfolio_summary['current_capital']:,.2f}")
    print(f"  组合价值: ${portfolio_summary['portfolio_value']:,.2f}")
    print(f"  总仓位数: {portfolio_summary['total_positions']}")
    print(f"  胜率: {portfolio_summary['win_rate']:.2f}%")
    
    print(f"订单管理器:")
    print(f"  活跃订单: {order_summary['active_orders']}")
    print(f"  总订单数: {order_summary['total_orders']}")
    print(f"  总成交数: {order_summary['total_fills']}")
    print(f"  总费用: ${order_summary['total_fees']:.2f}")
    
    print("\n" + "=" * 80)
    print("完整系统端到端测试完成！")
    print("✓ 数据获取 → 策略分析 → 回测验证 → 信号生成 → 订单执行 → 风险监控")
    print("=" * 80)
    
    return True


def run_complete_system_test():
    """Run complete system test"""
    print("\n" + "=" * 80)
    print("完整量化交易系统测试")
    print("=" * 80)
    
    try:
        success = asyncio.run(test_complete_system())
        
        print("\n" + "=" * 80)
        print("测试总结")
        print("=" * 80)
        
        if success:
            print("✓ 完整量化交易系统测试通过！")
            print("✓ 所有模块协同工作正常")
            print("✓ 从前端数据到后端执行全流程验证")
            return True
        else:
            print("✗ 完整系统测试失败")
            return False
            
    except Exception as e:
        print(f"✗ 完整系统测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_complete_system_test()
    exit(0 if success else 1)