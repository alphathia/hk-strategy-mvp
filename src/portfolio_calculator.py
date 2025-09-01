"""
Portfolio Calculator Engine

Handles historical portfolio value calculation, performance metrics,
and attribution analysis for HKEX portfolio tracking.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple, Optional, Any
import logging
import json
from dataclasses import dataclass

try:
    from .hkex_calendar import hkex_calendar, get_hkex_trading_days
except ImportError:
    from hkex_calendar import hkex_calendar, get_hkex_trading_days

logger = logging.getLogger(__name__)

@dataclass
class PortfolioMetrics:
    """Container for portfolio performance metrics."""
    start_value: float
    end_value: float
    total_return: float
    total_return_pct: float
    max_drawdown: float
    max_drawdown_pct: float
    volatility: float
    sharpe_ratio: Optional[float]
    trading_days: int
    best_day: Tuple[date, float]
    worst_day: Tuple[date, float]

@dataclass
class DailyContribution:
    """Container for daily position contribution analysis."""
    symbol: str
    contribution: float  # Absolute contribution to daily PV change
    contribution_pct: float  # Percentage contribution to daily PV change
    price_change: float  # Price change in HKD
    price_change_pct: float  # Price change percentage
    position_value: float  # Total position value

class PortfolioCalculator:
    """
    Portfolio Value Calculator with historical analysis capabilities.
    
    Calculates daily portfolio values, performance metrics, and attribution
    analysis for HKEX portfolio tracking over specified time periods.
    """
    
    def __init__(self):
        self.risk_free_rate = 0.025  # 2.5% risk-free rate for Sharpe ratio
    
    def fetch_historical_prices(self, symbols: List[str], start_date: date, end_date: date) -> Dict[str, pd.DataFrame]:
        """
        Fetch historical price data for multiple symbols.
        
        Args:
            symbols: List of stock symbols
            start_date: Data start date (includes 1-month buffer)
            end_date: Data end date
            
        Returns:
            Dictionary mapping symbol to price DataFrame
        """
        price_data = {}
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                
                # Convert dates to pandas datetime for yfinance
                start_str = start_date.strftime('%Y-%m-%d')
                end_str = (end_date + timedelta(days=1)).strftime('%Y-%m-%d')  # Include end date
                
                # Fetch data with some buffer
                hist = ticker.history(start=start_str, end=end_str, auto_adjust=False, actions=False)
                
                if hist.empty:
                    logger.warning(f"No historical data found for {symbol}")
                    continue
                
                # Reset index to get Date as column
                hist = hist.reset_index()
                hist['Date'] = pd.to_datetime(hist['Date']).dt.date
                
                # Sort by date
                hist = hist.sort_values('Date')
                
                price_data[symbol] = hist
                
                logger.info(f"Fetched {len(hist)} days of data for {symbol}")
                
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {e}")
                continue
        
        return price_data
    
    def calculate_daily_portfolio_values(
        self, 
        positions: Dict[str, int],  # symbol -> quantity
        price_data: Dict[str, pd.DataFrame],
        start_date: date,
        end_date: date,
        cash_amount: float = 0.0
    ) -> pd.DataFrame:
        """
        Calculate daily portfolio values for the analysis period.
        
        Args:
            positions: Dictionary mapping symbol to quantity
            price_data: Historical price data for all symbols
            start_date: Analysis start date
            end_date: Analysis end date
            cash_amount: Cash component of portfolio
            
        Returns:
            DataFrame with daily portfolio values and metrics
        """
        # Get all trading days in the analysis period
        trading_days = get_hkex_trading_days(start_date, end_date)
        
        if not trading_days:
            return pd.DataFrame()
        
        # Initialize results list
        daily_values = []
        
        for trade_date in trading_days:
            portfolio_value = 0.0
            position_values = {}
            
            # Calculate portfolio value for this date
            for symbol, quantity in positions.items():
                if quantity == 0:
                    continue
                    
                if symbol not in price_data:
                    logger.warning(f"No price data for {symbol} on {trade_date}")
                    continue
                
                # Get price for this date (use closest available price)
                symbol_data = price_data[symbol]
                price = self._get_price_for_date(symbol_data, trade_date)
                
                if price is not None:
                    position_value = quantity * price
                    portfolio_value += position_value
                    position_values[symbol] = {
                        'price': price,
                        'quantity': quantity,
                        'value': position_value
                    }
            
            total_value = portfolio_value + cash_amount
            
            daily_values.append({
                'trade_date': trade_date,
                'portfolio_value': portfolio_value,
                'cash_value': cash_amount,
                'total_value': total_value,
                'position_values': position_values
            })
        
        # Convert to DataFrame
        df = pd.DataFrame(daily_values)
        
        if df.empty:
            return df
        
        # Calculate daily changes and returns
        df['daily_change'] = df['total_value'].diff()
        df['daily_return'] = df['total_value'].pct_change()
        
        # Calculate attribution for each day
        df['top_contributors'] = df.apply(
            lambda row: self._calculate_daily_attribution(row, df, price_data), 
            axis=1
        )
        
        return df
    
    def _get_price_for_date(self, symbol_data: pd.DataFrame, target_date: date) -> Optional[float]:
        """
        Get the price for a symbol on a specific date.
        Uses the closest available price if exact date not found.
        """
        # Filter data up to target date
        available_data = symbol_data[symbol_data['Date'] <= target_date]
        
        if available_data.empty:
            return None
        
        # Use the most recent available price
        latest_row = available_data.iloc[-1]
        return float(latest_row['Close'])
    
    def _calculate_daily_attribution(self, row: pd.Series, df: pd.DataFrame, price_data: Dict[str, pd.DataFrame]) -> List[Dict]:
        """
        Calculate top contributors to daily portfolio change.
        
        Returns:
            List of top 3 contributors with detailed attribution
        """
        if row.name == 0:  # First day, no previous day for comparison
            return []
        
        current_positions = row['position_values']
        prev_row = df.iloc[row.name - 1]
        prev_positions = prev_row['position_values']
        
        contributions = []
        
        for symbol in current_positions.keys():
            if symbol not in prev_positions:
                continue
            
            current = current_positions[symbol]
            previous = prev_positions[symbol]
            
            # Calculate contribution to daily change
            value_change = current['value'] - previous['value']
            price_change = current['price'] - previous['price']
            price_change_pct = (price_change / previous['price']) * 100 if previous['price'] != 0 else 0
            
            # Calculate contribution percentage (relative to total daily change)
            total_change = row['daily_change']
            contribution_pct = (value_change / total_change * 100) if total_change != 0 else 0
            
            contributions.append({
                'symbol': symbol,
                'contribution': float(value_change),
                'contribution_pct': float(contribution_pct),
                'price_change': float(price_change),
                'price_change_pct': float(price_change_pct),
                'position_value': float(current['value'])
            })
        
        # Sort by absolute contribution and return top 3
        contributions.sort(key=lambda x: abs(x['contribution']), reverse=True)
        return contributions[:3]
    
    def calculate_performance_metrics(self, daily_values_df: pd.DataFrame) -> PortfolioMetrics:
        """
        Calculate comprehensive performance metrics from daily values.
        
        Args:
            daily_values_df: DataFrame with daily portfolio values
            
        Returns:
            PortfolioMetrics object with calculated metrics
        """
        if daily_values_df.empty:
            raise ValueError("Cannot calculate metrics from empty DataFrame")
        
        # Basic values
        start_value = float(daily_values_df.iloc[0]['total_value'])
        end_value = float(daily_values_df.iloc[-1]['total_value'])
        
        # Returns
        total_return = end_value - start_value
        total_return_pct = (total_return / start_value * 100) if start_value != 0 else 0
        
        # Calculate running maximum for drawdown
        daily_values_df['cummax'] = daily_values_df['total_value'].cummax()
        daily_values_df['drawdown'] = daily_values_df['total_value'] - daily_values_df['cummax']
        daily_values_df['drawdown_pct'] = (daily_values_df['drawdown'] / daily_values_df['cummax'] * 100)
        
        # Maximum drawdown
        max_drawdown = float(daily_values_df['drawdown'].min())
        max_drawdown_pct = float(daily_values_df['drawdown_pct'].min())
        
        # Volatility (annualized standard deviation of daily returns)
        daily_returns = daily_values_df['daily_return'].dropna()
        volatility = float(daily_returns.std() * np.sqrt(252))  # Annualized
        
        # Sharpe ratio
        sharpe_ratio = None
        if volatility != 0 and not daily_returns.empty:
            excess_return = (total_return_pct / 100) - self.risk_free_rate
            sharpe_ratio = float(excess_return / volatility)
        
        # Best and worst days - use daily_change instead of daily_return to avoid NaN issues
        daily_changes = daily_values_df['daily_change'].dropna()
        if not daily_changes.empty:
            best_day_idx = daily_changes.idxmax()
            worst_day_idx = daily_changes.idxmin()
            
            best_day = (
                daily_values_df.iloc[best_day_idx]['trade_date'],
                float(daily_values_df.iloc[best_day_idx]['daily_change'])
            )
            worst_day = (
                daily_values_df.iloc[worst_day_idx]['trade_date'],
                float(daily_values_df.iloc[worst_day_idx]['daily_change'])
            )
        else:
            # Fallback to first and last day if no changes available
            best_day = (daily_values_df.iloc[-1]['trade_date'], 0.0)
            worst_day = (daily_values_df.iloc[0]['trade_date'], 0.0)
        
        return PortfolioMetrics(
            start_value=start_value,
            end_value=end_value,
            total_return=total_return,
            total_return_pct=total_return_pct,
            max_drawdown=max_drawdown,
            max_drawdown_pct=max_drawdown_pct,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            trading_days=len(daily_values_df),
            best_day=best_day,
            worst_day=worst_day
        )
    
    def run_portfolio_analysis(
        self,
        positions: Dict[str, int],
        start_date: date,
        end_date: date,
        cash_amount: float = 0.0
    ) -> Tuple[pd.DataFrame, PortfolioMetrics]:
        """
        Run complete portfolio analysis for the specified period.
        
        Args:
            positions: Dictionary mapping symbol to quantity
            start_date: Analysis start date
            end_date: Analysis end date
            cash_amount: Cash component of portfolio
            
        Returns:
            Tuple of (daily_values_df, metrics)
        """
        logger.info(f"Starting portfolio analysis from {start_date} to {end_date}")
        
        # Get data collection start date (1 month prior)
        data_start_date = hkex_calendar.get_analysis_data_start_date(start_date)
        
        # Get all symbols with non-zero positions
        symbols = [symbol for symbol, qty in positions.items() if qty != 0]
        
        if not symbols:
            raise ValueError("No positions found for analysis")
        
        logger.info(f"Analyzing {len(symbols)} positions: {symbols}")
        
        # Fetch historical price data
        price_data = self.fetch_historical_prices(symbols, data_start_date, end_date)
        
        if not price_data:
            raise ValueError("No price data available for analysis")
        
        # Calculate daily portfolio values
        daily_values_df = self.calculate_daily_portfolio_values(
            positions, price_data, start_date, end_date, cash_amount
        )
        
        if daily_values_df.empty:
            raise ValueError("No daily values calculated")
        
        # Calculate performance metrics
        metrics = self.calculate_performance_metrics(daily_values_df)
        
        logger.info(f"Analysis complete: {metrics.trading_days} trading days, "
                   f"{metrics.total_return_pct:.2f}% return")
        
        return daily_values_df, metrics

# Global instance for easy import
portfolio_calculator = PortfolioCalculator()