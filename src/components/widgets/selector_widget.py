"""
Selector Widget Components.

Widgets for selection, filtering, and navigation.
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Union, Callable
import logging

from .base_widget import BaseWidget

logger = logging.getLogger(__name__)


class SelectorWidget(BaseWidget):
    """
    Base selector widget with options and callbacks.
    """
    
    def __init__(self, widget_id: str, options: List[Any], 
                 default_option: Any = None, title: str = "", 
                 format_func: Callable = None):
        """
        Initialize selector widget.
        
        Args:
            widget_id: Unique widget identifier
            options: List of options to select from
            default_option: Default selected option
            title: Widget title
            format_func: Function to format option display
        """
        super().__init__(widget_id, title)
        self.options = options
        self.default_option = default_option
        self.format_func = format_func or str
    
    def render_content(self) -> Dict[str, Any]:
        """
        Render selector content.
        
        Returns:
            Widget render data with selected option
        """
        try:
            if not self.options:
                st.info("No options available")
                return {'selected': None}
            
            # Get default index
            default_index = 0
            if self.default_option in self.options:
                default_index = self.options.index(self.default_option)
            
            selected = st.selectbox(
                self.title,
                options=self.options,
                index=default_index,
                format_func=self.format_func,
                key=self.state_key
            )
            
            return {
                'widget_type': 'selector',
                'selected': selected,
                'options_count': len(self.options)
            }
            
        except Exception as e:
            logger.error(f"Error rendering selector widget {self.widget_id}: {e}")
            st.error("Error displaying selector")
            return {'selected': None}


class PortfolioSelectorWidget(BaseWidget):
    """
    Widget for selecting portfolios with filtering and search.
    """
    
    def __init__(self, widget_id: str, portfolios: List[Dict[str, Any]], 
                 title: str = "Select Portfolio", multi_select: bool = False,
                 show_filters: bool = True):
        """
        Initialize portfolio selector widget.
        
        Args:
            widget_id: Unique widget identifier
            portfolios: List of portfolio dictionaries
            title: Widget title
            multi_select: Allow multiple selection
            show_filters: Show filter options
        """
        super().__init__(widget_id, title)
        self.portfolios = portfolios
        self.multi_select = multi_select
        self.show_filters = show_filters
    
    def render_content(self) -> Dict[str, Any]:
        """
        Render portfolio selector content.
        
        Returns:
            Widget render data with selected portfolios
        """
        try:
            if not self.portfolios:
                st.info("No portfolios available")
                return {'selected_portfolios': []}
            
            filtered_portfolios = self.portfolios.copy()
            
            # Show filters if enabled
            if self.show_filters and len(self.portfolios) > 3:
                filtered_portfolios = self._render_filters()
            
            if not filtered_portfolios:
                st.info("No portfolios match the selected filters")
                return {'selected_portfolios': []}
            
            # Portfolio selection
            if self.multi_select:
                selected_ids = st.multiselect(
                    self.title,
                    options=[p['portfolio_id'] for p in filtered_portfolios],
                    format_func=lambda x: self._format_portfolio_option(x, filtered_portfolios),
                    key=f"{self.state_key}_multiselect"
                )
                selected_portfolios = [p for p in filtered_portfolios if p['portfolio_id'] in selected_ids]
            else:
                selected_id = st.selectbox(
                    self.title,
                    options=[p['portfolio_id'] for p in filtered_portfolios],
                    format_func=lambda x: self._format_portfolio_option(x, filtered_portfolios),
                    key=f"{self.state_key}_selectbox"
                )
                selected_portfolios = [p for p in filtered_portfolios if p['portfolio_id'] == selected_id] if selected_id else []
            
            # Show selection summary
            if selected_portfolios:
                with st.expander("📋 Selected Portfolios", expanded=False):
                    for portfolio in selected_portfolios:
                        col1, col2, col3 = st.columns([2, 2, 1])
                        with col1:
                            st.write(f"**{portfolio['portfolio_id']}**")
                        with col2:
                            st.write(portfolio.get('name', 'Unknown'))
                        with col3:
                            st.write(portfolio.get('currency', 'HKD'))
            
            return {
                'widget_type': 'portfolio_selector',
                'selected_portfolios': selected_portfolios,
                'selected_ids': [p['portfolio_id'] for p in selected_portfolios],
                'filtered_count': len(filtered_portfolios)
            }
            
        except Exception as e:
            logger.error(f"Error rendering portfolio selector widget {self.widget_id}: {e}")
            st.error("Error displaying portfolio selector")
            return {'selected_portfolios': []}
    
    def _render_filters(self) -> List[Dict[str, Any]]:
        """
        Render filter controls and return filtered portfolios.
        
        Returns:
            Filtered portfolio list
        """
        try:
            with st.expander("🔍 Filters", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                # Currency filter
                with col1:
                    all_currencies = ['All'] + list(set(p.get('currency', 'HKD') for p in self.portfolios))
                    selected_currency = st.selectbox(
                        "Currency:",
                        options=all_currencies,
                        key=f"{self.state_key}_currency_filter"
                    )
                
                # Status filter
                with col2:
                    selected_status = st.selectbox(
                        "Status:",
                        options=['All', 'Active', 'Inactive'],
                        key=f"{self.state_key}_status_filter"
                    )
                
                # Search filter
                with col3:
                    search_term = st.text_input(
                        "Search:",
                        placeholder="Name or ID",
                        key=f"{self.state_key}_search"
                    )
            
            # Apply filters
            filtered = self.portfolios.copy()
            
            if selected_currency != 'All':
                filtered = [p for p in filtered if p.get('currency', 'HKD') == selected_currency]
            
            if selected_status != 'All':
                is_active = selected_status == 'Active'
                filtered = [p for p in filtered if p.get('is_active', True) == is_active]
            
            if search_term:
                search_lower = search_term.lower()
                filtered = [p for p in filtered 
                           if search_lower in p.get('portfolio_id', '').lower() 
                           or search_lower in p.get('name', '').lower()]
            
            return filtered
            
        except Exception as e:
            logger.error(f"Error rendering portfolio filters: {e}")
            return self.portfolios
    
    def _format_portfolio_option(self, portfolio_id: str, portfolios: List[Dict[str, Any]]) -> str:
        """
        Format portfolio option for display.
        
        Args:
            portfolio_id: Portfolio ID
            portfolios: List of portfolios
            
        Returns:
            Formatted display string
        """
        portfolio = next((p for p in portfolios if p['portfolio_id'] == portfolio_id), None)
        if not portfolio:
            return portfolio_id
        
        name = portfolio.get('name', 'Unknown')
        currency = portfolio.get('currency', 'HKD')
        status = "🟢" if portfolio.get('is_active', True) else "🔴"
        
        return f"{status} {portfolio_id} - {name} ({currency})"


class SymbolSelectorWidget(BaseWidget):
    """
    Widget for selecting stock symbols with search and filtering.
    """
    
    def __init__(self, widget_id: str, symbols: List[Dict[str, str]], 
                 title: str = "Select Symbol", multi_select: bool = False):
        """
        Initialize symbol selector widget.
        
        Args:
            widget_id: Unique widget identifier
            symbols: List of symbol dictionaries with 'symbol', 'name', 'sector'
            title: Widget title
            multi_select: Allow multiple selection
        """
        super().__init__(widget_id, title)
        self.symbols = symbols
        self.multi_select = multi_select
    
    def render_content(self) -> Dict[str, Any]:
        """
        Render symbol selector content.
        
        Returns:
            Widget render data with selected symbols
        """
        try:
            if not self.symbols:
                st.info("No symbols available")
                return {'selected_symbols': []}
            
            # Search and filter
            col1, col2 = st.columns([2, 1])
            
            with col1:
                search_term = st.text_input(
                    "Search symbols:",
                    placeholder="Symbol or company name",
                    key=f"{self.state_key}_search"
                )
            
            with col2:
                # Sector filter
                all_sectors = ['All'] + list(set(s.get('sector', 'Other') for s in self.symbols))
                selected_sector = st.selectbox(
                    "Sector:",
                    options=all_sectors,
                    key=f"{self.state_key}_sector"
                )
            
            # Apply filters
            filtered_symbols = self._apply_symbol_filters(search_term, selected_sector)
            
            if not filtered_symbols:
                st.info("No symbols match your criteria")
                return {'selected_symbols': []}
            
            # Symbol selection
            if self.multi_select:
                selected_symbol_codes = st.multiselect(
                    self.title,
                    options=[s['symbol'] for s in filtered_symbols],
                    format_func=lambda x: self._format_symbol_option(x, filtered_symbols),
                    key=f"{self.state_key}_multiselect"
                )
                selected_symbols = [s for s in filtered_symbols if s['symbol'] in selected_symbol_codes]
            else:
                selected_symbol_code = st.selectbox(
                    self.title,
                    options=[s['symbol'] for s in filtered_symbols],
                    format_func=lambda x: self._format_symbol_option(x, filtered_symbols),
                    key=f"{self.state_key}_selectbox"
                )
                selected_symbols = [s for s in filtered_symbols if s['symbol'] == selected_symbol_code] if selected_symbol_code else []
            
            return {
                'widget_type': 'symbol_selector',
                'selected_symbols': selected_symbols,
                'selected_codes': [s['symbol'] for s in selected_symbols],
                'filtered_count': len(filtered_symbols)
            }
            
        except Exception as e:
            logger.error(f"Error rendering symbol selector widget {self.widget_id}: {e}")
            st.error("Error displaying symbol selector")
            return {'selected_symbols': []}
    
    def _apply_symbol_filters(self, search_term: str, selected_sector: str) -> List[Dict[str, str]]:
        """Apply search and sector filters to symbols."""
        filtered = self.symbols.copy()
        
        # Search filter
        if search_term:
            search_lower = search_term.lower()
            filtered = [s for s in filtered
                       if search_lower in s.get('symbol', '').lower()
                       or search_lower in s.get('name', '').lower()]
        
        # Sector filter
        if selected_sector != 'All':
            filtered = [s for s in filtered if s.get('sector', 'Other') == selected_sector]
        
        return filtered
    
    def _format_symbol_option(self, symbol: str, symbols: List[Dict[str, str]]) -> str:
        """Format symbol option for display."""
        symbol_data = next((s for s in symbols if s['symbol'] == symbol), None)
        if not symbol_data:
            return symbol
        
        name = symbol_data.get('name', 'Unknown')
        sector = symbol_data.get('sector', 'Other')
        
        # Truncate long names
        if len(name) > 30:
            name = name[:27] + "..."
        
        return f"{symbol} - {name} ({sector})"


class AnalysisSelectorWidget(BaseWidget):
    """
    Widget for selecting portfolio analyses with date information.
    """
    
    def __init__(self, widget_id: str, analyses: List[Dict[str, Any]], 
                 title: str = "Select Analysis", max_selection: int = None):
        """
        Initialize analysis selector widget.
        
        Args:
            widget_id: Unique widget identifier
            analyses: List of analysis dictionaries
            title: Widget title
            max_selection: Maximum number of analyses to select
        """
        super().__init__(widget_id, title)
        self.analyses = analyses
        self.max_selection = max_selection
    
    def render_content(self) -> Dict[str, Any]:
        """
        Render analysis selector content.
        
        Returns:
            Widget render data with selected analyses
        """
        try:
            if not self.analyses:
                st.info("No analyses available")
                return {'selected_analyses': []}
            
            # Sort analyses by date (newest first)
            sorted_analyses = sorted(
                self.analyses, 
                key=lambda x: x.get('analysis_date', ''), 
                reverse=True
            )
            
            help_text = f"Select up to {self.max_selection} analyses" if self.max_selection else None
            
            selected_ids = st.multiselect(
                self.title,
                options=[str(a['analysis_id']) for a in sorted_analyses],
                format_func=lambda x: self._format_analysis_option(x, sorted_analyses),
                help=help_text,
                key=f"{self.state_key}_multiselect"
            )
            
            # Validate max selection
            if self.max_selection and len(selected_ids) > self.max_selection:
                st.warning(f"Maximum {self.max_selection} analyses allowed. Only the first {self.max_selection} will be used.")
                selected_ids = selected_ids[:self.max_selection]
            
            selected_analyses = [a for a in sorted_analyses if str(a['analysis_id']) in selected_ids]
            
            # Show selection details
            if selected_analyses:
                with st.expander("📊 Selected Analyses", expanded=False):
                    for analysis in selected_analyses:
                        col1, col2, col3 = st.columns([1, 2, 2])
                        with col1:
                            st.write(f"**#{analysis['analysis_id']}**")
                        with col2:
                            st.write(f"📅 {analysis.get('analysis_date', 'Unknown date')}")
                        with col3:
                            portfolio_name = analysis.get('portfolio_name', 'Unknown portfolio')
                            st.write(f"📁 {portfolio_name}")
            
            return {
                'widget_type': 'analysis_selector',
                'selected_analyses': selected_analyses,
                'selected_ids': [int(a['analysis_id']) for a in selected_analyses],
                'total_count': len(self.analyses)
            }
            
        except Exception as e:
            logger.error(f"Error rendering analysis selector widget {self.widget_id}: {e}")
            st.error("Error displaying analysis selector")
            return {'selected_analyses': []}
    
    def _format_analysis_option(self, analysis_id: str, analyses: List[Dict[str, Any]]) -> str:
        """Format analysis option for display."""
        analysis = next((a for a in analyses if str(a['analysis_id']) == analysis_id), None)
        if not analysis:
            return analysis_id
        
        date = analysis.get('analysis_date', 'Unknown date')
        portfolio_name = analysis.get('portfolio_name', 'Unknown')
        
        return f"#{analysis_id} - {date} ({portfolio_name})"


class NavigationWidget(BaseWidget):
    """
    Widget for navigation between pages or sections.
    """
    
    def __init__(self, widget_id: str, navigation_items: List[Dict[str, str]], 
                 title: str = "Navigation", orientation: str = "horizontal"):
        """
        Initialize navigation widget.
        
        Args:
            widget_id: Unique widget identifier
            navigation_items: List of navigation items with 'key', 'label', 'icon'
            title: Widget title
            orientation: Layout orientation ('horizontal' or 'vertical')
        """
        super().__init__(widget_id, title)
        self.navigation_items = navigation_items
        self.orientation = orientation
    
    def render_content(self) -> Dict[str, Any]:
        """
        Render navigation content.
        
        Returns:
            Widget render data with selected navigation
        """
        try:
            if not self.navigation_items:
                return {'selected': None}
            
            current_selection = self.get_state('selected')
            
            if self.orientation == "horizontal":
                cols = st.columns(len(self.navigation_items))
                
                for i, item in enumerate(self.navigation_items):
                    with cols[i]:
                        button_type = "primary" if current_selection == item['key'] else "secondary"
                        icon = item.get('icon', '')
                        label = f"{icon} {item['label']}" if icon else item['label']
                        
                        if st.button(label, key=f"{self.state_key}_{item['key']}", type=button_type):
                            self.set_state('selected', item['key'])
                            current_selection = item['key']
            else:
                # Vertical layout
                for item in self.navigation_items:
                    button_type = "primary" if current_selection == item['key'] else "secondary"
                    icon = item.get('icon', '')
                    label = f"{icon} {item['label']}" if icon else item['label']
                    
                    if st.button(label, key=f"{self.state_key}_{item['key']}", 
                               type=button_type, use_container_width=True):
                        self.set_state('selected', item['key'])
                        current_selection = item['key']
            
            return {
                'widget_type': 'navigation',
                'selected': current_selection,
                'items_count': len(self.navigation_items)
            }
            
        except Exception as e:
            logger.error(f"Error rendering navigation widget {self.widget_id}: {e}")
            st.error("Error displaying navigation")
            return {'selected': None}