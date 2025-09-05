#!/usr/bin/env python3
"""
Minimal Dashboard - Strategy Base Catalog Only
Clean, focused version containing only the working Strategy Base Catalog functionality
"""

import streamlit as st
import pandas as pd
import sys
import os

# Load environment variables first (critical for database connection)
from dotenv import load_dotenv
load_dotenv()

# Import database manager
sys.path.append('src')
try:
    from src.database import DatabaseManager
except ImportError:
    from database import DatabaseManager

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="HK Strategy MVP - Strategy Base Catalog",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# SIDEBAR
# =============================================================================

st.sidebar.markdown("# ⚙️ Strategy Base Catalog")
st.sidebar.markdown("*Comprehensive strategy documentation and analysis*")
st.sidebar.markdown("---")
st.sidebar.info("💡 **Focus Mode**: This minimal dashboard contains only the Strategy Base Catalog functionality for testing and development.")

# =============================================================================
# STRATEGY HELPER FUNCTIONS (EXTRACTED FROM MAIN DASHBOARD)
# =============================================================================

def _get_strategy_intent(base_strategy: str) -> str:
    """Get strategy intent description"""
    intents = {
        'BBRK': 'Momentum continuation after credible breakout',
        'BOSR': 'Mean-reversion entry when oversold conditions reclaimed',
        'BMAC': 'Trend shift via fast/slow EMA golden cross (12/26)',
        'BBOL': 'Buy bounce off lower band toward mean', 
        'BDIV': 'Momentum divergence - lower price low, higher oscillator low',
        'BSUP': 'Buy bounce at MA/BB support levels',
        'SBDN': 'Momentum continuation downward after credible breakdown',
        'SOBR': 'Mean-reversion short when overbought conditions fail',
        'SMAC': 'Trend shift down via fast/slow EMA bearish cross (12/26)', 
        'SDIV': 'Momentum divergence - higher price high, lower oscillator high',
        'SRES': 'Fade rally that fails at resistance (BB upper/key MAs)'
    }
    return intents.get(base_strategy, 'Professional trading strategy')

def _get_base_trigger(base_strategy: str) -> str:
    """Get base trigger condition"""
    triggers = {
        'BBRK': 'Close crosses above Bollinger Upper (20,2σ)',
        'BOSR': 'Close crosses above BB Lower OR RSI(7) crosses up through 30',
        'BMAC': 'EMA12 crosses above EMA26 (today)',
        'BBOL': 'Intraday low touches/breaks Lower, close finishes back above Lower',
        'BDIV': 'RSI(14) bullish divergence OR MACD histogram bullish divergence',
        'BSUP': 'Touch/undercut {SMA20, EMA50, EMA100, BB Middle}, close back above',
        'SBDN': 'Close crosses below Bollinger Lower',
        'SOBR': 'Close rejects BB Upper OR RSI(7) crosses down through 70', 
        'SMAC': 'EMA12 crosses below EMA26',
        'SDIV': 'RSI(14) bearish divergence OR MACD histogram bearish divergence',
        'SRES': 'Touch/overrun {SMA20, EMA50, EMA100, BB Upper}, close back below'
    }
    return triggers.get(base_strategy, 'Professional technical trigger')

def _display_strategy_details(cur, base_strategy: str, side: str, category: str):
    """Display comprehensive strategy details with level breakdown"""
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 Overview", 
        "🎯 Level Rules", 
        "📊 Technical Requirements", 
        "💼 Examples"
    ])
    
    with tab1:
        _display_strategy_overview(base_strategy, side, category)
    
    with tab2:
        _display_level_breakdown(cur, base_strategy)
    
    with tab3:
        _display_technical_requirements(base_strategy)
    
    with tab4:
        _display_strategy_examples(base_strategy)

