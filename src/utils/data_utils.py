"""
Data Processing and Fetching Utilities.

Utility functions for data fetching, processing, and validation.
Extracted from dashboard.py for modular architecture.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
import logging
import time

from src.database.connection import get_connection

logger = logging.getLogger(__name__)


def fetch_hk_price(hk_symbol: str) -> Optional[float]:
    """
    Fetch current price for Hong Kong stock.
    
    Args:
        hk_symbol: Hong Kong stock symbol (e.g., '0700.HK')
        
    Returns:
        Current price or None if unavailable
    """
    try:
        ticker = yf.Ticker(hk_symbol)
        info = ticker.info
        
        # Try multiple price fields
        price = (info.get('currentPrice') or 
                info.get('regularMarketPrice') or 
                info.get('previousClose'))
                
        if price and isinstance(price, (int, float)) and price > 0:
            return float(price)
            
        logger.warning(f"No valid price found for {hk_symbol}")
        return None
        
    except Exception as e:
        logger.error(f"Error fetching price for {hk_symbol}: {e}")
        return None


def fetch_hk_historical_prices(hk_symbol: str, days: int = 2) -> Dict[str, float]:
    """
    Fetch current and previous day prices for Hong Kong stock.
    
    Args:
        hk_symbol: Hong Kong stock symbol
        days: Number of days to fetch
        
    Returns:
        Dictionary with current and previous prices
    """
    try:
        ticker = yf.Ticker(hk_symbol)
        hist = ticker.history(period=f"{days}d")
        
        if len(hist) >= 2:
            current_price = float(hist['Close'].iloc[-1])
            previous_price = float(hist['Close'].iloc[-2])
            
            return {
                'current': current_price,
                'previous': previous_price,
                'change': current_price - previous_price,
                'change_percent': ((current_price - previous_price) / previous_price) * 100
            }
        else:
            logger.warning(f"Insufficient historical data for {hk_symbol}")
            return {}
            
    except Exception as e:
        logger.error(f"Error fetching historical prices for {hk_symbol}: {e}")
        return {}


def get_company_name(symbol: str) -> str:
    """
    Try to fetch company name from Yahoo Finance.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Company name or 'Unknown Company' if not found
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Try multiple name fields
        company_name = (info.get('longName') or 
                       info.get('shortName') or 
                       info.get('displayName', '').strip())
        
        if company_name:
            return company_name
        
        # Fallback for HK stocks
        if symbol.endswith('.HK'):
            code = symbol.replace('.HK', '')
            return f"HK Stock {code}"
            
        return 'Unknown Company'
        
    except Exception as e:
        logger.error(f"Error fetching company name for {symbol}: {e}")
        return 'Unknown Company'


def fetch_and_store_yahoo_data(symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
    """
    Fetch data from Yahoo Finance and store in database if missing.
    
    Args:
        symbol: Stock symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        
    Returns:
        DataFrame with OHLCV data or None
    """
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(start=start_date, end=end_date)
        
        if data.empty:
            logger.warning(f"No data available for {symbol} from {start_date} to {end_date}")
            return None
        
        # Store in database (implementation depends on schema)
        # This would need to be implemented based on your database structure
        logger.info(f"Fetched {len(data)} records for {symbol}")
        
        return data
        
    except Exception as e:
        logger.error(f"Error fetching Yahoo data for {symbol}: {e}")
        return None


def get_portfolio_data(portfolio_id: str) -> Optional[Dict[str, Any]]:
    """
    Get portfolio data from database.
    
    Args:
        portfolio_id: Portfolio identifier
        
    Returns:
        Portfolio data or None
    """
    try:
        conn = get_connection()
        if not conn:
            return None
            
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM portfolios 
                WHERE portfolio_id = %s
            """, (portfolio_id,))
            
            result = cursor.fetchone()
            if result:
                # Convert to dictionary (adjust based on your schema)
                return dict(result)
                
        return None
        
    except Exception as e:
        logger.error(f"Error fetching portfolio {portfolio_id}: {e}")
        return None


def get_all_portfolios_for_equity_analysis() -> List[Dict[str, Any]]:
    """
    Get all available portfolios for equity analysis selection.
    
    Returns:
        List of portfolio dictionaries
    """
    try:
        conn = get_connection()
        if not conn:
            return []
            
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT portfolio_id, name, description 
                FROM portfolios 
                ORDER BY name
            """)
            
            results = cursor.fetchall()
            return [dict(row) for row in results]
            
    except Exception as e:
        logger.error(f"Error fetching portfolios: {e}")
        return []


