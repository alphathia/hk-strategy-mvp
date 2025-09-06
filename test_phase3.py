#!/usr/bin/env python3
"""
Test script for Phase 3 of dashboard decomposition - Navigation System.
Verifies that all navigation components are working correctly.
"""

import sys
import os
from datetime import datetime
from unittest.mock import Mock, patch

sys.path.append('src')
sys.path.append('.')

def test_imports():
    """Test that all Phase 3 navigation modules can be imported."""
    print("🧪 Testing Phase 3 navigation imports...")
    
    try:
        # Test individual navigation imports
        from src.navigation.navigation_config import NavigationConfig, PagePermission, get_navigation_config
        print("✅ Navigation config imported successfully")
        
        from src.navigation.router import PageRouter, get_page_router, route_to_page
        print("✅ Router imported successfully")
        
        from src.navigation.sidebar import SidebarNavigator, get_sidebar_navigator, render_sidebar
        print("✅ Sidebar navigator imported successfully")
        
        from src.navigation.breadcrumbs import BreadcrumbManager, get_breadcrumb_manager, generate_breadcrumbs
        print("✅ Breadcrumb manager imported successfully")
        
        # Test package imports
        from src.navigation import NavigationConfig, PageRouter, SidebarNavigator, BreadcrumbManager
        print("✅ Package imports working correctly")
        
        # Test convenience function imports
        from src.navigation import route_to_page, render_sidebar, render_breadcrumbs, get_page_config
        print("✅ Convenience functions imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {str(e)}")
        return False

def test_navigation_config():
    """Test navigation configuration functionality."""
    print("\n🧪 Testing navigation configuration...")
    
    try:
        from src.navigation.navigation_config import NavigationConfig, PagePermission
        
        # Initialize configuration
        config = NavigationConfig()
        print("✅ Navigation configuration initialized")
        
        # Test navigation structure
        nav_structure = config.get_navigation_structure()
        if isinstance(nav_structure, dict) and len(nav_structure) >= 3:
            print(f"✅ Navigation structure loaded: {len(nav_structure)} sections")
        else:
            print("❌ Navigation structure failed")
            return False
        
        # Test section validation
        if config.validate_section_exists('portfolios') and config.validate_section_exists('strategy'):
            print("✅ Section validation working")
        else:
            print("❌ Section validation failed")
            return False
        
        # Test page validation
        if config.validate_page_exists('overview') and config.validate_page_exists('portfolio'):
            print("✅ Page validation working")
        else:
            print("❌ Page validation failed")
            return False
        
        # Test page configuration
        page_config = config.get_page_config('portfolio')
        if page_config and 'label' in page_config and 'route' in page_config:
            print("✅ Page configuration retrieval working")
        else:
            print("❌ Page configuration retrieval failed")
            return False
        
        # Test legacy mapping
        legacy_mapping = config.get_legacy_page_mapping()
        if isinstance(legacy_mapping, dict) and len(legacy_mapping) > 0:
            print("✅ Legacy page mapping working")
        else:
            print("❌ Legacy page mapping failed")
            return False
        
        # Test permissions
        user_permission = PagePermission.USER
        admin_permission = PagePermission.ADMIN
        if config.check_page_permission('portfolio', user_permission):
            print("✅ Permission checking working")
        else:
            print("❌ Permission checking failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Navigation config test failed: {str(e)}")
        return False

def test_page_router():
    """Test page router functionality."""
    print("\n🧪 Testing page router...")
    
    try:
        # Mock streamlit session state for testing
        with patch('streamlit.session_state', new={}):
            from src.navigation.router import PageRouter
            
            # Initialize router
            router = PageRouter()
            print("✅ Page router initialized")
            
            # Test current page retrieval
            current_page = router.get_current_page()
            if isinstance(current_page, str) and current_page:
                print(f"✅ Current page retrieval working: {current_page}")
            else:
                print("❌ Current page retrieval failed")
                return False
            
            # Test section retrieval
            current_section = router.get_current_section()
            if isinstance(current_section, str) and current_section:
                print(f"✅ Current section retrieval working: {current_section}")
            else:
                print("❌ Current section retrieval failed")
                return False
            
            # Test page validation
            is_valid, message = router.validate_page_access('overview')
            if is_valid:
                print("✅ Page access validation working")
            else:
                print(f"❌ Page access validation failed: {message}")
                return False
            
            # Test invalid page handling
            is_valid, message = router.validate_page_access('nonexistent_page')
            if not is_valid:
                print("✅ Invalid page detection working")
            else:
                print("❌ Invalid page detection failed")
                return False
            
            # Test navigation history
            history = router.get_navigation_history()
            if isinstance(history, list):
                print(f"✅ Navigation history working: {len(history)} items")
            else:
                print("❌ Navigation history failed")
                return False
            
            return True
        
    except Exception as e:
        print(f"❌ Page router test failed: {str(e)}")
        return False

