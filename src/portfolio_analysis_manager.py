"""
Portfolio Analysis Manager

Handles all portfolio analysis operations including:
- Creating new analyses with initial positions
- Managing state changes (buy/sell/dividend/split)
- Calculating performance metrics
- Validating business rules

Uses the simplified single-table approach for maximum flexibility.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import date, datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from decimal import Decimal
import yfinance as yf

# Import HKEX calendar functions
try:
    from .hkex_calendar import get_hkex_trading_days, is_hkex_trading_day
except ImportError:
    from hkex_calendar import get_hkex_trading_days, is_hkex_trading_day

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PortfolioAnalysisManager:
    """Manages portfolio analysis operations with the new simplified schema"""
    
    def __init__(self, database_manager):
        """Initialize with database connection"""
        self.db_manager = database_manager
        
    def get_connection(self):
        """Get database connection"""
        return self.db_manager.get_connection()
    
    def create_analysis(self, portfolio_id: str, analysis_name: str, 
                       start_date: date, end_date: date, start_cash: float) -> Tuple[bool, str, int]:
        """
        Create a new portfolio analysis with initial positions
        
        Args:
            portfolio_id: Portfolio to analyze
            analysis_name: Unique name for this analysis
            start_date: Analysis start date
            end_date: Analysis end date  
            start_cash: Starting cash position
            
        Returns:
            Tuple of (success, message, analysis_id)
        """
        try:
            conn = self.get_connection()
            
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # First, validate that the portfolio exists and has positions
                cur.execute("""
                    SELECT COUNT(*) as position_count
                    FROM portfolio_positions
                    WHERE portfolio_id = %s AND quantity > 0
                """, (portfolio_id,))
                
                result = cur.fetchone()
                position_count = result['position_count'] if result else 0
                
                if position_count == 0:
                    return False, f"Portfolio '{portfolio_id}' has no positions or does not exist. Please add stocks to the portfolio first.", 0
                
                # Check if analysis name already exists for this portfolio
                cur.execute("""
                    SELECT id FROM portfolio_analyses 
                    WHERE portfolio_id = %s AND analysis_name = %s
                """, (portfolio_id, analysis_name))
                
                if cur.fetchone():
                    return False, f"Analysis name '{analysis_name}' already exists for this portfolio", 0
                
                # Validate dates
                if end_date <= start_date:
                    return False, "End date must be after start date", 0
                
                # Create the analysis record
                cur.execute("""
                    INSERT INTO portfolio_analyses 
                    (portfolio_id, analysis_name, start_date, end_date, start_cash)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (portfolio_id, analysis_name, start_date, end_date, start_cash))
                
                analysis_id = cur.fetchone()['id']
                
                # Get current portfolio positions to create initial state
                cur.execute("""
                    SELECT symbol, company_name, quantity, avg_cost, current_price, sector
                    FROM portfolio_positions
                    WHERE portfolio_id = %s AND quantity > 0
                    ORDER BY symbol
                """, (portfolio_id,))
                
                positions = cur.fetchall()
                
                # Create initial state changes for each position
                for pos in positions:
                    # Calculate initial value (negative cash change as it represents investment)
                    initial_value = pos['avg_cost'] * pos['quantity']
                    
                    cur.execute("""
                        INSERT INTO portfolio_analysis_state_changes
                        (analysis_id, symbol, transaction_type, quantity_change, 
                         price_per_share, cash_change, transaction_date, notes)
                        VALUES (%s, %s, 'INITIAL', %s, %s, %s, %s, %s)
                    """, (
                        analysis_id, pos['symbol'], pos['quantity'],
                        pos['avg_cost'], -initial_value, start_date,
                        f"Initial position: {pos['company_name']}"
                    ))
                
                # Update calculated fields
                self._update_analysis_calculations(cur, analysis_id)
                
                conn.commit()
                
                logger.info(f"Created analysis '{analysis_name}' for portfolio {portfolio_id} with {len(positions)} positions")
                return True, f"Analysis '{analysis_name}' created successfully with {len(positions)} positions", analysis_id
                
        except Exception as e:
            logger.error(f"Error creating analysis: {e}")
            return False, f"Failed to create analysis: {str(e)}", 0
    
    def add_transaction(self, analysis_id: int, symbol: str, transaction_type: str,
                       quantity_change: int, price_per_share: float, 
                       transaction_date: date, notes: str = "") -> Tuple[bool, str]:
        """
        Add a transaction to an analysis
        
        Args:
            analysis_id: Analysis to modify
            symbol: Stock symbol
            transaction_type: Type of transaction (BUY, SELL, DIVIDEND, SPLIT, CASH_ADJUSTMENT)
            quantity_change: Change in quantity (positive for buy, negative for sell)
            price_per_share: Price per share for the transaction
            transaction_date: Date of transaction
            notes: Optional notes
            
        Returns:
            Tuple of (success, message)
        """
        try:
            conn = self.get_connection()
            
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Calculate cash change based on transaction type
                cash_change = self._calculate_cash_change(
                    transaction_type, quantity_change, price_per_share
                )
                
                # Insert the transaction (trigger will validate)
                cur.execute("""
                    INSERT INTO portfolio_analysis_state_changes
                    (analysis_id, symbol, transaction_type, quantity_change,
                     price_per_share, cash_change, transaction_date, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    analysis_id, symbol, transaction_type, quantity_change,
                    price_per_share, cash_change, transaction_date, notes
                ))
                
                # Update calculated fields
                self._update_analysis_calculations(cur, analysis_id)
                
                conn.commit()
                
                action = "bought" if quantity_change > 0 else "sold" if quantity_change < 0 else "processed"
                logger.info(f"Transaction recorded: {action} {abs(quantity_change)} shares of {symbol}")
                
                return True, f"Transaction recorded successfully: {action} {abs(quantity_change)} shares of {symbol}"
                
        except psycopg2.Error as e:
            logger.error(f"Database error adding transaction: {e}")
            return False, str(e)
        except Exception as e:
            logger.error(f"Error adding transaction: {e}")
            return False, f"Failed to add transaction: {str(e)}"
    
    def get_analysis_summary(self, portfolio_id: str) -> pd.DataFrame:
        """Get summary of all analyses for a portfolio"""
        try:
            conn = self.get_connection()
            
            query = """
                SELECT 
                    id,
                    analysis_name as name,
                    start_date,
                    end_date,
                    start_cash,
                    COALESCE(end_cash, 0) as end_cash,
                    COALESCE(start_equity_value, 0) as start_equity_value,
                    COALESCE(end_equity_value, 0) as end_equity_value,
                    COALESCE(start_total_value, 0) as start_total_value,
                    COALESCE(end_total_value, 0) as end_total_value,
                    COALESCE(total_equity_gain_loss, 0) as total_equity_gain_loss,
                    COALESCE(total_value_gain_loss, 0) as total_value_gain_loss,
                    created_at,
                    updated_at
                FROM portfolio_analyses
                WHERE portfolio_id = %s
                ORDER BY created_at DESC
            """
            
            return pd.read_sql(query, conn, params=[portfolio_id])
            
        except Exception as e:
            logger.error(f"Error getting analysis summary: {e}")
            return pd.DataFrame()
    
    def get_analysis_transactions(self, analysis_id: int) -> pd.DataFrame:
        """Get all transactions for an analysis"""
        try:
            conn = self.get_connection()
            
            query = """
                SELECT 
                    id,
                    symbol,
                    transaction_type,
                    quantity_change,
                    price_per_share,
                    cash_change,
                    transaction_date,
                    notes,
                    created_at
                FROM portfolio_analysis_state_changes
                WHERE analysis_id = %s
                ORDER BY transaction_date, created_at
            """
            
            return pd.read_sql(query, conn, params=[analysis_id])
            
        except Exception as e:
            logger.error(f"Error getting transactions: {e}")
            return pd.DataFrame()
    
    def get_current_positions(self, analysis_id: int) -> pd.DataFrame:
        """Get current positions for an analysis"""
        try:
            conn = self.get_connection()
            
            query = """
                SELECT 
                    sc.symbol,
                    SUM(sc.quantity_change) as current_quantity,
                    -- Calculate weighted average cost for purchases
                    CASE 
                        WHEN SUM(CASE WHEN sc.quantity_change > 0 THEN sc.quantity_change ELSE 0 END) > 0 THEN
                            ABS(SUM(CASE WHEN sc.quantity_change > 0 THEN sc.cash_change ELSE 0 END) / 
                                SUM(CASE WHEN sc.quantity_change > 0 THEN sc.quantity_change ELSE 0 END))
                        ELSE 0 
                    END as avg_cost,
                    -- Get current price from portfolio_positions (would be updated in real system)
                    MAX(pp.current_price) as current_price,
                    MAX(pp.company_name) as company_name
                FROM portfolio_analysis_state_changes sc
                LEFT JOIN portfolio_positions pp ON sc.symbol = pp.symbol
                WHERE sc.analysis_id = %s
                GROUP BY sc.symbol
                HAVING SUM(sc.quantity_change) > 0
                ORDER BY sc.symbol
            """
            
            return pd.read_sql(query, conn, params=[analysis_id])
            
        except Exception as e:
            logger.error(f"Error getting current positions: {e}")
            return pd.DataFrame()
    
    def delete_analysis(self, analysis_id: int) -> Tuple[bool, str]:
        """Delete an analysis and all its transactions"""
        try:
            conn = self.get_connection()
            
            with conn.cursor() as cur:
                # Get analysis name for logging
                cur.execute("SELECT analysis_name FROM portfolio_analyses WHERE id = %s", (analysis_id,))
                result = cur.fetchone()
                if not result:
                    return False, "Analysis not found"
                
                analysis_name = result[0]
                
                # Delete the analysis (CASCADE will handle transactions)
                cur.execute("DELETE FROM portfolio_analyses WHERE id = %s", (analysis_id,))
                
                if cur.rowcount == 0:
                    return False, "Analysis not found"
                
                conn.commit()
                
                logger.info(f"Deleted analysis '{analysis_name}' (ID: {analysis_id})")
                return True, f"Analysis '{analysis_name}' deleted successfully"
                
        except Exception as e:
            logger.error(f"Error deleting analysis: {e}")
            return False, f"Failed to delete analysis: {str(e)}"
    
    def _calculate_cash_change(self, transaction_type: str, quantity_change: int, 
                              price_per_share: float) -> float:
        """Calculate cash change for a transaction"""
        if transaction_type == 'BUY':
            return -abs(quantity_change) * price_per_share  # Cash decreases
        elif transaction_type == 'SELL':
            return abs(quantity_change) * price_per_share   # Cash increases
        elif transaction_type == 'DIVIDEND':
            return abs(quantity_change) * price_per_share   # Cash increases, quantity_change should be 0
        elif transaction_type == 'SPLIT':
            return 0  # No cash change for splits
        elif transaction_type == 'CASH_ADJUSTMENT':
            return quantity_change  # Direct cash adjustment
        else:
            return 0
    
    def _update_analysis_calculations(self, cur, analysis_id: int):
        """Update calculated fields for an analysis"""
        try:
            # Calculate start equity value (sum of initial investments)
            cur.execute("""
                SELECT COALESCE(SUM(ABS(cash_change)), 0) as start_equity_value
                FROM portfolio_analysis_state_changes
                WHERE analysis_id = %s AND transaction_type = 'INITIAL'
            """, (analysis_id,))
            
            result = cur.fetchone()
            start_equity_value = float(result['start_equity_value'] if isinstance(result, dict) else result[0])
            
            # Get start cash
            cur.execute("SELECT start_cash FROM portfolio_analyses WHERE id = %s", (analysis_id,))
            result = cur.fetchone()
            start_cash = float(result['start_cash'] if isinstance(result, dict) else result[0])
            
            # Calculate current cash (start cash + actual trading cash changes, excluding INITIAL)
            # INITIAL transactions represent existing positions, not cash outflows during analysis period
            cur.execute("""
                SELECT COALESCE(SUM(cash_change), 0) as total_cash_changes
                FROM portfolio_analysis_state_changes
                WHERE analysis_id = %s 
                  AND transaction_type != 'INITIAL'
            """, (analysis_id,))
            
            result = cur.fetchone()
            total_cash_changes = float(result['total_cash_changes'] if isinstance(result, dict) else result[0])
            end_cash = start_cash + total_cash_changes
            
            # Calculate current market value using real market prices
            end_equity_value = self._get_current_market_value(analysis_id)
            
            # Calculate totals
            start_total_value = start_cash + start_equity_value
            end_total_value = end_cash + end_equity_value
            
            # Update the analysis record
            cur.execute("""
                UPDATE portfolio_analyses SET
                    start_equity_value = %s,
                    end_equity_value = %s,
                    end_cash = %s,
                    start_total_value = %s,
                    end_total_value = %s,
                    total_equity_gain_loss = %s,
                    total_value_gain_loss = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                start_equity_value, end_equity_value, end_cash,
                start_total_value, end_total_value,
                end_equity_value - start_equity_value,
                end_total_value - start_total_value,
                analysis_id
            ))
            
            logger.debug(f"Updated calculations for analysis {analysis_id}: start_equity={start_equity_value}, end_cash={end_cash}")
            
        except Exception as e:
            logger.error(f"Error updating calculations: {e}")
            raise
    
    def _get_current_market_value(self, analysis_id: int) -> float:
        """
        Calculate current market value for an analysis using latest market prices
        
        Args:
            analysis_id: Analysis ID to calculate market value for
            
        Returns:
            Current market value of equity positions (float)
        """
        try:
            conn = self.get_connection()
            
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get analysis end date and all positions
                cur.execute("""
                    SELECT 
                        pa.end_date,
                        sc.symbol,
                        SUM(sc.quantity_change) as quantity
                    FROM portfolio_analyses pa
                    LEFT JOIN portfolio_analysis_state_changes sc ON pa.id = sc.analysis_id
                    WHERE pa.id = %s 
                      AND sc.symbol IS NOT NULL
                      AND sc.transaction_type IN ('INITIAL', 'BUY', 'SELL')
                    GROUP BY pa.end_date, sc.symbol
                    HAVING SUM(sc.quantity_change) > 0
                """, (analysis_id,))
                
                position_data = cur.fetchall()
                
                if not position_data:
                    logger.info(f"No equity positions found for analysis {analysis_id}")
                    return 0.0
                
                # Extract symbols and get end date
                symbols = [row['symbol'] for row in position_data]
                end_date = position_data[0]['end_date']
                
                logger.info(f"Calculating market value for analysis {analysis_id}: {len(symbols)} symbols as of {end_date}")
                
                # Fetch market prices for the end date (or latest available)
                # Use a small date range around the end date to get the closest price
                price_start = end_date - timedelta(days=7)  # Look back up to 7 days
                price_end = min(end_date + timedelta(days=2), date.today())  # Don't go beyond today
                
                price_df = self.fetch_bulk_historical_prices(symbols, price_start, price_end)
                
                if price_df.empty:
                    logger.warning(f"No price data available for analysis {analysis_id}, using cost basis fallback")
                    return self._get_cost_basis_value(analysis_id)
                
                # Calculate market value
                total_market_value = 0.0
                price_date_used = None
                
                for row in position_data:
                    symbol = row['symbol']
                    quantity = float(row['quantity'])
                    
                    # Get the latest available price for this symbol (closest to end_date)
                    symbol_prices = price_df[price_df['symbol'] == symbol].copy()
                    if not symbol_prices.empty:
                        # Sort by date and get the latest price
                        symbol_prices = symbol_prices.sort_values('date', ascending=False)
                        latest_price = float(symbol_prices.iloc[0]['close_price'])
                        price_date = symbol_prices.iloc[0]['date'].date()
                        
                        market_value = quantity * latest_price
                        total_market_value += market_value
                        
                        if price_date_used is None:
                            price_date_used = price_date
                        
                        logger.info(f"  {symbol}: {quantity} × ${latest_price:.2f} = ${market_value:,.2f}")
                    else:
                        logger.warning(f"  {symbol}: No price data available, excluding from market value")
                
                logger.info(f"Total market value for analysis {analysis_id}: ${total_market_value:,.2f} (as of {price_date_used})")
                return total_market_value
                
        except Exception as e:
            logger.error(f"Error calculating current market value for analysis {analysis_id}: {e}")
            logger.info("Falling back to cost basis calculation")
            return self._get_cost_basis_value(analysis_id)
        finally:
            if 'conn' in locals():
                conn.close()
    
    def _get_cost_basis_value(self, analysis_id: int) -> float:
        """
        Fallback method to calculate equity value using cost basis
        
        Args:
            analysis_id: Analysis ID to calculate cost basis for
            
        Returns:
            Cost basis value of equity positions (float)
        """
        try:
            conn = self.get_connection()
            
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COALESCE(SUM(ABS(cash_change)), 0) as cost_basis_value
                    FROM portfolio_analysis_state_changes
                    WHERE analysis_id = %s AND transaction_type = 'INITIAL'
                """, (analysis_id,))
                
                result = cur.fetchone()
                cost_basis = float(result[0] if result else 0)
                
                logger.info(f"Cost basis value for analysis {analysis_id}: ${cost_basis:,.2f}")
                return cost_basis
                
        except Exception as e:
            logger.error(f"Error calculating cost basis for analysis {analysis_id}: {e}")
            return 0.0
        finally:
            if 'conn' in locals():
                conn.close()
    
    def validate_analysis_name(self, portfolio_id: str, analysis_name: str, 
                              exclude_id: int = None) -> bool:
        """Check if analysis name is unique for portfolio"""
        try:
            conn = self.get_connection()
            
            with conn.cursor() as cur:
                query = """
                    SELECT id FROM portfolio_analyses 
                    WHERE portfolio_id = %s AND analysis_name = %s
                """
                params = [portfolio_id, analysis_name]
                
                if exclude_id:
                    query += " AND id != %s"
                    params.append(exclude_id)
                
                cur.execute(query, params)
                return cur.fetchone() is None
                
        except Exception as e:
            logger.error(f"Error validating analysis name: {e}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()
    
    def refresh_analysis_with_market_prices(self, analysis_id: int) -> Tuple[bool, str]:
        """
        Refresh an analysis with current market prices
        
        Args:
            analysis_id: Analysis ID to refresh
            
        Returns:
            Tuple of (success, message)
        """
        try:
            conn = self.get_connection()
            
            with conn.cursor() as cur:
                # Update the analysis calculations with current market prices
                self._update_analysis_calculations(cur, analysis_id)
                conn.commit()
                
                logger.info(f"Successfully refreshed analysis {analysis_id} with current market prices")
                return True, "Analysis updated with current market prices"
                
        except Exception as e:
            logger.error(f"Error refreshing analysis {analysis_id}: {e}")
            return False, f"Error updating analysis: {str(e)}"
        finally:
            if 'conn' in locals():
                conn.close()
    
    def refresh_all_analyses_for_portfolio(self, portfolio_id: str) -> Tuple[bool, str, int]:
        """
        Refresh all analyses for a portfolio with current market prices
        
        Args:
            portfolio_id: Portfolio ID to refresh analyses for
            
        Returns:
            Tuple of (success, message, count_updated)
        """
        try:
            conn = self.get_connection()
            
            with conn.cursor() as cur:
                # Get all analysis IDs for this portfolio
                cur.execute("""
                    SELECT id FROM portfolio_analyses 
                    WHERE portfolio_id = %s
                """, (portfolio_id,))
                
                analysis_ids = [row[0] for row in cur.fetchall()]
                
                if not analysis_ids:
                    return True, "No analyses found to update", 0
                
                # Update each analysis with current market prices
                updated_count = 0
                for analysis_id in analysis_ids:
                    try:
                        self._update_analysis_calculations(cur, analysis_id)
                        updated_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to update analysis {analysis_id}: {e}")
                        continue
                
                conn.commit()
                
                logger.info(f"Successfully refreshed {updated_count}/{len(analysis_ids)} analyses for portfolio {portfolio_id}")
                return True, f"Updated {updated_count} analyses with current market prices", updated_count
                
        except Exception as e:
            logger.error(f"Error refreshing analyses for portfolio {portfolio_id}: {e}")
            return False, f"Error updating analyses: {str(e)}", 0
        finally:
            if 'conn' in locals():
                conn.close()
    
    def get_analysis_timeline_data(self, analysis_ids: List[int]) -> pd.DataFrame:
        """
        Get timeline data for multiple analyses to plot total value over time using real market prices
        
        Args:
            analysis_ids: List of analysis IDs to include in timeline
            
        Returns:
            DataFrame with columns: analysis_id, analysis_name, date, total_value, 
                                   cash_position, equity_value, transaction_details
        """
        try:
            conn = self.get_connection()
            
            if not analysis_ids:
                return pd.DataFrame()
            
            # First, get the analysis date ranges and symbols
            placeholders = ','.join(['%s'] * len(analysis_ids))
            
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get analysis metadata and all symbols
                metadata_query = f"""
                    SELECT 
                        pa.id as analysis_id,
                        pa.analysis_name,
                        pa.start_date,
                        pa.end_date,
                        ARRAY_AGG(DISTINCT sc.symbol) FILTER (WHERE sc.symbol IS NOT NULL) as symbols
                    FROM portfolio_analyses pa
                    LEFT JOIN portfolio_analysis_state_changes sc ON pa.id = sc.analysis_id
                    WHERE pa.id IN ({placeholders})
                    GROUP BY pa.id, pa.analysis_name, pa.start_date, pa.end_date
                """
                
                cur.execute(metadata_query, analysis_ids)
                metadata_results = cur.fetchall()
                
                if not metadata_results:
                    return pd.DataFrame()
                
                # Collect all unique symbols and date range
                all_symbols = set()
                min_start_date = None
                max_end_date = None
                
                for row in metadata_results:
                    if row['symbols']:
                        all_symbols.update(row['symbols'])
                    
                    start_date = row['start_date']
                    end_date = row['end_date']
                    
                    if min_start_date is None or start_date < min_start_date:
                        min_start_date = start_date
                    if max_end_date is None or end_date > max_end_date:
                        max_end_date = end_date
                
                logger.info(f"Fetching market prices for {len(all_symbols)} symbols from {min_start_date} to {max_end_date}")
                
                # Fetch historical price data using our new method
                price_df = self.fetch_bulk_historical_prices(
                    list(all_symbols), 
                    min_start_date, 
                    max_end_date
                )
                
                # If we couldn't get any price data, fall back to original method
                if price_df.empty:
                    logger.warning("No price data available, falling back to cost basis calculation")
                    return self._get_timeline_data_cost_basis(analysis_ids)
                
                # Continue with the enhanced query using market prices
                timeline_results = self._calculate_timeline_with_market_prices(
                    cur, analysis_ids, price_df, metadata_results
                )
                
                return timeline_results
                
        except Exception as e:
            logger.error(f"Error getting timeline data with market prices: {e}")
            logger.info("Falling back to cost basis calculation")
            return self._get_timeline_data_cost_basis(analysis_ids)
        finally:
            if 'conn' in locals():
                conn.close()
    
    def _get_trading_days_for_analyses(self, cur, analysis_ids: List[int]) -> Dict[int, List[date]]:
        """Get trading days for each analysis using HKEX calendar"""
        try:
            placeholders = ','.join(['%s'] * len(analysis_ids))
            
            # Get date ranges for all analyses
            query = f"""
                SELECT id, start_date, end_date
                FROM portfolio_analyses 
                WHERE id IN ({placeholders})
            """
            
            logger.info(f"Executing query: {query} with analysis_ids: {analysis_ids}")
            cur.execute(query, tuple(analysis_ids))
            
            analyses_data = cur.fetchall()
            logger.info(f"Retrieved {len(analyses_data)} analyses data rows")
            
            # Generate trading days for each analysis
            trading_days_map = {}
            for analysis_row in analyses_data:
                # Handle both tuple and dict cursor results
                if isinstance(analysis_row, dict):
                    analysis_id = analysis_row['id']
                    start_date = analysis_row['start_date']  
                    end_date = analysis_row['end_date']
                else:
                    analysis_id = analysis_row[0]
                    start_date = analysis_row[1]
                    end_date = analysis_row[2]
                
                logger.info(f"Processing analysis {analysis_id}: {start_date} to {end_date}")
                
                trading_days = get_hkex_trading_days(start_date, end_date)
                trading_days_map[analysis_id] = trading_days
                logger.info(f"Analysis {analysis_id}: {len(trading_days)} trading days calculated")
            
            logger.info(f"Total trading days map: {len(trading_days_map)} analyses")
            return trading_days_map
            
        except Exception as e:
            logger.error(f"Error getting trading days: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {}
    
    def _calculate_timeline_with_market_prices(self, cur, analysis_ids: List[int], 
                                             price_df: pd.DataFrame, metadata_results) -> pd.DataFrame:
        """Calculate timeline data using real market prices and TRADING DAYS ONLY"""
        try:
            logger.info("Calculating timeline with market prices using TRADING DAYS only")
            
            # Get trading days for all analyses
            trading_days_map = self._get_trading_days_for_analyses(cur, analysis_ids)
            
            if not trading_days_map:
                logger.error("No trading days found for analyses")
                return pd.DataFrame()
            
            # Get all transaction data
            placeholders = ','.join(['%s'] * len(analysis_ids))
            cur.execute(f"""
                SELECT 
                    pa.id as analysis_id,
                    pa.analysis_name, 
                    pa.start_date,
                    pa.end_date,
                    pa.start_cash,
                    sc.transaction_date,
                    sc.symbol,
                    sc.transaction_type,
                    sc.quantity_change,
                    sc.cash_change
                FROM portfolio_analyses pa
                LEFT JOIN portfolio_analysis_state_changes sc ON pa.id = sc.analysis_id
                WHERE pa.id IN ({placeholders})
                ORDER BY pa.id, sc.transaction_date
            """, analysis_ids)
            
            transaction_data = cur.fetchall()
            
            # Process each analysis separately with trading days only
            all_results = []
            
            for metadata in metadata_results:
                analysis_id = metadata['analysis_id']
                analysis_name = metadata['analysis_name']
                
                # Get trading days for this analysis
                trading_days = trading_days_map.get(analysis_id, [])
                if not trading_days:
                    logger.warning(f"No trading days for analysis {analysis_id}")
                    continue
                
                logger.info(f"Processing analysis {analysis_id} with {len(trading_days)} trading days")
                
                # Get transactions for this analysis
                if isinstance(transaction_data[0], dict) if transaction_data else False:
                    analysis_transactions = [t for t in transaction_data if t['analysis_id'] == analysis_id]
                    start_cash = analysis_transactions[0]['start_cash'] if analysis_transactions else 0
                else:
                    analysis_transactions = [t for t in transaction_data if t[0] == analysis_id]
                    start_cash = analysis_transactions[0][4] if analysis_transactions else 0
                logger.info(f"Found {len(analysis_transactions)} transactions for analysis {analysis_id}, start_cash: {start_cash}")
                
                # Calculate daily values using trading days only
                daily_results = self._calculate_daily_values_trading_days(
                    analysis_id, analysis_name, trading_days, 
                    analysis_transactions, start_cash, price_df
                )
                
                all_results.extend(daily_results)
            
            # Convert to DataFrame
            if all_results:
                result_df = pd.DataFrame(all_results)
                logger.info(f"Generated timeline with {len(result_df)} trading day data points")
                return result_df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error calculating timeline with market prices: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return pd.DataFrame()
    
    def _calculate_daily_values_trading_days(self, analysis_id: int, analysis_name: str, 
                                          trading_days: List[date], transactions: List,
                                          start_cash: float, price_df: pd.DataFrame) -> List[Dict]:
        """Calculate daily portfolio values for trading days only"""
        daily_results = []
        
        # Initialize positions and cash
        positions = {}  # symbol -> quantity
        current_cash = start_cash
        processed_transactions = set()  # Track processed transactions to avoid double-processing
        
        for trading_day in trading_days:
            # Apply any transactions that occurred exactly on this trading day (FIXED: was <= causing double processing)
            for i, transaction in enumerate(transactions):
                # Create unique transaction identifier
                trans_id = f"{analysis_id}_{i}"
                
                # Skip if already processed
                if trans_id in processed_transactions:
                    continue
                
                # Handle both dict and tuple transaction data
                if isinstance(transaction, dict):
                    trans_date = transaction['transaction_date']
                    symbol = transaction['symbol']
                    trans_type = transaction['transaction_type']
                    qty_change = transaction['quantity_change'] or 0
                    cash_change = transaction['cash_change'] or 0
                else:
                    trans_date = transaction[5]  # transaction_date
                    symbol = transaction[6]
                    trans_type = transaction[7]
                    qty_change = transaction[8] or 0
                    cash_change = transaction[9] or 0
                
                # FIXED: Only process transactions that occur exactly on this trading day
                if trans_date and trans_date == trading_day:
                    if symbol and trans_type:
                        # Update positions
                        if symbol not in positions:
                            positions[symbol] = 0
                        positions[symbol] += qty_change
                        
                        # Update cash (handle Decimal type from database)
                        current_cash = float(current_cash) + float(cash_change or 0)
                        
                        # Mark transaction as processed
                        processed_transactions.add(trans_id)
            
            # Calculate equity value using market prices
            equity_value = 0.0
            transaction_details = []
            
            # Get market prices for this trading day
            day_prices = price_df[price_df['date'].dt.date == trading_day] if not price_df.empty else pd.DataFrame()
            
            for symbol, quantity in positions.items():
                if quantity == 0:
                    continue
                
                # Get price for this symbol on this date
                symbol_prices = day_prices[day_prices['symbol'] == symbol]
                if not symbol_prices.empty:
                    price = float(symbol_prices.iloc[0]['close_price'])
                    equity_value += quantity * price
                else:
                    # FIXED: Use intelligent fallback - get best available price
                    all_symbol_prices = price_df[price_df['symbol'] == symbol]
                    if not all_symbol_prices.empty:
                        # First try: Get latest price before or on this date (backward fill)
                        before_date = all_symbol_prices[all_symbol_prices['date'].dt.date <= trading_day]
                        if not before_date.empty:
                            price = float(before_date.iloc[-1]['close_price'])
                            equity_value += quantity * price
                        else:
                            # Second try: Get earliest price after this date (forward fill)
                            # This handles cases where we only have current/future price data
                            after_date = all_symbol_prices[all_symbol_prices['date'].dt.date >= trading_day]
                            if not after_date.empty:
                                price = float(after_date.iloc[0]['close_price'])
                                equity_value += quantity * price
            
            # Check for transactions on this exact date for hover details
            day_transactions = []
            for t in transactions:
                if isinstance(t, dict):
                    if t['transaction_date'] == trading_day:
                        day_transactions.append(t)
                else:
                    if t[5] == trading_day:  # transaction_date
                        day_transactions.append(t)
            
            if day_transactions:
                trans_details = []
                for t in day_transactions:
                    if isinstance(t, dict):
                        if t['symbol'] and t['transaction_type']:
                            trans_details.append(f"{t['transaction_type']} {t['symbol']} ({t['quantity_change']})")
                    else:
                        if t[6] and t[7]:  # symbol and transaction_type exist
                            trans_details.append(f"{t[7]} {t[6]} ({t[8]})")
                if trans_details:
                    transaction_details = '; '.join(trans_details)
            
            # Add daily result (ensure all values are float for consistency)
            total_value = float(current_cash) + equity_value
            daily_results.append({
                'analysis_id': analysis_id,
                'analysis_name': analysis_name,
                'date': trading_day,
                'total_value': total_value,
                'cash_position': float(current_cash),
                'equity_value': equity_value,
                'transaction_details': '; '.join(transaction_details) if transaction_details else None
            })
        
        return daily_results
    
    def _calculate_timeline_with_market_prices_old(self, cur, analysis_ids: List[int], 
                                                 price_df: pd.DataFrame, metadata_results) -> pd.DataFrame:
        """OLD VERSION - Calculate timeline data using real market prices (INCLUDES WEEKENDS - PROBLEMATIC)"""
        try:
            # Create a placeholder string for the IN clause
            placeholders = ','.join(['%s'] * len(analysis_ids))
            
            # Get position data from database
            position_query = f"""
                WITH daily_data AS (
                    -- Generate date series for each analysis (PROBLEM: includes weekends!)
                    SELECT 
                        pa.id as analysis_id,
                        pa.analysis_name,
                        pa.start_date,
                        pa.end_date,
                        pa.start_cash,
                        generate_series(pa.start_date, pa.end_date, interval '1 day')::date as date
                    FROM portfolio_analyses pa
                    WHERE pa.id IN ({placeholders})
                ),
                cumulative_transactions AS (
                    -- Get cumulative effect of transactions up to each date
                    SELECT 
                        dd.analysis_id,
                        dd.analysis_name,
                        dd.date,
                        dd.start_cash,
                        COALESCE(SUM(sc.cash_change) 
                            FILTER (WHERE sc.transaction_date <= dd.date AND sc.transaction_type != 'INITIAL'), 0) as cumulative_cash_change,
                        -- Get transaction details for this date (for hover details)
                        STRING_AGG(
                            CASE WHEN sc.transaction_date = dd.date 
                            THEN sc.transaction_type || ' ' || sc.symbol || ' (' || sc.quantity_change || ')' 
                            ELSE NULL END, 
                            '; '
                        ) as transaction_details
                    FROM daily_data dd
                    LEFT JOIN portfolio_analysis_state_changes sc ON dd.analysis_id = sc.analysis_id
                    GROUP BY dd.analysis_id, dd.analysis_name, dd.date, dd.start_cash
                ),
                position_quantities AS (
                    -- Calculate quantity held for each symbol at each date
                    SELECT 
                        ct.analysis_id,
                        ct.analysis_name,
                        ct.date,
                        ct.start_cash,
                        ct.cumulative_cash_change,
                        ct.transaction_details,
                        sc2.symbol,
                        COALESCE(SUM(sc3.quantity_change) 
                            FILTER (WHERE sc3.transaction_date <= ct.date), 0) as quantity
                    FROM cumulative_transactions ct
                    CROSS JOIN (
                        SELECT DISTINCT symbol 
                        FROM portfolio_analysis_state_changes 
                        WHERE analysis_id IN ({placeholders})
                          AND symbol IS NOT NULL
                    ) sc2
                    LEFT JOIN portfolio_analysis_state_changes sc3 
                        ON ct.analysis_id = sc3.analysis_id 
                        AND sc2.symbol = sc3.symbol
                    GROUP BY ct.analysis_id, ct.analysis_name, ct.date, ct.start_cash, ct.cumulative_cash_change, ct.transaction_details, sc2.symbol
                )
                SELECT 
                    analysis_id,
                    analysis_name,
                    date,
                    start_cash,
                    cumulative_cash_change,
                    transaction_details,
                    symbol,
                    quantity
                FROM position_quantities
                WHERE quantity != 0  -- Only include positions with non-zero quantities
                ORDER BY analysis_id, date, symbol;
            """
            
            # Execute with analysis_ids twice (for the two IN clauses)
            cur.execute(position_query, analysis_ids + analysis_ids)
            position_results = cur.fetchall()
            
            if not position_results:
                # No positions, return cash-only timeline
                return self._get_cash_only_timeline(cur, analysis_ids)
            
            # Convert to pandas for easier manipulation
            positions_df = pd.DataFrame(position_results)
            positions_df['date'] = pd.to_datetime(positions_df['date'])
            
            # Merge with price data
            price_df_copy = price_df.copy()
            price_df_copy['date'] = pd.to_datetime(price_df_copy['date'])
            
            # Merge positions with market prices
            timeline_data = positions_df.merge(
                price_df_copy[['symbol', 'date', 'close_price']], 
                on=['symbol', 'date'], 
                how='left'
            )
            
            # Calculate market values - ensure proper data types
            timeline_data['quantity'] = timeline_data['quantity'].astype(float)
            timeline_data['close_price'] = timeline_data['close_price'].fillna(0).astype(float)
            timeline_data['start_cash'] = timeline_data['start_cash'].astype(float)
            timeline_data['cumulative_cash_change'] = timeline_data['cumulative_cash_change'].astype(float)
            timeline_data['market_value'] = timeline_data['quantity'] * timeline_data['close_price']
            
            # Aggregate by analysis and date
            aggregated = timeline_data.groupby(['analysis_id', 'analysis_name', 'date']).agg({
                'start_cash': 'first',
                'cumulative_cash_change': 'first',
                'transaction_details': 'first',
                'market_value': 'sum'
            }).reset_index()
            
            # Calculate final values
            aggregated['cash_position'] = aggregated['start_cash'] + aggregated['cumulative_cash_change']
            aggregated['equity_value'] = aggregated['market_value']
            aggregated['total_value'] = aggregated['cash_position'] + aggregated['equity_value']
            
            # Fill missing dates for analyses with no positions on certain dates
            result_df = self._fill_missing_analysis_dates(aggregated, metadata_results)
            
            # Select and order columns
            final_columns = ['analysis_id', 'analysis_name', 'date', 'cash_position', 'equity_value', 'total_value', 'transaction_details']
            result_df = result_df[final_columns]
            
            logger.info(f"Successfully calculated market price timeline: {len(result_df)} records")
            return result_df
            
        except Exception as e:
            logger.error(f"Error in market price timeline calculation: {e}")
            raise
    
    def _fill_missing_analysis_dates(self, df: pd.DataFrame, metadata_results) -> pd.DataFrame:
        """Fill missing dates for analyses with complete date ranges"""
        if df.empty:
            return df
        
        complete_data = []
        
        for metadata in metadata_results:
            analysis_id = metadata['analysis_id']
            analysis_name = metadata['analysis_name']
            start_date = pd.Timestamp(metadata['start_date'])
            end_date = pd.Timestamp(metadata['end_date'])
            
            # Get data for this analysis
            analysis_data = df[df['analysis_id'] == analysis_id].copy()
            
            if analysis_data.empty:
                # Create cash-only entries for this analysis
                date_range = pd.date_range(start=start_date, end=end_date, freq='D')
                for date_val in date_range:
                    complete_data.append({
                        'analysis_id': analysis_id,
                        'analysis_name': analysis_name,
                        'date': date_val,
                        'cash_position': 0.0,  # Will be calculated properly
                        'equity_value': 0.0,
                        'total_value': 0.0,
                        'transaction_details': ''
                    })
            else:
                # Fill missing dates for existing analysis
                analysis_data.set_index('date', inplace=True)
                date_range = pd.date_range(start=start_date, end=end_date, freq='D')
                analysis_data = analysis_data.reindex(date_range, method='ffill')
                
                # Reset index and ensure proper columns
                analysis_data.reset_index(inplace=True)
                analysis_data['date'] = analysis_data['index']
                analysis_data['analysis_id'] = analysis_id
                analysis_data['analysis_name'] = analysis_name
                analysis_data = analysis_data.fillna(0)
                
                complete_data.append(analysis_data)
        
        if complete_data:
            if all(isinstance(x, pd.DataFrame) for x in complete_data):
                return pd.concat(complete_data, ignore_index=True)
            else:
                # Mix of DataFrames and dicts
                all_records = []
                for item in complete_data:
                    if isinstance(item, pd.DataFrame):
                        all_records.extend(item.to_dict('records'))
                    else:
                        all_records.extend(item)
                return pd.DataFrame(all_records)
        
        return df
    
    def _get_cash_only_timeline(self, cur, analysis_ids: List[int]) -> pd.DataFrame:
        """Generate timeline for analyses with no equity positions"""
        placeholders = ','.join(['%s'] * len(analysis_ids))
        
        query = f"""
            WITH daily_data AS (
                SELECT 
                    pa.id as analysis_id,
                    pa.analysis_name,
                    pa.start_cash,
                    generate_series(pa.start_date, pa.end_date, interval '1 day')::date as date
                FROM portfolio_analyses pa
                WHERE pa.id IN ({placeholders})
            )
            SELECT 
                dd.analysis_id,
                dd.analysis_name,
                dd.date,
                dd.start_cash as cash_position,
                0.0 as equity_value,
                dd.start_cash as total_value,
                '' as transaction_details
            FROM daily_data dd
            ORDER BY dd.analysis_id, dd.date;
        """
        
        cur.execute(query, analysis_ids)
        results = cur.fetchall()
        
        df = pd.DataFrame(results)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
        
        return df
    
    def _get_timeline_data_cost_basis(self, analysis_ids: List[int]) -> pd.DataFrame:
        """Fallback method using original cost basis calculation with TRADING DAYS ONLY"""
        try:
            logger.info("Using cost basis calculation fallback with TRADING DAYS only")
            conn = self.get_connection()
            
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get trading days for all analyses
                trading_days_map = self._get_trading_days_for_analyses(cur, analysis_ids)
                
                if not trading_days_map:
                    logger.error("No trading days found for cost basis calculation")
                    return pd.DataFrame()
                
                # Get analysis metadata and transactions
                placeholders = ','.join(['%s'] * len(analysis_ids))
                cur.execute(f"""
                    SELECT 
                        pa.id as analysis_id,
                        pa.analysis_name, 
                        pa.start_date,
                        pa.end_date,
                        pa.start_cash,
                        sc.transaction_date,
                        sc.symbol,
                        sc.transaction_type,
                        sc.quantity_change,
                        sc.cash_change,
                        sc.price
                    FROM portfolio_analyses pa
                    LEFT JOIN portfolio_analysis_state_changes sc ON pa.id = sc.analysis_id
                    WHERE pa.id IN ({placeholders})
                    ORDER BY pa.id, sc.transaction_date
                """, analysis_ids)
                
                transaction_data = cur.fetchall()
                
                # Process using trading days only
                all_results = []
                
                # Group transactions by analysis
                analysis_transactions = {}
                analysis_metadata = {}
                
                for row in transaction_data:
                    analysis_id = row['analysis_id']
                    
                    if analysis_id not in analysis_transactions:
                        analysis_transactions[analysis_id] = []
                        analysis_metadata[analysis_id] = {
                            'analysis_name': row['analysis_name'],
                            'start_cash': row['start_cash']
                        }
                    
                    if row['transaction_date']:  # Only add actual transactions
                        analysis_transactions[analysis_id].append(row)
                
                # Calculate daily values for each analysis using trading days
                for analysis_id, transactions in analysis_transactions.items():
                    trading_days = trading_days_map.get(analysis_id, [])
                    if not trading_days:
                        continue
                    
                    metadata = analysis_metadata[analysis_id]
                    daily_results = self._calculate_daily_values_cost_basis(
                        analysis_id, 
                        metadata['analysis_name'],
                        trading_days,
                        transactions,
                        metadata['start_cash']
                    )
                    
                    all_results.extend(daily_results)
                
                if all_results:
                    result_df = pd.DataFrame(all_results)
                    logger.info(f"Generated cost basis timeline with {len(result_df)} trading day data points")
                    return result_df
                else:
                    return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error in cost basis timeline calculation: {e}")
            return pd.DataFrame()
        finally:
            if 'conn' in locals():
                conn.close()
    
    def _calculate_daily_values_cost_basis(self, analysis_id: int, analysis_name: str,
                                        trading_days: List[date], transactions: List,
                                        start_cash: float) -> List[Dict]:
        """Calculate daily portfolio values using cost basis for trading days only"""
        daily_results = []
        
        # Initialize positions and cash
        positions = {}  # symbol -> {'quantity': X, 'cost_basis': Y}
        current_cash = start_cash
        
        for trading_day in trading_days:
            # Apply transactions that occurred on or before this date
            day_transactions = []
            
            for transaction in transactions:
                trans_date = transaction['transaction_date']
                if trans_date and trans_date <= trading_day:
                    symbol = transaction['symbol']
                    trans_type = transaction['transaction_type']
                    qty_change = transaction['quantity_change'] or 0
                    cash_change = transaction['cash_change'] or 0
                    price = transaction['price'] or 0
                    
                    if symbol and trans_type:
                        # Initialize position if needed
                        if symbol not in positions:
                            positions[symbol] = {'quantity': 0, 'cost_basis': 0}
                        
                        # Update position using cost basis
                        old_qty = positions[symbol]['quantity']
                        new_qty = old_qty + qty_change
                        
                        if new_qty > 0 and qty_change > 0:  # Buying
                            # Weighted average cost basis
                            old_value = old_qty * positions[symbol]['cost_basis']
                            new_value = qty_change * price
                            positions[symbol]['cost_basis'] = (old_value + new_value) / new_qty
                        
                        positions[symbol]['quantity'] = new_qty
                        current_cash += cash_change
                        
                        # Track transactions for this day
                        if trans_date == trading_day:
                            day_transactions.append(f"{trans_type} {symbol} ({qty_change})")
            
            # Calculate equity value using cost basis
            equity_value = 0.0
            for symbol, position in positions.items():
                if position['quantity'] > 0:
                    equity_value += position['quantity'] * position['cost_basis']
            
            total_value = current_cash + equity_value
            
            daily_results.append({
                'analysis_id': analysis_id,
                'analysis_name': analysis_name,
                'date': trading_day,
                'total_value': total_value,
                'cash_position': current_cash,
                'equity_value': equity_value,
                'transaction_details': '; '.join(day_transactions) if day_transactions else None
            })
        
        return daily_results
    
    def _get_timeline_data_cost_basis_old(self, analysis_ids: List[int]) -> pd.DataFrame:
        """OLD VERSION - Fallback method using original cost basis calculation (INCLUDES WEEKENDS - PROBLEMATIC)"""
        try:
            conn = self.get_connection()
            
            # Create a placeholder string for the IN clause
            placeholders = ','.join(['%s'] * len(analysis_ids))
            
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = f"""
                    WITH daily_data AS (
                        -- Generate date series for each analysis (PROBLEM: includes weekends!)
                        SELECT 
                            pa.id as analysis_id,
                            pa.analysis_name,
                            pa.start_date,
                            pa.end_date,
                            pa.start_cash,
                            generate_series(pa.start_date, pa.end_date, interval '1 day')::date as date
                        FROM portfolio_analyses pa
                        WHERE pa.id IN ({placeholders})
                    ),
                    cumulative_transactions AS (
                        -- Get cumulative effect of transactions up to each date
                        SELECT 
                            dd.analysis_id,
                            dd.analysis_name,
                            dd.date,
                            dd.start_cash,
                            COALESCE(SUM(sc.cash_change) 
                                FILTER (WHERE sc.transaction_date <= dd.date AND sc.transaction_type != 'INITIAL'), 0) as cumulative_cash_change,
                            -- Get recent transactions for this date (for hover details)
                            STRING_AGG(
                                CASE WHEN sc.transaction_date = dd.date 
                                THEN sc.transaction_type || ' ' || sc.symbol || ' (' || sc.quantity_change || ')' 
                                ELSE NULL END, 
                                '; '
                            ) as transaction_details
                        FROM daily_data dd
                        LEFT JOIN portfolio_analysis_state_changes sc ON dd.analysis_id = sc.analysis_id
                        GROUP BY dd.analysis_id, dd.analysis_name, dd.date, dd.start_cash
                    ),
                    position_values AS (
                        -- Calculate position values for each symbol at each date using cost basis
                        SELECT 
                            ct.analysis_id,
                            ct.analysis_name,
                            ct.date,
                            ct.start_cash,
                            ct.cumulative_cash_change,
                            ct.transaction_details,
                            sc2.symbol,
                            SUM(sc2.quantity_change) as quantity,
                            CASE 
                                WHEN SUM(sc2.quantity_change) > 0 THEN
                                    ABS(SUM(CASE WHEN sc2.quantity_change > 0 THEN sc2.cash_change ELSE 0 END)) / 
                                    SUM(CASE WHEN sc2.quantity_change > 0 THEN sc2.quantity_change ELSE 0 END)
                                ELSE 0
                            END as avg_cost
                        FROM cumulative_transactions ct
                        LEFT JOIN portfolio_analysis_state_changes sc2 ON ct.analysis_id = sc2.analysis_id
                            AND sc2.transaction_date <= ct.date
                            AND sc2.transaction_type IN ('BUY', 'SELL')
                        GROUP BY ct.analysis_id, ct.analysis_name, ct.date, ct.start_cash, ct.cumulative_cash_change, ct.transaction_details, sc2.symbol
                        HAVING sc2.symbol IS NOT NULL
                    ),
                    portfolio_values AS (
                        -- Aggregate position values by date
                        SELECT 
                            pv.analysis_id,
                            pv.analysis_name, 
                            pv.date,
                            pv.start_cash,
                            pv.cumulative_cash_change,
                            pv.transaction_details,
                            -- Calculate current cash position
                            (pv.start_cash + pv.cumulative_cash_change) as cash_position,
                            -- Calculate equity value using cost basis
                            COALESCE(SUM(GREATEST(0, pv.quantity) * pv.avg_cost), 0) as equity_value
                        FROM position_values pv
                        GROUP BY pv.analysis_id, pv.analysis_name, pv.date, pv.start_cash, pv.cumulative_cash_change, pv.transaction_details
                        
                        UNION ALL
                        
                        -- Include dates with no positions (cash-only days)
                        SELECT 
                            ct.analysis_id,
                            ct.analysis_name,
                            ct.date,
                            ct.start_cash,
                            ct.cumulative_cash_change,
                            ct.transaction_details,
                            (ct.start_cash + ct.cumulative_cash_change) as cash_position,
                            0 as equity_value
                        FROM cumulative_transactions ct
                        WHERE NOT EXISTS (
                            SELECT 1 FROM position_values pv2 
                            WHERE pv2.analysis_id = ct.analysis_id 
                            AND pv2.date = ct.date
                        )
                    )
                    SELECT 
                        analysis_id,
                        analysis_name,
                        date,
                        MAX(cash_position) as cash_position,
                        MAX(equity_value) as equity_value,
                        (MAX(cash_position) + MAX(equity_value)) as total_value,
                        COALESCE(MAX(transaction_details), '') as transaction_details
                    FROM portfolio_values
                    GROUP BY analysis_id, analysis_name, date
                    ORDER BY analysis_id, date;
                """
                
                cur.execute(query, analysis_ids)
                results = cur.fetchall()
                
                if not results:
                    return pd.DataFrame()
                
                # Convert to DataFrame
                df = pd.DataFrame(results)
                
                # Ensure proper data types
                df['date'] = pd.to_datetime(df['date'])
                df['total_value'] = df['total_value'].astype(float)
                df['cash_position'] = df['cash_position'].astype(float)
                df['equity_value'] = df['equity_value'].astype(float)
                
                return df
                
        except Exception as e:
            logger.error(f"Error getting cost basis timeline data: {e}")
            return pd.DataFrame()
        finally:
            if 'conn' in locals():
                conn.close()
    
    def fetch_bulk_historical_prices(self, symbols: List[str], start_date: date, end_date: date) -> pd.DataFrame:
        """
        Fetch historical prices for multiple symbols efficiently, prioritizing local database
        
        Args:
            symbols: List of stock symbols (should include .HK suffix for Hong Kong stocks)
            start_date: Start date for price data
            end_date: End date for price data
            
        Returns:
            DataFrame with columns: symbol, date, close_price
        """
        try:
            if not symbols:
                return pd.DataFrame(columns=['symbol', 'date', 'close_price'])
            
            # Ensure HK symbols have .HK suffix
            formatted_symbols = []
            for symbol in symbols:
                if symbol.endswith('.HK'):
                    formatted_symbols.append(symbol)
                elif symbol.replace('.', '').isdigit():  # Hong Kong stock number
                    formatted_symbols.append(f"{symbol}.HK" if not symbol.endswith('.HK') else symbol)
                else:
                    formatted_symbols.append(symbol)
            
            logger.info(f"Fetching historical prices for symbols: {formatted_symbols}")
            logger.info(f"Date range: {start_date} to {end_date}")
            
            # First try: Get data from local database
            db_results = self._get_database_price_data(formatted_symbols, start_date, end_date)
            
            if not db_results.empty:
                # Check if we have complete data for all symbols
                missing_symbols = []
                for symbol in formatted_symbols:
                    symbol_data = db_results[db_results['symbol'] == symbol]
                    if symbol_data.empty:
                        missing_symbols.append(symbol)
                        logger.info(f"No database data found for {symbol}")
                
                if not missing_symbols:
                    logger.info(f"Successfully retrieved complete data from database for all {len(formatted_symbols)} symbols")
                    return db_results
                else:
                    logger.info(f"Database has partial data, missing {len(missing_symbols)} symbols: {missing_symbols}")
                    # Continue to Yahoo Finance for missing symbols
                    formatted_symbols = missing_symbols
            else:
                logger.info("No data found in database, falling back to Yahoo Finance")
            
            # Second try: Fetch missing data using yfinance bulk download (more efficient)
            try:
                # Add buffer dates to ensure we have data for weekends/holidays
                buffer_start = start_date - timedelta(days=5)
                buffer_end = end_date + timedelta(days=2)
                
                price_data = yf.download(
                    formatted_symbols,
                    start=buffer_start,
                    end=buffer_end,
                    progress=False,
                    threads=True
                )
                
                if price_data.empty:
                    logger.warning("No price data returned from Yahoo Finance")
                    return self._get_fallback_price_data(symbols, start_date, end_date)
                
                # Process the multi-level columns from yfinance
                results = []
                
                if len(formatted_symbols) == 1:
                    # Single symbol - simpler structure
                    symbol = formatted_symbols[0]
                    if 'Close' in price_data.columns:
                        close_prices = price_data['Close'].dropna()
                        for date_idx, price in close_prices.items():
                            results.append({
                                'symbol': symbol,
                                'date': date_idx.date(),
                                'close_price': float(price)
                            })
                else:
                    # Multiple symbols - multi-level columns
                    if 'Close' in price_data.columns:
                        close_data = price_data['Close']
                        for symbol in formatted_symbols:
                            if symbol in close_data.columns:
                                symbol_prices = close_data[symbol].dropna()
                                for date_idx, price in symbol_prices.items():
                                    results.append({
                                        'symbol': symbol,
                                        'date': date_idx.date(),
                                        'close_price': float(price)
                                    })
                
                if not results:
                    logger.warning("No valid price data extracted")
                    return self._get_fallback_price_data(symbols, start_date, end_date)
                
                # Create DataFrame and filter to requested date range
                df = pd.DataFrame(results)
                df['date'] = pd.to_datetime(df['date'])
                df = df[(df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)]
                
                # Fill missing dates using forward fill for each symbol
                df = self._fill_missing_price_dates(df, start_date, end_date)
                
                logger.info(f"Successfully fetched price data: {len(df)} records for {len(df['symbol'].unique())} symbols")
                return df
                
            except Exception as yf_error:
                logger.warning(f"Yahoo Finance bulk download failed: {yf_error}")
                return self._fetch_prices_individually(formatted_symbols, start_date, end_date)
                
        except Exception as e:
            logger.error(f"Error fetching bulk historical prices: {e}")
            return self._get_fallback_price_data(symbols, start_date, end_date)
    
    def _fetch_prices_individually(self, symbols: List[str], start_date: date, end_date: date) -> pd.DataFrame:
        """Fallback method to fetch prices one symbol at a time"""
        results = []
        
        for symbol in symbols:
            try:
                logger.info(f"Fetching individual price data for {symbol}")
                stock = yf.Ticker(symbol)
                hist = stock.history(start=start_date - timedelta(days=5), end=end_date + timedelta(days=2))
                
                if not hist.empty:
                    close_prices = hist['Close'].dropna()
                    for date_idx, price in close_prices.items():
                        if start_date <= date_idx.date() <= end_date:
                            results.append({
                                'symbol': symbol,
                                'date': date_idx.date(),
                                'close_price': float(price)
                            })
                
            except Exception as e:
                logger.warning(f"Failed to fetch individual data for {symbol}: {e}")
                continue
        
        df = pd.DataFrame(results)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df = self._fill_missing_price_dates(df, start_date, end_date)
        
        return df
    
    def _fill_missing_price_dates(self, df: pd.DataFrame, start_date: date, end_date: date) -> pd.DataFrame:
        """Fill missing dates for each symbol using forward fill"""
        if df.empty:
            return df
        
        filled_results = []
        
        for symbol in df['symbol'].unique():
            symbol_data = df[df['symbol'] == symbol].copy()
            symbol_data = symbol_data.sort_values('date')
            
            # Create complete date range
            date_range = pd.date_range(start=start_date, end=end_date, freq='D')
            
            # Reindex to include all dates
            symbol_data.set_index('date', inplace=True)
            symbol_data = symbol_data.reindex(date_range, method='ffill')  # Forward fill
            
            # Reset index and add back to results
            symbol_data.reset_index(inplace=True)
            symbol_data['date'] = symbol_data['index']
            symbol_data['symbol'] = symbol
            symbol_data = symbol_data[['symbol', 'date', 'close_price']].dropna()
            
            filled_results.append(symbol_data)
        
        if filled_results:
            result_df = pd.concat(filled_results, ignore_index=True)
            result_df['date'] = pd.to_datetime(result_df['date'])
            return result_df
        
        return pd.DataFrame(columns=['symbol', 'date', 'close_price'])
    
    def _get_database_price_data(self, symbols: List[str], start_date: date, end_date: date) -> pd.DataFrame:
        """Get price data from local database"""
        try:
            conn = self.get_connection()
            
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Query the database for price data
                cur.execute("""
                    SELECT symbol, trade_date as date, close_price
                    FROM daily_equity_technicals 
                    WHERE symbol = ANY(%s) 
                    AND trade_date BETWEEN %s AND %s
                    ORDER BY symbol, trade_date
                """, (symbols, start_date, end_date))
                
                results = cur.fetchall()
                
                if results:
                    # Convert to DataFrame
                    df = pd.DataFrame(results)
                    df['date'] = pd.to_datetime(df['date'])
                    logger.info(f"Retrieved {len(results)} records from database for {len(set(r['symbol'] for r in results))} symbols")
                    return df
                else:
                    logger.info("No price data found in database")
                    return pd.DataFrame(columns=['symbol', 'date', 'close_price'])
                    
        except Exception as e:
            logger.warning(f"Error querying database for price data: {e}")
            return pd.DataFrame(columns=['symbol', 'date', 'close_price'])
        finally:
            if 'conn' in locals():
                conn.close()

    def _get_fallback_price_data(self, symbols: List[str], start_date: date, end_date: date) -> pd.DataFrame:
        """Generate fallback price data, first trying database with expanded date range"""
        try:
            # First try: Check database with expanded date range (up to 30 days before/after)
            logger.info("Trying database fallback with expanded date range")
            expanded_start = start_date - timedelta(days=30)
            expanded_end = end_date + timedelta(days=30)
            
            db_results = self._get_database_price_data(symbols, expanded_start, expanded_end)
            
            if not db_results.empty:
                logger.info(f"Found database fallback data for {len(db_results['symbol'].unique())} symbols")
                
                # For each symbol, get the closest available data
                results = []
                for symbol in symbols:
                    symbol_data = db_results[db_results['symbol'] == symbol]
                    if not symbol_data.empty:
                        # Get the record closest to the end_date
                        symbol_data['date_diff'] = abs((symbol_data['date'].dt.date - end_date).dt.days)
                        closest_record = symbol_data.loc[symbol_data['date_diff'].idxmin()]
                        
                        results.append({
                            'symbol': symbol,
                            'date': end_date,
                            'close_price': closest_record['close_price']
                        })
                        logger.info(f"Using database fallback for {symbol}: {closest_record['close_price']} from {closest_record['date'].date()}")
                
                if results:
                    df = pd.DataFrame(results)
                    df['date'] = pd.to_datetime(df['date'])
                    return df
        
        except Exception as e:
            logger.warning(f"Database fallback failed: {e}")
        
        # Last resort: Use hardcoded fallback prices
        logger.warning("Using hardcoded fallback prices as last resort")
        fallback_prices = {
            "0005.HK": 100.10, "0316.HK": 140.50, "0388.HK": 447.60, "0700.HK": 599.00,
            "0823.HK": 41.26, "0857.HK": 7.39, "0939.HK": 7.49, "1810.HK": 53.20,
            "2888.HK": 144.50, "3690.HK": 116.30, "9618.HK": 121.30, "9988.HK": 121.50
        }
        
        results = []
        for symbol in symbols:
            # Ensure proper .HK format for lookup
            lookup_symbol = symbol if symbol.endswith('.HK') else f"{symbol}.HK"
            base_price = fallback_prices.get(lookup_symbol, 75.0)
            
            results.append({
                'symbol': lookup_symbol,
                'date': end_date,
                'close_price': base_price
            })
        
        df = pd.DataFrame(results)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
        
        logger.warning(f"Using hardcoded fallback price data for {len(symbols)} symbols")
        return df