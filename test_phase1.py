#!/usr/bin/env python3
"""
Test script for Phase 1 of dashboard decomposition.
Verifies that all core modules are working correctly.
"""

import sys
import os
sys.path.append('src')
sys.path.append('.')

def test_imports():
    """Test that all Phase 1 modules can be imported."""
    print("🧪 Testing Phase 1 imports...")
    
    try:
        # Test config module
        from src.dashboard.config import get_config, validate_environment, setup_logging
        print("✅ Config module imported successfully")
        
        # Test state manager module  
        from src.dashboard.state_manager import SessionStateManager
        print("✅ State manager module imported successfully")
        
        # Test main module
        from src.dashboard.main import DashboardApp
        print("✅ Main module imported successfully")
        
        # Test package imports
        from src.dashboard import get_config, SessionStateManager, DashboardApp
        print("✅ Package imports working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {str(e)}")
        return False

def test_config():
    """Test configuration management."""
    print("\n🧪 Testing configuration management...")
    
    try:
        from src.dashboard.config import get_config
        
        config = get_config()
        
        # Test basic config sections
        app_config = config.get('app')
        db_config = config.get('database') 
        cache_config = config.get('cache')
        
        print(f"✅ App config loaded: {app_config['page_title']}")
        print(f"✅ Database config loaded: {db_config['host']}:{db_config['port']}")
        print(f"✅ Cache config loaded: TTL={cache_config['price_data_ttl']}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {str(e)}")
        return False

def test_phase_status():
    """Test phase status tracking."""
    print("\n🧪 Testing phase status tracking...")
    
    try:
        from src.dashboard import get_phase_status, print_phase_status
        
        status = get_phase_status()
        print(f"✅ Phase status retrieved: {len(status)} phases tracked")
        
        print("\n📊 Current Phase Status:")
        print_phase_status()
        
        return True
        
    except Exception as e:
        print(f"❌ Phase status test failed: {str(e)}")
        return False

def test_directory_structure():
    """Test that all required files exist."""
    print("\n🧪 Testing directory structure...")
    
    required_files = [
        'src/dashboard/__init__.py',
        'src/dashboard/config.py', 
        'src/dashboard/state_manager.py',
        'src/dashboard/main.py'
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            all_exist = False
    
    return all_exist

def main():
    """Run all Phase 1 tests."""
    print("🚀 Running Phase 1 Tests for Dashboard Decomposition")
    print("=" * 60)
    
    tests = [
        ("Directory Structure", test_directory_structure),
        ("Module Imports", test_imports),
        ("Configuration Management", test_config), 
        ("Phase Status Tracking", test_phase_status)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Results Summary:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print("=" * 60)
    print(f"🏆 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Phase 1 implementation is working correctly!")
        print("\n📋 Next Steps:")
        print("- Run: streamlit run src/dashboard/main.py")
        print("- Proceed with Phase 2: Services layer implementation")
    else:
        print("🔧 Some tests failed. Please review the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)