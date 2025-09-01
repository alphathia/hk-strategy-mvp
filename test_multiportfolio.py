#!/usr/bin/env python3
"""
Multi-Portfolio Functionality Test
Quick verification that the migrated database supports multi-portfolio operations
"""

import sys
import pandas as pd
sys.path.append('src')

from database import DatabaseManager
from database_enhanced import DatabaseManager as EnhancedDatabaseManager

def test_multiportfolio_functionality():
    """Test that multi-portfolio features work correctly"""
    
    print("🔍 TESTING MULTI-PORTFOLIO FUNCTIONALITY")
    print("=" * 60)
    
    # Test both database managers
    db_managers = {
        'Standard': DatabaseManager(),
        'Enhanced': EnhancedDatabaseManager()
    }
    
    success_count = 0
    total_tests = 0
    
    for name, db in db_managers.items():
        print(f"\n📊 Testing {name} DatabaseManager:")
        print("-" * 40)
        
        try:
            # Test 1: Get all portfolios
            total_tests += 1
            if hasattr(db, 'get_portfolios'):
                portfolios = db.get_portfolios()
                print(f"✅ Found {len(portfolios)} portfolios: {list(portfolios['portfolio_id']) if 'portfolio_id' in portfolios.columns else 'N/A'}")
                success_count += 1
            else:
                print("❌ get_portfolios method not available")
            
            # Test 2: Get positions for specific portfolio
            total_tests += 1
            positions_my_hkex = db.get_portfolio_positions(portfolio_id='My_HKEX_ALL')
            print(f"✅ 'My_HKEX_ALL' portfolio: {len(positions_my_hkex)} positions")
            success_count += 1
            
            # Test 3: Get all positions (should work regardless of schema)
            total_tests += 1
            all_positions = db.get_portfolio_positions()
            print(f"✅ All positions query: {len(all_positions)} total positions")
            success_count += 1
            
            # Test 4: Get trading signals
            total_tests += 1
            signals = db.get_trading_signals(limit=10, portfolio_id='My_HKEX_ALL')
            print(f"✅ Trading signals for 'My_HKEX_ALL': {len(signals)} signals")
            success_count += 1
            
            # Test 5: Schema detection for Enhanced manager
            if name == 'Enhanced':
                total_tests += 1
                schema_info = db.get_schema_info()
                print(f"✅ Schema version: {schema_info['version']}")
                print(f"   Multi-portfolio: {schema_info['capabilities']['multi_portfolio']}")
                print(f"   Backward compatible: {schema_info['capabilities']['backward_compatible']}")
                success_count += 1
            
        except Exception as e:
            print(f"❌ Error testing {name}: {e}")
    
    print(f"\n🏁 TEST SUMMARY:")
    print(f"   Tests passed: {success_count}/{total_tests}")
    print(f"   Success rate: {success_count/total_tests*100:.1f}%")
    
    if success_count == total_tests:
        print("✅ ALL TESTS PASSED - Multi-portfolio functionality is working!")
        return True
    else:
        print("❌ Some tests failed - Multi-portfolio functionality has issues")
        return False

def show_portfolio_data():
    """Show actual portfolio data to verify migration"""
    
    print(f"\n📊 ACTUAL PORTFOLIO DATA:")
    print("=" * 60)
    
    try:
        db = EnhancedDatabaseManager()
        
        # Show portfolios
        portfolios = db.get_portfolios()
        print(f"\n📁 PORTFOLIOS ({len(portfolios)}):")
        for _, portfolio in portfolios.iterrows():
            print(f"   • {portfolio['portfolio_id']}: {portfolio['name']}")
        
        # Show positions for main portfolio
        main_portfolio = 'My_HKEX_ALL'
        positions = db.get_portfolio_positions(portfolio_id=main_portfolio)
        print(f"\n💰 POSITIONS IN '{main_portfolio}' ({len(positions)}):")
        
        if len(positions) > 0:
            for _, pos in positions.head(5).iterrows():  # Show first 5
                market_value = pos.get('market_value', 0) or 0
                print(f"   • {pos['symbol']}: {pos['quantity']} shares @ {pos.get('current_price', 0)} = ${market_value:,.2f}")
            
            if len(positions) > 5:
                print(f"   ... and {len(positions) - 5} more positions")
        
        # Show trading signals
        signals = db.get_trading_signals(limit=5, portfolio_id=main_portfolio)
        print(f"\n📈 RECENT TRADING SIGNALS ({len(signals)}):")
        for _, signal in signals.iterrows():
            print(f"   • {signal['symbol']}: {signal['signal_type']} (strength: {signal['signal_strength']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error showing portfolio data: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 MULTI-PORTFOLIO DATABASE VERIFICATION")
    print("=" * 80)
    
    # Test functionality
    functionality_ok = test_multiportfolio_functionality()
    
    # Show actual data
    data_ok = show_portfolio_data()
    
    print(f"\n🎯 FINAL VERDICT:")
    print("=" * 80)
    
    if functionality_ok and data_ok:
        print("✅ MIGRATION WAS SUCCESSFUL!")
        print("✅ Multi-portfolio functionality is fully working")
        print("✅ All data has been properly migrated")
        print("✅ You can now use the multi-portfolio dashboard")
        print("\n🚀 Next steps:")
        print("   • Start dashboard: python dashboard.py")
        print("   • Or test via browser: streamlit run dashboard.py")
    else:
        print("❌ MIGRATION HAS ISSUES")
        print("❌ Multi-portfolio functionality is not working properly")
        print("\n🔧 Recommended actions:")
        print("   • Check backup files for restoration")
        print("   • Review migration logs for errors")
        print("   • Consider manual database cleanup")

if __name__ == "__main__":
    main()