"""
Data Service for HK Strategy Dashboard.
Handles data fetching from external sources, caching, and symbol management.

Extracted from dashboard.py lines 823-1134, 1135-1298
"""

import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import time

# Setup logging
logger = logging.getLogger(__name__)


class DataService:
    """Service for fetching and managing financial data."""
    
    def __init__(self, cache_enabled: bool = True, cache_ttl: int = 900):
        """
        Initialize the data service.
        
        Args:
            cache_enabled: Whether to enable caching
            cache_ttl: Cache time-to-live in seconds (default 15 minutes)
        """
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl
        
        # Fallback prices for Hong Kong stocks
        self.hk_fallback_prices = {
            "0005.HK": 100.10, "0316.HK": 140.50, "0388.HK": 447.60, "0700.HK": 599.00,
            "0823.HK": 41.26, "0857.HK": 7.39, "0939.HK": 7.49, "1810.HK": 53.20,
            "2888.HK": 144.50, "3690.HK": 116.30, "9618.HK": 121.30, "9988.HK": 121.50
        }
    
    def fetch_hk_price(self, hk_symbol: str) -> Tuple[float, str]:
        """
        Fetch current price for Hong Kong stock.
        
        Args:
            hk_symbol: HK stock symbol (e.g., "0700.HK")
            
        Returns:
            Tuple of (price, status_message)
        """
        try:
            stock = yf.Ticker(hk_symbol)
            
            # Try historical data first (more reliable)
            hist = stock.history(period="2d")
            if not hist.empty:
                price = float(hist['Close'].iloc[-1])
                return price, f"✅ {hk_symbol}: HK${price:.2f} (from history)"
            
            # Fall back to info data
            info = stock.info
            current_price = info.get('currentPrice', info.get('regularMarketPrice', info.get('previousClose')))
            if current_price and current_price > 0:
                price = float(current_price)
                return price, f"📈 {hk_symbol}: HK${price:.2f} (from info)"
                
            # Use fallback price if no data available
            fallback_price = self.hk_fallback_prices.get(hk_symbol, 75.0)
            return fallback_price, f"⚠️ {hk_symbol}: Using fallback price HK${fallback_price:.2f}"
            
        except Exception as e:
            logger.error(f"Error fetching price for {hk_symbol}: {str(e)}")
            price = self.hk_fallback_prices.get(hk_symbol, 75.0)
            return price, f"❌ {hk_symbol}: Error - using cached price HK${price:.2f}"
    
    def fetch_hk_historical_prices(self, hk_symbol: str) -> Tuple[float, float, str]:
        """
        Fetch current and previous day prices for Hong Kong stock.
        
        Args:
            hk_symbol: HK stock symbol (e.g., "0700.HK")
            
        Returns:
            Tuple of (current_price, previous_price, status_message)
        """
        try:
            stock = yf.Ticker(hk_symbol)
            hist = stock.history(period="5d")  # Get 5 days to ensure we have previous trading day
            
            if not hist.empty and len(hist) >= 2:
                current_price = float(hist['Close'].iloc[-1])
                previous_price = float(hist['Close'].iloc[-2])
                return current_price, previous_price, f"✅ {hk_symbol}: Current HK${current_price:.2f}, Previous HK${previous_price:.2f}"
            
            elif not hist.empty and len(hist) == 1:
                # Only one day available, use it for both
                price = float(hist['Close'].iloc[-1])
                return price, price, f"⚠️ {hk_symbol}: Only one day available HK${price:.2f}"
            
            else:
                # No historical data, fall back to info
                info = stock.info
                current_price = info.get('currentPrice', info.get('regularMarketPrice', info.get('previousClose')))
                if current_price and current_price > 0:
                    price = float(current_price)
                    # Estimate previous price as 99% of current (small realistic change)
                    prev_price = price * 0.99
                    return price, prev_price, f"📈 {hk_symbol}: Current HK${price:.2f}, Estimated Prev HK${prev_price:.2f}"
                else:
                    # Use fallback prices
                    fallback_price = self.hk_fallback_prices.get(hk_symbol, 75.0)
                    prev_fallback = fallback_price * 0.99
                    return fallback_price, prev_fallback, f"⚠️ {hk_symbol}: Using fallback prices"
            
        except Exception as e:
            logger.error(f"Error fetching historical prices for {hk_symbol}: {str(e)}")
            current_price = self.hk_fallback_prices.get(hk_symbol, 75.0)
            previous_price = current_price * 0.99  # Small realistic change
            return current_price, previous_price, f"❌ {hk_symbol}: Error - using cached prices"
    
    def get_company_name(self, symbol: str) -> str:
        """
        Try to fetch company name from Yahoo Finance.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Company name or 'Unknown Company' if not found
        """
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            return info.get('longName', info.get('shortName', 'Unknown Company'))
        except Exception as e:
            logger.error(f"Error fetching company name for {symbol}: {str(e)}")
            return 'Unknown Company'
    
    def validate_symbol_format(self, symbol: str) -> bool:
        """
        Validate stock symbol format.
        
        Args:
            symbol: Stock symbol to validate
            
        Returns:
            True if symbol format is valid
        """
        if not symbol:
            return False
        
        # Basic validation for HK symbols
        if '.HK' in symbol:
            return True
        
        # Basic validation for US symbols
        if symbol.isalpha() and len(symbol) <= 5:
            return True
        
        return False
    
    def convert_hk_symbol_format(self, symbol: str) -> str:
        """
        Convert between HK symbol formats (e.g., 0005.HK <-> 5.HK).
        
        Args:
            symbol: HK symbol to convert
            
        Returns:
            Converted symbol
        """
        if not symbol.endswith('.HK'):
            return symbol
        
        base_symbol = symbol.replace('.HK', '')
        
        # If it's a number with leading zeros, remove them
        try:
            numeric_part = int(base_symbol)
            return f"{numeric_part}.HK"
        except ValueError:
            return symbol
    
    def fetch_and_store_yahoo_data(self, symbol: str, start_date: str, end_date: str, db_manager=None) -> Tuple[bool, str]:
        """
        Fetch data from Yahoo Finance and store in database if missing.
        
        Args:
            symbol: Stock symbol
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            db_manager: Database manager instance
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if not db_manager:
                return False, "Database manager not provided"
            
            # Check existing data coverage in database
            conn = db_manager.get_connection()
            if not conn:
                return False, "Failed to get database connection"
            
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT MIN(trade_date), MAX(trade_date), COUNT(*)
                    FROM daily_equity_technicals
                    WHERE symbol = %s
                      AND trade_date >= %s
                      AND trade_date <= %s
                """, (symbol, start_date, end_date))
                
                result = cur.fetchone()
                existing_start, existing_end, count = result
                
                # Convert dates to datetime objects
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                
                # Calculate expected trading days (rough estimate)
                expected_days = (end_dt - start_dt).days
                data_coverage = count / max(expected_days * 0.7, 1)  # Assume ~70% are trading days
                
                needs_fetching = False
                if count == 0 or data_coverage < 0.8:  # Less than 80% coverage
                    needs_fetching = True
                elif existing_start is None or existing_end is None:
                    needs_fetching = True
                elif existing_start > start_dt.date() or existing_end < end_dt.date():
                    needs_fetching = True
                
                if needs_fetching:
                    # Fetch data from Yahoo Finance
                    logger.info(f"Fetching data for {symbol} from Yahoo Finance...")
                    
                    ticker = yf.Ticker(symbol)
                    hist_data = ticker.history(start=start_dt, end=end_dt + timedelta(days=1))
                    
                    if not hist_data.empty:
                        # Import technical indicators (will be moved to technical_indicators.py later)
                        from .technical_indicators import calculate_rsi
                        
                        # Calculate technical indicators
                        hist_data['rsi_14'] = calculate_rsi(hist_data['Close'], 14)
                        
                        # Store data in database
                        inserted_count = 0
                        for date, row in hist_data.iterrows():
                            # Convert to database format
                            trade_date = date.date()
                            open_price = self._convert_for_database(row['Open'])
                            high_price = self._convert_for_database(row['High'])
                            low_price = self._convert_for_database(row['Low'])
                            close_price = self._convert_for_database(row['Close'])
                            volume = self._convert_for_database(row['Volume'])
                            rsi_14 = self._convert_for_database(row['rsi_14'])
                            
                            # Insert or update record
                            cur.execute("""
                                INSERT INTO daily_equity_technicals 
                                (symbol, trade_date, open_price, high_price, low_price, close_price, volume, rsi_14)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (symbol, trade_date) 
                                DO UPDATE SET
                                    open_price = EXCLUDED.open_price,
                                    high_price = EXCLUDED.high_price,
                                    low_price = EXCLUDED.low_price,
                                    close_price = EXCLUDED.close_price,
                                    volume = EXCLUDED.volume,
                                    rsi_14 = EXCLUDED.rsi_14,
                                    updated_at = CURRENT_TIMESTAMP
                            """, (symbol, trade_date, open_price, high_price, low_price, close_price, volume, rsi_14))
                            
                            inserted_count += 1
                        
                        conn.commit()
                        return True, f"Successfully fetched and stored {inserted_count} records for {symbol}"
                    
                    else:
                        return False, f"No data available for {symbol} in the specified date range"
                
                else:
                    return True, f"Data for {symbol} already exists and is sufficient (coverage: {data_coverage:.1%})"
        
        except Exception as e:
            logger.error(f"Error fetching and storing data for {symbol}: {str(e)}")
            return False, f"Error: {str(e)}"
        
        finally:
            if conn:
                conn.close()
    
    def _convert_for_database(self, value: Any) -> Optional[float]:
        """
        Convert Python values to database-compatible format.
        
        Args:
            value: Value to convert
            
        Returns:
            Converted value or None
        """
        if pd.isna(value) or value is None:
            return None
        
        if isinstance(value, (int, float)):
            if np.isfinite(value):
                return float(value)
            else:
                return None
        
        try:
            converted = float(value)
            if np.isfinite(converted):
                return converted
            else:
                return None
        except (ValueError, TypeError):
            return None
    
    def get_cached_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get cached price data with expiration check.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Cached price data or None if expired/not found
        """
        if not self.cache_enabled:
            return None
        
        # Use session state manager's cache functionality
        if 'src.dashboard.state_manager' in globals():
            from src.dashboard.state_manager import get_cached_price_data
            return get_cached_price_data(symbol)
        
        return None
    
    def cache_price_data(self, symbol: str, price_data: Dict[str, Any]) -> None:
        """
        Cache price data with timestamp.
        
        Args:
            symbol: Stock symbol
            price_data: Price data to cache
        """
        if not self.cache_enabled:
            return
        
        # Use session state manager's cache functionality
        if 'src.dashboard.state_manager' in globals():
            from src.dashboard.state_manager import cache_price_data
            cache_price_data(symbol, price_data, self.cache_ttl // 60)


# Convenience functions for backward compatibility
def fetch_hk_price(hk_symbol: str) -> Tuple[float, str]:
    """Fetch current price for Hong Kong stock."""
    service = DataService()
    return service.fetch_hk_price(hk_symbol)

def fetch_hk_historical_prices(hk_symbol: str) -> Tuple[float, float, str]:
    """Fetch current and previous day prices for Hong Kong stock."""
    service = DataService()
    return service.fetch_hk_historical_prices(hk_symbol)

def get_company_name(symbol: str) -> str:
    """Try to fetch company name from Yahoo Finance."""
    service = DataService()
    return service.get_company_name(symbol)

def fetch_and_store_yahoo_data(symbol: str, start_date: str, end_date: str) -> Tuple[bool, str]:
    """Fetch data from Yahoo Finance and store in database if missing."""
    # Get database manager from session state
    db_manager = st.session_state.get('db_manager') if 'st' in globals() and hasattr(st, 'session_state') else None
    service = DataService()
    return service.fetch_and_store_yahoo_data(symbol, start_date, end_date, db_manager)

def convert_for_database(value: Any) -> Optional[float]:
    """Convert Python values to database-compatible format."""
    service = DataService()
    return service._convert_for_database(value)