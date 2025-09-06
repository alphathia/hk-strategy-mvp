"""
HK Strategy Dashboard - Core Module

This module provides the core components for the HK Strategy Dashboard application,
including configuration management, session state handling, and the main application entry point.

Phase 1 Components:
- Configuration Management (config.py)
- Session State Management (state_manager.py) 
- Main Application Entry Point (main.py)

Usage:
    from src.dashboard import DashboardApp
    from src.dashboard.config import get_config
    from src.dashboard.state_manager import SessionStateManager
    
    # Run the application
    app = DashboardApp()
    app.run()
"""

from .config import (
    get_config,
    load_config, 
    get_database_config,
    get_redis_config,
    get_chart_config,
    validate_environment,
    setup_logging
)

from .state_manager import (
    SessionStateManager,
    init_session_state,
    clear_modal_states,
    reset_portfolio_state,
    get_current_portfolio,
    set_current_page,
    get_navigation_state,
    cache_price_data,
    get_cached_price_data
)

from .main import DashboardApp, main

__version__ = "1.0.0"
__author__ = "HK Strategy Team"

# Module metadata
__all__ = [
    # Configuration
    'get_config',
    'load_config',
    'get_database_config', 
    'get_redis_config',
    'get_chart_config',
    'validate_environment',
    'setup_logging',
    
    # State Management
    'SessionStateManager',
    'init_session_state',
    'clear_modal_states', 
    'reset_portfolio_state',
    'get_current_portfolio',
    'set_current_page',
    'get_navigation_state',
    'cache_price_data',
    'get_cached_price_data',
    
    # Main Application
    'DashboardApp',
    'main'
]

# Phase tracking for development
PHASE_STATUS = {
    1: "✅ Complete - Core modules (config, state_manager, main)",
    2: "✅ Complete - Services layer (data_service, technical_indicators, portfolio_service, analysis_service)", 
    3: "✅ Complete - Navigation system (router, sidebar, breadcrumbs, navigation_config)",
    4: "🚧 Next - Page modules (overview, portfolio, pv_analysis, etc.)",
    5: "🚧 Planned - Component modules (dialogs, charts, tables)"
}

def get_phase_status() -> dict:
    """Get current implementation phase status."""
    return PHASE_STATUS

def print_phase_status() -> None:
    """Print current implementation phase status."""
    print("HK Strategy Dashboard - Implementation Status:")
    print("=" * 50)
    for phase, status in PHASE_STATUS.items():
        print(f"Phase {phase}: {status}")
    print("=" * 50)