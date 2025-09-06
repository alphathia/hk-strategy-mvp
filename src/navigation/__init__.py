"""
HK Strategy Dashboard - Navigation System (Phase 3)

This module provides the navigation system for the HK Strategy Dashboard application,
including page routing, sidebar navigation, breadcrumb management, and navigation configuration.

Phase 3 Components:
- Navigation Configuration (navigation_config.py) - Centralized navigation structure
- Page Router (router.py) - Page routing and navigation logic
- Sidebar Navigator (sidebar.py) - Sidebar navigation component
- Breadcrumb Manager (breadcrumbs.py) - Breadcrumb navigation system

Usage:
    from src.navigation import PageRouter, SidebarNavigator, BreadcrumbManager
    from src.navigation import route_to_page, render_sidebar, render_breadcrumbs
"""

from .navigation_config import (
    NavigationConfig,
    PagePermission,
    get_navigation_config,
    get_navigation_structure,
    get_page_config,
    validate_page_exists,
    get_page_section
)

from .router import (
    PageRouter,
    get_page_router,
    route_to_page,
    get_current_page,
    validate_page_access,
    handle_page_not_found,
    register_page_handler,
    render_current_page
)

from .sidebar import (
    SidebarNavigator,
    get_sidebar_navigator,
    render_sidebar,
    create_navigation_buttons,
    show_page_context,
    handle_sidebar_actions
)

from .breadcrumbs import (
    BreadcrumbManager,
    get_breadcrumb_manager,
    generate_breadcrumbs,
    render_breadcrumbs,
    get_page_context,
    update_breadcrumb_trail
)

__version__ = "3.0.0"
__author__ = "HK Strategy Team"

# Module metadata
__all__ = [
    # Configuration Classes
    'NavigationConfig',
    'PagePermission',
    
    # Service Classes
    'PageRouter',
    'SidebarNavigator', 
    'BreadcrumbManager',
    
    # Service Getters
    'get_navigation_config',
    'get_page_router',
    'get_sidebar_navigator',
    'get_breadcrumb_manager',
    
    # Configuration Functions
    'get_navigation_structure',
    'get_page_config',
    'validate_page_exists',
    'get_page_section',
    
    # Router Functions
    'route_to_page',
    'get_current_page',
    'validate_page_access',
    'handle_page_not_found',
    'register_page_handler',
    'render_current_page',
    
    # Sidebar Functions
    'render_sidebar',
    'create_navigation_buttons',
    'show_page_context',
    'handle_sidebar_actions',
    
    # Breadcrumb Functions
    'generate_breadcrumbs',
    'render_breadcrumbs',
    'get_page_context',
    'update_breadcrumb_trail'
]

# Phase tracking for development
PHASE_STATUS = {
    1: "✅ Complete - Core modules (config, state_manager, main)",
    2: "✅ Complete - Services layer (data_service, technical_indicators, portfolio_service, analysis_service)",
    3: "✅ Complete - Navigation system (router, sidebar, breadcrumbs, navigation_config)", 
    4: "🚧 Next - Page modules (overview, portfolio, pv_analysis, etc.)",
    5: "🚧 Planned - Component modules (dialogs, charts, tables)"
}

def get_navigation_info() -> dict:
    """Get information about available navigation components."""
    return {
        'navigation_config': {
            'description': 'Centralized navigation structure and configuration',
            'features': ['Hierarchical menu structure', 'Page permissions', 'Route mappings', 'Legacy compatibility'],
            'extracted_from': 'dashboard.py lines 2155-2184'
        },
        'router': {
            'description': 'Page routing and navigation logic',
            'features': ['Page navigation', 'Route validation', 'Access control', 'State management'],
            'extracted_from': 'dashboard.py routing logic'
        },
        'sidebar': {
            'description': 'Sidebar navigation component',
            'features': ['Hierarchical navigation', 'Portfolio selector', 'System status', 'Dynamic rendering'],
            'extracted_from': 'dashboard.py lines 2186-2242'
        },
        'breadcrumbs': {
            'description': 'Breadcrumb navigation system',
            'features': ['Context-aware breadcrumbs', 'Portfolio integration', 'Analysis context', 'Multiple render styles'],
            'extracted_from': 'dashboard.py lines 2600-2645'
        }
    }

