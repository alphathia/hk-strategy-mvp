"""
Portfolio Page for HK Strategy Dashboard.
Shows individual portfolio dashboard with positions, P&L, and real-time data.

Extracted from dashboard.py lines 5211-5996.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import copy
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta

from src.pages.base_page import BasePage

# Setup logging
logger = logging.getLogger(__name__)


class PortfolioPage(BasePage):
    """Portfolio page showing individual portfolio dashboard and editing interface."""
    
    def __init__(self):
        super().__init__('portfolio')
    
    def pre_render(self) -> None:
        """Pre-render setup with portfolio validation."""
        super().pre_render()
        
        # Ensure portfolio is selected
        if not self.require_portfolio_selection():
            return
    
    def _render_content(self) -> None:
        """Render the portfolio page content."""
        # Get current portfolio data
        current_portfolio = self.get_current_portfolio()
        selected_portfolio = self.get_selected_portfolio_id()
        
        if not current_portfolio or not selected_portfolio:
            st.error("No portfolio selected or portfolio not found.")
            return
        
        # Check if user is in editing mode
        is_editing = st.session_state.get('edit_mode', {}).get(selected_portfolio, False)
        
        # Render sidebar info
        self._render_sidebar_info(current_portfolio)
        
        # Render main content based on mode
        if is_editing:
            self._render_editing_interface(current_portfolio, selected_portfolio)
        else:
            self._render_viewing_interface(current_portfolio, selected_portfolio)
    
    def _render_sidebar_info(self, current_portfolio: Dict[str, Any]) -> None:
        """Render portfolio info in sidebar."""
        st.sidebar.markdown(f"**{current_portfolio['name']}**")
        st.sidebar.markdown(f"*{current_portfolio['description']}*")
    
    def _render_editing_interface(self, current_portfolio: Dict[str, Any], selected_portfolio: str) -> None:
        """Render the portfolio editing interface."""
        st.subheader(f"✏️ Editing: {current_portfolio['name']}")
        st.info("You are in edit mode. Make changes below, then Save or Cancel in the sidebar.")
        
        # Show pending changes indicator
        pending_changes = st.session_state.get('pending_changes', {}).get(selected_portfolio, [])
        if pending_changes:
            st.warning(f"⚠️ You have {len(pending_changes)} pending changes. Click Save to apply them.")
        
        self._render_debug_info(selected_portfolio)
        self._render_add_symbol_button(selected_portfolio)
        self._render_positions_editing_table(current_portfolio, selected_portfolio)
    
    def _render_viewing_interface(self, current_portfolio: Dict[str, Any], selected_portfolio: str) -> None:
        """Render the portfolio viewing interface."""
        st.subheader(f"📊 {current_portfolio['name']}")
        
        positions = current_portfolio.get('positions', [])
        if not positions:
            st.warning("This portfolio has no positions")
            return
        
        # Render portfolio summary and metrics
        self._render_portfolio_summary(current_portfolio, selected_portfolio, positions)
        
        # Render action buttons
        self._render_portfolio_actions(selected_portfolio)
        
        # Render portfolio table and charts
        self._render_portfolio_table(current_portfolio, selected_portfolio, positions)
        self._render_portfolio_charts(selected_portfolio, positions)
    
    def _render_debug_info(self, selected_portfolio: str) -> None:
        """Render debug information for editing mode."""
        if 'debug_delete_action' in st.session_state:
            with st.expander("🐛 Debug Info - Delete Action Analysis", expanded=False):
                debug_data = st.session_state['debug_delete_action']
                st.json(debug_data)
                if st.button("Clear Debug"):
                    del st.session_state['debug_delete_action']
                    st.rerun()
    
    def _render_add_symbol_button(self, selected_portfolio: str) -> None:
        """Render add new symbol button."""
        col_add_btn, col_spacer = st.columns([2, 8])
        with col_add_btn:
            if st.button("➕ Add New Symbol", type="primary", use_container_width=True):
                self._show_add_symbol_dialog(selected_portfolio)
    
    def _render_positions_editing_table(self, current_portfolio: Dict[str, Any], selected_portfolio: str) -> None:
        """Render positions editing table."""
        st.markdown("---")
        st.markdown("### 📋 Current Positions (Click to Edit)")
        
        positions = current_portfolio.get('positions', [])
        if not positions:
            st.info("No positions in this portfolio. Add some positions above.")
            return
        
        # Initialize session state keys
        self._init_editing_session_state(selected_portfolio)
        
        # Custom CSS for table styling
        st.markdown("""
        <style>
        .position-table { margin-bottom: 20px; }
        .deleted-row { background-color: rgba(255, 99, 71, 0.1); color: #8B0000; }
        .modified-row { background-color: rgba(255, 215, 0, 0.1); }
        </style>
        """, unsafe_allow_html=True)
        
        # Render table header
        self._render_editing_table_header()
        
        # Render table rows
        self._render_editing_table_rows(positions, selected_portfolio)
        
        # Render save/cancel buttons
        self._render_editing_actions(selected_portfolio)
    
    def _init_editing_session_state(self, selected_portfolio: str) -> None:
        """Initialize session state for editing."""
        edit_mode_key = f'edit_mode_{selected_portfolio}'
        deleted_key = f'deleted_positions_{selected_portfolio}'
        modified_key = f'modified_positions_{selected_portfolio}'
        
        if edit_mode_key not in st.session_state:
            st.session_state[edit_mode_key] = {}
        if deleted_key not in st.session_state:
            st.session_state[deleted_key] = set()
        if modified_key not in st.session_state:
            st.session_state[modified_key] = {}
    
    def _render_editing_table_header(self) -> None:
        """Render editing table header."""
        st.markdown("---")
        col_header = st.columns([1.5, 2, 1, 1, 1, 1.5])
        col_header[0].markdown("**Ticker**")
        col_header[1].markdown("**Stock Name**") 
        col_header[2].markdown("**Quantity**")
        col_header[3].markdown("**Avg Cost**")
        col_header[4].markdown("**Sector**")
        col_header[5].markdown("**Action**")
        st.markdown("---")
    
    def _render_editing_table_rows(self, positions: List[Dict[str, Any]], selected_portfolio: str) -> None:
        """Render editing table rows."""
        edit_mode_key = f'edit_mode_{selected_portfolio}'
        deleted_key = f'deleted_positions_{selected_portfolio}'
        modified_key = f'modified_positions_{selected_portfolio}'
        
        for i, position in enumerate(positions):
            symbol = position['symbol']
            is_deleted = symbol in st.session_state[deleted_key]
            is_editing = st.session_state[edit_mode_key].get(symbol, False)
            is_modified = symbol in st.session_state[modified_key]
            
            # Apply styling based on state
            if is_deleted:
                st.markdown('<div class="deleted-row">', unsafe_allow_html=True)
            elif is_modified:
                st.markdown('<div class="modified-row">', unsafe_allow_html=True)
            
            self._render_position_row(position, i, is_deleted, is_editing, is_modified, 
                                    selected_portfolio, edit_mode_key, deleted_key, modified_key)
            
            if is_deleted or is_modified:
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Add separator between rows
            if i < len(positions) - 1:
                st.markdown("<hr style='margin: 5px 0; border: 0.5px solid #ddd;'>", unsafe_allow_html=True)
        
        # Show pending changes status
        self._show_pending_changes_status(selected_portfolio, deleted_key, modified_key)
    
    def _render_position_row(self, position: Dict[str, Any], row_index: int, is_deleted: bool, 
                           is_editing: bool, is_modified: bool, selected_portfolio: str,
                           edit_mode_key: str, deleted_key: str, modified_key: str) -> None:
        """Render a single position row in editing mode."""
        symbol = position['symbol']
        col_data = st.columns([1.5, 2, 1, 1, 1, 1.5])
        
        # Symbol column
        with col_data[0]:
            if is_deleted:
                st.markdown(f"~~{symbol}~~ 🗑️")
            else:
                st.text(symbol)
        
        # Company name column
        with col_data[1]:
            if is_editing and not is_deleted:
                current_company = st.session_state[modified_key].get(symbol, {}).get('company_name', position['company_name'])
                edit_company = st.text_input("", value=current_company, key=f"edit_company_{row_index}", label_visibility="collapsed")
            else:
                company_display = self._truncate_company_name(position['company_name'])
                if is_deleted:
                    st.markdown(f"~~{company_display}~~")
                else:
                    st.text(company_display)
        
        # Quantity column
        with col_data[2]:
            if is_editing and not is_deleted:
                current_qty = st.session_state[modified_key].get(symbol, {}).get('quantity', position['quantity'])
                edit_quantity = st.number_input("", min_value=0, value=current_qty, key=f"edit_quantity_{row_index}", step=1, format="%d", label_visibility="collapsed")
            else:
                if is_deleted:
                    st.markdown(f"~~{position['quantity']:,}~~")
                else:
                    st.text(f"{position['quantity']:,}")
        
        # Average cost column
        with col_data[3]:
            if is_editing and not is_deleted:
                current_cost = st.session_state[modified_key].get(symbol, {}).get('avg_cost', position['avg_cost'])
                edit_avg_cost = st.number_input("", min_value=0.0, value=current_cost, key=f"edit_avg_cost_{row_index}", format="%.2f", step=0.01, label_visibility="collapsed")
            else:
                if is_deleted:
                    st.markdown(f"~~HK${position['avg_cost']:.2f}~~")
                else:
                    st.text(f"HK${position['avg_cost']:.2f}")
        
        # Sector column
        with col_data[4]:
            if is_editing and not is_deleted:
                current_sector = st.session_state[modified_key].get(symbol, {}).get('sector', position['sector'])
                sector_options = ["Tech", "Financials", "REIT", "Energy", "Other"]
                sector_index = sector_options.index(current_sector) if current_sector in sector_options else 4
                edit_sector = st.selectbox("", sector_options, index=sector_index, key=f"edit_sector_{row_index}", label_visibility="collapsed")
            else:
                if is_deleted:
                    st.markdown(f"~~{position.get('sector', 'Other')}~~")
                else:
                    st.text(position.get('sector', 'Other'))
        
        # Action column
        with col_data[5]:
            if is_deleted:
                if st.button("↩️ Restore", key=f"restore_{row_index}"):
                    st.session_state[deleted_key].remove(symbol)
                    st.rerun()
            elif is_editing:
                self._render_position_edit_actions(symbol, row_index, edit_mode_key, modified_key,
                                                 edit_company, edit_quantity, edit_avg_cost, edit_sector)
            else:
                self._render_position_normal_actions(position, row_index, selected_portfolio, 
                                                   edit_mode_key, deleted_key)
    
    def _render_position_edit_actions(self, symbol: str, row_index: int, edit_mode_key: str, 
                                    modified_key: str, edit_company: str, edit_quantity: int, 
                                    edit_avg_cost: float, edit_sector: str) -> None:
        """Render edit actions for a position."""
        col_save, col_cancel = st.columns(2)
        with col_save:
            if st.button("💾", key=f"save_{row_index}", help="Save changes"):
                st.session_state[modified_key][symbol] = {
                    'company_name': edit_company,
                    'quantity': edit_quantity,
                    'avg_cost': edit_avg_cost,
                    'sector': edit_sector
                }
                st.session_state[edit_mode_key][symbol] = False
                st.success(f"✅ {symbol} changes saved (click Save All to commit)")
                st.rerun()
        with col_cancel:
            if st.button("❌", key=f"cancel_{row_index}", help="Cancel editing"):
                st.session_state[edit_mode_key][symbol] = False
                if symbol in st.session_state[modified_key]:
                    del st.session_state[modified_key][symbol]
                st.rerun()
    
    def _render_position_normal_actions(self, position: Dict[str, Any], row_index: int, 
                                      selected_portfolio: str, edit_mode_key: str, deleted_key: str) -> None:
        """Render normal actions for a position."""
        col_update, col_delete = st.columns(2)
        with col_update:
            if st.button("✏️", key=f"edit_{row_index}", help="Edit position"):
                self._show_update_position_dialog(selected_portfolio, position)
        with col_delete:
            if st.button("🗑️", key=f"delete_{row_index}", help="Mark for deletion"):
                self._mark_position_for_deletion(position['symbol'], selected_portfolio, 
                                               edit_mode_key, deleted_key)
    
    def _show_pending_changes_status(self, selected_portfolio: str, deleted_key: str, modified_key: str) -> None:
        """Show status of pending changes."""
        deleted_count = len(st.session_state[deleted_key])
        modified_count = len(st.session_state[modified_key])
        
        if deleted_count > 0 or modified_count > 0:
            st.markdown("---")
            status_msg = []
            if modified_count > 0:
                status_msg.append(f"**{modified_count}** position(s) modified")
            if deleted_count > 0:
                status_msg.append(f"**{deleted_count}** position(s) marked for deletion")
            
            st.warning(f"⚠️ Pending changes: {', '.join(status_msg)}")
    
    def _render_editing_actions(self, selected_portfolio: str) -> None:
        """Render save/cancel actions for editing mode."""
        st.markdown("---")
        col_save_all, col_cancel_all = st.columns([1, 1])
        
        with col_save_all:
            if st.button("💾 Save All Changes", type="primary", use_container_width=True):
                self._handle_save_all_changes(selected_portfolio)
        
        with col_cancel_all:
            if st.button("🔙 Back", use_container_width=True):
                self._handle_cancel_editing(selected_portfolio)
    
    def _handle_save_all_changes(self, selected_portfolio: str) -> None:
        """Handle saving all changes."""
        deleted_key = f'deleted_positions_{selected_portfolio}'
        modified_key = f'modified_positions_{selected_portfolio}'
        edit_mode_key = f'edit_mode_{selected_portfolio}'
        
        deleted_count = len(st.session_state.get(deleted_key, set()))
        modified_count = len(st.session_state.get(modified_key, {}))
        
        if deleted_count == 0 and modified_count == 0:
            if st.session_state.get('no_changes_clicked', False):
                st.warning("💡 **Nothing to change**: No modifications have been made to this portfolio.")
                st.session_state['no_changes_clicked'] = False
            else:
                st.session_state['no_changes_clicked'] = True
                st.info("💡 No changes to save")
                st.rerun()
            return
        
        if not st.session_state.get('confirm_save', False):
            st.session_state.confirm_save = True
            st.warning("⚠️ This will permanently save all changes to the database. Click 'Save All Changes' again to confirm.")
            st.rerun()
            return
        
        # Process changes
        st.info(f"📝 **Changes Summary**: Adding/Updating {modified_count} position(s), Deleting {deleted_count} position(s)")
        success = self._apply_portfolio_changes(selected_portfolio)
        
        if success:
            # Clear session state
            st.session_state[modified_key].clear()
            st.session_state[deleted_key].clear()
            st.session_state[edit_mode_key].clear()
            
            # Reload portfolio data
            st.session_state.portfolios = self.services['portfolio'].get_all_portfolios()
            
            st.success("✅ All changes saved successfully to database!")
            st.rerun()
        
        st.session_state.confirm_save = False
    
    def _handle_cancel_editing(self, selected_portfolio: str) -> None:
        """Handle canceling editing mode."""
        # Clear all editing session state
        edit_mode_key = f'edit_mode_{selected_portfolio}'
        deleted_key = f'deleted_positions_{selected_portfolio}'
        modified_key = f'modified_positions_{selected_portfolio}'
        
        st.session_state.get(modified_key, {}).clear()
        st.session_state.get(deleted_key, set()).clear() 
        st.session_state.get(edit_mode_key, {}).clear()
        
        # Exit edit mode and return to overview page
        if 'edit_mode' not in st.session_state:
            st.session_state.edit_mode = {}
        st.session_state.edit_mode[selected_portfolio] = False
        
        if selected_portfolio in st.session_state.get('portfolio_backup', {}):
            del st.session_state.portfolio_backup[selected_portfolio]
        
        self.navigate_to_page('overview')
        st.success("🔙 Returning to All Portfolio Management...")
        st.rerun()
    
    def _render_portfolio_summary(self, current_portfolio: Dict[str, Any], selected_portfolio: str, 
                                positions: List[Dict[str, Any]]) -> None:
        """Render portfolio summary with metrics."""
        # Calculate portfolio metrics
        portfolio_metrics = self._calculate_portfolio_metrics(positions, selected_portfolio)
        
        # Render summary header
        today_date = date.today().strftime('%Y-%m-%d')
        st.markdown(f"<h4 style='margin-bottom: 10px;'>💰 Portfolio Summary - {today_date}</h4>", unsafe_allow_html=True)
        
        # Custom CSS for metrics
        st.markdown("""
        <style>
        .metric-container { padding: 8px; border-radius: 5px; text-align: center; margin: 2px; }
        .metric-label { font-size: 11px; color: #8e8ea0; margin-bottom: 2px; }
        .metric-value { font-size: 16px; font-weight: bold; margin-bottom: 1px; }
        .metric-delta { font-size: 10px; margin-top: 1px; }
        </style>
        """, unsafe_allow_html=True)
        
        # Render metrics in 6-column layout
        self._render_portfolio_metrics(portfolio_metrics, positions)
    
    def _calculate_portfolio_metrics(self, positions: List[Dict[str, Any]], selected_portfolio: str) -> Dict[str, Any]:
        """Calculate portfolio metrics."""
        total_value = total_cost = 0
        
        for position in positions:
            if position.get('quantity', 0) <= 0:
                continue
                
            symbol = position['symbol']
            quantity = position['quantity']
            avg_cost = position.get('avg_cost', 0)
            
            # Get current price
            current_price = self._get_symbol_price(selected_portfolio, symbol)
            
            market_value = current_price * quantity
            position_cost = avg_cost * quantity
            
            total_value += market_value
            total_cost += position_cost
        
        total_pnl = total_value - total_cost
        total_pnl_pct = self._safe_percentage(total_pnl, total_cost)
        
        return {
            'total_value': total_value,
            'total_cost': total_cost,
            'total_pnl': total_pnl,
            'total_pnl_pct': total_pnl_pct
        }
    
    def _render_portfolio_metrics(self, metrics: Dict[str, Any], positions: List[Dict[str, Any]]) -> None:
        """Render portfolio metrics in columns."""
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        # Portfolio Value
        with col1:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">Portfolio Value</div>
                <div class="metric-value">HK${metrics['total_value']:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Previous Value (if available)
        with col2:
            prev_day_data = st.session_state.get('prev_day_data')
            if prev_day_data:
                prev_display = f"HK${prev_day_data['prev_total_value']:,.0f}"
            else:
                prev_display = "N/A"
            
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">Previous Value</div>
                <div class="metric-value">{prev_display}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Daily Change (if available)
        with col3:
            if prev_day_data:
                daily_change = prev_day_data['daily_change']
                daily_change_pct = prev_day_data['daily_change_pct']
                change_color = "#00ff00" if daily_change >= 0 else "#ff4444"
                change_display = f"HK${daily_change:+,.0f}"
                delta_display = f"({daily_change_pct:+.2f}%)"
            else:
                change_display = "N/A"
                delta_display = ""
                change_color = "#8e8ea0"
            
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">Daily Change</div>
                <div class="metric-value" style="color: {change_color};">{change_display}</div>
                <div class="metric-delta" style="color: {change_color};">{delta_display}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Total Cost
        with col4:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">Total Cost</div>
                <div class="metric-value">HK${metrics['total_cost']:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Total P&L
        with col5:
            pnl_color = "#00ff00" if metrics['total_pnl'] >= 0 else "#ff4444"
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">Total P&L</div>
                <div class="metric-value" style="color: {pnl_color};">HK${metrics['total_pnl']:+,.0f}</div>
                <div class="metric-delta" style="color: {pnl_color};">({metrics['total_pnl_pct']:+.1f}%)</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Positions count
        with col6:
            active_count = len([pos for pos in positions if pos.get('quantity', 0) > 0])
            total_count = len(positions)
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">Positions</div>
                <div class="metric-value">{active_count}/{total_count}</div>
                <div class="metric-delta" style="font-size: 9px; color: #8e8ea0;">Active/Total</div>
            </div>
            """, unsafe_allow_html=True)
    
    def _render_portfolio_actions(self, selected_portfolio: str) -> None:
        """Render portfolio action buttons."""
        st.markdown("---")
        col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])
        
        with col1:
            if st.button("🔄 Get Real-time Data", type="primary"):
                self._handle_realtime_data_fetch(selected_portfolio)
        
        with col2:
            if st.button("📈 Advanced Portfolio Analysis", type="secondary", use_container_width=True):
                self._navigate_to_pv_analysis(selected_portfolio)
        
        with col3:
            last_update = st.session_state.get('last_update', {}).get(selected_portfolio)
            if last_update:
                st.caption(f"Last updated: {last_update.strftime('%H:%M:%S')}")
            else:
                st.caption("Using default prices")
        
        with col4:
            # Display current portfolio info
            portfolio_name = st.session_state.portfolios[selected_portfolio]['name']
            if len(portfolio_name) > 20:
                portfolio_name = portfolio_name[:20] + "..."
            st.caption(f"Current: **{portfolio_name}**")
        
        with col5:
            # Show debug info if available
            self._render_debug_button()
    
    def _render_portfolio_table(self, current_portfolio: Dict[str, Any], selected_portfolio: str, 
                               positions: List[Dict[str, Any]]) -> None:
        """Render portfolio holdings table."""
        st.subheader(f"📋 {selected_portfolio} Holdings")
        
        # Show note about zero-quantity positions
        zero_positions_count = len([pos for pos in positions if pos.get('quantity', 0) == 0])
        if zero_positions_count > 0:
            st.info(f"💡 Showing all {len(positions)} positions including {zero_positions_count} with zero quantity (marked with 🚫)")
        
        # Show fetch details if available
        self._render_fetch_details(selected_portfolio)
        
        # Prepare portfolio display data
        portfolio_display = self._prepare_portfolio_display_data(positions, selected_portfolio)
        
        if portfolio_display:
            df = pd.DataFrame(portfolio_display)
            
            # Format display dataframe
            df_display = self._format_display_dataframe(df)
            
            # Render interactive table
            st.markdown("**Portfolio Holdings** *(Click on company name for equity strategy analysis)*")
            self._render_interactive_portfolio_table(df_display, current_portfolio)
            
            # Show table in expander
            with st.expander("📊 View as Table", expanded=False):
                st.dataframe(
                    df_display[['Symbol', 'Company', 'Quantity', 'Avg Cost', 'Current', 
                              'Market Value', 'P&L', 'P&L %', 'Sector']], 
                    use_container_width=True, 
                    hide_index=True
                )
    
    def _render_portfolio_charts(self, selected_portfolio: str, positions: List[Dict[str, Any]]) -> None:
        """Render portfolio charts."""
        # Prepare data for charts
        portfolio_display = self._prepare_portfolio_display_data(positions, selected_portfolio)
        if not portfolio_display:
            return
        
        df = pd.DataFrame(portfolio_display)
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            fig_pie = px.pie(
                df, 
                values='Market Value', 
                names='Symbol',
                title=f"{selected_portfolio} - Allocation by Market Value"
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            fig_bar = px.bar(
                df, 
                x='Symbol', 
                y='P&L',
                title=f"{selected_portfolio} - P&L by Position",
                color='P&L',
                color_continuous_scale=['red', 'green']
            )
            fig_bar.update_layout(showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)
    
    def _prepare_portfolio_display_data(self, positions: List[Dict[str, Any]], selected_portfolio: str) -> List[Dict[str, Any]]:
        """Prepare portfolio data for display."""
        portfolio_display = []
        
        for position in positions:
            symbol = position.get('symbol', '')
            quantity = position.get('quantity', 0)
            avg_cost = position.get('avg_cost', 0)
            
            if not symbol:
                continue
            
            # Get current price
            current_price = self._get_symbol_price(selected_portfolio, symbol)
            
            # Calculate values
            market_value = current_price * quantity
            position_cost = avg_cost * quantity
            pnl = market_value - position_cost
            pnl_pct = self._safe_percentage(pnl, position_cost)
            
            # Format quantity display
            quantity_display = f"{quantity:,}"
            if quantity == 0:
                quantity_display = f"🚫 {quantity_display}"
            
            portfolio_display.append({
                "Symbol": symbol,
                "Company": self._truncate_company_name(position.get('company_name', 'Unknown')),
                "Quantity": quantity_display,
                "Avg Cost": f"HK${avg_cost:.2f}",
                "Current": f"HK${current_price:.2f}",
                "Market Value": market_value,
                "P&L": pnl,
                "P&L %": pnl_pct,
                "Sector": position.get('sector', 'Other')
            })
        
        return portfolio_display
    
    def _format_display_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Format dataframe for display."""
        df_display = df.copy()
        df_display['Market Value'] = df_display['Market Value'].apply(lambda x: f"HK${x:,.0f}")
        df_display['P&L'] = df_display['P&L'].apply(lambda x: f"HK${x:,.0f}")
        df_display['P&L %'] = df_display['P&L %'].apply(lambda x: f"{x:+.1f}%")
        return df_display
    
    def _render_interactive_portfolio_table(self, df_display: pd.DataFrame, current_portfolio: Dict[str, Any]) -> None:
        """Render interactive portfolio table with clickable company names."""
        # Table headers
        col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([1, 2.5, 1, 1, 1, 1.5, 1.5, 1, 1])
        headers = ["**Symbol**", "**Company** *(Click to analyze)*", "**Qty**", "**Avg Cost**", 
                  "**Current**", "**Market Value**", "**P&L**", "**P&L %**", "**Sector**"]
        
        for col, header in zip([col1, col2, col3, col4, col5, col6, col7, col8, col9], headers):
            col.markdown(header)
        
        st.markdown("---")
        
        # Table rows
        for idx, row in df_display.iterrows():
            col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([1, 2.5, 1, 1, 1, 1.5, 1.5, 1, 1])
            
            with col1:
                st.text(row['Symbol'])
            with col2:
                if st.button(row['Company'], key=f"company_{idx}_{row['Symbol']}", 
                           help=f"Analyze {row['Symbol']} strategy"):
                    self._navigate_to_equity_analysis(row, current_portfolio)
            
            for col, column_name in zip([col3, col4, col5, col6, col7, col8, col9], 
                                      ['Quantity', 'Avg Cost', 'Current', 'Market Value', 'P&L', 'P&L %', 'Sector']):
                with col:
                    st.text(row[column_name])
    
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
    
    def _safe_percentage(self, numerator: float, denominator: float) -> float:
        """Calculate percentage safely avoiding division by zero."""
        if denominator == 0:
            return 0.0
        return (numerator / denominator) * 100
    
    def _truncate_company_name(self, company_name: str, max_length: int = 25) -> str:
        """Truncate company name if too long."""
        if len(company_name) > max_length:
            return company_name[:max_length] + "..."
        return company_name
    
    def _apply_portfolio_changes(self, selected_portfolio: str) -> bool:
        """Apply portfolio changes using portfolio service."""
        try:
            deleted_key = f'deleted_positions_{selected_portfolio}'
            modified_key = f'modified_positions_{selected_portfolio}'
            
            success = True
            changes_made = []
            
            # Apply modifications
            for symbol, changes in st.session_state.get(modified_key, {}).items():
                position_data = {
                    "symbol": symbol,
                    "company_name": changes['company_name'],
                    "quantity": changes['quantity'],
                    "avg_cost": changes['avg_cost'],
                    "sector": changes['sector']
                }
                
                update_success = self.services['portfolio'].update_position(selected_portfolio, position_data)
                if not update_success:
                    success = False
                    st.error(f"❌ Failed to update {symbol}")
                else:
                    changes_made.append(f"Updated {symbol}")
            
            # Apply deletions
            for symbol in st.session_state.get(deleted_key, set()):
                remove_success = self.services['portfolio'].remove_position(selected_portfolio, symbol)
                if not remove_success:
                    success = False
                    st.error(f"❌ Failed to delete {symbol}")
                else:
                    changes_made.append(f"Deleted {symbol}")
            
            if success and changes_made:
                st.info(f"📋 **Changes Applied**: {', '.join(changes_made)}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error applying portfolio changes: {str(e)}")
            st.error(f"❌ Error applying changes: {str(e)}")
            return False
    
    def _handle_realtime_data_fetch(self, selected_portfolio: str) -> None:
        """Handle real-time data fetching."""
        try:
            current_portfolio = self.get_current_portfolio()
            if not current_portfolio:
                st.error("Portfolio not found")
                return
            
            positions = current_portfolio.get('positions', [])
            active_positions = [pos for pos in positions if pos.get('quantity', 0) > 0]
            
            if not active_positions:
                st.warning("No active positions to fetch real-time data for.")
                return
            
            # Use data service to fetch prices
            data_service = self.services['data']
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total_symbols = len(active_positions)
            portfolio_prices = {}
            
            for i, position in enumerate(active_positions):
                symbol = position["symbol"]
                status_text.text(f"Fetching {symbol} ({i+1}/{total_symbols})...")
                
                price, status = data_service.fetch_hk_price(symbol)
                portfolio_prices[symbol] = price
                
                if total_symbols > 0:
                    progress_bar.progress((i + 1) / total_symbols)
            
            # Update session state
            if 'portfolio_prices' not in st.session_state:
                st.session_state.portfolio_prices = {}
            st.session_state.portfolio_prices[selected_portfolio] = portfolio_prices
            
            if 'last_update' not in st.session_state:
                st.session_state.last_update = {}
            st.session_state.last_update[selected_portfolio] = datetime.now()
            
            status_text.text("✅ All prices updated!")
            time.sleep(1)
            status_text.empty()
            progress_bar.empty()
            
            st.rerun()
            
        except Exception as e:
            logger.error(f"Error fetching real-time data: {str(e)}")
            st.error(f"Error fetching real-time data: {str(e)}")
    
    def _navigate_to_pv_analysis(self, selected_portfolio: str) -> None:
        """Navigate to PV analysis page."""
        st.session_state.selected_portfolio_for_pv = selected_portfolio
        self.navigate_to_page('pv_analysis')
        st.rerun()
    
    def _navigate_to_equity_analysis(self, row: Dict[str, Any], current_portfolio: Dict[str, Any]) -> None:
        """Navigate to equity analysis page."""
        current_analysis = st.session_state.get('current_analysis')
        st.session_state.equity_context = {
            'symbol': row['Symbol'],
            'company_name': row['Company'],
            'portfolio_name': current_portfolio['name'],
            'portfolio_analysis_name': current_analysis.get('name', 'Current Portfolio Analysis') if current_analysis else 'Portfolio Holdings Analysis',
            'start_date': current_analysis.get('start_date', (date.today() - timedelta(days=180)).strftime('%Y-%m-%d')) if current_analysis else (date.today() - timedelta(days=180)).strftime('%Y-%m-%d'),
            'end_date': current_analysis.get('end_date', date.today().strftime('%Y-%m-%d')) if current_analysis else date.today().strftime('%Y-%m-%d')
        }
        self.navigate_to_page('equity_analysis')
        st.rerun()
    
    def _render_fetch_details(self, selected_portfolio: str) -> None:
        """Render fetch details in expander."""
        fetch_details = st.session_state.get('fetch_details', {}).get(selected_portfolio, [])
        if fetch_details:
            with st.expander("📋 Price Fetching Details", expanded=False):
                for detail in fetch_details:
                    st.text(detail)
    
    def _render_debug_button(self) -> None:
        """Render debug button if debug data available."""
        debug_data = st.session_state.get('debug_realtime_fetch')
        if debug_data and debug_data.get('fetch_completed', False):
            if st.button("🐛 Debug", help="Show real-time fetch debug info"):
                st.json(debug_data)
                if st.button("Clear Debug"):
                    del st.session_state['debug_realtime_fetch']
                    st.rerun()
    
    def _mark_position_for_deletion(self, symbol: str, selected_portfolio: str, 
                                  edit_mode_key: str, deleted_key: str) -> None:
        """Mark position for deletion with debug info."""
        # Store debug info
        debug_info = {
            'before_delete': {
                'selected_portfolio': selected_portfolio,
                'current_page': st.session_state.current_page,
                'edit_mode_state': st.session_state.get('edit_mode', {}).get(selected_portfolio, 'NOT_SET'),
                'portfolio_switch_request': st.session_state.get('portfolio_switch_request')
            }
        }
        st.session_state['debug_delete_action'] = debug_info
        
        # Mark for deletion
        st.session_state[deleted_key].add(symbol)
        st.info(f"📋 {symbol} marked for deletion")
        
        # Preserve edit state
        if 'edit_mode' not in st.session_state:
            st.session_state.edit_mode = {}
        st.session_state.edit_mode[selected_portfolio] = True
        st.session_state.current_page = 'portfolio'
        
        st.rerun()
    
    def _show_add_symbol_dialog(self, selected_portfolio: str) -> None:
        """Show add symbol dialog."""
        st.session_state['show_add_symbol_dialog'] = True
        st.session_state['add_symbol_portfolio'] = selected_portfolio
    
    def _show_update_position_dialog(self, selected_portfolio: str, position: Dict[str, Any]) -> None:
        """Show update position dialog."""
        st.session_state['show_update_position_dialog'] = True
        st.session_state['update_position_portfolio'] = selected_portfolio
        st.session_state['update_position_data'] = position