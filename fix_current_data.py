
#!/usr/bin/env python3
"""
Emergency fix for critical data accuracy issues
Refreshes current data for all symbols with Yahoo Finance validation
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

class CurrentDataFixer:
    """Fixes current data accuracy issues with Yahoo Finance validation"""
    
    def __init__(self):
        """Initialize with database connection"""
        load_dotenv()
        self.db = DatabaseManager()
    
    def get_current_yahoo_data(self, symbol: str) -> Dict:
        """Get comprehensive current data from Yahoo Finance"""
        try:
            logger.info(f"Fetching current Yahoo Finance data for {symbol}")
            
            ticker = yf.Ticker(symbol)
            
            # Get current info
            info = ticker.info
            
            # Get recent history for technical analysis
            hist = ticker.history(period='200d')  # Need 200 days for SMA200
            
            if hist.empty:
                logger.error(f"No historical data available for {symbol}")
                return None
            
            # Calculate technical indicators
            hist = self._calculate_technical_indicators(hist)
            
            # Get latest values
            latest = hist.iloc[-1]
            
            # Compile comprehensive data
            current_data = {
                # Basic price data
                'symbol': symbol,
                'trade_date': latest.name.date(),
                'open_price': float(latest['Open']),
                'close_price': float(latest['Close']),
                'high_price': float(latest['High']),
                'low_price': float(latest['Low']),
                'volume': int(latest['Volume']),
                
                # Day extremes
                'day_high': float(latest['High']),
                'day_low': float(latest['Low']),
                
                # 52-week extremes
                'week_52_high': float(hist['High'].rolling(window=252, min_periods=1).max().iloc[-1]),
                'week_52_low': float(hist['Low'].rolling(window=252, min_periods=1).min().iloc[-1]),
                
                # Technical indicators
                'rsi_14': float(latest['RSI_14']) if pd.notna(latest['RSI_14']) else None,
                'rsi_9': float(latest['RSI_9']) if pd.notna(latest['RSI_9']) else None,
                'ema_12': float(latest['EMA_12']) if pd.notna(latest['EMA_12']) else None,
                'ema_26': float(latest['EMA_26']) if pd.notna(latest['EMA_26']) else None,
                'ema_50': float(latest['EMA_50']) if pd.notna(latest['EMA_50']) else None,
                'sma_20': float(latest['SMA_20']) if pd.notna(latest['SMA_20']) else None,
                'sma_50': float(latest['SMA_50']) if pd.notna(latest['SMA_50']) else None,
                'sma_200': float(latest['SMA_200']) if pd.notna(latest['SMA_200']) else None,
                
                # Bollinger Bands
                'bollinger_upper': float(latest['BB_Upper']) if pd.notna(latest['BB_Upper']) else None,
                'bollinger_middle': float(latest['BB_Middle']) if pd.notna(latest['BB_Middle']) else None,
                'bollinger_lower': float(latest['BB_Lower']) if pd.notna(latest['BB_Lower']) else None,
                
                # MACD
                'macd': float(latest['MACD']) if pd.notna(latest['MACD']) else None,
                'macd_signal': float(latest['MACD_Signal']) if pd.notna(latest['MACD_Signal']) else None,
                'macd_histogram': float(latest['MACD_Histogram']) if pd.notna(latest['MACD_Histogram']) else None,
                
                # ATR
                'atr_14': float(latest['ATR_14']) if pd.notna(latest['ATR_14']) else None,
                
                # Volume indicators
                'volume_sma_20': int(latest['Volume_SMA_20']) if pd.notna(latest['Volume_SMA_20']) else None,
                'volume_ratio': float(latest['Volume_Ratio']) if pd.notna(latest['Volume_Ratio']) else None,
                
                # Price position indicators
                'price_vs_52w_high': float(latest['Price_vs_52W_High']) if pd.notna(latest['Price_vs_52W_High']) else None,
                'price_vs_52w_low': float(latest['Price_vs_52W_Low']) if pd.notna(latest['Price_vs_52W_Low']) else None,
                
                # Rate of change
                'roc_1d': float(latest['ROC_1d']) if pd.notna(latest['ROC_1d']) else None,
                'roc_5d': float(latest['ROC_5d']) if pd.notna(latest['ROC_5d']) else None,
                'roc_20d': float(latest['ROC_20d']) if pd.notna(latest['ROC_20d']) else None,
                
                # Support/Resistance
                'support_level': float(latest['Support']) if pd.notna(latest['Support']) else None,
                'resistance_level': float(latest['Resistance']) if pd.notna(latest['Resistance']) else None,
                
                # Financial ratios from info
                'pe_ratio': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                'pb_ratio': info.get('priceToBook'),
                'current_ratio': info.get('currentRatio'),
                'quick_ratio': info.get('quickRatio'),
                'debt_to_equity': info.get('debtToEquity'),
                'profit_margin': info.get('profitMargins'),
                'operating_margin': info.get('operatingMargins'),
                'gross_margin': info.get('grossMargins'),
                'market_cap': info.get('marketCap'),
                'enterprise_value': info.get('enterpriseValue')
            }
            
            logger.info(f"Successfully fetched current data for {symbol}: Close=${current_data['close_price']:.2f}")
            return current_data
            
        except Exception as e:
            logger.error(f"Error fetching Yahoo Finance data for {symbol}: {e}")
            return None
    
    def _calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate comprehensive technical indicators"""
        try:
            # RSI calculation
            def calc_rsi(prices, period=14):
                delta = prices.diff()
                gain = delta.where(delta > 0, 0)
                loss = -delta.where(delta < 0, 0)
                avg_gain = gain.rolling(window=period).mean()
                avg_loss = loss.rolling(window=period).mean()
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                return rsi
            
            # Calculate RSI
            df['RSI_14'] = calc_rsi(df['Close'], 14)
            df['RSI_9'] = calc_rsi(df['Close'], 9)
            
            # Moving averages
            df['EMA_12'] = df['Close'].ewm(span=12).mean()
            df['EMA_26'] = df['Close'].ewm(span=26).mean()
            df['EMA_50'] = df['Close'].ewm(span=50).mean()
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            
            # Bollinger Bands
            df['BB_Middle'] = df['SMA_20']  # 20-day SMA
            bb_std = df['Close'].rolling(window=20).std()
            df['BB_Upper'] = df['BB_Middle'] + (2 * bb_std)
            df['BB_Lower'] = df['BB_Middle'] - (2 * bb_std)
            
            # MACD
            df['MACD'] = df['EMA_12'] - df['EMA_26']
            df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
            df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
            
            # ATR (Average True Range)
            high_low = df['High'] - df['Low']
            high_close = np.abs(df['High'] - df['Close'].shift())
            low_close = np.abs(df['Low'] - df['Close'].shift())
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            df['ATR_14'] = true_range.rolling(window=14).mean()
            
            # Volume indicators
            df['Volume_SMA_20'] = df['Volume'].rolling(window=20).mean()
            df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA_20']
            
            # Price position indicators (using 252 days = 1 trading year)
            rolling_high = df['High'].rolling(window=252, min_periods=1).max()
            rolling_low = df['Low'].rolling(window=252, min_periods=1).min()
            df['Price_vs_52W_High'] = (rolling_high - df['Close']) / rolling_high
            df['Price_vs_52W_Low'] = (df['Close'] - rolling_low) / (rolling_high - rolling_low)
            
            # Rate of change
            df['ROC_1d'] = df['Close'].pct_change(periods=1) * 100
            df['ROC_5d'] = df['Close'].pct_change(periods=5) * 100
            df['ROC_20d'] = df['Close'].pct_change(periods=20) * 100
            
            # Support/Resistance (simple calculation using recent lows/highs)
            df['Support'] = df['Low'].rolling(window=20, min_periods=1).min()
            df['Resistance'] = df['High'].rolling(window=20, min_periods=1).max()
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return df
    
    def update_symbol_data(self, symbol: str) -> bool:
        """Update a single symbol's data"""
        try:
            logger.info(f"Updating data for {symbol}")
            
            # Get current data from Yahoo Finance
            current_data = self.get_current_yahoo_data(symbol)
            if not current_data:
                logger.error(f"Failed to get current data for {symbol}")
                return False
            
            # Update database
            conn = self.db.get_connection()
            cur = conn.cursor()
            
            # First, check what we currently have
            cur.execute("""
                SELECT close_price, trade_date 
                FROM daily_equity_technicals 
                WHERE symbol = %s 
                ORDER BY trade_date DESC 
                LIMIT 1
            """, (symbol,))
            
            existing = cur.fetchone()
            if existing:
                old_price, old_date = existing
                logger.info(f"Current database: {symbol} = ${float(old_price):.2f} ({old_date})")
                logger.info(f"Yahoo Finance: {symbol} = ${current_data['close_price']:.2f} ({current_data['trade_date']})")
                
                price_diff = abs(float(old_price) - current_data['close_price'])
                price_diff_pct = (price_diff / float(old_price)) * 100 if old_price else 0
                
                if price_diff_pct > 5:  # More than 5% difference
                    logger.warning(f"🚨 MAJOR PRICE DISCREPANCY: {price_diff_pct:.1f}% difference!")
                else:
                    logger.info(f"Price difference: {price_diff_pct:.1f}%")
            
            # Insert/Update with current data
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
            """, current_data)
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Successfully updated {symbol} with current Yahoo Finance data")
            return True
            
        except Exception as e:
            logger.error(f"Error updating {symbol}: {e}")
            return False
    
    def validate_all_symbols(self) -> Dict[str, Dict]:
        """Validate all symbols in the database"""
        try:
            # Get all symbols from portfolio analyses
            conn = self.db.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT DISTINCT symbol 
                FROM portfolio_analysis_state_changes 
                WHERE symbol IS NOT NULL 
                ORDER BY symbol
            """)
            
            symbols = [row[0] for row in cur.fetchall()]
            conn.close()
            
            logger.info(f"Validating {len(symbols)} symbols...")
            
            validation_results = {}
            
            for symbol in symbols:
                logger.info(f"Validating {symbol}...")
                
                # Get current database data
                conn = self.db.get_connection()
                cur = conn.cursor()
                
                cur.execute("""
                    SELECT close_price, trade_date, rsi_14, ema_12, sma_20
                    FROM daily_equity_technicals 
                    WHERE symbol = %s 
                    ORDER BY trade_date DESC 
                    LIMIT 1
                """, (symbol,))
                
                db_data = cur.fetchone()
                conn.close()
                
                if not db_data:
                    validation_results[symbol] = {
                        'status': 'MISSING',
                        'message': 'No data in database'
                    }
                    continue
                
                db_price, db_date, db_rsi, db_ema12, db_sma20 = db_data
                
                # Get Yahoo Finance data
                yahoo_data = self.get_current_yahoo_data(symbol)
                
                if not yahoo_data:
                    validation_results[symbol] = {
                        'status': 'ERROR',
                        'message': 'Failed to fetch Yahoo Finance data'
                    }
                    continue
                
                # Compare prices
                price_diff_pct = abs(float(db_price) - yahoo_data['close_price']) / float(db_price) * 100
                
                validation_results[symbol] = {
                    'status': 'MAJOR_DISCREPANCY' if price_diff_pct > 10 else 'MINOR_DISCREPANCY' if price_diff_pct > 2 else 'OK',
                    'db_price': float(db_price),
                    'yahoo_price': yahoo_data['close_price'],
                    'price_diff_pct': price_diff_pct,
                    'db_date': db_date,
                    'yahoo_date': yahoo_data['trade_date'],
                    'needs_update': price_diff_pct > 2
                }
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating symbols: {e}")
            return {}

