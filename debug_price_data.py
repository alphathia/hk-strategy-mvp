#!/usr/bin/env python3
"""
Debug price data lookup issues
"""

import sys
import os
sys.path.append('src')
from src.portfolio_analysis_manager import PortfolioAnalysisManager
from src.database import DatabaseManager
from datetime import date
import pandas as pd

def debug_price_data():
    """Debug why price data lookup is failing"""
    
    print('🔍 DEBUGGING PRICE DATA LOOKUP')
    print('='*60)
    
    # Initialize managers
    db_manager = DatabaseManager()
    portfolio_manager = PortfolioAnalysisManager(db_manager)
    
    # Test the exact symbols from analysis 28
    symbols = ['0700.HK', '1810.HK', '3690.HK', '9618.HK', '9988.HK']
    start_date = date(2025, 1, 2)
    end_date = date(2025, 8, 31)
    
    print(f'Fetching price data for symbols: {symbols}')
    print(f'Date range: {start_date} to {end_date}')
    
    # Get price data using the same method as the portfolio manager
    try:
        price_df = portfolio_manager._get_database_price_data(symbols, start_date, end_date)
        print(f'\\n📊 PRICE DATA RESULTS:')
        print(f'  Total records: {len(price_df)}')
        
        if not price_df.empty:
            print(f'  Columns: {list(price_df.columns)}')
            print(f'  Date range in data: {price_df["date"].min()} to {price_df["date"].max()}')
            print(f'  Symbols in data: {sorted(price_df["symbol"].unique())}')
            
            # Check sample data for Jan 2, 2025
            test_date = date(2025, 1, 2)
            jan2_data = price_df[price_df['date'].dt.date == test_date]
            print(f'\\n💰 PRICE DATA FOR {test_date}:')
            print(f'  Records found: {len(jan2_data)}')
            
            for _, row in jan2_data.iterrows():
                print(f'    {row["symbol"]}: ${float(row["close_price"]):.2f}')
            
            # Check if the data structure matches what the equity calculation expects
            print(f'\\n🔍 DATA STRUCTURE CHECK:')
            print(f'  price_df["date"] type: {type(price_df["date"].iloc[0]) if len(price_df) > 0 else "N/A"}')
            print(f'  Sample date value: {price_df["date"].iloc[0] if len(price_df) > 0 else "N/A"}')
            
            # Test the exact lookup logic used in _calculate_daily_values_trading_days
            trading_day = test_date
            day_prices = price_df[price_df['date'].dt.date == trading_day] if not price_df.empty else pd.DataFrame()
            print(f'\\n🎯 EXACT LOOKUP TEST FOR {trading_day}:')
            print(f'  day_prices length: {len(day_prices)}')
            
            # Test symbol lookup
            test_symbol = '0700.HK'
            symbol_prices = day_prices[day_prices['symbol'] == test_symbol]
            print(f'  {test_symbol} prices found: {len(symbol_prices)}')
            if not symbol_prices.empty:
                price = float(symbol_prices.iloc[0]['close_price'])
                print(f'  {test_symbol} price: ${price:.2f}')
            
        else:
            print('  ❌ No price data returned!')
            
    except Exception as e:
        print(f'❌ Error fetching price data: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_price_data()