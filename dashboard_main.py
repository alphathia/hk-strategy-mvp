#!/usr/bin/env python3
"""
Main Dashboard Router - Modular Architecture
Clean main entry point that routes to individual page modules
"""

import streamlit as st
import sys
import os
from datetime import datetime

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

# Add paths for imports
sys.path.append('src')
sys.path.append('pages')

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="HK Strategy MVP - Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

if 'current_page' not in st.session_state:
    st.session_state.current_page = 'overview'

if 'navigation' not in st.session_state:
    st.session_state.navigation = {
        'section': 'portfolios',
        'page': 'overview'
    }

# =============================================================================
# SIDEBAR NAVIGATION
# =============================================================================

st.sidebar.markdown("# 📊 HK Strategy MVP")
st.sidebar.markdown("*Professional Trading Dashboard*")
st.sidebar.markdown("---")

# Main navigation sections
st.sidebar.markdown("### 🎯 Navigation")

# Portfolio Section
if st.sidebar.button("📈 **Portfolio Overview**", use_container_width=True):
    st.session_state.current_page = 'overview'
    st.session_state.navigation = {'section': 'portfolios', 'page': 'overview'}
    st.rerun()

# Analysis Section  
st.sidebar.markdown("**📊 Analysis**")
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("PV Analysis", use_container_width=True):
        st.session_state.current_page = 'pv_analysis'
        st.session_state.navigation = {'section': 'analysis', 'page': 'pv_analysis'}
        st.rerun()
with col2:
    if st.button("Equity Analysis", use_container_width=True):
        st.session_state.current_page = 'equity_analysis'
        st.session_state.navigation = {'section': 'analysis', 'page': 'equity_analysis'}
        st.rerun()

# Strategy Section
st.sidebar.markdown("**⚙️ Strategy**")
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("Strategy Editor", use_container_width=True):
        st.session_state.current_page = 'strategy_editor'
        st.session_state.navigation = {'section': 'strategy', 'page': 'strategy_editor'}
        st.rerun()
with col2:
    if st.button("Strategy Catalog", use_container_width=True):
        st.session_state.current_page = 'strategy_catalog'
        st.session_state.navigation = {'section': 'strategy', 'page': 'strategy_catalog'}
        st.rerun()

if st.sidebar.button("📊 **Strategy Comparison**", use_container_width=True):
    st.session_state.current_page = 'strategy_comparison'
    st.session_state.navigation = {'section': 'strategy', 'page': 'strategy_comparison'}
    st.rerun()

# System info
st.sidebar.markdown("---")
st.sidebar.markdown("**📍 Current Page**")
st.sidebar.info(f"**{st.session_state.current_page.replace('_', ' ').title()}**")

st.sidebar.markdown("---")
st.sidebar.markdown(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
st.sidebar.markdown("🚀 *Generated with Claude Code*")

# =============================================================================
# PAGE ROUTING
# =============================================================================

def load_page_safely(page_name: str, render_function):
    """Safely load a page with error handling"""
    try:
        render_function()
    except Exception as e:
        st.error(f"❌ Error loading {page_name}: {str(e)}")
        st.markdown("### 🔧 Troubleshooting")
        st.markdown("- Check database connection")
        st.markdown("- Verify all required modules are installed")
        st.markdown("- Ensure proper environment configuration")
        
        if st.button("🔄 Reload Page"):
            st.rerun()

# Route to appropriate page
if st.session_state.current_page == 'overview':
    try:
        from pages.overview import render_overview_page
        load_page_safely("Portfolio Overview", render_overview_page)
    except ImportError as e:
        st.error(f"❌ Could not load Overview page: {e}")
    
elif st.session_state.current_page == 'pv_analysis':
    try:
        from pages.pv_analysis import render_pv_analysis_page
        load_page_safely("PV Analysis", render_pv_analysis_page)
    except ImportError as e:
        st.error(f"❌ Could not load PV Analysis page: {e}")

elif st.session_state.current_page == 'equity_analysis':
    try:
        from pages.equity_analysis import render_equity_analysis_page
        load_page_safely("Equity Analysis", render_equity_analysis_page)
    except ImportError as e:
        st.error(f"❌ Could not load Equity Analysis page: {e}")

elif st.session_state.current_page == 'strategy_editor':
    try:
        from pages.strategy_editor import render_strategy_editor_page
        load_page_safely("Strategy Editor", render_strategy_editor_page)
    except ImportError as e:
        st.error(f"❌ Could not load Strategy Editor page: {e}")

elif st.session_state.current_page == 'strategy_catalog':
    try:
        from pages.strategy_catalog import render_strategy_catalog_page
        load_page_safely("Strategy Catalog", render_strategy_catalog_page)
    except ImportError as e:
        st.error(f"❌ Could not load Strategy Catalog page: {e}")
        st.info("💡 **Fallback:** You can use `streamlit run minimal_dashboard.py` for Strategy Catalog functionality.")

elif st.session_state.current_page == 'strategy_comparison':
    try:
        from pages.strategy_comparison import render_strategy_comparison_page
        load_page_safely("Strategy Comparison", render_strategy_comparison_page)
    except ImportError as e:
        st.error(f"❌ Could not load Strategy Comparison page: {e}")

else:
    st.title("🏠 Welcome to HK Strategy MVP")
    st.markdown("### 📊 Professional Trading Dashboard")
    st.markdown("Use the sidebar navigation to explore different sections:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 📈 Portfolio")
        st.markdown("- Portfolio Overview")
        st.markdown("- Performance Tracking")
        st.markdown("- Risk Management")
    
    with col2:
        st.markdown("#### 📊 Analysis")
        st.markdown("- PV Analysis")
        st.markdown("- Equity Analysis") 
        st.markdown("- Technical Indicators")
    
    with col3:
        st.markdown("#### ⚙️ Strategy")
        st.markdown("- Strategy Editor")
        st.markdown("- **Strategy Catalog** ✅")
        st.markdown("- Strategy Comparison")

# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown(
        "<div style='text-align: center'>"
        "🚀 <strong>Modular Dashboard Architecture</strong><br>"
        "<small>Generated with Claude Code - Professional Trading Platform</small>"
        "</div>", 
        unsafe_allow_html=True
    )