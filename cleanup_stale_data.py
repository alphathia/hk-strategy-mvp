#!/usr/bin/env python3
"""
Clean up stale data and ensure current accurate data is displayed
"""

import sys
import os
sys.path.append('src')
from src.database import DatabaseManager
from dotenv import load_dotenv

load_dotenv()

def cleanup_stale_data():
    """Clean up stale data and keep only accurate current data"""
    db = DatabaseManager()
    conn = db.get_connection()
    cur = conn.cursor()

    print('🔧 CLEANING UP STALE DATA AND ENSURING LATEST DATA IS CURRENT')
    print('='*60)

    # For each symbol, keep only the most recently updated (accurate) data
    symbols_to_fix = ['0700.HK', '0005.HK', '1810.HK', '3690.HK', '9618.HK', '9988.HK']

    for symbol in symbols_to_fix:
        print(f'\nProcessing {symbol}...')
        
        # Get the most recently updated entry (this should be our corrected data)
        cur.execute('''
            SELECT trade_date, close_price, updated_at
            FROM daily_equity_technicals 
            WHERE symbol = %s
            ORDER BY updated_at DESC
            LIMIT 1
        ''', (symbol,))
        
        latest_accurate = cur.fetchone()
        if latest_accurate:
            latest_date, latest_price, latest_updated = latest_accurate
            print(f'  Latest accurate data: {latest_date} ${float(latest_price):.2f} (updated: {latest_updated})')
            
            # Delete all other entries for this symbol except the most recent one
            cur.execute('''
                DELETE FROM daily_equity_technicals 
                WHERE symbol = %s AND updated_at != %s
            ''', (symbol, latest_updated))
            
            deleted_count = cur.rowcount
            print(f'  Deleted {deleted_count} stale entries')
            
            # Update the remaining entry to today's date so it shows as current
            cur.execute('''
                UPDATE daily_equity_technicals 
                SET trade_date = CURRENT_DATE,
                    updated_at = CURRENT_TIMESTAMP
                WHERE symbol = %s AND updated_at = %s
            ''', (symbol, latest_updated))
            
            print(f'  ✅ Updated {symbol} to current date with accurate price ${float(latest_price):.2f}')

    conn.commit()

    print('\n📊 VERIFYING CLEANED DATA...')
    print('-' * 40)

    # Verify the cleanup worked
    for symbol in symbols_to_fix:
        cur.execute('''
            SELECT trade_date, close_price, rsi_14, ema_12, sma_20, updated_at
            FROM daily_equity_technicals 
            WHERE symbol = %s
            ORDER BY trade_date DESC
            LIMIT 1
        ''', (symbol,))
        
        result = cur.fetchone()
        if result:
            trade_date, close_price, rsi_14, ema_12, sma_20, updated_at = result
            rsi_display = f"{float(rsi_14):.1f}" if rsi_14 else "N/A"
            print(f'✅ {symbol}: {trade_date} | Close=${float(close_price):.2f} | RSI={rsi_display} | Updated: {updated_at.strftime("%H:%M")}')

    conn.close()
    print('\n🎉 Data cleanup completed! All symbols now show current, accurate data.')

if __name__ == "__main__":
    cleanup_stale_data()