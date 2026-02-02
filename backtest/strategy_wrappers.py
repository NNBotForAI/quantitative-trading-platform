"""
Strategy Wrapper for Backtest Engine
Wraps our strategies for Backtrader compatibility
"""

import backtrader as bt
from indicators import calculate_sma, calculate_ema, calculate_macd
import numpy as np


class DualMAStrategyWrapper(bt.Strategy):
    """
    Dual Moving Average Crossover Strategy for Backtrader
    Based on Backtrader SignalStrategy pattern
    """
    
    params = (
        ('short_period', 10),
        ('long_period', 30),
        ('risk_per_trade', 0.02),
    )
    
    def __init__(self):
        # Calculate indicators
        self.sma_short = bt.indicators.SMA(self.data.close, period=self.p.short_period)
        self.sma_long = bt.indicators.SMA(self.data.close, period=self.p.long_period)
        
        # Crossover signals
        self.crossover = bt.indicators.CrossOver(self.sma_short, self.sma_long)
        
    def next(self):
        """Execute trading logic"""
        if not self.position:  # No position
            if self.crossover > 0:  # Golden cross
                # Calculate position size
                size = self._calculate_position_size()
                self.buy(size=size)
                
        else:  # Has position
            if self.crossover < 0:  # Death cross
                self.sell(size=self.position.size)
    
    def _calculate_position_size(self) -> float:
        """Calculate position size based on risk"""
        account_value = self.broker.getvalue()
        risk_amount = account_value * self.p.risk_per_trade
        
        # Calculate number of shares
        price = self.data.close[0]
        shares = int(risk_amount / price)
        
        return max(1, shares)


class MACDStrategyWrapper(bt.Strategy):
    """
    MACD Strategy for Backtrader
    Based on Backtrader SignalStrategy pattern
    """
    
    params = (
        ('fast_period', 12),
        ('slow_period', 26),
        ('signal_period', 9),
        ('risk_per_trade', 0.03),
    )
    
    def __init__(self):
        # Calculate MACD indicators
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.p.fast_period,
            period_me2=self.p.slow_period,
            period_signal=self.p.signal_period
        )
        
        # MACD crossover
        self.macd_crossover = bt.indicators.CrossOver(self.macd.macd, self.macd.signal)
        
    def next(self):
        """Execute trading logic"""
        if not self.position:  # No position
            if self.macd_crossover > 0:  # MACD golden cross
                # Calculate position size
                size = self._calculate_position_size()
                self.buy(size=size)
                
        else:  # Has position
            if self.macd_crossover < 0:  # MACD death cross
                self.sell(size=self.position.size)
    
    def _calculate_position_size(self) -> float:
        """Calculate position size based on risk"""
        account_value = self.broker.getvalue()
        risk_amount = account_value * self.p.risk_per_trade
        
        # Calculate number of shares
        price = self.data.close[0]
        shares = int(risk_amount / price)
        
        return max(1, shares)


class RSIStrategy(bt.Strategy):
    """
    RSI Strategy for Backtrader
    """
    
    params = (
        ('rsi_period', 14),
        ('rsi_overbought', 70),
        ('rsi_oversold', 30),
        ('risk_per_trade', 0.02),
    )
    
    def __init__(self):
        # Calculate RSI indicator
        self.rsi = bt.indicators.RSI(self.data.close, period=self.p.rsi_period)
        
    def next(self):
        """Execute trading logic"""
        if not self.position:  # No position
            if self.rsi < self.p.rsi_oversold:  # RSI < 30: oversold, buy
                size = self._calculate_position_size()
                self.buy(size=size)
                
        else:  # Has position
            if self.rsi > self.p.rsi_overbought:  # RSI > 70: overbought, sell
                self.sell(size=self.position.size)
    
    def _calculate_position_size(self) -> float:
        """Calculate position size based on risk"""
        account_value = self.broker.getvalue()
        risk_amount = account_value * self.p.risk_per_trade
        
        # Calculate number of shares
        price = self.data.close[0]
        shares = int(risk_amount / price)
        
        return max(1, shares)


class BollingerBandsStrategy(bt.Strategy):
    """
    Bollinger Bands Strategy for Backtrader
    """
    
    params = (
        ('bb_period', 20),
        ('bb_dev', 2.0),
        ('risk_per_trade', 0.02),
    )
    
    def __init__(self):
        # Calculate Bollinger Bands
        self.bb = bt.indicators.BollingerBands(
            self.data.close,
            period=self.p.bb_period,
            devfactor=self.p.bb_dev
        )
        
    def next(self):
        """Execute trading logic"""
        if not self.position:  # No position
            if self.data.close[0] < self.bb.bot[0]:  # Price < lower band: oversold, buy
                size = self._calculate_position_size()
                self.buy(size=size)
                
        else:  # Has position
            if self.data.close[0] > self.bb.top[0]:  # Price > upper band: overbought, sell
                self.sell(size=self.position.size)
    
    def _calculate_position_size(self) -> float:
        """Calculate position size based on risk"""
        account_value = self.broker.getvalue()
        risk_amount = account_value * self.p.risk_per_trade
        
        # Calculate number of shares
        price = self.data.close[0]
        shares = int(risk_amount / price)
        
        return max(1, shares)