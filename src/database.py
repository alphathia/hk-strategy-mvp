import os
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
import pandas as pd
from typing import List, Dict, Optional
from datetime import date
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        # Load from .env file if present
        from dotenv import load_dotenv
        load_dotenv()
        
        self.db_url = os.getenv('DATABASE_URL', 'postgresql://trader:default_password@localhost:5432/hk_strategy')
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        
    def get_connection(self):
        try:
            conn = psycopg2.connect(self.db_url)
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def get_portfolio_positions(self, portfolio_id: str = None) -> pd.DataFrame:
        try:
            with self.get_connection() as conn:
                # Check if portfolio_id column exists (multi-portfolio schema)
                check_query = """
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'portfolio_positions' AND column_name = 'portfolio_id'
                """
                result = pd.read_sql(check_query, conn)
                has_portfolio_id = not result.empty
                
                if has_portfolio_id:
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
        try:
            with self.get_connection() as conn:
                # Check if portfolio_id column exists (multi-portfolio schema)
                check_query = """
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'trading_signals' AND column_name = 'portfolio_id'
                """
                result = pd.read_sql(check_query, conn)
                has_portfolio_id = not result.empty
                
                if has_portfolio_id:
                    # Multi-portfolio schema
                    query = """
                    SELECT ts.symbol, ts.signal_type, ts.signal_strength, ts.price,
                           ts.rsi, ts.ma_5, ts.ma_20, ts.ma_50, ts.created_at,
                           pp.company_name, ts.portfolio_id
                    FROM trading_signals ts
                    LEFT JOIN portfolio_positions pp ON ts.symbol = pp.symbol AND ts.portfolio_id = pp.portfolio_id
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
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Check if portfolio_id column exists (multi-portfolio schema)
                    check_query = """
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'trading_signals' AND column_name = 'portfolio_id'
                    """
                    result = pd.read_sql(check_query, conn)
                    has_portfolio_id = not result.empty
                    
                    if has_portfolio_id:
                        # Multi-portfolio schema
                        query = """
                        INSERT INTO trading_signals 
                        (portfolio_id, symbol, signal_type, signal_strength, price, rsi, ma_5, ma_20, ma_50,
                         bollinger_upper, bollinger_lower)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        cur.execute(query, (
                            portfolio_id or 'DEFAULT', symbol, signal_type, signal_strength, price,
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

    def update_position_price(self, symbol: str, new_price: float) -> bool:
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    query = """
                    UPDATE portfolio_positions 
                    SET current_price = %s, last_updated = CURRENT_TIMESTAMP
                    WHERE symbol = %s
                    """
                    cur.execute(query, (new_price, symbol))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error updating position price: {e}")
            return False

    def get_cache(self, key: str) -> Optional[str]:
        try:
            return self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    def set_cache(self, key: str, value: str, expiry: int = 300) -> bool:
        try:
            return self.redis_client.setex(key, expiry, value)
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False

    # Portfolio Analysis Methods

    def save_portfolio_analysis(self, name: str, start_date: date, end_date: date, 
                              user_notes: str, start_pv: float, end_pv: float,
                              total_return: float, max_drawdown: float, volatility: float) -> int:
        """Save portfolio analysis metadata and return analysis ID."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    query = """
                    INSERT INTO portfolio_analyses 
                    (name, start_date, end_date, user_notes, start_pv, end_pv, 
                     total_return, max_drawdown, volatility)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """
                    cur.execute(query, (
                        name, start_date, end_date, user_notes, start_pv, end_pv,
                        total_return, max_drawdown, volatility
                    ))
                    analysis_id = cur.fetchone()[0]
                    conn.commit()
                    return analysis_id
        except Exception as e:
            logger.error(f"Error saving portfolio analysis: {e}")
            raise

    def save_portfolio_value_history(self, analysis_id: int, daily_values: List[Dict]) -> bool:
        """Save daily portfolio value history for an analysis."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    query = """
                    INSERT INTO portfolio_value_history 
                    (analysis_id, trade_date, portfolio_value, cash_value, total_value, 
                     daily_change, daily_return, top_contributors)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    values_data = []
                    for daily_value in daily_values:
                        contributors_json = json.dumps(daily_value.get('top_contributors', []))
                        values_data.append((
                            analysis_id,
                            daily_value['trade_date'],
                            daily_value['portfolio_value'],
                            daily_value['cash_value'],
                            daily_value['total_value'],
                            daily_value.get('daily_change'),
                            daily_value.get('daily_return'),
                            contributors_json
                        ))
                    
                    cur.executemany(query, values_data)
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error saving portfolio value history: {e}")
            return False

    def get_portfolio_analyses(self, limit: int = 50) -> pd.DataFrame:
        """Get list of saved portfolio analyses."""
        try:
            with self.get_connection() as conn:
                query = """
                SELECT id, name, start_date, end_date, created_at, 
                       start_pv, end_pv, total_return, max_drawdown, volatility,
                       (SELECT COUNT(*) FROM portfolio_value_history pv 
                        WHERE pv.analysis_id = pa.id) as trading_days
                FROM portfolio_analyses pa
                ORDER BY created_at DESC
                LIMIT %s
                """
                return pd.read_sql(query, conn, params=[limit])
        except Exception as e:
            logger.error(f"Error fetching portfolio analyses: {e}")
            return pd.DataFrame()

    def get_portfolio_analysis(self, analysis_id: int) -> Dict:
        """Get specific portfolio analysis metadata."""
        try:
            with self.get_connection() as conn:
                query = """
                SELECT * FROM portfolio_analyses WHERE id = %s
                """
                result = pd.read_sql(query, conn, params=[analysis_id])
                if not result.empty:
                    return result.iloc[0].to_dict()
                return {}
        except Exception as e:
            logger.error(f"Error fetching portfolio analysis {analysis_id}: {e}")
            return {}

    def get_portfolio_value_history(self, analysis_id: int) -> pd.DataFrame:
        """Get daily portfolio value history for an analysis."""
        try:
            with self.get_connection() as conn:
                query = """
                SELECT trade_date, portfolio_value, cash_value, total_value,
                       daily_change, daily_return, top_contributors
                FROM portfolio_value_history
                WHERE analysis_id = %s
                ORDER BY trade_date
                """
                df = pd.read_sql(query, conn, params=[analysis_id])
                
                # Parse JSON contributors
                if not df.empty:
                    df['top_contributors'] = df['top_contributors'].apply(
                        lambda x: json.loads(x) if x else []
                    )
                
                return df
        except Exception as e:
            logger.error(f"Error fetching portfolio value history for analysis {analysis_id}: {e}")
            return pd.DataFrame()

    def delete_portfolio_analysis(self, analysis_id: int) -> bool:
        """Delete a portfolio analysis and its history."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM portfolio_analyses WHERE id = %s", (analysis_id,))
                    conn.commit()
                    return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting portfolio analysis {analysis_id}: {e}")
            return False

    def get_portfolio_positions_dict(self) -> Dict[str, int]:
        """Get current portfolio positions as symbol->quantity dictionary."""
        try:
            positions_df = self.get_portfolio_positions()
            if positions_df.empty:
                return {}
            return dict(zip(positions_df['symbol'], positions_df['quantity']))
        except Exception as e:
            logger.error(f"Error getting portfolio positions dict: {e}")
            return {}

    # Strategy Management Methods
    
    def get_strategies(self, active_only: bool = True) -> pd.DataFrame:
        """Get list of available strategies."""
        try:
            with self.get_connection() as conn:
                query = """
                SELECT id, strategy_name, description, strategy_type, 
                       parameters, created_at, updated_at, is_active
                FROM strategies
                """
                if active_only:
                    query += " WHERE is_active = TRUE"
                query += " ORDER BY strategy_name"
                return pd.read_sql(query, conn)
        except Exception as e:
            logger.error(f"Error fetching strategies: {e}")
            return pd.DataFrame()

    def create_strategy(self, name: str, description: str, strategy_type: str, 
                       parameters: Dict = None) -> int:
        """Create a new strategy and return its ID."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    query = """
                    INSERT INTO strategies (strategy_name, description, strategy_type, parameters)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """
                    params_json = json.dumps(parameters or {})
                    cur.execute(query, (name, description, strategy_type, params_json))
                    strategy_id = cur.fetchone()[0]
                    conn.commit()
                    return strategy_id
        except Exception as e:
            logger.error(f"Error creating strategy: {e}")
            raise

    # Portfolio Analysis Equity Methods
    
    def save_portfolio_analysis_equities(self, analysis_id: int, equities: List[Dict]) -> bool:
        """Save equities associated with a portfolio analysis."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    query = """
                    INSERT INTO portfolio_analysis_equities 
                    (portfolio_analysis_id, symbol, quantity, avg_cost, analysis_start_price, 
                     analysis_end_price, analysis_notes, weight_in_portfolio)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    equity_data = []
                    for equity in equities:
                        equity_data.append((
                            analysis_id,
                            equity['symbol'],
                            equity['quantity'],
                            equity['avg_cost'],
                            equity.get('analysis_start_price'),
                            equity.get('analysis_end_price'),
                            equity.get('analysis_notes'),
                            equity.get('weight_in_portfolio')
                        ))
                    
                    cur.executemany(query, equity_data)
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error saving portfolio analysis equities: {e}")
            return False

    def get_portfolio_analysis_equities(self, analysis_id: int) -> pd.DataFrame:
        """Get equities for a specific portfolio analysis."""
        try:
            with self.get_connection() as conn:
                query = """
                SELECT pae.*, 
                       COUNT(paes.id) as strategies_applied,
                       AVG(paes.total_return) as avg_strategy_return
                FROM portfolio_analysis_equities pae
                LEFT JOIN portfolio_analysis_equity_strategies paes 
                    ON pae.id = paes.portfolio_analysis_equity_id
                WHERE pae.portfolio_analysis_id = %s
                GROUP BY pae.id
                ORDER BY pae.weight_in_portfolio DESC
                """
                return pd.read_sql(query, conn, params=[analysis_id])
        except Exception as e:
            logger.error(f"Error fetching portfolio analysis equities: {e}")
            return pd.DataFrame()

    # Portfolio Analysis Equity Strategy Methods
    
    def apply_strategy_to_equity(self, portfolio_analysis_equity_id: int, strategy_id: int,
                                parameters_override: Dict = None, performance_metrics: Dict = None) -> int:
        """Apply a strategy to a specific equity in a portfolio analysis."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    query = """
                    INSERT INTO portfolio_analysis_equity_strategies 
                    (portfolio_analysis_equity_id, strategy_id, parameters_override, performance_metrics,
                     total_return, max_drawdown, sharpe_ratio, win_rate, total_trades)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """
                    params_json = json.dumps(parameters_override or {})
                    metrics_json = json.dumps(performance_metrics or {})
                    metrics = performance_metrics or {}
                    
                    cur.execute(query, (
                        portfolio_analysis_equity_id, strategy_id, params_json, metrics_json,
                        metrics.get('total_return'), metrics.get('max_drawdown'),
                        metrics.get('sharpe_ratio'), metrics.get('win_rate'),
                        metrics.get('total_trades', 0)
                    ))
                    strategy_application_id = cur.fetchone()[0]
                    conn.commit()
                    return strategy_application_id
        except Exception as e:
            logger.error(f"Error applying strategy to equity: {e}")
            raise

    def get_equity_strategy_results(self, portfolio_analysis_equity_id: int) -> pd.DataFrame:
        """Get strategy results for a specific equity in a portfolio analysis."""
        try:
            with self.get_connection() as conn:
                query = """
                SELECT paes.*, s.strategy_name, s.strategy_type, s.description
                FROM portfolio_analysis_equity_strategies paes
                JOIN strategies s ON paes.strategy_id = s.id
                WHERE paes.portfolio_analysis_equity_id = %s AND paes.is_active = TRUE
                ORDER BY paes.total_return DESC
                """
                return pd.read_sql(query, conn, params=[portfolio_analysis_equity_id])
        except Exception as e:
            logger.error(f"Error fetching equity strategy results: {e}")
            return pd.DataFrame()

    # Equity Strategy Analysis Methods
    
    def save_equity_strategy_analysis(self, symbol: str, strategy_id: int, analysis_name: str,
                                    start_date: date, end_date: date, performance_data: Dict,
                                    metrics: Dict, user_notes: str = None) -> int:
        """Save a cross-portfolio equity strategy analysis."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    query = """
                    INSERT INTO equity_strategy_analyses 
                    (symbol, strategy_id, analysis_name, start_date, end_date, 
                     initial_price, final_price, performance_data, total_return, 
                     volatility, max_drawdown, sharpe_ratio, sortino_ratio, 
                     win_rate, profit_factor, total_trades, user_notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """
                    performance_json = json.dumps(performance_data)
                    
                    cur.execute(query, (
                        symbol, strategy_id, analysis_name, start_date, end_date,
                        metrics.get('initial_price'), metrics.get('final_price'),
                        performance_json, metrics.get('total_return'),
                        metrics.get('volatility'), metrics.get('max_drawdown'),
                        metrics.get('sharpe_ratio'), metrics.get('sortino_ratio'),
                        metrics.get('win_rate'), metrics.get('profit_factor'),
                        metrics.get('total_trades', 0), user_notes
                    ))
                    analysis_id = cur.fetchone()[0]
                    conn.commit()
                    return analysis_id
        except Exception as e:
            logger.error(f"Error saving equity strategy analysis: {e}")
            raise

    def get_equity_strategy_analyses(self, symbol: str = None, strategy_id: int = None) -> pd.DataFrame:
        """Get equity strategy analyses with optional filters."""
        try:
            with self.get_connection() as conn:
                query = """
                SELECT esa.*, s.strategy_name, s.strategy_type
                FROM equity_strategy_analyses esa
                JOIN strategies s ON esa.strategy_id = s.id
                WHERE 1=1
                """
                params = []
                
                if symbol:
                    query += " AND esa.symbol = %s"
                    params.append(symbol)
                
                if strategy_id:
                    query += " AND esa.strategy_id = %s"
                    params.append(strategy_id)
                
                query += " ORDER BY esa.updated_at DESC"
                
                return pd.read_sql(query, conn, params=params)
        except Exception as e:
            logger.error(f"Error fetching equity strategy analyses: {e}")
            return pd.DataFrame()

    def get_equity_cross_portfolio_performance(self, symbol: str = None) -> pd.DataFrame:
        """Get cross-portfolio performance summary for equities."""
        try:
            with self.get_connection() as conn:
                query = """
                SELECT * FROM equity_cross_portfolio_performance
                """
                params = []
                
                if symbol:
                    query += " WHERE symbol = %s"
                    params.append(symbol)
                
                query += " ORDER BY avg_return_across_strategies DESC"
                
                return pd.read_sql(query, conn, params=params)
        except Exception as e:
            logger.error(f"Error fetching cross-portfolio performance: {e}")
            return pd.DataFrame()

    def get_strategy_performance_summary(self) -> pd.DataFrame:
        """Get performance summary for all strategies."""
        try:
            with self.get_connection() as conn:
                query = """
                SELECT * FROM strategy_performance_summary
                ORDER BY avg_return DESC
                """
                return pd.read_sql(query, conn)
        except Exception as e:
            logger.error(f"Error fetching strategy performance summary: {e}")
            return pd.DataFrame()

    # Strategy Signal Tracking Methods
    
    def save_strategy_signals(self, equity_strategy_analysis_id: int, signals: List[Dict]) -> bool:
        """Save strategy signals for an equity strategy analysis."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    query = """
                    INSERT INTO strategy_signals 
                    (equity_strategy_analysis_id, signal_date, signal_type, price, 
                     quantity, signal_strength, technical_indicators, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    signal_data = []
                    for signal in signals:
                        indicators_json = json.dumps(signal.get('technical_indicators', {}))
                        signal_data.append((
                            equity_strategy_analysis_id,
                            signal['signal_date'],
                            signal['signal_type'],
                            signal['price'],
                            signal.get('quantity', 0),
                            signal.get('signal_strength', 0.5),
                            indicators_json,
                            signal.get('notes')
                        ))
                    
                    cur.executemany(query, signal_data)
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error saving strategy signals: {e}")
            return False

    def get_strategy_signals(self, equity_strategy_analysis_id: int) -> pd.DataFrame:
        """Get strategy signals for a specific analysis."""
        try:
            with self.get_connection() as conn:
                query = """
                SELECT signal_date, signal_type, price, quantity, signal_strength,
                       technical_indicators, notes, created_at
                FROM strategy_signals
                WHERE equity_strategy_analysis_id = %s
                ORDER BY signal_date
                """
                df = pd.read_sql(query, conn, params=[equity_strategy_analysis_id])
                
                # Parse JSON technical indicators
                if not df.empty:
                    df['technical_indicators'] = df['technical_indicators'].apply(
                        lambda x: json.loads(x) if x else {}
                    )
                
                return df
        except Exception as e:
            logger.error(f"Error fetching strategy signals: {e}")
            return pd.DataFrame()