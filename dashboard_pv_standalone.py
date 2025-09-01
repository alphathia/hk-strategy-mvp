import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import numpy as np
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from database import DatabaseManager
from analysis_manager import AnalysisManager
from hkex_calendar import validate_hkex_analysis_period

st.set_page_config(
    page_title="HK Strategy Portfolio Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("🏦 HK Strategy Portfolio Dashboard")
st.markdown("---")

@st.cache_data(ttl=300)
def get_stock_price(hk_symbol):
    """
    Fetch current price for Hong Kong stock from Yahoo Finance
    Input: HKEX symbol like '0005.HK'
    """
    try:
        # Yahoo Finance expects HK symbols in format like '0005.HK'
        stock = yf.Ticker(hk_symbol)
        
        # Try to get recent price data
        hist = stock.history(period="2d")
        if not hist.empty:
            current_price = hist['Close'].iloc[-1]
            return float(current_price)
        
        # Fallback to info method
        info = stock.info
        current_price = info.get('currentPrice', info.get('regularMarketPrice', info.get('previousClose')))
        if current_price:
            return float(current_price)
        
        # If all else fails, return a reasonable HK stock price
        return 50.0
        
    except Exception as e:
        # Return mock prices for HK stocks for demo
        mock_prices = {
            "0005.HK": 39.75,  # HSBC
            "0316.HK": 98.20,  # Orient Overseas
            "0388.HK": 285.50, # HKEX
            "0700.HK": 315.20, # Tencent
            "0823.HK": 44.15,  # Link REIT
            "0857.HK": 7.80,   # PetroChina
            "0939.HK": 5.52,   # CCB
            "1810.HK": 13.45,  # Xiaomi
            "2888.HK": 148.20, # Standard Chartered
            "3690.HK": 98.50,  # Meituan
            "9618.HK": 130.10, # JD.com
            "9988.HK": 118.75  # Alibaba
        }
        return mock_prices.get(hk_symbol, 50.0)

@st.cache_data(ttl=300)
def get_stock_data(ticker, period="1mo"):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        return hist
    except Exception as e:
        st.warning(f"Could not fetch historical data for {ticker}: {str(e)}")
        return pd.DataFrame()

def calculate_portfolio_metrics(portfolio_df):
    total_value = portfolio_df['Market Value'].sum()
    total_cost = portfolio_df['Total Cost'].sum()
    total_pnl = total_value - total_cost
    total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
    
    return total_value, total_cost, total_pnl, total_pnl_pct

with st.sidebar:
    st.header("Portfolio Settings")
    
    # Initialize database connection
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    # Initialize analysis manager
    if 'analysis_manager' not in st.session_state:
        st.session_state.analysis_manager = AnalysisManager(st.session_state.db_manager)
    
    st.subheader("Portfolio Information")
    st.info("💡 Portfolio data is loaded from PostgreSQL database (init.sql)")
    st.markdown("**Current HKEX Holdings:**")
    st.markdown("- 0005.HK (HSBC Holdings)")
    st.markdown("- 0700.HK (Tencent Holdings)")
    st.markdown("- 0939.HK (China Construction Bank)")
    st.markdown("- 9988.HK (Alibaba Group)")
    st.markdown("- And 8 more positions...")
    
    with st.expander("🔧 Database Status"):
        try:
            test_df = st.session_state.db_manager.get_portfolio_positions()
            st.success(f"✅ Database connected - {len(test_df)} positions loaded")
            st.write("Database URL:", st.session_state.db_manager.db_url)
        except Exception as e:
            st.error(f"❌ Database connection failed: {str(e)}")
            st.info("Run: docker-compose up -d to start PostgreSQL")

# Load portfolio data from database
try:
    portfolio_df = st.session_state.db_manager.get_portfolio_positions()
    
    if portfolio_df.empty:
        st.error("No portfolio data available. Please check database connection.")
        st.info("Make sure PostgreSQL is running and the database is initialized with init.sql")
        st.stop()
    else:
        st.success(f"✅ Loaded {len(portfolio_df)} positions from database")
        
except Exception as e:
    st.error(f"Database connection failed: {str(e)}")
    st.info("Please ensure PostgreSQL is running and properly configured.")
    st.stop()

# Update current prices with Yahoo Finance data
with st.spinner("Updating current prices from Yahoo Finance..."):
    for idx, row in portfolio_df.iterrows():
        symbol = row['symbol']
        try:
            # Fetch current price for HK stock
            current_price = get_stock_price(symbol)
            
            # Update in database
            st.session_state.db_manager.update_position_price(symbol, current_price)
            
            # Update in dataframe for display
            portfolio_df.at[idx, 'current_price'] = current_price
            portfolio_df.at[idx, 'market_value'] = current_price * row['quantity']
            portfolio_df.at[idx, 'unrealized_pnl'] = (current_price - row['avg_cost']) * row['quantity']
            
        except Exception as e:
            st.warning(f"Could not update price for {symbol}: {str(e)}")

# Create portfolio display data
portfolio_list = []
for _, row in portfolio_df.iterrows():
    pnl_pct = (row['unrealized_pnl'] / (row['avg_cost'] * row['quantity']) * 100) if row['avg_cost'] * row['quantity'] > 0 else 0
    
    portfolio_list.append({
        "Symbol": row['symbol'],
        "Company": row['company_name'][:30] + "..." if len(str(row['company_name'])) > 30 else row['company_name'],
        "Quantity": f"{row['quantity']:,}",
        "Avg Cost": f"HK${row['avg_cost']:.2f}",
        "Current Price": f"HK${row['current_price']:.2f}",
        "Market Value": row['market_value'],
        "Total Cost": row['avg_cost'] * row['quantity'],
        "P&L": row['unrealized_pnl'],
        "P&L %": pnl_pct,
        "Sector": row['sector']
    })
    
    display_df = pd.DataFrame(portfolio_list)
    
    # Calculate totals
    total_value = sum([row['Market Value'] for row in portfolio_list])
    total_cost = sum([row['Total Cost'] for row in portfolio_list])
    total_pnl = sum([row['P&L'] for row in portfolio_list])
    total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Portfolio Value", f"${total_value:,.2f}")
    
    with col2:
        st.metric("Total Cost", f"${total_cost:,.2f}")
    
    with col3:
        color = "normal" if total_pnl >= 0 else "inverse"
        st.metric("Total P&L", f"${total_pnl:,.2f}", delta=f"{total_pnl_pct:.2f}%")
    
    with col4:
        st.metric("Number of Positions", len(portfolio_df))
    
    st.markdown("---")
    
    # Portfolio Value (PV) Chart Section
    st.subheader("📊 Portfolio Value Analysis")
    
    # Create tabs for different views
    pv_tab1, pv_tab2 = st.tabs(["📈 Create New Analysis", "📁 Load Previous Analysis"])
    
    with pv_tab1:
        # Date selection controls
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            start_date = st.date_input(
                "Analysis Start Date",
                value=date.today() - timedelta(days=180),  # Default 6 months ago
                max_value=date.today(),
                help="Select the start date for portfolio analysis"
            )
        
        with col2:
            end_date = st.date_input(
                "Analysis End Date", 
                value=date.today(),
                max_value=date.today(),
                help="Select the end date for portfolio analysis"
            )
        
        with col3:
            cash_amount = st.number_input(
                "Cash Amount (HKD)",
                min_value=0.0,
                value=0.0,
                step=10000.0,
                help="Cash component of portfolio"
            )
        
        # Validate dates
        if start_date and end_date:
            is_valid, message, adj_start, adj_end = validate_hkex_analysis_period(start_date, end_date)
            
            if not is_valid:
                st.error(f"❌ {message}")
            else:
                if adj_start != start_date or adj_end != end_date:
                    st.info(f"ℹ️ {message}")
                
                # Analysis controls
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    analysis_name = st.text_input(
                        "Analysis Name",
                        value=f"PV Analysis {adj_start} to {adj_end}",
                        help="Name for this analysis (required if saving)"
                    )
                
                with col2:
                    save_analysis = st.checkbox(
                        "Save Analysis",
                        value=True,
                        help="Save this analysis for future reference"
                    )
                
                with col3:
                    run_analysis = st.button(
                        "🚀 Run Analysis",
                        type="primary",
                        help="Calculate portfolio value for the selected period"
                    )
                
                # Run analysis when button is clicked
                if run_analysis:
                    if save_analysis and not analysis_name.strip():
                        st.error("Please provide an analysis name to save the results.")
                    else:
                        with st.spinner("Running portfolio analysis..."):
                            try:
                                # Get current portfolio positions
                                positions = st.session_state.db_manager.get_portfolio_positions_dict()
                                
                                if not positions:
                                    st.error("No portfolio positions found. Please check database connection.")
                                else:
                                    # Create analysis
                                    analysis_id, daily_values_df, metrics = st.session_state.analysis_manager.create_analysis(
                                        name=analysis_name,
                                        start_date=adj_start,
                                        end_date=adj_end,
                                        positions=positions,
                                        cash_amount=cash_amount,
                                        save_analysis=save_analysis
                                    )
                                    
                                    # Store results in session state for display
                                    st.session_state.current_analysis = {
                                        'id': analysis_id,
                                        'name': analysis_name,
                                        'daily_values': daily_values_df,
                                        'metrics': metrics,
                                        'start_date': adj_start,
                                        'end_date': adj_end,
                                        'cash_amount': cash_amount
                                    }
                                    
                                    st.success(f"✅ Analysis completed! {len(daily_values_df)} trading days analyzed.")
                                    if save_analysis:
                                        st.success(f"📁 Analysis saved with ID: {analysis_id}")
                                    
                            except Exception as e:
                                st.error(f"❌ Error running analysis: {str(e)}")
    
    with pv_tab2:
        # Load previous analysis
        st.write("**Load Previously Saved Analysis**")
        
        # Get list of saved analyses
        saved_analyses = st.session_state.db_manager.get_portfolio_analyses(limit=20)
        
        if saved_analyses.empty:
            st.info("No saved analyses found. Create a new analysis in the first tab.")
        else:
            # Format analysis list for display
            analysis_options = []
            for _, row in saved_analyses.iterrows():
                return_pct = row['total_return'] * 100
                analysis_options.append(
                    f"ID {row['id']}: {row['name']} ({row['start_date']} to {row['end_date']}) - {return_pct:+.2f}%"
                )
            
            selected_analysis = st.selectbox(
                "Select Analysis to Load:",
                options=range(len(analysis_options)),
                format_func=lambda x: analysis_options[x],
                help="Select a previously saved analysis to view"
            )
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                load_analysis = st.button("📁 Load Analysis", type="primary")
            
            with col2:
                if st.button("🗑️ Delete Selected", help="Delete the selected analysis"):
                    analysis_id = saved_analyses.iloc[selected_analysis]['id']
                    if st.session_state.db_manager.delete_portfolio_analysis(analysis_id):
                        st.success("✅ Analysis deleted successfully!")
                        st.experimental_rerun()
                    else:
                        st.error("❌ Failed to delete analysis.")
            
            # Load selected analysis
            if load_analysis:
                analysis_id = saved_analyses.iloc[selected_analysis]['id']
                
                with st.spinner("Loading analysis..."):
                    try:
                        analysis_info, daily_values_df, metrics = st.session_state.analysis_manager.load_analysis(analysis_id)
                        
                        # Store results in session state for display
                        st.session_state.current_analysis = {
                            'id': analysis_id,
                            'name': analysis_info['name'],
                            'daily_values': daily_values_df,
                            'metrics': metrics,
                            'start_date': analysis_info['start_date'],
                            'end_date': analysis_info['end_date'],
                            'cash_amount': 0.0,  # Not stored in analysis_info
                            'created_at': analysis_info['created_at']
                        }
                        
                        st.success(f"✅ Loaded analysis: {analysis_info['name']}")
                        
                    except Exception as e:
                        st.error(f"❌ Error loading analysis: {str(e)}")
    
    # Display current analysis results if available
    if 'current_analysis' in st.session_state:
        analysis = st.session_state.current_analysis
        daily_values_df = analysis['daily_values']
        metrics = analysis['metrics']
        
        st.markdown("---")
        st.subheader(f"📈 {analysis['name']}")
        
        # Display KPIs above chart
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "Start PV",
                f"HK${metrics.start_value:,.0f}",
                help="Portfolio value at start date"
            )
        
        with col2:
            st.metric(
                "End PV", 
                f"HK${metrics.end_value:,.0f}",
                delta=f"HK${metrics.total_return:,.0f}",
                help="Portfolio value at end date"
            )
        
        with col3:
            st.metric(
                "Total Return",
                f"{metrics.total_return_pct:+.2f}%",
                help="Total percentage return over the period"
            )
        
        with col4:
            st.metric(
                "Max Drawdown",
                f"{metrics.max_drawdown_pct:.2f}%",
                help="Maximum drawdown during the period"
            )
        
        with col5:
            st.metric(
                "Volatility",
                f"{metrics.volatility:.2f}%",
                help="Annualized volatility (standard deviation)"
            )
        
        # Create interactive PV chart
        fig = go.Figure()
        
        # Prepare hover data with daily changes and contributors
        hover_texts = []
        for _, row in daily_values_df.iterrows():
            hover_text = f"<b>{row['trade_date']}</b><br>"
            hover_text += f"Portfolio Value: HK${row['total_value']:,.0f}<br>"
            
            if pd.notna(row['daily_change']):
                hover_text += f"Daily Change: HK${row['daily_change']:+,.0f}<br>"
            
            if pd.notna(row['daily_return']):
                hover_text += f"Daily Return: {row['daily_return']*100:+.2f}%<br>"
            
            # Add top contributors
            if row['top_contributors'] and len(row['top_contributors']) > 0:
                hover_text += "<br><b>Top Contributors:</b><br>"
                for i, contrib in enumerate(row['top_contributors'][:3]):  # Show top 3
                    hover_text += f"• {contrib['symbol']}: HK${contrib['contribution']:+,.0f}<br>"
            
            hover_texts.append(hover_text)
        
        # Portfolio Value line
        fig.add_trace(go.Scatter(
            x=daily_values_df['trade_date'],
            y=daily_values_df['total_value'],
            mode='lines',
            name='Portfolio Value',
            line=dict(color='#1f77b4', width=2),
            hovertemplate='%{text}<extra></extra>',
            text=hover_texts
        ))
        
        # Add cash line if cash component exists
        if analysis['cash_amount'] > 0:
            fig.add_trace(go.Scatter(
                x=daily_values_df['trade_date'],
                y=daily_values_df['cash_value'],
                mode='lines',
                name='Cash',
                line=dict(color='green', width=1, dash='dash'),
                hovertemplate='<b>%{x}</b><br>' +
                             'Cash Value: HK$%{y:,.0f}<br>' +
                             '<extra></extra>'
            ))
        
        # Customize chart layout
        fig.update_layout(
            title=f"Portfolio Value Chart ({analysis['start_date']} to {analysis['end_date']})",
            xaxis_title="Date",
            yaxis_title="Value (HKD)",
            hovermode='x unified',
            showlegend=True,
            height=500
        )
        
        # Format y-axis
        fig.update_yaxis(tickformat=',.0f')
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Additional analysis details
        with st.expander("📊 Detailed Analysis", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Performance Summary:**")
                st.write(f"• Trading Days: {metrics.trading_days}")
                st.write(f"• Start Value: HK${metrics.start_value:,.0f}")
                st.write(f"• End Value: HK${metrics.end_value:,.0f}")
                st.write(f"• Absolute P&L: HK${metrics.total_return:+,.0f}")
                st.write(f"• Return %: {metrics.total_return_pct:+.2f}%")
                st.write(f"• Max Drawdown: {metrics.max_drawdown_pct:.2f}%")
                st.write(f"• Volatility: {metrics.volatility:.2f}%")
                if metrics.sharpe_ratio:
                    st.write(f"• Sharpe Ratio: {metrics.sharpe_ratio:.3f}")
            
            with col2:
                st.write("**Best & Worst Days:**")
                st.write(f"• Best Day: {metrics.best_day[0]} (+HK${metrics.best_day[1]:,.0f})")
                st.write(f"• Worst Day: {metrics.worst_day[0]} (HK${metrics.worst_day[1]:,.0f})")
                
                # Show recent top contributors
                if not daily_values_df.empty and daily_values_df.iloc[-1]['top_contributors']:
                    st.write("**Recent Top Contributors:**")
                    for contrib in daily_values_df.iloc[-1]['top_contributors']:
                        st.write(f"• {contrib['symbol']}: HK${contrib['contribution']:+,.0f} ({contrib['contribution_pct']:+.1f}%)")
    
    st.markdown("---")
    
    st.subheader("📊 HKEX Portfolio Holdings")
    
    # Format display values
    display_formatted = display_df.copy()
    display_formatted['Market Value'] = display_formatted['Market Value'].apply(lambda x: f"HK${x:,.2f}")
    display_formatted['P&L'] = display_formatted['P&L'].apply(lambda x: f"HK${x:,.2f}")
    display_formatted['P&L %'] = display_formatted['P&L %'].apply(lambda x: f"{x:+.2f}%")
    
    # Remove columns not needed for display
    display_cols = ['Symbol', 'Company', 'Quantity', 'Avg Cost', 'Current Price', 'Market Value', 'P&L', 'P&L %', 'Sector']
    
    st.dataframe(
        display_formatted[display_cols],
        use_container_width=True,
        hide_index=True
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Portfolio Allocation")
        fig_pie = px.pie(
            display_df, 
            values='Market Value', 
            names='Symbol',
            title="HKEX Portfolio Allocation"
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.subheader("P&L by Position")
        colors = ['green' if x >= 0 else 'red' for x in portfolio_df['P&L']]
        fig_bar = px.bar(
            display_df, 
            x='Symbol', 
            y='P&L',
            title="P&L by HKEX Position",
            color='P&L',
            color_continuous_scale=['red', 'green']
        )
        fig_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    st.markdown("---")
    
    selected_ticker = st.selectbox(
        "Select a HKEX symbol for detailed view:",
        options=display_df['Symbol'].tolist(),
        index=0
    )
    
    if selected_ticker:
        st.subheader(f"📈 {selected_ticker} - Detailed View")
        
        period_options = {
            "1 Week": "5d",
            "1 Month": "1mo", 
            "3 Months": "3mo",
            "6 Months": "6mo",
            "1 Year": "1y"
        }
        
        selected_period = st.selectbox(
            "Select time period:",
            options=list(period_options.keys()),
            index=1
        )
        
        hist_data = get_stock_data(selected_ticker, period_options[selected_period])
        
        if not hist_data.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hist_data.index,
                y=hist_data['Close'],
                mode='lines',
                name=f'{selected_ticker} Price',
                line=dict(color='blue', width=2)
            ))
            
            position_data = portfolio_df[portfolio_df['symbol'] == selected_ticker].iloc[0]
            cost_basis = position_data['avg_cost']
            
            fig.add_hline(
                y=cost_basis,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Cost Basis: ${cost_basis:.2f}"
            )
            
            fig.update_layout(
                title=f"{selected_ticker} Price History ({selected_period})",
                xaxis_title="Date",
                yaxis_title="Price ($)",
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            col1, col2, col3 = st.columns(3)
            current_price = get_stock_price(selected_ticker)
            
            with col1:
                st.metric("Current Price", f"HK${current_price:.2f}")
            
            with col2:
                pct_change = ((current_price - cost_basis) / cost_basis * 100) if cost_basis > 0 else 0
                st.metric("vs Cost Basis", f"{pct_change:+.2f}%")
            
            with col3:
                if len(hist_data) > 1:
                    period_change = ((hist_data['Close'].iloc[-1] - hist_data['Close'].iloc[0]) / hist_data['Close'].iloc[0] * 100)
                    st.metric(f"{selected_period} Change", f"{period_change:+.2f}%")
        else:
            st.error(f"Unable to fetch historical data for {selected_ticker}")

st.markdown("---")
st.caption("💰 HKEX equity data from PostgreSQL database. Prices updated via Yahoo Finance API.")