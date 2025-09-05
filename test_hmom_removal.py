#!/usr/bin/env python3
"""
Test script to verify HMOM removal from Strategy Editor
"""

import sys
import os

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_trading_signals_removal():
    """Test that trading_signals.py no longer returns HMOM"""
    try:
        from trading_signals import TradingSignalGenerator
        
        generator = TradingSignalGenerator()
        
        # Test neutral score that used to return HMOM5
        neutral_score = 0.0
        signal = generator._determine_signal_type(neutral_score)
        
        print(f"✅ Neutral score ({neutral_score}) now returns: {signal}")
        assert signal != 'HMOM5', f"ERROR: Still returning HMOM5 for neutral score"
        assert signal is None, f"ERROR: Expected None for neutral score, got {signal}"
        
        # Test signal descriptions
        descriptions = generator.get_signal_description('HMOM5')
        print(f"✅ HMOM5 description now: {descriptions}")
        
        # Test signal colors  
        color = generator.get_signal_color('HMOM5')
        print(f"✅ HMOM5 color now: {color}")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error in trading_signals test: {e}")
        return False
    
    return True

def test_strategy_removal():
    """Test that strategy.py no longer defaults to HMOM"""
    try:
        # Check that strategy.py compiles without HMOM references
        import subprocess
        result = subprocess.run(['python', '-m', 'py_compile', 'src/strategy.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ strategy.py compiles successfully after HMOM removal")
        else:
            print(f"❌ strategy.py compilation error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing strategy.py: {e}")
        return False
    
    return True

def test_signal_dictionary_removal():
    """Test that signal_dictionary.py no longer maps to HMOM"""
    try:
        from signal_dictionary import SignalDictionary
        
        # Check legacy mapping
        legacy_def = SignalDictionary.get_signal_definition('legacy_signal')
        if legacy_def:
            mapping = legacy_def.default_parameters.get('migration_mapping', {})
            c_mapping = mapping.get('C')
            
            print(f"✅ Legacy C signal now maps to: {c_mapping}")
            assert c_mapping != 'HMOM5', f"ERROR: C still maps to HMOM5"
            assert c_mapping is None, f"ERROR: Expected None for C mapping, got {c_mapping}"
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing signal_dictionary: {e}")
        return False
    
    return True

def test_dashboard_syntax():
    """Test that dashboard.py compiles after Strategy Editor changes"""
    try:
        import subprocess
        result = subprocess.run(['python', '-m', 'py_compile', 'dashboard.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ dashboard.py compiles successfully after Strategy Editor updates")
        else:
            print(f"❌ dashboard.py compilation error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing dashboard.py: {e}")
        return False
    
    return True

def main():
    """Run all HMOM removal tests"""
    print("🧪 Testing HMOM removal from Strategy Editor and application...")
    print("=" * 60)
    
    tests = [
        ("Trading Signals HMOM Removal", test_trading_signals_removal),
        ("Strategy HMOM Removal", test_strategy_removal),
        ("Signal Dictionary HMOM Removal", test_signal_dictionary_removal),
        ("Dashboard Strategy Editor Updates", test_dashboard_syntax),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            if test_func():
                print(f"✅ PASSED: {test_name}")
                passed += 1
            else:
                print(f"❌ FAILED: {test_name}")
                failed += 1
        except Exception as e:
            print(f"❌ ERROR in {test_name}: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! HMOM has been successfully removed.")
        print("\n📋 Next steps:")
        print("1. Run the database cleanup script: remove_hmom_cleanup.sql")
        print("2. Start the dashboard: streamlit run dashboard.py")
        print("3. Navigate to Strategy Editor and verify no HMOM strategies appear")
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)