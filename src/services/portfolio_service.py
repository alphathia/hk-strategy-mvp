"""
Portfolio Service for HK Strategy Dashboard.
Wrapper around the existing PortfolioManager with enhanced functionality.

Provides a clean interface for portfolio CRUD operations and calculations.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
import copy

# Import existing portfolio manager
from portfolio_manager import PortfolioManager, get_portfolio_manager

# Setup logging
logger = logging.getLogger(__name__)


class PortfolioService:
    """Service layer for portfolio management operations."""
    
    def __init__(self, portfolio_manager: Optional[PortfolioManager] = None):
        """
        Initialize the portfolio service.
        
        Args:
            portfolio_manager: Existing portfolio manager instance (optional)
        """
        self.portfolio_manager = portfolio_manager or get_portfolio_manager()
        
    def create_portfolio(self, portfolio_id: str, name: str, description: str = "") -> bool:
        """
        Create a new portfolio.
        
        Args:
            portfolio_id: Unique portfolio identifier
            name: Display name for the portfolio
            description: Optional description
            
        Returns:
            True if created successfully
        """
        try:
            portfolio_data = {
                'name': name,
                'description': description,
                'positions': [],
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            success = self.portfolio_manager.create_portfolio(portfolio_id, portfolio_data)
            if success:
                logger.info(f"Created portfolio: {portfolio_id} ({name})")
            return success
            
        except Exception as e:
            logger.error(f"Error creating portfolio {portfolio_id}: {str(e)}")
            return False
    
    def get_portfolio(self, portfolio_id: str) -> Optional[Dict[str, Any]]:
        """
        Get portfolio data by ID.
        
        Args:
            portfolio_id: Portfolio identifier
            
        Returns:
            Portfolio data dictionary or None
        """
        try:
            portfolios = self.portfolio_manager.get_all_portfolios()
            return portfolios.get(portfolio_id)
        except Exception as e:
            logger.error(f"Error getting portfolio {portfolio_id}: {str(e)}")
            return None
    
    def get_all_portfolios(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all portfolios.
        
        Returns:
            Dictionary of all portfolios
        """
        try:
            return self.portfolio_manager.get_all_portfolios()
        except Exception as e:
            logger.error(f"Error getting all portfolios: {str(e)}")
            return {}
    
    def update_portfolio(self, portfolio_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update portfolio information.
        
        Args:
            portfolio_id: Portfolio identifier
            updates: Dictionary of updates to apply
            
        Returns:
            True if updated successfully
        """
        try:
            portfolio = self.get_portfolio(portfolio_id)
            if not portfolio:
                return False
            
            # Apply updates
            portfolio.update(updates)
            portfolio['updated_at'] = datetime.now().isoformat()
            
            success = self.portfolio_manager.save_portfolio(portfolio_id, portfolio)
            if success:
                logger.info(f"Updated portfolio: {portfolio_id}")
            return success
            
        except Exception as e:
            logger.error(f"Error updating portfolio {portfolio_id}: {str(e)}")
            return False
    
    def delete_portfolio(self, portfolio_id: str) -> bool:
        """
        Delete a portfolio and all associated data.
        
        Args:
            portfolio_id: Portfolio identifier
            
        Returns:
            True if deleted successfully
        """
        try:
            success = self.portfolio_manager.delete_portfolio(portfolio_id)
            if success:
                logger.info(f"Deleted portfolio: {portfolio_id}")
            return success
            
        except Exception as e:
            logger.error(f"Error deleting portfolio {portfolio_id}: {str(e)}")
            return False
    
    def copy_portfolio(self, source_id: str, new_portfolio_id: str, new_name: str) -> bool:
        """
        Create a copy of an existing portfolio.
        
        Args:
            source_id: Source portfolio ID
            new_portfolio_id: New portfolio ID
            new_name: New portfolio name
            
        Returns:
            True if copied successfully
        """
        try:
            source_portfolio = self.get_portfolio(source_id)
            if not source_portfolio:
                logger.error(f"Source portfolio {source_id} not found")
                return False
            
            # Create deep copy and update metadata
            new_portfolio = copy.deepcopy(source_portfolio)
            new_portfolio['name'] = new_name
            new_portfolio['description'] = f"Copy of {source_portfolio.get('name', source_id)}"
            new_portfolio['created_at'] = datetime.now().isoformat()
            new_portfolio['updated_at'] = datetime.now().isoformat()
            
            success = self.portfolio_manager.create_portfolio(new_portfolio_id, new_portfolio)
            if success:
                logger.info(f"Copied portfolio {source_id} to {new_portfolio_id}")
            return success
            
        except Exception as e:
            logger.error(f"Error copying portfolio {source_id}: {str(e)}")
            return False
    
    def add_position(self, portfolio_id: str, symbol: str, quantity: int, cost_per_share: float, sector: str = "Unknown") -> bool:
        """
        Add a new position to portfolio.
        
        Args:
            portfolio_id: Portfolio identifier
            symbol: Stock symbol
            quantity: Number of shares
            cost_per_share: Average cost per share
            sector: Stock sector (optional)
            
        Returns:
            True if position added successfully
        """
        try:
            portfolio = self.get_portfolio(portfolio_id)
            if not portfolio:
                return False
            
            # Check if position already exists
            positions = portfolio.get('positions', [])
            for i, pos in enumerate(positions):
                if pos.get('symbol') == symbol:
                    # Update existing position
                    total_cost = (pos['quantity'] * pos['cost_per_share']) + (quantity * cost_per_share)
                    total_quantity = pos['quantity'] + quantity
                    new_avg_cost = total_cost / total_quantity if total_quantity > 0 else cost_per_share
                    
                    positions[i] = {
                        'symbol': symbol,
                        'quantity': total_quantity,
                        'cost_per_share': round(new_avg_cost, 2),
                        'sector': sector,
                        'updated_at': datetime.now().isoformat()
                    }
                    break
            else:
                # Add new position
                new_position = {
                    'symbol': symbol,
                    'quantity': quantity,
                    'cost_per_share': round(cost_per_share, 2),
                    'sector': sector,
                    'added_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                positions.append(new_position)
            
            portfolio['positions'] = positions
            success = self.update_portfolio(portfolio_id, {'positions': positions})
            
            if success:
                logger.info(f"Added position {symbol} to portfolio {portfolio_id}")
            return success
            
        except Exception as e:
            logger.error(f"Error adding position {symbol} to portfolio {portfolio_id}: {str(e)}")
            return False
    
    def update_position(self, portfolio_id: str, symbol: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing position.
        
        Args:
            portfolio_id: Portfolio identifier
            symbol: Stock symbol
            updates: Dictionary of position updates
            
        Returns:
            True if position updated successfully
        """
        try:
            portfolio = self.get_portfolio(portfolio_id)
            if not portfolio:
                return False
            
            positions = portfolio.get('positions', [])
            for i, pos in enumerate(positions):
                if pos.get('symbol') == symbol:
                    positions[i].update(updates)
                    positions[i]['updated_at'] = datetime.now().isoformat()
                    
                    success = self.update_portfolio(portfolio_id, {'positions': positions})
                    if success:
                        logger.info(f"Updated position {symbol} in portfolio {portfolio_id}")
                    return success
            
            logger.warning(f"Position {symbol} not found in portfolio {portfolio_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error updating position {symbol} in portfolio {portfolio_id}: {str(e)}")
            return False
    
    def remove_position(self, portfolio_id: str, symbol: str) -> bool:
        """
        Remove a position from portfolio.
        
        Args:
            portfolio_id: Portfolio identifier
            symbol: Stock symbol to remove
            
        Returns:
            True if position removed successfully
        """
        try:
            portfolio = self.get_portfolio(portfolio_id)
            if not portfolio:
                return False
            
            positions = portfolio.get('positions', [])
            original_count = len(positions)
            positions = [pos for pos in positions if pos.get('symbol') != symbol]
            
            if len(positions) < original_count:
                success = self.update_portfolio(portfolio_id, {'positions': positions})
                if success:
                    logger.info(f"Removed position {symbol} from portfolio {portfolio_id}")
                return success
            else:
                logger.warning(f"Position {symbol} not found in portfolio {portfolio_id}")
                return False
            
        except Exception as e:
            logger.error(f"Error removing position {symbol} from portfolio {portfolio_id}: {str(e)}")
            return False
    
    def get_portfolio_positions(self, portfolio_id: str) -> List[Dict[str, Any]]:
        """
        Get all positions for a portfolio.
        
        Args:
            portfolio_id: Portfolio identifier
            
        Returns:
            List of position dictionaries
        """
        try:
            portfolio = self.get_portfolio(portfolio_id)
            return portfolio.get('positions', []) if portfolio else []
        except Exception as e:
            logger.error(f"Error getting positions for portfolio {portfolio_id}: {str(e)}")
            return []
    
    def calculate_portfolio_value(self, portfolio_id: str, current_prices: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Calculate total portfolio value and metrics.
        
        Args:
            portfolio_id: Portfolio identifier
            current_prices: Dictionary of current prices (optional)
            
        Returns:
            Dictionary with portfolio value metrics
        """
        try:
            positions = self.get_portfolio_positions(portfolio_id)
            if not positions:
                return {
                    'total_cost': 0.0,
                    'total_market_value': 0.0,
                    'total_pnl': 0.0,
                    'total_pnl_percentage': 0.0,
                    'positions_count': 0
                }
            
            total_cost = 0.0
            total_market_value = 0.0
            
            for position in positions:
                symbol = position.get('symbol', '')
                quantity = position.get('quantity', 0)
                cost_per_share = position.get('cost_per_share', 0.0)
                
                position_cost = quantity * cost_per_share
                total_cost += position_cost
                
                # Use current price if available, otherwise use cost price
                current_price = cost_per_share
                if current_prices and symbol in current_prices:
                    current_price = current_prices[symbol]
                
                position_market_value = quantity * current_price
                total_market_value += position_market_value
            
            total_pnl = total_market_value - total_cost
            total_pnl_percentage = (total_pnl / total_cost * 100) if total_cost > 0 else 0.0
            
            return {
                'total_cost': round(total_cost, 2),
                'total_market_value': round(total_market_value, 2),
                'total_pnl': round(total_pnl, 2),
                'total_pnl_percentage': round(total_pnl_percentage, 2),
                'positions_count': len(positions)
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio value for {portfolio_id}: {str(e)}")
            return {'error': str(e)}
    
    def get_portfolio_performance(self, portfolio_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Calculate portfolio performance over a period.
        
        Args:
            portfolio_id: Portfolio identifier
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Dictionary with performance metrics
        """
        try:
            # This is a placeholder for more advanced performance calculation
            # In a full implementation, this would calculate historical performance
            # based on historical price data and position changes over time
            
            current_metrics = self.calculate_portfolio_value(portfolio_id)
            
            return {
                'portfolio_id': portfolio_id,
                'start_date': start_date,
                'end_date': end_date,
                'current_value': current_metrics.get('total_market_value', 0),
                'current_pnl': current_metrics.get('total_pnl', 0),
                'current_pnl_percentage': current_metrics.get('total_pnl_percentage', 0),
                'note': 'Historical performance calculation not implemented yet'
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio performance for {portfolio_id}: {str(e)}")
            return {'error': str(e)}
    
    def validate_portfolio_name(self, name: str, exclude_id: Optional[str] = None) -> Tuple[bool, str]:
        """
        Validate portfolio name for uniqueness and format.
        
        Args:
            name: Portfolio name to validate
            exclude_id: Portfolio ID to exclude from uniqueness check
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not name or not name.strip():
                return False, "Portfolio name cannot be empty"
            
            if len(name.strip()) < 3:
                return False, "Portfolio name must be at least 3 characters long"
            
            if len(name.strip()) > 100:
                return False, "Portfolio name cannot exceed 100 characters"
            
            # Check for uniqueness
            portfolios = self.get_all_portfolios()
            for portfolio_id, portfolio_data in portfolios.items():
                if portfolio_id == exclude_id:
                    continue
                if portfolio_data.get('name', '').lower() == name.strip().lower():
                    return False, "A portfolio with this name already exists"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validating portfolio name '{name}': {str(e)}")
            return False, "Error validating portfolio name"


# Convenience functions for backward compatibility
_service_instance = None

def get_portfolio_service() -> PortfolioService:
    """Get global portfolio service instance (singleton)."""
    global _service_instance
    if _service_instance is None:
        _service_instance = PortfolioService()
    return _service_instance

def create_portfolio(portfolio_id: str, name: str, description: str = "") -> bool:
    """Create a new portfolio."""
    return get_portfolio_service().create_portfolio(portfolio_id, name, description)

def get_portfolio(portfolio_id: str) -> Optional[Dict[str, Any]]:
    """Get portfolio data by ID."""
    return get_portfolio_service().get_portfolio(portfolio_id)

def get_all_portfolios() -> Dict[str, Dict[str, Any]]:
    """Get all portfolios.""" 
    return get_portfolio_service().get_all_portfolios()

def add_position(portfolio_id: str, symbol: str, quantity: int, cost_per_share: float, sector: str = "Unknown") -> bool:
    """Add a new position to portfolio."""
    return get_portfolio_service().add_position(portfolio_id, symbol, quantity, cost_per_share, sector)

def calculate_portfolio_value(portfolio_id: str, current_prices: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """Calculate total portfolio value and metrics."""
    return get_portfolio_service().calculate_portfolio_value(portfolio_id, current_prices)