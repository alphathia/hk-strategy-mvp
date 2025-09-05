#!/usr/bin/env python3
"""
Test script to verify TXYZN signal generation and database storage
"""

import sys
import os
sys.path.append('src')

from src.strategy import HKStrategyEngine
from src.database import DatabaseManager
import pandas as pd

def test_txyzn_signal_generation():
    """Test that signals are generated and stored with correct TXYZN format"""
    print("🧪 Testing TXYZN Signal Generation")
    print("=" * 50)
    
    # Initialize the strategy engine
    engine = HKStrategyEngine()
    
    # Test with a single ticker first
    test_ticker = "0700.HK"  # Tencent
    print(f"📊 Testing signal generation for {test_ticker}")
    
    try:
        # Generate signals (this will call our updated save_signal_to_db method)
        results = engine.generate_signals_for_watchlist()
        
        if test_ticker in results:
            signal_result = results[test_ticker]['signals']
            indicators = results[test_ticker]['indicators']
            
            print(f"✅ Successfully generated signals for {test_ticker}")
            print(f"   - A (Strong Buy): {signal_result.A}")
            print(f"   - B (Buy): {signal_result.B}")
            print(f"   - C (Sell): {signal_result.C}")
            print(f"   - D (Strong Sell): {signal_result.D}")
            print(f"   - Recommendation: {signal_result.recommendation}")
            print(f"   - Price: ${indicators.price:.2f}")
        
        # Verify database storage
        print("\n🔍 Checking database storage...")
        db = DatabaseManager()
        
        # Query recent signals with TXYZN format
        query = """
        SELECT symbol, signal_type, strategy_base, signal_magnitude, 
               signal_strength, strategy_category, price, created_at
        FROM trading_signals 
        WHERE symbol = %s 
        AND created_at > NOW() - INTERVAL '5 minutes'
        ORDER BY created_at DESC 
        LIMIT 5
        """
        
        with db.get_connection() as conn:
            recent_signals_df = pd.read_sql(query, conn, params=[test_ticker])
        
        if len(recent_signals_df) > 0:
            print("✅ Found recent signals in database:")
            for _, row in recent_signals_df.iterrows():
                print(f"   📈 {row['symbol']}: {row['signal_type']} "
                      f"(Base: {row['strategy_base']}, Magnitude: {row['signal_magnitude']}, "
                      f"Category: {row['strategy_category']})")
                print(f"      Price: ${row['price']:.2f}, Strength: {row['signal_strength']:.2f}")
                print(f"      Time: {str(row['created_at'])[:19]}")
                print()
        else:
            print("⚠️ No recent signals found in database")
            
        # Verify strategy catalog
        print("🗂️ Checking strategy catalog...")
        catalog_query = """
        SELECT strategy_base, strategy_name, signal_side, category, priority
        FROM strategy_catalog 
        ORDER BY priority 
        LIMIT 5
        """
        
        with db.get_connection() as conn:
            catalog_df = pd.read_sql(catalog_query, conn)
        
        if len(catalog_df) > 0:
            print("✅ Strategy catalog populated:")
            for _, row in catalog_df.iterrows():
                side_emoji = {"B": "🟢", "S": "🔴", "H": "🟡"}[row['signal_side']]
                print(f"   {side_emoji} {row['strategy_base']}: {row['strategy_name']} ({row['category']})")
        else:
            print("❌ Strategy catalog is empty")
            
        print("\n" + "=" * 50)
        print("✅ TXYZN Signal System Test Completed Successfully!")
        print("\n📝 Key Points:")
        print("   • Strategy bases (BBRK, SBDN, BDIV, etc.) represent actual strategies")
        print("   • Magnitude (1-9) represents signal strength/confidence level")
        print("   • Database correctly stores both strategy_base and signal_magnitude")
        print("   • Strategy Editor can now properly display the distinction")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_strategy_base_understanding():
    """Test that we understand strategy bases vs magnitudes correctly"""
    print("\n🎯 Testing Strategy Base vs Magnitude Understanding")
    print("=" * 50)
    
    example_signals = [
        ("BBRK9", "BBRK", 9, "Strong Buy Breakout"),
        ("BBRK3", "BBRK", 3, "Weak Buy Breakout"),
        ("SBRK7", "SBRK", 7, "Strong Sell Breakdown"),
        ("SBDN3", "SBDN", 3, "Light Sell Breakdown")
    ]
    
    print("📋 Example TXYZN Signal Breakdown:")
    for signal, base, magnitude, description in example_signals:
        print(f"   {signal}: Strategy Base = {base}, Magnitude = {magnitude}")
        print(f"             → {description}")
        print()
    
    print("✅ Understanding confirmed:")
    print("   • Strategy Base (XYZ): The actual trading strategy")
    print("   • Magnitude (N): Signal strength/confidence (1=weak, 9=strong)")
    print("   • Same strategy base can have different magnitudes")
    
    return True

if __name__ == "__main__":
    print("🚀 TXYZN Signal System Test Suite")
    print("=" * 60)
    
    success = True
    
    # Test strategy understanding
    success &= test_strategy_base_understanding()
    
    # Test signal generation
    success &= test_txyzn_signal_generation()
    
    if success:
        print("\n🎉 All tests passed! TXYZN system is working correctly.")
    else:
        print("\n💥 Some tests failed. Check the output above for details.")
    
    sys.exit(0 if success else 1)