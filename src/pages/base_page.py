"""
Base Page Class for HK Strategy Dashboard.
Abstract base class providing common functionality for all dashboard pages.

Provides consistent page lifecycle, error handling, and integration with
navigation system and services layer.
"""

import streamlit as st
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import navigation and services
from src.navigation import get_navigation_config, get_page_router
from src.services import DataService, TechnicalIndicators, PortfolioService, AnalysisService

# Setup logging
logger = logging.getLogger(__name__)


class BasePage(ABC):
    """
    Abstract base class for all dashboard pages.
    Provides common functionality and enforces consistent page structure.
    """
    
    def __init__(self, page_key: str):
        """
        Initialize base page.
        
        Args:
            page_key: Unique identifier for this page
        """
        self.page_key = page_key
        self.config = get_navigation_config()
        self.router = get_page_router()
        
        # Initialize services
        self.services = {
            'data': DataService(),
            'indicators': TechnicalIndicators(),
            'portfolio': PortfolioService(),
            'analysis': AnalysisService()
        }
        
        # Page configuration
        self.page_config = self.config.get_page_config(page_key)
        
        # Initialize page state
        self._init_page_state()
    
    def _init_page_state(self) -> None:
        """Initialize page-specific session state variables."""
        page_state_key = f"page_state_{self.page_key}"
        if page_state_key not in st.session_state:
            st.session_state[page_state_key] = {
                'initialized': True,
                'last_visit': datetime.now().isoformat(),
                'error_count': 0
            }
    
    def get_page_state(self) -> Dict[str, Any]:
        """Get page-specific session state."""
        page_state_key = f"page_state_{self.page_key}"
        return st.session_state.get(page_state_key, {})
    
    def update_page_state(self, updates: Dict[str, Any]) -> None:
        """Update page-specific session state."""
        page_state_key = f"page_state_{self.page_key}"
        if page_state_key in st.session_state:
            st.session_state[page_state_key].update(updates)
        else:
            st.session_state[page_state_key] = updates
    
    def render(self) -> None:
        """
        Main render method for the page.
        Handles page lifecycle: pre-render, content, post-render, error handling.
        """
        try:
            # Pre-render setup
            self.pre_render()
            
            # Render page content
            self._render_content()
            
            # Post-render cleanup
            self.post_render()
            
        except Exception as e:
            self.handle_page_error(e)
    
    def pre_render(self) -> None:
        """
        Pre-render setup. Called before main content rendering.
        Override in subclasses for page-specific setup.
        """
        # Update last visit time
        self.update_page_state({'last_visit': datetime.now().isoformat()})
        
        # Log page access
        logger.debug(f"Rendering page: {self.page_key}")
        
        # Validate page access
        if not self.validate_page_access():
            st.error("Access denied to this page")
            st.stop()
    
    def post_render(self) -> None:
        """
        Post-render cleanup. Called after main content rendering.
        Override in subclasses for page-specific cleanup.
        """
        # Update page state
        page_state = self.get_page_state()
        page_state['last_render'] = datetime.now().isoformat()
        self.update_page_state(page_state)
    
    @abstractmethod
    def _render_content(self) -> None:
        """
        Render the main page content.
        Must be implemented by all page subclasses.
        """
        pass
    
    def validate_page_access(self) -> bool:
        """
        Validate if current user can access this page.
        Override in subclasses for custom access control.
        """
        if not self.page_config:
            return False
        
        # Check if portfolio is required
        if self.config.requires_portfolio(self.page_key):
            selected_portfolio = (st.session_state.get('selected_portfolio') or 
                                st.session_state.get('selected_portfolio_for_pv'))
            portfolios = st.session_state.get('portfolios', {})
            return selected_portfolio and selected_portfolio in portfolios
        
        return True
    
    def handle_page_error(self, error: Exception) -> None:
        """
        Handle page rendering errors.
        Override in subclasses for custom error handling.
        """
        logger.error(f"Error rendering page {self.page_key}: {str(error)}")
        
        # Update error count
        page_state = self.get_page_state()
        page_state['error_count'] = page_state.get('error_count', 0) + 1
        page_state['last_error'] = str(error)
        page_state['last_error_time'] = datetime.now().isoformat()
        self.update_page_state(page_state)
        
        # Display error to user
        st.error(f"Error loading {self.page_config.get('label', self.page_key)}")
        
        # Show detailed error in debug mode
        if st.session_state.get('debug_mode', False):
            st.exception(error)
        else:
            st.error(f"Error details: {str(error)}")
    
    def render_page_header(self, title: Optional[str] = None, subtitle: Optional[str] = None) -> None:
        """
        Render standard page header.
        
        Args:
            title: Page title (uses config if not provided)
            subtitle: Page subtitle
        """
        if not title and self.page_config:
            title = self.page_config.get('label', self.page_key.title())
        
        if title:
            st.subheader(title)
        
        if subtitle:
            st.caption(subtitle)
        
        # Add description if available
        if self.page_config and self.page_config.get('description'):
            st.caption(self.page_config['description'])
    
    def render_page_footer(self) -> None:
        """Render standard page footer with debug info."""
        if st.session_state.get('debug_mode', False):
            with st.expander("🔍 Page Debug Info", expanded=False):
                page_state = self.get_page_state()
                debug_info = {
                    'page_key': self.page_key,
                    'page_config': self.page_config,
                    'page_state': page_state,
                    'services_loaded': list(self.services.keys())
                }
                st.json(debug_info)
    
    def get_current_portfolio(self) -> Optional[Dict[str, Any]]:
        """Get currently selected portfolio data."""
        selected_portfolio = (st.session_state.get('selected_portfolio') or 
                            st.session_state.get('selected_portfolio_for_pv'))
        
        if selected_portfolio and selected_portfolio in st.session_state.get('portfolios', {}):
            return st.session_state.portfolios[selected_portfolio]
        
        return None
    
    def get_selected_portfolio_id(self) -> Optional[str]:
        """Get currently selected portfolio ID."""
        return (st.session_state.get('selected_portfolio') or 
                st.session_state.get('selected_portfolio_for_pv'))
    
    def require_portfolio_selection(self) -> bool:
        """
        Ensure a portfolio is selected. Show selection interface if not.
        
        Returns:
            True if portfolio is selected, False if selection interface was shown
        """
        if self.get_current_portfolio():
            return True
        
        # Show portfolio selection interface
        st.warning("Please select a portfolio to continue.")
        
        portfolios = st.session_state.get('portfolios', {})
        if not portfolios:
            st.error("No portfolios available. Please create a portfolio first.")
            if st.button("Go to Portfolio Overview"):
                self.router.route_to_page('overview')
                st.rerun()
            return False
        
        # Portfolio selector
        portfolio_options = list(portfolios.keys())
        portfolio_labels = [portfolios[key]['name'] for key in portfolio_options]
        
        selected_index = st.selectbox(
            "Choose Portfolio:",
            range(len(portfolio_options)),
            format_func=lambda i: portfolio_labels[i]
        )
        
        if st.button("Select Portfolio", type="primary"):
            selected_portfolio = portfolio_options[selected_index]
            st.session_state.selected_portfolio = selected_portfolio
            st.session_state.selected_portfolio_for_pv = selected_portfolio
            st.rerun()
        
        return False
    
    def show_loading_spinner(self, message: str = "Loading...") -> None:
        """Show loading spinner with message."""
        st.spinner(message)
    
    def show_success_message(self, message: str) -> None:
        """Show success message."""
        st.success(message)
    
    def show_error_message(self, message: str) -> None:
        """Show error message.""" 
        st.error(message)
    
    def show_warning_message(self, message: str) -> None:
        """Show warning message."""
        st.warning(message)
    
    def show_info_message(self, message: str) -> None:
        """Show info message."""
        st.info(message)
    
    def get_page_url(self) -> str:
        """Get URL for this page."""
        return self.router.get_page_url(self.page_key)
    
    def navigate_to_page(self, page_key: str, **kwargs) -> bool:
        """Navigate to another page."""
        return self.router.route_to_page(page_key, **kwargs)
    
    def get_page_permissions(self) -> Dict[str, Any]:
        """Get permissions for this page."""
        if not self.page_config:
            return {}
        
        return {
            'permission_level': self.page_config.get('permission', 'user'),
            'requires_portfolio': self.page_config.get('requires_portfolio', False),
            'description': self.page_config.get('description', '')
        }
    
    def log_user_action(self, action: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Log user action for analytics."""
        log_data = {
            'page': self.page_key,
            'action': action,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        logger.info(f"User action: {log_data}")
    
    def clear_page_cache(self) -> None:
        """Clear page-specific cache data."""
        page_state_key = f"page_state_{self.page_key}"
        if page_state_key in st.session_state:
            # Keep essential state, clear cache
            essential_keys = ['initialized', 'last_visit']
            current_state = st.session_state[page_state_key]
            cleared_state = {key: current_state[key] for key in essential_keys if key in current_state}
            cleared_state['cache_cleared_at'] = datetime.now().isoformat()
            st.session_state[page_state_key] = cleared_state
    
    def get_page_metrics(self) -> Dict[str, Any]:
        """Get page performance and usage metrics."""
        page_state = self.get_page_state()
        return {
            'page_key': self.page_key,
            'visits': page_state.get('visit_count', 0),
            'errors': page_state.get('error_count', 0),
            'last_visit': page_state.get('last_visit'),
            'last_error': page_state.get('last_error_time'),
            'initialized': page_state.get('initialized', False)
        }