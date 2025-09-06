"""
Page Manager for HK Strategy Dashboard.

Central manager for handling page routing, creation, and lifecycle management.
Integrates the modular page architecture with the navigation system.
"""

import logging
from typing import Optional, Dict, Any
import streamlit as st

from . import PAGE_REGISTRY, create_page_instance, validate_page_key
from .base_page import BasePage
from ..navigation.navigation_config import get_navigation_config

# Setup logging
logger = logging.getLogger(__name__)


class PageManager:
    """Central page manager for routing and lifecycle management."""
    
    def __init__(self):
        """Initialize the page manager."""
        self.navigation_config = get_navigation_config()
        self._page_cache: Dict[str, BasePage] = {}
        
    def render_current_page(self) -> None:
        """
        Render the current page based on session state.
        
        This is the main entry point for page rendering in the dashboard.
        """
        try:
            # Get current navigation state
            current_section = getattr(st.session_state, 'current_section', 'portfolios')
            current_page = getattr(st.session_state, 'current_page', 'overview')
            
            # Resolve legacy page names if necessary
            current_page = self.navigation_config.resolve_legacy_page(current_page)
            
            # Validate page exists
            if not validate_page_key(current_page):
                logger.warning(f"Unknown page key: {current_page}. Falling back to overview.")
                current_page = 'overview'
                st.session_state.current_page = current_page
            
            # Check permissions
            if not self._check_page_permissions(current_page):
                st.error("🚫 Access Denied: You don't have permission to access this page.")
                return
            
            # Check portfolio requirements
            if self._requires_portfolio_selection(current_page):
                if not self._has_portfolio_selected():
                    st.warning("⚠️ Please select a portfolio to access this page.")
                    self._render_portfolio_selection()
                    return
            
            # Get or create page instance
            page = self._get_page_instance(current_page)
            if not page:
                st.error(f"❌ Failed to load page: {current_page}")
                return
            
            # Render the page
            logger.info(f"Rendering page: {current_page}")
            page.render()
            
        except Exception as e:
            logger.error(f"Error rendering page: {str(e)}")
            st.error(f"❌ Page rendering error: {str(e)}")
            
            # Fallback to overview page
            try:
                overview_page = self._get_page_instance('overview')
                if overview_page:
                    overview_page.render()
            except Exception as fallback_error:
                logger.error(f"Fallback page rendering failed: {str(fallback_error)}")
                st.error("❌ Critical error: Unable to render any page.")
    
    def _get_page_instance(self, page_key: str) -> Optional[BasePage]:
        """
        Get page instance, using cache when possible.
        
        Args:
            page_key: The page key to get
            
        Returns:
            Page instance or None if not found
        """
        # Check cache first
        if page_key in self._page_cache:
            return self._page_cache[page_key]
        
        # Create new instance
        page = create_page_instance(page_key)
        if page:
            # Cache the instance for reuse
            self._page_cache[page_key] = page
            logger.debug(f"Created and cached page instance: {page_key}")
        else:
            logger.error(f"Failed to create page instance: {page_key}")
        
        return page
    
    def _check_page_permissions(self, page_key: str) -> bool:
        """
        Check if current user has permission to access the page.
        
        Args:
            page_key: The page key to check
            
        Returns:
            True if user has permission, False otherwise
        """
        try:
            # Get current user permission level (placeholder - would integrate with auth system)
            user_permission = getattr(st.session_state, 'user_permission', 'USER')
            
            # Convert string to enum if needed
            from ..navigation.navigation_config import PagePermission
            if isinstance(user_permission, str):
                user_permission = getattr(PagePermission, user_permission, PagePermission.USER)
            
            # Check permission using navigation config
            return self.navigation_config.check_page_permission(page_key, user_permission)
            
        except Exception as e:
            logger.warning(f"Permission check failed for {page_key}: {str(e)}")
            return True  # Default to allowing access if check fails
    
    def _requires_portfolio_selection(self, page_key: str) -> bool:
        """
        Check if page requires portfolio selection.
        
        Args:
            page_key: The page key to check
            
        Returns:
            True if portfolio selection is required
        """
        return self.navigation_config.requires_portfolio(page_key)
    
    def _has_portfolio_selected(self) -> bool:
        """
        Check if user has selected a portfolio.
        
        Returns:
            True if portfolio is selected
        """
        current_portfolio = getattr(st.session_state, 'current_portfolio', None)
        return current_portfolio is not None and current_portfolio != ''
    
    def _render_portfolio_selection(self) -> None:
        """Render portfolio selection interface."""
        st.info("📊 This page requires a portfolio selection.")
        
        # Get available portfolios
        portfolios = getattr(st.session_state, 'portfolios', {})
        
        if not portfolios:
            st.warning("No portfolios found. Please create a portfolio first.")
            if st.button("➕ Create Portfolio"):
                st.session_state.current_page = 'overview'
                st.rerun()
            return
        
        # Portfolio selection
        portfolio_options = list(portfolios.keys())
        selected_portfolio = st.selectbox(
            "Select Portfolio:",
            portfolio_options,
            index=0
        )
        
        if st.button("📊 Continue to Page", type="primary"):
            st.session_state.current_portfolio = selected_portfolio
            st.rerun()
    
    def clear_page_cache(self) -> None:
        """Clear the page instance cache."""
        self._page_cache.clear()
        logger.info("Page cache cleared")
    
    def get_cached_pages(self) -> list:
        """Get list of currently cached page keys."""
        return list(self._page_cache.keys())
    
    def navigate_to_page(self, page_key: str, section_key: Optional[str] = None) -> None:
        """
        Navigate to a specific page.
        
        Args:
            page_key: The page key to navigate to
            section_key: Optional section key (will be inferred if not provided)
        """
        if not validate_page_key(page_key):
            logger.error(f"Invalid page key: {page_key}")
            return
        
        # Infer section if not provided
        if not section_key:
            section_key = self.navigation_config.get_page_section(page_key)
        
        # Update session state
        if section_key:
            st.session_state.current_section = section_key
        st.session_state.current_page = page_key
        
        logger.info(f"Navigated to page: {page_key} in section: {section_key}")
        st.rerun()


# Global page manager instance
_page_manager_instance = None


def get_page_manager() -> PageManager:
    """Get global page manager instance (singleton)."""
    global _page_manager_instance
    if _page_manager_instance is None:
        _page_manager_instance = PageManager()
    return _page_manager_instance


def render_current_page() -> None:
    """Convenience function to render the current page."""
    manager = get_page_manager()
    manager.render_current_page()


def navigate_to_page(page_key: str, section_key: Optional[str] = None) -> None:
    """Convenience function to navigate to a page."""
    manager = get_page_manager()
    manager.navigate_to_page(page_key, section_key)


def clear_page_cache() -> None:
    """Convenience function to clear page cache."""
    manager = get_page_manager()
    manager.clear_page_cache()