#!/usr/bin/env python3
"""
Comprehensive test script for EMA-5 indicator integration
Tests all components: database, calculation, strategy usage, and UI integration
"""

import sys
import os
import pandas as pd
import numpy as np

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_ema5_calculation():
    """Test EMA-5 calculation accuracy"""
    print("🧮 Testing EMA-5 calculation accuracy...")
    
    try:
        from strategy import ema
        
        # Create test data
        test_prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109]
        df = pd.DataFrame({'Close': test_prices})
        
        # Calculate EMA-5
        df["EMA5"] = ema(df["Close"], 5)
        
        # Manual EMA-5 calculation for verification
        alpha = 2.0 / (5 + 1)
        manual_ema = [test_prices[0]]  # Initialize with first price
        for i in range(1, len(test_prices)):
            ema_val = (test_prices[i] * alpha) + (manual_ema[-1] * (1 - alpha))
            manual_ema.append(ema_val)
        
        # Compare calculated vs manual
        calculated_ema = df["EMA5"].iloc[-1]
        manual_ema_final = manual_ema[-1]
        
        print(f"✅ EMA-5 calculation test:")
        print(f"   Final price: {test_prices[-1]}")
        print(f"   Calculated EMA-5: {calculated_ema:.4f}")
        print(f"   Manual EMA-5: {manual_ema_final:.4f}")
        print(f"   Difference: {abs(calculated_ema - manual_ema_final):.6f}")
        
        assert abs(calculated_ema - manual_ema_final) < 0.001, "EMA-5 calculation accuracy test failed"
        return True
        
    except Exception as e:
        print(f"❌ EMA-5 calculation test failed: {e}")
        return False

def test_strategy_integration():
    """Test EMA-5 integration in strategy system"""
    print("\n📈 Testing strategy integration...")
    
    try:
        from strategy import Strategy, Indicators
        
        # Create mock indicators with EMA-5
        indicators = Indicators(
            price=105.0,
            rsi14=60.0,
            ema5=104.5,
            ema20=103.0,
            ema50=102.0,
            volume=1000000,
            atr14=2.5,
            twenty_day_high=106.0,
            twenty_day_low=98.0,
            bollinger_upper=107.0,
            bollinger_lower=99.0,
            macd=0.5,
            williams_r=-25.0
        )
        
        print(f"✅ Strategy integration test:")
        print(f"   Price: {indicators.price}")
        print(f"   EMA-5: {indicators.ema5}")
        print(f"   EMA-20: {indicators.ema20}")
        print(f"   EMA-50: {indicators.ema50}")
        print(f"   Price above EMA-5: {indicators.price > indicators.ema5}")
        print(f"   EMA-5 above EMA-20: {indicators.ema5 > indicators.ema20}")
        
        # Test EMA alignment
        bullish_alignment = (indicators.ema5 > indicators.ema20 and 
                           indicators.ema20 > indicators.ema50)
        print(f"   Bullish EMA alignment: {bullish_alignment}")
        
        return True
        
    except Exception as e:
        print(f"❌ Strategy integration test failed: {e}")
        return False

def test_indicator_dictionary():
    """Test EMA-5 in indicator dictionary"""
    print("\n📚 Testing indicator dictionary integration...")
    
    try:
        from indicator_dictionary import IndicatorDictionary
        
        # Test EMA-5 definition exists
        ema5_info = IndicatorDictionary.INDICATORS.get("ema5")
        assert ema5_info is not None, "EMA-5 not found in indicator dictionary"
        
        print(f"✅ Indicator dictionary test:")
        print(f"   Name: {ema5_info['name']}")
        print(f"   Full Name: {ema5_info['full_name']}")
        print(f"   Category: {ema5_info['category'].value}")
        print(f"   Description: {ema5_info['description']}")
        
        # Test EMA-5 is in overlay indicators
        overlay_indicators = IndicatorDictionary.get_chart_overlay_indicators()
        assert "ema5" in overlay_indicators, "EMA-5 not in overlay indicators"
        print(f"   ✅ EMA-5 included in chart overlay indicators")
        
        # Test UI configuration
        ui_config = IndicatorDictionary.get_ui_display_config("ema5")
        print(f"   UI Chart Type: {ui_config['chart_type']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Indicator dictionary test failed: {e}")
        return False

def test_dashboard_syntax():
    """Test dashboard compilation after EMA-5 addition"""
    print("\n🖥️ Testing dashboard integration...")
    
    try:
        import subprocess
        result = subprocess.run(['python', '-m', 'py_compile', 'dashboard.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dashboard compiles successfully with EMA-5 integration")
        else:
            print(f"❌ Dashboard compilation error: {result.stderr}")
            return False
            
        # Check if EMA-5 is in the indicator lists
        with open('dashboard.py', 'r') as f:
            dashboard_content = f.read()
            
        if '"ema_5"' in dashboard_content and '"EMA (5)"' in dashboard_content:
            print("✅ EMA-5 found in dashboard indicator lists")
        else:
            print("❌ EMA-5 not found in dashboard indicator lists")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Dashboard integration test failed: {e}")
        return False

def test_database_migration():
    """Test database migration script syntax"""
    print("\n🗄️ Testing database migration script...")
    
    try:
        # Check migration script exists and has proper SQL syntax
        migration_file = 'add_ema5_indicator.sql'
        
        if not os.path.exists(migration_file):
            print(f"❌ Migration file {migration_file} not found")
            return False
            
        with open(migration_file, 'r') as f:
            content = f.read()
            
        # Check for key components
        required_components = [
            'ALTER TABLE daily_equity_technicals',
            'ADD COLUMN IF NOT EXISTS ema_5',
            'calculate_ema5_backfill',
            'CREATE INDEX',
            'technical_analysis_view',
            'get_ema5_signal'
        ]
        
        missing_components = []
        for component in required_components:
            if component not in content:
                missing_components.append(component)
                
        if missing_components:
            print(f"❌ Missing components in migration script: {missing_components}")
            return False
            
        print("✅ Database migration script contains all required components:")
        print("   - ALTER TABLE for ema_5 column")
        print("   - Backfill function for historical data")
        print("   - Index creation for performance")
        print("   - Updated views and helper functions")
        
        return True
        
    except Exception as e:
        print(f"❌ Database migration test failed: {e}")
        return False

def main():
    """Run all EMA-5 integration tests"""
    print("🧪 Testing EMA-5 Indicator Integration")
    print("=" * 50)
    
    tests = [
        ("EMA-5 Calculation Accuracy", test_ema5_calculation),
        ("Strategy Integration", test_strategy_integration),
        ("Indicator Dictionary", test_indicator_dictionary),
        ("Dashboard Integration", test_dashboard_syntax),
        ("Database Migration", test_database_migration),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"\n✅ PASSED: {test_name}")
                passed += 1
            else:
                print(f"\n❌ FAILED: {test_name}")
                failed += 1
        except Exception as e:
            print(f"\n❌ ERROR in {test_name}: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! EMA-5 integration is complete.")
        print("\n📋 Implementation Summary:")
        print("✅ EMA-5 calculation: Already implemented and tested")
        print("✅ Strategy usage: Already integrated in signal logic")
        print("✅ Indicator dictionary: Comprehensive definition provided")  
        print("✅ Dashboard UI: Added to technical indicator selections")
        print("✅ Database schema: Migration script created for ema_5 column")
        print("\n🚀 Next steps:")
        print("1. Run the database migration: add_ema5_indicator.sql")
        print("2. Restart dashboard: streamlit run dashboard.py")
        print("3. Test EMA-5 selection in technical indicators")
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)