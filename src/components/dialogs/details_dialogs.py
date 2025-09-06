"""
Details Display Dialog Components.

Modal dialogs for displaying position and portfolio details.
Extracted from dashboard.py lines 621-680 and 682-741.
"""

from typing import Dict, Any, Optional, List
import streamlit as st

from .base_dialog import BaseDialog, dialog_component


@dialog_component("Total Positions Details", width="large")
class TotalPositionsDialog(BaseDialog):
    """Dialog for showing all unique symbols across portfolios."""
    
    def __init__(self, symbol_details: Dict[str, Any]):
        """
        Initialize total positions dialog.
        
        Args:
            symbol_details: Dict of symbol -> details mapping
        """
        super().__init__("Total Positions Details", width="large")
        self.symbol_details = symbol_details
    
    def render_content(self) -> Optional[Dict[str, Any]]:
        """Render total positions dialog content."""
        st.markdown("**All unique symbols across your portfolios**")
        st.markdown("---")
        
        if not self.symbol_details:
            st.info("No symbols found in any portfolio.")
            if st.button("🔙 Back", use_container_width=True):
                return {'action': 'back'}
            return None
        
        # Create sorted list for display
        symbols_list = self._prepare_symbols_data()
        
        # Display summary
        st.info(f"📊 **Total Unique Symbols:** {len(symbols_list)}")
        
        # Display table
        self._render_symbols_table(symbols_list, "📋 Symbol Details")
        
        st.markdown("---")
        
        # Back button
        if st.button("🔙 Back", use_container_width=True):
            return {'action': 'back'}
        
        return None
    
    def _prepare_symbols_data(self) -> List[Dict[str, str]]:
        """Prepare symbols data for display."""
        symbols_list = []
        for symbol, details in self.symbol_details.items():
            symbols_list.append({
                "Symbol": symbol,
                "Company Name": details.get('company_name', 'Unknown'),
                "Sector": details.get('sector', 'Other')
            })
        
        # Sort by symbol
        symbols_list.sort(key=lambda x: x['Symbol'])
        return symbols_list
    
    def _render_symbols_table(self, symbols_list: List[Dict[str, str]], title: str) -> None:
        """Render symbols table."""
        st.markdown(f"### {title}")
        
        # Create table header
        header_cols = st.columns([1, 2.5, 1.5])
        with header_cols[0]:
            st.markdown("**Symbol**")
        with header_cols[1]:
            st.markdown("**Company Name**")
        with header_cols[2]:
            st.markdown("**Sector**")
        
        st.markdown("---")
        
        # Display rows
        for symbol_data in symbols_list:
            row_cols = st.columns([1, 2.5, 1.5])
            with row_cols[0]:
                st.write(symbol_data["Symbol"])
            with row_cols[1]:
                # Truncate long company names
                company_name = symbol_data["Company Name"]
                if len(company_name) > 35:
                    company_name = company_name[:32] + "..."
                st.write(company_name)
            with row_cols[2]:
                st.write(symbol_data["Sector"])
    
    def on_submit(self, data: Dict[str, Any]) -> bool:
        """Handle dialog submission."""
        try:
            if data['action'] == 'back':
                st.rerun()
                return True
            return False
        except Exception as e:
            self.show_error(f"Error: {str(e)}")
            return False


@dialog_component("Active Positions Details", width="large")
class ActivePositionsDialog(BaseDialog):
    """Dialog for showing only active symbols (quantity > 0)."""
    
    def __init__(self, active_symbol_details: Dict[str, Any]):
        """
        Initialize active positions dialog.
        
        Args:
            active_symbol_details: Dict of active symbol -> details mapping
        """
        super().__init__("Active Positions Details", width="large")
        self.active_symbol_details = active_symbol_details
    
    def render_content(self) -> Optional[Dict[str, Any]]:
        """Render active positions dialog content."""
        st.markdown("**Active symbols with holdings > 0**")
        st.markdown("---")
        
        if not self.active_symbol_details:
            st.info("No active positions found.")
            if st.button("🔙 Back", use_container_width=True):
                return {'action': 'back'}
            return None
        
        # Create sorted list for display
        active_symbols_list = self._prepare_active_symbols_data()
        
        # Display summary
        st.info(f"📊 **Active Positions:** {len(active_symbols_list)}")
        
        # Display table
        self._render_symbols_table(active_symbols_list, "📋 Active Symbol Details")
        
        st.markdown("---")
        
        # Back button
        if st.button("🔙 Back", use_container_width=True):
            return {'action': 'back'}
        
        return None
    
    def _prepare_active_symbols_data(self) -> List[Dict[str, str]]:
        """Prepare active symbols data for display."""
        active_symbols_list = []
        for symbol, details in self.active_symbol_details.items():
            active_symbols_list.append({
                "Symbol": symbol,
                "Company Name": details.get('company_name', 'Unknown'),
                "Sector": details.get('sector', 'Other')
            })
        
        # Sort by symbol
        active_symbols_list.sort(key=lambda x: x['Symbol'])
        return active_symbols_list
    
    def _render_symbols_table(self, symbols_list: List[Dict[str, str]], title: str) -> None:
        """Render symbols table."""
        st.markdown(f"### {title}")
        
        # Create table header
        header_cols = st.columns([1, 2.5, 1.5])
        with header_cols[0]:
            st.markdown("**Symbol**")
        with header_cols[1]:
            st.markdown("**Company Name**")
        with header_cols[2]:
            st.markdown("**Sector**")
        
        st.markdown("---")
        
        # Display rows
        for symbol_data in symbols_list:
            row_cols = st.columns([1, 2.5, 1.5])
            with row_cols[0]:
                st.write(symbol_data["Symbol"])
            with row_cols[1]:
                # Truncate long company names
                company_name = symbol_data["Company Name"]
                if len(company_name) > 35:
                    company_name = company_name[:32] + "..."
                st.write(company_name)
            with row_cols[2]:
                st.write(symbol_data["Sector"])
    
    def on_submit(self, data: Dict[str, Any]) -> bool:
        """Handle dialog submission."""
        try:
            if data['action'] == 'back':
                st.rerun()
                return True
            return False
        except Exception as e:
            self.show_error(f"Error: {str(e)}")
            return False


# Convenience functions for displaying dialogs
def show_total_positions_dialog(symbol_details: Dict[str, Any]):
    """Show the total positions dialog."""
    dialog = TotalPositionsDialog(symbol_details)
    return dialog._streamlit_dialog(symbol_details)


def show_active_positions_dialog(active_symbol_details: Dict[str, Any]):
    """Show the active positions dialog."""
    dialog = ActivePositionsDialog(active_symbol_details)
    return dialog._streamlit_dialog(active_symbol_details)