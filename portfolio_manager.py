"""
Portfolio Manager - Handles database integration and portfolio isolation
"""
import psycopg2
import logging
from typing import Dict, List, Any, Optional
import copy
from src.config_manager import get_config

logger = logging.getLogger(__name__)

class PortfolioManager:
    """Manages portfolio data with database persistence and proper isolation"""
    
    def __init__(self):
        self.config = get_config()
        self._connection = None
        self._initialize_database()
    
    def get_connection(self):
        """Get database connection with retry"""
        try:
            if self._connection is None or self._connection.closed:
                db_url = self.config.get_database_url()
                logger.debug(f"Attempting connection with config URL: {db_url}")
                self._connection = psycopg2.connect(db_url)
            return self._connection
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            # Fallback to environment variables
            import os
            db_password = os.getenv('DATABASE_PASSWORD', 'YOUR_PASSWORD')
            fallback_url = f"postgresql://trader:{db_password}@localhost:5432/hk_strategy"
            logger.debug(f"Attempting fallback connection with URL: {fallback_url}")
            try:
                self._connection = psycopg2.connect(fallback_url)
                logger.info("Fallback connection successful")
                return self._connection
            except Exception as e2:
                logger.error(f"Fallback connection also failed: {e2}")
                raise e2
    
    def _initialize_database(self):
        """Initialize portfolio management tables"""
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                # Create portfolios table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS portfolios (
                        portfolio_id VARCHAR(50) PRIMARY KEY,
                        name VARCHAR(200) NOT NULL,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create portfolio_positions table (separate from main positions table)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS portfolio_holdings (
                        id SERIAL PRIMARY KEY,
                        portfolio_id VARCHAR(50) REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
                        symbol VARCHAR(20) NOT NULL,
                        company_name VARCHAR(200),
                        quantity INTEGER NOT NULL DEFAULT 0,
                        avg_cost DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                        sector VARCHAR(50) DEFAULT 'Other',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(portfolio_id, symbol)
                    )
                """)
                
                conn.commit()
                logger.info("Portfolio management tables initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize portfolio database: {e}")
            # Non-fatal error - continue with session-only mode
    
    def get_all_portfolios(self) -> Dict[str, Dict[str, Any]]:
        """Get all portfolios from database with their positions"""
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                # Get portfolios
                cur.execute("""
                    SELECT portfolio_id, name, description 
                    FROM portfolios 
                    ORDER BY created_at
                """)
                portfolio_rows = cur.fetchall()
                
                portfolios = {}
                for portfolio_id, name, description in portfolio_rows:
                    # Get positions for this portfolio
                    cur.execute("""
                        SELECT symbol, company_name, quantity, avg_cost, sector
                        FROM portfolio_holdings
                        WHERE portfolio_id = %s
                        ORDER BY symbol
                    """, (portfolio_id,))
                    
                    positions = []
                    for symbol, company_name, quantity, avg_cost, sector in cur.fetchall():
                        positions.append({
                            'symbol': symbol,
                            'company_name': company_name or 'Unknown Company',
                            'quantity': int(quantity),
                            'avg_cost': float(avg_cost),
                            'sector': sector or 'Other'
                        })
                    
                    portfolios[portfolio_id] = {
                        'name': name,
                        'description': description or '',
                        'positions': positions
                    }
                
                # If no portfolios found in database, try to migrate from existing data
                if not portfolios:
                    logger.info("No portfolios found in database, initializing with default portfolio")
                    default_portfolio = self._get_default_portfolio()
                    
                    # Try to save the default portfolio to database
                    for portfolio_id, portfolio_data in default_portfolio.items():
                        success = self.save_portfolio(portfolio_id, portfolio_data)
                        if success:
                            logger.info(f"Migrated default portfolio {portfolio_id} to database")
                        else:
                            logger.warning(f"Failed to migrate portfolio {portfolio_id} to database")
                    
                    return default_portfolio
                
                return portfolios
                
        except Exception as e:
            logger.error(f"Failed to load portfolios from database: {e}")
            # Return default portfolio if database fails
            default = self._get_default_portfolio()
            logger.info("Returning default portfolio due to database error")
            return default
    
    def _get_default_portfolio(self) -> Dict[str, Dict[str, Any]]:
        """Return default HKEX portfolio if database is unavailable"""
        return {
            "HKEX_Base": {
                "name": "HKEX Base Portfolio",
                "description": "Primary Hong Kong equity holdings (Session Only)",
                "positions": [
                    {"symbol": "0005.HK", "company_name": "HSBC Holdings plc", "quantity": 13428, "avg_cost": 38.50, "sector": "Financials"},
                    {"symbol": "0316.HK", "company_name": "Orient Overseas", "quantity": 100, "avg_cost": 95.00, "sector": "Other"},
                    {"symbol": "0388.HK", "company_name": "Hong Kong Exchanges", "quantity": 300, "avg_cost": 280.00, "sector": "Financials"},
                    {"symbol": "0700.HK", "company_name": "Tencent Holdings Ltd", "quantity": 3100, "avg_cost": 320.50, "sector": "Tech"},
                    {"symbol": "0823.HK", "company_name": "Link REIT", "quantity": 1300, "avg_cost": 42.80, "sector": "REIT"},
                    {"symbol": "0939.HK", "company_name": "China Construction Bank", "quantity": 26700, "avg_cost": 5.45, "sector": "Financials"},
                    {"symbol": "1810.HK", "company_name": "Xiaomi Corporation", "quantity": 2000, "avg_cost": 12.30, "sector": "Tech"},
                    {"symbol": "2888.HK", "company_name": "Standard Chartered PLC", "quantity": 348, "avg_cost": 145.00, "sector": "Financials"},
                    {"symbol": "3690.HK", "company_name": "Meituan", "quantity": 340, "avg_cost": 95.00, "sector": "Tech"},
                    {"symbol": "9618.HK", "company_name": "JD.com", "quantity": 133, "avg_cost": 125.00, "sector": "Tech"},
                    {"symbol": "9988.HK", "company_name": "Alibaba Group", "quantity": 2000, "avg_cost": 115.00, "sector": "Tech"}
                ]
            }
        }
    
    def save_portfolio(self, portfolio_id: str, portfolio_data: Dict[str, Any]) -> bool:
        """Save portfolio to database with proper isolation"""
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                # Insert/update portfolio metadata
                cur.execute("""
                    INSERT INTO portfolios (portfolio_id, name, description, updated_at)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (portfolio_id) 
                    DO UPDATE SET 
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        updated_at = CURRENT_TIMESTAMP
                """, (portfolio_id, portfolio_data['name'], portfolio_data['description']))
                
                # Clear existing positions for this portfolio
                cur.execute("DELETE FROM portfolio_holdings WHERE portfolio_id = %s", (portfolio_id,))
                
                # Insert new positions
                for position in portfolio_data['positions']:
                    cur.execute("""
                        INSERT INTO portfolio_holdings 
                        (portfolio_id, symbol, company_name, quantity, avg_cost, sector)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        portfolio_id,
                        position['symbol'],
                        position['company_name'],
                        position['quantity'],
                        position['avg_cost'],
                        position.get('sector', 'Other')
                    ))
                
                conn.commit()
                logger.info(f"Portfolio {portfolio_id} saved to database")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save portfolio {portfolio_id}: {e}")
            return False
    
    def create_portfolio(self, portfolio_id: str, name: str, description: str = "") -> bool:
        """Create a new empty portfolio"""
        portfolio_data = {
            'name': name,
            'description': description,
            'positions': []
        }
        return self.save_portfolio(portfolio_id, portfolio_data)
    
    def copy_portfolio(self, source_portfolio_id: str, target_portfolio_id: str, 
                      target_name: str, target_description: str = "") -> bool:
        """Copy a portfolio with proper deep copy isolation"""
        try:
            # Get source portfolio
            all_portfolios = self.get_all_portfolios()
            if source_portfolio_id not in all_portfolios:
                available_portfolios = list(all_portfolios.keys())
                logger.error(f"Source portfolio '{source_portfolio_id}' not found. Available portfolios: {available_portfolios}")
                return False
            
            # Check if target already exists
            if target_portfolio_id in all_portfolios:
                logger.error(f"Target portfolio '{target_portfolio_id}' already exists")
                return False
            
            # Deep copy the source portfolio data
            source_data = all_portfolios[source_portfolio_id]
            target_data = {
                'name': target_name,
                'description': target_description,
                'positions': copy.deepcopy(source_data['positions'])  # Deep copy ensures isolation
            }
            
            # Save the copied portfolio
            return self.save_portfolio(target_portfolio_id, target_data)
            
        except Exception as e:
            logger.error(f"Failed to copy portfolio from {source_portfolio_id} to {target_portfolio_id}: {e}")
            return False
    
    def delete_portfolio(self, portfolio_id: str) -> bool:
        """Delete a portfolio from database"""
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                # Delete portfolio (cascade will handle positions)
                cur.execute("DELETE FROM portfolios WHERE portfolio_id = %s", (portfolio_id,))
                conn.commit()
                logger.info(f"Portfolio {portfolio_id} deleted from database")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete portfolio {portfolio_id}: {e}")
            return False
    
    def update_position(self, portfolio_id: str, position_data: Dict[str, Any]) -> bool:
        """Update a single position in a portfolio"""
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO portfolio_holdings 
                    (portfolio_id, symbol, company_name, quantity, avg_cost, sector, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (portfolio_id, symbol)
                    DO UPDATE SET 
                        company_name = EXCLUDED.company_name,
                        quantity = EXCLUDED.quantity,
                        avg_cost = EXCLUDED.avg_cost,
                        sector = EXCLUDED.sector,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    portfolio_id,
                    position_data['symbol'],
                    position_data['company_name'],
                    position_data['quantity'],
                    position_data['avg_cost'],
                    position_data.get('sector', 'Other')
                ))
                
                conn.commit()
                logger.info(f"Position {position_data['symbol']} updated in portfolio {portfolio_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update position in portfolio {portfolio_id}: {e}")
            return False
    
    def remove_position(self, portfolio_id: str, symbol: str) -> bool:
        """Remove a position from a portfolio"""
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM portfolio_holdings 
                    WHERE portfolio_id = %s AND symbol = %s
                """, (portfolio_id, symbol))
                
                conn.commit()
                logger.info(f"Position {symbol} removed from portfolio {portfolio_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to remove position {symbol} from portfolio {portfolio_id}: {e}")
            return False

# Global instance
_portfolio_manager = None

def get_portfolio_manager() -> PortfolioManager:
    """Get global portfolio manager instance"""
    global _portfolio_manager
    if _portfolio_manager is None:
        _portfolio_manager = PortfolioManager()
    return _portfolio_manager