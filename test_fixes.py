#!/usr/bin/env python3
"""
Test script to verify all fixes are working properly
"""

import sys
import os
sys.path.append('src')
from src.database import DatabaseManager
from src.portfolio_analysis_manager import PortfolioAnalysisManager
from datetime import date, timedelta
import pandas as pd

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def test_sql_extract_fix():
    """Test that the SQL EXTRACT error is fixed"""
    print("=" * 60)
    print("TEST 1: SQL EXTRACT Fix")
    print("=" * 60)
    
    db = DatabaseManager()
    conn = db.get_connection()
    cur = conn.cursor()
    
    # Test the previously problematic symbols
    problematic_symbols = ['0316.HK', '0388.HK', '0823.HK', '0939.HK', '2888.HK']
    test_date = '2025-08-29'
    
    print(f"Testing {len(problematic_symbols)} previously problematic symbols...")
    
    success_count = 0
    for symbol in problematic_symbols:
        try:
            # Test the fixed SQL query
            cur.execute("""
                SELECT open_price, close_price, high_price, low_price, volume, trade_date
                FROM daily_equity_technicals 
                WHERE symbol = %s 
                AND ABS(trade_date - %s::date) <= 7
                ORDER BY ABS(trade_date - %s::date)
                LIMIT 1
            """, (symbol, test_date, test_date))
            
            result = cur.fetchone()
            if result:
                print(f"✅ {symbol}: Close=${result[1]:.2f}, Date={result[5]}")
                success_count += 1
            else:
                print(f"⚠️  {symbol}: No data found within 7 days of {test_date}")
                
        except Exception as e:
            print(f"❌ {symbol}: SQL Error - {e}")
    
    conn.close()
    print(f"\nResult: {success_count}/{len(problematic_symbols)} symbols working without SQL errors")
    return success_count == len(problematic_symbols)

def test_end_equity_calculation():
    """Test that End Equity calculation now returns proper values"""
    print("\n" + "=" * 60)
    print("TEST 2: End Equity Calculation")
    print("=" * 60)
    
    try:
        # Initialize the analysis manager
        db_manager = DatabaseManager()
        analysis_manager = PortfolioAnalysisManager(db_manager)
        
        # Get a sample portfolio analysis to test
        db = DatabaseManager()
        conn = db.get_connection()
        cur = conn.cursor()
        
        # Find an existing portfolio analysis
        cur.execute("""
            SELECT id, portfolio_id, end_date, end_equity_value 
            FROM portfolio_analyses 
            WHERE end_equity_value = 0 OR end_equity_value IS NULL
            LIMIT 1
        """)
        
        result = cur.fetchone()
        if not result:
            print("No portfolio analyses with zero end equity found - checking any analysis...")
            cur.execute("""
                SELECT id, portfolio_id, end_date, end_equity_value 
                FROM portfolio_analyses 
                ORDER BY created_at DESC
                LIMIT 1
            """)
            result = cur.fetchone()
        
        if result:
            analysis_id, portfolio_id, end_date, current_end_equity = result
            print(f"Testing analysis ID {analysis_id} for portfolio {portfolio_id}")
            print(f"End date: {end_date}")
            print(f"Current end_equity_value: {current_end_equity}")
            
            # Test the _get_current_market_value method
            try:
                market_value = analysis_manager._get_current_market_value(analysis_id)
                print(f"Calculated market value: ${market_value:.2f}")
                
                if market_value > 0:
                    print("✅ End Equity calculation now returns non-zero value!")
                    
                    # Update the analysis calculations
                    print("Updating analysis calculations...")
                    analysis_manager.update_analysis_calculations(analysis_id)
                    
                    # Check the updated value
                    cur.execute("SELECT end_equity_value FROM portfolio_analyses WHERE id = %s", (analysis_id,))
                    new_end_equity = cur.fetchone()[0]
                    print(f"Updated end_equity_value: ${new_end_equity:.2f}")
                    
                    conn.close()
                    return True
                else:
                    print("❌ End Equity calculation still returns zero")
                    conn.close()
                    return False
                    
            except Exception as calc_error:
                print(f"❌ Error in market value calculation: {calc_error}")
                conn.close()
                return False
        else:
            print("❌ No portfolio analyses found to test")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Error testing End Equity calculation: {e}")
        return False

def test_database_price_data():
    """Test that database price data is being used correctly"""
    print("\n" + "=" * 60) 
    print("TEST 3: Database Price Data Usage")
    print("=" * 60)
    
    try:
        db_manager = DatabaseManager()
        analysis_manager = PortfolioAnalysisManager(db_manager)
        
        # Test symbols with known data
        test_symbols = ['0316.HK', '0388.HK', '0823.HK']
        start_date = date(2025, 8, 25)
        end_date = date(2025, 8, 29)
        
        print(f"Testing bulk price fetch for {len(test_symbols)} symbols...")
        print(f"Date range: {start_date} to {end_date}")
        
        # Test the enhanced fetch_bulk_historical_prices method
        price_df = analysis_manager.fetch_bulk_historical_prices(test_symbols, start_date, end_date)
        
        if not price_df.empty:
            print(f"✅ Successfully retrieved {len(price_df)} price records")
            print(f"Symbols with data: {list(price_df['symbol'].unique())}")
            
            # Show sample data
            for symbol in test_symbols:
                symbol_data = price_df[price_df['symbol'] == symbol]
                if not symbol_data.empty:
                    latest_price = symbol_data.iloc[-1]
                    print(f"  {symbol}: ${latest_price['close_price']:.2f} on {latest_price['date'].date()}")
                else:
                    print(f"  {symbol}: No data found")
            
            return True
        else:
            print("❌ No price data retrieved")
            return False
            
    except Exception as e:
        print(f"❌ Error testing database price data: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 TESTING ALL PORTFOLIO ANALYSIS FIXES")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: SQL EXTRACT fix
    test_results.append(("SQL EXTRACT Fix", test_sql_extract_fix()))
    
    # Test 2: End Equity calculation
    test_results.append(("End Equity Calculation", test_end_equity_calculation()))
    
    # Test 3: Database price data usage
    test_results.append(("Database Price Data", test_database_price_data()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(test_results)} tests passed")
    
    if passed == len(test_results):
        print("🎉 All fixes are working correctly!")
    else:
        print("⚠️  Some issues still need attention")

if __name__ == "__main__":
    main()