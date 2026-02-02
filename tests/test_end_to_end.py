"""
End-to-End Integration Test
Testing the complete quantitative trading system with real data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import asyncio
import pandas as pd
from datetime import datetime, timedelta

from adapters import OKXAdapter
from backtest import DualMAStrategyWrapper
from backtest import BacktestEngine
from backtest.analyzers import create_analyzers, PerformanceAnalyzer
from risk import PositionManager, RiskRulesEngine, RiskMonitor


async def test_end_to_end_system():
    """Test the complete system with real OKX data"""
    print("\n" + "=" * 80)
    print("端到端系统测试：完整量化交易流程")
    print("=" * 80)
    
    # Step 1: Initialize data adapter
    print("\n1. 初始化数据适配器...")
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
    
    print("✓ OKX连接成功")
    
    # Step 2: Get historical data
    print("\n2. 获取历史数据...")
    historical_data = await adapter.get_historical_data("BTC-USDT", "1H", 200)
    
    if len(historical_data) < 100:
        print(f"✗ 历史数据不足: {len(historical_data)}")
        return False
    
    print(f"✓ 获取到 {len(historical_data)} 条BTC-USDT历史数据")
    
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
    
    print(f"  数据时间范围: {data.index[0]} 至 {data.index[-1]}")
    print(f"  价格范围: ${data['close'].min():,.2f} - ${data['close'].max():,.2f}")
    
    # Step 3: Initialize risk management
    print("\n3. 初始化风控系统...")
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
        
        print(f"\n回测性能摘要:")
        print(f"  初始资金: ${summary['initial_value']:,.2f}")
        print(f"  最终资金: ${summary['final_value']:,.2f}")
        print(f"  总收益率: {summary['total_return']:.2f}%")
        print(f"  夏普比率: {summary['sharpe_ratio']:.2f}")
        print(f"  最大回撤: {summary['drawdown'].get('max_drawdown', 0):.2f}%")
        print(f"  交易次数: {summary['trades'].get('total', {}).get('total', 0)}")
        # 由于交易可能为0，避免除零错误
        total_trades = summary['trades'].get('total', {}).get('total', 0)
        winning_trades = summary['trades'].get('pnl', {}).get('won', {}).get('total', 0)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        print(f"  胜率: {winning_trades}/{total_trades} ({win_rate:.1f}%)")
    else:
        print("✗ 回测失败")
        return False
    
    # Step 5: Test risk monitoring
    print("\n5. 测试风险监控...")
    risk_summary = risk_monitor.get_risk_summary()
    
    print(f"风险监控摘要:")
    print(f"  24小时告警: {risk_summary['alerts_24h']['total']}")
    print(f"  未确认严重告警: {risk_summary['unacknowledged_critical']}")
    print(f"  组合风险比例: {risk_summary['portfolio_risk']['risk_percent']:.2f}%")
    print(f"  组合敞口比例: {risk_summary['portfolio_risk']['exposure_percent']:.2f}%")
    
    # Step 6: Test position management
    print("\n6. 测试仓位管理...")
    # Simulate opening positions based on strategy signals
    latest_price = data['close'].iloc[-1]
    quantity = position_manager.calculate_position_size("BTC-USDT", latest_price, latest_price * 0.95)
    
    print(f"  根据当前价格 ${latest_price:.2f} 计算仓位: {quantity} BTC")
    
    if quantity > 0:
        position = position_manager.open_position(
            "BTC-USDT",
            "buy",
            quantity,
            latest_price,
            stop_loss=latest_price * 0.95,
            take_profit=latest_price * 1.10
        )
        
        print(f"  ✓ 开仓: {quantity} BTC @ ${latest_price:.2f}")
        print(f"  ✓ 止损: ${latest_price * 0.95:.2f}")
        print(f"  ✓ 止盈: ${latest_price * 1.10:.2f}")
    
    # Get final portfolio summary
    portfolio_summary = position_manager.get_summary()
    print(f"\n最终组合摘要:")
    print(f"  初始资本: ${portfolio_summary['initial_capital']:,.2f}")
    print(f"  当前资本: ${portfolio_summary['current_capital']:,.2f}")
    print(f"  组合价值: ${portfolio_summary['portfolio_value']:,.2f}")
    print(f"  总仓位数: {portfolio_summary['total_positions']}")
    print(f"  总交易数: {portfolio_summary['total_trades']}")
    print(f"  胜率: {portfolio_summary['win_rate']:.2f}%")
    
    print("\n" + "=" * 80)
    print("端到端系统测试完成！")
    print("✓ 数据获取 - 策略回测 - 风控管理 - 仓位管理 全流程验证")
    print("=" * 80)
    
    return True


def run_end_to_end_tests():
    """Run end-to-end integration tests"""
    print("\n" + "=" * 80)
    print("端到端集成测试")
    print("=" * 80)
    
    try:
        success = asyncio.run(test_end_to_end_system())
        
        print("\n" + "=" * 80)
        print("测试总结")
        print("=" * 80)
        
        if success:
            print("✓ 所有端到端测试通过！")
            print("✓ 完整的量化交易系统已验证")
            return True
        else:
            print("✗ 部分端到端测试失败")
            return False
            
    except Exception as e:
        print(f"✗ 端到端测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_end_to_end_tests()
    exit(0 if success else 1)