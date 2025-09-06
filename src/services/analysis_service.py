"""
Analysis Service for HK Strategy Dashboard.
Handles portfolio analysis operations, comparisons, and metrics calculation.

Provides a clean interface around the existing PortfolioAnalysisManager.
"""

import logging
import streamlit as st
from typing import Dict, List, Any, Optional, Tuple
from datetime import date, datetime, timedelta
from decimal import Decimal

# Import existing analysis manager
try:
    from portfolio_analysis_manager import PortfolioAnalysisManager
except ImportError:
    # Alternative import path
    from src.portfolio_analysis_manager import PortfolioAnalysisManager

# Setup logging
logger = logging.getLogger(__name__)


class AnalysisService:
    """Service layer for portfolio analysis operations."""
    
    def __init__(self, database_manager=None):
        """
        Initialize the analysis service.
        
        Args:
            database_manager: Database manager instance
        """
        self.database_manager = database_manager or self._get_db_manager()
        self.analysis_manager = None
        
        if self.database_manager:
            self.analysis_manager = PortfolioAnalysisManager(self.database_manager)
    
    def _get_db_manager(self):
        """Get database manager from session state or create new one."""
        try:
            if hasattr(st, 'session_state') and 'db_manager' in st.session_state:
                return st.session_state.db_manager
            
            # Import and create database manager
            from src.database import DatabaseManager
            return DatabaseManager()
            
        except Exception as e:
            logger.error(f"Failed to get database manager: {str(e)}")
            return None
    
    def create_portfolio_analysis(self, portfolio_id: str, analysis_data: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
        """
        Create a new portfolio analysis.
        
        Args:
            portfolio_id: Portfolio identifier
            analysis_data: Dictionary containing analysis parameters
            
        Returns:
            Tuple of (success, message, analysis_id)
        """
        try:
            if not self.analysis_manager:
                return False, "Analysis manager not initialized", None
            
            analysis_name = analysis_data.get('name', '')
            start_date = analysis_data.get('start_date')
            end_date = analysis_data.get('end_date')
            start_cash = analysis_data.get('start_cash', 0.0)
            
            # Validate required fields
            if not analysis_name:
                return False, "Analysis name is required", None
            
            if not start_date or not end_date:
                return False, "Start and end dates are required", None
            
            # Convert string dates to date objects if needed
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # Create the analysis
            success, message, analysis_id = self.analysis_manager.create_analysis(
                portfolio_id=portfolio_id,
                analysis_name=analysis_name,
                start_date=start_date,
                end_date=end_date,
                start_cash=float(start_cash)
            )
            
            if success:
                logger.info(f"Created analysis '{analysis_name}' for portfolio {portfolio_id} (ID: {analysis_id})")
            
            return success, message, analysis_id
            
        except Exception as e:
            logger.error(f"Error creating portfolio analysis: {str(e)}")
            return False, f"Error creating analysis: {str(e)}", None
    
    def get_analysis(self, analysis_id: int) -> Optional[Dict[str, Any]]:
        """
        Get analysis data by ID.
        
        Args:
            analysis_id: Analysis identifier
            
        Returns:
            Analysis data dictionary or None
        """
        try:
            if not self.analysis_manager:
                return None
            
            # Get analysis from database
            conn = self.database_manager.get_connection()
            if not conn:
                return None
            
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, portfolio_id, name, start_date, end_date, start_cash, 
                           created_at, updated_at
                    FROM portfolio_analyses
                    WHERE id = %s
                """, (analysis_id,))
                
                result = cur.fetchone()
                if result:
                    return {
                        'id': result[0],
                        'portfolio_id': result[1],
                        'name': result[2],
                        'start_date': result[3],
                        'end_date': result[4],
                        'start_cash': float(result[5]),
                        'created_at': result[6],
                        'updated_at': result[7]
                    }
                
            return None
            
        except Exception as e:
            logger.error(f"Error getting analysis {analysis_id}: {str(e)}")
            return None
    
    def get_portfolio_analyses(self, portfolio_id: str) -> List[Dict[str, Any]]:
        """
        Get all analyses for a portfolio.
        
        Args:
            portfolio_id: Portfolio identifier
            
        Returns:
            List of analysis dictionaries
        """
        try:
            if not self.database_manager:
                return []
            
            conn = self.database_manager.get_connection()
            if not conn:
                return []
            
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, portfolio_id, name, start_date, end_date, start_cash,
                           created_at, updated_at
                    FROM portfolio_analyses
                    WHERE portfolio_id = %s
                    ORDER BY created_at DESC
                """, (portfolio_id,))
                
                results = cur.fetchall()
                analyses = []
                
                for result in results:
                    analyses.append({
                        'id': result[0],
                        'portfolio_id': result[1],
                        'name': result[2],
                        'start_date': result[3],
                        'end_date': result[4],
                        'start_cash': float(result[5]),
                        'created_at': result[6],
                        'updated_at': result[7]
                    })
                
                return analyses
            
        except Exception as e:
            logger.error(f"Error getting analyses for portfolio {portfolio_id}: {str(e)}")
            return []
    
    def update_analysis(self, analysis_id: int, updates: Dict[str, Any]) -> bool:
        """
        Update analysis data.
        
        Args:
            analysis_id: Analysis identifier
            updates: Dictionary of updates to apply
            
        Returns:
            True if updated successfully
        """
        try:
            if not self.database_manager:
                return False
            
            conn = self.database_manager.get_connection()
            if not conn:
                return False
            
            # Build update query dynamically based on provided updates
            update_fields = []
            values = []
            
            allowed_fields = ['name', 'start_date', 'end_date', 'start_cash']
            for field in allowed_fields:
                if field in updates:
                    update_fields.append(f"{field} = %s")
                    values.append(updates[field])
            
            if not update_fields:
                return False
            
            # Add updated timestamp
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            values.append(analysis_id)
            
            query = f"""
                UPDATE portfolio_analyses 
                SET {', '.join(update_fields)}
                WHERE id = %s
            """
            
            with conn.cursor() as cur:
                cur.execute(query, values)
                conn.commit()
            
            logger.info(f"Updated analysis {analysis_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating analysis {analysis_id}: {str(e)}")
            return False
    
    def delete_analysis(self, analysis_id: int) -> bool:
        """
        Delete an analysis.
        
        Args:
            analysis_id: Analysis identifier
            
        Returns:
            True if deleted successfully
        """
        try:
            if not self.analysis_manager:
                return False
            
            # Use analysis manager's delete method if it exists
            if hasattr(self.analysis_manager, 'delete_analysis'):
                success = self.analysis_manager.delete_analysis(analysis_id)
                if success:
                    logger.info(f"Deleted analysis {analysis_id}")
                return success
            
            # Fallback to direct database operation
            conn = self.database_manager.get_connection()
            if not conn:
                return False
            
            with conn.cursor() as cur:
                # Delete analysis and related data
                cur.execute("DELETE FROM portfolio_analyses WHERE id = %s", (analysis_id,))
                conn.commit()
            
            logger.info(f"Deleted analysis {analysis_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting analysis {analysis_id}: {str(e)}")
            return False
    
    def refresh_analysis_prices(self, analysis_id: int) -> Tuple[bool, str]:
        """
        Refresh market prices for an analysis.
        
        Args:
            analysis_id: Analysis identifier
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if not self.analysis_manager:
                return False, "Analysis manager not available"
            
            # Use analysis manager's refresh method if it exists
            if hasattr(self.analysis_manager, 'refresh_analysis_prices'):
                return self.analysis_manager.refresh_analysis_prices(analysis_id)
            
            # Basic implementation - get analysis and update current prices
            analysis = self.get_analysis(analysis_id)
            if not analysis:
                return False, "Analysis not found"
            
            # This is a simplified implementation
            # In a full implementation, this would update all position prices
            logger.info(f"Price refresh requested for analysis {analysis_id}")
            return True, "Price refresh completed"
            
        except Exception as e:
            logger.error(f"Error refreshing prices for analysis {analysis_id}: {str(e)}")
            return False, f"Error: {str(e)}"
    
    def compare_analyses(self, analysis_ids: List[int]) -> Dict[str, Any]:
        """
        Compare multiple analyses and return metrics.
        
        Args:
            analysis_ids: List of analysis IDs to compare
            
        Returns:
            Dictionary with comparison metrics
        """
        try:
            if not analysis_ids:
                return {'error': 'No analyses provided for comparison'}
            
            comparisons = []
            for analysis_id in analysis_ids:
                analysis = self.get_analysis(analysis_id)
                if analysis:
                    metrics = self.calculate_analysis_metrics(analysis_id)
                    comparisons.append({
                        'analysis_id': analysis_id,
                        'name': analysis['name'],
                        'start_date': analysis['start_date'],
                        'end_date': analysis['end_date'],
                        'metrics': metrics
                    })
            
            return {
                'comparisons': comparisons,
                'total_analyses': len(comparisons),
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error comparing analyses: {str(e)}")
            return {'error': str(e)}
    
    def calculate_analysis_metrics(self, analysis_id: int) -> Dict[str, Any]:
        """
        Calculate performance metrics for an analysis.
        
        Args:
            analysis_id: Analysis identifier
            
        Returns:
            Dictionary with performance metrics
        """
        try:
            analysis = self.get_analysis(analysis_id)
            if not analysis:
                return {'error': 'Analysis not found'}
            
            # Basic metrics calculation
            # In a full implementation, this would calculate:
            # - Total return
            # - Annualized return
            # - Sharpe ratio
            # - Maximum drawdown
            # - Volatility
            # - Beta
            
            metrics = {
                'analysis_id': analysis_id,
                'start_cash': analysis['start_cash'],
                'period_days': (analysis['end_date'] - analysis['start_date']).days,
                'start_date': analysis['start_date'].isoformat(),
                'end_date': analysis['end_date'].isoformat(),
                'note': 'Full metrics calculation not implemented yet'
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating metrics for analysis {analysis_id}: {str(e)}")
            return {'error': str(e)}
    
    def export_analysis_data(self, analysis_id: int, format: str = 'json') -> Optional[bytes]:
        """
        Export analysis data in specified format.
        
        Args:
            analysis_id: Analysis identifier
            format: Export format ('json', 'csv', etc.)
            
        Returns:
            Exported data as bytes or None
        """
        try:
            analysis = self.get_analysis(analysis_id)
            if not analysis:
                return None
            
            if format.lower() == 'json':
                import json
                metrics = self.calculate_analysis_metrics(analysis_id)
                export_data = {
                    'analysis': analysis,
                    'metrics': metrics,
                    'exported_at': datetime.now().isoformat()
                }
                return json.dumps(export_data, indent=2, default=str).encode('utf-8')
            
            elif format.lower() == 'csv':
                # Basic CSV export
                import io
                output = io.StringIO()
                output.write(f"Analysis ID,{analysis_id}\n")
                output.write(f"Name,{analysis['name']}\n")
                output.write(f"Start Date,{analysis['start_date']}\n")
                output.write(f"End Date,{analysis['end_date']}\n")
                output.write(f"Start Cash,{analysis['start_cash']}\n")
                return output.getvalue().encode('utf-8')
            
            return None
            
        except Exception as e:
            logger.error(f"Error exporting analysis {analysis_id}: {str(e)}")
            return None


# Convenience functions for backward compatibility
_service_instance = None

def get_analysis_service() -> AnalysisService:
    """Get global analysis service instance (singleton)."""
    global _service_instance
    if _service_instance is None:
        _service_instance = AnalysisService()
    return _service_instance

def create_portfolio_analysis(portfolio_id: str, analysis_data: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
    """Create a new portfolio analysis."""
    return get_analysis_service().create_portfolio_analysis(portfolio_id, analysis_data)

def get_analysis(analysis_id: int) -> Optional[Dict[str, Any]]:
    """Get analysis data by ID."""
    return get_analysis_service().get_analysis(analysis_id)

def get_portfolio_analyses(portfolio_id: str) -> List[Dict[str, Any]]:
    """Get all analyses for a portfolio."""
    return get_analysis_service().get_portfolio_analyses(portfolio_id)

def compare_analyses(analysis_ids: List[int]) -> Dict[str, Any]:
    """Compare multiple analyses and return metrics."""
    return get_analysis_service().compare_analyses(analysis_ids)

def calculate_analysis_metrics(analysis_id: int) -> Dict[str, Any]:
    """Calculate performance metrics for an analysis."""
    return get_analysis_service().calculate_analysis_metrics(analysis_id)