"""
Test Backtest Engine
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import backtrader as bt
import pandas as pd
from datetime import datetime, timedelta
from backtest.engine import BacktestEngine, DataFeed
from backtest.strategy_wrappers import DualMAStrategyWrapper, MACDStrategyWrapper
from backtest.analyzers import create_analyzers, PerformanceAnalyzer


def create_mock_data(days=30, start_date=None):
    """Create mock price data"""
    if not start_date:
        start_date = datetime.now() - timedelta(days=days)
    
    dates = pd.date_range(start=start_date, periods=days, freq='D')
    
    # Simulate price with trend and noise
    base_price = 100000.0
    prices = []
    
    for i in range(days):
        trend = i * 100.0  # Uptrend
        noise = (i % 7 - 3) * 500.0  # Weekly cycle
        price = base_price + trend + noise
        prices.append(price)
    
    # Create DataFrame with OHLCV data
    data = pd.DataFrame({
        'datetime': dates,
        'open': [p * 0.995 for p in prices],
        'high': [p * 1.015 for p in prices],
        'low': [p * 0.985 for p in prices],
        'close': prices,
        'volume': [100 + i * 10 for i in range(days)]
    })
    
    data.set_index('datetime', inplace=True)
    
    return data


def test_dual_ma_backtest():
    """Test Dual Moving Average Strategy Backtest"""
    print("\n" + "=" * 60)
    print("测试双均线策略回测")
    print("=" * 60)
    
    # Create engine
    engine = BacktestEngine()
    
    # Add strategy
    engine.add_strategy(
        DualMAStrategyWrapper,
        short_period=10,
        long_period=30,
        risk_per_trade=0.02
    )
    
    # Add data
    data = create_mock_data(60)
    data_feed = DataFeed(dataname=data)
    engine.add_data(data_feed)
    
    # Add analyzers
    create_analyzers(engine.cerebro)
    
    # Set commission
    engine.set_commission(0.001)
    
    # Run backtest
    results = engine.run()
    
    # Analyze results
    analyzer = PerformanceAnalyzer(engine.cerebro, engine.results)
    analyzer.print_summary()
    
    print("✓ 双均线策略回测完成")
    return True


def test_macd_backtest():
    """Test MACD Strategy Backtest"""
    print("\n" + "=" * 60)
    print("测试MACD策略回测")
    print("=" * 60)
    
    # Create engine
    engine = BacktestEngine()
    
    # Add strategy
    engine.add_strategy(
        MACDStrategyWrapper,
        fast_period=12,
        slow_period=26,
        signal_period=9,
        risk_per_trade=0.03
    )
    
    # Add data
    data = create_mock_data(60)
    data_feed = DataFeed(dataname=data)
    engine.add_data(data_feed)
    
    # Add analyzers
    create_analyzers(engine.cerebro)
    
    # Set commission
    engine.set_commission(0.001)
    
    # Run backtest
    results = engine.run()
    
    # Analyze results
    analyzer = PerformanceAnalyzer(engine.cerebro, engine.results)
    analyzer.print_summary()
    
    print("✓ MACD策略回测完成")
    return True


def test_engine_basic():
    """Test basic engine functionality"""
    print("\n" + "=" * 60)
    print("测试回测引擎基本功能")
    print("=" * 60)
    
    # Create engine
    engine = BacktestEngine()
    
    # Test cash setting
    engine.set_cash(100000.0)
    print(f"✓ 初始资金设置: ${100000.0:,.2f}")
    
    # Test commission setting
    engine.set_commission(0.001)
    print(f"✓ 手续费设置: 0.1%")
    
    # Test strategy addition
    engine.add_strategy(DualMAStrategyWrapper)
    print(f"✓ 策略已添加: DualMA")
    
    # Test data creation
    data = create_mock_data(30)
    data_feed = DataFeed(dataname=data)
    engine.add_data(data_feed)
    print(f"✓ 数据已添加: {len(data)} 条记录")
    
    # Test analyzer addition
    create_analyzers(engine.cerebro)
    print(f"✓ 分析器已添加")
    
    print("✓ 引擎基本功能测试完成")
    return True


def run_all_backtests():
    """Run all backtest tests"""
    print("\n" + "=" * 60)
    print("回测引擎测试")
    print("=" * 60)
    
    all_passed = True
    
    try:
        # Test basic functionality
        all_passed &= test_engine_basic()
        
        # Test dual MA backtest
        all_passed &= test_dual_ma_backtest()
        
        # Test MACD backtest
        all_passed &= test_macd_backtest()
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    if all_passed:
        print("✓ 所有回测引擎测试通过！")
        return True
    else:
        print("✗ 部分测试失败")
        return False


if __name__ == "__main__":
    success = run_all_backtests()
    exit(0 if success else 1)