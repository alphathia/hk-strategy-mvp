import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from datetime import datetime
import time

st.set_page_config(
    page_title="HK Strategy Multi-Portfolio Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("🏦 HK Strategy Multi-Portfolio Dashboard")
st.markdown("---")

# Initialize session state for portfolios and prices
if 'portfolios' not in st.session_state:
    st.session_state.portfolios = {
        "HKEX_Base": {
            "name": "HKEX Base Portfolio",
            "description": "Primary Hong Kong equity holdings from init.sql",
            "positions": [
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
        }
    }

if 'portfolio_prices' not in st.session_state:
    st.session_state.portfolio_prices = {}
    
if 'fetch_details' not in st.session_state:
    st.session_state.fetch_details = {}
    
if 'last_update' not in st.session_state:
    st.session_state.last_update = {}

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

# Portfolio Selection
st.sidebar.header("📁 Portfolio Management")

# Portfolio selector
selected_portfolio = st.sidebar.selectbox(
    "Select Portfolio:",
    options=list(st.session_state.portfolios.keys()),
    format_func=lambda x: f"{x} ({len([p for p in st.session_state.portfolios[x]['positions'] if p['quantity'] > 0])} positions)"
)

# Portfolio info
current_portfolio = st.session_state.portfolios[selected_portfolio]
st.sidebar.markdown(f"**{current_portfolio['name']}**")
st.sidebar.markdown(f"*{current_portfolio['description']}*")

# Add new portfolio section
st.sidebar.markdown("---")
st.sidebar.subheader("➕ Add New Portfolio")

new_portfolio_id = st.sidebar.text_input("Portfolio ID:", placeholder="e.g., US_Growth")
new_portfolio_name = st.sidebar.text_input("Portfolio Name:", placeholder="e.g., US Growth Stocks")
new_portfolio_desc = st.sidebar.text_area("Description:", placeholder="Portfolio description...")

if st.sidebar.button("Create Portfolio"):
    if new_portfolio_id and new_portfolio_name and new_portfolio_id not in st.session_state.portfolios:
        st.session_state.portfolios[new_portfolio_id] = {
            "name": new_portfolio_name,
            "description": new_portfolio_desc or "New portfolio",
            "positions": []
        }
        st.sidebar.success(f"✅ Created portfolio: {new_portfolio_id}")
        st.rerun()
    else:
        st.sidebar.error("❌ Invalid portfolio ID or already exists")

# Main dashboard content
st.subheader(f"📊 {current_portfolio['name']}")

# Get active positions (quantity > 0)
active_positions = [pos for pos in current_portfolio['positions'] if pos['quantity'] > 0]

if not active_positions:
    st.warning("This portfolio has no active positions (quantity > 0)")
    st.stop()

# Price update section
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    if st.button(f"🔄 Get Real-time Data for {selected_portfolio}", type="primary"):
        # Initialize portfolio-specific storage
        if selected_portfolio not in st.session_state.portfolio_prices:
            st.session_state.portfolio_prices[selected_portfolio] = {}
        if selected_portfolio not in st.session_state.fetch_details:
            st.session_state.fetch_details[selected_portfolio] = []
            
        # Clear previous details
        st.session_state.fetch_details[selected_portfolio] = []
        st.session_state.portfolio_prices[selected_portfolio] = {}
        
        # Show progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_symbols = len(active_positions)
        
        for i, position in enumerate(active_positions):
            symbol = position["symbol"]
            status_text.text(f"Fetching {symbol} ({i+1}/{total_symbols})...")
            
            # Fetch price
            price, status = fetch_hk_price(symbol)
            st.session_state.portfolio_prices[selected_portfolio][symbol] = price
            st.session_state.fetch_details[selected_portfolio].append(status)
            
            # Update progress
            progress_bar.progress((i + 1) / total_symbols)
            
        st.session_state.last_update[selected_portfolio] = datetime.now()
        status_text.text("✅ All prices updated!")
        time.sleep(1)
        status_text.empty()
        progress_bar.empty()
        st.rerun()

with col2:
    if selected_portfolio in st.session_state.last_update:
        st.info(f"Last updated: {st.session_state.last_update[selected_portfolio].strftime('%H:%M:%S')}")
    else:
        st.info("Using default prices")

with col3:
    st.metric("Active Positions", len(active_positions))

# Show fetch details in collapsible panel
if selected_portfolio in st.session_state.fetch_details and st.session_state.fetch_details[selected_portfolio]:
    with st.expander("📋 Price Fetching Details (Click to expand)", expanded=False):
        for detail in st.session_state.fetch_details[selected_portfolio]:
            st.text(detail)

# Process portfolio data
portfolio_display = []
total_value = total_cost = 0

for position in active_positions:
    symbol = position["symbol"]
    
    # Use fetched price or default
    if (selected_portfolio in st.session_state.portfolio_prices and 
        symbol in st.session_state.portfolio_prices[selected_portfolio]):
        current_price = st.session_state.portfolio_prices[selected_portfolio][symbol]
    else:
        # Use reasonable default prices from init.sql data
        default_prices = {
            "0005.HK": 39.75, "0316.HK": 98.20, "0388.HK": 285.50, "0700.HK": 315.20,
            "0823.HK": 44.15, "0939.HK": 5.52, "1810.HK": 13.45, "2888.HK": 148.20,
            "3690.HK": 98.50, "9618.HK": 130.10, "9988.HK": 118.75
        }
        current_price = default_prices.get(symbol, 50.0)
    
    market_value = current_price * position["quantity"]
    position_cost = position["avg_cost"] * position["quantity"]
    pnl = market_value - position_cost
    pnl_pct = (pnl / position_cost * 100) if position_cost > 0 else 0
    
    total_value += market_value
    total_cost += position_cost
    
    portfolio_display.append({
        "Symbol": symbol,
        "Company": position["company_name"][:25] + "..." if len(position["company_name"]) > 25 else position["company_name"],
        "Quantity": f"{position['quantity']:,}",
        "Avg Cost": f"HK${position['avg_cost']:.2f}",
        "Current": f"HK${current_price:.2f}",
        "Market Value": market_value,
        "P&L": pnl,
        "P&L %": pnl_pct,
        "Sector": position["sector"]
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
    st.metric("Total P&L", f"HK${total_pnl:,.0f}", delta=f"{total_pnl_pct:+.1f}%")
with col4:
    st.metric("Positions", len(portfolio_display))

st.markdown("---")

# Portfolio table
st.subheader(f"📋 {selected_portfolio} Holdings")
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

# Portfolio overview section
st.markdown("---")
st.subheader("📊 All Portfolios Overview")

overview_data = []
for portfolio_id, portfolio_info in st.session_state.portfolios.items():
    active_pos = [pos for pos in portfolio_info['positions'] if pos['quantity'] > 0]
    
    # Calculate basic metrics (using default prices if not updated)
    total_val = 0
    for pos in active_pos:
        if (portfolio_id in st.session_state.portfolio_prices and 
            pos['symbol'] in st.session_state.portfolio_prices[portfolio_id]):
            price = st.session_state.portfolio_prices[portfolio_id][pos['symbol']]
        else:
            default_prices = {
                "0005.HK": 39.75, "0316.HK": 98.20, "0388.HK": 285.50, "0700.HK": 315.20,
                "0823.HK": 44.15, "0939.HK": 5.52, "1810.HK": 13.45, "2888.HK": 148.20,
                "3690.HK": 98.50, "9618.HK": 130.10, "9988.HK": 118.75
            }
            price = default_prices.get(pos['symbol'], 50.0)
        total_val += price * pos['quantity']
    
    last_update = st.session_state.last_update.get(portfolio_id, "Never")
    if last_update != "Never":
        last_update = last_update.strftime('%H:%M:%S')
    
    overview_data.append({
        "Portfolio": portfolio_id,
        "Name": portfolio_info['name'],
        "Positions": len(active_pos),
        "Value": f"HK${total_val:,.0f}",
        "Last Updated": last_update
    })

if overview_data:
    overview_df = pd.DataFrame(overview_data)
    st.dataframe(overview_df, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("💰 Multi-portfolio dashboard • Real-time prices via Yahoo Finance API")