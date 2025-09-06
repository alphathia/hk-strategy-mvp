"""
Technical Indicators Service for HK Strategy Dashboard.
Handles calculation of various technical analysis indicators.

Extracted from dashboard.py lines 1299-1398
"""

import pandas as pd
import numpy as np
import streamlit as st
import logging
from typing import Tuple, Optional, List, Dict, Any

# Setup logging
logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """Service for calculating technical analysis indicators."""
    
    def __init__(self):
        """Initialize the technical indicators service."""
        self.available_indicators = [
            ("RSI (7)", "rsi_7"),
            ("RSI (14)", "rsi_14"), 
            ("RSI (21)", "rsi_21"),
            ("MACD", "macd"),
            ("MACD Signal", "macd_signal"),
            ("SMA (20)", "sma_20"),
            ("EMA (12)", "ema_12"),
            ("EMA (26)", "ema_26"),
            ("EMA (50)", "ema_50"),
            ("Bollinger Upper", "bb_upper"),
            ("Bollinger Lower", "bb_lower")
        ]
    
    def calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """
        Calculate RSI indicator with enhanced error handling.
        
        Args:
            prices: Price series
            window: Period for RSI calculation (default 14)
            
        Returns:
            RSI series or None if calculation fails
        """
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
            
            # Handle division by zero more carefully
            # Replace zero losses with a small value to avoid infinite RS values
            loss = loss.replace(0, np.nan)
            rs = gain / loss
            
            # Handle infinite and NaN values before final calculation
            rs = rs.replace([np.inf, -np.inf], np.nan)
            
            # Calculate RSI, handling NaN values
            rsi = 100 - (100 / (1 + rs))
            
            # Clean up any remaining problematic values
            rsi = rsi.replace([np.inf, -np.inf], np.nan)
            
            return rsi
            
        except Exception as e:
            logger.error(f"RSI calculation error: {str(e)}")
            
            # Enhanced error reporting in debug mode
            try:
                if hasattr(st, 'session_state') and st.session_state.get('debug_mode', False):
                    st.error(f"🔍 Debug RSI Error: {str(e)}")
                    st.error(f"🔍 Debug RSI Prices Shape: {prices.shape if hasattr(prices, 'shape') else 'No shape'}")
                    st.error(f"🔍 Debug RSI Prices Type: {type(prices)}")
            except:
                pass
            
            return None
    
    def calculate_rsi_realtime(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate RSI with configurable period for real-time use.
        
        Args:
            prices: Price series
            period: Period for RSI calculation
            
        Returns:
            RSI series
        """
        try:
            delta = prices.diff()
            gain = delta.clip(lower=0)  # Positive price changes
            loss = -delta.clip(upper=0)  # Negative price changes (made positive)
            avg_gain = gain.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
            avg_loss = loss.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
            rs = avg_gain / avg_loss.replace(0, np.nan)
            rsi = 100 - (100 / (1 + rs))
            return rsi.fillna(50)
        except Exception as e:
            logger.error(f"Real-time RSI calculation error: {str(e)}")
            return pd.Series([50] * len(prices), index=prices.index)
    
    def calculate_macd_realtime(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate MACD with configurable parameters for real-time use.
        
        Args:
            prices: Price series
            fast: Fast EMA period (default 12)
            slow: Slow EMA period (default 26)
            signal: Signal line EMA period (default 9)
            
        Returns:
            Tuple of (macd_line, signal_line, histogram)
        """
        try:
            ema_fast = prices.ewm(span=fast, adjust=False, min_periods=fast).mean()
            ema_slow = prices.ewm(span=slow, adjust=False, min_periods=slow).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal, adjust=False, min_periods=signal).mean()
            histogram = macd_line - signal_line
            return macd_line, signal_line, histogram
        except Exception as e:
            logger.error(f"MACD calculation error: {str(e)}")
            # Return zeros if calculation fails
            zeros = pd.Series([0] * len(prices), index=prices.index)
            return zeros, zeros, zeros
    
    def calculate_ema_realtime(self, prices: pd.Series, period: int) -> pd.Series:
        """
        Calculate EMA with configurable period for real-time use.
        
        Args:
            prices: Price series
            period: EMA period
            
        Returns:
            EMA series
        """
        try:
            ema = prices.ewm(span=period, adjust=False, min_periods=period).mean()
            return ema
        except Exception as e:
            logger.error(f"EMA calculation error: {str(e)}")
            # Return original prices if calculation fails
            return prices
    
    def calculate_sma(self, prices: pd.Series, window: int) -> pd.Series:
        """
        Calculate Simple Moving Average.
        
        Args:
            prices: Price series
            window: SMA window period
            
        Returns:
            SMA series
        """
        try:
            return prices.rolling(window=window).mean()
        except Exception as e:
            logger.error(f"SMA calculation error: {str(e)}")
            return prices
    
    def calculate_bollinger_bands(self, prices: pd.Series, window: int = 20, num_std: int = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands.
        
        Args:
            prices: Price series
            window: Moving average window (default 20)
            num_std: Number of standard deviations (default 2)
            
        Returns:
            Tuple of (upper_band, middle_band, lower_band)
        """
        try:
            middle_band = prices.rolling(window=window).mean()
            std = prices.rolling(window=window).std()
            upper_band = middle_band + (std * num_std)
            lower_band = middle_band - (std * num_std)
            return upper_band, middle_band, lower_band
        except Exception as e:
            logger.error(f"Bollinger Bands calculation error: {str(e)}")
            # Return original prices for all bands if calculation fails
            return prices, prices, prices
    
    def calculate_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
        """
        Calculate Stochastic Oscillator.
        
        Args:
            high: High price series
            low: Low price series
            close: Close price series
            k_period: %K period (default 14)
            d_period: %D smoothing period (default 3)
            
        Returns:
            Tuple of (%K, %D)
        """
        try:
            lowest_low = low.rolling(window=k_period).min()
            highest_high = high.rolling(window=k_period).max()
            k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
            d_percent = k_percent.rolling(window=d_period).mean()
            return k_percent, d_percent
        except Exception as e:
            logger.error(f"Stochastic calculation error: {str(e)}")
            zeros = pd.Series([0] * len(close), index=close.index)
            return zeros, zeros
    
    def get_available_indicators(self) -> List[Tuple[str, str]]:
        """
        Get list of available technical indicators.
        
        Returns:
            List of (display_name, indicator_key) tuples
        """
        return self.available_indicators.copy()
    
    def calculate_indicator(self, indicator_key: str, data: Dict[str, pd.Series], **params) -> Optional[pd.Series]:
        """
        Calculate a specific indicator based on key.
        
        Args:
            indicator_key: Indicator key (e.g., "rsi_14", "macd", etc.)
            data: Dictionary containing price data (close, high, low, volume)
            **params: Additional parameters for indicator calculation
            
        Returns:
            Calculated indicator series or None
        """
        try:
            close_prices = data.get('close', data.get('Close'))
            if close_prices is None:
                logger.error(f"No close price data available for {indicator_key}")
                return None
            
            if indicator_key.startswith('rsi_'):
                period = int(indicator_key.split('_')[1])
                return self.calculate_rsi(close_prices, window=period)
            
            elif indicator_key == 'macd':
                macd_line, _, _ = self.calculate_macd_realtime(close_prices)
                return macd_line
            
            elif indicator_key == 'macd_signal':
                _, signal_line, _ = self.calculate_macd_realtime(close_prices)
                return signal_line
            
            elif indicator_key.startswith('sma_'):
                period = int(indicator_key.split('_')[1])
                return self.calculate_sma(close_prices, window=period)
            
            elif indicator_key.startswith('ema_'):
                period = int(indicator_key.split('_')[1])
                return self.calculate_ema_realtime(close_prices, period=period)
            
            elif indicator_key == 'bb_upper':
                upper, _, _ = self.calculate_bollinger_bands(close_prices)
                return upper
            
            elif indicator_key == 'bb_lower':
                _, _, lower = self.calculate_bollinger_bands(close_prices)
                return lower
            
            else:
                logger.warning(f"Unknown indicator key: {indicator_key}")
                return None
                
        except Exception as e:
            logger.error(f"Error calculating indicator {indicator_key}: {str(e)}")
            return None
    
    def calculate_multiple_indicators(self, indicator_keys: List[str], data: Dict[str, pd.Series]) -> Dict[str, pd.Series]:
        """
        Calculate multiple indicators at once.
        
        Args:
            indicator_keys: List of indicator keys to calculate
            data: Dictionary containing price data
            
        Returns:
            Dictionary of calculated indicators
        """
        results = {}
        for key in indicator_keys:
            result = self.calculate_indicator(key, data)
            if result is not None:
                results[key] = result
        return results
    
    def get_current_indicator_value(self, indicator_key: str, data: Dict[str, pd.Series]) -> Optional[float]:
        """
        Get the current (most recent) value of an indicator.
        
        Args:
            indicator_key: Indicator key
            data: Dictionary containing price data
            
        Returns:
            Current indicator value or None
        """
        try:
            indicator_series = self.calculate_indicator(indicator_key, data)
            if indicator_series is not None and not indicator_series.empty:
                return float(indicator_series.iloc[-1])
            return None
        except Exception as e:
            logger.error(f"Error getting current value for {indicator_key}: {str(e)}")
            return None
    
    def validate_indicator_params(self, indicator: str, params: Dict[str, Any]) -> bool:
        """
        Validate technical indicator parameters.
        
        Args:
            indicator: Indicator name
            params: Parameters to validate
            
        Returns:
            True if parameters are valid
        """
        try:
            # Basic validation for common parameters
            if 'period' in params or 'window' in params:
                period = params.get('period', params.get('window', 14))
                if not isinstance(period, int) or period <= 0:
                    return False
            
            if indicator.lower() == 'macd':
                fast = params.get('fast', 12)
                slow = params.get('slow', 26)
                signal = params.get('signal', 9)
                if not all(isinstance(x, int) and x > 0 for x in [fast, slow, signal]):
                    return False
                if fast >= slow:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating indicator params for {indicator}: {str(e)}")
            return False


# Convenience functions for backward compatibility
def calculate_rsi(prices: pd.Series, window: int = 14) -> pd.Series:
    """Calculate RSI indicator with enhanced error handling."""
    service = TechnicalIndicators()
    return service.calculate_rsi(prices, window)

def calculate_rsi_realtime(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI with configurable period for real-time use."""
    service = TechnicalIndicators()
    return service.calculate_rsi_realtime(prices, period)

def calculate_macd_realtime(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate MACD with configurable parameters for real-time use."""
    service = TechnicalIndicators()
    return service.calculate_macd_realtime(prices, fast, slow, signal)

def calculate_ema_realtime(prices: pd.Series, period: int) -> pd.Series:
    """Calculate EMA with configurable period for real-time use."""
    service = TechnicalIndicators()
    return service.calculate_ema_realtime(prices, period)