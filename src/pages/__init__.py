"""
Pages Package for HK Strategy Dashboard.

This package contains all page modules for the modular dashboard architecture.
Each page inherits from BasePage and provides specific functionality.

Phase 4 - Page Modules Implementation
Extracted from monolithic dashboard.py (6000+ lines) into modular components.
"""

from .base_page import BasePage

# Import all page classes
from .overview_page import OverviewPage
from .portfolio_page import PortfolioPage
from .pv_analysis_page import PVAnalysisPage
from .equity_analysis_page import EquityAnalysisPage
from .strategy_editor_page import StrategyEditorPage
from .strategy_comparison_page import StrategyComparisonPage
from .system_status_page import SystemStatusPage
from .database_admin_page import DatabaseAdminPage
from .user_settings_page import UserSettingsPage

# Page registry mapping page keys to classes
PAGE_REGISTRY = {
    # Portfolio section
    'overview': OverviewPage,
    'portfolio': PortfolioPage, 
    'pv_analysis': PVAnalysisPage,
    
    # Strategy section
    'equity_analysis': EquityAnalysisPage,
    'strategy_editor': StrategyEditorPage,
    'strategy_comparison': StrategyComparisonPage,
    
    # System section
    'system_status': SystemStatusPage,
    'database_admin': DatabaseAdminPage,
    'user_settings': UserSettingsPage
}

# Import page manager
from .page_manager import (
    PageManager, get_page_manager, render_current_page, 
    navigate_to_page, clear_page_cache
)

# Export all page classes, registry, and manager
__all__ = [
    'BasePage',
    'OverviewPage',
    'PortfolioPage', 
    'PVAnalysisPage',
    'EquityAnalysisPage',
    'StrategyEditorPage',
    'StrategyComparisonPage',
    'SystemStatusPage',
    'DatabaseAdminPage',
    'UserSettingsPage',
    'PAGE_REGISTRY',
    'PageManager',
    'get_page_manager',
    'render_current_page',
    'navigate_to_page',
    'clear_page_cache'
]


def get_page_class(page_key: str):
    """
    Get page class by page key.
    
    Args:
        page_key: The page key from navigation configuration
        
    Returns:
        Page class or None if not found
    """
    return PAGE_REGISTRY.get(page_key)


def create_page_instance(page_key: str):
    """
    Create page instance by page key.
    
    Args:
        page_key: The page key from navigation configuration
        
    Returns:
        Page instance or None if page not found
    """
    page_class = get_page_class(page_key)
    return page_class() if page_class else None


def get_available_pages():
    """
    Get list of all available page keys.
    
    Returns:
        List of page keys
    """
    return list(PAGE_REGISTRY.keys())


def validate_page_key(page_key: str) -> bool:
    """
    Validate that a page key exists in the registry.
    
    Args:
        page_key: The page key to validate
        
    Returns:
        True if page exists, False otherwise
    """
    return page_key in PAGE_REGISTRY