def _display_strategy_overview(base_strategy: str, side: str, category: str):
    """Display strategy overview information"""
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown(f"**Intent:** {_get_strategy_intent(base_strategy)}")
        st.markdown(f"**Base Trigger:** {_get_base_trigger(base_strategy)}")
        st.markdown(f"**Category:** {category.title()}")
        st.markdown(f"**Side:** {'Buy' if side == 'B' else 'Sell'} Strategy")
        
        # Strategy characteristics
        characteristics = _get_strategy_characteristics(base_strategy)
        if characteristics:
            st.markdown("**Key Characteristics:**")
            for char in characteristics:
                st.markdown(f"• {char}")
    
    with col2:
        st.markdown("**Signal Strength Levels:**")
        st.markdown("🔴 **Level 1-3:** Weak signals (experimental)")
        st.markdown("🟡 **Level 4-6:** Moderate signals (standard)")
        st.markdown("🟢 **Level 7-9:** Strong signals (institutional)")
        
        # Show TXYZN examples
        st.markdown("\n**TXYZN Examples:**")
        for level in [1, 5, 9]:
            strength_desc = {1: "Weak", 5: "Moderate", 9: "Extreme"}[level]
            st.markdown(f"• `{base_strategy}{level}` - {strength_desc}")

def _display_level_breakdown(cur, base_strategy: str):
    """Display detailed level-by-level rule breakdown"""
    st.markdown("### 🎯 Level-by-Level Rule Progression")
    st.markdown("*Each level requires ALL previous conditions PLUS new ones*")
    
    # Get all levels for this strategy
    try:
        cur.execute("""
        SELECT strength, name, description 
        FROM strategy 
        WHERE base_strategy = %s 
        ORDER BY strength
        """, (base_strategy,))
        levels = cur.fetchall()
        
        if levels:
            # Level selector
            selected_level = st.selectbox(
                "Select Level to View Details:",
                range(1, 10),
                index=4,  # Default to level 5
                format_func=lambda x: f"Level {x} - {['Weak', 'Very Light', 'Light', 'Moderate-', 'Moderate', 'Moderate+', 'Strong', 'Very Strong', 'Extreme'][x-1]}",
                key=f"level_selector_{base_strategy}"
            )
            
            # Find the selected level data
            selected_level_data = None
            for level in levels:
                if level[0] == selected_level:  # level[0] is strength, not level[1]
                    selected_level_data = level
                    break
            
            if selected_level_data:
                strength, name, description = selected_level_data
                
                st.markdown(f"### {name}")
                st.markdown(f"**Conditions:** {description}")
                
                # Parse and display conditions
                conditions = _parse_level_conditions(base_strategy)
                if conditions:
                    st.markdown("**Cumulative Requirements:**")
                    for i, condition in enumerate(conditions[:selected_level], 1):
                        st.markdown(f"{i}. {condition}")
                
                # Progress indicator
                progress = selected_level / 9
                st.progress(progress)
                st.markdown(f"**Strength Achievement: {selected_level}/9 ({progress*100:.0f}%)**")
                
    except Exception as e:
        st.error(f"Error displaying level breakdown: {e}")

