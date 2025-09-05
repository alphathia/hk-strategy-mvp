"""
Enhanced Technical Analysis - Missing indicators for strategy level engine
Implements all technical indicators required for TXYZn level 1-9 analysis

Key additions:
- EMA5 calculation and integration
- BBWidth rising detection (≥3 of last 5 bars)
- Volume SMA20 ratio calculations
- Multi-period RSI (RSI 7/14/21)
- MACD histogram trend analysis
- EMA stack analysis (5>12>26>50>100)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

class EnhancedTechnicalAnalysis:
    """Enhanced technical analysis with all indicators needed for strategy levels"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_all_indicators(self, price_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate comprehensive technical indicators for strategy level analysis
        
        Args:
            price_data: DataFrame with OHLCV data
            
        Returns:
            Dict containing all technical indicator values
        """
        if len(price_data) < 100:  # Need sufficient history
            raise ValueError("Insufficient price data for technical analysis")
        
        df = price_data.copy()
        indicators = {}
        
        # Basic price data
        indicators['close_price'] = df['Close'].iloc[-1] if 'Close' in df else df['close'].iloc[-1]
        indicators['volume'] = df['Volume'].iloc[-1] if 'Volume' in df else df['volume'].iloc[-1]
        
        # Moving Averages (all periods needed)
        indicators['ema5'] = self._calculate_ema(df, 5)
        indicators['ema12'] = self._calculate_ema(df, 12)
        indicators['ema26'] = self._calculate_ema(df, 26)
        indicators['ema50'] = self._calculate_ema(df, 50)
        indicators['ema100'] = self._calculate_ema(df, 100) if len(df) >= 100 else indicators['ema50']
        indicators['sma20'] = self._calculate_sma(df, 20)
        
        # Bollinger Bands with additional metrics
        bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(df, period=20, std=2.0)
        indicators['bb_upper'] = bb_upper
        indicators['bb_middle'] = bb_middle  # Same as SMA20
        indicators['bb_lower'] = bb_lower
        indicators['bb_width_rising_count'] = self._calculate_bb_width_rising(df, period=20, std=2.0)
        
        # RSI multi-period
        indicators['rsi7'] = self._calculate_rsi(df, 7)
        indicators['rsi14'] = self._calculate_rsi(df, 14)
        indicators['rsi21'] = self._calculate_rsi(df, 21)
        
        # MACD with histogram analysis
        macd, macd_signal, macd_histogram = self._calculate_macd(df, fast=12, slow=26, signal=9)
        indicators['macd'] = macd
        indicators['macd_signal'] = macd_signal
        indicators['macd_histogram'] = macd_histogram
        indicators['macd_histogram_increasing'] = self._is_histogram_increasing(df, fast=12, slow=26, signal=9)
        
        # Volume analysis
        indicators['volume_sma20'] = self._calculate_volume_sma(df, 20)
        indicators['volume_ratio'] = indicators['volume'] / indicators['volume_sma20'] if indicators['volume_sma20'] > 0 else 1.0
        
        # EMA stack analysis
        indicators['ema_stack_bullish'] = self._check_ema_stack_bullish(indicators)
        indicators['ema_stack_bearish'] = self._check_ema_stack_bearish(indicators)
        
        # Additional metadata
        indicators['symbol'] = getattr(price_data, 'symbol', 'UNKNOWN')
        indicators['bar_date'] = date.today()  # Should be passed in real implementation
        
        return indicators
    
    def _calculate_ema(self, df: pd.DataFrame, period: int) -> float:
        """Calculate Exponential Moving Average"""
        close_col = 'Close' if 'Close' in df else 'close'
        ema = df[close_col].ewm(span=period, adjust=False).mean()
        return ema.iloc[-1] if len(ema) > 0 else df[close_col].iloc[-1]
    
    def _calculate_sma(self, df: pd.DataFrame, period: int) -> float:
        """Calculate Simple Moving Average"""
        close_col = 'Close' if 'Close' in df else 'close'
        sma = df[close_col].rolling(window=period).mean()
        return sma.iloc[-1] if len(sma) > 0 else df[close_col].iloc[-1]
    
    def _calculate_bollinger_bands(self, df: pd.DataFrame, period: int = 20, std: float = 2.0) -> Tuple[float, float, float]:
        """Calculate Bollinger Bands"""
        close_col = 'Close' if 'Close' in df else 'close'
        sma = df[close_col].rolling(window=period).mean()
        rolling_std = df[close_col].rolling(window=period).std()
        
        upper_band = sma + (rolling_std * std)
        lower_band = sma - (rolling_std * std)
        
        return (
            upper_band.iloc[-1] if len(upper_band) > 0 else df[close_col].iloc[-1] * 1.02,
            sma.iloc[-1] if len(sma) > 0 else df[close_col].iloc[-1],
            lower_band.iloc[-1] if len(lower_band) > 0 else df[close_col].iloc[-1] * 0.98
        )
    
    def _calculate_bb_width_rising(self, df: pd.DataFrame, period: int = 20, std: float = 2.0) -> int:
        """
        Calculate how many of the last 5 bars had rising Bollinger Band width
        Returns: count (0-5) of rising BBWidth bars
        """
        if len(df) < period + 5:
            return 0
        
        close_col = 'Close' if 'Close' in df else 'close'
        sma = df[close_col].rolling(window=period).mean()
        rolling_std = df[close_col].rolling(window=period).std()
        
        # Calculate BBWidth: (Upper - Lower) / Middle
        bb_width = (rolling_std * std * 2) / sma
        bb_width = bb_width.fillna(0)
        
        # Check last 5 bars for rising width
        if len(bb_width) < 6:
            return 0
        
        last_5_widths = bb_width.tail(6)  # Get 6 to compare 5 changes
        rising_count = 0
        
        for i in range(1, 6):  # Compare each bar to previous
            if last_5_widths.iloc[i] > last_5_widths.iloc[i-1]:
                rising_count += 1
        
        return rising_count
    
    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate RSI"""
        close_col = 'Close' if 'Close' in df else 'close'
        delta = df[close_col].diff()
        
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1] if len(rsi) > 0 else 50.0
    
    def _calculate_macd(self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float, float]:
        """Calculate MACD, Signal, and Histogram"""
        close_col = 'Close' if 'Close' in df else 'close'
        
        ema_fast = df[close_col].ewm(span=fast, adjust=False).mean()
        ema_slow = df[close_col].ewm(span=slow, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return (
            macd_line.iloc[-1] if len(macd_line) > 0 else 0.0,
            signal_line.iloc[-1] if len(signal_line) > 0 else 0.0,
            histogram.iloc[-1] if len(histogram) > 0 else 0.0
        )
    
    def _is_histogram_increasing(self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9, lookback: int = 2) -> bool:
        """Check if MACD histogram is increasing over the last N bars"""
        if len(df) < slow + signal + lookback:
            return False
        
        close_col = 'Close' if 'Close' in df else 'close'
        
        ema_fast = df[close_col].ewm(span=fast, adjust=False).mean()
        ema_slow = df[close_col].ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        # Check if current histogram > previous histogram for the last `lookback` periods
        recent_histogram = histogram.tail(lookback + 1)
        if len(recent_histogram) < lookback + 1:
            return False
        
        for i in range(1, lookback + 1):
            if recent_histogram.iloc[i] <= recent_histogram.iloc[i - 1]:
                return False
        
        return True
    
    def _calculate_volume_sma(self, df: pd.DataFrame, period: int = 20) -> float:
        """Calculate Volume Simple Moving Average"""
        volume_col = 'Volume' if 'Volume' in df else 'volume'
        if volume_col not in df:
            return 1000000  # Default volume if not available
        
        volume_sma = df[volume_col].rolling(window=period).mean()
        return volume_sma.iloc[-1] if len(volume_sma) > 0 else df[volume_col].iloc[-1]
    
    def _check_ema_stack_bullish(self, indicators: Dict[str, float]) -> bool:
        """Check if EMA stack is in bullish order: EMA5 > EMA12 > EMA26 > EMA50 > EMA100"""
        try:
            return (indicators['ema5'] > indicators['ema12'] > 
                   indicators['ema26'] > indicators['ema50'] > 
                   indicators['ema100'])
        except (KeyError, TypeError):
            return False
    
    def _check_ema_stack_bearish(self, indicators: Dict[str, float]) -> bool:
        """Check if EMA stack is in bearish order: EMA5 < EMA12 < EMA26 < EMA50 < EMA100"""
        try:
            return (indicators['ema5'] < indicators['ema12'] < 
                   indicators['ema26'] < indicators['ema50'] < 
                   indicators['ema100'])
        except (KeyError, TypeError):
            return False
    
    def detect_divergence_rsi(self, df: pd.DataFrame, period: int = 14, lookback: int = 10) -> Dict[str, bool]:
        """
        Detect RSI bullish/bearish divergence
        
        Returns:
            Dict with 'bullish_divergence' and 'bearish_divergence' booleans
        """
        if len(df) < period + lookback + 5:
            return {'bullish_divergence': False, 'bearish_divergence': False}
        
        close_col = 'Close' if 'Close' in df else 'close'
        rsi = self._calculate_rsi_series(df, period)
        prices = df[close_col].tail(lookback + 1)
        rsi_values = rsi.tail(lookback + 1)
        
        # Look for divergence patterns
        bullish_divergence = False
        bearish_divergence = False
        
        # Find recent lows and highs
        for i in range(1, len(prices) - 1):
            current_price = prices.iloc[-1]
            past_price = prices.iloc[-1-i]
            current_rsi = rsi_values.iloc[-1]
            past_rsi = rsi_values.iloc[-1-i]
            
            # Bullish divergence: lower price low, higher RSI low (both below 40)
            if (current_price < past_price and current_rsi > past_rsi and 
                current_rsi < 40 and past_rsi < 40):
                bullish_divergence = True
            
            # Bearish divergence: higher price high, lower RSI high (both above 60)
            if (current_price > past_price and current_rsi < past_rsi and
                current_rsi > 60 and past_rsi > 60):
                bearish_divergence = True
        
        return {
            'bullish_divergence': bullish_divergence,
            'bearish_divergence': bearish_divergence
        }
    
    def _calculate_rsi_series(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate RSI as a series for divergence analysis"""
        close_col = 'Close' if 'Close' in df else 'close'
        delta = df[close_col].diff()
        
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.fillna(50)
    
    def detect_support_resistance_levels(self, df: pd.DataFrame, indicators: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        """
        Detect key support and resistance levels from EMAs and Bollinger Bands
        
        Returns:
            Dict with support and resistance level information
        """
        levels = {
            'support_levels': {
                'sma20': indicators['sma20'],
                'ema50': indicators['ema50'],
                'ema100': indicators['ema100'],
                'bb_lower': indicators['bb_lower']
            },
            'resistance_levels': {
                'sma20': indicators['sma20'],
                'ema50': indicators['ema50'], 
                'ema100': indicators['ema100'],
                'bb_upper': indicators['bb_upper']
            }
        }
        
        return levels

# Usage example and testing
if __name__ == "__main__":
    print("Enhanced Technical Analysis - Professional TXYZn indicator calculations")
    print("Includes EMA5, BBWidth rising detection, multi-period RSI, volume ratios, and EMA stack analysis")