# Local database implementation without PostgreSQL/Redis for development
import sqlite3
import pandas as pd
import json
import os
from typing import Dict, Optional, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.db_path = "hk_strategy.db"
        self.cache = {}  # Simple in-memory cache instead of Redis
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create portfolio_positions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL UNIQUE,
                company_name TEXT,
                quantity INTEGER NOT NULL DEFAULT 0,
                avg_cost REAL NOT NULL DEFAULT 0,
                current_price REAL DEFAULT 0,
                market_value REAL GENERATED ALWAYS AS (quantity * current_price) STORED,
                unrealized_pnl REAL GENERATED ALWAYS AS ((current_price - avg_cost) * quantity) STORED,
                sector TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create trading_signals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trading_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                signal_type TEXT NOT NULL CHECK (signal_type IN ('A', 'B', 'C', 'D')),
                signal_strength REAL NOT NULL DEFAULT 0.5,
                price REAL NOT NULL,
                volume INTEGER DEFAULT 0,
                rsi REAL,
                ma_5 REAL,
                ma_20 REAL,
                ma_50 REAL,
                bollinger_upper REAL,
                bollinger_lower REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (symbol) REFERENCES portfolio_positions(symbol) ON DELETE CASCADE
            )
        ''')
        
        # Insert sample HK equities if not exists
        sample_data = [
            ('0005.HK', 'HSBC Holdings plc', 13428, 38.50, 39.75, 'Financials'),
            ('0316.HK', 'Orient Overseas', 100, 95.00, 98.20, 'Other'),
            ('0388.HK', 'Hong Kong Exchanges', 300, 280.00, 285.50, 'Financials'),
            ('0700.HK', 'Tencent Holdings Ltd', 3100, 320.50, 315.20, 'Tech'),
            ('0823.HK', 'Link REIT', 1300, 42.80, 44.15, 'REIT'),
            ('0857.HK', 'PetroChina Company Ltd', 0, 7.50, 7.80, 'Energy'),
            ('0939.HK', 'China Construction Bank', 26700, 5.45, 5.52, 'Financials'),
            ('1810.HK', 'Xiaomi Corporation', 2000, 12.30, 13.45, 'Tech'),
            ('2888.HK', 'Standard Chartered PLC', 348, 145.00, 148.20, 'Financials'),
            ('3690.HK', 'Meituan', 340, 95.00, 98.50, 'Tech'),
            ('9618.HK', 'JD.com', 133, 125.00, 130.10, 'Tech'),
            ('9988.HK', 'Alibaba Group', 2000, 115.00, 118.75, 'Tech')
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO portfolio_positions 
            (symbol, company_name, quantity, avg_cost, current_price, sector) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', sample_data)
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")

    def get_portfolio_positions(self) -> pd.DataFrame:
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
            SELECT symbol, company_name, quantity, avg_cost, current_price,
                   market_value, unrealized_pnl, sector, last_updated
            FROM portfolio_positions
            ORDER BY market_value DESC
            """
            df = pd.read_sql(query, conn)
            conn.close()
            return df
        except Exception as e:
            logger.error(f"Error fetching portfolio positions: {e}")
            return pd.DataFrame()

    def get_trading_signals(self, limit: int = 50) -> pd.DataFrame:
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
            SELECT ts.symbol, ts.signal_type, ts.signal_strength, ts.price,
                   ts.rsi, ts.ma_5, ts.ma_20, ts.ma_50, ts.created_at,
                   pp.company_name
            FROM trading_signals ts
            LEFT JOIN portfolio_positions pp ON ts.symbol = pp.symbol
            ORDER BY ts.created_at DESC
            LIMIT ?
            """
            df = pd.read_sql(query, conn, params=[limit])
            conn.close()
            return df
        except Exception as e:
            logger.error(f"Error fetching trading signals: {e}")
            return pd.DataFrame()

    def insert_trading_signal(self, symbol: str, signal_type: str, signal_strength: float,
                            price: float, **kwargs) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            query = """
            INSERT INTO trading_signals 
            (symbol, signal_type, signal_strength, price, rsi, ma_5, ma_20, ma_50,
             bollinger_upper, bollinger_lower)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (
                symbol, signal_type, signal_strength, price,
                kwargs.get('rsi'), kwargs.get('ma_5'), kwargs.get('ma_20'),
                kwargs.get('ma_50'), kwargs.get('bollinger_upper'),
                kwargs.get('bollinger_lower')
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error inserting trading signal: {e}")
            return False

    def update_position_price(self, symbol: str, new_price: float) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            query = """
            UPDATE portfolio_positions 
            SET current_price = ?, last_updated = CURRENT_TIMESTAMP
            WHERE symbol = ?
            """
            cursor.execute(query, (new_price, symbol))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error updating position price: {e}")
            return False

    # Simple in-memory cache instead of Redis
    def get_cache(self, key: str) -> Optional[str]:
        return self.cache.get(key)

    def set_cache(self, key: str, value: str, expiry: int = 300) -> bool:
        self.cache[key] = value
        return True