def _parse_level_conditions(base_strategy: str) -> list:
    """Get level conditions for a specific base strategy with detailed technical specifications"""
    # Define detailed conditions for each strategy
    strategy_conditions = {
        'BBRK': [
            "Close crosses above Bollinger Upper (20,2σ) by ≥0.01% with confirmation candle",
            "Volume ≥ 1.0× VolSMA20 (minimum participation threshold)",
            "EMA5 > EMA12 and Close > SMA20 (short-term momentum alignment)",
            "MACD > Signal line (bullish cross or continuation above)",
            "EMA12 > EMA26 (medium-term trend confirmation)",
            "RSI(14) ≥ 55 (momentum strength above neutral)",
            "Close > EMA50 and BBWidth rising ≥3/5 bars (expansion confirmation)",
            "MACD > 0 and Volume ≥ 1.3× VolSMA20 (institutional participation)",
            "Full EMA stack (5>12>26>50>100) + All RSI(7/14/21) ≥60 + Volume ≥1.5×"
        ],
        'BOSR': [
            "Close crosses above BB Lower OR RSI(7) crosses up through 30 (oversold reclaim)",
            "Close ≥ EMA5 (immediate trend alignment)",
            "RSI(14) > 30 and MACD Histogram increasing (momentum building)",
            "MACD ≥ Signal line (bullish momentum confirmation)",
            "Close ≥ SMA20/BB Middle (mean reversion completion)",
            "EMA12 > EMA26 or fresh bullish cross today (trend shift confirmation)",
            "RSI(14) ≥ 50 (neutral momentum recovery)",
            "Volume ≥ 1.2× VolSMA20 and Close ≥ EMA50 (institutional confirmation)",
            "Close ≥ EMA100 and RSI(21) ≥ 55 and Volume ≥1.4× (full recovery)"
        ],
        'BMAC': [
            "EMA12 crosses above EMA26 today with ≥0.02% separation",
            "Close ≥ SMA20 and EMA5 ≥ EMA12 (alignment confirmation)",
            "MACD > Signal line (momentum confirmation)",
            "RSI(14) ≥ 50 (neutral momentum threshold)",
            "Close ≥ EMA50 (longer-term trend participation)",
            "MACD > 0 (positive momentum zone)",
            "Volume ≥ 1.2× VolSMA20 (participation confirmation)",
            "Close ≥ EMA100 and BBWidth rising ≥3/5 bars (expansion phase)",
            "Full EMA stack positive and RSI(21) ≥ 55 and Volume ≥1.5×"
        ],
        'BBOL': [
            "Intraday low touches/breaks BB Lower, close finishes back above Lower",
            "Volume ≥ 1.0× VolSMA20 during the bounce (support confirmation)",
            "EMA5 ≥ Close and RSI(7) oversold recovery (≥25 from <25)",
            "MACD Histogram stops declining or turns positive",
            "Close ≥ BB Middle/SMA20 (mean reversion target)",
            "RSI(14) ≥ 40 and EMA12 ≥ EMA26 (momentum recovery)",
            "Volume ≥ 1.2× VolSMA20 and Close ≥ EMA50",
            "MACD > 0 and BBWidth contracting (volatility normalization)",
            "Close ≥ EMA100 and RSI(21) ≥ 50 and Volume ≥1.4×"
        ],
        'BDIV': [
            "Price makes lower low while RSI(14) or MACD Histogram makes higher low",
            "Divergence spans ≥5 bars with clear momentum shift",
            "Volume confirmation on divergence completion (≥1.1× VolSMA20)",
            "MACD crosses above Signal line (divergence resolution)",
            "Close crosses above previous swing high (breakout confirmation)",
            "RSI(14) ≥ 50 and EMA5 > EMA12 (momentum acceleration)",
            "Volume ≥ 1.3× VolSMA20 and Close > SMA20 (institutional recognition)",
            "EMA12 > EMA26 and MACD > 0 (trend shift confirmation)",
            "Full trend alignment and RSI(21) ≥ 55 and Volume ≥1.5×"
        ],
        'BSUP': [
            "Touch/undercut support level (SMA20/EMA50/EMA100/BB Middle), close back above",
            "Volume ≥ 1.0× VolSMA20 during support test (buying interest)",
            "RSI(7) oversold recovery (from <30 to ≥30) or bounce from support",
            "MACD Histogram improving or MACD > Signal",
            "EMA5 > Close and momentum building (RSI(14) ≥ 45)",
            "Close ≥ resistance level that was previous support",
            "Volume ≥ 1.2× VolSMA20 and RSI(14) ≥ 50",
            "EMA12 > EMA26 and MACD > 0 (trend confirmation)",
            "Close > all major EMAs and RSI(21) ≥ 55 and Volume ≥1.4×"
        ],
        'SBDN': [
            "Close crosses below Bollinger Lower (20,2σ) by ≥0.01% with confirmation",
            "Volume ≥ 1.0× VolSMA20 (breakdown participation)",
            "EMA5 < EMA12 and Close < SMA20 (short-term momentum shift)",
            "MACD < Signal line (bearish cross or continuation below)",
            "EMA12 < EMA26 (medium-term trend shift)",
            "RSI(14) ≤ 45 (momentum weakness below neutral)",
            "Close < EMA50 and BBWidth rising ≥3/5 bars (expansion confirmation)",
            "MACD < 0 and Volume ≥ 1.3× VolSMA20 (institutional distribution)",
            "Full EMA stack negative (5<12<26<50<100) + All RSI ≤40 + Volume ≥1.5×"
        ],
        'SOBR': [
            "Close rejects BB Upper OR RSI(7) crosses down through 70 (overbought failure)",
            "Close ≤ EMA5 (immediate trend break)",
            "RSI(14) < 70 and MACD Histogram declining (momentum weakening)",
            "MACD ≤ Signal line (bearish momentum confirmation)",
            "Close ≤ SMA20/BB Middle (mean reversion initiation)",
            "EMA12 < EMA26 or fresh bearish cross today (trend shift)",
            "RSI(14) ≤ 50 (neutral momentum failure)",
            "Volume ≥ 1.2× VolSMA20 and Close ≤ EMA50 (institutional distribution)",
            "Close ≤ EMA100 and RSI(21) ≤ 45 and Volume ≥1.4× (full rejection)"
        ],
        'SMAC': [
            "EMA12 crosses below EMA26 today with ≥0.02% separation",
            "Close ≤ SMA20 and EMA5 ≤ EMA12 (alignment confirmation)",
            "MACD < Signal line (momentum confirmation)",
            "RSI(14) ≤ 50 (neutral momentum failure)",
            "Close ≤ EMA50 (longer-term trend participation)",
            "MACD < 0 (negative momentum zone)",
            "Volume ≥ 1.2× VolSMA20 (distribution confirmation)",
            "Close ≤ EMA100 and BBWidth rising ≥3/5 bars (expansion phase)",
            "Full EMA stack negative and RSI(21) ≤ 45 and Volume ≥1.5×"
        ],
        'SDIV': [
            "Price makes higher high while RSI(14) or MACD Histogram makes lower high",
            "Divergence spans ≥5 bars with clear momentum deterioration",
            "Volume confirmation on divergence completion (≥1.1× VolSMA20)",
            "MACD crosses below Signal line (divergence resolution)",
            "Close crosses below previous swing low (breakdown confirmation)",
            "RSI(14) ≤ 50 and EMA5 < EMA12 (momentum deceleration)",
            "Volume ≥ 1.3× VolSMA20 and Close < SMA20 (institutional distribution)",
            "EMA12 < EMA26 and MACD < 0 (trend shift confirmation)",
            "Full trend breakdown and RSI(21) ≤ 45 and Volume ≥1.5×"
        ],
        'SRES': [
            "Touch/overrun resistance (BB Upper/SMA20/EMA50/EMA100), close back below",
            "Volume ≥ 1.0× VolSMA20 during resistance test (selling interest)",
            "RSI(7) overbought failure (from >70 to ≤70) or rejection at resistance",
            "MACD Histogram deteriorating or MACD < Signal",
            "EMA5 < Close and momentum failing (RSI(14) ≤ 55)",
            "Close ≤ support level that was previous resistance",
            "Volume ≥ 1.2× VolSMA20 and RSI(14) ≤ 50",
            "EMA12 < EMA26 and MACD < 0 (trend confirmation)",
            "Close < all major EMAs and RSI(21) ≤ 45 and Volume ≥1.4×"
        ]
    }
    # Return conditions for the specified strategy
    if base_strategy in strategy_conditions:
        return strategy_conditions[base_strategy]
    
    # Fallback for unrecognized strategies
    return [f"Level {i} technical condition (unknown strategy: {base_strategy})" for i in range(1, 10)]

