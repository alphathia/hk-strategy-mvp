"""
Breadcrumb Navigation for HK Strategy Dashboard.
Handles breadcrumb trail generation and rendering based on current page context.

Extracted from dashboard.py lines 2600-2645
"""

import streamlit as st
import logging
from typing import Dict, List, Any, Optional
from datetime import date, timedelta

from .navigation_config import get_navigation_config
from .router import get_page_router

# Setup logging
logger = logging.getLogger(__name__)


class BreadcrumbManager:
    """Manages breadcrumb navigation trail generation and rendering."""
    
    def __init__(self):
        """Initialize the breadcrumb manager."""
        self.config = get_navigation_config()
        self.router = get_page_router()
    
    def generate_breadcrumbs(self) -> List[str]:
        """
        Generate breadcrumb trail based on current navigation state.
        
        Extracted from dashboard.py lines 2600-2640
        """
        breadcrumbs = []
        
        # Get current navigation state
        nav_state = st.session_state.get('navigation', {})
        current_section = nav_state.get('section', 'portfolios')
        current_page = nav_state.get('page', 'overview')
        
        # Add section to breadcrumbs
        section_labels = self.config._build_section_labels()
        
        if current_section in section_labels:
            breadcrumbs.append(section_labels[current_section])
        
        # Add current page context based on section
        breadcrumbs.extend(self._get_page_breadcrumbs(current_section, current_page))
        
        return breadcrumbs
    
    def _get_page_breadcrumbs(self, current_section: str, current_page: str) -> List[str]:
        """Get page-specific breadcrumb components."""
        breadcrumbs = []
        
        if current_section == 'portfolios':
            breadcrumbs.extend(self._get_portfolio_breadcrumbs(current_page))
        elif current_section == 'strategy':
            breadcrumbs.extend(self._get_strategy_breadcrumbs(current_page))
        elif current_section == 'system':
            breadcrumbs.extend(self._get_system_breadcrumbs(current_page))
        
        return breadcrumbs
    
    def _get_portfolio_breadcrumbs(self, current_page: str) -> List[str]:
        """
        Get breadcrumbs for portfolio section pages.
        
        Extracted from dashboard.py lines 2614-2629
        """
        breadcrumbs = []
        
        if current_page == 'overview':
            breadcrumbs.append('📋 All Portfolios')
            
        elif current_page == 'portfolio':
            breadcrumbs.append('📊 Portfolio View')
            # Add portfolio name if available
            portfolio_name = self._get_selected_portfolio_name()
            if portfolio_name:
                breadcrumbs.append(f"📂 {portfolio_name}")
                
        elif current_page == 'pv_analysis':
            breadcrumbs.append('📈 Portfolio Analysis')
            # Add portfolio name if available
            portfolio_name = self._get_selected_portfolio_name()
            if portfolio_name:
                breadcrumbs.append(f"📂 {portfolio_name}")
                
            # Add analysis name if available
            analysis_name = self._get_current_analysis_name()
            if analysis_name:
                breadcrumbs.append(f"📊 {analysis_name}")
        
        return breadcrumbs
    
    def _get_strategy_breadcrumbs(self, current_page: str) -> List[str]:
        """
        Get breadcrumbs for strategy section pages.
        
        Extracted from dashboard.py lines 2630-2634
        """
        breadcrumbs = []
        
        if current_page == 'equity_analysis':
            breadcrumbs.append('📈 Equity Analysis')
            # Add equity symbol if available
            equity_context = st.session_state.get('equity_context', {})
            if equity_context.get('symbol'):
                symbol = equity_context['symbol']
                company_name = equity_context.get('company_name', symbol)
                breadcrumbs.append(f"📊 {symbol} ({company_name})")
                
        elif current_page == 'strategy_editor':
            breadcrumbs.append('⚙️ Strategy Editor')
            
        elif current_page == 'strategy_comparison':
            breadcrumbs.append('📊 Strategy Comparison')
            # Add number of strategies being compared
            selected_strategies = st.session_state.get('selected_for_compare', [])
            if selected_strategies:
                breadcrumbs.append(f"🔍 {len(selected_strategies)} Strategies")
        
        return breadcrumbs
    
    def _get_system_breadcrumbs(self, current_page: str) -> List[str]:
        """
        Get breadcrumbs for system section pages.
        
        Extracted from dashboard.py lines 2635-2637
        """
        breadcrumbs = []
        
        if current_page == 'system_status':
            breadcrumbs.append('⚙️ System Status')
        elif current_page == 'database_admin':
            breadcrumbs.append('🗄️ Database Admin')
        elif current_page == 'user_settings':
            breadcrumbs.append('👤 User Settings')
        
        return breadcrumbs
    
    def _get_selected_portfolio_name(self) -> Optional[str]:
        """Get the name of the currently selected portfolio."""
        # Check multiple possible locations for selected portfolio
        selected_portfolio = (st.session_state.get('selected_portfolio') or 
                            st.session_state.get('selected_portfolio_for_pv'))
        
        if selected_portfolio and selected_portfolio in st.session_state.get('portfolios', {}):
            portfolio_data = st.session_state.portfolios[selected_portfolio]
            return portfolio_data.get('name', selected_portfolio)
        
        return None
    
    def _get_current_analysis_name(self) -> Optional[str]:
        """Get the name of the currently selected analysis."""
        current_analysis = st.session_state.get('current_analysis')
        if current_analysis and isinstance(current_analysis, dict):
            return current_analysis.get('name')
        return None
    
    def render_breadcrumbs(self, style: str = "default") -> None:
        """
        Render breadcrumb navigation trail.
        
        Args:
            style: Rendering style ('default', 'minimal', 'detailed')
        """
        breadcrumbs = self.generate_breadcrumbs()
        
        if not breadcrumbs:
            return
        
        if style == "minimal":
            self._render_minimal_breadcrumbs(breadcrumbs)
        elif style == "detailed":
            self._render_detailed_breadcrumbs(breadcrumbs)
        else:
            self._render_default_breadcrumbs(breadcrumbs)
    
    def _render_default_breadcrumbs(self, breadcrumbs: List[str]) -> None:
        """
        Render default breadcrumb style.
        
        Extracted from dashboard.py lines 2642-2645
        """
        breadcrumb_text = " → ".join(breadcrumbs)
        st.markdown(
            f"<div style='font-size: 14px; color: #8e8ea0; margin-bottom: 10px; padding: 5px 0;'>{breadcrumb_text}</div>", 
            unsafe_allow_html=True
        )
    
    def _render_minimal_breadcrumbs(self, breadcrumbs: List[str]) -> None:
        """Render minimal breadcrumb style."""
        if len(breadcrumbs) > 1:
            current_page = breadcrumbs[-1]
            st.caption(f"📍 {current_page}")
    
    def _render_detailed_breadcrumbs(self, breadcrumbs: List[str]) -> None:
        """Render detailed breadcrumb style with navigation links."""
        if not breadcrumbs:
            return
        
        # Create columns for each breadcrumb level
        cols = st.columns(len(breadcrumbs))
        
        for i, (breadcrumb, col) in enumerate(zip(breadcrumbs, cols)):
            with col:
                if i == len(breadcrumbs) - 1:
                    # Current page - no link
                    st.markdown(f"**{breadcrumb}**")
                else:
                    # Clickable breadcrumb (placeholder - could be implemented with navigation)
                    st.markdown(breadcrumb)
    
    def get_page_context(self) -> Dict[str, Any]:
        """Get detailed page context information for breadcrumbs."""
        current_page = self.router.get_current_page()
        current_section = self.router.get_current_section()
        
        page_config = self.config.get_page_config(current_page)
        section_config = self.config.get_section(current_section)
        
        context = {
            'current_page': current_page,
            'current_section': current_section,
            'page_config': page_config,
            'section_config': section_config,
            'breadcrumbs': self.generate_breadcrumbs()
        }
        
        # Add portfolio context if relevant
        if self.config.requires_portfolio(current_page) or current_page in ['portfolio', 'pv_analysis']:
            context['portfolio_name'] = self._get_selected_portfolio_name()
            context['requires_portfolio'] = True
        
        # Add equity context if relevant
        if current_page == 'equity_analysis':
            equity_context = st.session_state.get('equity_context', {})
            context['equity_context'] = equity_context
        
        # Add analysis context if relevant
        if current_page == 'pv_analysis':
            context['analysis_name'] = self._get_current_analysis_name()
        
        return context
    
    def update_breadcrumb_trail(self, page_key: str, **context) -> None:
        """
        Update breadcrumb trail for dynamic page changes.
        
        Args:
            page_key: Current page
            **context: Additional context information
        """
        # Store context for breadcrumb generation
        if 'breadcrumb_context' not in st.session_state:
            st.session_state.breadcrumb_context = {}
        
        st.session_state.breadcrumb_context[page_key] = context
    
    def get_breadcrumb_navigation_data(self) -> Dict[str, Any]:
        """Get structured data for breadcrumb navigation."""
        breadcrumbs = self.generate_breadcrumbs()
        context = self.get_page_context()
        
        return {
            'breadcrumbs': breadcrumbs,
            'context': context,
            'navigation_trail': self.router.get_navigation_history(),
            'can_go_back': self.router.can_go_back(),
            'generated_at': st.session_state.get('navigation', {}).get('last_navigation')
        }
    
    def render_navigation_summary(self) -> None:
        """Render a summary of current navigation state."""
        context = self.get_page_context()
        
        with st.expander("🧭 Navigation Summary", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Current Location:**")
                breadcrumbs = self.generate_breadcrumbs()
                for i, breadcrumb in enumerate(breadcrumbs):
                    indent = "  " * i
                    st.markdown(f"{indent}• {breadcrumb}")
            
            with col2:
                st.markdown("**Page Info:**")
                if context['page_config']:
                    st.markdown(f"**Page:** {context['page_config']['label']}")
                    st.markdown(f"**Section:** {context['section_config']['label']}")
                    if context['page_config'].get('description'):
                        st.caption(context['page_config']['description'])


# Global breadcrumb manager instance
_breadcrumb_instance = None

def get_breadcrumb_manager() -> BreadcrumbManager:
    """Get global breadcrumb manager instance (singleton)."""
    global _breadcrumb_instance
    if _breadcrumb_instance is None:
        _breadcrumb_instance = BreadcrumbManager()
    return _breadcrumb_instance

def generate_breadcrumbs() -> List[str]:
    """Generate breadcrumb trail based on current navigation state."""
    return get_breadcrumb_manager().generate_breadcrumbs()

def render_breadcrumbs(style: str = "default") -> None:
    """Render breadcrumb navigation trail."""
    return get_breadcrumb_manager().render_breadcrumbs(style)

def get_page_context() -> Dict[str, Any]:
    """Get detailed page context information for breadcrumbs."""
    return get_breadcrumb_manager().get_page_context()

def update_breadcrumb_trail(page_key: str, **context) -> None:
    """Update breadcrumb trail for dynamic page changes."""
    return get_breadcrumb_manager().update_breadcrumb_trail(page_key, **context)