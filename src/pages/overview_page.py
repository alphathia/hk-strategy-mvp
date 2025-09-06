"""
Overview Page for HK Strategy Dashboard.
Displays portfolio overview, statistics, and portfolio management interface.

Extracted from dashboard.py lines 4883-5210.
"""

import streamlit as st
import copy
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime

from src.pages.base_page import BasePage

# Setup logging
logger = logging.getLogger(__name__)


class OverviewPage(BasePage):
    """Overview page showing all portfolios management and statistics."""
    
    def __init__(self):
        super().__init__('overview')
    
    def _render_content(self) -> None:
        """Render the overview page content."""
        st.subheader("📋 All Portfolios Management")
        
        # Render portfolio statistics
        self._render_portfolio_statistics()
        
        st.markdown("---")
        
        # Render portfolio overview table
        self._render_portfolio_overview_table()
        
        # Navigation hint
        st.markdown("---")
        st.info("💡 Use the navigation dropdown to view individual portfolios or check system status")
    
    def _render_portfolio_statistics(self) -> None:
        """Render portfolio statistics section."""
        # Get portfolios from session state
        portfolios = st.session_state.get('portfolios', {})
        total_portfolios = len(portfolios)
        
        if not portfolios:
            st.warning("No portfolios found. Create a portfolio to get started.")
            if st.button("➕ Create New Portfolio", type="primary"):
                self._show_create_portfolio_dialog()
            return
        
        # Calculate unique symbols statistics
        unique_symbols_data = self._calculate_unique_symbols(portfolios)
        total_positions = len(unique_symbols_data['all_unique_symbols'])
        active_positions = len(unique_symbols_data['active_unique_symbols'])
        
        # Show debug information
        self._render_debug_info(unique_symbols_data)
        
        # Custom CSS for metrics
        st.markdown("""
        <style>
        .clickable-metric {
            background: white;
            border: 1px solid #d4d4d4;
            border-radius: 4px;
            padding: 1rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s ease;
            height: 100px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }
        .clickable-metric:hover {
            background: #f8f9fa;
            border-color: #007bff;
            box-shadow: 0 2px 4px rgba(0,123,255,0.1);
        }
        .metric-value {
            font-size: 2rem;
            font-weight: 600;
            color: #1f77b4;
            margin: 0;
        }
        .metric-label {
            font-size: 0.9rem;
            color: #666;
            margin: 0.25rem 0 0 0;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Render metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Portfolios", total_portfolios, help="Number of portfolios in your system")
        with col2:
            if st.button(f"**{total_positions}**\n\nTotal Positions", 
                        key="total_positions_btn", 
                        help="Click to view all unique symbols",
                        use_container_width=True):
                self._show_total_positions_dialog(unique_symbols_data['all_symbol_details'])
        with col3:
            if st.button(f"**{active_positions}**\n\nActive Positions", 
                        key="active_positions_btn", 
                        help="Click to view active symbols only",
                        use_container_width=True):
                self._show_active_positions_dialog(unique_symbols_data['active_symbol_details'])
    
    def _calculate_unique_symbols(self, portfolios: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate unique symbols statistics across all portfolios."""
        debug_info = []
        all_positions_count = 0
        active_positions_count = 0
        inactive_positions_count = 0
        
        # Collect unique symbols with details across all portfolios
        all_unique_symbols = set()
        active_unique_symbols = set()
        all_symbol_details = {}
        active_symbol_details = {}
        
        for portfolio_id, portfolio_data in portfolios.items():
            positions = portfolio_data.get('positions', [])
            portfolio_total = len(positions)
            portfolio_active = len([pos for pos in positions if pos.get('quantity', 0) > 0])
            portfolio_inactive = portfolio_total - portfolio_active
            
            debug_info.append(f"{portfolio_id}: {portfolio_total} total ({portfolio_active} active, {portfolio_inactive} inactive)")
            all_positions_count += portfolio_total
            active_positions_count += portfolio_active
            inactive_positions_count += portfolio_inactive
            
            # Add unique symbols with details
            for pos in positions:
                symbol = pos.get('symbol', '')
                if not symbol:
                    continue
                    
                all_unique_symbols.add(symbol)
                
                # Store symbol details (use first occurrence if symbol appears in multiple portfolios)
                if symbol not in all_symbol_details:
                    all_symbol_details[symbol] = {
                        'company_name': pos.get('company_name', 'Unknown'),
                        'sector': pos.get('sector', 'Other')
                    }
                
                if pos.get('quantity', 0) > 0:
                    active_unique_symbols.add(symbol)
                    if symbol not in active_symbol_details:
                        active_symbol_details[symbol] = {
                            'company_name': pos.get('company_name', 'Unknown'),
                            'sector': pos.get('sector', 'Other')
                        }
        
        return {
            'debug_info': debug_info,
            'all_positions_count': all_positions_count,
            'active_positions_count': active_positions_count,
            'inactive_positions_count': inactive_positions_count,
            'all_unique_symbols': all_unique_symbols,
            'active_unique_symbols': active_unique_symbols,
            'all_symbol_details': all_symbol_details,
            'active_symbol_details': active_symbol_details
        }
    
    def _render_debug_info(self, symbols_data: Dict[str, Any]) -> None:
        """Render debug information about position counting."""
        with st.expander("📊 Position Count Breakdown (Debug)", expanded=False):
            st.write("**Detailed position breakdown by portfolio:**")
            for info in symbols_data['debug_info']:
                st.write(f"- {info}")
            
            st.write("**Summary:**")
            st.write(f"- Total Position Entries: {symbols_data['all_positions_count']}")
            st.write(f"- Active Positions: {symbols_data['active_positions_count']}")
            st.write(f"- Inactive Positions (qty=0): {symbols_data['inactive_positions_count']}")
            
            # Show the difference between old method and new method
            st.write(f"- **NEW METHOD (Displayed Above):** Unique Symbols: {len(symbols_data['all_unique_symbols'])} total, {len(symbols_data['active_unique_symbols'])} active")
            st.write(f"- **OLD METHOD:** Position Entries: {symbols_data['all_positions_count']} total, {symbols_data['active_positions_count']} active")
            st.write(f"- **Difference:** The new method eliminates duplicate symbols across portfolios")
    
    def _render_portfolio_overview_table(self) -> None:
        """Render the interactive portfolio overview table."""
        st.subheader("📊 Portfolio Overview")
        
        portfolios = st.session_state.get('portfolios', {})
        if not portfolios:
            st.info("No portfolios to display.")
            return
        
        # Generate overview data
        overview_data = self._generate_overview_data(portfolios)
        
        # Table header with create button
        table_header_col1, table_header_col2 = st.columns([3, 1])
        with table_header_col1:
            st.markdown("### 📋 Interactive Portfolio Table")
        with table_header_col2:
            if st.button("➕ Create New Portfolio", type="primary", use_container_width=True):
                self._show_create_portfolio_dialog()
        
        # CSS styling for clickable portfolio names
        st.markdown("""
        <style>
        div[data-testid="column"] > div[data-testid="stButton"] > button[kind="secondary"] {
            background: transparent !important;
            border: none !important;
            padding: 4px 8px !important;
            color: #1f77b4 !important;
            text-decoration: underline !important;
            font-weight: normal !important;
            text-align: left !important;
            width: 100% !important;
        }
        div[data-testid="column"] > div[data-testid="stButton"] > button[kind="secondary"]:hover {
            color: #0d5aa7 !important;
            background-color: #f0f8ff !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Render table
        self._render_table_header()
        st.markdown("---")
        self._render_table_rows(overview_data)
    
    def _generate_overview_data(self, portfolios: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate overview data for all portfolios."""
        overview_data = []
        
        for portfolio_id, portfolio_info in portfolios.items():
            positions = portfolio_info.get('positions', [])
            active_pos = [pos for pos in positions if pos.get('quantity', 0) > 0]
            
            # Calculate total value
            total_val = self._calculate_portfolio_value(portfolio_id, active_pos)
            
            # Get last update timestamp
            last_update_str = self._get_last_update_string(portfolio_id)
            
            overview_data.append({
                "Name": portfolio_info.get('name', 'Unnamed Portfolio'),
                "Description": self._truncate_description(portfolio_info.get('description', '')),
                "All Positions": len(positions),
                "Active": len(active_pos),
                "Value": f"HK${total_val:,.0f}",
                "Last Updated": last_update_str,
                "Portfolio ID": portfolio_id
            })
        
        return overview_data
    
    def _calculate_portfolio_value(self, portfolio_id: str, active_positions: List[Dict[str, Any]]) -> float:
        """Calculate total portfolio value."""
        total_val = 0
        
        for pos in active_positions:
            symbol = pos.get('symbol', '')
            quantity = pos.get('quantity', 0)
            
            # Get price from session state or use default
            price = self._get_symbol_price(portfolio_id, symbol)
            total_val += price * quantity
        
        return total_val
    
    def _get_symbol_price(self, portfolio_id: str, symbol: str) -> float:
        """Get symbol price from session state or use default."""
        portfolio_prices = st.session_state.get('portfolio_prices', {})
        
        if (portfolio_id in portfolio_prices and 
            symbol in portfolio_prices[portfolio_id]):
            return portfolio_prices[portfolio_id][symbol]
        
        # Default prices for common HK stocks
        default_prices = {
            "0005.HK": 39.75, "0316.HK": 98.20, "0388.HK": 285.50, "0700.HK": 315.20,
            "0823.HK": 44.15, "0939.HK": 5.52, "1810.HK": 13.45, "2888.HK": 148.20,
            "3690.HK": 98.50, "9618.HK": 130.10, "9988.HK": 118.75
        }
        
        return default_prices.get(symbol, 50.0)
    
    def _get_last_update_string(self, portfolio_id: str) -> str:
        """Get formatted last update string for portfolio."""
        last_update = st.session_state.get('portfolio_timestamps', {}).get(portfolio_id)
        if not last_update:
            last_update = st.session_state.get('last_update', {}).get(portfolio_id)
        
        if last_update and last_update != "Never":
            if hasattr(last_update, 'strftime'):
                return last_update.strftime('%Y-%m-%d %H:%M:%S')
            else:
                return str(last_update)
        
        return "Never"
    
    def _truncate_description(self, description: str, max_length: int = 50) -> str:
        """Truncate description if too long."""
        if len(description) > max_length:
            return description[:max_length] + "..."
        return description
    
    def _render_table_header(self) -> None:
        """Render table header."""
        header_cols = st.columns([2.5, 2.3, 1.2, 1.0, 1.5, 2, 2])
        with header_cols[0]:
            st.markdown("**Name**")
        with header_cols[1]:
            st.markdown("**Description**")
        with header_cols[2]:
            st.markdown("**All Positions**")
        with header_cols[3]:
            st.markdown("**Active**")
        with header_cols[4]:
            st.markdown("**Value**")
        with header_cols[5]:
            st.markdown("**Last Updated**")
        with header_cols[6]:
            st.markdown("**Actions**")
    
    def _render_table_rows(self, overview_data: List[Dict[str, Any]]) -> None:
        """Render table rows with action buttons."""
        for i, portfolio_data in enumerate(overview_data):
            portfolio_id = portfolio_data["Portfolio ID"]
            
            row_cols = st.columns([2.5, 2.3, 1.2, 1.0, 1.5, 2, 2])
            
            # Portfolio name (clickable)
            with row_cols[0]:
                if st.button(portfolio_data['Name'], 
                           key=f"name_click_{portfolio_id}_{i}", 
                           help=f"View {portfolio_id} dashboard",
                           use_container_width=True,
                           type="secondary"):
                    self._navigate_to_portfolio_view(portfolio_id)
            
            # Other columns
            with row_cols[1]:
                st.write(portfolio_data['Description'])
            with row_cols[2]:
                st.write(portfolio_data['All Positions'])
            with row_cols[3]:
                st.write(portfolio_data['Active'])
            with row_cols[4]:
                st.write(portfolio_data['Value'])
            with row_cols[5]:
                st.write(portfolio_data['Last Updated'])
            
            # Action buttons
            with row_cols[6]:
                self._render_action_buttons(portfolio_id, i)
            
            # Add separator between rows
            if i < len(overview_data) - 1:
                st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
    
    def _render_action_buttons(self, portfolio_id: str, row_index: int) -> None:
        """Render action buttons for each portfolio row."""
        action_button_cols = st.columns(3)
        
        # Edit button
        with action_button_cols[0]:
            if st.button("🔄", key=f"update_{portfolio_id}_{row_index}", 
                        help="Edit portfolio positions and details", 
                        use_container_width=True, type="primary"):
                self._handle_edit_portfolio(portfolio_id)
        
        # Copy button
        with action_button_cols[1]:
            if st.button("📋", key=f"copy_{portfolio_id}_{row_index}", 
                        help="Create a copy of this portfolio", 
                        use_container_width=True):
                self._show_copy_portfolio_dialog(portfolio_id)
        
        # Delete button
        with action_button_cols[2]:
            self._render_delete_button(portfolio_id, row_index)
    
    def _render_delete_button(self, portfolio_id: str, row_index: int) -> None:
        """Render delete button with confirmation."""
        confirm_key = f"confirm_delete_{portfolio_id}"
        is_confirming = st.session_state.get(confirm_key, False)
        
        button_label = "⚠️" if is_confirming else "🗑️"
        button_type = "secondary" if not is_confirming else "primary"
        help_text = "Click again to confirm deletion" if is_confirming else "Delete this portfolio"
        
        if st.button(button_label, key=f"delete_{portfolio_id}_{row_index}", 
                    help=help_text, use_container_width=True, type=button_type):
            self._handle_delete_portfolio(portfolio_id, confirm_key, is_confirming)
    
    def _navigate_to_portfolio_view(self, portfolio_id: str) -> None:
        """Navigate to portfolio dashboard in view mode."""
        st.session_state.current_page = 'portfolio'
        st.session_state.portfolio_switch_request = portfolio_id
        
        # Clear edit mode
        if portfolio_id in st.session_state.get('edit_mode', {}):
            st.session_state.edit_mode[portfolio_id] = False
        
        # Update navigation state
        st.session_state.navigation['section'] = 'portfolios'
        st.session_state.navigation['page'] = 'portfolio'
        
        st.success(f"👁️ Viewing {portfolio_id} dashboard...")
        st.rerun()
    
    def _handle_edit_portfolio(self, portfolio_id: str) -> None:
        """Handle portfolio edit request with analysis check."""
        # Check for portfolio analysis restrictions
        has_analyses, analysis_count, message = self._check_portfolio_has_analyses(portfolio_id)
        
        if has_analyses:
            st.error(f"🚫 **Cannot edit portfolio**: {message}")
            st.warning("⚠️ Updating portfolios that already have analyses is not allowed.")
            st.info(f"💡 **Solution**: Copy '{portfolio_id}' to a new portfolio first, then edit the copy.")
        else:
            # Navigate to portfolio dashboard in edit mode
            st.session_state.current_page = 'portfolio'
            st.session_state.portfolio_switch_request = portfolio_id
            
            # Initialize edit mode
            if 'edit_mode' not in st.session_state:
                st.session_state.edit_mode = {}
            if 'portfolio_backup' not in st.session_state:
                st.session_state.portfolio_backup = {}
                
            st.session_state.edit_mode[portfolio_id] = True
            st.session_state.portfolio_backup[portfolio_id] = copy.deepcopy(
                st.session_state.portfolios[portfolio_id]
            )
            
            # Update navigation state
            st.session_state.navigation['section'] = 'portfolios'
            st.session_state.navigation['page'] = 'portfolio'
            
            st.success(f"🔄 Opening {portfolio_id} for editing...")
            st.rerun()
    
    def _handle_delete_portfolio(self, portfolio_id: str, confirm_key: str, is_confirming: bool) -> None:
        """Handle portfolio deletion with confirmation."""
        portfolios = st.session_state.get('portfolios', {})
        
        if len(portfolios) <= 1:
            st.error("❌ Cannot delete the only portfolio!")
            return
        
        if not is_confirming:
            st.session_state[confirm_key] = True
            st.warning(f"⚠️ Click the warning icon again to permanently delete '{portfolio_id}'")
            st.rerun()
        else:
            # Actually delete the portfolio
            success = self._delete_portfolio(portfolio_id)
            if success:
                st.success(f"✅ Portfolio '{portfolio_id}' deleted!")
                # Clean up confirmation state
                if confirm_key in st.session_state:
                    del st.session_state[confirm_key]
                st.rerun()
            else:
                st.error(f"❌ Failed to delete portfolio '{portfolio_id}'")
    
    def _check_portfolio_has_analyses(self, portfolio_id: str) -> tuple[bool, int, str]:
        """Check if portfolio has associated analyses."""
        # This is a placeholder - integrate with actual analysis service
        # For now, return False (no analyses) to allow editing
        return False, 0, ""
    
    def _delete_portfolio(self, portfolio_id: str) -> bool:
        """Delete portfolio using portfolio service."""
        try:
            portfolio_service = self.services['portfolio']
            success = portfolio_service.delete_portfolio(portfolio_id)
            
            if success:
                # Update session state
                if portfolio_id in st.session_state.portfolios:
                    del st.session_state.portfolios[portfolio_id]
                
                # Clean up related session state
                for key in ['edit_mode', 'portfolio_backup', 'selected_portfolio']:
                    if key in st.session_state and isinstance(st.session_state[key], dict):
                        if portfolio_id in st.session_state[key]:
                            del st.session_state[key][portfolio_id]
                
                return True
            
        except Exception as e:
            logger.error(f"Error deleting portfolio {portfolio_id}: {str(e)}")
        
        return False
    
    def _show_create_portfolio_dialog(self) -> None:
        """Show create portfolio dialog."""
        st.session_state['show_create_portfolio_dialog'] = True
    
    def _show_copy_portfolio_dialog(self, portfolio_id: str) -> None:
        """Show copy portfolio dialog."""
        st.session_state['show_copy_portfolio_dialog'] = True
        st.session_state['copy_source_portfolio'] = portfolio_id
    
    def _show_total_positions_dialog(self, symbol_details: Dict[str, Dict[str, str]]) -> None:
        """Show dialog with all unique symbols."""
        with st.expander("📊 All Unique Symbols", expanded=True):
            if not symbol_details:
                st.info("No symbols found.")
                return
            
            st.write(f"**Total unique symbols: {len(symbol_details)}**")
            
            # Create table
            for symbol, details in sorted(symbol_details.items()):
                col1, col2, col3 = st.columns([1, 2, 1])
                with col1:
                    st.write(symbol)
                with col2:
                    st.write(details.get('company_name', 'Unknown'))
                with col3:
                    st.write(details.get('sector', 'Other'))
    
    def _show_active_positions_dialog(self, symbol_details: Dict[str, Dict[str, str]]) -> None:
        """Show dialog with active symbols only."""
        with st.expander("📊 Active Symbols Only", expanded=True):
            if not symbol_details:
                st.info("No active symbols found.")
                return
            
            st.write(f"**Total active symbols: {len(symbol_details)}**")
            
            # Create table
            for symbol, details in sorted(symbol_details.items()):
                col1, col2, col3 = st.columns([1, 2, 1])
                with col1:
                    st.write(symbol)
                with col2:
                    st.write(details.get('company_name', 'Unknown'))
                with col3:
                    st.write(details.get('sector', 'Other'))