def get_portfolio_analyses_for_equity(portfolio_id: str) -> List[Dict[str, Any]]:
    """
    Get all portfolio analyses for a specific portfolio.
    
    Args:
        portfolio_id: Portfolio identifier
        
    Returns:
        List of analysis dictionaries
    """
    try:
        conn = get_connection()
        if not conn:
            return []
            
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM portfolio_analyses 
                WHERE portfolio_id = %s 
                ORDER BY analysis_date DESC
            """, (portfolio_id,))
            
            results = cursor.fetchall()
            return [dict(row) for row in results]
            
    except Exception as e:
        logger.error(f"Error fetching analyses for portfolio {portfolio_id}: {e}")
        return []


def get_equities_from_portfolio(portfolio_id: str) -> List[Dict[str, Any]]:
    """
    Get all equities/symbols from a specific portfolio (both active and inactive positions).
    
    Args:
        portfolio_id: Portfolio identifier
        
    Returns:
        List of equity dictionaries
    """
    try:
        conn = get_connection()
        if not conn:
            return []
            
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT symbol, company_name, quantity, avg_cost, sector
                FROM portfolio_positions 
                WHERE portfolio_id = %s 
                ORDER BY symbol
            """, (portfolio_id,))
            
            results = cursor.fetchall()
            return [dict(row) for row in results]
            
    except Exception as e:
        logger.error(f"Error fetching equities for portfolio {portfolio_id}: {e}")
        return []


def get_analysis_period_for_equity(analysis_id: int) -> Optional[Tuple[date, date]]:
    """
    Get the analysis period (start_date, end_date) for a specific analysis.
    
    Args:
        analysis_id: Analysis identifier
        
    Returns:
        Tuple of (start_date, end_date) or None
    """
    try:
        conn = get_connection()
        if not conn:
            return None
            
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT start_date, end_date 
                FROM portfolio_analyses 
                WHERE analysis_id = %s
            """, (analysis_id,))
            
            result = cursor.fetchone()
            if result:
                return (result['start_date'], result['end_date'])
                
        return None
        
    except Exception as e:
        logger.error(f"Error fetching analysis period for {analysis_id}: {e}")
        return None


def fetch_equity_prices_by_date(symbol: str, target_date: date) -> Optional[Dict[str, float]]:
    """
    Fetch OHLCV data for a specific symbol and date from daily_equity_technicals table.
    
    Args:
        symbol: Stock symbol
        target_date: Target date
        
    Returns:
        Dictionary with OHLCV data or None
    """
    try:
        conn = get_connection()
        if not conn:
            return get_yahoo_finance_price_fallback(symbol, target_date)
            
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT open_price, high_price, low_price, close_price, volume
                FROM daily_equity_technicals 
                WHERE symbol = %s AND date = %s
            """, (symbol, target_date))
            
            result = cursor.fetchone()
            if result:
                return {
                    'open': float(result['open_price']),
                    'high': float(result['high_price']),
                    'low': float(result['low_price']),
                    'close': float(result['close_price']),
                    'volume': int(result['volume'])
                }
        
        # Fallback to Yahoo Finance
        return get_yahoo_finance_price_fallback(symbol, target_date)
        
    except Exception as e:
        logger.error(f"Error fetching equity prices for {symbol} on {target_date}: {e}")
        return get_yahoo_finance_price_fallback(symbol, target_date)