def get_phase_status() -> dict:
    """Get current implementation phase status."""
    return PHASE_STATUS

def print_navigation_summary() -> None:
    """Print summary of available navigation components."""
    print("HK Strategy Dashboard - Navigation System (Phase 3)")
    print("=" * 60)
    
    nav_info = get_navigation_info()
    for component_name, info in nav_info.items():
        print(f"\n🧭 {component_name.replace('_', ' ').title()}")
        print(f"   Description: {info['description']}")
        print(f"   Features: {len(info['features'])} available")
        
        if 'extracted_from' in info:
            print(f"   Extracted from: {info['extracted_from']}")
    
    print("\n" + "=" * 60)
    print("Phase Status:")
    for phase, status in PHASE_STATUS.items():
        print(f"Phase {phase}: {status}")
    print("=" * 60)

def get_navigation_demo_functions() -> dict:
    """Get demonstration functions for navigation system."""
    return {
        'basic_navigation': """
# Basic Navigation Usage
from src.navigation import route_to_page, get_current_page

# Navigate to a page
success = route_to_page('portfolio')

# Get current page
current = get_current_page()
        """,
        
        'sidebar_rendering': """
# Sidebar Navigation
from src.navigation import render_sidebar, show_page_context

# Render complete sidebar
render_sidebar()

# Show page context
show_page_context()
        """,
        
        'breadcrumb_usage': """
# Breadcrumb Navigation
from src.navigation import render_breadcrumbs, generate_breadcrumbs

# Render breadcrumbs
render_breadcrumbs(style="default")

# Get breadcrumb data
breadcrumbs = generate_breadcrumbs()
        """,
        
        'configuration_access': """
# Navigation Configuration
from src.navigation import get_navigation_config, get_page_config

# Get navigation structure
config = get_navigation_config()
nav_structure = config.get_navigation_structure()

# Get page configuration
page_config = get_page_config('portfolio')
        """
    }

# Navigation system integration helpers
class NavigationIntegration:
    """Helper class for integrating navigation system with existing dashboard."""
    
    @staticmethod
    def setup_navigation():
        """Setup navigation system for existing dashboard."""
        # Initialize navigation components
        router = get_page_router()
        sidebar = get_sidebar_navigator() 
        breadcrumbs = get_breadcrumb_manager()
        
        return {
            'router': router,
            'sidebar': sidebar,
            'breadcrumbs': breadcrumbs
        }
    
    @staticmethod
    def migrate_legacy_routing():
        """Migrate legacy routing to new navigation system.""" 
        config = get_navigation_config()
        mapping = config.get_legacy_page_mapping()
        
        return mapping
    
    @staticmethod
    def validate_navigation_setup():
        """Validate navigation system setup."""
        try:
            # Test navigation components
            config = get_navigation_config()
            router = get_page_router()
            sidebar = get_sidebar_navigator()
            breadcrumbs = get_breadcrumb_manager()
            
            # Basic validation
            nav_structure = config.get_navigation_structure()
            current_page = router.get_current_page()
            breadcrumb_list = breadcrumbs.generate_breadcrumbs()
            
            return {
                'status': 'success',
                'components': ['config', 'router', 'sidebar', 'breadcrumbs'],
                'navigation_sections': len(nav_structure),
                'current_page': current_page,
                'breadcrumbs': len(breadcrumb_list)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

def setup_navigation():
    """Setup navigation system for existing dashboard."""
    return NavigationIntegration.setup_navigation()

def validate_navigation_setup():
    """Validate navigation system setup."""
    return NavigationIntegration.validate_navigation_setup()