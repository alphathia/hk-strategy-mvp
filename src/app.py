import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
try:
    from database import DatabaseManager
except ImportError:
    from database_local import DatabaseManager
from strategy import HKStrategyEngine, RAILS, CURRENT_QTY, H03_BASELINE_QTY, WATCHLIST
import time
from datetime import datetime
import numpy as np

st.set_page_config(
    page_title="HK Equity Trading Strategy MVP",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def init_components():
    db = DatabaseManager()
    strategy_engine = HKStrategyEngine()
    return db, strategy_engine

def format_currency(amount):
    if amount >= 1e6:
        return f"${amount/1e6:.1f}M"
    elif amount >= 1e3:
        return f"${amount/1e3:.1f}K"
    else:
        return f"${amount:.2f}"

def format_percentage(value):
    return f"{value:.2f}%"

def main():
    st.title("🏢 HK Equity Trading Strategy MVP")
    
    db, strategy_engine = init_components()
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Portfolio Overview", "🎯 Trading Signals", "📈 Performance", "⚙️ Settings"])
    
    with tab1:
        st.header("Portfolio Positions")
        
        col1, col2, col3, col4 = st.columns(4)
        
        portfolio_df = db.get_portfolio_positions()
        
        if not portfolio_df.empty:
            total_value = portfolio_df['market_value'].sum()
            total_cost = (portfolio_df['avg_cost'] * portfolio_df['quantity']).sum()
            total_pnl = portfolio_df['unrealized_pnl'].sum()
            pnl_percentage = (total_pnl / total_cost) * 100 if total_cost > 0 else 0
            
            with col1:
                st.metric("Total Portfolio Value", format_currency(total_value))
            with col2:
                st.metric("Total P&L", format_currency(total_pnl), 
                         delta=f"{pnl_percentage:+.2f}%")
            with col3:
                st.metric("Positions", len(portfolio_df))
            with col4:
                avg_return = pnl_percentage
                st.metric("Avg Return", f"{avg_return:.2f}%")
            
            st.subheader("Position Details")
            
            display_df = portfolio_df.copy()
            display_df['market_value'] = display_df['market_value'].apply(format_currency)
            display_df['unrealized_pnl'] = display_df['unrealized_pnl'].apply(format_currency)
            display_df['avg_cost'] = display_df['avg_cost'].apply(lambda x: f"${x:.2f}")
            display_df['current_price'] = display_df['current_price'].apply(lambda x: f"${x:.2f}")
            
            st.dataframe(
                display_df,
                column_config={
                    "symbol": "Symbol",
                    "company_name": "Company",
                    "quantity": "Quantity", 
                    "avg_cost": "Avg Cost",
                    "current_price": "Current Price",
                    "market_value": "Market Value",
                    "unrealized_pnl": "P&L",
                    "sector": "Sector"
                },
                use_container_width=True,
                hide_index=True
            )
            
            st.subheader("Portfolio Allocation")
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_sector = px.pie(
                    portfolio_df, 
                    values='market_value', 
                    names='sector',
                    title="Allocation by Sector",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                st.plotly_chart(fig_sector, use_container_width=True)
            
            with col2:
                top_positions = portfolio_df.nlargest(5, 'market_value')
                fig_top = px.bar(
                    top_positions,
                    x='market_value',
                    y='symbol',
                    orientation='h',
                    title="Top 5 Positions by Value",
                    color='unrealized_pnl',
                    color_continuous_scale='RdYlGn'
                )
                fig_top.update_layout(yaxis=dict(categoryorder='total ascending'))
                st.plotly_chart(fig_top, use_container_width=True)
        
        else:
            st.warning("No portfolio data available. Please check database connection.")
    
    with tab2:
        st.header("Trading Signals")
        
        col1, col2 = st.columns([3, 1])
        
        with col2:
            if st.button("🔄 Generate New Signals", type="primary"):
                with st.spinner("Generating HK strategy signals..."):
                    try:
                        results = strategy_engine.generate_signals_for_watchlist()
                        st.success(f"Generated signals for {len(results)} tickers!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error generating signals: {str(e)}")
            
            st.subheader("Strategy Configuration")
            st.write("**Signal Types (TXYZN Format):**")
            st.write("• **BBRK9**: Strong BUY - Breakout (Strength: 9)")
            st.write("• **BRSV7**: Strong BUY - RSI Reversal (Strength: 7)")
            st.write("• **No Signal**: Neutral zone - no clear directional bias")
            st.write("• **SBRK3**: SELL - Breakdown (Strength: 3)")
            st.write("• **SOVB1**: SELL - Overbought (Strength: 1)")
            st.write("")
            st.write("**Format**: T-XYZ-N where:")
            st.write("• T: B=Buy, S=Sell")
            st.write("• XYZ: Strategy (BRK=Breakout, RSV=RSI Reversal, MOM=Momentum, OVB=Overbought)")
            st.write("• N: Strength (1-9, higher = stronger)")
            
            if st.button("📊 Run Full Strategy Analysis"):
                with st.spinner("Running comprehensive analysis..."):
                    try:
                        results = strategy_engine.generate_signals_for_watchlist()
                        performance = strategy_engine.get_portfolio_performance(results)
                        
                        st.success("Analysis complete!")
                        st.metric("Alpha vs H03", f"HK$ {performance['alpha']:,.0f}", 
                                 delta=f"{performance['alpha_pct']:+.2f}%")
                        st.metric("Portfolio Value", f"HK$ {performance['actual_value']:,.0f}")
                    except Exception as e:
                        st.error(f"Analysis error: {str(e)}")
        
        signals_df = db.get_trading_signals(limit=20)
        
        if not signals_df.empty:
            col1, col2, col3, col4 = st.columns(4)
            
            signal_counts = signals_df['signal_type'].value_counts()
            
            # Count both new and legacy signal types
            buy_signals = (signal_counts.get('A', 0) + signal_counts.get('B', 0) + 
                         signal_counts.get('BBRK9', 0) + signal_counts.get('BRSV7', 0) + 
                         signal_counts.get('BMOM7', 0) + signal_counts.get('BMOM9', 0))
            hold_signals = signal_counts.get('C', 0)  # Legacy C signals only
            sell_signals = (signal_counts.get('D', 0) + signal_counts.get('SBRK3', 0) + 
                          signal_counts.get('SOVB1', 0) + signal_counts.get('SMOM3', 0))
            
            with col1:
                st.metric("Buy Signals", buy_signals, 
                         help="All bullish signals (BXYZN, A, B)")
            with col2:
                st.metric("Hold Signals", hold_signals,
                         help="Neutral signals (legacy C only)") 
            with col3:
                st.metric("Sell Signals", sell_signals,
                         help="All bearish signals (SXYZN, D)")
            with col4:
                total_signals = buy_signals + hold_signals + sell_signals
                st.metric("Total Signals", total_signals,
                         help="All signals generated")
            
            st.subheader("Recent Signals")
            
            # Signal color mapping for new TXYZN and legacy A/B/C/D formats
            signal_colors = {
                # New TXYZN format
                'BBRK9': '#00C851', 'BRSV7': '#33B679', 'BMOM7': '#33B679', 'BMOM9': '#00C851',
 'SBRK3': '#FF4444', 'SOVB1': '#FF4444', 'SMOM3': '#FF4444',
                # Legacy format
                'A': '#00C851', 'B': '#33B679', 'C': '#FFB300', 'D': '#FF4444'
            }
            signal_descriptions = {
                # New TXYZN format
                'BBRK9': 'Strong BUY - Breakout above resistance (Strength: 9)',
                'BRSV7': 'Strong BUY - RSI Reversal recovery (Strength: 7)', 
                'BMOM7': 'BUY - Moderate momentum signal (Strength: 7)',
                'BMOM9': 'Strong BUY - High momentum signal (Strength: 9)',
                'SBRK3': 'SELL - Breakdown below support (Strength: 3)',
                'SOVB1': 'SELL - Overbought reversal (Strength: 1)',
                'SMOM3': 'SELL - Bearish momentum signal (Strength: 3)',
                # Legacy format
                'A': 'Strong BUY - Breakout above resistance',
                'B': 'Strong BUY - Oversold recovery', 
                'C': 'Strong SELL - Breakdown below support',
                'D': 'Strong TRIM - Overbought reversal'
            }
            
            for _, signal in signals_df.head(10).iterrows():
                color = signal_colors.get(signal['signal_type'], '#666666')
                description = signal_descriptions.get(signal['signal_type'], 'Unknown signal')
                
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 1, 2])
                    
                    with col1:
                        st.markdown(f'<div style="background-color: {color}; color: white; text-align: center; padding: 10px; border-radius: 5px; font-weight: bold;">{signal["signal_type"]}</div>', unsafe_allow_html=True)
                    
                    with col2:
                        st.write(f"**{signal['symbol']}**")
                        st.write(signal['company_name'] or 'N/A')
                    
                    with col3:
                        st.write(description)
                        st.write(f"Strength: {signal['signal_strength']:.2f}")
                    
                    with col4:
                        st.write(f"**${signal['price']:.2f}**")
                        if pd.notna(signal['rsi']):
                            st.write(f"RSI: {signal['rsi']:.1f}")
                    
                    with col5:
                        st.write(signal['created_at'].strftime("%Y-%m-%d %H:%M"))
                    
                    st.divider()
            
            st.subheader("Signal Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_signals = px.histogram(
                    signals_df, 
                    x='signal_type',
                    title="Signal Distribution",
                    color='signal_type',
                    color_discrete_map=signal_colors
                )
                st.plotly_chart(fig_signals, use_container_width=True)
            
            with col2:
                if 'rsi' in signals_df.columns:
                    fig_rsi = px.scatter(
                        signals_df,
                        x='rsi',
                        y='signal_strength', 
                        color='signal_type',
                        title="RSI vs Signal Strength",
                        color_discrete_map=signal_colors
                    )
                    st.plotly_chart(fig_rsi, use_container_width=True)
        
        else:
            st.info("No signals available. Click 'Generate New Signals' to create some!")
    
    with tab3:
        st.header("Performance Analytics")
        
        portfolio_df = db.get_portfolio_positions()
        signals_df = db.get_trading_signals(limit=100)
        
        if not portfolio_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("P&L Distribution")
                fig_pnl = px.bar(
                    portfolio_df,
                    x='symbol',
                    y='unrealized_pnl',
                    color='unrealized_pnl',
                    color_continuous_scale='RdYlGn',
                    title="Unrealized P&L by Position"
                )
                fig_pnl.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_pnl, use_container_width=True)
            
            with col2:
                st.subheader("Risk Metrics")
                portfolio_df['weight'] = portfolio_df['market_value'] / portfolio_df['market_value'].sum()
                portfolio_df['return_pct'] = (portfolio_df['unrealized_pnl'] / (portfolio_df['avg_cost'] * portfolio_df['quantity'])) * 100
                
                fig_risk = px.scatter(
                    portfolio_df,
                    x='weight',
                    y='return_pct',
                    size='market_value',
                    color='sector',
                    hover_data=['symbol'],
                    title="Risk-Return Profile"
                )
                st.plotly_chart(fig_risk, use_container_width=True)
        
        if not signals_df.empty:
            st.subheader("Signal Performance Over Time")
            signals_df['date'] = pd.to_datetime(signals_df['created_at']).dt.date
            daily_signals = signals_df.groupby(['date', 'signal_type']).size().reset_index(name='count')
            
            # Redefine signal_colors for this scope - support both formats
            signal_colors = {
                # New TXYZN format
                'BBRK9': '#00C851', 'BRSV7': '#33B679', 'BMOM7': '#33B679', 'BMOM9': '#00C851',
 'SBRK3': '#FF4444', 'SOVB1': '#FF4444', 'SMOM3': '#FF4444',
                # Legacy format
                'A': '#00C851', 'B': '#33B679', 'C': '#FFB300', 'D': '#FF4444'
            }
            fig_timeline = px.line(
                daily_signals,
                x='date',
                y='count',
                color='signal_type',
                title="Daily Signal Generation",
                color_discrete_map=signal_colors
            )
            st.plotly_chart(fig_timeline, use_container_width=True)
    
    with tab4:
        st.header("Strategy Settings")
        
        st.subheader("HK Strategy Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Signal Thresholds:**")
            st.write("• RSI Oversold: < 32")
            st.write("• RSI Overbought: ≥ 68") 
            st.write("• Breakout: Price > 20D-High + 0.35×ATR")
            st.write("• Breakdown: Price < EMA50 - 0.35×ATR")
            
            st.write("**Volume Confirmation:**")
            st.write("• A signals: ≥ 1.5× average volume")
            st.write("• B signals: ≥ 1.3× average volume")
            st.write("• C/D signals: ≥ 1.5×/1.3× volume")
        
        with col2:
            st.write("**Stock-Specific Rules (RAILS):**")
            for ticker, rules in RAILS.items():
                st.write(f"**{ticker}:**")
                for rule_type, value in rules.items():
                    if rule_type == "add_zone":
                        st.write(f"  - Add zone: {value[0]:.2f}-{value[1]:.2f}")
                    else:
                        st.write(f"  - {rule_type.replace('_', ' ').title()}: {value}")
            
            st.write("**Portfolio Quantities:**")
            current_total = sum(qty for qty in CURRENT_QTY.values() if qty > 0)
            st.metric("Active Positions", len([q for q in CURRENT_QTY.values() if q > 0]))
            st.metric("Total Shares", f"{current_total:,}")
        
        st.subheader("Database Status")
        
        try:
            portfolio_count = len(db.get_portfolio_positions())
            signals_count = len(db.get_trading_signals(limit=1000))
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.success(f"✅ PostgreSQL Connected")
                st.write(f"Positions: {portfolio_count}")
            
            with col2:
                try:
                    db.redis_client.ping()
                    st.success("✅ Redis Connected")
                except:
                    st.error("❌ Redis Disconnected")
            
            with col3:
                st.info(f"📊 Total Signals: {signals_count}")
        
        except Exception as e:
            st.error(f"❌ Database Error: {str(e)}")
        
        st.subheader("System Information")
        st.write(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.write("Strategy: HK Equity Momentum/Breakout Strategy")
        st.write("Signal Types (New TXYZN Format):")
        st.write("• BBRK9: Strong BUY (Breakout above resistance, Strength: 9)")
        st.write("• BRSV7: Strong BUY (RSI Reversal recovery, Strength: 7)")
        st.write("• No Signal: Neutral zone - no clear directional bias")
        st.write("• SBRK3: SELL (Breakdown below support, Strength: 3)")
        st.write("• SOVB1: SELL (Overbought reversal, Strength: 1)")
        st.write("")
        st.write("Signal Format: T-XYZ-N")
        st.write("• T: Trading action (B=Buy, S=Sell)")
        st.write("• XYZ: Strategy identifier (BRK=Breakout, RSV=RSI Reversal, MOM=Momentum, OVB=Overbought)")
        st.write("• N: Signal strength (1-9, where 9 is strongest)")
        from strategy import BASELINE_DATE, LOOKBACK_DAYS, USE_LIVE_QUOTES
        st.write(f"Baseline Date: {BASELINE_DATE}")
        st.write(f"Lookback Period: {LOOKBACK_DAYS} days")
        st.write(f"Live Quotes: {'Enabled' if USE_LIVE_QUOTES else 'Disabled'}")

if __name__ == "__main__":
    main()