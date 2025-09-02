"""
Strategic Database Manager - Extension for Strategic Signal System
Extends existing DatabaseManager with strategic signal capabilities
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor, Json
import pandas as pd
from typing import List, Dict, Optional, Tuple, Any
from datetime import date, datetime
import json
import logging
import uuid
import hashlib

from src.strategic_signal_engine import StrategicSignal, IndicatorSnapshot
from src.database import DatabaseManager  # Import existing DatabaseManager

logger = logging.getLogger(__name__)

class StrategicDatabaseManager(DatabaseManager):
    """Extended DatabaseManager with Strategic Signal capabilities"""
    
    def __init__(self):
        super().__init__()
        self.schema_version = "strategic_v1.0"
    
    # ==============================================
    # Parameter Set Management
    # ==============================================
    
    def create_parameter_set(self, name: str, params: Dict, 
                           owner_user_id: Optional[str] = None,
                           engine_version: str = "1.0.0") -> str:
        """Create a new parameter set and return its ID"""
        try:
            params_json = json.dumps(params, sort_keys=True)  # Canonicalized
            params_hash = hashlib.md5(params_json.encode()).hexdigest()
            param_set_id = str(uuid.uuid4())
            
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    query = """
                    INSERT INTO parameter_set 
                    (param_set_id, name, owner_user_id, params_json, params_hash, engine_version)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (params_hash, engine_version) DO UPDATE 
                    SET name = EXCLUDED.name
                    RETURNING param_set_id
                    """
                    cur.execute(query, (
                        param_set_id, name, owner_user_id, 
                        params_json, params_hash, engine_version
                    ))
                    
                    result = cur.fetchone()
                    actual_id = result[0] if result else param_set_id
                    conn.commit()
                    
                    logger.info(f"Created/updated parameter set: {name} ({actual_id})")
                    return actual_id
                    
        except Exception as e:
            logger.error(f"Error creating parameter set: {e}")
            raise
    
    def get_parameter_set(self, param_set_id: str) -> Optional[Dict]:
        """Get parameter set by ID"""
        try:
            with self.get_connection() as conn:
                query = """
                SELECT param_set_id, name, owner_user_id, params_json, 
                       params_hash, engine_version, created_at
                FROM parameter_set 
                WHERE param_set_id = %s
                """
                result = pd.read_sql(query, conn, params=[param_set_id])
                
                if not result.empty:
                    row = result.iloc[0]
                    return {
                        'param_set_id': row['param_set_id'],
                        'name': row['name'],
                        'owner_user_id': row['owner_user_id'],
                        'parameters': json.loads(row['params_json']),
                        'params_hash': row['params_hash'],
                        'engine_version': row['engine_version'],
                        'created_at': row['created_at']
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error fetching parameter set {param_set_id}: {e}")
            return None
    
    def list_parameter_sets(self, owner_user_id: Optional[str] = None) -> pd.DataFrame:
        """List parameter sets, optionally filtered by owner"""
        try:
            with self.get_connection() as conn:
                query = """
                SELECT param_set_id, name, owner_user_id, engine_version, created_at,
                       LENGTH(params_json) as params_size
                FROM parameter_set
                """
                params = []
                
                if owner_user_id:
                    query += " WHERE owner_user_id = %s OR owner_user_id IS NULL"
                    params.append(owner_user_id)
                
                query += " ORDER BY created_at DESC"
                
                return pd.read_sql(query, conn, params=params if params else None)
                
        except Exception as e:
            logger.error(f"Error listing parameter sets: {e}")
            return pd.DataFrame()
    
    # ==============================================
    # Signal Run Management  
    # ==============================================
    
    def create_signal_run(self, param_set_id: str, universe_name: str,
                         start_date: date, end_date: date,
                         notes: Optional[str] = None) -> str:
        """Create a new signal run and return its ID"""
        try:
            run_id = str(uuid.uuid4())
            
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    query = """
                    INSERT INTO signal_run 
                    (run_id, param_set_id, universe_name, start_date, end_date, notes)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING run_id
                    """
                    cur.execute(query, (
                        run_id, param_set_id, universe_name, 
                        start_date, end_date, notes
                    ))
                    
                    actual_run_id = cur.fetchone()[0]
                    conn.commit()
                    
                    logger.info(f"Created signal run: {universe_name} ({actual_run_id})")
                    return actual_run_id
                    
        except Exception as e:
            logger.error(f"Error creating signal run: {e}")
            raise
    
    def complete_signal_run(self, run_id: str) -> bool:
        """Mark a signal run as completed"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    query = """
                    UPDATE signal_run 
                    SET completed_at = CURRENT_TIMESTAMP
                    WHERE run_id = %s
                    """
                    cur.execute(query, (run_id,))
                    conn.commit()
                    
                    return cur.rowcount > 0
                    
        except Exception as e:
            logger.error(f"Error completing signal run {run_id}: {e}")
            return False
    
    def get_signal_run(self, run_id: str) -> Optional[Dict]:
        """Get signal run details"""
        try:
            with self.get_connection() as conn:
                query = """
                SELECT sr.*, ps.name as parameter_set_name
                FROM signal_run sr
                JOIN parameter_set ps ON sr.param_set_id = ps.param_set_id
                WHERE sr.run_id = %s
                """
                result = pd.read_sql(query, conn, params=[run_id])
                
                if not result.empty:
                    return result.iloc[0].to_dict()
                return None
                
        except Exception as e:
            logger.error(f"Error fetching signal run {run_id}: {e}")
            return None
    
    # ==============================================
    # Indicator Snapshot Management
    # ==============================================
    
    def save_indicator_snapshot(self, snapshot: IndicatorSnapshot) -> bool:
        """Save indicator snapshot to database"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    query = """
                    INSERT INTO indicator_snapshot (
                        symbol, bar_date, open_price, high_price, low_price, close_price, volume,
                        rsi6, rsi12, rsi14, rsi24,
                        macd, macd_sig, macd_hist, ppo, ppo_sig, ppo_hist,
                        ema5, ema10, ema20, ema50, sma20, sma50,
                        bb_upper, bb_middle, bb_lower, atr14,
                        vr24, mfi14, ad_line,
                        stoch_k, stoch_d, williams_r, adx14, parabolic_sar
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, 
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (symbol, bar_date) DO UPDATE SET
                        open_price = EXCLUDED.open_price,
                        high_price = EXCLUDED.high_price,
                        low_price = EXCLUDED.low_price,
                        close_price = EXCLUDED.close_price,
                        volume = EXCLUDED.volume,
                        rsi6 = EXCLUDED.rsi6, rsi12 = EXCLUDED.rsi12, 
                        rsi14 = EXCLUDED.rsi14, rsi24 = EXCLUDED.rsi24,
                        macd = EXCLUDED.macd, macd_sig = EXCLUDED.macd_sig, macd_hist = EXCLUDED.macd_hist,
                        ppo = EXCLUDED.ppo, ppo_sig = EXCLUDED.ppo_sig, ppo_hist = EXCLUDED.ppo_hist,
                        ema5 = EXCLUDED.ema5, ema10 = EXCLUDED.ema10, ema20 = EXCLUDED.ema20, 
                        ema50 = EXCLUDED.ema50, sma20 = EXCLUDED.sma20, sma50 = EXCLUDED.sma50,
                        bb_upper = EXCLUDED.bb_upper, bb_middle = EXCLUDED.bb_middle, bb_lower = EXCLUDED.bb_lower,
                        atr14 = EXCLUDED.atr14, vr24 = EXCLUDED.vr24, mfi14 = EXCLUDED.mfi14, ad_line = EXCLUDED.ad_line,
                        stoch_k = EXCLUDED.stoch_k, stoch_d = EXCLUDED.stoch_d, williams_r = EXCLUDED.williams_r,
                        adx14 = EXCLUDED.adx14, parabolic_sar = EXCLUDED.parabolic_sar
                    """
                    
                    cur.execute(query, (
                        snapshot.symbol, snapshot.bar_date,
                        snapshot.open_price, snapshot.high_price, snapshot.low_price, 
                        snapshot.close_price, snapshot.volume,
                        snapshot.rsi6, snapshot.rsi12, snapshot.rsi14, snapshot.rsi24,
                        snapshot.macd, snapshot.macd_sig, snapshot.macd_hist,
                        snapshot.ppo, snapshot.ppo_sig, snapshot.ppo_hist,
                        snapshot.ema5, snapshot.ema10, snapshot.ema20, snapshot.ema50,
                        snapshot.sma20, snapshot.sma50,
                        snapshot.bb_upper, snapshot.bb_middle, snapshot.bb_lower, snapshot.atr14,
                        snapshot.vr24, snapshot.mfi14, snapshot.ad_line,
                        snapshot.stoch_k, snapshot.stoch_d, snapshot.williams_r,
                        snapshot.adx14, snapshot.parabolic_sar
                    ))
                    
                    conn.commit()
                    return True
                    
        except Exception as e:
            logger.error(f"Error saving indicator snapshot for {snapshot.symbol}: {e}")
            return False
    
    def get_indicator_snapshot(self, symbol: str, bar_date: date) -> Optional[IndicatorSnapshot]:
        """Get indicator snapshot for specific symbol and date"""
        try:
            with self.get_connection() as conn:
                query = """
                SELECT * FROM indicator_snapshot 
                WHERE symbol = %s AND bar_date = %s
                """
                result = pd.read_sql(query, conn, params=[symbol, bar_date])
                
                if not result.empty:
                    row = result.iloc[0]
                    return IndicatorSnapshot(
                        symbol=row['symbol'],
                        bar_date=row['bar_date'],
                        open_price=row['open_price'],
                        high_price=row['high_price'],
                        low_price=row['low_price'],
                        close_price=row['close_price'],
                        volume=row['volume'],
                        rsi6=row['rsi6'], rsi12=row['rsi12'], rsi14=row['rsi14'], rsi24=row['rsi24'],
                        macd=row['macd'], macd_sig=row['macd_sig'], macd_hist=row['macd_hist'],
                        ppo=row['ppo'], ppo_sig=row['ppo_sig'], ppo_hist=row['ppo_hist'],
                        ema5=row['ema5'], ema10=row['ema10'], ema20=row['ema20'], ema50=row['ema50'],
                        sma20=row['sma20'], sma50=row['sma50'],
                        bb_upper=row['bb_upper'], bb_middle=row['bb_middle'], bb_lower=row['bb_lower'],
                        atr14=row['atr14'], vr24=row['vr24'], mfi14=row['mfi14'], ad_line=row['ad_line'],
                        stoch_k=row['stoch_k'], stoch_d=row['stoch_d'], williams_r=row['williams_r'],
                        adx14=row['adx14'], parabolic_sar=row['parabolic_sar']
                    )
                return None
                
        except Exception as e:
            logger.error(f"Error fetching indicator snapshot for {symbol} on {bar_date}: {e}")
            return None
    
    def get_latest_indicators(self, symbol: str, limit: int = 1) -> pd.DataFrame:
        """Get latest indicator snapshots for a symbol"""
        try:
            with self.get_connection() as conn:
                query = """
                SELECT * FROM indicator_snapshot 
                WHERE symbol = %s 
                ORDER BY bar_date DESC 
                LIMIT %s
                """
                return pd.read_sql(query, conn, params=[symbol, limit])
                
        except Exception as e:
            logger.error(f"Error fetching latest indicators for {symbol}: {e}")
            return pd.DataFrame()
    
    # ==============================================
    # Strategic Signal Event Management
    # ==============================================
    
    def save_signal_event(self, signal: StrategicSignal, run_id: Optional[str] = None,
                         param_set_id: Optional[str] = None) -> bool:
        """Save a strategic signal event"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    query = """
                    INSERT INTO signal_event (
                        run_id, param_set_id, symbol, bar_date, strategy_key, action, strength,
                        close_at_signal, volume_at_signal, thresholds_json, reasons_json, 
                        score_json, provisional
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (run_id, symbol, bar_date, tf, strategy_key) DO UPDATE SET
                        action = EXCLUDED.action,
                        strength = EXCLUDED.strength,
                        close_at_signal = EXCLUDED.close_at_signal,
                        volume_at_signal = EXCLUDED.volume_at_signal,
                        thresholds_json = EXCLUDED.thresholds_json,
                        reasons_json = EXCLUDED.reasons_json,
                        score_json = EXCLUDED.score_json,
                        provisional = EXCLUDED.provisional
                    """
                    
                    cur.execute(query, (
                        run_id, param_set_id, signal.symbol, signal.bar_date,
                        signal.strategy_key, signal.action, signal.strength,
                        signal.close_at_signal, signal.volume_at_signal,
                        Json(signal.thresholds_json), Json(signal.reasons_json),
                        Json(signal.score_json), signal.provisional
                    ))
                    
                    conn.commit()
                    return True
                    
        except Exception as e:
            logger.error(f"Error saving signal event: {e}")
            return False
    
    def get_signal_events(self, symbol: Optional[str] = None, 
                         strategy_key: Optional[str] = None,
                         date_range: Optional[Tuple[date, date]] = None,
                         min_strength: int = 1,
                         limit: int = 100) -> pd.DataFrame:
        """Get signal events with filtering"""
        try:
            with self.get_connection() as conn:
                query = """
                SELECT se.*, s.name as strategy_name, s.category, s.description
                FROM signal_event se
                LEFT JOIN strategy s ON se.strategy_key = s.strategy_key
                WHERE se.provisional = false AND se.strength >= %s
                """
                params = [min_strength]
                
                if symbol:
                    query += " AND se.symbol = %s"
                    params.append(symbol)
                
                if strategy_key:
                    query += " AND se.strategy_key = %s"
                    params.append(strategy_key)
                
                if date_range:
                    query += " AND se.bar_date BETWEEN %s AND %s"
                    params.extend(date_range)
                
                query += " ORDER BY se.bar_date DESC, se.strength DESC LIMIT %s"
                params.append(limit)
                
                return pd.read_sql(query, conn, params=params)
                
        except Exception as e:
            logger.error(f"Error fetching signal events: {e}")
            return pd.DataFrame()
    
    def get_latest_portfolio_signals(self, portfolio_symbols: List[str], 
                                   days_back: int = 10,
                                   min_strength: int = 5) -> pd.DataFrame:
        """Get latest signals for portfolio symbols"""
        try:
            if not portfolio_symbols:
                return pd.DataFrame()
            
            with self.get_connection() as conn:
                placeholders = ','.join(['%s'] * len(portfolio_symbols))
                query = f"""
                SELECT se.*, s.name as strategy_name, s.category
                FROM signal_event se
                LEFT JOIN strategy s ON se.strategy_key = s.strategy_key
                WHERE se.symbol IN ({placeholders})
                  AND se.provisional = false
                  AND se.strength >= %s
                  AND se.bar_date >= CURRENT_DATE - INTERVAL '{days_back} days'
                ORDER BY se.bar_date DESC, se.strength DESC
                """
                
                params = portfolio_symbols + [min_strength]
                return pd.read_sql(query, conn, params=params)
                
        except Exception as e:
            logger.error(f"Error fetching portfolio signals: {e}")
            return pd.DataFrame()
    
    # ==============================================
    # Chart and UI Data Methods
    # ==============================================
    
    def get_chart_overlay_data(self, symbol: str, indicators: List[str],
                              date_range: Optional[Tuple[date, date]] = None) -> pd.DataFrame:
        """Get indicator data for chart overlays"""
        try:
            if not indicators:
                return pd.DataFrame()
            
            # Validate indicator names
            valid_indicators = [ind for ind in indicators if ind in [
                'ema5', 'ema10', 'ema20', 'ema50', 'sma20', 'sma50',
                'bb_upper', 'bb_middle', 'bb_lower', 'parabolic_sar'
            ]]
            
            if not valid_indicators:
                return pd.DataFrame()
            
            with self.get_connection() as conn:
                columns = ['symbol', 'bar_date', 'close_price'] + valid_indicators
                column_str = ', '.join(columns)
                
                query = f"""
                SELECT {column_str}
                FROM indicator_snapshot 
                WHERE symbol = %s
                """
                params = [symbol]
                
                if date_range:
                    query += " AND bar_date BETWEEN %s AND %s"
                    params.extend(date_range)
                
                query += " ORDER BY bar_date"
                
                return pd.read_sql(query, conn, params=params)
                
        except Exception as e:
            logger.error(f"Error fetching chart overlay data: {e}")
            return pd.DataFrame()
    
    def get_signal_highlights(self, symbol: str, 
                            date_range: Optional[Tuple[date, date]] = None) -> pd.DataFrame:
        """Get signals for chart highlighting"""
        try:
            with self.get_connection() as conn:
                query = """
                SELECT se.bar_date, se.strategy_key, se.action, se.strength,
                       se.close_at_signal, se.reasons_json, s.name, s.category
                FROM signal_event se
                LEFT JOIN strategy s ON se.strategy_key = s.strategy_key
                WHERE se.symbol = %s AND se.provisional = false
                """
                params = [symbol]
                
                if date_range:
                    query += " AND se.bar_date BETWEEN %s AND %s"
                    params.extend(date_range)
                
                query += " ORDER BY se.bar_date"
                
                return pd.read_sql(query, conn, params=params)
                
        except Exception as e:
            logger.error(f"Error fetching signal highlights: {e}")
            return pd.DataFrame()
    
    # ==============================================
    # Migration and Maintenance
    # ==============================================
    
    def migrate_legacy_signals(self, batch_size: int = 1000) -> int:
        """Migrate old A/B/C/D signals to new format"""
        try:
            migrated_count = 0
            
            with self.get_connection() as conn:
                # Get legacy signals
                legacy_query = """
                SELECT * FROM trading_signals 
                WHERE signal_type IN ('A', 'B', 'C', 'D')
                ORDER BY created_at
                LIMIT %s
                """
                
                legacy_signals = pd.read_sql(legacy_query, conn, params=[batch_size])
                
                if legacy_signals.empty:
                    return 0
                
                # Convert to new format
                with conn.cursor() as cur:
                    for _, signal in legacy_signals.iterrows():
                        # Map A/B/C/D to TXYZn format
                        if signal['signal_type'] == 'A':
                            strategy_key = 'BMOM9'
                            action = 'B'
                            strength = 9
                        elif signal['signal_type'] == 'B':
                            strategy_key = 'BMOM7' 
                            action = 'B'
                            strength = 7
                        elif signal['signal_type'] == 'C':
                            strategy_key = 'BMOM5'
                            action = 'B' 
                            strength = 5
                        else:  # D
                            strategy_key = 'SMOM3'
                            action = 'S'
                            strength = 3
                        
                        # Create new signal event
                        insert_query = """
                        INSERT INTO signal_event (
                            symbol, bar_date, strategy_key, action, strength,
                            close_at_signal, volume_at_signal, thresholds_json,
                            reasons_json, score_json, provisional
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                        """
                        
                        cur.execute(insert_query, (
                            signal['symbol'],
                            signal['created_at'].date(),
                            strategy_key,
                            action,
                            strength,
                            signal['price'],
                            signal.get('volume', 0),
                            Json({'migrated_from_legacy': True}),
                            Json([f"Migrated from legacy signal type {signal['signal_type']}"]),
                            Json({'legacy_strength': signal['signal_strength']}),
                            False
                        ))
                        
                        migrated_count += 1
                
                conn.commit()
                logger.info(f"Migrated {migrated_count} legacy signals")
                return migrated_count
                
        except Exception as e:
            logger.error(f"Error migrating legacy signals: {e}")
            return 0
    
    def cleanup_provisional_signals(self, days_old: int = 7) -> int:
        """Clean up old provisional signals"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    query = """
                    DELETE FROM signal_event 
                    WHERE provisional = true 
                      AND created_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
                    """
                    cur.execute(query, (days_old,))
                    deleted_count = cur.rowcount
                    conn.commit()
                    
                    logger.info(f"Cleaned up {deleted_count} old provisional signals")
                    return deleted_count
                    
        except Exception as e:
            logger.error(f"Error cleaning up provisional signals: {e}")
            return 0
    
    # ==============================================
    # Performance and Analytics
    # ==============================================
    
    def get_strategy_performance_summary(self) -> pd.DataFrame:
        """Get performance summary by strategy"""
        try:
            with self.get_connection() as conn:
                query = """
                SELECT 
                    s.base_strategy,
                    s.side,
                    COUNT(*) as total_signals,
                    AVG(se.strength::numeric) as avg_strength,
                    COUNT(*) FILTER (WHERE se.strength >= 7) as strong_signals,
                    COUNT(DISTINCT se.symbol) as unique_symbols,
                    MIN(se.bar_date) as first_signal,
                    MAX(se.bar_date) as latest_signal
                FROM signal_event se
                JOIN strategy s ON se.strategy_key = s.strategy_key
                WHERE se.provisional = false
                GROUP BY s.base_strategy, s.side
                ORDER BY total_signals DESC
                """
                return pd.read_sql(query, conn)
                
        except Exception as e:
            logger.error(f"Error getting strategy performance summary: {e}")
            return pd.DataFrame()

# Example usage and testing
if __name__ == "__main__":
    # Test the extended database manager
    db_manager = StrategicDatabaseManager()
    
    # Test parameter set creation
    test_params = {
        "rsi_overbought": 70,
        "rsi_oversold": 30,
        "volume_threshold": 1.5
    }
    
    param_set_id = db_manager.create_parameter_set("Test Parameters", test_params)
    print(f"Created parameter set: {param_set_id}")
    
    # Test retrieving parameter set
    retrieved_params = db_manager.get_parameter_set(param_set_id)
    print(f"Retrieved parameters: {retrieved_params}")