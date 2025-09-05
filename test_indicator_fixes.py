#!/usr/bin/env python3
"""
Test script to verify EMA-5 display fix and 5-indicator limit changes
"""

import sys
import os
import re

def test_dashboard_compilation():
    """Test that dashboard compiles after changes"""
    print("🖥️ Testing dashboard compilation...")
    
    try:
        import subprocess
        result = subprocess.run(['python', '-m', 'py_compile', 'dashboard.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dashboard compiles successfully after updates")
            return True
        else:
            print(f"❌ Dashboard compilation error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing dashboard compilation: {e}")
        return False

def test_indicator_limit_changes():
    """Test that indicator limit has been changed from 3 to 5"""
    print("\n📊 Testing indicator limit changes...")
    
    try:
        with open('dashboard.py', 'r') as f:
            content = f.read()
        
        changes_found = []
        
        # Test 1: Modal dialog text change
        if "Select up to 5 technical indicators" in content:
            changes_found.append("✅ Modal dialog text updated to 'up to 5 indicators'")
        else:
            changes_found.append("❌ Modal dialog text not updated")
        
        # Test 2: Max selection validation
        if ">= 5 and not is_selected" in content:
            changes_found.append("✅ Max selection validation updated to 5")
        else:
            changes_found.append("❌ Max selection validation not updated")
        
        # Test 3: Selection limit check
        if "< 5:" in content and "selected_indicators_modal.append" in content:
            changes_found.append("✅ Selection limit check updated to 5")
        else:
            changes_found.append("❌ Selection limit check not updated")
        
        # Test 4: Ensure old limits are removed
        old_limit_patterns = [
            r"up to 3 technical indicators",
            r">= 3 and not is_selected",
            r"< 3:\s*\n.*selected_indicators_modal\.append"
        ]
        
        old_limits_found = []
        for pattern in old_limit_patterns:
            if re.search(pattern, content):
                old_limits_found.append(pattern)
        
        if not old_limits_found:
            changes_found.append("✅ Old 3-indicator limits successfully removed")
        else:
            changes_found.append(f"❌ Old 3-indicator limits still present: {old_limits_found}")
        
        # Print all findings
        for finding in changes_found:
            print(f"   {finding}")
        
        # Overall success
        success_count = sum(1 for finding in changes_found if finding.startswith("✅"))
        total_count = len(changes_found)
        
        print(f"\n   📊 Indicator limit changes: {success_count}/{total_count} successful")
        return success_count == total_count
        
    except Exception as e:
        print(f"❌ Error testing indicator limit changes: {e}")
        return False

def test_error_handling_improvements():
    """Test that error handling has been improved"""
    print("\n🛠️ Testing error handling improvements...")
    
    try:
        with open('dashboard.py', 'r') as f:
            content = f.read()
        
        improvements_found = []
        
        # Test for individual indicator error handling
        if "except Exception as indicator_error:" in content:
            improvements_found.append("✅ Individual indicator error handling added")
        else:
            improvements_found.append("❌ Individual indicator error handling not found")
        
        # Test for column existence checking
        if "column" in content and "does not exist" in content and "run database migration" in content:
            improvements_found.append("✅ Database migration error message added")
        else:
            improvements_found.append("❌ Database migration error message not found")
        
        # Test for success/failure message tracking
        if "successful_indicators" in content and "failed_indicators" in content:
            improvements_found.append("✅ Success/failure tracking implemented")
        else:
            improvements_found.append("❌ Success/failure tracking not implemented")
        
        # Test for user-friendly status messages
        if "st.success" in content and "Loaded indicators:" in content:
            improvements_found.append("✅ Success status messages added")
        else:
            improvements_found.append("❌ Success status messages not found")
        
        if "st.warning" in content and "Failed to load indicators:" in content:
            improvements_found.append("✅ Warning status messages added")
        else:
            improvements_found.append("❌ Warning status messages not found")
        
        # Print all findings
        for finding in improvements_found:
            print(f"   {finding}")
        
        # Overall success
        success_count = sum(1 for finding in improvements_found if finding.startswith("✅"))
        total_count = len(improvements_found)
        
        print(f"\n   🛠️ Error handling improvements: {success_count}/{total_count} successful")
        return success_count == total_count
        
    except Exception as e:
        print(f"❌ Error testing error handling improvements: {e}")
        return False

def test_ema5_integration():
    """Test that EMA-5 is properly integrated in indicator lists"""
    print("\n📈 Testing EMA-5 integration...")
    
    try:
        with open('dashboard.py', 'r') as f:
            content = f.read()
        
        ema5_tests = []
        
        # Test for EMA-5 in available indicators list
        if '"EMA (5)"' in content and '"ema_5"' in content:
            ema5_tests.append("✅ EMA-5 in available indicators list")
        else:
            ema5_tests.append("❌ EMA-5 not found in available indicators list")
        
        # Count EMA-5 occurrences (should be in both lists)
        ema5_display_count = content.count('"EMA (5)"')
        ema5_code_count = content.count('"ema_5"')
        
        if ema5_display_count >= 2 and ema5_code_count >= 2:
            ema5_tests.append(f"✅ EMA-5 found in multiple locations (display: {ema5_display_count}, code: {ema5_code_count})")
        else:
            ema5_tests.append(f"❌ EMA-5 not found in enough locations (display: {ema5_display_count}, code: {ema5_code_count})")
        
        # Print all findings
        for finding in ema5_tests:
            print(f"   {finding}")
        
        # Overall success
        success_count = sum(1 for finding in ema5_tests if finding.startswith("✅"))
        total_count = len(ema5_tests)
        
        print(f"\n   📈 EMA-5 integration: {success_count}/{total_count} successful")
        return success_count == total_count
        
    except Exception as e:
        print(f"❌ Error testing EMA-5 integration: {e}")
        return False

def test_chart_color_support():
    """Test that chart has enough colors for 5 indicators"""
    print("\n🎨 Testing chart color support...")
    
    try:
        with open('dashboard.py', 'r') as f:
            content = f.read()
        
        # Look for the colors array
        colors_pattern = r"colors\s*=\s*\[(.*?)\]"
        match = re.search(colors_pattern, content, re.DOTALL)
        
        if match:
            colors_content = match.group(1)
            # Count color entries
            color_count = len([c for c in colors_content.split(',') if c.strip().strip("'\"").strip()])
            
            if color_count >= 5:
                print(f"   ✅ Chart supports {color_count} colors (sufficient for 5 indicators)")
                return True
            else:
                print(f"   ❌ Chart only supports {color_count} colors (insufficient for 5 indicators)")
                return False
        else:
            print("   ❌ Colors array not found in chart code")
            return False
        
    except Exception as e:
        print(f"❌ Error testing chart color support: {e}")
        return False

def main():
    """Run all indicator fix tests"""
    print("🧪 Testing EMA-5 Display Fix and 5-Indicator Limit")
    print("=" * 60)
    
    tests = [
        ("Dashboard Compilation", test_dashboard_compilation),
        ("Indicator Limit Changes (3→5)", test_indicator_limit_changes),
        ("Error Handling Improvements", test_error_handling_improvements),
        ("EMA-5 Integration", test_ema5_integration),
        ("Chart Color Support", test_chart_color_support),
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
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Indicator fixes are complete.")
        print("\n📋 What was fixed:")
        print("✅ UI limit increased from 3 to 5 technical indicators")
        print("✅ Better error handling with specific EMA-5 guidance")
        print("✅ Success/failure status messages for user feedback")
        print("✅ EMA-5 properly integrated in indicator selections")
        print("✅ Chart supports 5 colors for all indicators")
        print("\n🚀 Next steps:")
        print("1. CRITICAL: Run database migration: psql -d your_db -f add_ema5_indicator.sql")
        print("2. Restart dashboard: streamlit run dashboard.py")
        print("3. Test: Select EMA (5), EMA (12), EMA (26) - all should display")
        print("4. Test: Select up to 5 indicators total")
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)