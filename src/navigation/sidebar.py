"""
Sidebar Navigation for HK Strategy Dashboard.
Handles sidebar rendering, navigation buttons, and portfolio selection.

Extracted from dashboard.py lines 2186-2242
"""

import streamlit as st
import logging
from typing import Dict, List, Any, Optional

from .navigation_config import get_navigation_config
from .router import get_page_router

# Setup logging
logger = logging.getLogger(__name__)


class SidebarNavigator:
    """Manages sidebar navigation rendering and interactions."""
    
    def __init__(self):
        """Initialize the sidebar navigator."""
        self.config = get_navigation_config()
        self.router = get_page_router()
    
    def render_sidebar(self) -> None:
        """
        Render the main sidebar navigation.
        
        Extracted from dashboard.py lines 2186-2242
        """
        # Render header
        self._render_sidebar_header()
        
        # Render navigation sections
        self._render_navigation_sections()
        
        # Render portfolio selector if needed
        self._render_portfolio_selector()
        
        # Render sidebar footer
        self._render_sidebar_footer()
    
    def _render_sidebar_header(self) -> None:
        """
        Render sidebar header with branding.
        
        Extracted from dashboard.py lines 2187-2193
        """
        st.sidebar.markdown("""
        <div style='text-align: center; padding: 10px 0;'>
            <h3 style='margin: 0; color: #1f77b4;'>🏠 HK Strategy</h3>
            <p style='margin: 0; font-size: 12px; color: #8e8ea0;'>Multi-Dashboard System</p>
        </div>
        """, unsafe_allow_html=True)
        st.sidebar.markdown("---")
    
    def _render_navigation_sections(self) -> None:
        """
        Render hierarchical navigation sections.
        
        Extracted logic from dashboard.py lines 2195-2242
        """
        current_section = self.router.get_current_section()
        current_page = self.router.get_current_page()
        
        # Get ordered sections
        ordered_sections = self.config.get_ordered_sections()
        
        for section_key, section_data in ordered_sections:
            # Create expandable section
            is_expanded = (current_section == section_key)
            
            with st.sidebar.expander(
                f"{section_data['icon']} {section_data['label']}", 
                expanded=is_expanded
            ):
                self._render_section_pages(section_key, section_data, current_page)
    
    def _render_section_pages(self, section_key: str, section_data: Dict[str, Any], current_page: str) -> None:
        """Render pages within a navigation section."""
        for page_key, page_config in section_data['pages'].items():
            self._render_page_button(section_key, page_key, page_config, current_page)
    
    def _render_page_button(self, section_key: str, page_key: str, page_config: Dict[str, Any], current_page: str) -> None:
        """Render a single page navigation button."""
        # Create unique button key
        button_key = f"nav_{section_key}_{page_key}"
        
        # Check if this is the current page
        is_current = (current_page == page_key)
        
        # Handle legacy page mapping for existing functionality
        legacy_mapping = self.config.get_legacy_page_mapping()
        legacy_page = None
        for legacy_key, mapped_page in legacy_mapping.items():
            if mapped_page == page_key:
                legacy_page = legacy_key
                break
        
        # Check if page is available or should show as future feature
        is_available = self._is_page_available(page_key)
        
        if is_available:
            # Available page - render functional button
            if st.sidebar.button(
                page_config['label'], 
                key=button_key,
                help=page_config.get('description', ''),
                disabled=is_current
            ):
                # Handle page navigation
                success = self.router.route_to_page(page_key)
                if success:
                    logger.info(f"Navigated to {page_key} via sidebar")
                else:
                    st.error(f"Failed to navigate to {page_config['label']}")
        else:
            # Future/unavailable pages - show as disabled
            st.sidebar.button(
                f"🚧 {page_config['label']} (Coming Soon)",
                key=button_key,
                disabled=True,
                help=f"This feature is planned for future releases: {page_config.get('description', '')}"
            )
    
    def _is_page_available(self, page_key: str) -> bool:
        """Check if a page is currently available or is a future feature."""
        # For Phase 3, we'll mark pages as available based on existing implementation
        available_pages = {
            'overview', 'portfolio', 'pv_analysis', 'equity_analysis', 
            'strategy_editor', 'strategy_comparison', 'system_status'
        }
        return page_key in available_pages
    
    def _render_portfolio_selector(self) -> None:
        """Render portfolio selection dropdown in sidebar if needed."""
        current_page = self.router.get_current_page()
        
        # Only show portfolio selector for portfolio-related pages
        if self.config.requires_portfolio(current_page) or current_page in ['portfolio', 'pv_analysis']:
            self._render_portfolio_dropdown()
    
    def _render_portfolio_dropdown(self) -> None:
        """Render portfolio selection dropdown."""
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📊 Portfolio Selection")
        
        portfolios = st.session_state.get('portfolios', {})
        if not portfolios:
            st.sidebar.warning("No portfolios available")
            return
        
        # Get current selection
        current_selection = (st.session_state.get('selected_portfolio') or 
                           st.session_state.get('selected_portfolio_for_pv'))
        
        # Create portfolio options
        portfolio_options = list(portfolios.keys())
        portfolio_labels = [portfolios[key]['name'] for key in portfolio_options]
        
        # Find current index
        current_index = 0
        if current_selection and current_selection in portfolio_options:
            current_index = portfolio_options.index(current_selection)
        
        # Portfolio selector
        selected_index = st.sidebar.selectbox(
            "Select Portfolio:",
            range(len(portfolio_options)),
            index=current_index,
            format_func=lambda i: portfolio_labels[i],
            key="sidebar_portfolio_selector"
        )
        
        selected_portfolio = portfolio_options[selected_index]
        
        # Update session state if changed
        if selected_portfolio != current_selection:
            st.session_state.selected_portfolio = selected_portfolio
            st.session_state.selected_portfolio_for_pv = selected_portfolio
            st.rerun()
    
    def _render_sidebar_footer(self) -> None:
        """Render sidebar footer with system information."""
        st.sidebar.markdown("---")
        
        # Show current page info
        current_page = self.router.get_current_page()
        page_config = self.config.get_page_config(current_page)
        
        if page_config:
            st.sidebar.markdown(f"**Current Page:** {page_config['label']}")
        
        # Show navigation state in debug mode
        if st.session_state.get('debug_mode', False):
            with st.sidebar.expander("🔍 Navigation Debug", expanded=False):
                router_state = self.router.get_router_state()
                st.json(router_state)
        
        # Show system status
        with st.sidebar.expander("📊 System Status", expanded=False):
            self._render_system_status()
    
    def _render_system_status(self) -> None:
        """Render system status information."""
        # Portfolio count
        portfolios = st.session_state.get('portfolios', {})
        st.markdown(f"**Portfolios:** {len(portfolios)}")
        
        # Database connection status
        db_manager = st.session_state.get('db_manager')
        db_status = "✅ Connected" if db_manager else "❌ Disconnected"
        st.markdown(f"**Database:** {db_status}")
        
        # Current session info
        current_page = self.router.get_current_page()
        st.markdown(f"**Page:** {current_page}")
        
        # Navigation history
        history = self.router.get_navigation_history()
        if len(history) > 1:
            st.markdown(f"**Previous:** {history[-2]}")
    
    def create_navigation_buttons(self, section_key: str) -> None:
        """
        Create navigation buttons for a specific section.
        
        Args:
            section_key: Section to create buttons for
        """
        section = self.config.get_section(section_key)
        if not section:
            return
        
        current_page = self.router.get_current_page()
        
        for page_key, page_config in section['pages'].items():
            self._render_page_button(section_key, page_key, page_config, current_page)
    
    def handle_sidebar_actions(self) -> None:
        """Handle sidebar-specific actions and state changes."""
        # This method can be extended for custom sidebar interactions
        # For now, all actions are handled in the render methods
        pass
    
    def show_page_context(self) -> None:
        """Show current page context and information.""" 
        current_page = self.router.get_current_page()
        section_key = self.router.get_current_section()
        
        page_config = self.config.get_page_config(current_page)
        section_config = self.config.get_section(section_key)
        
        if page_config and section_config:
            st.sidebar.markdown("---")
            st.sidebar.markdown("### 📍 Current Context")
            st.sidebar.markdown(f"**Section:** {section_config['label']}")
            st.sidebar.markdown(f"**Page:** {page_config['label']}")
            
            if page_config.get('description'):
                st.sidebar.caption(page_config['description'])


# Global sidebar navigator instance
_sidebar_instance = None

def get_sidebar_navigator() -> SidebarNavigator:
    """Get global sidebar navigator instance (singleton)."""
    global _sidebar_instance
    if _sidebar_instance is None:
        _sidebar_instance = SidebarNavigator()
    return _sidebar_instance

def render_sidebar() -> None:
    """Render main sidebar navigation."""
    return get_sidebar_navigator().render_sidebar()

def create_navigation_buttons(section_key: str) -> None:
    """Create navigation buttons for a specific section."""
    return get_sidebar_navigator().create_navigation_buttons(section_key)

def show_page_context() -> None:
    """Show current page context and breadcrumbs."""
    return get_sidebar_navigator().show_page_context()

def handle_sidebar_actions() -> None:
    """Handle sidebar button clicks and navigation."""
    return get_sidebar_navigator().handle_sidebar_actions()