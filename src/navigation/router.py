"""
Page Router for HK Strategy Dashboard.
Manages page navigation, routing, and state transitions.

Extracts routing logic from dashboard.py lines 2648+ and session state management.
"""

import streamlit as st
import logging
from typing import Dict, List, Any, Optional, Callable, Tuple
from datetime import datetime

from .navigation_config import get_navigation_config, PagePermission

# Setup logging
logger = logging.getLogger(__name__)


class PageRouter:
    """Manages page routing and navigation for the dashboard."""
    
    def __init__(self):
        """Initialize the page router."""
        self.config = get_navigation_config()
        self._page_handlers = {}
        self._middleware = []
        
        # Initialize session state if needed
        self._init_navigation_state()
    
    def _init_navigation_state(self) -> None:
        """Initialize navigation-related session state variables."""
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'overview'  # Default page
        
        if 'navigation' not in st.session_state:
            st.session_state.navigation = {
                'section': 'portfolios',
                'page': 'overview',
                'breadcrumbs': []
            }
        
        if 'previous_page' not in st.session_state:
            st.session_state.previous_page = None
    
    def register_page_handler(self, page_key: str, handler: Callable) -> None:
        """
        Register a handler function for a specific page.
        
        Args:
            page_key: Page identifier
            handler: Function to handle page rendering
        """
        if not self.config.validate_page_exists(page_key):
            logger.warning(f"Registering handler for unknown page: {page_key}")
        
        self._page_handlers[page_key] = handler
        logger.debug(f"Registered handler for page: {page_key}")
    
    def add_middleware(self, middleware: Callable) -> None:
        """
        Add middleware function to be executed before page routing.
        
        Args:
            middleware: Function to execute before routing
        """
        self._middleware.append(middleware)
        logger.debug(f"Added middleware: {middleware.__name__}")
    
    def get_current_page(self) -> str:
        """Get the current page key."""
        return st.session_state.get('current_page', 'overview')
    
    def get_current_section(self) -> str:
        """Get the current section key."""
        current_page = self.get_current_page()
        return self.config.get_page_section(current_page) or 'portfolios'
    
    def get_previous_page(self) -> Optional[str]:
        """Get the previous page key."""
        return st.session_state.get('previous_page')
    
    def route_to_page(self, page_key: str, **kwargs) -> bool:
        """
        Navigate to a specific page with optional parameters.
        
        Args:
            page_key: Target page identifier
            **kwargs: Additional parameters for page navigation
            
        Returns:
            True if navigation was successful
        """
        try:
            # Resolve legacy page names for backward compatibility
            resolved_page = self.config.resolve_legacy_page(page_key)
            
            # Validate page exists
            if not self.config.validate_page_exists(resolved_page):
                logger.error(f"Invalid page: {page_key} (resolved: {resolved_page})")
                return False
            
            # Check permissions
            if not self._check_page_permission(resolved_page):
                logger.warning(f"Access denied to page: {resolved_page}")
                return False
            
            # Check portfolio requirement
            if not self._check_portfolio_requirement(resolved_page):
                logger.warning(f"Portfolio required for page: {resolved_page}")
                return False
            
            # Execute middleware
            for middleware in self._middleware:
                try:
                    if not middleware(resolved_page, **kwargs):
                        logger.info(f"Middleware blocked navigation to: {resolved_page}")
                        return False
                except Exception as e:
                    logger.error(f"Middleware error for page {resolved_page}: {str(e)}")
                    return False
            
            # Perform navigation
            success = self._perform_navigation(resolved_page, **kwargs)
            
            if success:
                logger.info(f"Navigated to page: {resolved_page}")
            
            return success
            
        except Exception as e:
            logger.error(f"Navigation error to page {page_key}: {str(e)}")
            return False
    
    def _check_page_permission(self, page_key: str, user_permission: PagePermission = PagePermission.USER) -> bool:
        """Check if user has permission to access the page."""
        return self.config.check_page_permission(page_key, user_permission)
    
    def _check_portfolio_requirement(self, page_key: str) -> bool:
        """Check if page requires portfolio and one is selected."""
        if not self.config.requires_portfolio(page_key):
            return True
        
        # Check if a portfolio is selected
        selected_portfolio = (st.session_state.get('selected_portfolio') or 
                            st.session_state.get('selected_portfolio_for_pv'))
        
        portfolios = st.session_state.get('portfolios', {})
        return selected_portfolio and selected_portfolio in portfolios
    
    def _perform_navigation(self, page_key: str, **kwargs) -> bool:
        """Perform the actual navigation to the page."""
        try:
            # Store previous page
            current_page = st.session_state.get('current_page')
            if current_page != page_key:
                st.session_state.previous_page = current_page
            
            # Update current page
            st.session_state.current_page = page_key
            
            # Update navigation state
            section_key = self.config.get_page_section(page_key)
            if section_key:
                st.session_state.navigation.update({
                    'section': section_key,
                    'page': page_key,
                    'last_navigation': datetime.now().isoformat()
                })
            
            # Clear modal states on page change
            self._clear_modal_states()
            
            # Store navigation parameters
            if kwargs:
                st.session_state.navigation['params'] = kwargs
            
            # Trigger Streamlit rerun
            st.rerun()
            
            return True
            
        except Exception as e:
            logger.error(f"Error performing navigation to {page_key}: {str(e)}")
            return False
    
    def _clear_modal_states(self) -> None:
        """Clear modal dialog states when navigating between pages."""
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
    
    def handle_page_not_found(self, page_key: str) -> None:
        """Handle navigation to non-existent page."""
        logger.warning(f"Page not found: {page_key}")
        
        # Try to navigate to section default page
        section = self.config.get_page_section(page_key)
        if section:
            default_page = self.config.get_default_page_for_section(section)
            if default_page:
                self.route_to_page(default_page)
                return
        
        # Fallback to overview
        self.route_to_page('overview')
    
    def validate_page_access(self, page_key: str) -> Tuple[bool, str]:
        """
        Validate if a page can be accessed.
        
        Args:
            page_key: Page to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if page exists
        if not self.config.validate_page_exists(page_key):
            return False, f"Page '{page_key}' does not exist"
        
        # Check permissions
        if not self._check_page_permission(page_key):
            return False, f"Access denied to page '{page_key}'"
        
        # Check portfolio requirement
        if not self._check_portfolio_requirement(page_key):
            return False, f"Page '{page_key}' requires a portfolio to be selected"
        
        return True, ""
    
    def get_navigation_history(self) -> List[str]:
        """Get navigation history (simplified)."""
        history = []
        current_page = self.get_current_page()
        previous_page = self.get_previous_page()
        
        if previous_page:
            history.append(previous_page)
        if current_page:
            history.append(current_page)
        
        return history
    
    def can_go_back(self) -> bool:
        """Check if user can navigate back to previous page."""
        previous_page = self.get_previous_page()
        if not previous_page:
            return False
        
        is_valid, _ = self.validate_page_access(previous_page)
        return is_valid
    
    def go_back(self) -> bool:
        """Navigate back to previous page."""
        if self.can_go_back():
            previous_page = self.get_previous_page()
            return self.route_to_page(previous_page)
        return False
    
    def get_page_url(self, page_key: str, **params) -> str:
        """
        Generate URL for a page (placeholder for future URL routing).
        
        Args:
            page_key: Page identifier
            **params: URL parameters
            
        Returns:
            URL string
        """
        route = self.config.get_page_route(page_key)
        if not route:
            return f"/{page_key}"
        
        url = f"/{route}"
        if params:
            param_str = "&".join([f"{k}={v}" for k, v in params.items()])
            url += f"?{param_str}"
        
        return url
    
    def render_current_page(self) -> None:
        """Render the current page using registered handlers."""
        current_page = self.get_current_page()
        
        # Check if we have a handler for the current page
        if current_page in self._page_handlers:
            try:
                handler = self._page_handlers[current_page]
                handler()
            except Exception as e:
                logger.error(f"Error rendering page {current_page}: {str(e)}")
                st.error(f"Error loading page: {str(e)}")
        else:
            # Handle pages that don't have registered handlers (legacy pages)
            self._handle_legacy_page_routing(current_page)
    
    def _handle_legacy_page_routing(self, page_key: str) -> None:
        """Handle legacy page routing for backward compatibility."""
        # This is a placeholder for integration with existing dashboard.py routing
        # In the full implementation, this would delegate to the original routing logic
        
        st.warning(f"Legacy page routing for: {page_key}")
        st.info("This page will be migrated to the new navigation system in future phases.")
        
        # Show page configuration for debugging
        page_config = self.config.get_page_config(page_key)
        if page_config:
            st.json(page_config)
    
    def get_router_state(self) -> Dict[str, Any]:
        """Get current router state for debugging."""
        return {
            'current_page': self.get_current_page(),
            'current_section': self.get_current_section(),
            'previous_page': self.get_previous_page(),
            'navigation_state': st.session_state.get('navigation', {}),
            'registered_handlers': list(self._page_handlers.keys()),
            'middleware_count': len(self._middleware)
        }


# Global router instance
_router_instance = None

def get_page_router() -> PageRouter:
    """Get global page router instance (singleton)."""
    global _router_instance
    if _router_instance is None:
        _router_instance = PageRouter()
    return _router_instance

def route_to_page(page_key: str, **kwargs) -> bool:
    """Navigate to specified page with optional parameters."""
    return get_page_router().route_to_page(page_key, **kwargs)

def get_current_page() -> str:
    """Get current page name."""
    return get_page_router().get_current_page()

def validate_page_access(page_key: str) -> Tuple[bool, str]:
    """Validate if a page can be accessed."""
    return get_page_router().validate_page_access(page_key)

def handle_page_not_found(page_key: str) -> None:
    """Handle navigation to non-existent page."""
    return get_page_router().handle_page_not_found(page_key)

def register_page_handler(page_key: str, handler: Callable) -> None:
    """Register a handler function for a specific page."""
    return get_page_router().register_page_handler(page_key, handler)

def render_current_page() -> None:
    """Render the current page using registered handlers."""
    return get_page_router().render_current_page()