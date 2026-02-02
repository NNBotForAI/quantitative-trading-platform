"""
Test strategy signal generation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import asyncio
from datetime import datetime, timedelta
from adapters import OKXAdapter
from strategies.specific_strategies import DualMACrossStrategy, MACDStrategy
from data_interface_framework import MarketData, AssetType


async def test_dual_ma_strategy():
    """Test Dual Moving Average Strategy"""
    print("\n" + "=" * 60)
    print("测试双均线策略")
    print("=" * 60)
    
    strategy = DualMACrossStrategy()
    
    # Generate mock data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Simulate uptrend
    base_price = 100000.0
    data = []
    
    for i in range(30):
        # Simulate uptrend with noise
        price = base_price * (1 + i * 0.01) * (1 + (i % 5 - 2) * 0.005)
        
        market_data = MarketData(
            timestamp=start_date + timedelta(days=i),
            symbol="BTC-USDT",
            open_price=price * 0.99,
            high=price * 1.02,
            low=price * 0.98,
            close=price,
            volume=100 + i * 10,
            asset_type=AssetType.CRYPTO,
            source="模拟数据"
        )
        data.append(market_data)
    
    # Generate signals
    signals = strategy.generate_signals(data)
    
    print(f"策略名称: {strategy.name}")
    print(f"参数: {strategy.parameters}")
    print(f"数据点数: {len(data)}")
    print(f"最新价格: ${data[-1].close:,.2f}")
    print(f"\n生成的信号: {signals}")
    
    # Calculate position size
    account_balance = 10000.0
    position_size = strategy.calculate_position_size(data[-1].close, account_balance)
    
    print(f"\n账户余额: ${account_balance:,.2f}")
    print(f"仓位大小: ${position_size:,.2f}")
    print(f"风险比例: {strategy.parameters['risk_per_trade']}")
    
    print("\n✓ 双均线策略测试完成")
    return True


async def test_macd_strategy():
    """Test MACD Strategy"""
    print("\n" + "=" * 60)
    print("测试MACD策略")
    print("=" * 60)
    
    strategy = MACDStrategy()
    
    # Generate mock data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Simulate data
    base_price = 100000.0
    data = []
    
    for i in range(30):
        # Simulate data with trends
        trend = 0.01 * ((i // 10) % 2)  # Alternate between uptrend and downtrend
        price = base_price * (1 + trend) * (1 + (i % 5 - 2) * 0.003)
        
        market_data = MarketData(
            timestamp=start_date + timedelta(days=i),
            symbol="BTC-USDT",
            open_price=price * 0.995,
            high=price * 1.015,
            low=price * 0.985,
            close=price,
            volume=100 + i * 10,
            asset_type=AssetType.CRYPTO,
            source="模拟数据"
        )
        data.append(market_data)
    
    # Generate signals
    signals = strategy.generate_signals(data)
    
    print(f"策略名称: {strategy.name}")
    print(f"参数: {strategy.parameters}")
    print(f"数据点数: {len(data)}")
    print(f"最新价格: ${data[-1].close:,.2f}")
    print(f"\n生成的信号: {signals}")
    
    # Calculate position size
    account_balance = 10000.0
    position_size = strategy.calculate_position_size(data[-1].close, account_balance)
    
    print(f"\n账户余额: ${account_balance:,.2f}")
    print(f"仓位大小: ${position_size:,.2f}")
    print(f"风险比例: {strategy.parameters['risk_per_trade']}")
    
    print("\n✓ MACD策略测试完成")
    return True


async def test_strategy_with_real_data():
    """Test strategies with real OKX data"""
    print("\n" + "=" * 60)
    print("测试策略（使用OKX真实数据）")
    print("=" * 60)
    
    # Get real data from OKX
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
        print("✗ OKX连接失败，无法获取真实数据")
        return False
    
    print("\n获取BTC-USDT历史数据...")
    historical_data = await adapter.get_historical_data("BTC-USDT", "1H", 30)
    
    if len(historical_data) < 10:
        print(f"✗ 历史数据不足: {len(historical_data)}")
        return False
    
    print(f"✓ 获取到 {len(historical_data)} 条历史数据")
    
    # Test dual MA strategy with real data
    print("\n" + "-" * 60)
    print("双均线策略（真实数据）")
    print("-" * 60)
    
    ma_strategy = DualMACrossStrategy()
    ma_signals = ma_strategy.generate_signals(historical_data)
    
    print(f"最新价格: ${historical_data[-1].close:,.2f}")
    print(f"信号: {ma_signals}")
    
    # Test MACD strategy with real data
    print("\n" + "-" * 60)
    print("MACD策略（真实数据）")
    print("-" * 60)
    
    macd_strategy = MACDStrategy()
    macd_signals = macd_strategy.generate_signals(historical_data)
    
    print(f"最新价格: ${historical_data[-1].close:,.2f}")
    print(f"信号: {macd_signals}")
    
    print("\n✓ 真实数据策略测试完成")
    return True


async def test_all_strategies():
    """Run all strategy tests"""
    print("\n" + "=" * 60)
    print("策略测试")
    print("=" * 60)
    
    all_passed = True
    
    try:
        # Test with mock data
        all_passed &= await test_dual_ma_strategy()
        all_passed &= await test_macd_strategy()
        
        # Test with real data
        all_passed &= await test_strategy_with_real_data()
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    if all_passed:
        print("✓ 所有策略测试通过！")
        return True
    else:
        print("✗ 部分测试失败")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_all_strategies())
    exit(0 if success else 1)