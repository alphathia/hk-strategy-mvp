"""
HK Strategy Dashboard - Services Layer (Phase 2)

This module provides the services layer for the HK Strategy Dashboard application,
including data fetching, technical analysis, portfolio management, and analysis operations.

Phase 2 Components:
- Data Service (data_service.py) - External data fetching and caching
- Technical Indicators (technical_indicators.py) - Technical analysis calculations  
- Portfolio Service (portfolio_service.py) - Portfolio CRUD operations
- Analysis Service (analysis_service.py) - Portfolio analysis operations

Usage:
    from src.services import DataService, TechnicalIndicators, PortfolioService, AnalysisService
    
    # Or use convenience functions
    from src.services import fetch_hk_price, calculate_rsi, create_portfolio, create_portfolio_analysis
"""

from .data_service import (
    DataService,
    fetch_hk_price,
    fetch_hk_historical_prices,
    get_company_name,
    fetch_and_store_yahoo_data,
    convert_for_database
)

from .technical_indicators import (
    TechnicalIndicators,
    calculate_rsi,
    calculate_rsi_realtime,
    calculate_macd_realtime,
    calculate_ema_realtime
)

from .portfolio_service import (
    PortfolioService,
    get_portfolio_service,
    create_portfolio,
    get_portfolio,
    get_all_portfolios,
    add_position,
    calculate_portfolio_value
)

from .analysis_service import (
    AnalysisService,
    get_analysis_service,
    create_portfolio_analysis,
    get_analysis,
    get_portfolio_analyses,
    compare_analyses,
    calculate_analysis_metrics
)

__version__ = "2.0.0"
__author__ = "HK Strategy Team"

# Module metadata
__all__ = [
    # Service Classes
    'DataService',
    'TechnicalIndicators', 
    'PortfolioService',
    'AnalysisService',
    
    # Service Getters
    'get_portfolio_service',
    'get_analysis_service',
    
    # Data Service Functions
    'fetch_hk_price',
    'fetch_hk_historical_prices',
    'get_company_name',
    'fetch_and_store_yahoo_data',
    'convert_for_database',
    
    # Technical Indicators Functions
    'calculate_rsi',
    'calculate_rsi_realtime',
    'calculate_macd_realtime',
    'calculate_ema_realtime',
    
    # Portfolio Service Functions
    'create_portfolio',
    'get_portfolio',
    'get_all_portfolios',
    'add_position',
    'calculate_portfolio_value',
    
    # Analysis Service Functions
    'create_portfolio_analysis',
    'get_analysis',
    'get_portfolio_analyses',
    'compare_analyses',
    'calculate_analysis_metrics'
]

# Phase tracking for development
PHASE_STATUS = {
    1: "✅ Complete - Core modules (config, state_manager, main)",
    2: "✅ Complete - Services layer (data_service, technical_indicators, portfolio_service, analysis_service)", 
    3: "🚧 Next - Navigation system (router, sidebar)",
    4: "🚧 Planned - Page modules (overview, portfolio, pv_analysis, etc.)",
    5: "🚧 Planned - Component modules (dialogs, charts, tables)"
}

def get_services_info() -> dict:
    """Get information about available services."""
    return {
        'data_service': {
            'description': 'External data fetching and caching',
            'functions': ['fetch_hk_price', 'fetch_hk_historical_prices', 'get_company_name', 'fetch_and_store_yahoo_data'],
            'extracted_from': 'dashboard.py lines 823-1134, 1135-1298'
        },
        'technical_indicators': {
            'description': 'Technical analysis calculations',
            'functions': ['calculate_rsi', 'calculate_macd_realtime', 'calculate_ema_realtime', 'calculate_bollinger_bands'],
            'extracted_from': 'dashboard.py lines 1299-1398'
        },
        'portfolio_service': {
            'description': 'Portfolio CRUD operations',
            'functions': ['create_portfolio', 'get_portfolio', 'add_position', 'calculate_portfolio_value'],
            'wrapper_around': 'portfolio_manager.py'
        },
        'analysis_service': {
            'description': 'Portfolio analysis operations',
            'functions': ['create_portfolio_analysis', 'compare_analyses', 'calculate_analysis_metrics'],
            'wrapper_around': 'portfolio_analysis_manager.py'
        }
    }

def get_phase_status() -> dict:
    """Get current implementation phase status."""
    return PHASE_STATUS

def print_services_summary() -> None:
    """Print summary of available services."""
    print("HK Strategy Dashboard - Services Layer (Phase 2)")
    print("=" * 55)
    
    services_info = get_services_info()
    for service_name, info in services_info.items():
        print(f"\n📦 {service_name.replace('_', ' ').title()}")
        print(f"   Description: {info['description']}")
        print(f"   Functions: {len(info['functions'])} available")
        
        if 'extracted_from' in info:
            print(f"   Extracted from: {info['extracted_from']}")
        if 'wrapper_around' in info:
            print(f"   Wrapper around: {info['wrapper_around']}")
    
    print("\n" + "=" * 55)
    print("Phase Status:")
    for phase, status in PHASE_STATUS.items():
        print(f"Phase {phase}: {status}")
    print("=" * 55)