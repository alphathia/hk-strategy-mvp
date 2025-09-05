#!/usr/bin/env python3
"""
Diagnostic script to identify why EMA-5 is not showing in the dashboard
"""

import sys
import os
sys.path.append('src')

def check_database_connection():
    """Test database connection and basic table access"""
    print("🔍 Testing database connection...")
    
    try:
        from database import DatabaseManager
        
        db_manager = DatabaseManager()
        conn = db_manager.get_connection()
        
        with conn:
            with conn.cursor() as cur:
                # Test basic connection
                cur.execute("SELECT version();")
                version = cur.fetchone()
                print(f"✅ Database connection successful: {version[0][:50]}...")
                
                # Check if daily_equity_technicals table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'daily_equity_technicals'
                    );
                """)
                table_exists = cur.fetchone()[0]
                
                if table_exists:
                    print("✅ daily_equity_technicals table exists")
                    return True
                else:
                    print("❌ daily_equity_technicals table does NOT exist")
                    return False
                    
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def check_ema5_column():
    """Check if ema_5 column exists in the table"""
    print("\n📊 Checking EMA-5 column...")
    
    try:
        from database import DatabaseManager
        
        db_manager = DatabaseManager()
        conn = db_manager.get_connection()
        
        with conn:
            with conn.cursor() as cur:
                # Check column exists
                cur.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'daily_equity_technicals' 
                    AND column_name = 'ema_5';
                """)
                column_info = cur.fetchone()
                
                if column_info:
                    print(f"✅ ema_5 column exists: {column_info[0]} ({column_info[1]})")
                    return True
                else:
                    print("❌ ema_5 column does NOT exist - migration failed")
                    return False
                    
    except Exception as e:
        print(f"❌ Error checking ema_5 column: {e}")
        return False

def check_data_availability():
    """Check if there's any data in daily_equity_technicals"""
    print("\n📈 Checking data availability...")
    
    try:
        from database import DatabaseManager
        
        db_manager = DatabaseManager()
        conn = db_manager.get_connection()
        
        with conn:
            with conn.cursor() as cur:
                # Check total records
                cur.execute("SELECT COUNT(*) FROM daily_equity_technicals;")
                total_records = cur.fetchone()[0]
                print(f"📊 Total records in daily_equity_technicals: {total_records}")
                
                if total_records == 0:
                    print("❌ Table is empty - no data to calculate EMA-5 from")
                    return False
                
                # Check EMA-5 populated records
                cur.execute("SELECT COUNT(*) FROM daily_equity_technicals WHERE ema_5 IS NOT NULL;")
                ema5_records = cur.fetchone()[0]
                print(f"📊 Records with EMA-5 data: {ema5_records}")
                
                if ema5_records == 0:
                    print("❌ No EMA-5 data populated - migration backfill failed")
                    return False
                
                # Check available symbols
                cur.execute("SELECT DISTINCT symbol FROM daily_equity_technicals ORDER BY symbol LIMIT 10;")
                symbols = cur.fetchall()
                print(f"📊 Available symbols (first 10): {[s[0] for s in symbols]}")
                
                # Check date range
                cur.execute("""
                    SELECT MIN(trade_date), MAX(trade_date) 
                    FROM daily_equity_technicals 
                    WHERE ema_5 IS NOT NULL;
                """)
                date_range = cur.fetchone()
                if date_range and date_range[0]:
                    print(f"📊 EMA-5 date range: {date_range[0]} to {date_range[1]}")
                
                # Sample EMA-5 data
                cur.execute("""
                    SELECT symbol, trade_date, close_price, ema_5 
                    FROM daily_equity_technicals 
                    WHERE ema_5 IS NOT NULL 
                    ORDER BY trade_date DESC 
                    LIMIT 5;
                """)
                samples = cur.fetchall()
                
                if samples:
                    print("📊 Sample EMA-5 data:")
                    for sample in samples:
                        print(f"   {sample[0]}: {sample[1]} | Price: {sample[2]} | EMA-5: {sample[3]}")
                    return True
                else:
                    print("❌ No sample data found")
                    return False
                    
    except Exception as e:
        print(f"❌ Error checking data availability: {e}")
        return False

