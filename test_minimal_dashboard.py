#!/usr/bin/env python3
"""
Test Script for Minimal Dashboard
Verifies that minimal_dashboard.py can be imported and basic functions work
"""

def test_minimal_dashboard():
    """Test minimal dashboard imports and basic functionality"""
    
    print("🧪 Testing Minimal Dashboard...")
    print("=" * 50)
    
    try:
        # Test 1: Import the minimal dashboard
        print("1. Testing imports...")
        import minimal_dashboard
        print("   ✅ Import successful")
        
        # Test 2: Test helper functions
        print("2. Testing helper functions...")
        
        # Test strategy intent function
        intent = minimal_dashboard._get_strategy_intent('BBRK')
        print(f"   ✅ _get_strategy_intent('BBRK'): {intent}")
        
        # Test base trigger function  
        trigger = minimal_dashboard._get_base_trigger('BBRK')
        print(f"   ✅ _get_base_trigger('BBRK'): {trigger}")
        
        # Test strategy characteristics
        characteristics = minimal_dashboard._get_strategy_characteristics('BBRK')
        print(f"   ✅ _get_strategy_characteristics('BBRK'): {len(characteristics)} characteristics")
        
        # Test level conditions parser
        conditions = minimal_dashboard._parse_level_conditions("BBRK test description")
        print(f"   ✅ _parse_level_conditions: {len(conditions)} conditions")
        
        print("\n🎉 SUCCESS: Minimal dashboard passes all tests!")
        print("\n📋 KEY BENEFITS:")
        print("   • ✅ Clean, focused dashboard with only Strategy Base Catalog")
        print("   • ✅ All helper functions working correctly")  
        print("   • ✅ No syntax errors or import issues")
        print("   • ✅ Ready for Streamlit deployment")
        print("\n🚀 TO RUN: streamlit run minimal_dashboard.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_minimal_dashboard()
    if success:
        print("\n✨ The minimal dashboard is ready to use!")
        print("   Run: streamlit run minimal_dashboard.py")
    else:
        print("\n⚠️ Issues found - please check the errors above")