def get_yahoo_finance_price_fallback(symbol: str, target_date: date) -> Optional[Dict[str, float]]:
    """
    Fallback to Yahoo Finance for specific date price data.
    
    Args:
        symbol: Stock symbol
        target_date: Target date
        
    Returns:
        Dictionary with OHLCV data or None
    """
    try:
        ticker = yf.Ticker(symbol)
        end_date = target_date + timedelta(days=1)
        start_date = target_date - timedelta(days=5)  # Get some buffer
        
        hist = ticker.history(start=start_date, end=end_date)
        
        if not hist.empty:
            # Find closest date
            closest_date = min(hist.index, key=lambda x: abs(x.date() - target_date))
            data = hist.loc[closest_date]
            
            return {
                'open': float(data['Open']),
                'high': float(data['High']),
                'low': float(data['Low']),
                'close': float(data['Close']),
                'volume': int(data['Volume'])
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Yahoo Finance fallback failed for {symbol}: {e}")
        return None


def validate_date_range(start_date: str, end_date: str) -> Tuple[bool, str]:
    """
    Validate date range inputs.
    
    Args:
        start_date: Start date string
        end_date: End date string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        if start > end:
            return False, "Start date must be before end date"
        
        if end > date.today():
            return False, "End date cannot be in the future"
        
        if (end - start).days > 365 * 2:  # 2 years max
            return False, "Date range cannot exceed 2 years"
        
        return True, ""
        
    except ValueError as e:
        return False, f"Invalid date format: {e}"


def format_currency(value: float, currency: str = "HKD") -> str:
    """
    Format currency values consistently.
    
    Args:
        value: Numeric value
        currency: Currency code
        
    Returns:
        Formatted currency string
    """
    try:
        if currency == "HKD":
            return f"HK${value:,.2f}"
        else:
            return f"{value:,.2f} {currency}"
    except (ValueError, TypeError):
        return "N/A"


def calculate_percentage_change(current: float, previous: float) -> float:
    """
    Calculate percentage change between two values.
    
    Args:
        current: Current value
        previous: Previous value
        
    Returns:
        Percentage change
    """
    try:
        if previous == 0:
            return 0.0
        return ((current - previous) / previous) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        return 0.0


def get_all_portfolios_for_equity_analysis(portfolios_data: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Get all available portfolios for equity analysis selection.
    
    Args:
        portfolios_data: Dictionary of portfolio data (optional, uses session state if not provided)
        
    Returns:
        List of portfolio dictionaries
    """
    try:
        # Import streamlit here to avoid circular imports
        import streamlit as st
        
        portfolios = []
        
        # Use provided data or fall back to session state
        portfolio_source = portfolios_data or (st.session_state.portfolios if 'portfolios' in st.session_state else {})
        
        if portfolio_source:
            for portfolio_id, portfolio_data in portfolio_source.items():
                portfolios.append({
                    'portfolio_id': portfolio_id,
                    'name': portfolio_data.get('name', portfolio_id) if isinstance(portfolio_data, dict) else portfolio_id
                })
        
        # Add "All Portfolio Overview" option
        portfolios.insert(0, {
            'portfolio_id': 'all_overview',
            'name': 'All Portfolio Overview'
        })
        
        return portfolios
    except Exception as e:
        logger.error(f"Error loading portfolios: {e}")
        return [{
            'portfolio_id': 'all_overview',
            'name': 'All Portfolio Overview'
        }]


def get_portfolio_analyses_for_equity(portfolio_id: str) -> List[Dict[str, Any]]:
    """
    Get all portfolio analyses for a specific portfolio.
    
    Args:
        portfolio_id: Portfolio identifier
        
    Returns:
        List of analysis dictionaries
    """
    try:
        import streamlit as st
        db = st.session_state.db_manager if hasattr(st.session_state, 'db_manager') else None
        
        if not db:
            logger.warning("No database manager available")
            return []
            
        conn = db.get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, name, start_date, end_date
            FROM portfolio_analyses
            WHERE name ILIKE %s
            ORDER BY created_at DESC
        """, (f"%{portfolio_id}%",))
        
        results = cur.fetchall()
        conn.close()
        
        return [{'id': r[0], 'name': r[1], 'start_date': r[2], 'end_date': r[3]} for r in results]
    except Exception as e:
        logger.error(f"Error fetching portfolio analyses for {portfolio_id}: {e}")
        return []


def get_equities_from_portfolio(portfolio_id: str, portfolios_data: Dict[str, Any] = None, debug_mode: bool = False) -> List[Dict[str, Any]]:
    """
    Get all equities/symbols from a specific portfolio (both active and inactive positions).
    
    Args:
        portfolio_id: Portfolio identifier
        portfolios_data: Dictionary of portfolio data (optional, uses session state if not provided)
        debug_mode: Enable debug logging
        
    Returns:
        List of equity dictionaries
    """
    try:
        # Import streamlit here to avoid circular imports
        import streamlit as st
        
        # Use provided data or fall back to session state
        portfolio_source = portfolios_data or (st.session_state.portfolios if 'portfolios' in st.session_state else {})
        
        # Validate that portfolio data exists
        if not portfolio_source:
            if debug_mode:
                logger.warning("No portfolio data found")
            return []
        
        if portfolio_id == 'all_overview':
            # For "All Portfolio Overview", get all unique equities from all portfolios
            all_equities = []
            for pid, portfolio_data in portfolio_source.items():
                if 'positions' in portfolio_data and portfolio_data['positions']:
                    for position in portfolio_data['positions']:
                        equity = {
                            'symbol': position['symbol'],
                            'company_name': position.get('company_name', 'Unknown Company')
                        }
                        # Avoid duplicates by checking if equity already exists
                        if not any(e['symbol'] == equity['symbol'] for e in all_equities):
                            all_equities.append(equity)
            
            if debug_mode:
                logger.info(f"Found {len(all_equities)} unique equities across all portfolios")
            
            return all_equities
            
        elif portfolio_id in portfolio_source:
            # Get positions from the specific portfolio
            portfolio_data = portfolio_source[portfolio_id]
            if 'positions' in portfolio_data and portfolio_data['positions']:
                equities = []
                active_count = 0
                inactive_count = 0
                
                for position in portfolio_data['positions']:
                    equity = {
                        'symbol': position['symbol'],
                        'company_name': position.get('company_name', 'Unknown Company')
                    }
                    equities.append(equity)
                    
                    # Count active vs inactive for debug
                    if position.get('quantity', 0) > 0:
                        active_count += 1
                    else:
                        inactive_count += 1
                
                if debug_mode:
                    logger.info(f"Portfolio {portfolio_id} has {len(equities)} total equities ({active_count} active, {inactive_count} inactive)")
                
                return equities
            else:
                # Portfolio exists but has no positions
                if debug_mode:
                    logger.info(f"Portfolio {portfolio_id} exists but has no positions")
                return []
        else:
            # Portfolio ID not found
            if debug_mode:
                logger.warning(f"Portfolio {portfolio_id} not found")
            return []
            
    except Exception as e:
        logger.error(f"Error loading equities for portfolio {portfolio_id}: {str(e)}")
        return []


def get_analysis_period_for_equity(analysis_id: int) -> Optional[Dict[str, Any]]:
    """
    Get the analysis period (start_date, end_date) for a specific analysis.
    
    Args:
        analysis_id: Analysis identifier
        
    Returns:
        Dictionary with analysis period data or None
    """
    try:
        import streamlit as st
        db = st.session_state.db_manager if hasattr(st.session_state, 'db_manager') else None
        
        if not db:
            logger.warning("No database manager available")
            return None
            
        conn = db.get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT start_date, end_date, name
            FROM portfolio_analyses
            WHERE id = %s
        """, (analysis_id,))
        
        result = cur.fetchone()
        conn.close()
        
        if result:
            return {'start_date': result[0], 'end_date': result[1], 'name': result[2]}
        return None
    except Exception as e:
        logger.error(f"Error fetching analysis period for {analysis_id}: {e}")
        return None