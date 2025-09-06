"""
Navigation Configuration for HK Strategy Dashboard.
Centralized configuration for navigation structure, routes, and permissions.

Extracted from dashboard.py lines 2155-2184
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

# Setup logging
logger = logging.getLogger(__name__)


class PagePermission(Enum):
    """Page permission levels."""
    PUBLIC = "public"
    USER = "user"
    ADMIN = "admin"


class NavigationConfig:
    """Centralized navigation configuration management."""
    
    def __init__(self):
        """Initialize navigation configuration."""
        self._navigation_structure = self._build_navigation_structure()
        self._page_routes = self._build_page_routes()
        self._section_labels = self._build_section_labels()
        
    def _build_navigation_structure(self) -> Dict[str, Any]:
        """
        Build the hierarchical navigation structure.
        
        Extracted from dashboard.py lines 2156-2184
        """
        return {
            'portfolios': {
                'icon': '📊',
                'label': 'PORTFOLIOS',
                'order': 1,
                'permission': PagePermission.USER,
                'pages': {
                    'overview': {
                        'label': '📋 All Portfolios Overview',
                        'route': 'overview',
                        'permission': PagePermission.USER,
                        'requires_portfolio': False,
                        'description': 'Overview of all portfolios'
                    },
                    'portfolio': {
                        'label': '📊 Portfolio Dashboard', 
                        'route': 'portfolio',
                        'permission': PagePermission.USER,
                        'requires_portfolio': True,
                        'description': 'Individual portfolio management'
                    },
                    'pv_analysis': {
                        'label': '📈 Portfolio Analysis Dashboard',
                        'route': 'pv_analysis',
                        'permission': PagePermission.USER,
                        'requires_portfolio': True,
                        'description': 'Portfolio value analysis and comparison'
                    }
                }
            },
            'strategy': {
                'icon': '🎯', 
                'label': 'STRATEGY ANALYSIS',
                'order': 2,
                'permission': PagePermission.USER,
                'pages': {
                    'equity_analysis': {
                        'label': '📈 Equity Strategy Analysis',
                        'route': 'equity_analysis',
                        'permission': PagePermission.USER,
                        'requires_portfolio': False,
                        'description': 'Individual equity analysis with technical indicators'
                    },
                    'strategy_editor': {
                        'label': '⚙️ Strategy Editor',
                        'route': 'strategy_editor',
                        'permission': PagePermission.USER,
                        'requires_portfolio': False,
                        'description': 'Manage trading strategies and signals'
                    },
                    'strategy_comparison': {
                        'label': '📊 Strategy Comparison',
                        'route': 'strategy_comparison',
                        'permission': PagePermission.USER,
                        'requires_portfolio': False,
                        'description': 'Compare multiple trading strategies'
                    }
                }
            },
            'system': {
                'icon': '🔧',
                'label': 'SYSTEM & ADMIN',
                'order': 3,
                'permission': PagePermission.ADMIN,
                'pages': {
                    'system_status': {
                        'label': '⚙️ System Status',
                        'route': 'system',
                        'permission': PagePermission.USER,
                        'requires_portfolio': False,
                        'description': 'System health and status monitoring'
                    },
                    'database_admin': {
                        'label': '🗄️ Database Management',
                        'route': 'database_admin',
                        'permission': PagePermission.ADMIN,
                        'requires_portfolio': False,
                        'description': 'Database administration tools'
                    },
                    'user_settings': {
                        'label': '👤 User Settings',
                        'route': 'user_settings',
                        'permission': PagePermission.USER,
                        'requires_portfolio': False,
                        'description': 'User preferences and settings'
                    }
                }
            }
        }
    
    def _build_page_routes(self) -> Dict[str, str]:
        """Build mapping of page keys to route names."""
        routes = {}
        for section_key, section_data in self._navigation_structure.items():
            for page_key, page_data in section_data['pages'].items():
                routes[page_key] = page_data['route']
        return routes
    
    def _build_section_labels(self) -> Dict[str, str]:
        """
        Build section labels for breadcrumbs.
        
        Extracted from dashboard.py lines 2603-2607
        """
        return {
            'portfolios': '📊 Portfolios',
            'strategy': '🎯 Strategy Analysis', 
            'system': '🔧 System & Admin'
        }
    
    def get_navigation_structure(self) -> Dict[str, Any]:
        """Get the complete navigation structure."""
        return self._navigation_structure.copy()
    
    def get_section(self, section_key: str) -> Optional[Dict[str, Any]]:
        """Get specific section configuration."""
        return self._navigation_structure.get(section_key)
    
    def get_page_config(self, page_key: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific page."""
        for section_data in self._navigation_structure.values():
            if page_key in section_data['pages']:
                return section_data['pages'][page_key]
        return None
    
    def get_page_route(self, page_key: str) -> Optional[str]:
        """Get route name for a page key."""
        return self._page_routes.get(page_key)
    
    def get_section_label(self, section_key: str) -> str:
        """Get display label for a section."""
        return self._section_labels.get(section_key, section_key.title())
    
    def get_all_pages(self) -> List[str]:
        """Get list of all available page keys."""
        pages = []
        for section_data in self._navigation_structure.values():
            pages.extend(section_data['pages'].keys())
        return pages
    
    def get_pages_by_section(self, section_key: str) -> List[str]:
        """Get list of page keys for a specific section."""
        section = self.get_section(section_key)
        return list(section['pages'].keys()) if section else []
    
    def validate_page_exists(self, page_key: str) -> bool:
        """Validate that a page exists in the navigation structure."""
        return page_key in self._page_routes
    
    def validate_section_exists(self, section_key: str) -> bool:
        """Validate that a section exists in the navigation structure."""
        return section_key in self._navigation_structure
    
    def get_page_section(self, page_key: str) -> Optional[str]:
        """Get the section that contains a specific page."""
        for section_key, section_data in self._navigation_structure.items():
            if page_key in section_data['pages']:
                return section_key
        return None
    
    def get_default_page_for_section(self, section_key: str) -> Optional[str]:
        """Get the default page for a section (first page in order)."""
        section = self.get_section(section_key)
        if section and section['pages']:
            return next(iter(section['pages'].keys()))
        return None
    
    def get_page_permission(self, page_key: str) -> PagePermission:
        """Get permission level required for a page."""
        page_config = self.get_page_config(page_key)
        return page_config.get('permission', PagePermission.USER) if page_config else PagePermission.USER
    
    def check_page_permission(self, page_key: str, user_permission: PagePermission = PagePermission.USER) -> bool:
        """Check if user has permission to access a page."""
        required_permission = self.get_page_permission(page_key)
        
        # Permission hierarchy: PUBLIC < USER < ADMIN
        permission_hierarchy = {
            PagePermission.PUBLIC: 0,
            PagePermission.USER: 1,
            PagePermission.ADMIN: 2
        }
        
        return permission_hierarchy.get(user_permission, 0) >= permission_hierarchy.get(required_permission, 0)
    
    def requires_portfolio(self, page_key: str) -> bool:
        """Check if a page requires a portfolio to be selected."""
        page_config = self.get_page_config(page_key)
        return page_config.get('requires_portfolio', False) if page_config else False
    
    def get_legacy_page_mapping(self) -> Dict[str, str]:
        """
        Get mapping from legacy page names to new page keys.
        For backward compatibility with existing dashboard.py routing.
        """
        return {
            # Legacy routes from dashboard.py
            'system': 'system_status',
            'pv_analysis': 'pv_analysis',
            'equity_analysis': 'equity_analysis', 
            'strategy_editor': 'strategy_editor',
            'strategy_comparison': 'strategy_comparison',
            'overview': 'overview',
            'portfolio': 'portfolio'
        }
    
    def resolve_legacy_page(self, legacy_page: str) -> str:
        """Resolve legacy page name to current page key."""
        mapping = self.get_legacy_page_mapping()
        return mapping.get(legacy_page, legacy_page)
    
    def get_navigation_breadcrumb_config(self) -> Dict[str, Dict[str, str]]:
        """
        Get breadcrumb configuration for navigation.
        
        Extracted logic from dashboard.py lines 2613-2637
        """
        return {
            'portfolios': {
                'overview': '📋 All Portfolios',
                'portfolio': '📊 Portfolio View',
                'pv_analysis': '📈 Portfolio Analysis'
            },
            'strategy': {
                'equity_analysis': '📈 Equity Analysis',
                'strategy_editor': '⚙️ Strategy Editor',
                'strategy_comparison': '📊 Strategy Comparison'
            },
            'system': {
                'system_status': '⚙️ System Status',
                'database_admin': '🗄️ Database Admin',
                'user_settings': '👤 User Settings'
            }
        }
    
    def get_ordered_sections(self) -> List[Tuple[str, Dict[str, Any]]]:
        """Get sections ordered by their configured order."""
        sections = [(key, data) for key, data in self._navigation_structure.items()]
        return sorted(sections, key=lambda x: x[1].get('order', 999))


# Global configuration instance
_config_instance = None

def get_navigation_config() -> NavigationConfig:
    """Get global navigation configuration instance (singleton)."""
    global _config_instance
    if _config_instance is None:
        _config_instance = NavigationConfig()
    return _config_instance

def get_navigation_structure() -> Dict[str, Any]:
    """Get the complete navigation structure."""
    return get_navigation_config().get_navigation_structure()

def get_page_config(page_key: str) -> Optional[Dict[str, Any]]:
    """Get configuration for a specific page."""
    return get_navigation_config().get_page_config(page_key)

def validate_page_exists(page_key: str) -> bool:
    """Validate that a page exists in the navigation structure."""
    return get_navigation_config().validate_page_exists(page_key)

def get_page_section(page_key: str) -> Optional[str]:
    """Get the section that contains a specific page."""
    return get_navigation_config().get_page_section(page_key)