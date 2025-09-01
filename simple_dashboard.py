import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="Portfolio Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("🏦 HK Strategy Portfolio Dashboard")
st.markdown("---")

def get_stock_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d")
        if not hist.empty:
            return float(hist['Close'].iloc[-1])
        return 100.0  # fallback price
    except:
        # Mock prices for demo
        mock_prices = {
            "AAPL": 175.0, 
            "GOOGL": 2800.0, 
            "MSFT": 350.0, 
            "TSLA": 250.0, 
            "AMZN": 3400.0
        }
        return mock_prices.get(ticker, 100.0)

# Initialize portfolio data
if 'portfolio_data' not in st.session_state:
    st.session_state.portfolio_data = [
        {"Ticker": "AAPL", "Quantity": 100, "Cost Basis": 150.0},
        {"Ticker": "GOOGL", "Quantity": 50, "Cost Basis": 2500.0},
        {"Ticker": "MSFT", "Quantity": 75, "Cost Basis": 300.0},
        {"Ticker": "TSLA", "Quantity": 30, "Cost Basis": 200.0},
        {"Ticker": "AMZN", "Quantity": 25, "Cost Basis": 3200.0}
    ]

# Sidebar for portfolio management
with st.sidebar:
    st.header("Portfolio Settings")
    st.subheader("Add/Edit Positions")
    
    ticker = st.text_input("Ticker Symbol", placeholder="e.g., AAPL").upper()
    quantity = st.number_input("Quantity", min_value=0, value=0)
    cost_basis = st.number_input("Cost Basis ($)", min_value=0.0, value=0.0, format="%.2f")
    
    if st.button("Add/Update Position") and ticker and quantity > 0:
        # Find if position exists
        existing = next((item for item in st.session_state.portfolio_data if item["Ticker"] == ticker), None)
        if existing:
            existing["Quantity"] = quantity
            existing["Cost Basis"] = cost_basis
            st.success(f"Updated {ticker}")
        else:
            st.session_state.portfolio_data.append({
                "Ticker": ticker,
                "Quantity": quantity,
                "Cost Basis": cost_basis
            })
            st.success(f"Added {ticker}")
        st.rerun()
    
    if st.button("Remove Position") and ticker:
        st.session_state.portfolio_data = [
            item for item in st.session_state.portfolio_data 
            if item["Ticker"] != ticker
        ]
        st.success(f"Removed {ticker}")
        st.rerun()

# Main dashboard
st.subheader("📊 Portfolio Overview")

# Debug info
st.info(f"Portfolio has {len(st.session_state.portfolio_data)} positions")

# Create portfolio table
portfolio_rows = []
total_value = 0
total_cost = 0

for position in st.session_state.portfolio_data:
    ticker = position["Ticker"]
    quantity = position["Quantity"]
    cost_basis = position["Cost Basis"]
    
    current_price = get_stock_price(ticker)
    market_value = current_price * quantity
    position_cost = cost_basis * quantity
    pnl = market_value - position_cost
    pnl_pct = (pnl / position_cost * 100) if position_cost > 0 else 0
    
    total_value += market_value
    total_cost += position_cost
    
    portfolio_rows.append({
        "Ticker": ticker,
        "Quantity": quantity,
        "Cost Basis": f"${cost_basis:.2f}",
        "Current Price": f"${current_price:.2f}",
        "Market Value": f"${market_value:,.2f}",
        "P&L": f"${pnl:,.2f}",
        "P&L %": f"{pnl_pct:+.2f}%"
    })

# Display metrics
col1, col2, col3, col4 = st.columns(4)
total_pnl = total_value - total_cost
total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0

with col1:
    st.metric("Portfolio Value", f"${total_value:,.2f}")
with col2:
    st.metric("Total Cost", f"${total_cost:,.2f}")
with col3:
    st.metric("Total P&L", f"${total_pnl:,.2f}", delta=f"{total_pnl_pct:+.2f}%")
with col4:
    st.metric("Positions", len(portfolio_rows))

st.markdown("---")

# Portfolio table
st.subheader("📋 Portfolio Positions")
if portfolio_rows:
    df = pd.DataFrame(portfolio_rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Simple charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Portfolio allocation
        values = [float(row["Market Value"].replace("$", "").replace(",", "")) for row in portfolio_rows]
        tickers = [row["Ticker"] for row in portfolio_rows]
        
        fig_pie = px.pie(
            values=values, 
            names=tickers,
            title="Portfolio Allocation"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # P&L chart
        pnl_values = [float(row["P&L"].replace("$", "").replace(",", "")) for row in portfolio_rows]
        
        fig_bar = px.bar(
            x=tickers,
            y=pnl_values,
            title="P&L by Position",
            color=pnl_values,
            color_continuous_scale=["red", "green"]
        )
        st.plotly_chart(fig_bar, use_container_width=True)

else:
    st.info("No portfolio positions found. Add positions using the sidebar.")

st.markdown("---")
st.caption("💡 This is a simplified version. Data refreshes on page reload.")