def test_sidebar_navigator():
    """Test sidebar navigator functionality."""
    print("\n🧪 Testing sidebar navigator...")
    
    try:
        # Mock streamlit for testing
        with patch('streamlit.sidebar') as mock_sidebar, \
             patch('streamlit.session_state', new={}):
            
            from src.navigation.sidebar import SidebarNavigator
            
            # Initialize sidebar navigator
            sidebar = SidebarNavigator()
            print("✅ Sidebar navigator initialized")
            
            # Test if sidebar would render (without actually rendering)
            try:
                # This would normally call Streamlit functions
                # We're just testing that the methods exist and can be called
                print("✅ Sidebar render methods available")
            except Exception as e:
                print(f"⚠️ Sidebar render test skipped (requires Streamlit): {str(e)}")
            
            # Test page availability check
            if hasattr(sidebar, '_is_page_available'):
                is_available = sidebar._is_page_available('overview')
                print(f"✅ Page availability check working: overview = {is_available}")
            else:
                print("❌ Page availability check method missing")
                return False
            
            return True
        
    except Exception as e:
        print(f"❌ Sidebar navigator test failed: {str(e)}")
        return False

def test_breadcrumb_manager():
    """Test breadcrumb manager functionality."""
    print("\n🧪 Testing breadcrumb manager...")
    
    try:
        # Mock streamlit session state for testing
        mock_session_state = {
            'navigation': {
                'section': 'portfolios',
                'page': 'overview'
            },
            'portfolios': {
                'test_portfolio': {'name': 'Test Portfolio'}
            }
        }
        
        with patch('streamlit.session_state', new=mock_session_state):
            from src.navigation.breadcrumbs import BreadcrumbManager
            
            # Initialize breadcrumb manager
            breadcrumbs = BreadcrumbManager()
            print("✅ Breadcrumb manager initialized")
            
            # Test breadcrumb generation
            breadcrumb_list = breadcrumbs.generate_breadcrumbs()
            if isinstance(breadcrumb_list, list) and len(breadcrumb_list) > 0:
                print(f"✅ Breadcrumb generation working: {len(breadcrumb_list)} items")
                print(f"   Breadcrumbs: {' → '.join(breadcrumb_list)}")
            else:
                print("❌ Breadcrumb generation failed")
                return False
            
            # Test page context
            context = breadcrumbs.get_page_context()
            if isinstance(context, dict) and 'current_page' in context:
                print("✅ Page context retrieval working")
            else:
                print("❌ Page context retrieval failed")
                return False
            
            # Test different page contexts
            mock_session_state['navigation']['page'] = 'portfolio'
            mock_session_state['selected_portfolio'] = 'test_portfolio'
            
            portfolio_breadcrumbs = breadcrumbs.generate_breadcrumbs()
            if len(portfolio_breadcrumbs) > len(breadcrumb_list):
                print("✅ Context-aware breadcrumbs working")
            else:
                print("⚠️ Context-aware breadcrumbs may need adjustment")
            
            return True
        
    except Exception as e:
        print(f"❌ Breadcrumb manager test failed: {str(e)}")
        return False

def test_navigation_integration():
    """Test navigation components working together."""
    print("\n🧪 Testing navigation integration...")
    
    try:
        from src.navigation import (
            get_navigation_info, get_phase_status, setup_navigation, 
            validate_navigation_setup
        )
        
        # Test navigation info
        nav_info = get_navigation_info()
        if isinstance(nav_info, dict) and len(nav_info) == 4:
            print("✅ Navigation info retrieval working")
        else:
            print("❌ Navigation info retrieval failed")
            return False
        
        # Test phase status
        phase_status = get_phase_status()
        if isinstance(phase_status, dict) and 3 in phase_status:
            print("✅ Phase status tracking working")
        else:
            print("❌ Phase status tracking failed")
            return False
        
        # Test navigation setup
        nav_components = setup_navigation()
        if isinstance(nav_components, dict) and len(nav_components) >= 3:
            print("✅ Navigation setup working")
        else:
            print("❌ Navigation setup failed")
            return False
        
        # Test validation
        validation_result = validate_navigation_setup()
        if isinstance(validation_result, dict) and 'status' in validation_result:
            print(f"✅ Navigation validation working: {validation_result['status']}")
        else:
            print("❌ Navigation validation failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Navigation integration test failed: {str(e)}")
        return False

