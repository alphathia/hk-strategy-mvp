"""
Enhanced Database Manager with Migration State Awareness
Provides seamless backward compatibility during database migration phases
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
import pandas as pd
from typing import List, Dict, Optional, Tuple
from datetime import date
import json
import logging
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SchemaVersion(Enum):
    """Database schema version enumeration"""
    SINGLE_PORTFOLIO = "1.0"
    MULTI_PORTFOLIO_TRANSITIONAL = "2.0"  # Phase 1: Added portfolio_id columns
    MULTI_PORTFOLIO_COMPLETE = "3.0"      # Phase 2: Full constraints and integrity

class DatabaseManager:
    """
    Enhanced Database Manager with migration state awareness.
    Automatically detects schema version and adapts queries accordingly.
    """
    
    def __init__(self):
        # Load from .env file if present
        from dotenv import load_dotenv
        load_dotenv()
        
        self.db_url = os.getenv('DATABASE_URL', 'postgresql://trader:default_password@localhost:5432/hk_strategy')
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        
        # Initialize Redis with error handling
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            # Test Redis connection
            self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Continuing without caching.")
            self.redis_client = None
        
        # Cache schema version to avoid repeated queries
        self._schema_version = None
        self._schema_capabilities = None
        
    def get_connection(self):
        """Get database connection with enhanced error handling"""
        try:
            conn = psycopg2.connect(self.db_url)
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def detect_schema_version(self, force_refresh: bool = False) -> Tuple[SchemaVersion, Dict]:
        """
        Detect current database schema version and capabilities.
        
        Args:
            force_refresh: Force re-detection of schema version
            
        Returns:
            Tuple of (SchemaVersion, capabilities_dict)
        """
        if self._schema_version is not None and not force_refresh:
            return self._schema_version, self._schema_capabilities
        
        try:
            conn = self.get_connection()
            
            # Check for portfolios table existence
            has_portfolios_table = pd.read_sql("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'portfolios'
                )
            """, conn).iloc[0, 0]
            
            # Check for portfolio_id columns in main tables
            portfolio_id_checks = {}
            for table in ['portfolio_positions', 'trading_signals', 'price_history']:
                portfolio_id_checks[table] = pd.read_sql(f"""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = '{table}' AND column_name = 'portfolio_id'
                    )
                """, conn).iloc[0, 0]
            
            # Check for foreign key constraints (indicates Phase 2 completion)
            has_foreign_keys = pd.read_sql("""
                SELECT COUNT(*) > 0 as has_fks FROM information_schema.table_constraints 
                WHERE constraint_type = 'FOREIGN KEY' 
                  AND table_name IN ('portfolio_positions', 'trading_signals', 'price_history')
                  AND constraint_name LIKE '%portfolio%'
            """, conn).iloc[0, 0]
            
            # Check if portfolio_id columns are NOT NULL (indicates Phase 2)
            not_null_checks = {}
            for table in ['portfolio_positions', 'trading_signals', 'price_history']:
                if portfolio_id_checks[table]:
                    not_null_checks[table] = pd.read_sql(f"""
                        SELECT is_nullable = 'NO' as is_not_null FROM information_schema.columns 
                        WHERE table_name = '{table}' AND column_name = 'portfolio_id'
                    """, conn).iloc[0, 0]
                else:
                    not_null_checks[table] = False
            
            # Determine schema version with more precise logic
            if not has_portfolios_table and not any(portfolio_id_checks.values()):
                # Original single-portfolio schema
                version = SchemaVersion.SINGLE_PORTFOLIO
                capabilities = {
                    'multi_portfolio': False,
                    'portfolio_isolation': False,
                    'backward_compatible': True,
                    'has_constraints': False,
                    'portfolio_id_required': False
                }
                
            elif has_portfolios_table and all(portfolio_id_checks.values()) and not all(not_null_checks.values()):
                # Phase 1: Multi-portfolio with backward compatibility (fully completed)
                version = SchemaVersion.MULTI_PORTFOLIO_TRANSITIONAL
                capabilities = {
                    'multi_portfolio': True,
                    'portfolio_isolation': True,
                    'backward_compatible': True,
                    'has_constraints': False,
                    'portfolio_id_required': False
                }
                
            elif has_portfolios_table and all(portfolio_id_checks.values()) and all(not_null_checks.values()) and has_foreign_keys:
                # Phase 2: Full multi-portfolio with constraints
                version = SchemaVersion.MULTI_PORTFOLIO_COMPLETE
                capabilities = {
                    'multi_portfolio': True,
                    'portfolio_isolation': True,
                    'backward_compatible': False,
                    'has_constraints': True,
                    'portfolio_id_required': True
                }
                
            elif has_portfolios_table and not all(portfolio_id_checks.values()):
                # Partial migration: portfolios table exists but portfolio_id columns missing
                version = SchemaVersion.SINGLE_PORTFOLIO
                capabilities = {
                    'multi_portfolio': False,
                    'portfolio_isolation': False,
                    'backward_compatible': True,
                    'has_constraints': False,
                    'portfolio_id_required': False,
                    'warning': 'Partial migration detected - portfolios table exists but portfolio_id columns missing'
                }
                
            else:
                # Other inconsistent states
                version = SchemaVersion.SINGLE_PORTFOLIO
                capabilities = {
                    'multi_portfolio': False,
                    'portfolio_isolation': False,
                    'backward_compatible': True,
                    'has_constraints': False,
                    'portfolio_id_required': False,
                    'warning': 'Inconsistent schema state detected - defaulting to single-portfolio'
                }
            
            self._schema_version = version
            self._schema_capabilities = capabilities
            
            logger.info(f"Detected schema version: {version.value}")
            if 'warning' in capabilities:
                logger.warning(f"Schema warning: {capabilities['warning']}")
                
            return version, capabilities
            
        except Exception as e:
            logger.error(f"Failed to detect schema version: {e}")
            # Default to single portfolio for safety
            return SchemaVersion.SINGLE_PORTFOLIO, {
                'multi_portfolio': False,
                'portfolio_isolation': False,
                'backward_compatible': True,
                'has_constraints': False,
                'portfolio_id_required': False,
                'error': str(e)
            }
    
    def get_portfolio_positions(self, portfolio_id: str = None) -> pd.DataFrame:
        """
        Get portfolio positions with automatic schema adaptation.
        
        Args:
            portfolio_id: Portfolio identifier (ignored in single-portfolio mode)
            
        Returns:
            DataFrame with position data
        """
        try:
            version, capabilities = self.detect_schema_version()
            
            with self.get_connection() as conn:
                if capabilities['multi_portfolio']:
                    # Multi-portfolio schema
                    query = """
                    SELECT symbol, company_name, quantity, avg_cost, current_price,
                           market_value, unrealized_pnl, sector, last_updated, portfolio_id
                    FROM portfolio_positions
                    """
                    params = []
                    
                    if portfolio_id:
                        query += " WHERE portfolio_id = %s"
                        params.append(portfolio_id)
                    
                    query += " ORDER BY market_value DESC"
                    
                    return pd.read_sql(query, conn, params=params if params else None)
                else:
                    # Single portfolio schema (backward compatibility)
                    query = """
                    SELECT symbol, company_name, quantity, avg_cost, current_price,
                           market_value, unrealized_pnl, sector, last_updated
                    FROM portfolio_positions
                    ORDER BY market_value DESC
                    """
                    return pd.read_sql(query, conn)
                    
        except Exception as e:
            logger.error(f"Error fetching portfolio positions: {e}")
            return pd.DataFrame()
    
    def get_trading_signals(self, limit: int = 50, portfolio_id: str = None) -> pd.DataFrame:
        """
        Get trading signals with automatic schema adaptation.
        
        Args:
            limit: Maximum number of signals to return
            portfolio_id: Portfolio identifier (ignored in single-portfolio mode)
            
        Returns:
            DataFrame with trading signals
        """
        try:
            version, capabilities = self.detect_schema_version()
            
            with self.get_connection() as conn:
                if capabilities['multi_portfolio']:
                    # Multi-portfolio schema
                    query = """
                    SELECT ts.symbol, ts.signal_type, ts.signal_strength, ts.price,
                           ts.rsi, ts.ma_5, ts.ma_20, ts.ma_50, ts.created_at,
                           pp.company_name, ts.portfolio_id
                    FROM trading_signals ts
                    LEFT JOIN portfolio_positions pp ON ts.symbol = pp.symbol 
                          AND ts.portfolio_id = pp.portfolio_id
                    """
                    params = []
                    
                    if portfolio_id:
                        query += " WHERE ts.portfolio_id = %s"
                        params.append(portfolio_id)
                    
                    query += " ORDER BY ts.created_at DESC LIMIT %s"
                    params.append(limit)
                    
                    return pd.read_sql(query, conn, params=params)
                else:
                    # Single portfolio schema (backward compatibility)
                    query = """
                    SELECT ts.symbol, ts.signal_type, ts.signal_strength, ts.price,
                           ts.rsi, ts.ma_5, ts.ma_20, ts.ma_50, ts.created_at,
                           pp.company_name
                    FROM trading_signals ts
                    LEFT JOIN portfolio_positions pp ON ts.symbol = pp.symbol
                    ORDER BY ts.created_at DESC
                    LIMIT %s
                    """
                    return pd.read_sql(query, conn, params=[limit])
                    
        except Exception as e:
            logger.error(f"Error fetching trading signals: {e}")
            return pd.DataFrame()
    
    def insert_trading_signal(self, symbol: str, signal_type: str, signal_strength: float,
                            price: float, portfolio_id: str = None, **kwargs) -> bool:
        """
        Insert trading signal with automatic schema adaptation.
        
        Args:
            symbol: Stock symbol
            signal_type: Signal type (A, B, C, D)
            signal_strength: Signal strength (0.0 to 1.0)
            price: Current price
            portfolio_id: Portfolio identifier (optional, defaults to 'DEFAULT' in multi-portfolio mode)
            **kwargs: Additional signal data (rsi, ma_5, etc.)
            
        Returns:
            Boolean indicating success
        """
        try:
            version, capabilities = self.detect_schema_version()
            
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    if capabilities['multi_portfolio']:
                        # Multi-portfolio schema
                        effective_portfolio_id = portfolio_id or 'DEFAULT'
                        
                        query = """
                        INSERT INTO trading_signals 
                        (portfolio_id, symbol, signal_type, signal_strength, price, rsi, ma_5, ma_20, ma_50,
                         bollinger_upper, bollinger_lower)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        cur.execute(query, (
                            effective_portfolio_id, symbol, signal_type, signal_strength, price,
                            kwargs.get('rsi'), kwargs.get('ma_5'), kwargs.get('ma_20'),
                            kwargs.get('ma_50'), kwargs.get('bollinger_upper'),
                            kwargs.get('bollinger_lower')
                        ))
                    else:
                        # Single portfolio schema (backward compatibility)
                        query = """
                        INSERT INTO trading_signals 
                        (symbol, signal_type, signal_strength, price, rsi, ma_5, ma_20, ma_50,
                         bollinger_upper, bollinger_lower)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        cur.execute(query, (
                            symbol, signal_type, signal_strength, price,
                            kwargs.get('rsi'), kwargs.get('ma_5'), kwargs.get('ma_20'),
                            kwargs.get('ma_50'), kwargs.get('bollinger_upper'),
                            kwargs.get('bollinger_lower')
                        ))
                    
                    conn.commit()
                    return True
                    
        except Exception as e:
            logger.error(f"Error inserting trading signal: {e}")
            return False
    
    def get_portfolios(self) -> pd.DataFrame:
        """
        Get all portfolios (multi-portfolio schema only).
        
        Returns:
            DataFrame with portfolio metadata or empty DataFrame for single-portfolio
        """
        try:
            version, capabilities = self.detect_schema_version()
            
            if not capabilities['multi_portfolio']:
                # Return a simulated single portfolio for backward compatibility
                return pd.DataFrame([{
                    'portfolio_id': 'DEFAULT',
                    'name': 'Legacy Portfolio',
                    'description': 'Single portfolio mode',
                    'created_at': None,
                    'updated_at': None
                }])
            
            with self.get_connection() as conn:
                query = """
                SELECT portfolio_id, name, description, created_at, updated_at
                FROM portfolios
                ORDER BY created_at DESC
                """
                return pd.read_sql(query, conn)
                
        except Exception as e:
            logger.error(f"Error fetching portfolios: {e}")
            return pd.DataFrame()
    
    def create_portfolio(self, portfolio_id: str, name: str, description: str = "") -> bool:
        """
        Create a new portfolio (multi-portfolio schema only).
        
        Args:
            portfolio_id: Unique portfolio identifier
            name: Portfolio display name
            description: Optional description
            
        Returns:
            Boolean indicating success
        """
        try:
            version, capabilities = self.detect_schema_version()
            
            if not capabilities['multi_portfolio']:
                logger.warning("Cannot create portfolio in single-portfolio schema")
                return False
            
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    query = """
                    INSERT INTO portfolios (portfolio_id, name, description)
                    VALUES (%s, %s, %s)
                    """
                    cur.execute(query, (portfolio_id, name, description))
                    conn.commit()
                    return True
                    
        except Exception as e:
            logger.error(f"Error creating portfolio: {e}")
            return False
    
    def get_schema_info(self) -> Dict:
        """
        Get comprehensive schema information for debugging and monitoring.
        
        Returns:
            Dictionary with schema details
        """
        version, capabilities = self.detect_schema_version()
        
        return {
            'version': version.value,
            'capabilities': capabilities,
            'migration_recommendations': self._get_migration_recommendations(version, capabilities)
        }
    
    def _get_migration_recommendations(self, version: SchemaVersion, capabilities: Dict) -> List[str]:
        """Get migration recommendations based on current schema state"""
        recommendations = []
        
        if version == SchemaVersion.SINGLE_PORTFOLIO:
            recommendations.append("Consider running Phase 1 migration (migration_v1_to_v2.sql) to enable multi-portfolio support")
            recommendations.append("Current schema supports only single portfolio operations")
            
        elif version == SchemaVersion.MULTI_PORTFOLIO_TRANSITIONAL:
            if capabilities.get('warning'):
                recommendations.append("Schema state appears inconsistent - verify migration completion")
            recommendations.append("Phase 1 migration completed - multi-portfolio features available")
            recommendations.append("Consider running Phase 2 migration (migration_v2_to_v3.sql) for full data integrity")
            recommendations.append("Current schema maintains backward compatibility")
            
        elif version == SchemaVersion.MULTI_PORTFOLIO_COMPLETE:
            recommendations.append("Schema fully migrated - all multi-portfolio features available")
            recommendations.append("Foreign key constraints ensure data integrity")
            recommendations.append("No further migration needed")
        
        return recommendations

    def test_connection_health(self) -> Dict:
        """
        Comprehensive connection health check.
        
        Returns:
            Dictionary with health status
        """
        health = {
            'database': {'status': 'unknown', 'details': ''},
            'redis': {'status': 'unknown', 'details': ''},
            'schema': {'status': 'unknown', 'details': ''}
        }
        
        # Test database connection
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
            health['database'] = {'status': 'healthy', 'details': f'Connected to {version}'}
        except Exception as e:
            health['database'] = {'status': 'error', 'details': str(e)}
        
        # Test Redis connection
        if self.redis_client:
            try:
                self.redis_client.ping()
                health['redis'] = {'status': 'healthy', 'details': 'Redis responding to ping'}
            except Exception as e:
                health['redis'] = {'status': 'error', 'details': str(e)}
        else:
            health['redis'] = {'status': 'disabled', 'details': 'Redis client not initialized'}
        
        # Test schema state
        try:
            schema_info = self.get_schema_info()
            health['schema'] = {
                'status': 'healthy', 
                'details': f"Schema version {schema_info['version']} detected"
            }
        except Exception as e:
            health['schema'] = {'status': 'error', 'details': str(e)}
        
        return health