def main():
    """Main execution"""
    print("🔧 EMERGENCY DATA ACCURACY FIX")
    print("="*50)
    
    fixer = CurrentDataFixer()
    
    # First, validate all symbols to see the scope of the issue
    print("📊 VALIDATING ALL SYMBOLS...")
    validation_results = fixer.validate_all_symbols()
    
    print("\n📋 VALIDATION RESULTS:")
    print("="*60)
    
    major_issues = []
    minor_issues = []
    ok_symbols = []
    
    for symbol, result in validation_results.items():
        status = result['status']
        if status == 'MAJOR_DISCREPANCY':
            major_issues.append(symbol)
            print(f"🚨 {symbol}: MAJOR ISSUE - {result['price_diff_pct']:.1f}% difference (DB: ${result['db_price']:.2f}, Yahoo: ${result['yahoo_price']:.2f})")
        elif status == 'MINOR_DISCREPANCY':
            minor_issues.append(symbol)
            print(f"⚠️  {symbol}: Minor difference - {result['price_diff_pct']:.1f}% (DB: ${result['db_price']:.2f}, Yahoo: ${result['yahoo_price']:.2f})")
        elif status == 'OK':
            ok_symbols.append(symbol)
            print(f"✅ {symbol}: OK - {result['price_diff_pct']:.1f}% difference")
        else:
            print(f"❌ {symbol}: {result['message']}")
    
    print(f"\n📊 SUMMARY:")
    print(f"🚨 Major Issues: {len(major_issues)} symbols")
    print(f"⚠️  Minor Issues: {len(minor_issues)} symbols") 
    print(f"✅ OK: {len(ok_symbols)} symbols")
    
    # Fix major issues first
    if major_issues:
        print(f"\n🔧 FIXING MAJOR ISSUES...")
        for symbol in major_issues:
            print(f"Fixing {symbol}...")
            success = fixer.update_symbol_data(symbol)
            if success:
                print(f"✅ {symbol} fixed successfully")
            else:
                print(f"❌ Failed to fix {symbol}")
    
    # Fix minor issues
    if minor_issues:
        print(f"\n🔧 FIXING MINOR ISSUES...")
        for symbol in minor_issues:
            print(f"Fixing {symbol}...")
            success = fixer.update_symbol_data(symbol)
            if success:
                print(f"✅ {symbol} updated successfully")
            else:
                print(f"❌ Failed to update {symbol}")
    
    print(f"\n🎉 DATA FIX COMPLETED!")

if __name__ == "__main__":
    main()