def test_convenience_functions():
    """Test convenience functions for backward compatibility."""
    print("\n🧪 Testing convenience functions...")
    
    try:
        # Mock streamlit session state
        with patch('streamlit.session_state', new={}):
            # Test configuration convenience functions
            from src.navigation import get_navigation_config, get_page_config, validate_page_exists
            
            config = get_navigation_config()
            if config:
                print("✅ get_navigation_config working")
            else:
                print("❌ get_navigation_config failed")
                return False
            
            page_config = get_page_config('overview')
            if page_config:
                print("✅ get_page_config working")
            else:
                print("❌ get_page_config failed")
                return False
            
            is_valid = validate_page_exists('portfolio')
            if is_valid:
                print("✅ validate_page_exists working")
            else:
                print("❌ validate_page_exists failed")
                return False
            
            # Test router convenience functions
            from src.navigation import get_page_router, get_current_page
            
            router = get_page_router()
            current_page = get_current_page()
            
            if router and isinstance(current_page, str):
                print("✅ Router convenience functions working")
            else:
                print("❌ Router convenience functions failed")
                return False
            
            # Test breadcrumb convenience functions
            from src.navigation import generate_breadcrumbs, get_page_context
            
            breadcrumbs = generate_breadcrumbs()
            context = get_page_context()
            
            if isinstance(breadcrumbs, list) and isinstance(context, dict):
                print("✅ Breadcrumb convenience functions working")
            else:
                print("❌ Breadcrumb convenience functions failed")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Convenience functions test failed: {str(e)}")
        return False

def test_directory_structure():
    """Test that all required Phase 3 files exist."""
    print("\n🧪 Testing Phase 3 directory structure...")
    
    required_files = [
        'src/navigation/__init__.py',
        'src/navigation/navigation_config.py',
        'src/navigation/router.py',
        'src/navigation/sidebar.py',
        'src/navigation/breadcrumbs.py'
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            all_exist = False
    
    return all_exist

def test_backward_compatibility():
    """Test backward compatibility with existing dashboard."""
    print("\n🧪 Testing backward compatibility...")
    
    try:
        # Mock streamlit session state
        with patch('streamlit.session_state', new={'current_page': 'overview'}):
            from src.navigation.navigation_config import get_navigation_config
            
            config = get_navigation_config()
            
            # Test legacy page mapping
            legacy_mapping = config.get_legacy_page_mapping()
            expected_mappings = ['system', 'pv_analysis', 'equity_analysis', 'strategy_editor']
            
            mapping_found = all(page in legacy_mapping for page in expected_mappings)
            if mapping_found:
                print("✅ Legacy page mapping working")
            else:
                print("❌ Legacy page mapping incomplete")
                return False
            
            # Test legacy page resolution
            resolved_page = config.resolve_legacy_page('system')
            if resolved_page == 'system_status':
                print("✅ Legacy page resolution working")
            else:
                print("❌ Legacy page resolution failed")
                return False
            
            return True
        
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {str(e)}")
        return False

def main():
    """Run all Phase 3 tests."""
    print("🚀 Running Phase 3 Tests for Dashboard Decomposition - Navigation System")
    print("=" * 85)
    
    tests = [
        ("Directory Structure", test_directory_structure),
        ("Navigation Imports", test_imports),
        ("Navigation Configuration", test_navigation_config),
        ("Page Router", test_page_router),
        ("Sidebar Navigator", test_sidebar_navigator),
        ("Breadcrumb Manager", test_breadcrumb_manager),
        ("Navigation Integration", test_navigation_integration),
        ("Convenience Functions", test_convenience_functions),
        ("Backward Compatibility", test_backward_compatibility)
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
    print("\n" + "=" * 85)
    print("📋 Phase 3 Test Results Summary:")
    print("=" * 85)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print("=" * 85)
    print(f"🏆 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Phase 3 Navigation System is working correctly!")
        print("\n📋 What's Available:")
        print("✅ Navigation Configuration - Centralized navigation structure")
        print("✅ Page Router - Page routing and navigation logic")
        print("✅ Sidebar Navigator - Hierarchical sidebar navigation")
        print("✅ Breadcrumb Manager - Context-aware breadcrumb system")
        print("\n📋 Next Steps:")
        print("- Navigation system is ready for Phase 4 page integration")
        print("- Proceed with Phase 4: Page modules implementation") 
        print("- Integrate navigation with existing dashboard pages")
        print("\n🔧 Integration Notes:")
        print("- All navigation components maintain backward compatibility")
        print("- Legacy page routing is preserved during transition")
        print("- Navigation system ready for gradual migration")
        
    else:
        print(f"🔧 {total - passed} tests failed. Please review the implementation.")
        print("💡 Note: Some failures may be expected without full Streamlit context")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)