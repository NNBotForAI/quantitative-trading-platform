"""
Integration Test: Backtest with Real OKX Data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import asyncio
import pandas as pd
from datetime import datetime, timedelta
from adapters import OKXAdapter
from backtest import BacktestEngine, DualMAStrategyWrapper, MACDStrategyWrapper
from backtest.analyzers import create_analyzers, PerformanceAnalyzer


async def test_backtest_with_real_data():
    """Test backtest with real OKX data"""
    print("\n" + "=" * 60)
    print("真实数据回测测试")
    print("=" * 60)
    
    # Connect to OKX
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
    
    print("\n✓ OKX连接成功")
    
    # Get historical data
    print("\n获取BTC-USDT历史数据...")
    historical_data = await adapter.get_historical_data("BTC-USDT", "1H", 100)
    
    if len(historical_data) < 30:
        print(f"✗ 历史数据不足: {len(historical_data)}")
        return False
    
    print(f"✓ 获取到 {len(historical_data)} 条历史数据")
    
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
    
    print(f"\n数据时间范围:")
    print(f"  开始: {data.index[0]}")
    print(f"  结束: {data.index[-1]}")
    print(f"  价格范围: ${data['close'].min():,.2f} - ${data['close'].max():,.2f}")
    
    # Test Dual MA backtest
    print("\n" + "-" * 60)
    print("双均线策略回测（真实数据）")
    print("-" * 60)
    
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
    engine.set_commission(0.001)
    
    results = engine.run()
    
    if results:
        analyzer = PerformanceAnalyzer(engine.cerebro, engine.results)
        analyzer.print_summary()
    
    # Test MACD backtest
    print("\n" + "-" * 60)
    print("MACD策略回测（真实数据）")
    print("-" * 60)
    
    engine2 = BacktestEngine()
    engine2.add_strategy(
        MACDStrategyWrapper,
        fast_period=12,
        slow_period=26,
        signal_period=9,
        risk_per_trade=0.03
    )
    
    data_feed2 = DataFeed(dataname=data)
    engine2.add_data(data_feed2)
    
    create_analyzers(engine2.cerebro)
    engine2.set_commission(0.001)
    
    results2 = engine2.run()
    
    if results2:
        analyzer2 = PerformanceAnalyzer(engine2.cerebro, engine2.results)
        analyzer2.print_summary()
    
    print("\n✓ 真实数据回测完成")
    return True


async def run_integration_tests():
    """Run integration tests"""
    print("\n" + "=" * 60)
    print("集成测试：真实数据回测")
    print("=" * 60)
    
    all_passed = True
    
    try:
        all_passed &= await test_backtest_with_real_data()
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    if all_passed:
        print("✓ 所有集成测试通过！")
        return True
    else:
        print("✗ 部分测试失败")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_integration_tests())
    exit(0 if success else 1)