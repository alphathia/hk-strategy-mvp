"""
Portfolio Analysis Manager

Handles saving, loading, and managing portfolio value analyses
with database persistence and caching capabilities.
"""

import pandas as pd
import json
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
import logging

try:
    from .portfolio_calculator import portfolio_calculator, PortfolioMetrics
    from .hkex_calendar import validate_hkex_analysis_period
except ImportError:
    from portfolio_calculator import portfolio_calculator, PortfolioMetrics
    from hkex_calendar import validate_hkex_analysis_period

logger = logging.getLogger(__name__)

class AnalysisManager:
    """
    Manages portfolio analyses including creation, saving, loading,
    and retrieval of historical analysis results.
    """
    
    def __init__(self, db_manager):
        """
        Initialize Analysis Manager with database connection.
        
        Args:
            db_manager: DatabaseManager instance for data persistence
        """
        self.db_manager = db_manager
    
    def create_analysis(
        self,
        name: str,
        start_date: date,
        end_date: date,
        positions: Dict[str, int],
        cash_amount: float = 0.0,
        user_notes: str = "",
        save_analysis: bool = True
    ) -> Tuple[int, pd.DataFrame, PortfolioMetrics]:
        """
        Create a new portfolio analysis.
        
        Args:
            name: Analysis name
            start_date: Analysis start date
            end_date: Analysis end date
            positions: Portfolio positions (symbol -> quantity)
            cash_amount: Cash component
            user_notes: Optional user notes
            save_analysis: Whether to save to database
            
        Returns:
            Tuple of (analysis_id, daily_values_df, metrics)
        """
        logger.info(f"Creating analysis '{name}' from {start_date} to {end_date}")
        
        # Validate date range
        is_valid, message, adj_start, adj_end = validate_hkex_analysis_period(start_date, end_date)
        
        if not is_valid:
            raise ValueError(f"Invalid analysis period: {message}")
        
        if adj_start != start_date or adj_end != end_date:
            logger.info(f"Dates adjusted: {message}")
            start_date, end_date = adj_start, adj_end
        
        # Run portfolio analysis
        daily_values_df, metrics = portfolio_calculator.run_portfolio_analysis(
            positions, start_date, end_date, cash_amount
        )
        
        analysis_id = None
        if save_analysis:
            # Try to save analysis to database
            try:
                analysis_id = self._save_analysis_to_db(
                    name, start_date, end_date, user_notes, metrics, daily_values_df
                )
                logger.info(f"Analysis saved with ID: {analysis_id}")
            except Exception as e:
                logger.warning(f"Failed to save analysis to database: {e}")
                logger.info("Analysis will continue without database save")
                # Continue without database save - analysis_id remains None
        
        return analysis_id, daily_values_df, metrics
    
    def _save_analysis_to_db(
        self,
        name: str,
        start_date: date,
        end_date: date,
        user_notes: str,
        metrics: PortfolioMetrics,
        daily_values_df: pd.DataFrame
    ) -> int:
        """
        Save analysis results to database.
        
        Returns:
            Analysis ID
        """
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    # Insert analysis record
                    insert_analysis_query = """
                    INSERT INTO portfolio_analyses 
                    (name, start_date, end_date, user_notes, start_pv, end_pv, 
                     total_return, max_drawdown, volatility)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """
                    
                    cur.execute(insert_analysis_query, (
                        name,
                        start_date,
                        end_date,
                        user_notes,
                        metrics.start_value,
                        metrics.end_value,
                        metrics.total_return_pct / 100.0,  # Store as decimal
                        metrics.max_drawdown_pct / 100.0,  # Store as decimal
                        metrics.volatility
                    ))
                    
                    analysis_id = cur.fetchone()[0]
                    
                    # Insert daily values
                    insert_values_query = """
                    INSERT INTO portfolio_value_history 
                    (analysis_id, trade_date, portfolio_value, cash_value, total_value, 
                     daily_change, daily_return, top_contributors)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    values_data = []
                    for _, row in daily_values_df.iterrows():
                        # Convert top_contributors to JSON
                        contributors_json = json.dumps(row['top_contributors']) if row['top_contributors'] else None
                        
                        values_data.append((
                            analysis_id,
                            row['trade_date'],
                            row['portfolio_value'],
                            row['cash_value'],
                            row['total_value'],
                            row['daily_change'] if pd.notna(row['daily_change']) else None,
                            row['daily_return'] if pd.notna(row['daily_return']) else None,
                            contributors_json
                        ))
                    
                    cur.executemany(insert_values_query, values_data)
                    conn.commit()
                    
                    return analysis_id
                    
        except Exception as e:
            logger.error(f"Error saving analysis to database: {e}")
            raise
    
    def load_analysis(self, analysis_id: int) -> Tuple[Dict, pd.DataFrame, PortfolioMetrics]:
        """
        Load a saved analysis from database.
        
        Args:
            analysis_id: Analysis ID to load
            
        Returns:
            Tuple of (analysis_info, daily_values_df, metrics)
        """
        # Ensure analysis_id is a Python int (not numpy.int64)
        analysis_id = int(analysis_id)
        
        try:
            with self.db_manager.get_connection() as conn:
                logger.info(f"Loading analysis metadata for ID {analysis_id}")
                
                # Load analysis metadata
                analysis_query = """
                SELECT id, name, start_date, end_date, created_at, user_notes,
                       start_pv, end_pv, total_return, max_drawdown, volatility
                FROM portfolio_analyses
                WHERE id = %s
                """
                
                analysis_df = pd.read_sql(analysis_query, conn, params=[analysis_id])
                
                if analysis_df.empty:
                    raise ValueError(f"Analysis {analysis_id} not found")
                
                analysis_info = analysis_df.iloc[0].to_dict()
                logger.info(f"Loaded analysis metadata: {analysis_info['name']}")
                
                # Load daily values
                logger.info(f"Loading daily values for analysis {analysis_id}")
                values_query = """
                SELECT trade_date, portfolio_value, cash_value, total_value,
                       daily_change, daily_return, top_contributors
                FROM portfolio_value_history
                WHERE analysis_id = %s
                ORDER BY trade_date
                """
                
                daily_values_df = pd.read_sql(values_query, conn, params=[analysis_id])
                
                if daily_values_df.empty:
                    raise ValueError(f"No daily values found for analysis {analysis_id}")
                
                logger.info(f"Loaded {len(daily_values_df)} daily values, parsing contributors...")
                
                # Parse JSON contributors with robust type handling
                def safe_parse_contributors(x):
                    """Safely parse top_contributors field regardless of data type"""
                    if not x:  # None, empty string, etc.
                        return []
                    if isinstance(x, (list, dict)):  # Already parsed
                        return x
                    if isinstance(x, str):  # JSON string to parse
                        try:
                            return json.loads(x)
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse contributors JSON: {x}")
                            return []
                    logger.warning(f"Unexpected contributor type {type(x)}: {x}")
                    return []  # Fallback for unexpected types
                
                daily_values_df['top_contributors'] = daily_values_df['top_contributors'].apply(safe_parse_contributors)
                logger.info("Successfully parsed contributors")
                
                # Reconstruct metrics object
                metrics = PortfolioMetrics(
                    start_value=float(analysis_info['start_pv']),
                    end_value=float(analysis_info['end_pv']),
                    total_return=float(analysis_info['end_pv'] - analysis_info['start_pv']),
                    total_return_pct=float(analysis_info['total_return'] * 100),
                    max_drawdown=0.0,  # Will be recalculated if needed
                    max_drawdown_pct=float(analysis_info['max_drawdown'] * 100),
                    volatility=float(analysis_info['volatility']),
                    sharpe_ratio=None,  # Not stored, would need recalculation
                    trading_days=len(daily_values_df),
                    best_day=(daily_values_df.iloc[0]['trade_date'], 0.0),  # Simplified
                    worst_day=(daily_values_df.iloc[0]['trade_date'], 0.0)   # Simplified
                )
                
                logger.info(f"Loaded analysis '{analysis_info['name']}' with {len(daily_values_df)} days")
                
                return analysis_info, daily_values_df, metrics
                
        except Exception as e:
            logger.error(f"Error loading analysis {analysis_id}: {e}")
            raise
    
    def list_analyses(self, limit: int = 50) -> pd.DataFrame:
        """
        Get list of saved analyses.
        
        Args:
            limit: Maximum number of analyses to return
            
        Returns:
            DataFrame with analysis summaries
        """
        try:
            with self.db_manager.get_connection() as conn:
                query = """
                SELECT id, name, start_date, end_date, created_at, 
                       start_pv, end_pv, total_return, max_drawdown,
                       (SELECT COUNT(*) FROM portfolio_value_history pv WHERE pv.analysis_id = pa.id) as trading_days
                FROM portfolio_analyses pa
                ORDER BY created_at DESC
                LIMIT %s
                """
                
                analyses_df = pd.read_sql(query, conn, params=[limit])
                
                if not analyses_df.empty:
                    # Calculate additional summary fields
                    analyses_df['return_pct'] = analyses_df['total_return'] * 100
                    analyses_df['drawdown_pct'] = analyses_df['max_drawdown'] * 100
                    analyses_df['period_days'] = (
                        pd.to_datetime(analyses_df['end_date']) - 
                        pd.to_datetime(analyses_df['start_date'])
                    ).dt.days
                
                return analyses_df
                
        except Exception as e:
            logger.error(f"Error listing analyses: {e}")
            return pd.DataFrame()
    
    def delete_analysis(self, analysis_id: int) -> bool:
        """
        Delete a saved analysis.
        
        Args:
            analysis_id: Analysis ID to delete
            
        Returns:
            True if successful
        """
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    # Delete analysis (cascade will handle daily values)
                    cur.execute("DELETE FROM portfolio_analyses WHERE id = %s", (analysis_id,))
                    conn.commit()
                    
                    if cur.rowcount > 0:
                        logger.info(f"Deleted analysis {analysis_id}")
                        return True
                    else:
                        logger.warning(f"Analysis {analysis_id} not found for deletion")
                        return False
                        
        except Exception as e:
            logger.error(f"Error deleting analysis {analysis_id}: {e}")
            return False
    
    def get_analysis_summary(self, analysis_id: int) -> Dict:
        """
        Get quick summary of an analysis without loading full data.
        
        Args:
            analysis_id: Analysis ID
            
        Returns:
            Dictionary with summary information
        """
        try:
            with self.db_manager.get_connection() as conn:
                query = """
                SELECT pa.*, 
                       (SELECT COUNT(*) FROM portfolio_value_history pv WHERE pv.analysis_id = pa.id) as trading_days,
                       (SELECT MIN(trade_date) FROM portfolio_value_history pv WHERE pv.analysis_id = pa.id) as actual_start,
                       (SELECT MAX(trade_date) FROM portfolio_value_history pv WHERE pv.analysis_id = pa.id) as actual_end
                FROM portfolio_analyses pa
                WHERE pa.id = %s
                """
                
                result = pd.read_sql(query, conn, params=[analysis_id])
                
                if result.empty:
                    return {}
                
                summary = result.iloc[0].to_dict()
                summary['return_pct'] = summary['total_return'] * 100
                summary['drawdown_pct'] = summary['max_drawdown'] * 100
                
                return summary
                
        except Exception as e:
            logger.error(f"Error getting analysis summary {analysis_id}: {e}")
            return {}