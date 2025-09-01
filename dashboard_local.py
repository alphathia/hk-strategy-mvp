import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
from datetime import datetime

st.set_page_config(
    page_title="HK Strategy Portfolio Dashboard (Local)",
    page_icon="📈",
    layout="wide"
)

st.title("🏦 HK Strategy Portfolio Dashboard (Local PostgreSQL)")
st.markdown("---")

@st.cache_data(ttl=60)  # Shorter cache time for debugging
def get_stock_price(hk_symbol):
    """Fetch current price for Hong Kong stock from Yahoo Finance"""
    try:
        print(f"Fetching price for: {hk_symbol}")
        stock = yf.Ticker(hk_symbol)
        
        # Try historical data first (most reliable)
        hist = stock.history(period="2d")
        if not hist.empty:
            price = float(hist['Close'].iloc[-1])
            print(f"✅ Got price for {hk_symbol}: HK${price:.2f}")
            return price
        
        # Try info method as backup
        info = stock.info
        current_price = info.get('currentPrice', info.get('regularMarketPrice', info.get('previousClose')))
        if current_price and current_price > 0:
            price = float(current_price)
            print(f"📈 Got info price for {hk_symbol}: HK${price:.2f}")
            return price
            
        print(f"❌ No price data found for {hk_symbol}")
        return 50.0
        
    except Exception as e:
        print(f"💥 Error fetching {hk_symbol}: {str(e)}")
        # Return updated mock prices based on recent data
        mock_prices = {
            "0005.HK": 100.10, "0316.HK": 140.50, "0388.HK": 447.60, "0700.HK": 599.00,
            "0823.HK": 41.26, "0857.HK": 7.39, "0939.HK": 7.49, "1810.HK": 53.20,
            "2888.HK": 144.50, "3690.HK": 116.30, "9618.HK": 121.30, "9988.HK": 121.50
        }
        price = mock_prices.get(hk_symbol, 50.0)
        print(f"🔄 Using mock price for {hk_symbol}: HK${price:.2f}")
        return price

def get_db_connection():
    """Try different connection methods for local PostgreSQL"""
    connection_strings = [
        "postgresql://trader:YOUR_PASSWORD@localhost:5432/hk_strategy",
        "postgresql://postgres@localhost:5432/hk_strategy", 
        "postgresql://bthia@localhost:5432/hk_strategy",
        "postgresql://postgres:postgres@localhost:5432/hk_strategy"
    ]
    
    for conn_str in connection_strings:
        try:
            conn = psycopg2.connect(conn_str)
            st.success(f"✅ Connected using: {conn_str.split('@')[0]}@localhost")
            return conn
        except Exception as e:
            continue
    
    return None

def create_sample_data():
    """Create sample HKEX data if database connection fails"""
    return [
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

# Try to connect to database
with st.sidebar:
    st.header("Database Connection")
    
    conn = get_db_connection()
    
    if conn:
        try:
            # Try to fetch data from database
            query = "SELECT symbol, company_name, quantity, avg_cost, current_price, sector FROM portfolio_positions ORDER BY quantity * avg_cost DESC"
            portfolio_df = pd.read_sql(query, conn)
            conn.close()
            
            if portfolio_df.empty:
                st.warning("⚠️ Database connected but no portfolio data found")
                st.info("Run init.sql to populate data")
                portfolio_data = create_sample_data()
            else:
                st.success(f"✅ Loaded {len(portfolio_df)} positions from database")
                portfolio_data = portfolio_df.to_dict('records')
                
        except Exception as e:
            st.error(f"❌ Database query failed: {str(e)}")
            st.info("Using sample HKEX data instead")
            portfolio_data = create_sample_data()
    else:
        st.error("❌ Cannot connect to PostgreSQL")
        st.info("Using sample HKEX data from init.sql")
        portfolio_data = create_sample_data()
    
    st.markdown("**Setup Instructions:**")
    st.code("sudo -u postgres createuser trader")
    st.code("sudo -u postgres createdb hk_strategy -O trader") 
    st.code("psql -U trader -d hk_strategy -f init.sql")

# Process portfolio data
st.subheader("📊 HKEX Portfolio Overview")

portfolio_display = []
total_value = total_cost = 0

with st.spinner("Updating prices from Yahoo Finance..."):
    for item in portfolio_data:
        current_price = get_stock_price(item["symbol"])
        market_value = current_price * item["quantity"]
        position_cost = item["avg_cost"] * item["quantity"]
        pnl = market_value - position_cost
        pnl_pct = (pnl / position_cost * 100) if position_cost > 0 else 0
        
        total_value += market_value
        total_cost += position_cost
        
        portfolio_display.append({
            "Symbol": item["symbol"],
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
        st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")
st.caption("💰 HKEX data from init.sql • Prices via Yahoo Finance API")