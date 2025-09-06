"""
Equity Analysis Page for HK Strategy Dashboard.
Provides equity strategy analysis with technical indicators and chart visualization.

Extracted from dashboard.py lines 3562-4318.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date, timedelta

from src.pages.base_page import BasePage

# Setup logging
logger = logging.getLogger(__name__)


class EquityAnalysisPage(BasePage):
    """Equity analysis page with technical indicators and chart visualization."""
    
    def __init__(self):
        super().__init__('equity_analysis')
    
    def _render_content(self) -> None:
        """Render the equity analysis page content."""
        # Compact styling
        self._render_compact_styling()
        
        # Debug toggle
        self._render_debug_toggle()
        
        # Initialize states
        self._init_equity_states()
        
        # Handle equity context from navigation
        self._handle_equity_context()
        
        # Date selection panel
        self._render_date_selection()
        
        # Selection method choice
        self._render_selection_method()
        
        # Display chart if data is ready
        self._render_chart_section()
        
        # Navigation buttons
        self._render_navigation_buttons()
    
    def _render_compact_styling(self) -> None:
        """Render compact CSS styling."""
        st.markdown("""
        <style>
        /* Compact styling for Equity Strategy Analysis */
        .stSelectbox label {
            font-size: 12px !important;
            font-weight: normal !important;
        }
        .stSelectbox div[data-testid="stSelectbox"] > div {
            font-size: 12px !important;
        }
        .stDateInput label {
            font-size: 12px !important;
            font-weight: normal !important;
        }
        .stMultiSelect label {
            font-size: 12px !important;
            font-weight: normal !important;
        }
        .stCheckbox label {
            font-size: 12px !important;
        }
        /* Metric elements - 14px bold font size */
        .stMetric label {
            font-size: 14px !important;
            font-weight: bold !important;
        }
        .stMetric div {
            font-size: 14px !important;
            font-weight: bold !important;
        }
        /* Reduce metric spacing */
        .metric-container {
            padding: 5px !important;
        }
        </style>
        <div style='margin-bottom: 15px;'>
            <h3 style='font-size: 18px; margin: 0; color: #1f77b4;'>📈 Equity Strategy Analysis</h3>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_debug_toggle(self) -> None:
        """Render debug toggle."""
        debug_col1, debug_col2 = st.columns([4, 1])
        with debug_col2:
            debug_mode = st.checkbox("🔍 Debug Mode", help="Enable debug information for troubleshooting equity population")
            st.session_state.debug_mode = debug_mode
    
    def _init_equity_states(self) -> None:
        """Initialize equity-related session states."""
        if 'equity_portfolio_id' not in st.session_state:
            st.session_state.equity_portfolio_id = None
        if 'equity_symbol' not in st.session_state:
            st.session_state.equity_symbol = None
        if 'equity_start_date' not in st.session_state:
            st.session_state.equity_start_date = datetime.now().date() - timedelta(days=365)
        if 'equity_end_date' not in st.session_state:
            st.session_state.equity_end_date = datetime.now().date()
        if 'confirmed_indicators' not in st.session_state:
            st.session_state.confirmed_indicators = []
        if 'show_indicators_clicked' not in st.session_state:
            st.session_state.show_indicators_clicked = False
    
    def _handle_equity_context(self) -> None:
        """Handle equity context from navigation."""
        portfolios = self._get_all_portfolios_for_equity_analysis()
        
        # Check if we came from portfolio analysis or overview navigation
        if 'equity_context' in st.session_state:
            equity_ctx = st.session_state.equity_context
            # Pre-populate selections from context
            for p in portfolios:
                if p['name'] == equity_ctx.get('portfolio_name'):
                    st.session_state.equity_portfolio_id = p['portfolio_id']
                    break
        
        # Handle navigation from All Portfolio Overview → stock selection
        if not st.session_state.equity_portfolio_id and 'selected_stock_context' in st.session_state:
            st.session_state.equity_portfolio_id = 'all_overview'
            stock_ctx = st.session_state.selected_stock_context
            st.session_state.equity_symbol = stock_ctx.get('symbol')
    
    def _render_date_selection(self) -> None:
        """Render date selection panel."""
        st.markdown("#### 📅 Analysis Period")
        date_col1, date_col2, date_col3 = st.columns([2, 2, 1])
        
        with date_col1:
            start_date = st.date_input(
                "Start Date",
                value=st.session_state.equity_start_date,
                max_value=datetime.now().date(),
                key="equity_start_date_picker"
            )
            st.session_state.equity_start_date = start_date
        
        with date_col2:
            end_date = st.date_input(
                "End Date",
                value=st.session_state.equity_end_date,
                min_value=st.session_state.equity_start_date,
                max_value=datetime.now().date(),
                key="equity_end_date_picker"
            )
            st.session_state.equity_end_date = end_date
        
        with date_col3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("📅 Reset to 12M", help="Reset to 12 months ago"):
                st.session_state.equity_start_date = datetime.now().date() - timedelta(days=365)
                st.session_state.equity_end_date = datetime.now().date()
                st.rerun()
        
        st.markdown("---")
    
    def _render_selection_method(self) -> None:
        """Render selection method interface."""
        st.markdown("#### 📊 Analysis Method")
        selection_method = st.radio(
            "Choose how to select equity for analysis:",
            ["Portfolio-based Selection", "Direct Symbol Entry"],
            index=0,
            horizontal=True,
            help="Portfolio-based: Select from existing portfolio holdings. Direct: Select from all known securities."
        )
        
        go_clicked = False
        can_proceed = False
        
        if selection_method == "Direct Symbol Entry":
            go_clicked, can_proceed = self._render_direct_selection()
        else:
            go_clicked, can_proceed = self._render_portfolio_selection()
        
        # Process analysis when Go is clicked
        if go_clicked and can_proceed:
            self._process_analysis()
    
    def _render_direct_selection(self) -> Tuple[bool, bool]:
        """Render direct symbol selection interface."""
        st.markdown("**Direct Symbol Analysis** - Select from all known securities in portfolios")
        
        all_securities = self._get_equities_from_portfolio('all_overview')
        
        if not all_securities:
            st.warning("⚠️ No securities found in any portfolios. Please create portfolios with positions first.")
            return False, False
        
        direct_col1, direct_go = st.columns([5, 1])
        
        with direct_col1:
            # Create dropdown options
            security_options = []
            for security in all_securities:
                company_name = security['company_name']
                if len(company_name) > 30:
                    company_name = company_name[:27] + "..."
                security_options.append(f"{security['symbol']} - {company_name}")
            
            # Find current selection index
            current_index = 0
            if st.session_state.get('direct_selected_security'):
                for i, option in enumerate(security_options):
                    if option.startswith(st.session_state.direct_selected_security):
                        current_index = i
                        break
            
            selected_security_display = st.selectbox(
                f"📈 Select Security ({len(security_options)} available)",
                options=security_options,
                index=current_index,
                key="direct_security_selector",
                help="Select any security from all your portfolios (active and inactive positions)"
            )
            
            if selected_security_display:
                selected_symbol = selected_security_display.split(' - ')[0]
                st.session_state.direct_selected_security = selected_symbol
                selected_security_info = next(s for s in all_securities if s['symbol'] == selected_symbol)
                st.session_state.direct_security_info = selected_security_info
        
        with direct_go:
            st.markdown("<br>", unsafe_allow_html=True)
            can_proceed = bool(st.session_state.get('direct_selected_security'))
            go_clicked = st.button("🚀 Analyze", type="primary", disabled=not can_proceed)
        
        return go_clicked, can_proceed
    
    def _render_portfolio_selection(self) -> Tuple[bool, bool]:
        """Render portfolio-based selection interface."""
        st.markdown("**Portfolio-based Selection** - Choose from existing portfolio holdings")
        
        portfolios = self._get_all_portfolios_for_equity_analysis()
        select_col1, select_col2, go_col = st.columns([4, 5, 1])
        
        with select_col1:
            # Portfolio selection
            portfolio_options = []
            for p in portfolios:
                name = p['name']
                if len(name) > 20:
                    name = name[:17] + "..."
                portfolio_options.append(f"{p['portfolio_id']} ({name})")
            
            selected_portfolio_display = st.selectbox(
                "📁 Portfolio",
                options=portfolio_options,
                index=0 if portfolio_options else None,
                key="portfolio_selector"
            )
            
            if selected_portfolio_display:
                selected_portfolio_id = selected_portfolio_display.split(' ')[0]
                
                # Clear equity selection if portfolio changes
                if st.session_state.equity_portfolio_id != selected_portfolio_id:
                    st.session_state.equity_symbol = None
                    
                st.session_state.equity_portfolio_id = selected_portfolio_id
        
        with select_col2:
            if st.session_state.equity_portfolio_id:
                equities = self._get_equities_from_portfolio(st.session_state.equity_portfolio_id)
                
                if equities:
                    # Equity selection
                    equity_options = []
                    for e in equities:
                        company_name = e['company_name']
                        if len(company_name) > 25:
                            company_name = company_name[:22] + "..."
                        equity_options.append(f"{e['symbol']} - {company_name}")
                    
                    # Find current selection index
                    current_index = 0
                    if st.session_state.equity_symbol:
                        for i, option in enumerate(equity_options):
                            if option.startswith(st.session_state.equity_symbol):
                                current_index = i
                                break
                    
                    portfolio_name = next(p['name'] for p in portfolios if p['portfolio_id'] == st.session_state.equity_portfolio_id)
                    
                    selected_equity_display = st.selectbox(
                        f"📈 Equity ({len(equity_options)} available)",
                        options=equity_options,
                        index=current_index,
                        key="equity_selector",
                        help=f"All equities from {portfolio_name} (including both active and inactive positions)"
                    )
                    
                    if selected_equity_display:
                        selected_symbol = selected_equity_display.split(' - ')[0]
                        st.session_state.equity_symbol = selected_symbol
                else:
                    # No equities found
                    portfolio_name = next(p['name'] for p in portfolios if p['portfolio_id'] == st.session_state.equity_portfolio_id)
                    st.selectbox(
                        "📈 Equity", 
                        options=[], 
                        disabled=True,
                        help=f"No equities found in {portfolio_name}"
                    )
                    st.warning(f"⚠️ No equities found in portfolio '{portfolio_name}'. Please select a different portfolio.")
            else:
                st.selectbox("📈 Equity", options=[], disabled=True, help="Select a portfolio first")
        
        with go_col:
            st.markdown("<br>", unsafe_allow_html=True)
            can_proceed = bool(st.session_state.equity_portfolio_id and st.session_state.equity_symbol)
            go_clicked = st.button("🚀 Go", type="primary", disabled=not can_proceed)
        
        return go_clicked, can_proceed
    
    def _process_analysis(self) -> None:
        """Process equity analysis request."""
        try:
            if st.session_state.get('direct_selected_security'):
                # Direct analysis
                self._process_direct_analysis()
            else:
                # Portfolio-based analysis
                self._process_portfolio_analysis()
        except Exception as e:
            logger.error(f"Error processing analysis: {str(e)}")
            st.error(f"❌ Error processing analysis: {str(e)}")
    
    def _process_direct_analysis(self) -> None:
        """Process direct symbol analysis."""
        selected_info = st.session_state.direct_security_info
        start_date_str = st.session_state.equity_start_date.strftime('%Y-%m-%d')
        end_date_str = st.session_state.equity_end_date.strftime('%Y-%m-%d')
        
        data_fetched = self._fetch_and_store_yahoo_data(
            st.session_state.direct_selected_security,
            start_date_str,
            end_date_str
        )
        
        if data_fetched:
            equity_ctx = {
                'portfolio_id': "direct_analysis",
                'portfolio_name': "Direct Analysis",
                'portfolio_analysis_name': "Custom Date Range",
                'symbol': selected_info['symbol'],
                'company_name': selected_info['company_name'],
                'start_date': start_date_str,
                'end_date': end_date_str
            }
            
            st.session_state.equity_context = equity_ctx
            st.session_state.chart_data_ready = True
            st.success(f"✅ Successfully loaded data for {selected_info['symbol']} - {selected_info['company_name']}")
        else:
            st.error("❌ Failed to fetch data. Please try a different security.")
    
    def _process_portfolio_analysis(self) -> None:
        """Process portfolio-based analysis."""
        portfolios = self._get_all_portfolios_for_equity_analysis()
        selected_portfolio = next(p for p in portfolios if p['portfolio_id'] == st.session_state.equity_portfolio_id)
        selected_equity = next(e for e in self._get_equities_from_portfolio(st.session_state.equity_portfolio_id) 
                             if e['symbol'] == st.session_state.equity_symbol)
        
        start_date_str = st.session_state.equity_start_date.strftime('%Y-%m-%d')
        end_date_str = st.session_state.equity_end_date.strftime('%Y-%m-%d')
        
        data_fetched = self._fetch_and_store_yahoo_data(
            st.session_state.equity_symbol,
            start_date_str,
            end_date_str
        )
        
        if data_fetched:
            equity_ctx = {
                'portfolio_id': st.session_state.equity_portfolio_id,
                'portfolio_name': selected_portfolio['name'],
                'portfolio_analysis_name': "Custom Date Range",
                'symbol': st.session_state.equity_symbol,
                'company_name': selected_equity['company_name'],
                'start_date': start_date_str,
                'end_date': end_date_str
            }
            
            st.session_state.equity_context = equity_ctx
            st.session_state.chart_data_ready = True
        else:
            st.error("❌ Failed to fetch data. Please try again or select a different date range.")
    
    def _render_chart_section(self) -> None:
        """Render chart section if data is ready."""
        if not st.session_state.get('chart_data_ready', False) or 'equity_context' not in st.session_state:
            return
        
        equity_ctx = st.session_state.equity_context
        
        # Display context information
        self._render_context_info(equity_ctx)
        
        # Technical indicators configuration
        self._render_technical_indicators_config()
        
        # Candlestick chart
        self._render_candlestick_chart(equity_ctx)
    
    def _render_context_info(self, equity_ctx: Dict[str, Any]) -> None:
        """Render context information."""
        st.markdown("---")
        info_col1, info_col2, info_col3, info_col4, info_col5 = st.columns([1, 1.5, 1.5, 2, 1.5])
        
        with info_col1:
            st.metric("Analysis", "Equity Strategy")
        with info_col2:
            st.metric("Portfolio", equity_ctx['portfolio_name'])
        with info_col3:
            analysis_name = equity_ctx['portfolio_analysis_name']
            if len(analysis_name) > 20:
                analysis_name = analysis_name[:20] + "..."
            st.metric("Analysis", analysis_name)
        with info_col4:
            company_name = equity_ctx['company_name']
            if len(company_name) > 15:
                company_name = company_name[:15] + "..."
            st.metric("Stock", f"{equity_ctx['symbol']} - {company_name}")
        with info_col5:
            st.metric("Period", f"{equity_ctx['start_date']} to {equity_ctx['end_date']}")
        
        st.markdown("---")
    
    def _render_technical_indicators_config(self) -> None:
        """Render technical indicators configuration."""
        st.markdown("#### ⚙️ Technical Indicators Configuration")
        
        indicator_col1, indicator_col2 = st.columns([3, 1])
        with indicator_col1:
            # Show currently selected indicators
            if st.session_state.confirmed_indicators:
                available_indicators = self._get_available_indicators()
                selected_names = []
                for code in st.session_state.confirmed_indicators:
                    name = next((name for name, c in available_indicators if c == code), code)
                    selected_names.append(name)
                st.markdown(f"**Selected Indicators:** {', '.join(selected_names)}")
            else:
                st.markdown("**No technical indicators selected**")
        
        with indicator_col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("📊 Select Indicators", type="primary"):
                self._show_select_indicators_dialog()
        
        # Configuration panel
        if st.session_state.confirmed_indicators:
            self._render_indicators_config_panel()
    
    def _render_indicators_config_panel(self) -> None:
        """Render indicators configuration panel."""
        with st.expander("⚙️ Indicator Configuration & Calculation Methods", expanded=False):
            st.markdown("#### How Technical Indicators are Calculated:")
            
            for indicator_code in st.session_state.confirmed_indicators:
                if indicator_code in ['rsi_7', 'rsi_14', 'rsi_21']:
                    st.markdown("""
                    **RSI (Relative Strength Index):**
                    - Period: Variable (7, 14, or 21 days based on selection)
                    - Formula: RSI = 100 - (100 / (1 + RS))
                    - RS = Average Gain / Average Loss over N periods
                    - Uses exponential moving average for smoothing
                    - Values: 0-100 (>70 overbought, <30 oversold)
                    """)
                elif indicator_code in ['macd', 'macd_signal']:
                    st.markdown("""
                    **MACD (Moving Average Convergence Divergence):**
                    - Fast EMA: 12 periods, Slow EMA: 26 periods, Signal: 9 periods
                    - MACD Line = EMA(12) - EMA(26)
                    - Signal Line = EMA(9) of MACD Line
                    - Histogram = MACD Line - Signal Line
                    - Buy signal when MACD crosses above Signal Line
                    """)
                elif indicator_code in ['ema_12', 'ema_26', 'ema_50', 'ema_100']:
                    period = indicator_code.split('_')[1]
                    st.markdown(f"""
                    **EMA ({period}) - Exponential Moving Average:**
                    - Period: {period} days
                    - More responsive to recent price changes than SMA
                    - Used for trend identification and support/resistance
                    """)
            
            # Configuration options
            col1, col2, col3 = st.columns(3)
            with col1:
                use_realtime = st.checkbox("Use Real-time Calculation", value=True, 
                                         help="Calculate indicators from price data instead of database")
            with col2:
                rsi_period = st.slider("RSI Period", min_value=7, max_value=21, value=14)
            with col3:
                macd_fast = st.slider("MACD Fast", min_value=8, max_value=16, value=12)
    
    def _render_candlestick_chart(self, equity_ctx: Dict[str, Any]) -> None:
        """Render candlestick chart with technical indicators."""
        st.markdown(f"### 📊 {equity_ctx['symbol']} Price Chart")
        
        try:
            # Convert date strings to datetime objects
            start_dt = datetime.strptime(equity_ctx['start_date'], '%Y-%m-%d')
            end_dt = datetime.strptime(equity_ctx['end_date'], '%Y-%m-%d')
            
            with st.spinner(f"Loading price data for {equity_ctx['symbol']}..."):
                # Fetch stock data using yfinance
                ticker = yf.Ticker(equity_ctx['symbol'])
                hist_data = ticker.history(start=start_dt, end=end_dt)
            
            if hist_data.empty:
                st.error(f"❌ No price data found for {equity_ctx['symbol']} in the specified period.")
                return
            
            # Create basic candlestick chart
            fig = go.Figure(data=go.Candlestick(
                x=hist_data.index,
                open=hist_data['Open'],
                high=hist_data['High'],
                low=hist_data['Low'],
                close=hist_data['Close'],
                name=equity_ctx['symbol']
            ))
            
            # Add technical indicators if selected
            self._add_technical_indicators_to_chart(fig, hist_data)
            
            # Display chart
            st.plotly_chart(fig, use_container_width=True)
            
            # Show key statistics
            self._render_key_statistics(hist_data)
            
            # Volume chart
            self._render_volume_chart(equity_ctx, hist_data)
            
            # Reset indicator click flag
            if st.session_state.show_indicators_clicked:
                st.session_state.show_indicators_clicked = False
                    
        except Exception as e:
            logger.error(f"Error loading chart data: {str(e)}")
            st.error(f"❌ Error loading chart data: {str(e)}")
            st.info("💡 Make sure the stock symbol is correct and has available data on Yahoo Finance.")
    
    def _add_technical_indicators_to_chart(self, fig: go.Figure, hist_data: pd.DataFrame) -> None:
        """Add technical indicators to chart."""
        if not (st.session_state.show_indicators_clicked and st.session_state.confirmed_indicators):
            return
        
        with st.spinner("Calculating technical indicators..."):
            try:
                indicator_data = self._calculate_technical_indicators(hist_data)
                
                if indicator_data:
                    # Add indicators to chart
                    self._add_indicators_to_figure(fig, indicator_data)
                    
                    # Show indicator summary
                    self._render_indicators_summary(indicator_data)
                    
            except Exception as e:
                logger.error(f"Error calculating technical indicators: {str(e)}")
                st.warning(f"⚠️ Error calculating technical indicators: {str(e)}")
    
    def _calculate_technical_indicators(self, hist_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate technical indicators from price data."""
        indicator_data = {}
        
        for indicator_code in st.session_state.confirmed_indicators:
            try:
                if indicator_code in ['rsi_7', 'rsi_14', 'rsi_21']:
                    period = int(indicator_code.split('_')[1])
                    rsi_values = self._calculate_rsi(hist_data['Close'], period)
                    indicator_data[indicator_code] = {
                        'dates': hist_data.index.tolist(),
                        'values': rsi_values.tolist()
                    }
                elif indicator_code in ['ema_12', 'ema_26', 'ema_50', 'ema_100']:
                    period = int(indicator_code.split('_')[1])
                    ema_values = hist_data['Close'].ewm(span=period).mean()
                    indicator_data[indicator_code] = {
                        'dates': hist_data.index.tolist(),
                        'values': ema_values.tolist()
                    }
                elif indicator_code == 'macd':
                    ema_12 = hist_data['Close'].ewm(span=12).mean()
                    ema_26 = hist_data['Close'].ewm(span=26).mean()
                    macd_line = ema_12 - ema_26
                    indicator_data[indicator_code] = {
                        'dates': hist_data.index.tolist(),
                        'values': macd_line.tolist()
                    }
                elif indicator_code == 'macd_signal':
                    ema_12 = hist_data['Close'].ewm(span=12).mean()
                    ema_26 = hist_data['Close'].ewm(span=26).mean()
                    macd_line = ema_12 - ema_26
                    signal_line = macd_line.ewm(span=9).mean()
                    indicator_data[indicator_code] = {
                        'dates': hist_data.index.tolist(),
                        'values': signal_line.tolist()
                    }
                elif indicator_code == 'sma_20':
                    sma_values = hist_data['Close'].rolling(window=20).mean()
                    indicator_data[indicator_code] = {
                        'dates': hist_data.index.tolist(),
                        'values': sma_values.tolist()
                    }
                elif indicator_code in ['bollinger_upper', 'bollinger_lower', 'bollinger_middle']:
                    sma_20 = hist_data['Close'].rolling(window=20).mean()
                    std_20 = hist_data['Close'].rolling(window=20).std()
                    
                    if indicator_code == 'bollinger_upper':
                        values = sma_20 + (2 * std_20)
                    elif indicator_code == 'bollinger_lower':
                        values = sma_20 - (2 * std_20)
                    else:  # bollinger_middle
                        values = sma_20
                        
                    indicator_data[indicator_code] = {
                        'dates': hist_data.index.tolist(),
                        'values': values.tolist()
                    }
            except Exception as e:
                logger.warning(f"Error calculating {indicator_code}: {str(e)}")
        
        return indicator_data
    
    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _add_indicators_to_figure(self, fig: go.Figure, indicator_data: Dict[str, Any]) -> None:
        """Add indicators to the figure."""
        available_indicators = self._get_available_indicators()
        
        # Separate Bollinger Bands from regular indicators
        bollinger_indicators = {}
        regular_indicators = {}
        
        for indicator_code, data in indicator_data.items():
            if indicator_code in ['bollinger_upper', 'bollinger_lower', 'bollinger_middle']:
                bollinger_indicators[indicator_code] = data
            else:
                regular_indicators[indicator_code] = data
        
        # Handle Bollinger Bands
        self._add_bollinger_bands_to_figure(fig, bollinger_indicators)
        
        # Handle regular indicators
        if regular_indicators:
            colors = ['blue', 'purple', 'orange', 'brown', 'pink']
            for i, (indicator_code, data) in enumerate(regular_indicators.items()):
                if i < len(colors):
                    display_name = next((name for name, code in available_indicators if code == indicator_code), indicator_code)
                    
                    fig.add_trace(go.Scatter(
                        x=data['dates'],
                        y=data['values'],
                        mode='lines',
                        name=display_name,
                        line=dict(color=colors[i], width=2),
                        yaxis='y2'
                    ))
        
        # Update layout
        self._update_chart_layout_with_indicators(fig, regular_indicators)
    
    def _add_bollinger_bands_to_figure(self, fig: go.Figure, bollinger_indicators: Dict[str, Any]) -> None:
        """Add Bollinger Bands to figure."""
        if 'bollinger_upper' in bollinger_indicators:
            fig.add_trace(go.Scatter(
                x=bollinger_indicators['bollinger_upper']['dates'],
                y=bollinger_indicators['bollinger_upper']['values'],
                mode='lines',
                name='BB Upper',
                line=dict(color='rgba(255, 0, 0, 0.8)', width=1, dash='dot'),
                showlegend=True
            ))
        
        if 'bollinger_lower' in bollinger_indicators:
            fig.add_trace(go.Scatter(
                x=bollinger_indicators['bollinger_lower']['dates'],
                y=bollinger_indicators['bollinger_lower']['values'],
                mode='lines',
                name='BB Lower',
                line=dict(color='rgba(0, 255, 0, 0.8)', width=1, dash='dot'),
                showlegend=True
            ))
        
        if 'bollinger_middle' in bollinger_indicators:
            fig.add_trace(go.Scatter(
                x=bollinger_indicators['bollinger_middle']['dates'],
                y=bollinger_indicators['bollinger_middle']['values'],
                mode='lines',
                name='BB Middle (SMA20)',
                line=dict(color='rgba(128, 128, 128, 0.8)', width=1),
                showlegend=True
            ))
        
        # Add shaded area between bands
        if 'bollinger_upper' in bollinger_indicators and 'bollinger_lower' in bollinger_indicators:
            fig.add_trace(go.Scatter(
                x=bollinger_indicators['bollinger_upper']['dates'],
                y=bollinger_indicators['bollinger_upper']['values'],
                mode='lines',
                line=dict(width=0),
                showlegend=False,
                hoverinfo='skip'
            ))
            fig.add_trace(go.Scatter(
                x=bollinger_indicators['bollinger_lower']['dates'],
                y=bollinger_indicators['bollinger_lower']['values'],
                mode='lines',
                fill='tonexty',
                fillcolor='rgba(68, 68, 68, 0.1)',
                line=dict(width=0),
                name='Bollinger Band',
                showlegend=True,
                hovertemplate='Bollinger Band Zone<extra></extra>'
            ))
    
    def _update_chart_layout_with_indicators(self, fig: go.Figure, regular_indicators: Dict[str, Any]) -> None:
        """Update chart layout with indicators."""
        equity_ctx = st.session_state.equity_context
        
        layout_config = {
            'title': f"{equity_ctx['company_name']} ({equity_ctx['symbol']}) - Price Chart with Technical Analysis<br><sub>Period: {equity_ctx['start_date']} to {equity_ctx['end_date']}</sub>",
            'yaxis': dict(title="Price (HKD)", side='left'),
            'xaxis_title': "Date",
            'height': 650,
            'showlegend': True,
            'xaxis_rangeslider_visible': False,
            'legend': dict(
                x=0,
                y=1,
                bgcolor='rgba(255, 255, 255, 0.8)',
                bordercolor='rgba(0, 0, 0, 0.2)',
                borderwidth=1
            )
        }
        
        # Add secondary y-axis only if there are regular indicators
        if regular_indicators:
            layout_config['yaxis2'] = dict(
                title="Indicator Values",
                side='right',
                overlaying='y',
                showgrid=False,
                zeroline=False
            )
        
        fig.update_layout(**layout_config)
    
    def _render_indicators_summary(self, indicator_data: Dict[str, Any]) -> None:
        """Render indicators summary."""
        with st.expander("📊 Technical Indicators Summary", expanded=False):
            available_indicators = self._get_available_indicators()
            indicator_col1, indicator_col2, indicator_col3 = st.columns(3)
            
            for i, (indicator_code, data) in enumerate(indicator_data.items()):
                display_name = next((name for name, code in available_indicators if code == indicator_code), indicator_code)
                latest_value = data['values'][-1] if data['values'] else 'N/A'
                col = [indicator_col1, indicator_col2, indicator_col3][i % 3]
                with col:
                    if isinstance(latest_value, (int, float)):
                        st.metric(display_name, f"{latest_value:.2f}")
                    else:
                        st.metric(display_name, str(latest_value))
    
    def _render_key_statistics(self, hist_data: pd.DataFrame) -> None:
        """Render key statistics."""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Start Price", f"HK${hist_data['Close'].iloc[0]:.2f}")
        with col2:
            st.metric("End Price", f"HK${hist_data['Close'].iloc[-1]:.2f}")
        with col3:
            price_change = hist_data['Close'].iloc[-1] - hist_data['Close'].iloc[0]
            price_change_pct = (price_change / hist_data['Close'].iloc[0]) * 100
            st.metric("Total Return", f"{price_change_pct:+.2f}%", f"HK${price_change:+.2f}")
        with col4:
            volatility = hist_data['Close'].pct_change().std() * (252 ** 0.5) * 100
            st.metric("Volatility (Annual)", f"{volatility:.2f}%")
    
    def _render_volume_chart(self, equity_ctx: Dict[str, Any], hist_data: pd.DataFrame) -> None:
        """Render volume chart."""
        fig_volume = go.Figure()
        fig_volume.add_trace(go.Bar(
            x=hist_data.index,
            y=hist_data['Volume'],
            name='Volume',
            marker_color='lightblue'
        ))
        
        fig_volume.update_layout(
            title=f"{equity_ctx['symbol']} - Trading Volume",
            yaxis_title="Volume",
            xaxis_title="Date",
            height=300,
            showlegend=False
        )
        
        st.plotly_chart(fig_volume, use_container_width=True)
    
    def _render_navigation_buttons(self) -> None:
        """Render navigation buttons."""
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("🔙 Back to Portfolios", type="secondary"):
                self.navigate_to_page('overview')
                st.rerun()
        
        with col2:
            st.markdown("*This dashboard will be triggered from Portfolio Value Analysis*")
        
        with col3:
            if st.button("📊 Go to PV Analysis", type="primary"):
                self.navigate_to_page('pv_analysis')
                st.rerun()
    
    def _get_all_portfolios_for_equity_analysis(self) -> List[Dict[str, Any]]:
        """Get all portfolios for equity analysis."""
        # This would integrate with the portfolio service
        try:
            portfolios = st.session_state.get('portfolios', {})
            return [
                {
                    'portfolio_id': portfolio_id,
                    'name': portfolio_data.get('name', 'Unnamed Portfolio')
                }
                for portfolio_id, portfolio_data in portfolios.items()
            ]
        except Exception as e:
            logger.error(f"Error getting portfolios: {str(e)}")
            return []
    
    def _get_equities_from_portfolio(self, portfolio_id: str) -> List[Dict[str, Any]]:
        """Get equities from portfolio."""
        try:
            if portfolio_id == 'all_overview':
                # Get all unique securities from all portfolios
                all_securities = []
                seen_symbols = set()
                
                portfolios = st.session_state.get('portfolios', {})
                for portfolio_data in portfolios.values():
                    positions = portfolio_data.get('positions', [])
                    for pos in positions:
                        symbol = pos.get('symbol', '')
                        if symbol and symbol not in seen_symbols:
                            all_securities.append({
                                'symbol': symbol,
                                'company_name': pos.get('company_name', 'Unknown')
                            })
                            seen_symbols.add(symbol)
                
                return all_securities
            else:
                # Get securities from specific portfolio
                portfolios = st.session_state.get('portfolios', {})
                if portfolio_id in portfolios:
                    positions = portfolios[portfolio_id].get('positions', [])
                    return [
                        {
                            'symbol': pos.get('symbol', ''),
                            'company_name': pos.get('company_name', 'Unknown')
                        }
                        for pos in positions
                        if pos.get('symbol')
                    ]
        except Exception as e:
            logger.error(f"Error getting equities from portfolio {portfolio_id}: {str(e)}")
        
        return []
    
    def _fetch_and_store_yahoo_data(self, symbol: str, start_date: str, end_date: str) -> bool:
        """Fetch and store Yahoo Finance data."""
        try:
            ticker = yf.Ticker(symbol)
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            hist_data = ticker.history(start=start_dt, end=end_dt)
            return not hist_data.empty
        except Exception as e:
            logger.error(f"Error fetching Yahoo data for {symbol}: {str(e)}")
            return False
    
    def _get_available_indicators(self) -> List[Tuple[str, str]]:
        """Get list of available indicators."""
        return [
            ("RSI (7)", "rsi_7"), ("RSI (14)", "rsi_14"), ("RSI (21)", "rsi_21"),
            ("MACD", "macd"), ("MACD Signal", "macd_signal"), ("SMA (20)", "sma_20"),
            ("EMA (12)", "ema_12"), ("EMA (26)", "ema_26"), ("EMA (50)", "ema_50"),
            ("EMA (100)", "ema_100"), ("Bollinger Upper", "bollinger_upper"),
            ("Bollinger Middle", "bollinger_middle"), ("Bollinger Lower", "bollinger_lower"), 
            ("Volume SMA (20)", "volume_sma_20")
        ]
    
    def _show_select_indicators_dialog(self) -> None:
        """Show select indicators dialog."""
        st.session_state['show_select_indicators_dialog'] = True