def _display_technical_requirements(base_strategy: str):
    """Display technical indicator requirements"""
    st.markdown("### 📊 Required Technical Indicators")
    
    # Common indicators for all strategies
    required_indicators = [
        "EMA5, EMA12, EMA26, EMA50, EMA100 (Moving Averages)",
        "RSI(7), RSI(14), RSI(21) (Multi-period RSI)",
        "MACD, MACD Signal, MACD Histogram",
        "Bollinger Bands (20,2σ) with Width Analysis",
        "Volume SMA(20) for Volume Ratios",
        "SMA(20) for trend confirmation"
    ]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Core Indicators:**")
        for indicator in required_indicators[:3]:
            st.markdown(f"• {indicator}")
    
    with col2:
        st.markdown("**Additional Analysis:**")
        for indicator in required_indicators[3:]:
            st.markdown(f"• {indicator}")
    
    # Volume thresholds
    st.markdown("### 📈 Volume Ratio Thresholds")
    volume_thresholds = [
        "1.0× VolSMA20 - Minimum volume confirmation",
        "1.1× VolSMA20 - Light volume increase", 
        "1.2× VolSMA20 - Moderate volume confirmation",
        "1.3× VolSMA20 - Strong volume confirmation",
        "1.5× VolSMA20 - Institutional-grade volume"
    ]
    
    for threshold in volume_thresholds:
        st.markdown(f"• {threshold}")

