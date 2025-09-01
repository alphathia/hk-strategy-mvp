import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from datetime import datetime
import time

st.set_page_config(
    page_title="HK Strategy Portfolio Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("🏦 HK Strategy Portfolio Dashboard")
st.markdown("---")

# Initialize session state for prices and fetch details
if 'portfolio_prices' not in st.session_state:
    st.session_state.portfolio_prices = {}
    
if 'fetch_details' not in st.session_state:
    st.session_state.fetch_details = []
    
if 'last_update' not in st.session_state:
    st.session_state.last_update = None

def fetch_hk_price(hk_symbol):
    """Fetch current price for Hong Kong stock - returns price and status"""
    try:
        stock = yf.Ticker(hk_symbol)
        
        # Get recent historical data
        hist = stock.history(period="2d")
        if not hist.empty:
            price = float(hist['Close'].iloc[-1])
            return price, f"✅ {hk_symbol}: HK${price:.2f} (from history)"
        
        # Fallback to info
        info = stock.info
        current_price = info.get('currentPrice', info.get('regularMarketPrice', info.get('previousClose')))
        if current_price and current_price > 0:
            price = float(current_price)
            return price, f"📈 {hk_symbol}: HK${price:.2f} (from info)"
            
        # Use fallback price
        fallback_price = 75.0
        return fallback_price, f"⚠️ {hk_symbol}: Using fallback price HK${fallback_price:.2f}"
        
    except Exception as e:
        # Use recent real prices as fallback
        recent_prices = {
            "0005.HK": 100.10, "0316.HK": 140.50, "0388.HK": 447.60, "0700.HK": 599.00,
            "0823.HK": 41.26, "0857.HK": 7.39, "0939.HK": 7.49, "1810.HK": 53.20,
            "2888.HK": 144.50, "3690.HK": 116.30, "9618.HK": 121.30, "9988.HK": 121.50
        }
        price = recent_prices.get(hk_symbol, 75.0)
        return price, f"❌ {hk_symbol}: Error - using cached price HK${price:.2f}"

# HKEX Portfolio from init.sql
portfolio_data = [
    {"symbol": "0005.HK", "company_name": "HSBC Holdings plc", "quantity": 13428, "avg_cost": 38.50, "sector": "Financials"},
    {"symbol": "0316.HK", "company_name": "Orient Overseas", "quantity": 100, "avg_cost": 95.00, "sector": "Other"},
    {"symbol": "0388.HK", "company_name": "Hong Kong Exchanges", "quantity": 300, "avg_cost": 280.00, "sector": "Financials"},
    {"symbol": "0700.HK", "company_name": "Tencent Holdings Ltd", "quantity": 3100, "avg_cost": 320.50, "sector": "Tech"},
    {"symbol": "0823.HK", "company_name": "Link REIT", "quantity": 1300, "avg_cost": 42.80, "sector": "REIT"},
    {"symbol": "0939.HK", "company_name": "China Construction Bank", "quantity": 26700, "avg_cost": 5.45, "sector": "Financials"},
    {"symbol": "1810.HK", "company_name": "Xiaomi Corporation", "quantity": 2000, "avg_cost": 12.30, "sector": "Tech"},
    {"symbol": "2888.HK", "company_name": "Standard Chartered PLC", "quantity": 348, "avg_cost": 145.00, "sector": "Financials"},
    {"symbol": "3690.HK", "company_name": "Meituan", "quantity": 340, "avg_cost": 95.00, "sector": "Tech"},
    {"symbol": "9618.HK", "company_name": "JD.com", "quantity": 133, "avg_cost": 125.00, "sector": "Tech"},
    {"symbol": "9988.HK", "company_name": "Alibaba Group", "quantity": 2000, "avg_cost": 115.00, "sector": "Tech"}
]

# Filter out zero quantity positions
active_portfolio = [item for item in portfolio_data if item["quantity"] > 0]

st.subheader("📊 HKEX Portfolio Overview")

# Price update section
col1, col2 = st.columns([2, 1])

with col1:
    if st.button("🔄 Get Real-time Data", type="primary"):
        # Clear previous details
        st.session_state.fetch_details = []
        st.session_state.portfolio_prices = {}
        
        # Show progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_symbols = len(active_portfolio)
        
        for i, item in enumerate(active_portfolio):
            symbol = item["symbol"]
            status_text.text(f"Fetching {symbol} ({i+1}/{total_symbols})...")
            
            # Fetch price
            price, status = fetch_hk_price(symbol)
            st.session_state.portfolio_prices[symbol] = price
            st.session_state.fetch_details.append(status)
            
            # Update progress
            progress_bar.progress((i + 1) / total_symbols)
            
        st.session_state.last_update = datetime.now()
        status_text.text("✅ All prices updated!")
        time.sleep(1)
        status_text.empty()
        progress_bar.empty()
        st.rerun()

with col2:
    if st.session_state.last_update:
        st.info(f"Last updated: {st.session_state.last_update.strftime('%H:%M:%S')}")
    else:
        st.info("Using default prices - click button to update")

# Show fetch details in collapsible panel
if st.session_state.fetch_details:
    with st.expander("📋 Fetching Details (Click to expand)", expanded=False):
        for detail in st.session_state.fetch_details:
            st.text(detail)

# Process portfolio data
portfolio_display = []
total_value = total_cost = 0

for item in active_portfolio:
    symbol = item["symbol"]
    
    # Use fetched price or default
    if symbol in st.session_state.portfolio_prices:
        current_price = st.session_state.portfolio_prices[symbol]
    else:
        # Use reasonable default prices from init.sql data
        default_prices = {
            "0005.HK": 39.75, "0316.HK": 98.20, "0388.HK": 285.50, "0700.HK": 315.20,
            "0823.HK": 44.15, "0939.HK": 5.52, "1810.HK": 13.45, "2888.HK": 148.20,
            "3690.HK": 98.50, "9618.HK": 130.10, "9988.HK": 118.75
        }
        current_price = default_prices.get(symbol, 50.0)
    
    market_value = current_price * item["quantity"]
    position_cost = item["avg_cost"] * item["quantity"]
    pnl = market_value - position_cost
    pnl_pct = (pnl / position_cost * 100) if position_cost > 0 else 0
    
    total_value += market_value
    total_cost += position_cost
    
    portfolio_display.append({
        "Symbol": symbol,
        "Company": item["company_name"][:25] + "..." if len(item["company_name"]) > 25 else item["company_name"],
        "Quantity": f"{item['quantity']:,}",
        "Avg Cost": f"HK${item['avg_cost']:.2f}",
        "Current": f"HK${current_price:.2f}",
        "Market Value": market_value,
        "P&L": pnl,
        "P&L %": pnl_pct,
        "Sector": item["sector"]
    })

# Display metrics
st.markdown("### 💰 Portfolio Summary")
col1, col2, col3, col4 = st.columns(4)
total_pnl = total_value - total_cost
total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0

with col1:
    st.metric("Portfolio Value", f"HK${total_value:,.0f}")
with col2:
    st.metric("Total Cost", f"HK${total_cost:,.0f}")
with col3:
    delta_color = "normal" if total_pnl >= 0 else "inverse"
    st.metric("Total P&L", f"HK${total_pnl:,.0f}", delta=f"{total_pnl_pct:+.1f}%")
with col4:
    st.metric("Active Positions", len(portfolio_display))

st.markdown("---")

# Portfolio table
st.subheader("📋 HKEX Holdings")
if portfolio_display:
    df = pd.DataFrame(portfolio_display)
    
    # Format for display
    df_display = df.copy()
    df_display['Market Value'] = df_display['Market Value'].apply(lambda x: f"HK${x:,.0f}")
    df_display['P&L'] = df_display['P&L'].apply(lambda x: f"HK${x:,.0f}")
    df_display['P&L %'] = df_display['P&L %'].apply(lambda x: f"{x:+.1f}%")
    
    st.dataframe(
        df_display[['Symbol', 'Company', 'Quantity', 'Avg Cost', 'Current', 'Market Value', 'P&L', 'P&L %', 'Sector']], 
        use_container_width=True, 
        hide_index=True
    )
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        fig_pie = px.pie(
            df, 
            values='Market Value', 
            names='Symbol',
            title="Portfolio Allocation by Market Value"
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        fig_bar = px.bar(
            df, 
            x='Symbol', 
            y='P&L',
            title="P&L by Position",
            color='P&L',
            color_continuous_scale=['red', 'green']
        )
        fig_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")
st.caption("💰 HKEX portfolio data from init.sql • Real-time prices via Yahoo Finance API")