"""
Test technical indicators calculation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from indicators import (
    calculate_sma,
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands
)


def test_sma():
    """Test Simple Moving Average"""
    print("\n" + "=" * 60)
    print("测试SMA（简单移动平均）")
    print("=" * 60)
    
    prices = [100, 102, 103, 104, 105, 106, 107, 108, 109, 110]
    sma_5 = calculate_sma(prices, 5)
    sma_10 = calculate_sma(prices, 10)
    
    print(f"价格序列: {prices}")
    print(f"SMA(5): {sma_5}")
    print(f"SMA(10): {sma_10}")
    
    # SMA(5) = (106+107+108+109+110)/5 = 540/5 = 108.0
    assert sma_5 == 108.0, f"SMA(5) should be 108.0, got {sma_5}"
    assert sma_10 == 105.4, f"SMA(10) should be 105.4, got {sma_10}"
    
    print("✓ SMA测试通过")
    return True


def test_ema():
    """Test Exponential Moving Average"""
    print("\n" + "=" * 60)
    print("测试EMA（指数移动平均）")
    print("=" * 60)
    
    prices = [100, 102, 103, 104, 105, 106, 107, 108, 109, 110]
    ema_5 = calculate_ema(prices, 5)
    ema_10 = calculate_ema(prices, 10)
    
    print(f"价格序列: {prices}")
    print(f"EMA(5): {ema_5}")
    print(f"EMA(10): {ema_10}")
    
    # EMA should be different from SMA
    assert ema_5 > 105.0, f"EMA(5) should be > 105.0, got {ema_5}"
    assert ema_10 > 105.0, f"EMA(10) should be > 105.0, got {ema_10}"
    
    print("✓ EMA测试通过")
    return True


def test_rsi():
    """Test Relative Strength Index"""
    print("\n" + "=" * 60)
    print("测试RSI（相对强弱指标）")
    print("=" * 60)
    
    # Test with uptrend
    uptrend = [100, 105, 110, 115, 120, 125, 130, 135, 140, 145, 150, 155, 160, 165, 170]
    rsi_uptrend = calculate_rsi(uptrend, 14)
    
    print(f"上升趋势价格: {uptrend}")
    print(f"RSI(14): {rsi_uptrend}")
    
    # RSI should be high (>70) for uptrend
    assert rsi_uptrend > 70, f"RSI should be >70 for uptrend, got {rsi_uptrend}"
    
    # Test with downtrend
    downtrend = [170, 165, 160, 155, 150, 145, 140, 135, 130, 125, 120, 115, 110, 105, 100]
    rsi_downtrend = calculate_rsi(downtrend, 14)
    
    print(f"下降趋势价格: {downtrend}")
    print(f"RSI(14): {rsi_downtrend}")
    
    # RSI should be low (<30) for downtrend
    assert rsi_downtrend < 30, f"RSI should be <30 for downtrend, got {rsi_downtrend}"
    
    print("✓ RSI测试通过")
    return True


def test_macd():
    """Test MACD indicator"""
    print("\n" + "=" * 60)
    print("测试MACD（平滑异同移动平均）")
    print("=" * 60)
    
    prices = [100, 102, 103, 104, 105, 106, 107, 108, 109, 110,
              111, 112, 113, 114, 115, 116, 117, 118, 119, 120,
              121, 122, 123, 124, 125, 126, 127, 128, 129, 130]
    
    macd_result = calculate_macd(prices, 12, 26, 9)
    
    print(f"价格序列长度: {len(prices)}")
    print(f"MACD: {macd_result}")
    
    assert 'macd' in macd_result, "MACD result should contain 'macd'"
    assert 'signal' in macd_result, "MACD result should contain 'signal'"
    assert 'histogram' in macd_result, "MACD result should contain 'histogram'"
    
    macd_value = macd_result['macd']
    signal_value = macd_result['signal']
    histogram_value = macd_result['histogram']
    
    # Histogram should equal MACD - Signal
    assert abs(histogram_value - (macd_value - signal_value)) < 0.01, \
        f"Histogram should equal MACD - Signal, got {histogram_value} vs {macd_value - signal_value}"
    
    print("✓ MACD测试通过")
    return True


def test_bollinger_bands():
    """Test Bollinger Bands"""
    print("\n" + "=" * 60)
    print("测试布林带（Bollinger Bands）")
    print("=" * 60)
    
    prices = [100, 102, 103, 104, 105, 106, 107, 108, 109, 110,
              111, 112, 113, 114, 115, 116, 117, 118, 119, 120]
    
    bb_result = calculate_bollinger_bands(prices, period=20, num_std_dev=2.0)
    
    print(f"价格序列长度: {len(prices)}")
    print(f"布林带上轨: {bb_result['upper'][-1]}")
    print(f"布林带中轨: {bb_result['middle'][-1]}")
    print(f"布林带下轨: {bb_result['lower'][-1]}")
    
    assert 'middle' in bb_result, "Bollinger Bands should contain 'middle'"
    assert 'upper' in bb_result, "Bollinger Bands should contain 'upper'"
    assert 'lower' in bb_result, "Bollinger Bands should contain 'lower'"
    
    # Upper band should be > middle > lower
    assert bb_result['upper'][-1] > bb_result['middle'][-1], "Upper band should be > middle"
    assert bb_result['middle'][-1] > bb_result['lower'][-1], "Middle should be > lower"
    
    print("✓ 布林带测试通过")
    return True


def test_all_indicators():
    """Run all indicator tests"""
    print("\n" + "=" * 60)
    print("技术指标测试")
    print("=" * 60)
    
    all_passed = True
    
    try:
        all_passed &= test_sma()
        all_passed &= test_ema()
        all_passed &= test_rsi()
        all_passed &= test_macd()
        all_passed &= test_bollinger_bands()
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    if all_passed:
        print("✓ 所有技术指标测试通过！")
        return True
    else:
        print("✗ 部分测试失败")
        return False


if __name__ == "__main__":
    success = test_all_indicators()
    exit(0 if success else 1)