"""
Session State Management for the HK Strategy Dashboard.
Centralized management of Streamlit session state variables.
"""

import streamlit as st
import copy
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List
from portfolio_manager import get_portfolio_manager
import sys
import os

# Add src to path for imports
sys.path.append('src')
try:
    from src.database import DatabaseManager
    from src.analysis_manager import AnalysisManager
except ImportError:
    from database import DatabaseManager
    from analysis_manager import AnalysisManager


class SessionStateManager:
    """Manages Streamlit session state initialization and cleanup."""
    
    @staticmethod
    def init_session_state() -> None:
        """Initialize all session state variables with defaults."""
        # Core portfolio management
        SessionStateManager._init_portfolio_state()
        
        # Navigation and UI state
        SessionStateManager._init_navigation_state()
        
        # Analysis and database connections
        SessionStateManager._init_analysis_state()
        
        # Technical indicators and charts
        SessionStateManager._init_indicators_state()
        
        # Modal and form states
        SessionStateManager._init_modal_states()
        
        # Cache management
        SessionStateManager._init_cache_state()
    
    @staticmethod
    def _init_portfolio_state() -> None:
        """Initialize portfolio-related session state variables."""
        if 'portfolios' not in st.session_state:
            try:
                # Load portfolios from database
                portfolio_manager = get_portfolio_manager()
                st.session_state.portfolios = portfolio_manager.get_all_portfolios()
                
                # Debug info
                if st.session_state.portfolios:
                    st.success(f"✅ Loaded {len(st.session_state.portfolios)} portfolios from database")
                else:
                    st.warning("⚠️ No portfolios loaded - database might be empty")
                    
            except Exception as e:
                st.error(f"❌ Failed to initialize portfolios: {str(e)}")
                # Fallback to empty dict to prevent crashes
                st.session_state.portfolios = {}
        
        if 'portfolio_manager' not in st.session_state:
            st.session_state.portfolio_manager = get_portfolio_manager()
        
        if 'selected_portfolio' not in st.session_state:
            st.session_state.selected_portfolio = None
        
        if 'selected_portfolio_for_pv' not in st.session_state:
            st.session_state.selected_portfolio_for_pv = None
        
        if 'current_portfolio_selection' not in st.session_state:
            st.session_state.current_portfolio_selection = None
        
        if 'portfolio_switch_request' not in st.session_state:
            st.session_state.portfolio_switch_request = None
        
        # Portfolio editing states
        if 'edit_mode' not in st.session_state:
            st.session_state.edit_mode = {}
        
        if 'portfolio_backup' not in st.session_state:
            st.session_state.portfolio_backup = {}
        
        if 'pending_changes' not in st.session_state:
            st.session_state.pending_changes = {}
        
        if 'last_save_status' not in st.session_state:
            st.session_state.last_save_status = {}
        
        if 'portfolio_timestamps' not in st.session_state:
            st.session_state.portfolio_timestamps = {}
    
    @staticmethod
    def _init_navigation_state() -> None:
        """Initialize navigation-related session state variables."""
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'overview'  # Start with overview by default
        
        if 'navigation' not in st.session_state:
            st.session_state.navigation = {
                'section': 'overview',
                'page': 'overview',
                'breadcrumbs': []
            }
    
    @staticmethod
    def _init_analysis_state() -> None:
        """Initialize analysis and database connection state variables."""
        if 'db_manager' not in st.session_state:
            st.session_state.db_manager = DatabaseManager()
        
        if 'analysis_manager' not in st.session_state:
            st.session_state.analysis_manager = AnalysisManager(st.session_state.db_manager)
        
        if 'current_analysis' not in st.session_state:
            st.session_state.current_analysis = None
        
        if 'selected_for_compare' not in st.session_state:
            st.session_state.selected_for_compare = []
        
        if 'selected_analysis_date' not in st.session_state:
            st.session_state.selected_analysis_date = None
        
        if 'selected_analysis_id' not in st.session_state:
            st.session_state.selected_analysis_id = None
        
        # Equity analysis specific
        if 'equity_context' not in st.session_state:
            st.session_state.equity_context = {}
        
        if 'equity_portfolio_id' not in st.session_state:
            st.session_state.equity_portfolio_id = None
        
        if 'equity_symbol' not in st.session_state:
            st.session_state.equity_symbol = None
        
        if 'equity_start_date' not in st.session_state:
            st.session_state.equity_start_date = (date.today() - timedelta(days=180)).strftime('%Y-%m-%d')
        
        if 'equity_end_date' not in st.session_state:
            st.session_state.equity_end_date = date.today().strftime('%Y-%m-%d')
    
    @staticmethod
    def _init_indicators_state() -> None:
        """Initialize technical indicators session state variables."""
        if 'selected_indicators_modal' not in st.session_state:
            st.session_state.selected_indicators_modal = []
        
        if 'confirmed_indicators' not in st.session_state:
            st.session_state.confirmed_indicators = []
        
        if 'show_indicators_clicked' not in st.session_state:
            st.session_state.show_indicators_clicked = False
    
    @staticmethod
    def _init_modal_states() -> None:
        """Initialize modal dialog session state variables."""
        modal_flags = [
            'show_create_portfolio_dialog',
            'show_copy_portfolio_dialog', 
            'show_add_symbol_dialog',
            'show_update_position_dialog',
            'show_create_analysis_dialog',
            'show_detail_modal',
            'show_transaction_modal',
            'delete_confirm_id'
        ]
        
        for flag in modal_flags:
            if flag not in st.session_state:
                st.session_state[flag] = False
    
    @staticmethod
    def _init_cache_state() -> None:
        """Initialize caching session state variables."""
        if 'portfolio_prices' not in st.session_state:
            st.session_state.portfolio_prices = {}
        
        if 'fetch_details' not in st.session_state:
            st.session_state.fetch_details = {}
        
        if 'last_update' not in st.session_state:
            st.session_state.last_update = {}
        
        if 'price_data_cache' not in st.session_state:
            st.session_state.price_data_cache = {}
        
        if 'cache_expiry' not in st.session_state:
            st.session_state.cache_expiry = {}
    
    @staticmethod
    def clear_modal_states() -> None:
        """Clear all modal dialog states."""
        modal_flags = [
            'show_create_portfolio_dialog',
            'show_copy_portfolio_dialog', 
            'show_add_symbol_dialog',
            'show_update_position_dialog',
            'show_create_analysis_dialog',
            'show_detail_modal',
            'show_transaction_modal',
            'delete_confirm_id'
        ]
        
        for flag in modal_flags:
            if flag in st.session_state:
                st.session_state[flag] = False
    
    @staticmethod
    def reset_portfolio_state() -> None:
        """Reset portfolio-related session states."""
        portfolio_keys = [
            'selected_portfolio',
            'selected_portfolio_for_pv',
            'current_portfolio_selection',
            'portfolio_switch_request',
            'edit_mode',
            'portfolio_backup',
            'pending_changes'
        ]
        
        for key in portfolio_keys:
            if key in st.session_state:
                if key in ['edit_mode', 'portfolio_backup', 'pending_changes']:
                    st.session_state[key] = {}
                else:
                    st.session_state[key] = None
    
    @staticmethod
    def get_current_portfolio() -> Optional[Dict[str, Any]]:
        """Get currently selected portfolio data."""
        selected_portfolio = st.session_state.get('selected_portfolio')
        if selected_portfolio and selected_portfolio in st.session_state.get('portfolios', {}):
            return st.session_state.portfolios[selected_portfolio]
        return None
    
    @staticmethod
    def set_current_page(page: str) -> None:
        """Navigate to specified page with state cleanup."""
        if page != st.session_state.get('current_page'):
            # Clear modals when changing pages
            SessionStateManager.clear_modal_states()
            
            # Update navigation state
            st.session_state.current_page = page
            st.session_state.navigation['page'] = page
            
            # Page-specific cleanup
            if page == 'overview':
                st.session_state.navigation['section'] = 'overview'
            elif page == 'portfolio':
                st.session_state.navigation['section'] = 'portfolios'
            elif page == 'pv_analysis':
                st.session_state.navigation['section'] = 'analysis'
            elif page == 'equity_analysis':
                st.session_state.navigation['section'] = 'equity'
            elif page == 'strategy_editor':
                st.session_state.navigation['section'] = 'strategies'
    
    @staticmethod
    def get_navigation_state() -> Dict[str, Any]:
        """Get current navigation context and breadcrumbs."""
        nav_state = st.session_state.get('navigation', {})
        current_page = st.session_state.get('current_page', 'overview')
        
        # Build breadcrumbs based on current page
        breadcrumbs = []
        if current_page == 'overview':
            breadcrumbs = [{'name': 'Portfolio Overview', 'page': 'overview'}]
        elif current_page == 'portfolio':
            breadcrumbs = [
                {'name': 'Portfolio Overview', 'page': 'overview'},
                {'name': 'Portfolio Management', 'page': 'portfolio'}
            ]
        elif current_page == 'pv_analysis':
            breadcrumbs = [
                {'name': 'Portfolio Overview', 'page': 'overview'},
                {'name': 'PV Analysis', 'page': 'pv_analysis'}
            ]
        elif current_page == 'equity_analysis':
            breadcrumbs = [
                {'name': 'Portfolio Overview', 'page': 'overview'},
                {'name': 'Equity Analysis', 'page': 'equity_analysis'}
            ]
        elif current_page == 'strategy_editor':
            breadcrumbs = [
                {'name': 'Portfolio Overview', 'page': 'overview'},
                {'name': 'Strategy Editor', 'page': 'strategy_editor'}
            ]
        
        return {
            'current_page': current_page,
            'section': nav_state.get('section', 'overview'),
            'breadcrumbs': breadcrumbs
        }
    
    @staticmethod
    def cache_price_data(symbol: str, data: dict, expiry_minutes: int = 15) -> None:
        """Cache price data with expiration."""
        if 'price_data_cache' not in st.session_state:
            st.session_state.price_data_cache = {}
        if 'cache_expiry' not in st.session_state:
            st.session_state.cache_expiry = {}
        
        st.session_state.price_data_cache[symbol] = data
        st.session_state.cache_expiry[symbol] = datetime.now().timestamp() + (expiry_minutes * 60)
    
    @staticmethod
    def get_cached_price_data(symbol: str) -> Optional[dict]:
        """Retrieve cached price data if not expired."""
        if 'price_data_cache' not in st.session_state or 'cache_expiry' not in st.session_state:
            return None
        
        if symbol not in st.session_state.price_data_cache:
            return None
        
        # Check if expired
        expiry_time = st.session_state.cache_expiry.get(symbol, 0)
        if datetime.now().timestamp() > expiry_time:
            # Remove expired data
            if symbol in st.session_state.price_data_cache:
                del st.session_state.price_data_cache[symbol]
            if symbol in st.session_state.cache_expiry:
                del st.session_state.cache_expiry[symbol]
            return None
        
        return st.session_state.price_data_cache[symbol]
    
    @staticmethod
    def clear_cache() -> None:
        """Clear all cached data."""
        cache_keys = ['price_data_cache', 'cache_expiry', 'portfolio_prices', 'fetch_details', 'last_update']
        for key in cache_keys:
            if key in st.session_state:
                st.session_state[key] = {}
    
    @staticmethod
    def init_portfolio_specific_state(portfolio_id: str) -> None:
        """Initialize portfolio-specific session state variables."""
        if f'edit_mode_{portfolio_id}' not in st.session_state:
            st.session_state[f'edit_mode_{portfolio_id}'] = False
        
        if f'deleted_positions_{portfolio_id}' not in st.session_state:
            st.session_state[f'deleted_positions_{portfolio_id}'] = []
        
        if f'modified_positions_{portfolio_id}' not in st.session_state:
            st.session_state[f'modified_positions_{portfolio_id}'] = {}
    
    @staticmethod
    def get_state_summary() -> Dict[str, Any]:
        """Get summary of current session state for debugging."""
        return {
            'current_page': st.session_state.get('current_page'),
            'selected_portfolio': st.session_state.get('selected_portfolio'),
            'portfolios_count': len(st.session_state.get('portfolios', {})),
            'cache_items': len(st.session_state.get('price_data_cache', {})),
            'navigation_state': st.session_state.get('navigation', {}),
            'modal_states': {
                key: st.session_state.get(key, False) 
                for key in st.session_state.keys() 
                if 'show_' in key or 'dialog' in key
            }
        }


# Convenience functions for backward compatibility
def init_session_state() -> None:
    """Initialize all session state variables with defaults."""
    SessionStateManager.init_session_state()

def clear_modal_states() -> None:
    """Clear all modal dialog states."""
    SessionStateManager.clear_modal_states()

def reset_portfolio_state() -> None:
    """Reset portfolio-related session states."""
    SessionStateManager.reset_portfolio_state()

def get_current_portfolio() -> Optional[Dict[str, Any]]:
    """Get currently selected portfolio data."""
    return SessionStateManager.get_current_portfolio()

def set_current_page(page: str) -> None:
    """Navigate to specified page with state cleanup."""
    SessionStateManager.set_current_page(page)

def get_navigation_state() -> Dict[str, Any]:
    """Get current navigation context and breadcrumbs.""" 
    return SessionStateManager.get_navigation_state()

def cache_price_data(symbol: str, data: dict, expiry_minutes: int = 15) -> None:
    """Cache price data with expiration."""
    SessionStateManager.cache_price_data(symbol, data, expiry_minutes)

def get_cached_price_data(symbol: str) -> Optional[dict]:
    """Retrieve cached price data if not expired."""
    return SessionStateManager.get_cached_price_data(symbol)