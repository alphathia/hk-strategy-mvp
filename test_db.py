#!/usr/bin/env python3
"""
Test script to verify PostgreSQL database connection and data
"""
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from database import DatabaseManager
    
    print("🔧 Testing HK Strategy Database Connection...")
    
    # Initialize database manager
    db = DatabaseManager()
    print(f"Database URL: {db.db_url}")
    
    # Test connection
    try:
        conn = db.get_connection()
        print("✅ Database connection successful!")
        conn.close()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)
    
    # Test portfolio data
    print("\n📊 Testing Portfolio Data...")
    portfolio_df = db.get_portfolio_positions()
    
    if portfolio_df.empty:
        print("❌ No portfolio data found")
        print("Run: docker-compose up -d && docker-compose exec postgres psql -U trader -d hk_strategy -f /docker-entrypoint-initdb.d/init.sql")
    else:
        print(f"✅ Found {len(portfolio_df)} portfolio positions:")
        for _, row in portfolio_df.iterrows():
            print(f"  • {row['symbol']}: {row['company_name']} - {row['quantity']:,} shares @ HK${row['avg_cost']:.2f}")
    
    print("\n🎯 Ready to run dashboard:")
    print("streamlit run dashboard.py")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the project directory and dependencies are installed")
except Exception as e:
    print(f"❌ Unexpected error: {e}")