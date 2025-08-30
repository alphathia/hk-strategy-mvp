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
from datetime import date, datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from decimal import Decimal

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
            
            # Calculate current cash (start cash + all cash changes)
            cur.execute("""
                SELECT COALESCE(SUM(cash_change), 0) as total_cash_changes
                FROM portfolio_analysis_state_changes
                WHERE analysis_id = %s
            """, (analysis_id,))
            
            result = cur.fetchone()
            total_cash_changes = float(result['total_cash_changes'] if isinstance(result, dict) else result[0])
            end_cash = start_cash + total_cash_changes
            
            # For now, use start equity value as end equity value
            # In a real system, this would calculate current market value
            end_equity_value = start_equity_value
            
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