def test_specific_symbol():
    """Test EMA-5 data for common HK symbols"""
    print("\n🎯 Testing specific symbols...")
    
    test_symbols = ['0700.HK', '0005.HK', '0700', '0005', 'AAPL', 'TSLA']
    
    try:
        from database import DatabaseManager
        
        db_manager = DatabaseManager()
        conn = db_manager.get_connection()
        
        with conn:
            with conn.cursor() as cur:
                found_symbols = []
                
                for symbol in test_symbols:
                    cur.execute("""
                        SELECT COUNT(*) 
                        FROM daily_equity_technicals 
                        WHERE symbol = %s AND ema_5 IS NOT NULL;
                    """, (symbol,))
                    count = cur.fetchone()[0]
                    
                    if count > 0:
                        print(f"✅ {symbol}: {count} records with EMA-5")
                        found_symbols.append(symbol)
                    else:
                        print(f"❌ {symbol}: No EMA-5 data")
                
                # Test the first found symbol with recent data
                if found_symbols:
                    test_symbol = found_symbols[0]
                    cur.execute("""
                        SELECT trade_date, close_price, ema_5 
                        FROM daily_equity_technicals 
                        WHERE symbol = %s AND ema_5 IS NOT NULL
                        ORDER BY trade_date DESC 
                        LIMIT 10;
                    """, (test_symbol,))
                    recent_data = cur.fetchall()
                    
                    print(f"\n📈 Recent EMA-5 data for {test_symbol}:")
                    for data in recent_data[:5]:
                        print(f"   {data[0]}: Close={data[1]}, EMA-5={data[2]}")
                    
                    return test_symbol, len(recent_data)
                else:
                    print("❌ No symbols found with EMA-5 data")
                    return None, 0
                    
    except Exception as e:
        print(f"❌ Error testing specific symbols: {e}")
        return None, 0

def check_dashboard_query():
    """Simulate the dashboard's EMA-5 query"""
    print("\n🖥️ Simulating dashboard query...")
    
    try:
        from database import DatabaseManager
        from datetime import datetime, timedelta
        
        # Test with a known good symbol and recent dates
        test_symbol = '0700.HK'  # Default test
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)  # Last 30 days
        
        db_manager = DatabaseManager()
        conn = db_manager.get_connection()
        
        with conn:
            with conn.cursor() as cur:
                # This mimics the exact query from dashboard.py line 4117-4124
                query = """
                    SELECT trade_date, ema_5
                    FROM daily_equity_technicals
                    WHERE symbol = %s
                      AND trade_date >= %s
                      AND trade_date <= %s
                      AND ema_5 IS NOT NULL
                    ORDER BY trade_date
                """
                
                cur.execute(query, (test_symbol, start_date, end_date))
                results = cur.fetchall()
                
                print(f"🔍 Dashboard query simulation for {test_symbol}:")
                print(f"   Date range: {start_date} to {end_date}")
                print(f"   Results found: {len(results)}")
                
                if results:
                    print("✅ Dashboard query would return EMA-5 data:")
                    for i, result in enumerate(results[-3:]):  # Show last 3
                        print(f"   {result[0]}: {result[1]}")
                    return True
                else:
                    print("❌ Dashboard query returns no results")
                    
                    # Check if symbol exists at all
                    cur.execute("SELECT COUNT(*) FROM daily_equity_technicals WHERE symbol = %s", (test_symbol,))
                    symbol_count = cur.fetchone()[0]
                    
                    if symbol_count == 0:
                        print(f"   Reason: Symbol '{test_symbol}' not found in database")
                    else:
                        print(f"   Symbol exists ({symbol_count} records) but no EMA-5 data in date range")
                    
                    return False
                    
    except Exception as e:
        print(f"❌ Error simulating dashboard query: {e}")
        return False

def main():
    """Run complete EMA-5 diagnostic"""
    print("🔧 EMA-5 Diagnostic Tool")
    print("=" * 50)
    
    checks = [
        ("Database Connection", check_database_connection),
        ("EMA-5 Column Existence", check_ema5_column),
        ("Data Availability", check_data_availability),
        ("Specific Symbol Test", lambda: test_specific_symbol()[0] is not None),
        ("Dashboard Query Simulation", check_dashboard_query),
    ]
    
    results = []
    
    for check_name, check_func in checks:
        print()
        try:
            success = check_func()
            results.append((check_name, success))
        except Exception as e:
            print(f"❌ {check_name} failed with error: {e}")
            results.append((check_name, False))
    
    print("\n" + "=" * 50)
    print("📋 Diagnostic Summary:")
    
    for check_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {check_name}")
    
    failed_checks = [name for name, success in results if not success]
    
    if not failed_checks:
        print("\n🎉 All diagnostics passed!")
        print("EMA-5 data should be available. Try:")
        print("1. Clear Streamlit cache: streamlit cache clear")
        print("2. Restart dashboard")
        print("3. Use a symbol from the available list above")
    else:
        print(f"\n⚠️ Failed checks: {failed_checks}")
        print("\n🔧 Recommended fixes:")
        
        if "EMA-5 Column Existence" in failed_checks:
            print("- Re-run the migration: psql -d hk_strategy -f add_ema5_indicator.sql")
        
        if "Data Availability" in failed_checks:
            print("- Check if daily_equity_technicals table is being populated")
            print("- Verify your data pipeline is running")
        
        if "Dashboard Query Simulation" in failed_checks:
            print("- Try different symbols that exist in your database")
            print("- Check date ranges match your data")

if __name__ == "__main__":
    main()