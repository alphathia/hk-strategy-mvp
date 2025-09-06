"""
Technical Indicators Calculation Utilities.

Functions for calculating various technical indicators.
Extracted from dashboard.py for modular architecture.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime, date

from src.database.connection import get_connection

logger = logging.getLogger(__name__)


def calculate_rsi(prices: pd.Series, window: int = 14) -> pd.Series:
    """
    Calculate RSI indicator with enhanced error handling.
    
    Args:
        prices: Series of closing prices
        window: RSI calculation window
        
    Returns:
        RSI values as pandas Series
    """
    try:
        if len(prices) < window + 1:
            logger.warning(f"Insufficient data for RSI calculation: need {window + 1}, got {len(prices)}")
            return pd.Series(dtype=float)
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.fillna(50)  # Neutral RSI for NaN values
        
    except Exception as e:
        logger.error(f"Error calculating RSI: {e}")
        return pd.Series(dtype=float)


def calculate_rsi_realtime(prices: pd.Series, period: int = 14) -> Optional[float]:
    """
    Calculate RSI with configurable period for real-time use.
    
    Args:
        prices: Series of closing prices
        period: RSI calculation period
        
    Returns:
        Current RSI value or None
    """
    try:
        rsi_series = calculate_rsi(prices, window=period)
        if not rsi_series.empty:
            return float(rsi_series.iloc[-1])
        return None
        
    except Exception as e:
        logger.error(f"Error calculating real-time RSI: {e}")
        return None


def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
    """
    Calculate MACD indicator.
    
    Args:
        prices: Series of closing prices
        fast: Fast EMA period
        slow: Slow EMA period
        signal: Signal line EMA period
        
    Returns:
        Dictionary with MACD, signal, and histogram series
    """
    try:
        if len(prices) < slow + signal:
            logger.warning(f"Insufficient data for MACD calculation")
            return {'macd': pd.Series(dtype=float), 'signal': pd.Series(dtype=float), 'histogram': pd.Series(dtype=float)}
        
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
        
    except Exception as e:
        logger.error(f"Error calculating MACD: {e}")
        return {'macd': pd.Series(dtype=float), 'signal': pd.Series(dtype=float), 'histogram': pd.Series(dtype=float)}


def calculate_macd_realtime(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Optional[Dict[str, float]]:
    """
    Calculate MACD with configurable parameters for real-time use.
    
    Args:
        prices: Series of closing prices
        fast: Fast EMA period
        slow: Slow EMA period
        signal: Signal line EMA period
        
    Returns:
        Dictionary with current MACD values or None
    """
    try:
        macd_data = calculate_macd(prices, fast, slow, signal)
        
        if not macd_data['macd'].empty:
            return {
                'macd': float(macd_data['macd'].iloc[-1]),
                'signal': float(macd_data['signal'].iloc[-1]),
                'histogram': float(macd_data['histogram'].iloc[-1])
            }
        return None
        
    except Exception as e:
        logger.error(f"Error calculating real-time MACD: {e}")
        return None


def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
    """
    Calculate Exponential Moving Average.
    
    Args:
        prices: Series of closing prices
        period: EMA period
        
    Returns:
        EMA values as pandas Series
    """
    try:
        if len(prices) < period:
            logger.warning(f"Insufficient data for EMA calculation")
            return pd.Series(dtype=float)
        
        return prices.ewm(span=period).mean()
        
    except Exception as e:
        logger.error(f"Error calculating EMA: {e}")
        return pd.Series(dtype=float)


def calculate_ema_realtime(prices: pd.Series, period: int) -> Optional[float]:
    """
    Calculate EMA with configurable period for real-time use.
    
    Args:
        prices: Series of closing prices
        period: EMA period
        
    Returns:
        Current EMA value or None
    """
    try:
        ema_series = calculate_ema(prices, period)
        if not ema_series.empty:
            return float(ema_series.iloc[-1])
        return None
        
    except Exception as e:
        logger.error(f"Error calculating real-time EMA: {e}")
        return None


def calculate_sma(prices: pd.Series, period: int) -> pd.Series:
    """
    Calculate Simple Moving Average.
    
    Args:
        prices: Series of closing prices
        period: SMA period
        
    Returns:
        SMA values as pandas Series
    """
    try:
        if len(prices) < period:
            logger.warning(f"Insufficient data for SMA calculation")
            return pd.Series(dtype=float)
        
        return prices.rolling(window=period).mean()
        
    except Exception as e:
        logger.error(f"Error calculating SMA: {e}")
        return pd.Series(dtype=float)


def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: float = 2) -> Dict[str, pd.Series]:
    """
    Calculate Bollinger Bands.
    
    Args:
        prices: Series of closing prices
        period: Moving average period
        std_dev: Standard deviation multiplier
        
    Returns:
        Dictionary with upper, middle, and lower band series
    """
    try:
        if len(prices) < period:
            logger.warning(f"Insufficient data for Bollinger Bands calculation")
            return {'upper': pd.Series(dtype=float), 'middle': pd.Series(dtype=float), 'lower': pd.Series(dtype=float)}
        
        middle_band = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)
        
        return {
            'upper': upper_band,
            'middle': middle_band,
            'lower': lower_band
        }
        
    except Exception as e:
        logger.error(f"Error calculating Bollinger Bands: {e}")
        return {'upper': pd.Series(dtype=float), 'middle': pd.Series(dtype=float), 'lower': pd.Series(dtype=float)}


def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, 
                        k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
    """
    Calculate Stochastic Oscillator.
    
    Args:
        high: Series of high prices
        low: Series of low prices
        close: Series of closing prices
        k_period: %K period
        d_period: %D period
        
    Returns:
        Dictionary with %K and %D series
    """
    try:
        if len(close) < k_period:
            logger.warning(f"Insufficient data for Stochastic calculation")
            return {'%K': pd.Series(dtype=float), '%D': pd.Series(dtype=float)}
        
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        
        k_percent = 100 * (close - lowest_low) / (highest_high - lowest_low)
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return {
            '%K': k_percent,
            '%D': d_percent
        }
        
    except Exception as e:
        logger.error(f"Error calculating Stochastic: {e}")
        return {'%K': pd.Series(dtype=float), '%D': pd.Series(dtype=float)}


def fetch_technical_analysis_data(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Fetch technical analysis data from daily_equity_technicals table.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Dictionary with technical data or None
    """
    try:
        conn = get_connection()
        if not conn:
            return get_fallback_technical_data(symbol)
            
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT date, close_price, rsi_14, macd, macd_signal, 
                       sma_20, sma_50, ema_12, ema_26,
                       bollinger_upper, bollinger_middle, bollinger_lower,
                       volume
                FROM daily_equity_technicals 
                WHERE symbol = %s 
                ORDER BY date DESC 
                LIMIT 100
            """, (symbol,))
            
            results = cursor.fetchall()
            if results:
                return {
                    'dates': [row['date'] for row in results],
                    'close_prices': [float(row['close_price']) for row in results],
                    'rsi_14': [float(row['rsi_14']) if row['rsi_14'] else None for row in results],
                    'macd': [float(row['macd']) if row['macd'] else None for row in results],
                    'macd_signal': [float(row['macd_signal']) if row['macd_signal'] else None for row in results],
                    'sma_20': [float(row['sma_20']) if row['sma_20'] else None for row in results],
                    'sma_50': [float(row['sma_50']) if row['sma_50'] else None for row in results],
                    'volume': [int(row['volume']) for row in results]
                }
        
        # Fallback if no database data
        return get_fallback_technical_data(symbol)
        
    except Exception as e:
        logger.error(f"Error fetching technical data for {symbol}: {e}")
        return get_fallback_technical_data(symbol)


def get_fallback_technical_data(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Provide fallback technical data when database data is unavailable.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Dictionary with calculated technical indicators or None
    """
    try:
        import yfinance as yf
        
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="3mo")  # 3 months of data
        
        if hist.empty:
            return None
        
        close_prices = hist['Close']
        high_prices = hist['High']
        low_prices = hist['Low']
        
        # Calculate indicators
        rsi = calculate_rsi(close_prices)
        macd_data = calculate_macd(close_prices)
        sma_20 = calculate_sma(close_prices, 20)
        sma_50 = calculate_sma(close_prices, 50)
        bollinger = calculate_bollinger_bands(close_prices)
        
        return {
            'dates': hist.index.tolist(),
            'close_prices': close_prices.tolist(),
            'rsi_14': rsi.tolist(),
            'macd': macd_data['macd'].tolist(),
            'macd_signal': macd_data['signal'].tolist(),
            'sma_20': sma_20.tolist(),
            'sma_50': sma_50.tolist(),
            'bollinger_upper': bollinger['upper'].tolist(),
            'bollinger_middle': bollinger['middle'].tolist(),
            'bollinger_lower': bollinger['lower'].tolist(),
            'volume': hist['Volume'].tolist()
        }
        
    except Exception as e:
        logger.error(f"Error calculating fallback technical data for {symbol}: {e}")
        return None


