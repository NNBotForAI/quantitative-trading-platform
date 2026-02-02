"""
Technical Indicators for Quantitative Trading Platform
Based on Backtrader indicators
"""

from typing import List, Dict
import numpy as np


def calculate_sma(prices: List[float], period: int) -> float:
    """Simple Moving Average"""
    if len(prices) < period:
        return 0.0
    return sum(prices[-period:]) / period


def calculate_ema(prices: List[float], period: int) -> float:
    """Exponential Moving Average"""
    if len(prices) < period:
        return 0.0
    
    multiplier = 2 / (period + 1)
    ema = prices[0]
    
    for price in prices[1:]:
        ema = (price * multiplier) + (ema * (1 - multiplier))
    
    return ema


def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """Relative Strength Index"""
    if len(prices) < period + 1:
        return 50.0
    
    # Calculate price changes
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    
    # Separate gains and losses
    gains = [delta if delta > 0 else 0 for delta in deltas]
    losses = [-delta if delta < 0 else 0 for delta in deltas]
    
    # Calculate average gains and losses
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    
    # Calculate relative strength
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    
    # Calculate RSI
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_macd(
    prices: List[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> Dict[str, float]:
    """MACD (Moving Average Convergence Divergence)"""
    
    # Calculate fast and slow EMA
    fast_ema = calculate_ema(prices, fast_period)
    slow_ema = calculate_ema(prices, slow_period)
    
    # Calculate MACD line
    macd_line = fast_ema - slow_ema
    signal_line = calculate_ema([macd_line] * signal_period, signal_period)
    
    # Calculate histogram
    histogram = macd_line - signal_line
    
    return {
        "macd": macd_line,
        "signal": signal_line,
        "histogram": histogram
    }


def calculate_bollinger_bands(
    prices: List[float],
    period: int = 20,
    num_std_dev: float = 2.0
) -> Dict[str, List[float]]:
    """Bollinger Bands"""
    
    if len(prices) < period:
        return {
            "middle": [],
            "upper": [],
            "lower": []
        }
    
    # Calculate moving average (middle band)
    sma = calculate_sma(prices, period)
    middle_band = [sma] * len(prices)
    
    # Calculate standard deviation
    std_dev = np.std(prices[-period:])
    upper_band = sma + (std_dev * num_std_dev)
    lower_band = sma - (std_dev * num_std_dev)
    
    return {
        "middle": middle_band,
        "upper": [upper_band] * len(prices),
        "lower": [lower_band] * len(prices)
    }