def _display_strategy_examples(base_strategy: str):
    """Display strategy examples and scenarios"""
    st.markdown("### 💼 Real-World Examples")
    
    # Example scenarios
    st.markdown("#### 📊 Level Comparison Examples")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🟡 Level 5 Scenario (Moderate):**")
        st.markdown(f"• {base_strategy} base trigger activated")
        st.markdown("• Volume confirmation present")
        st.markdown("• Basic momentum alignment")
        st.markdown("• MACD bullish cross")
        st.markdown("• EMA trend confirmation")
        st.info("**Typical Use:** Standard signal generation")
    
    with col2:
        st.markdown("**🟢 Level 9 Scenario (Extreme):**")
        st.markdown(f"• {base_strategy} base trigger activated")
        st.markdown("• Strong volume surge (≥1.5×)")
        st.markdown("• Full EMA stack alignment")
        st.markdown("• Multiple RSI confirmations")
        st.markdown("• All conditions maximized")
        st.success("**Typical Use:** High-confidence institutional signals")

def _get_strategy_characteristics(base_strategy: str) -> list:
    """Get strategy characteristics"""
    characteristics = {
        'BBRK': ['High volatility environment', 'Strong volume required', 'Trend continuation focus'],
        'BOSR': ['Mean reversion opportunity', 'Oversold bounce potential', 'Risk management critical'],
        'BMAC': ['Trend shift identification', 'Momentum confirmation', 'Classic technical approach'],
        'BBOL': ['Bollinger band mean reversion', 'Normal volatility environment', 'Support level bounce'],
        'BDIV': ['Advanced pattern recognition', 'Divergence analysis', 'Counter-trend opportunity'],
        'BSUP': ['Support level testing', 'Key level bounce', 'Technical level confirmation'],
        'SBDN': ['Bearish breakout', 'Downward momentum', 'Volume confirmation required'],
        'SOBR': ['Overbought rejection', 'Mean reversion short', 'Resistance level failure'],
        'SMAC': ['Bearish trend shift', 'Moving average cross', 'Momentum confirmation'],
        'SDIV': ['Bearish divergence', 'Momentum weakness', 'Advanced pattern'],
        'SRES': ['Resistance rejection', 'Level-based shorting', 'Technical bounce failure']
    }
    return characteristics.get(base_strategy, ['Professional trading strategy', 'Technical analysis based', 'Risk management required'])