def get_available_indicators() -> List[Tuple[str, str]]:
    """
    Get list of available technical indicators.
    
    Returns:
        List of (display_name, indicator_code) tuples
    """
    return [
        ("RSI (14)", "rsi_14"),
        ("MACD", "macd"),
        ("MACD Signal", "macd_signal"),
        ("SMA (20)", "sma_20"),
        ("SMA (50)", "sma_50"),
        ("EMA (12)", "ema_12"),
        ("EMA (26)", "ema_26"),
        ("Bollinger Upper", "bollinger_upper"),
        ("Bollinger Middle", "bollinger_middle"),
        ("Bollinger Lower", "bollinger_lower"),
        ("Stochastic %K", "stoch_k"),
        ("Stochastic %D", "stoch_d"),
        ("Volume", "volume")
    ]


def validate_indicator_selection(selected_indicators: List[str], max_selection: int = 3) -> Tuple[bool, str]:
    """
    Validate indicator selection.
    
    Args:
        selected_indicators: List of selected indicator codes
        max_selection: Maximum number of indicators allowed
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    available_codes = [code for _, code in get_available_indicators()]
    
    if len(selected_indicators) > max_selection:
        return False, f"Maximum {max_selection} indicators allowed"
    
    for indicator in selected_indicators:
        if indicator not in available_codes:
            return False, f"Invalid indicator: {indicator}"
    
    return True, ""


def calculate_indicator_signals(symbol: str, indicators: List[str]) -> Dict[str, Any]:
    """
    Calculate trading signals based on selected indicators.
    
    Args:
        symbol: Stock symbol
        indicators: List of indicator codes
        
    Returns:
        Dictionary with signal analysis
    """
    try:
        tech_data = fetch_technical_analysis_data(symbol)
        if not tech_data:
            return {'signals': [], 'overall': 'NEUTRAL'}
        
        signals = []
        bullish_count = 0
        bearish_count = 0
        
        # RSI signals
        if 'rsi_14' in indicators and tech_data.get('rsi_14'):
            current_rsi = tech_data['rsi_14'][0] if tech_data['rsi_14'][0] else 50
            if current_rsi < 30:
                signals.append(('RSI', 'BULLISH', 'Oversold condition'))
                bullish_count += 1
            elif current_rsi > 70:
                signals.append(('RSI', 'BEARISH', 'Overbought condition'))
                bearish_count += 1
            else:
                signals.append(('RSI', 'NEUTRAL', f'RSI at {current_rsi:.1f}'))
        
        # MACD signals
        if 'macd' in indicators and tech_data.get('macd') and tech_data.get('macd_signal'):
            current_macd = tech_data['macd'][0] if tech_data['macd'][0] else 0
            current_signal = tech_data['macd_signal'][0] if tech_data['macd_signal'][0] else 0
            
            if current_macd > current_signal:
                signals.append(('MACD', 'BULLISH', 'MACD above signal line'))
                bullish_count += 1
            else:
                signals.append(('MACD', 'BEARISH', 'MACD below signal line'))
                bearish_count += 1
        
        # Moving average signals
        if 'sma_20' in indicators and 'sma_50' in indicators:
            sma_20 = tech_data.get('sma_20', [None])[0]
            sma_50 = tech_data.get('sma_50', [None])[0]
            
            if sma_20 and sma_50:
                if sma_20 > sma_50:
                    signals.append(('SMA Cross', 'BULLISH', 'SMA20 above SMA50'))
                    bullish_count += 1
                else:
                    signals.append(('SMA Cross', 'BEARISH', 'SMA20 below SMA50'))
                    bearish_count += 1
        
        # Overall signal
        if bullish_count > bearish_count:
            overall = 'BULLISH'
        elif bearish_count > bullish_count:
            overall = 'BEARISH'
        else:
            overall = 'NEUTRAL'
        
        return {
            'signals': signals,
            'overall': overall,
            'bullish_count': bullish_count,
            'bearish_count': bearish_count
        }
        
    except Exception as e:
        logger.error(f"Error calculating indicator signals for {symbol}: {e}")
        return {'signals': [], 'overall': 'NEUTRAL'}