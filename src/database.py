import os
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
import pandas as pd
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL', 'postgresql://trader:YOUR_PASSWORD@localhost:5432/hk_strategy')
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        
    def get_connection(self):
        try:
            conn = psycopg2.connect(self.db_url)
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def get_portfolio_positions(self) -> pd.DataFrame:
        try:
            with self.get_connection() as conn:
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

    def get_trading_signals(self, limit: int = 50) -> pd.DataFrame:
        try:
            with self.get_connection() as conn:
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
                            price: float, **kwargs) -> bool:
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
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