# =============================================================================
# MAIN DASHBOARD
# =============================================================================

def main():
    """Main dashboard application"""
    
    # Page Header
    st.title("⚙️ Strategy Base Catalog")
    st.markdown("*Comprehensive documentation of all trading strategy bases and their confidence level determination*")
    st.markdown("---")
    
    # Initialize database connection
    try:
        db_manager = DatabaseManager()
        conn = db_manager.get_connection()
        st.success("✅ Database connection established")
    except Exception as e:
        st.error(f"❌ Database connection failed: {str(e)}")
        st.error("**Please ensure:**")
        st.error("• PostgreSQL is running")
        st.error("• Database credentials are correct")
        st.error("• Strategy table exists")
        st.stop()
    
    try:
        cur = conn.cursor()
        
        # Get strategy base statistics from our updated strategy table
        cur.execute("""
        SELECT 
            COUNT(DISTINCT base_strategy) as total_base_strategies,
            COUNT(DISTINCT category) as categories,
            COUNT(DISTINCT CASE WHEN side = 'B' THEN base_strategy END) as buy_strategies,
            COUNT(DISTINCT CASE WHEN side = 'S' THEN base_strategy END) as sell_strategies
        FROM strategy
        """)
        stats = cur.fetchone()
        
        if stats:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Base Strategies", stats[0] or 0)
            with col2:
                st.metric("Categories", stats[1] or 0)
            with col3:
                st.metric("Buy Strategies", stats[2] or 0)
            with col4:
                st.metric("Sell Strategies", stats[3] or 0)
        
        # Strategy Base Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            category_filter = st.selectbox(
                "Category Filter:",
                ["All", "breakout", "mean-reversion", "trend", "divergence", "level"]
            )
        with col2:
            side_filter = st.selectbox("Signal Side Filter:", ["All", "B", "S"])
        with col3:
            st.markdown("**Complexity:** All strategies shown")
        
        # Build query with filters - get base strategy info
        query = """
        SELECT DISTINCT base_strategy, 
               base_strategy as strategy_name,
               side, category,
               'Level-based strategy with 9 strength variants' as description,
               COUNT(*) as level_count
        FROM strategy
        WHERE base_strategy IS NOT NULL
        """
        params = []
        
        if category_filter != "All":
            query += " AND category = %s"
            params.append(category_filter)
        if side_filter != "All":
            query += " AND side = %s"
            params.append(side_filter)
        
        query += " GROUP BY base_strategy, side, category"
        query += " ORDER BY category, base_strategy"
        
        cur.execute(query, params)
        base_strategies = cur.fetchall()
        
        # Display strategy bases with comprehensive level information
        st.markdown("### 📋 Available Strategy Bases")
        st.markdown("*Each strategy has 9 strength levels with cumulative conditions*")
        
        if base_strategies:
            for strategy in base_strategies:
                base, name, side, category, description, level_count = strategy
                
                # Create TXYZN example with different magnitudes
                side_name = {"B": "Buy", "S": "Sell"}[side]
                side_color = {"B": "🟢", "S": "🔴"}[side]
                
                category_icon = {
                    "breakout": "🚀",
                    "mean-reversion": "↩️", 
                    "trend": "📈",
                    "divergence": "🔄",
                    "level": "🎯"
                }.get(category, "📊")
                
                with st.expander(f"{side_color} **{base}** - {category_icon} {_get_strategy_intent(base)} ({side_name})"):
                    # Get detailed level information for this strategy
                    _display_strategy_details(cur, base, side, category)
        else:
            st.info("No strategy bases found matching the selected filters.")
    
    except Exception as e:
        st.error(f"Error loading strategy bases: {str(e)}")
    
    finally:
        # Close database connection
        try:
            conn.close()
        except:
            pass

# =============================================================================
# RUN APPLICATION
# =============================================================================

if __name__ == "__main__":
    main()