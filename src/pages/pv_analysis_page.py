"""
Portfolio-Value Analysis Page for HK Strategy Dashboard.
Advanced portfolio analysis with timeline data, comparison charts, and portfolio state analysis.

Extracted from dashboard.py lines 2840-3561.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date, timedelta

from src.pages.base_page import BasePage

# Setup logging
logger = logging.getLogger(__name__)


class PVAnalysisPage(BasePage):
    """Portfolio-Value analysis page with advanced portfolio analytics."""
    
    def __init__(self):
        super().__init__('pv_analysis')
    
    def _render_content(self) -> None:
        """Render the PV analysis page content."""
        st.subheader("📈 Portfolio Analysis Dashboard")
        
        # Initialize Portfolio Analysis Manager
        self._init_portfolio_analysis_manager()
        
        # Handle portfolio selection and modal states
        selected_portfolio = self._handle_portfolio_selection()
        
        if not selected_portfolio:
            self._render_load_portfolio_interface()
            return
        
        # Portfolio is selected - show analysis interface
        current_portfolio = st.session_state.portfolios[selected_portfolio]
        self._render_analysis_interface(current_portfolio, selected_portfolio)
    
    def _init_portfolio_analysis_manager(self) -> None:
        """Initialize Portfolio Analysis Manager."""
        if 'portfolio_analysis_manager' not in st.session_state:
            try:
                from portfolio_analysis_manager import PortfolioAnalysisManager
                st.session_state.portfolio_analysis_manager = PortfolioAnalysisManager(
                    st.session_state.db_manager
                )
            except ImportError as e:
                logger.warning(f"Portfolio Analysis Manager not available: {e}")
                st.warning("⚠️ Advanced portfolio analysis features are not available")
    
    def _handle_portfolio_selection(self) -> Optional[str]:
        """Handle portfolio selection and clear modal states when needed."""
        # Check portfolio selection sources
        selected_portfolio = (st.session_state.get('selected_portfolio') or 
                            st.session_state.get('selected_portfolio_for_pv'))
        
        # If coming from Advanced button, sync selections
        if st.session_state.get('selected_portfolio_for_pv') and not st.session_state.get('selected_portfolio'):
            st.session_state.selected_portfolio = st.session_state.selected_portfolio_for_pv
            selected_portfolio = st.session_state.selected_portfolio_for_pv
            self._clear_modal_states()
        
        # Clear modal states if portfolio changed
        if 'previous_selected_portfolio' in st.session_state and st.session_state.previous_selected_portfolio != selected_portfolio:
            self._clear_modal_states()
        st.session_state.previous_selected_portfolio = selected_portfolio
        
        return selected_portfolio
    
    def _clear_modal_states(self) -> None:
        """Clear modal dialog states."""
        modal_flags = [
            'show_create_analysis_dialog',
            'show_detail_modal',
            'show_transaction_modal',
            'delete_confirm_id',
            'show_technical_modal'
        ]
        
        for flag in modal_flags:
            if flag in st.session_state:
                st.session_state[flag] = None if 'modal' in flag else False
    
    def _render_load_portfolio_interface(self) -> None:
        """Render portfolio loading interface."""
        st.markdown("## 📂 Load Portfolio")
        st.markdown("Select a portfolio to begin analysis.")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            portfolio_keys = list(st.session_state.portfolios.keys())
            if portfolio_keys:
                selected = st.selectbox(
                    "Choose Portfolio:",
                    options=portfolio_keys,
                    format_func=lambda x: f"{st.session_state.portfolios[x]['name']}"
                )
                
                if st.button("📂 Load Portfolio", type="primary"):
                    st.session_state.selected_portfolio = selected
                    st.rerun()
            else:
                st.error("No portfolios available. Please create a portfolio first.")
                
        with col2:
            st.markdown("### Quick Actions")
            if st.button("🔙 Back to Overview"):
                self.navigate_to_page('overview')
                st.rerun()
    
    def _render_analysis_interface(self, current_portfolio: Dict[str, Any], selected_portfolio: str) -> None:
        """Render the main analysis interface."""
        # Header with action buttons
        self._render_header(current_portfolio, selected_portfolio)
        
        # Create new analysis dialog
        if st.session_state.get('show_create_analysis_dialog', False):
            self._render_create_analysis_dialog(selected_portfolio)
        
        # Portfolio Analysis Table
        self._render_portfolio_analyses_table(selected_portfolio)
    
    def _render_header(self, current_portfolio: Dict[str, Any], selected_portfolio: str) -> None:
        """Render header with portfolio name and action buttons."""
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"### Portfolio Analysis: **{current_portfolio['name']}**")
        with col2:
            if st.button("📈 Update Market Prices", help="Refresh all analyses with current market prices"):
                self._handle_update_market_prices(selected_portfolio)
        with col3:
            if st.button("➕ Create New Analysis", type="primary"):
                st.session_state.show_create_analysis_dialog = True
                st.rerun()
    
    def _handle_update_market_prices(self, selected_portfolio: str) -> None:
        """Handle market price updates."""
        if 'portfolio_analysis_manager' not in st.session_state:
            st.error("Portfolio analysis manager not available")
            return
        
        with st.spinner("Updating market prices..."):
            try:
                success, message, count = st.session_state.portfolio_analysis_manager.refresh_all_analyses_for_portfolio(selected_portfolio)
                if success:
                    st.success(f"✅ {message}")
                    # Clear price cache
                    if 'price_data_cache' in st.session_state:
                        st.session_state.price_data_cache.clear()
                        st.session_state.cache_expiry.clear()
                else:
                    st.error(f"❌ {message}")
            except Exception as e:
                logger.error(f"Error updating market prices: {str(e)}")
                st.error(f"❌ Error updating prices: {str(e)}")
            st.rerun()
    
    def _render_create_analysis_dialog(self, selected_portfolio: str) -> None:
        """Render create new analysis dialog."""
        with st.container():
            st.markdown("---")
            st.markdown("### ➕ Create New Portfolio Analysis")
            
            current_portfolio = st.session_state.portfolios[selected_portfolio]
            st.info(f"📂 **Creating analysis for portfolio:** {current_portfolio['name']} (ID: {selected_portfolio})")
            
            col1, col2 = st.columns(2)
            with col1:
                analysis_name = st.text_input(
                    "Analysis Name*",
                    placeholder="e.g., Q1 2024 Performance Review",
                    help="Enter a unique name for this analysis"
                )
                start_date = st.date_input(
                    "Start Date*",
                    value=date.today() - timedelta(days=90),
                    max_value=date.today()
                )
            
            with col2:
                start_cash = st.number_input(
                    "Start Cash (HKD)*",
                    min_value=0.0,
                    value=100000.0,
                    step=10000.0,
                    format="%.2f"
                )
                end_date = st.date_input(
                    "End Date*",
                    value=date.today(),
                    max_value=date.today()
                )
            
            # Validation
            error_msg = self._validate_analysis_form(analysis_name, start_date, end_date, selected_portfolio)
            
            if error_msg:
                st.error(f"❌ {error_msg}")
            
            # Action buttons
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.button("💾 Save", disabled=bool(error_msg), type="primary", use_container_width=True):
                    self._handle_create_analysis(selected_portfolio, analysis_name.strip(), 
                                               start_date, end_date, start_cash)
            
            with col_cancel:
                if st.button("❌ Cancel", use_container_width=True):
                    st.session_state.show_create_analysis_dialog = False
                    st.rerun()
            
            st.markdown("---")
    
    def _validate_analysis_form(self, analysis_name: str, start_date: date, end_date: date, 
                               selected_portfolio: str) -> str:
        """Validate analysis form inputs."""
        if not analysis_name.strip():
            return "Analysis name is required"
        elif end_date <= start_date:
            return "End date must be after start date"
        
        # Check name uniqueness if portfolio_analysis_manager is available
        if 'portfolio_analysis_manager' in st.session_state:
            try:
                if not st.session_state.portfolio_analysis_manager.validate_analysis_name(
                    selected_portfolio, analysis_name.strip()
                ):
                    return f"Analysis name '{analysis_name.strip()}' already exists for this portfolio"
            except Exception as e:
                logger.warning(f"Could not validate analysis name: {e}")
        
        return ""
    
    def _handle_create_analysis(self, portfolio_id: str, analysis_name: str, 
                               start_date: date, end_date: date, start_cash: float) -> None:
        """Handle analysis creation."""
        if 'portfolio_analysis_manager' not in st.session_state:
            st.error("Portfolio analysis manager not available")
            return
        
        try:
            success, message, analysis_id = st.session_state.portfolio_analysis_manager.create_analysis(
                portfolio_id=portfolio_id,
                analysis_name=analysis_name,
                start_date=start_date,
                end_date=end_date,
                start_cash=start_cash
            )
            
            if success:
                st.success(f"✅ {message}")
                st.session_state.show_create_analysis_dialog = False
                st.rerun()
            else:
                st.error(f"❌ {message}")
        except Exception as e:
            logger.error(f"Error creating analysis: {str(e)}")
            st.error(f"❌ Error creating analysis: {str(e)}")
    
    def _render_portfolio_analyses_table(self, selected_portfolio: str) -> None:
        """Render portfolio analyses table."""
        st.markdown("### 📊 Portfolio Analyses")
        
        if 'portfolio_analysis_manager' not in st.session_state:
            st.warning("Portfolio analysis manager not available")
            return
        
        # Get analyses for this portfolio
        try:
            analyses_df = st.session_state.portfolio_analysis_manager.get_analysis_summary(selected_portfolio)
        except Exception as e:
            logger.error(f"Error getting analysis summary: {str(e)}")
            st.error(f"Error loading analyses: {str(e)}")
            return
        
        if analyses_df.empty:
            st.info("No portfolio analyses found. Create your first analysis using the button above.")
            return
        
        # Initialize states
        self._init_analysis_states()
        
        # Render table
        self._render_analyses_table_header()
        self._render_analyses_table_rows(analyses_df)
        
        # Render modals
        self._render_detail_modal(analyses_df)
        self._render_transaction_modal(analyses_df)
        
        # Render comparison section
        self._render_comparison_section(analyses_df, selected_portfolio)
    
    def _init_analysis_states(self) -> None:
        """Initialize analysis-related session states."""
        if 'selected_for_compare' not in st.session_state:
            st.session_state.selected_for_compare = []
        if 'delete_confirm_id' not in st.session_state:
            st.session_state.delete_confirm_id = None
        if 'show_detail_modal' not in st.session_state:
            st.session_state.show_detail_modal = None
        if 'show_transaction_modal' not in st.session_state:
            st.session_state.show_transaction_modal = None
    
    def _render_analyses_table_header(self) -> None:
        """Render analyses table header."""
        st.markdown("#### Analysis Summary")
        
        header_col1, header_col2, header_col3, header_col4, header_col5, header_col6, header_col7, header_col8 = st.columns([0.8, 2.5, 1.2, 1.2, 1.2, 1.0, 1.0, 1])
        headers = ["**Compare**", "**Name**", "**Start Date**", "**End Date**", 
                  "**Start Cash**", "**Detail**", "**Transaction**", "**Delete**"]
        
        for col, header in zip([header_col1, header_col2, header_col3, header_col4, header_col5, header_col6, header_col7, header_col8], headers):
            with col:
                col.markdown(header)
        
        st.markdown("---")
    
    def _render_analyses_table_rows(self, analyses_df: pd.DataFrame) -> None:
        """Render analyses table rows."""
        for idx, row in analyses_df.iterrows():
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([0.8, 2.5, 1.2, 1.2, 1.2, 1.0, 1.0, 1])
            
            # Compare checkbox
            with col1:
                compare_key = f"compare_{row['id']}"
                is_selected = st.checkbox("", key=compare_key, value=row['id'] in st.session_state.selected_for_compare)
                self._update_comparison_selection(row['id'], is_selected)
            
            # Analysis name
            with col2:
                st.markdown(f"**{row['name']}**")
            
            # Dates
            with col3:
                start_date_str = row['start_date'].strftime("%Y-%m-%d") if pd.notna(row['start_date']) else "-"
                st.write(start_date_str)
            
            with col4:
                end_date_str = row['end_date'].strftime("%Y-%m-%d") if pd.notna(row['end_date']) else "-"
                st.write(end_date_str)
            
            # Start cash
            with col5:
                start_cash_str = f"${row['start_cash']:,.0f}" if pd.notna(row['start_cash']) else "-"
                st.write(start_cash_str)
            
            # Action buttons
            with col6:
                if st.button("📊", key=f"detail_{row['id']}", help=f"View details for {row['name']}"):
                    st.session_state.show_detail_modal = row['id']
                    st.rerun()
            
            with col7:
                if st.button("📝", key=f"transaction_{row['id']}", help=f"View transactions for {row['name']}"):
                    st.session_state.show_transaction_modal = row['id']
                    st.rerun()
            
            with col8:
                self._render_delete_button(row)
            
            # Separator
            st.markdown('<hr style="margin:5px 0; border:0.5px solid #e0e0e0">', unsafe_allow_html=True)
    
    def _update_comparison_selection(self, analysis_id: int, is_selected: bool) -> None:
        """Update comparison selection state."""
        if is_selected and analysis_id not in st.session_state.selected_for_compare:
            st.session_state.selected_for_compare.append(analysis_id)
        elif not is_selected and analysis_id in st.session_state.selected_for_compare:
            st.session_state.selected_for_compare.remove(analysis_id)
    
    def _render_delete_button(self, row: pd.Series) -> None:
        """Render delete button with confirmation."""
        if st.session_state.delete_confirm_id == row['id']:
            # Show confirmation buttons
            subcol1, subcol2 = st.columns(2)
            with subcol1:
                if st.button("✅", key=f"confirm_delete_{row['id']}", help="Confirm delete"):
                    self._handle_delete_analysis(row['id'])
            with subcol2:
                if st.button("❌", key=f"cancel_delete_{row['id']}", help="Cancel"):
                    st.session_state.delete_confirm_id = None
                    st.rerun()
        else:
            if st.button("🗑️", key=f"delete_{row['id']}", help=f"Delete '{row['name']}'"):
                st.session_state.delete_confirm_id = row['id']
                st.rerun()
    
    def _handle_delete_analysis(self, analysis_id: int) -> None:
        """Handle analysis deletion."""
        if 'portfolio_analysis_manager' not in st.session_state:
            st.error("Portfolio analysis manager not available")
            return
        
        try:
            success, message = st.session_state.portfolio_analysis_manager.delete_analysis(analysis_id)
            if success:
                st.success(f"✅ {message}")
                st.session_state.delete_confirm_id = None
                if analysis_id in st.session_state.selected_for_compare:
                    st.session_state.selected_for_compare.remove(analysis_id)
                st.rerun()
            else:
                st.error(f"❌ {message}")
        except Exception as e:
            logger.error(f"Error deleting analysis: {str(e)}")
            st.error(f"❌ Error deleting analysis: {str(e)}")
    
    def _render_detail_modal(self, analyses_df: pd.DataFrame) -> None:
        """Render detail modal."""
        if not st.session_state.show_detail_modal:
            return
        
        detail_matches = analyses_df[analyses_df['id'] == st.session_state.show_detail_modal]
        if detail_matches.empty:
            st.session_state.show_detail_modal = None
            st.rerun()
            return
        
        detail_analysis = detail_matches.iloc[0]
        
        with st.container():
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 3, 1])
            with col2:
                st.markdown(f"### 📊 Analysis Details: {detail_analysis['name']}")
                
                # Financial Summary
                self._render_financial_summary(detail_analysis)
                
                # Performance Metrics
                self._render_performance_metrics(detail_analysis)
                
                # Position Details
                self._render_position_details(detail_analysis)
                
                # Close button
                if st.button("✖️ Close", key="close_detail_modal"):
                    st.session_state.show_detail_modal = None
                    st.rerun()
            
            st.markdown("---")
    
    def _render_financial_summary(self, analysis: pd.Series) -> None:
        """Render financial summary section."""
        st.markdown("#### 💰 Financial Summary")
        fin_col1, fin_col2 = st.columns(2)
        
        with fin_col1:
            st.metric("Start Cash", f"${analysis['start_cash']:,.2f}")
            st.metric("Start Equity", f"${analysis['start_equity_value']:,.2f}")
            st.metric("Start Total", f"${analysis['start_total_value']:,.2f}")
        
        with fin_col2:
            st.metric("End Cash", f"${analysis['end_cash']:,.2f}")
            st.metric("End Equity", f"${analysis['end_equity_value']:,.2f}", 
                     delta=f"{analysis['total_equity_gain_loss']:,.2f}")
            st.metric("End Total", f"${analysis['end_total_value']:,.2f}",
                     delta=f"{analysis['total_value_gain_loss']:,.2f}")
    
    def _render_performance_metrics(self, analysis: pd.Series) -> None:
        """Render performance metrics section."""
        st.markdown("#### 📈 Performance Metrics")
        perf_col1, perf_col2, perf_col3 = st.columns(3)
        
        with perf_col1:
            total_return_pct = (analysis['total_value_gain_loss'] / analysis['start_total_value'] * 100) if analysis['start_total_value'] > 0 else 0
            st.metric("Total Return", f"{total_return_pct:.2f}%")
        
        with perf_col2:
            equity_return_pct = (analysis['total_equity_gain_loss'] / analysis['start_equity_value'] * 100) if analysis['start_equity_value'] > 0 else 0
            st.metric("Equity Return", f"{equity_return_pct:.2f}%")
        
        with perf_col3:
            analysis_days = (analysis['end_date'] - analysis['start_date']).days
            st.metric("Analysis Period", f"{analysis_days} days")
    
    def _render_position_details(self, analysis: pd.Series) -> None:
        """Render position details section."""
        st.markdown("#### 🏢 Position Details")
        
        if 'portfolio_analysis_manager' not in st.session_state:
            st.warning("Position data not available")
            return
        
        try:
            positions_df = st.session_state.portfolio_analysis_manager.get_current_positions(analysis['id'])
            
            if not positions_df.empty:
                display_positions = self._format_positions_for_display(positions_df)
                st.dataframe(pd.DataFrame(display_positions), use_container_width=True, hide_index=True)
            else:
                st.info("No position data available for this analysis")
        except Exception as e:
            logger.error(f"Error loading position details: {str(e)}")
            st.error("Error loading position data")
    
    def _format_positions_for_display(self, positions_df: pd.DataFrame) -> List[Dict[str, str]]:
        """Format positions dataframe for display."""
        display_positions = []
        for _, pos in positions_df.iterrows():
            market_value = pos['current_quantity'] * pos['current_price'] if pd.notna(pos['current_price']) else 0
            cost_basis = pos['current_quantity'] * pos['avg_cost'] if pd.notna(pos['avg_cost']) else 0
            pnl = market_value - cost_basis
            
            display_positions.append({
                'Symbol': pos['symbol'],
                'Company': pos['company_name'][:30] + "..." if len(str(pos['company_name'])) > 30 else pos['company_name'],
                'Quantity': f"{pos['current_quantity']:,}",
                'Avg Cost': f"${pos['avg_cost']:.2f}" if pd.notna(pos['avg_cost']) else "-",
                'Current Price': f"${pos['current_price']:.2f}" if pd.notna(pos['current_price']) else "-",
                'Market Value': f"${market_value:,.2f}",
                'P&L': f"${pnl:+,.2f}"
            })
        
        return display_positions
    
    def _render_transaction_modal(self, analyses_df: pd.DataFrame) -> None:
        """Render transaction modal."""
        if not st.session_state.show_transaction_modal:
            return
        
        trans_matches = analyses_df[analyses_df['id'] == st.session_state.show_transaction_modal]
        if trans_matches.empty:
            st.session_state.show_transaction_modal = None
            st.rerun()
            return
        
        trans_analysis = trans_matches.iloc[0]
        
        with st.container():
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 3, 1])
            with col2:
                st.markdown(f"### 📝 Transaction History: {trans_analysis['name']}")
                
                if 'portfolio_analysis_manager' not in st.session_state:
                    st.warning("Transaction data not available")
                else:
                    try:
                        transactions_df = st.session_state.portfolio_analysis_manager.get_analysis_transactions(
                            st.session_state.show_transaction_modal
                        )
                        
                        if not transactions_df.empty:
                            display_transactions = self._format_transactions_for_display(transactions_df)
                            st.dataframe(pd.DataFrame(display_transactions), use_container_width=True, hide_index=True)
                        else:
                            st.info("No transactions found for this analysis")
                    except Exception as e:
                        logger.error(f"Error loading transactions: {str(e)}")
                        st.error("Error loading transaction data")
                
                # Close button
                if st.button("✖️ Close", key="close_transaction_modal"):
                    st.session_state.show_transaction_modal = None
                    st.rerun()
            
            st.markdown("---")
    
    def _format_transactions_for_display(self, transactions_df: pd.DataFrame) -> List[Dict[str, str]]:
        """Format transactions dataframe for display."""
        display_transactions = []
        for _, txn in transactions_df.iterrows():
            display_transactions.append({
                'Date': txn['transaction_date'].strftime('%Y-%m-%d') if pd.notna(txn['transaction_date']) else '-',
                'Type': txn['transaction_type'],
                'Symbol': txn['symbol'],
                'Quantity': f"{txn['quantity_change']:+,}",
                'Price/Share': f"${txn['price_per_share']:.3f}" if pd.notna(txn['price_per_share']) else '-',
                'Cash Change': f"${txn['cash_change']:+,.2f}" if pd.notna(txn['cash_change']) else '-',
                'Notes': txn['notes'][:50] + "..." if len(str(txn['notes'])) > 50 else str(txn['notes'])
            })
        
        return display_transactions
    
    def _render_comparison_section(self, analyses_df: pd.DataFrame, selected_portfolio: str) -> None:
        """Render comparison chart section."""
        # Analysis actions
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh Table"):
                st.rerun()
        with col2:
            st.info("💡 Use Detail and Transaction buttons in the table above")
        
        # Comparison charts
        if st.session_state.selected_for_compare:
            self._render_comparison_charts(analyses_df, selected_portfolio)
    
    def _render_comparison_charts(self, analyses_df: pd.DataFrame, selected_portfolio: str) -> None:
        """Render comparison charts for selected analyses."""
        st.markdown("---")
        st.markdown(f"### 📈 Portfolio Performance Comparison ({len(st.session_state.selected_for_compare)} analyses)")
        
        # Initialize cache
        if 'price_data_cache' not in st.session_state:
            st.session_state.price_data_cache = {}
            st.session_state.cache_expiry = {}
        
        # Get timeline data
        timeline_df = self._get_timeline_data()
        
        if timeline_df.empty:
            st.warning("No data available for selected analyses")
            return
        
        # Create and display comparison chart
        self._render_timeline_chart(timeline_df)
        
        # Portfolio analysis summary
        self._render_portfolio_analysis_summary(analyses_df, timeline_df)
    
    def _get_timeline_data(self) -> pd.DataFrame:
        """Get timeline data with caching."""
        cache_key = f"timeline_{sorted(st.session_state.selected_for_compare)}"
        current_time = time.time()
        cache_duration = 300  # 5 minutes
        
        # Check cache
        if (cache_key in st.session_state.price_data_cache and 
            cache_key in st.session_state.cache_expiry and
            current_time - st.session_state.cache_expiry[cache_key] < cache_duration):
            
            st.info("📊 Using cached data for faster display")
            return st.session_state.price_data_cache[cache_key]
        
        # Fetch fresh data
        if 'portfolio_analysis_manager' not in st.session_state:
            return pd.DataFrame()
        
        try:
            with st.spinner("📈 Fetching real-time market data..."):
                timeline_df = st.session_state.portfolio_analysis_manager.get_analysis_timeline_data(
                    st.session_state.selected_for_compare
                )
                
                # Cache results
                st.session_state.price_data_cache[cache_key] = timeline_df
                st.session_state.cache_expiry[cache_key] = current_time
                
                if not timeline_df.empty:
                    st.success("✅ Market data fetched successfully")
                
                return timeline_df
        except Exception as e:
            logger.error(f"Error fetching timeline data: {str(e)}")
            st.error(f"Error fetching timeline data: {str(e)}")
            return pd.DataFrame()
    
    def _render_timeline_chart(self, timeline_df: pd.DataFrame) -> None:
        """Render timeline comparison chart."""
        fig = go.Figure()
        
        # Add trace for each analysis
        for analysis_id in st.session_state.selected_for_compare:
            analysis_data = timeline_df[timeline_df['analysis_id'] == analysis_id]
            if not analysis_data.empty:
                analysis_name = analysis_data.iloc[0]['analysis_name']
                
                # Create hover text
                hover_text = []
                for _, point in analysis_data.iterrows():
                    hover_info = f"<b>{analysis_name}</b><br>"
                    hover_info += f"Date: {point['date'].strftime('%Y-%m-%d')}<br>"
                    hover_info += f"Total Value: ${point['total_value']:,.2f}<br>"
                    hover_info += f"Cash: ${point['cash_position']:,.2f}<br>"
                    hover_info += f"Equity: ${point['equity_value']:,.2f}"
                    if point.get('transaction_details'):
                        hover_info += f"<br>Transactions: {point['transaction_details']}"
                    hover_text.append(hover_info)
                
                fig.add_trace(go.Scatter(
                    x=analysis_data['date'],
                    y=analysis_data['total_value'],
                    mode='lines+markers',
                    name=analysis_name,
                    hovertemplate='%{hovertext}<extra></extra>',
                    hovertext=hover_text,
                    line=dict(width=2),
                    marker=dict(size=4)
                ))
        
        # Update layout
        fig.update_layout(
            title="Portfolio Total Value Over Time",
            xaxis_title="Date",
            yaxis_title="Total Value (HKD)",
            height=500,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            hovermode='x unified'
        )
        
        fig.update_layout(yaxis=dict(tickformat='$,.0f'))
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_portfolio_analysis_summary(self, analyses_df: pd.DataFrame, timeline_df: pd.DataFrame) -> None:
        """Render portfolio analysis summary section."""
        st.markdown("---")
        st.markdown("### 📈 Portfolio Analysis Summary")
        
        # Initialize states
        if 'selected_analysis_date' not in st.session_state:
            st.session_state.selected_analysis_date = None
        if 'selected_analysis_id' not in st.session_state:
            st.session_state.selected_analysis_id = None
        
        # Selection controls
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            # Analysis selection
            analysis_options = [(row['id'], row['name']) for _, row in analyses_df.iterrows() 
                              if row['id'] in st.session_state.selected_for_compare]
            if analysis_options:
                selected_option = st.selectbox(
                    "Select Analysis for Details:",
                    options=analysis_options,
                    format_func=lambda x: x[1],
                    key="analysis_detail_selector"
                )
                st.session_state.selected_analysis_id = selected_option[0] if selected_option else None
        
        with col2:
            # Date selection
            self._render_date_selection(analyses_df)
        
        with col3:
            # Action buttons
            self._render_analysis_action_buttons(analyses_df)
        
        # Show results
        self._render_portfolio_state_results(analyses_df)
        
        # Clear selections button
        if st.button("❌ Clear All Chart Selections"):
            st.session_state.selected_for_compare = []
            st.rerun()
    
    def _render_date_selection(self, analyses_df: pd.DataFrame) -> None:
        """Render date selection control."""
        if not st.session_state.selected_analysis_id:
            return
        
        analysis_matches = analyses_df[analyses_df['id'] == st.session_state.selected_analysis_id]
        if analysis_matches.empty:
            st.session_state.selected_analysis_id = None
            st.warning("Selected analysis not found in current portfolio. Please select a different analysis.")
            return
        
        selected_analysis = analysis_matches.iloc[0]
        start_date = selected_analysis['start_date']
        end_date = selected_analysis['end_date']
        
        selected_date = st.date_input(
            "📅 Choose Date for Portfolio Analysis:",
            value=end_date,
            min_value=start_date,
            max_value=end_date,
            key="analysis_date_selector",
            help="Select any date within the analysis period"
        )
        
        # Validate trading day
        if selected_date and 'portfolio_analysis_manager' in st.session_state:
            try:
                effective_date, date_reason = st.session_state.portfolio_analysis_manager.get_effective_trading_date(
                    selected_date, st.session_state.selected_analysis_id
                )
                
                if effective_date != selected_date:
                    st.info(f"📊 **Trading Day Adjustment**: {date_reason}")
                    st.info(f"🗓️ **Effective Analysis Date**: {effective_date.strftime('%A, %B %d, %Y')}")
                else:
                    st.success(f"✅ **{date_reason}**: {effective_date.strftime('%A, %B %d, %Y')}")
                
                st.session_state.selected_analysis_date = selected_date
                st.session_state.effective_analysis_date = effective_date
            except Exception as e:
                logger.error(f"Error validating trading date: {str(e)}")
    
    def _render_analysis_action_buttons(self, analyses_df: pd.DataFrame) -> None:
        """Render analysis action buttons."""
        # Analyze button
        if st.session_state.get('selected_analysis_date') and st.session_state.get('selected_analysis_id'):
            if st.button("📊 Analyze Portfolio", type="primary", use_container_width=True):
                self._handle_portfolio_analysis()
        
        # Refresh button
        if st.button("🔄 Refresh Chart"):
            if 'price_data_cache' in st.session_state:
                st.session_state.price_data_cache.clear()
                st.session_state.cache_expiry.clear()
            st.rerun()
    
    def _handle_portfolio_analysis(self) -> None:
        """Handle portfolio analysis request."""
        if 'portfolio_analysis_manager' not in st.session_state:
            st.error("Portfolio analysis manager not available")
            return
        
        try:
            portfolio_state = st.session_state.portfolio_analysis_manager.get_portfolio_state_at_date(
                st.session_state.selected_analysis_id,
                st.session_state.selected_analysis_date
            )
            st.session_state.portfolio_state_analysis = portfolio_state
            st.success(f"✅ Portfolio analyzed for {portfolio_state['effective_date']}")
            st.rerun()
        except Exception as e:
            logger.error(f"Error analyzing portfolio: {str(e)}")
            st.error(f"❌ Error analyzing portfolio: {str(e)}")
    
    def _render_portfolio_state_results(self, analyses_df: pd.DataFrame) -> None:
        """Render portfolio state analysis results."""
        if not st.session_state.get('portfolio_state_analysis'):
            if st.session_state.selected_analysis_id and st.session_state.selected_analysis_date:
                selected_analysis = analyses_df[analyses_df['id'] == st.session_state.selected_analysis_id].iloc[0]
                st.markdown(f"#### 🏢 Equity Analysis - {selected_analysis['name']} ({st.session_state.selected_analysis_date})")
                st.info("📊 **Click 'Analyze Portfolio' button above to see the portfolio state for the selected date**")
            else:
                st.info("💡 Select an analysis and date above to view detailed portfolio analysis")
            return
        
        portfolio_state = st.session_state.portfolio_state_analysis
        effective_date = portfolio_state['effective_date']
        selected_analysis = analyses_df[analyses_df['id'] == st.session_state.selected_analysis_id].iloc[0]
        
        st.markdown(f"#### 📊 Portfolio State Analysis - {selected_analysis['name']} ({effective_date})")
        
        # Portfolio summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("💰 Total Portfolio Value", f"HK${portfolio_state['total_portfolio_value']:,.2f}")
        with col2:
            st.metric("📈 Market Value", f"HK${portfolio_state['total_market_value']:,.2f}")
        with col3:
            st.metric("💵 Cash Position", f"HK${portfolio_state['cash_position']:,.2f}")
        with col4:
            st.metric("📋 Active Positions", portfolio_state['position_count'])
        
        # Date adjustment info
        if portfolio_state['target_date'] != portfolio_state['effective_date']:
            st.info(f"📅 **{portfolio_state['date_reason']}**: Analysis conducted for {effective_date.strftime('%A, %B %d, %Y')}")
        
        # Positions table
        self._render_portfolio_state_positions(portfolio_state)
    
    def _render_portfolio_state_positions(self, portfolio_state: Dict[str, Any]) -> None:
        """Render portfolio state positions table."""
        positions = portfolio_state.get('positions', [])
        if not positions:
            st.info("💼 Portfolio had no active positions on the selected date")
            return
        
        st.markdown("##### 🏢 Individual Holdings")
        
        # Table header
        header_cols = st.columns([1, 3, 1.2, 1.2, 1.2, 1.5, 1.5, 1])
        headers = ['Symbol', 'Company', 'Qty', 'Avg Cost', 'Current', 'Market Value', 'P&L', 'Detail']
        for col, header in zip(header_cols, headers):
            with col:
                st.markdown(f"**{header}**")
        
        # Position rows
        for position in positions:
            row_cols = st.columns([1, 3, 1.2, 1.2, 1.2, 1.5, 1.5, 1])
            
            with row_cols[0]:
                st.text(position['symbol'])
            
            with row_cols[1]:
                company_name = position.get('company_name', 'N/A')
                if len(company_name) > 25:
                    company_name = company_name[:22] + "..."
                st.text(company_name)
            
            with row_cols[2]:
                st.text(f"{position['quantity']:,}")
            
            with row_cols[3]:
                st.text(f"${position['avg_cost']:.2f}")
            
            with row_cols[4]:
                st.text(f"${position['current_price']:.2f}")
            
            with row_cols[5]:
                st.text(f"${position['market_value']:,.0f}")
            
            with row_cols[6]:
                pnl = position['unrealized_pnl']
                pnl_color = "green" if pnl >= 0 else "red"
                st.markdown(f"<span style='color: {pnl_color}'>${pnl:+,.0f}</span>", unsafe_allow_html=True)
            
            with row_cols[7]:
                if st.button("📋", key=f"detail_{position['symbol']}", help="Show technical details"):
                    st.session_state.show_technical_modal = position['symbol']
        
        # Technical modal
        self._render_technical_modal()
    
    def _render_technical_modal(self) -> None:
        """Render technical analysis modal."""
        if not st.session_state.get('show_technical_modal'):
            return
        
        symbol = st.session_state.show_technical_modal
        
        with st.container():
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 3, 1])
            with col2:
                st.markdown(f"### 📊 Technical Analysis: {symbol}")
                
                # Fetch technical data
                tech_data = self._fetch_technical_data(symbol)
                
                # Display metrics
                tech_col1, tech_col2, tech_col3 = st.columns(3)
                
                with tech_col1:
                    st.metric("Day High", f"${tech_data['day_high']:.2f}" if tech_data.get('day_high') else "N/A")
                    st.metric("Day Low", f"${tech_data['day_low']:.2f}" if tech_data.get('day_low') else "N/A")
                    st.metric("52-Week High", f"${tech_data['week_52_high']:.2f}" if tech_data.get('week_52_high') else "N/A")
                    st.metric("52-Week Low", f"${tech_data['week_52_low']:.2f}" if tech_data.get('week_52_low') else "N/A")
                
                with tech_col2:
                    st.metric("RSI (14)", f"{tech_data['rsi_14']:.1f}" if tech_data.get('rsi_14') else "N/A")
                    st.metric("RSI (9)", f"{tech_data['rsi_9']:.1f}" if tech_data.get('rsi_9') else "N/A")
                    st.metric("Volume", f"{tech_data['volume']:,}" if tech_data.get('volume') else "N/A")
                    st.metric("Volume Ratio", f"{tech_data['volume_ratio']:.2f}" if tech_data.get('volume_ratio') else "N/A")
                
                with tech_col3:
                    st.metric("EMA 12", f"${tech_data['ema_12']:.2f}" if tech_data.get('ema_12') else "N/A")
                    st.metric("EMA 26", f"${tech_data['ema_26']:.2f}" if tech_data.get('ema_26') else "N/A")
                    st.metric("SMA 50", f"${tech_data['sma_50']:.2f}" if tech_data.get('sma_50') else "N/A")
                    st.metric("SMA 200", f"${tech_data['sma_200']:.2f}" if tech_data.get('sma_200') else "N/A")
                
                # Action buttons
                close_col1, close_col2 = st.columns([1, 1])
                with close_col1:
                    if st.button("❌ Close", key="close_modal"):
                        st.session_state.show_technical_modal = None
                        st.rerun()
                with close_col2:
                    if st.button("📈 View Full Chart", key="view_chart"):
                        self._navigate_to_equity_analysis(symbol, tech_data)
                
                st.markdown("---")
    
    def _fetch_technical_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch technical analysis data for symbol."""
        try:
            # This would integrate with the actual technical analysis data fetching
            # For now, return placeholder data structure
            return {
                'symbol': symbol,
                'day_high': None,
                'day_low': None,
                'week_52_high': None,
                'week_52_low': None,
                'rsi_14': None,
                'rsi_9': None,
                'volume': None,
                'volume_ratio': None,
                'ema_12': None,
                'ema_26': None,
                'sma_50': None,
                'sma_200': None,
                'company_name': symbol
            }
        except Exception as e:
            logger.error(f"Error fetching technical data for {symbol}: {str(e)}")
            return {'symbol': symbol, 'company_name': symbol}
    
    def _navigate_to_equity_analysis(self, symbol: str, tech_data: Dict[str, Any]) -> None:
        """Navigate to equity analysis with context."""
        try:
            if st.session_state.selected_analysis_id:
                # Get analysis info for context
                if 'portfolio_analysis_manager' in st.session_state:
                    analyses_df = st.session_state.portfolio_analysis_manager.get_analysis_summary(
                        st.session_state.get('selected_portfolio', '')
                    )
                    analysis_matches = analyses_df[analyses_df['id'] == st.session_state.selected_analysis_id]
                    
                    if not analysis_matches.empty:
                        analysis_info = analysis_matches.iloc[0]
                        
                        # Set equity context
                        st.session_state.equity_context = {
                            'symbol': symbol,
                            'company_name': tech_data.get('company_name', symbol),
                            'portfolio_name': st.session_state.get('selected_portfolio', ''),
                            'portfolio_analysis_name': analysis_info['name'],
                            'start_date': str(analysis_info['start_date']),
                            'end_date': str(analysis_info['end_date'])
                        }
                        
                        # Navigate to equity analysis
                        self.navigate_to_page('equity_analysis')
                        st.rerun()
                        return
            
            # Fallback navigation without specific analysis context
            st.session_state.equity_context = {
                'symbol': symbol,
                'company_name': tech_data.get('company_name', symbol),
                'portfolio_name': 'Portfolio Analysis',
                'portfolio_analysis_name': 'Current Analysis',
                'start_date': (date.today() - timedelta(days=180)).strftime('%Y-%m-%d'),
                'end_date': date.today().strftime('%Y-%m-%d')
            }
            
            self.navigate_to_page('equity_analysis')
            st.rerun()
            
        except Exception as e:
            logger.error(f"Error navigating to equity analysis: {str(e)}")
            st.error("Error navigating to equity analysis")