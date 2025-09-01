#!/usr/bin/env python3
"""
Yahoo Finance Price Data Populator
Fetches historical price data and technical indicators for Hong Kong stocks
and populates the daily_equity_technicals table.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
import logging
import sys
import os
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database import DatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PriceDataPopulator:
    """Handles fetching and storing price data from Yahoo Finance"""
    
    def __init__(self):
        """Initialize the populator with database connection"""
        load_dotenv()
        self.db = DatabaseManager()
        
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators for price data"""
        try:
            # Ensure we have the required columns
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in required_cols:
                if col not in df.columns:
                    raise ValueError(f"Missing required column: {col}")
            
            # Calculate RSI (14-day and 9-day)
            df['rsi_14'] = self._calculate_rsi(df['Close'], 14)
            df['rsi_9'] = self._calculate_rsi(df['Close'], 9)
            
            # Calculate moving averages
            df['ema_12'] = df['Close'].ewm(span=12).mean()
            df['ema_26'] = df['Close'].ewm(span=26).mean()
            df['ema_50'] = df['Close'].ewm(span=50).mean()
            df['sma_20'] = df['Close'].rolling(window=20).mean()
            df['sma_50'] = df['Close'].rolling(window=50).mean()
            df['sma_200'] = df['Close'].rolling(window=200).mean()
            
            # Calculate Bollinger Bands (20-day, 2 std dev)
            bb_period = 20
            bb_std = 2
            df['bollinger_middle'] = df['Close'].rolling(window=bb_period).mean()
            bb_rolling_std = df['Close'].rolling(window=bb_period).std()
            df['bollinger_upper'] = df['bollinger_middle'] + (bb_rolling_std * bb_std)
            df['bollinger_lower'] = df['bollinger_middle'] - (bb_rolling_std * bb_std)
            
            # Calculate MACD
            df['macd'] = df['ema_12'] - df['ema_26']
            df['macd_signal'] = df['macd'].ewm(span=9).mean()
            df['macd_histogram'] = df['macd'] - df['macd_signal']
            
            # Calculate ATR (14-day Average True Range)
            df['atr_14'] = self._calculate_atr(df, 14)
            
            # Calculate volume indicators
            df['volume_sma_20'] = df['Volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['Volume'] / df['volume_sma_20']
            
            # Calculate 52-week high/low
            df['week_52_high'] = df['High'].rolling(window=252, min_periods=1).max()
            df['week_52_low'] = df['Low'].rolling(window=252, min_periods=1).min()
            
            # Calculate price position indicators
            df['price_vs_52w_high'] = (df['Close'] - df['week_52_low']) / (df['week_52_high'] - df['week_52_low'])
            df['price_vs_52w_low'] = (df['week_52_high'] - df['Close']) / df['week_52_high']
            
            # Calculate rate of change
            df['roc_1d'] = df['Close'].pct_change(periods=1) * 100
            df['roc_5d'] = df['Close'].pct_change(periods=5) * 100
            df['roc_20d'] = df['Close'].pct_change(periods=20) * 100
            
            # Simple support/resistance levels (using recent lows/highs)
            df['support_level'] = df['Low'].rolling(window=20, min_periods=1).min()
            df['resistance_level'] = df['High'].rolling(window=20, min_periods=1).max()
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        try:
            delta = prices.diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
        except:
            return pd.Series([50.0] * len(prices), index=prices.index)
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        try:
            high_low = df['High'] - df['Low']
            high_close = np.abs(df['High'] - df['Close'].shift())
            low_close = np.abs(df['Low'] - df['Close'].shift())
            
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(window=period).mean()
            
            return atr
        except:
            return pd.Series([1.0] * len(df), index=df.index)
    
    def fetch_yahoo_finance_data(self, symbol: str, start_date: date, end_date: date) -> Optional[pd.DataFrame]:
        """Fetch historical data from Yahoo Finance"""
        try:
            logger.info(f"Fetching Yahoo Finance data for {symbol} from {start_date} to {end_date}")
            
            # Create ticker object
            ticker = yf.Ticker(symbol)
            
            # Fetch historical data with buffer for technical indicators
            buffer_start = start_date - timedelta(days=365)  # 1 year buffer for indicators
            hist = ticker.history(start=buffer_start, end=end_date + timedelta(days=1), auto_adjust=True, prepost=True)
            
            if hist.empty:
                logger.warning(f"No data returned for {symbol}")
                return None
                
            # Reset index to make Date a column
            hist = hist.reset_index()
            hist['Date'] = hist['Date'].dt.date
            
            # Filter to actual requested date range after calculating indicators
            hist_with_indicators = self.calculate_technical_indicators(hist)
            filtered_data = hist_with_indicators[hist_with_indicators['Date'] >= start_date]
            
            logger.info(f"Successfully fetched {len(filtered_data)} records for {symbol}")
            return filtered_data
            
        except Exception as e:
            logger.error(f"Error fetching Yahoo Finance data for {symbol}: {e}")
            return None
    
    def store_price_data(self, symbol: str, data: pd.DataFrame) -> int:
        """Store price data in the daily_equity_technicals table"""
        try:
            conn = self.db.get_connection()
            cur = conn.cursor()
            
            records_inserted = 0
            
            for _, row in data.iterrows():
                try:
                    # Prepare the data for insertion
                    record = {
                        'symbol': symbol,
                        'trade_date': row['Date'],
                        'open_price': float(row['Open']) if pd.notna(row['Open']) else None,
                        'close_price': float(row['Close']) if pd.notna(row['Close']) else None,
                        'high_price': float(row['High']) if pd.notna(row['High']) else None,
                        'low_price': float(row['Low']) if pd.notna(row['Low']) else None,
                        'volume': int(row['Volume']) if pd.notna(row['Volume']) else None,
                        'day_high': float(row['High']) if pd.notna(row['High']) else None,
                        'day_low': float(row['Low']) if pd.notna(row['Low']) else None,
                        'week_52_high': float(row['week_52_high']) if pd.notna(row['week_52_high']) else None,
                        'week_52_low': float(row['week_52_low']) if pd.notna(row['week_52_low']) else None,
                        'rsi_14': float(row['rsi_14']) if pd.notna(row['rsi_14']) else None,
                        'rsi_9': float(row['rsi_9']) if pd.notna(row['rsi_9']) else None,
                        'ema_12': float(row['ema_12']) if pd.notna(row['ema_12']) else None,
                        'ema_26': float(row['ema_26']) if pd.notna(row['ema_26']) else None,
                        'ema_50': float(row['ema_50']) if pd.notna(row['ema_50']) else None,
                        'sma_20': float(row['sma_20']) if pd.notna(row['sma_20']) else None,
                        'sma_50': float(row['sma_50']) if pd.notna(row['sma_50']) else None,
                        'sma_200': float(row['sma_200']) if pd.notna(row['sma_200']) else None,
                        'bollinger_upper': float(row['bollinger_upper']) if pd.notna(row['bollinger_upper']) else None,
                        'bollinger_middle': float(row['bollinger_middle']) if pd.notna(row['bollinger_middle']) else None,
                        'bollinger_lower': float(row['bollinger_lower']) if pd.notna(row['bollinger_lower']) else None,
                        'macd': float(row['macd']) if pd.notna(row['macd']) else None,
                        'macd_signal': float(row['macd_signal']) if pd.notna(row['macd_signal']) else None,
                        'macd_histogram': float(row['macd_histogram']) if pd.notna(row['macd_histogram']) else None,
                        'atr_14': float(row['atr_14']) if pd.notna(row['atr_14']) else None,
                        'volume_sma_20': int(row['volume_sma_20']) if pd.notna(row['volume_sma_20']) else None,
                        'volume_ratio': float(row['volume_ratio']) if pd.notna(row['volume_ratio']) else None,
                        'price_vs_52w_high': float(row['price_vs_52w_high']) if pd.notna(row['price_vs_52w_high']) else None,
                        'price_vs_52w_low': float(row['price_vs_52w_low']) if pd.notna(row['price_vs_52w_low']) else None,
                        'roc_1d': float(row['roc_1d']) if pd.notna(row['roc_1d']) else None,
                        'roc_5d': float(row['roc_5d']) if pd.notna(row['roc_5d']) else None,
                        'roc_20d': float(row['roc_20d']) if pd.notna(row['roc_20d']) else None,
                        'support_level': float(row['support_level']) if pd.notna(row['support_level']) else None,
                        'resistance_level': float(row['resistance_level']) if pd.notna(row['resistance_level']) else None,
                    }
                    
                    # Insert using ON CONFLICT to handle duplicates
                    cur.execute("""
                        INSERT INTO daily_equity_technicals (
                            symbol, trade_date, open_price, close_price, high_price, low_price, volume,
                            day_high, day_low, week_52_high, week_52_low, rsi_14, rsi_9,
                            ema_12, ema_26, ema_50, sma_20, sma_50, sma_200,
                            bollinger_upper, bollinger_middle, bollinger_lower,
                            macd, macd_signal, macd_histogram, atr_14,
                            volume_sma_20, volume_ratio, price_vs_52w_high, price_vs_52w_low,
                            roc_1d, roc_5d, roc_20d, support_level, resistance_level
                        ) VALUES (
                            %(symbol)s, %(trade_date)s, %(open_price)s, %(close_price)s, %(high_price)s, %(low_price)s, %(volume)s,
                            %(day_high)s, %(day_low)s, %(week_52_high)s, %(week_52_low)s, %(rsi_14)s, %(rsi_9)s,
                            %(ema_12)s, %(ema_26)s, %(ema_50)s, %(sma_20)s, %(sma_50)s, %(sma_200)s,
                            %(bollinger_upper)s, %(bollinger_middle)s, %(bollinger_lower)s,
                            %(macd)s, %(macd_signal)s, %(macd_histogram)s, %(atr_14)s,
                            %(volume_sma_20)s, %(volume_ratio)s, %(price_vs_52w_high)s, %(price_vs_52w_low)s,
                            %(roc_1d)s, %(roc_5d)s, %(roc_20d)s, %(support_level)s, %(resistance_level)s
                        ) ON CONFLICT (symbol, trade_date) DO UPDATE SET
                            open_price = EXCLUDED.open_price,
                            close_price = EXCLUDED.close_price,
                            high_price = EXCLUDED.high_price,
                            low_price = EXCLUDED.low_price,
                            volume = EXCLUDED.volume,
                            day_high = EXCLUDED.day_high,
                            day_low = EXCLUDED.day_low,
                            week_52_high = EXCLUDED.week_52_high,
                            week_52_low = EXCLUDED.week_52_low,
                            rsi_14 = EXCLUDED.rsi_14,
                            rsi_9 = EXCLUDED.rsi_9,
                            ema_12 = EXCLUDED.ema_12,
                            ema_26 = EXCLUDED.ema_26,
                            ema_50 = EXCLUDED.ema_50,
                            sma_20 = EXCLUDED.sma_20,
                            sma_50 = EXCLUDED.sma_50,
                            sma_200 = EXCLUDED.sma_200,
                            bollinger_upper = EXCLUDED.bollinger_upper,
                            bollinger_middle = EXCLUDED.bollinger_middle,
                            bollinger_lower = EXCLUDED.bollinger_lower,
                            macd = EXCLUDED.macd,
                            macd_signal = EXCLUDED.macd_signal,
                            macd_histogram = EXCLUDED.macd_histogram,
                            atr_14 = EXCLUDED.atr_14,
                            volume_sma_20 = EXCLUDED.volume_sma_20,
                            volume_ratio = EXCLUDED.volume_ratio,
                            price_vs_52w_high = EXCLUDED.price_vs_52w_high,
                            price_vs_52w_low = EXCLUDED.price_vs_52w_low,
                            roc_1d = EXCLUDED.roc_1d,
                            roc_5d = EXCLUDED.roc_5d,
                            roc_20d = EXCLUDED.roc_20d,
                            support_level = EXCLUDED.support_level,
                            resistance_level = EXCLUDED.resistance_level,
                            updated_at = CURRENT_TIMESTAMP
                    """, record)
                    
                    records_inserted += 1
                    
                except Exception as row_error:
                    logger.warning(f"Error inserting record for {symbol} on {row['Date']}: {row_error}")
                    continue
            
            conn.commit()
            conn.close()
            
            logger.info(f"Successfully stored {records_inserted} records for {symbol}")
            return records_inserted
            
        except Exception as e:
            logger.error(f"Error storing price data for {symbol}: {e}")
            return 0
    
    def populate_symbol_data(self, symbol: str, start_date: date, end_date: date) -> bool:
        """Populate data for a single symbol"""
        try:
            logger.info(f"Starting data population for {symbol}")
            
            # Fetch data from Yahoo Finance
            data = self.fetch_yahoo_finance_data(symbol, start_date, end_date)
            
            if data is None or data.empty:
                logger.warning(f"No data available for {symbol}")
                return False
            
            # Store in database
            records_count = self.store_price_data(symbol, data)
            
            if records_count > 0:
                logger.info(f"Successfully populated {records_count} records for {symbol}")
                return True
            else:
                logger.warning(f"No records stored for {symbol}")
                return False
                
        except Exception as e:
            logger.error(f"Error populating data for {symbol}: {e}")
            return False
    
    def populate_multiple_symbols(self, symbols: List[str], start_date: date, end_date: date) -> Dict[str, bool]:
        """Populate data for multiple symbols"""
        results = {}
        
        logger.info(f"Starting bulk population for {len(symbols)} symbols")
        
        for symbol in symbols:
            try:
                success = self.populate_symbol_data(symbol, start_date, end_date)
                results[symbol] = success
                
                if success:
                    logger.info(f"✅ {symbol}: Success")
                else:
                    logger.warning(f"❌ {symbol}: Failed")
                    
            except Exception as e:
                logger.error(f"❌ {symbol}: Error - {e}")
                results[symbol] = False
        
        # Summary
        successful = sum(1 for success in results.values() if success)
        total = len(symbols)
        
        logger.info(f"Bulk population completed: {successful}/{total} symbols successful")
        
        return results

def main():
    """Main function for command-line usage"""
    # Get symbols that need data
    load_dotenv()
    db = DatabaseManager()
    conn = db.get_connection()
    cur = conn.cursor()
    
    # Find symbols used in analyses that don't have data
    cur.execute("""
        SELECT DISTINCT pasc.symbol 
        FROM portfolio_analysis_state_changes pasc
        LEFT JOIN daily_equity_technicals det ON pasc.symbol = det.symbol
        WHERE pasc.symbol IS NOT NULL 
        AND det.symbol IS NULL
        ORDER BY pasc.symbol
    """)
    
    missing_symbols = [row[0] for row in cur.fetchall()]
    conn.close()
    
    if not missing_symbols:
        print("✅ All required symbols already have data in the database")
        return
    
    print(f"📊 Found {len(missing_symbols)} symbols needing data: {missing_symbols}")
    
    # Date range for historical data (last 2 years)
    end_date = date.today()
    start_date = end_date - timedelta(days=2*365)  # 2 years
    
    print(f"📅 Fetching data from {start_date} to {end_date}")
    
    # Populate data
    populator = PriceDataPopulator()
    results = populator.populate_multiple_symbols(missing_symbols, start_date, end_date)
    
    # Print final summary
    print("\n" + "="*60)
    print("FINAL RESULTS:")
    print("="*60)
    
    for symbol, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{symbol}: {status}")

if __name__ == "__main__":
    main()