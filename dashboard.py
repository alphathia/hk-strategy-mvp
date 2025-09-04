import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import time
import copy
import psycopg2
import redis
import sys
import os
import platform
import numpy as np
import logging

# Load environment variables first (critical for database connection)
from dotenv import load_dotenv
load_dotenv()

from src.config_manager import get_config, ConfigurationError
from portfolio_manager import get_portfolio_manager

# Import PV Analysis modules
sys.path.append('src')
try:
    from src.database import DatabaseManager
    from src.analysis_manager import AnalysisManager
    from src.hkex_calendar import validate_hkex_analysis_period, hkex_calendar
except ImportError:
    from database import DatabaseManager
    from analysis_manager import AnalysisManager
    from hkex_calendar import validate_hkex_analysis_period, hkex_calendar

@st.dialog("Select Technical Indicators")
def select_indicators_dialog():
    """Modal dialog for selecting technical indicators"""
    st.markdown("**Select up to 3 technical indicators to overlay on the price chart:**")
    st.markdown("---")
    
    # Available technical indicators
    available_indicators = [
        ("RSI (7)", "rsi_7"),
        ("RSI (14)", "rsi_14"), 
        ("RSI (21)", "rsi_21"),
        ("MACD", "macd"),
        ("MACD Signal", "macd_signal"),
        ("SMA (20)", "sma_20"),
        ("EMA (12)", "ema_12"),
        ("EMA (26)", "ema_26"),
        ("EMA (50)", "ema_50"),
        ("EMA (100)", "ema_100"),
        ("Bollinger Upper", "bollinger_upper"),
        ("Bollinger Middle", "bollinger_middle"),
        ("Bollinger Lower", "bollinger_lower"),
        ("Volume SMA (20)", "volume_sma_20")
    ]
    
    # Initialize selection state if not exists
    if 'selected_indicators_modal' not in st.session_state:
        st.session_state.selected_indicators_modal = []
    
    # Create checkboxes in a grid layout
    cols = st.columns(3)
    selected_count = 0
    
    for i, (name, code) in enumerate(available_indicators):
        col_idx = i % 3
        with cols[col_idx]:
            # Check if this indicator is currently selected
            is_selected = code in st.session_state.selected_indicators_modal
            
            # Disable checkbox if 3 are already selected and this one isn't selected
            max_reached = len(st.session_state.selected_indicators_modal) >= 3 and not is_selected
            
            checkbox_result = st.checkbox(
                name, 
                value=is_selected, 
                disabled=max_reached,
                key=f"modal_indicator_{code}"
            )
            
            # Update selection state
            if checkbox_result and code not in st.session_state.selected_indicators_modal:
                if len(st.session_state.selected_indicators_modal) < 3:
                    st.session_state.selected_indicators_modal.append(code)
            elif not checkbox_result and code in st.session_state.selected_indicators_modal:
                st.session_state.selected_indicators_modal.remove(code)
    
    selected_count = len(st.session_state.selected_indicators_modal)
    
    # Show selection status
    st.markdown("---")
    if selected_count == 0:
        st.info("📊 Select 1-3 indicators to display")
    elif selected_count >= 3:
        st.success(f"✅ Maximum selected: {selected_count}/3")
    else:
        st.info(f"📊 Selected: {selected_count}/3")
    
    # Action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Show Indicators", disabled=selected_count == 0, type="primary", use_container_width=True):
            # Store final selection and close modal
            st.session_state.confirmed_indicators = st.session_state.selected_indicators_modal.copy()
            st.session_state.show_indicators_clicked = True
            st.rerun()
    
    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            # Reset modal selection and close
            st.session_state.selected_indicators_modal = []
            st.rerun()

@st.dialog("Copy Portfolio")
def copy_portfolio_dialog(portfolio_id: str):
    """Modal dialog for copying a portfolio with proper UI"""
    # Check if portfolio exists
    if portfolio_id not in st.session_state.portfolios:
        st.error(f"❌ Portfolio '{portfolio_id}' not found in current session")
        st.warning("💡 Try refreshing the page or check if the portfolio was recently deleted.")
        if st.button("🔄 Refresh Portfolios", use_container_width=True):
            st.session_state.portfolios = st.session_state.portfolio_manager.get_all_portfolios()
            st.rerun()
        return
    
    original_portfolio = st.session_state.portfolios[portfolio_id]
    
    st.markdown(f"**Create a copy of: {original_portfolio['name']}**")
    st.markdown("---")
    
    # Generate default new ID
    default_new_id = f"{portfolio_id}_Copy"
    counter = 1
    while default_new_id in st.session_state.portfolios:
        default_new_id = f"{portfolio_id}_Copy{counter}"
        counter += 1
    
    # Form inputs with better spacing
    col1, col2 = st.columns(2)
    with col1:
        new_portfolio_id = st.text_input(
            "Portfolio ID:", 
            value=default_new_id,
            help="Unique identifier for the new portfolio"
        )
    with col2:
        new_portfolio_name = st.text_input(
            "Portfolio Name:",
            value=f"Copy of {original_portfolio['name']}",
            help="Display name for the new portfolio"
        )
    
    new_portfolio_desc = st.text_area(
        "Description (Optional):",
        value=f"Copy of {original_portfolio['description']}",
        height=100,
        help="Optional description for the new portfolio"
    )
    
    # Validation
    error_msg = ""
    if not new_portfolio_id.strip():
        error_msg = "Portfolio ID is required"
    elif new_portfolio_id.strip() in st.session_state.portfolios:
        error_msg = f"Portfolio ID '{new_portfolio_id.strip()}' already exists"
    elif not new_portfolio_name.strip():
        error_msg = "Portfolio Name is required"
    
    if error_msg:
        st.error(f"❌ {error_msg}")
    
    st.markdown("---")
    
    # Action buttons with better spacing
    col_btn1, col_btn2, col_spacer = st.columns([1, 1, 2])
    
    with col_btn1:
        if st.button("📋 Create Copy", disabled=bool(error_msg), use_container_width=True, type="primary"):
            # Use the proper copy_portfolio method
            success = st.session_state.portfolio_manager.copy_portfolio(
                portfolio_id,
                new_portfolio_id.strip(),
                new_portfolio_name.strip(),
                new_portfolio_desc.strip()
            )
            
            if success:
                # Refresh portfolios and enter edit mode for the new copy
                st.session_state.portfolios = st.session_state.portfolio_manager.get_all_portfolios()
                st.session_state.current_page = 'portfolio'
                # Use portfolio_switch_request to properly select the new portfolio
                st.session_state.portfolio_switch_request = new_portfolio_id.strip()
                st.session_state.edit_mode[new_portfolio_id.strip()] = True
                st.session_state.portfolio_backup[new_portfolio_id.strip()] = copy.deepcopy(st.session_state.portfolios[new_portfolio_id.strip()])
                # Update navigation state for unified navigation system
                st.session_state.navigation['section'] = 'portfolios'
                st.session_state.navigation['page'] = 'portfolio'
                st.success(f"📋 Successfully created copy: {new_portfolio_id.strip()}")
                st.rerun()
            else:
                st.error(f"❌ Failed to create copy of '{portfolio_id}'")
                st.warning("💡 **Possible reasons:**")
                st.markdown("- Source portfolio may not exist in database")
                st.markdown("- Target portfolio ID already exists")
                st.markdown("- Database connection issue")
                st.info("💡 **Try:** Refresh portfolios or check application logs for details")
    
    with col_btn2:
        if st.button("❌ Cancel", use_container_width=True):
            st.rerun()

@st.dialog("Add New Symbol")
def add_symbol_dialog(portfolio_id: str):
    """Modal dialog for adding a new symbol to the portfolio"""
    st.markdown("**Add a new stock position to your portfolio**")
    st.markdown("---")
    
    # Symbol input with validation
    col1, col2 = st.columns([2, 1])
    with col1:
        # Use validated symbol as value if available, otherwise empty
        current_symbol = st.session_state.get('validated_symbol', '')
        symbol_input = st.text_input(
            "Stock Symbol:", 
            value=current_symbol,
            placeholder="e.g., 0001.HK, 0700.HK",
            help="Enter Hong Kong stock symbol"
        )
    with col2:
        if st.button("🔍 Check Symbol", use_container_width=True):
            if symbol_input.strip():
                trimmed_symbol = symbol_input.strip().upper()
                
                # Clear previous validation state
                st.session_state['validation_success'] = False
                
                # Show loading message
                with st.spinner(f"Looking up {trimmed_symbol} on Yahoo Finance..."):
                    try:
                        # Create ticker and fetch info
                        stock = yf.Ticker(trimmed_symbol)
                        info = stock.info
                        
                        # Enhanced validation and name retrieval
                        if info and len(info) > 1:
                            # Try multiple name fields for better reliability
                            long_name = info.get('longName', '').strip()
                            short_name = info.get('shortName', '').strip()
                            display_name = info.get('displayName', '').strip()
                            
                            # Choose best available name
                            if long_name and long_name != '':
                                company_name = long_name
                            elif short_name and short_name != '':
                                company_name = short_name
                            elif display_name and display_name != '':
                                company_name = display_name
                            else:
                                # Fallback: use symbol-based name
                                if trimmed_symbol.endswith('.HK'):
                                    code = trimmed_symbol.replace('.HK', '')
                                    company_name = f"HK Stock {code}"
                                else:
                                    company_name = 'Unknown Company'
                            
                            # Determine sector with expanded mapping
                            raw_sector = info.get('sector', 'Other')
                            if raw_sector in ["Technology", "Information Technology", "Communication Services"]:
                                sector = "Tech"
                            elif raw_sector in ["Financials", "Financial Services"]:
                                sector = "Financials"
                            elif raw_sector in ["Real Estate"]:
                                sector = "REIT"
                            elif raw_sector in ["Energy"]:
                                sector = "Energy"
                            elif raw_sector in ["Consumer Discretionary", "Consumer Staples"]:
                                sector = "Consumer"
                            elif raw_sector in ["Healthcare"]:
                                sector = "Healthcare"
                            else:
                                sector = "Other"
                            
                            # Validate that we have meaningful data
                            quote_type = info.get('quoteType', '')
                            if quote_type == 'EQUITY' or info.get('symbol') == trimmed_symbol:
                                # Store in session state for display
                                st.session_state['validated_symbol'] = trimmed_symbol
                                st.session_state['validated_company'] = company_name
                                st.session_state['validated_sector'] = sector
                                st.session_state['validation_success'] = True
                                st.success(f"✅ Found: {company_name}")
                                
                                # Show additional info for debugging
                                if quote_type:
                                    st.info(f"Type: {quote_type} | Sector: {raw_sector}")
                            else:
                                st.session_state['validation_success'] = False
                                st.error("❌ Symbol exists but may not be a valid equity")
                                st.info(f"Quote type: {quote_type}, Raw data keys: {len(info)}")
                        else:
                            st.session_state['validation_success'] = False
                            st.error("❌ Symbol not found on Yahoo Finance")
                            st.info(f"Received data keys: {len(info) if info else 0}")
                            
                    except Exception as e:
                        st.session_state['validation_success'] = False
                        st.error(f"❌ Error validating symbol: {str(e)}")
                        
                        # Provide helpful troubleshooting info
                        if "404" in str(e):
                            st.info("💡 Make sure to use the correct format (e.g., 0700.HK)")
                        elif "timeout" in str(e).lower():
                            st.info("💡 Network timeout - please try again")
                        else:
                            st.info("💡 Check internet connection and try again")
            else:
                st.error("Please enter a symbol")
    
    # Display validated information
    validated_symbol = st.session_state.get('validated_symbol', '')
    validated_company = st.session_state.get('validated_company', '')
    validated_sector = st.session_state.get('validated_sector', 'Other')
    
    # Show validated info if available
    if validated_symbol:
        st.success(f"**Validated Symbol**: {validated_symbol}")
        st.info(f"**Company**: {validated_company}")
        st.info(f"**Sector**: {validated_sector}")
    
    st.markdown("---")
    
    # Quantity and Cost inputs
    col_qty, col_cost = st.columns(2)
    with col_qty:
        quantity = st.number_input(
            "Quantity:",
            min_value=0,
            value=100,
            step=1,
            format="%d",
            help="Number of shares (0 allowed for watchlist tracking)"
        )
    with col_cost:
        avg_cost = st.number_input(
            "Average Cost (HK$):",
            min_value=0.0,
            value=50.0,
            step=0.01,
            format="%.2f",
            help="Average cost per share in HK$ (0 allowed for free shares)"
        )
    
    # Validation
    error_msg = ""
    if not validated_symbol:
        error_msg = "Please check the symbol first"
    elif not isinstance(quantity, int) or quantity < 0:
        error_msg = "Quantity must be a non-negative integer"
    elif not isinstance(avg_cost, (int, float)) or avg_cost < 0:
        error_msg = "Average cost must be a non-negative number"
    else:
        # Check for duplicate symbol in current portfolio
        existing_symbols = [pos['symbol'] for pos in st.session_state.portfolios[portfolio_id]['positions']]
        if validated_symbol in existing_symbols:
            error_msg = f"Symbol {validated_symbol} already exists in this portfolio. You cannot add the same symbol twice."
    
    if error_msg:
        st.error(f"❌ {error_msg}")
        # Add helpful hint for duplicate symbol error
        if "already exists in this portfolio" in error_msg:
            st.info("💡 To modify an existing position, use the **Edit** button in the position table below.")
    
    st.markdown("---")
    
    # Action buttons
    col_add, col_cancel, col_spacer = st.columns([1, 1, 2])
    
    with col_add:
        if st.button("➕ Add Position", disabled=bool(error_msg), use_container_width=True, type="primary"):
            # Add to session state pending changes
            modified_key = f'modified_positions_{portfolio_id}'
            if modified_key not in st.session_state:
                st.session_state[modified_key] = {}
            
            # Add new position to modified positions
            st.session_state[modified_key][validated_symbol] = {
                'symbol': validated_symbol,
                'company_name': validated_company,
                'quantity': quantity,
                'avg_cost': avg_cost,
                'sector': validated_sector
            }
            
            # Add to current portfolio for immediate display
            # Note: Duplicate validation above ensures this symbol doesn't already exist
            st.session_state.portfolios[portfolio_id]['positions'].append({
                'symbol': validated_symbol,
                'company_name': validated_company,
                'quantity': quantity,
                'avg_cost': avg_cost,
                'sector': validated_sector
            })
            
            # Clear validation session state
            for key in ['validated_symbol', 'validated_company', 'validated_sector', 'validation_success']:
                if key in st.session_state:
                    del st.session_state[key]
                    
            st.success(f"✅ {validated_symbol} added to portfolio!")
            st.rerun()
    
    with col_cancel:
        if st.button("❌ Cancel", use_container_width=True):
            # Clear validation session state
            for key in ['validated_symbol', 'validated_company', 'validated_sector', 'validation_success']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

@st.dialog("Update Position")
def update_position_dialog(portfolio_id: str, position: dict):
    """Modal dialog for updating an existing position"""
    st.markdown(f"**Update Position: {position['symbol']}**")
    st.markdown("---")
    
    # Display read-only position info
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        st.text_input("Symbol:", value=position['symbol'], disabled=True)
        st.text_input("Company:", value=position['company_name'], disabled=True)
    with col_info2:
        st.text_input("Sector:", value=position.get('sector', 'Other'), disabled=True)
    
    st.markdown("---")
    st.markdown("**Update the following information:**")
    
    # Editable fields
    col_qty, col_cost = st.columns(2)
    with col_qty:
        new_quantity = st.number_input(
            "Quantity:",
            min_value=0,
            value=position['quantity'],
            step=1,
            format="%d",
            help="Number of shares (0 to remove position)"
        )
    with col_cost:
        new_avg_cost = st.number_input(
            "Average Cost (HK$):",
            min_value=0.0,
            value=position['avg_cost'],
            step=0.01,
            format="%.2f",
            help="Average cost per share in HK$ (0 allowed for free shares)"
        )
    
    # Validation
    error_msg = ""
    if not isinstance(new_quantity, int) or new_quantity < 0:
        error_msg = "Quantity must be a non-negative integer"
    elif not isinstance(new_avg_cost, (int, float)) or new_avg_cost < 0:
        error_msg = "Average cost must be a non-negative number"
    
    if error_msg:
        st.error(f"❌ {error_msg}")
    
    st.markdown("---")
    
    # Action buttons
    col_update, col_cancel, col_spacer = st.columns([1, 1, 2])
    
    with col_update:
        if st.button("💾 Update", disabled=bool(error_msg), use_container_width=True, type="primary"):
            # Update in session state
            modified_key = f'modified_positions_{portfolio_id}'
            deleted_key = f'deleted_positions_{portfolio_id}'
            
            if modified_key not in st.session_state:
                st.session_state[modified_key] = {}
            if deleted_key not in st.session_state:
                st.session_state[deleted_key] = set()
            
            if new_quantity == 0:
                # Mark for deletion
                st.session_state[deleted_key].add(position['symbol'])
                # Remove from modified if it was there
                if position['symbol'] in st.session_state[modified_key]:
                    del st.session_state[modified_key][position['symbol']]
            else:
                # Update position
                st.session_state[modified_key][position['symbol']] = {
                    'symbol': position['symbol'],
                    'company_name': position['company_name'],
                    'quantity': new_quantity,
                    'avg_cost': new_avg_cost,
                    'sector': position.get('sector', 'Other')
                }
                # Remove from deleted if it was there
                if position['symbol'] in st.session_state[deleted_key]:
                    st.session_state[deleted_key].remove(position['symbol'])
            
            # Update display data immediately
            for i, pos in enumerate(st.session_state.portfolios[portfolio_id]['positions']):
                if pos['symbol'] == position['symbol']:
                    if new_quantity == 0:
                        # Don't remove from display, just mark as deleted for visual indication
                        pass
                    else:
                        st.session_state.portfolios[portfolio_id]['positions'][i] = {
                            'symbol': position['symbol'],
                            'company_name': position['company_name'],
                            'quantity': new_quantity,
                            'avg_cost': new_avg_cost,
                            'sector': position.get('sector', 'Other')
                        }
                    break
            
            action = "marked for deletion" if new_quantity == 0 else "updated"
            st.success(f"✅ {position['symbol']} {action}!")
            st.rerun()
    
    with col_cancel:
        if st.button("❌ Cancel", use_container_width=True):
            st.rerun()

st.set_page_config(
    page_title="HK Strategy Multi-Portfolio Dashboard",
    page_icon="📈",
    layout="wide"
)

@st.dialog("Create New Portfolio")
def create_portfolio_dialog():
    """Modal dialog for creating a new portfolio"""
    st.markdown("**Create a new portfolio to track your investments**")
    st.markdown("---")
    
    # Form fields
    new_portfolio_id = st.text_input(
        "Portfolio ID:",
        placeholder="e.g., TECH_GROWTH",
        key="new_portfolio_id_modal",
        help="Unique identifier for the portfolio (no spaces, use underscores)"
    )
    new_portfolio_name = st.text_input(
        "Portfolio Name:",
        placeholder="e.g., Technology Growth Stocks",
        key="new_portfolio_name_modal",
        help="Display name for the portfolio"
    )
    new_portfolio_desc = st.text_area(
        "Description:",
        placeholder="Brief description of the portfolio strategy...",
        key="new_portfolio_desc_modal",
        help="Optional description of the portfolio"
    )
    
    st.markdown("---")
    
    # Validation
    error_msg = ""
    if new_portfolio_id:
        portfolio_id = new_portfolio_id.strip().upper().replace(' ', '_')
        if portfolio_id in st.session_state.portfolios:
            error_msg = f"Portfolio '{portfolio_id}' already exists!"
        elif not new_portfolio_name.strip():
            error_msg = "Portfolio Name is required"
    elif new_portfolio_name:
        error_msg = "Portfolio ID is required"
    
    if error_msg:
        st.error(f"❌ {error_msg}")
    
    # Buttons
    col_create, col_cancel = st.columns(2)
    with col_create:
        disabled = bool(error_msg) or not new_portfolio_id or not new_portfolio_name
        if st.button("✅ Create Portfolio", use_container_width=True, disabled=disabled):
            portfolio_id = new_portfolio_id.strip().upper().replace(' ', '_')
            
            # Create new portfolio in database using portfolio manager
            success = st.session_state.portfolio_manager.create_portfolio(
                portfolio_id,
                new_portfolio_name.strip(),
                new_portfolio_desc.strip()
            )
            
            if success:
                # Refresh portfolios from database to ensure consistency
                st.session_state.portfolios = st.session_state.portfolio_manager.get_all_portfolios()
                st.success(f"✅ Portfolio '{new_portfolio_name}' created successfully and saved to database!")
                
                # Clear form fields
                for key in ['new_portfolio_id_modal', 'new_portfolio_name_modal', 'new_portfolio_desc_modal']:
                    if key in st.session_state:
                        del st.session_state[key]
                
                # Brief delay to show success message
                import time
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"❌ Failed to create portfolio '{new_portfolio_name}' in database!")
                st.warning("💡 **Possible reasons:**")
                st.markdown("- Portfolio ID already exists in database")
                st.markdown("- Database connection issue")
                st.info("💡 **Try:** Use a different Portfolio ID or check database connection")
    
    with col_cancel:
        if st.button("❌ Cancel", use_container_width=True):
            # Clear form fields on cancel
            for key in ['new_portfolio_id_modal', 'new_portfolio_name_modal', 'new_portfolio_desc_modal']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

@st.dialog("Total Positions Details")
def show_total_positions_dialog(symbol_details):
    """Modal dialog showing all unique symbols across portfolios"""
    st.markdown("**All unique symbols across your portfolios**")
    st.markdown("---")
    
    if not symbol_details:
        st.info("No symbols found in any portfolio.")
        if st.button("🔙 Back", use_container_width=True):
            st.rerun()
        return
    
    # Create a sorted list for display
    symbols_list = []
    for symbol, details in symbol_details.items():
        symbols_list.append({
            "Symbol": symbol,
            "Company Name": details.get('company_name', 'Unknown'),
            "Sector": details.get('sector', 'Other')
        })
    
    # Sort by symbol
    symbols_list.sort(key=lambda x: x['Symbol'])
    
    # Display summary
    st.info(f"📊 **Total Unique Symbols:** {len(symbols_list)}")
    
    # Display table
    st.markdown("### 📋 Symbol Details")
    
    # Create table header
    header_cols = st.columns([1, 2.5, 1.5])
    with header_cols[0]:
        st.markdown("**Symbol**")
    with header_cols[1]:
        st.markdown("**Company Name**")
    with header_cols[2]:
        st.markdown("**Sector**")
    
    st.markdown("---")
    
    # Display rows
    for symbol_data in symbols_list:
        row_cols = st.columns([1, 2.5, 1.5])
        with row_cols[0]:
            st.write(symbol_data["Symbol"])
        with row_cols[1]:
            # Truncate long company names
            company_name = symbol_data["Company Name"]
            if len(company_name) > 35:
                company_name = company_name[:32] + "..."
            st.write(company_name)
        with row_cols[2]:
            st.write(symbol_data["Sector"])
    
    st.markdown("---")
    
    # Back button
    if st.button("🔙 Back", use_container_width=True):
        st.rerun()

@st.dialog("Active Positions Details")
def show_active_positions_dialog(active_symbol_details):
    """Modal dialog showing only active symbols (quantity > 0)"""
    st.markdown("**Active symbols with holdings > 0**")
    st.markdown("---")
    
    if not active_symbol_details:
        st.info("No active positions found.")
        if st.button("🔙 Back", use_container_width=True):
            st.rerun()
        return
    
    # Create a sorted list for display
    active_symbols_list = []
    for symbol, details in active_symbol_details.items():
        active_symbols_list.append({
            "Symbol": symbol,
            "Company Name": details.get('company_name', 'Unknown'),
            "Sector": details.get('sector', 'Other')
        })
    
    # Sort by symbol
    active_symbols_list.sort(key=lambda x: x['Symbol'])
    
    # Display summary
    st.info(f"📊 **Active Positions:** {len(active_symbols_list)}")
    
    # Display table
    st.markdown("### 📋 Active Symbol Details")
    
    # Create table header
    header_cols = st.columns([1, 2.5, 1.5])
    with header_cols[0]:
        st.markdown("**Symbol**")
    with header_cols[1]:
        st.markdown("**Company Name**")
    with header_cols[2]:
        st.markdown("**Sector**")
    
    st.markdown("---")
    
    # Display rows
    for symbol_data in active_symbols_list:
        row_cols = st.columns([1, 2.5, 1.5])
        with row_cols[0]:
            st.write(symbol_data["Symbol"])
        with row_cols[1]:
            # Truncate long company names
            company_name = symbol_data["Company Name"]
            if len(company_name) > 35:
                company_name = company_name[:32] + "..."
            st.write(company_name)
        with row_cols[2]:
            st.write(symbol_data["Sector"])
    
    st.markdown("---")
    
    # Back button
    if st.button("🔙 Back", use_container_width=True):
        st.rerun()

# Helper function for safe percentage calculations
def _safe_percentage(numerator, denominator):
    """Safely calculate percentage to avoid divide by zero errors"""
    try:
        return (numerator / denominator * 100) if denominator != 0 else 0
    except (ZeroDivisionError, TypeError):
        return 0

st.title("🏦 HK Strategy Dashboard")
st.caption("Multi-portfolio HK stock tracking system")
st.markdown("---")

# Initialize session state with database integration
if 'portfolios' not in st.session_state:
    try:
        # Load portfolios from database
        portfolio_manager = get_portfolio_manager()
        st.session_state.portfolios = portfolio_manager.get_all_portfolios()
        
        # Debug info
        if st.session_state.portfolios:
            st.success(f"✅ Loaded {len(st.session_state.portfolios)} portfolios from database")
        else:
            st.warning("⚠️ No portfolios loaded - this shouldn't happen!")
            
    except Exception as e:
        st.error(f"❌ Failed to initialize portfolios: {str(e)}")
        # Fallback to empty dict to prevent crashes
        st.session_state.portfolios = {}
    
if 'portfolio_manager' not in st.session_state:
    st.session_state.portfolio_manager = get_portfolio_manager()

if 'portfolio_prices' not in st.session_state:
    st.session_state.portfolio_prices = {}
    
if 'fetch_details' not in st.session_state:
    st.session_state.fetch_details = {}
    
if 'last_update' not in st.session_state:
    st.session_state.last_update = {}

if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = {}

if 'portfolio_backup' not in st.session_state:
    st.session_state.portfolio_backup = {}

if 'current_page' not in st.session_state:
    st.session_state.current_page = 'overview'  # Start with overview by default

if 'pending_changes' not in st.session_state:
    st.session_state.pending_changes = {}

if 'portfolio_switch_request' not in st.session_state:
    st.session_state.portfolio_switch_request = None

# Track the actual current portfolio selection (not just default)
if 'current_portfolio_selection' not in st.session_state:
    st.session_state.current_portfolio_selection = None

if 'last_save_status' not in st.session_state:
    st.session_state.last_save_status = {}

if 'portfolio_timestamps' not in st.session_state:
    st.session_state.portfolio_timestamps = {}

# Initialize PV Analysis components
if 'db_manager' not in st.session_state:
    st.session_state.db_manager = DatabaseManager()

if 'analysis_manager' not in st.session_state:
    st.session_state.analysis_manager = AnalysisManager(st.session_state.db_manager)

if 'selected_portfolio_for_pv' not in st.session_state:
    st.session_state.selected_portfolio_for_pv = None

if 'current_analysis' not in st.session_state:
    st.session_state.current_analysis = None

def fetch_hk_price(hk_symbol):
    """Fetch current price for Hong Kong stock"""
    try:
        stock = yf.Ticker(hk_symbol)
        hist = stock.history(period="2d")
        if not hist.empty:
            price = float(hist['Close'].iloc[-1])
            return price, f"✅ {hk_symbol}: HK${price:.2f} (from history)"
        
        info = stock.info
        current_price = info.get('currentPrice', info.get('regularMarketPrice', info.get('previousClose')))
        if current_price and current_price > 0:
            price = float(current_price)
            return price, f"📈 {hk_symbol}: HK${price:.2f} (from info)"
            
        fallback_price = 75.0
        return fallback_price, f"⚠️ {hk_symbol}: Using fallback price HK${fallback_price:.2f}"
        
    except Exception as e:
        recent_prices = {
            "0005.HK": 100.10, "0316.HK": 140.50, "0388.HK": 447.60, "0700.HK": 599.00,
            "0823.HK": 41.26, "0857.HK": 7.39, "0939.HK": 7.49, "1810.HK": 53.20,
            "2888.HK": 144.50, "3690.HK": 116.30, "9618.HK": 121.30, "9988.HK": 121.50
        }
        price = recent_prices.get(hk_symbol, 75.0)
        return price, f"❌ {hk_symbol}: Error - using cached price HK${price:.2f}"

def fetch_hk_historical_prices(hk_symbol):
    """Fetch current and previous day prices for Hong Kong stock"""
    try:
        stock = yf.Ticker(hk_symbol)
        hist = stock.history(period="5d")  # Get 5 days to ensure we have previous trading day
        if not hist.empty and len(hist) >= 2:
            current_price = float(hist['Close'].iloc[-1])
            previous_price = float(hist['Close'].iloc[-2])
            return current_price, previous_price, f"✅ {hk_symbol}: Current HK${current_price:.2f}, Previous HK${previous_price:.2f}"
        elif not hist.empty and len(hist) == 1:
            # Only one day available, use it for both
            price = float(hist['Close'].iloc[-1])
            return price, price, f"⚠️ {hk_symbol}: Only one day available HK${price:.2f}"
        else:
            # No historical data, fall back to info
            info = stock.info
            current_price = info.get('currentPrice', info.get('regularMarketPrice', info.get('previousClose')))
            if current_price and current_price > 0:
                price = float(current_price)
                # Estimate previous price as 99% of current (small realistic change)
                prev_price = price * 0.99
                return price, prev_price, f"📈 {hk_symbol}: Current HK${price:.2f}, Estimated Prev HK${prev_price:.2f}"
            else:
                # Use fallback prices
                fallback_price = 75.0
                prev_fallback = fallback_price * 0.99
                return fallback_price, prev_fallback, f"⚠️ {hk_symbol}: Using fallback prices"
        
    except Exception as e:
        recent_prices = {
            "0005.HK": 100.10, "0316.HK": 140.50, "0388.HK": 447.60, "0700.HK": 599.00,
            "0823.HK": 41.26, "0857.HK": 7.39, "0939.HK": 7.49, "1810.HK": 53.20,
            "2888.HK": 144.50, "3690.HK": 116.30, "9618.HK": 121.30, "9988.HK": 121.50
        }
        current_price = recent_prices.get(hk_symbol, 75.0)
        previous_price = current_price * 0.99  # Small realistic change
        return current_price, previous_price, f"❌ {hk_symbol}: Error - using cached prices"

def get_company_name(symbol):
    """Try to fetch company name from Yahoo Finance"""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        return info.get('longName', info.get('shortName', 'Unknown Company'))
    except:
        return 'Unknown Company'

@st.cache_data
def get_all_portfolios_for_equity_analysis():
    """Get all available portfolios for equity analysis selection"""
    try:
        portfolios = []
        if 'portfolios' in st.session_state and st.session_state.portfolios:
            for portfolio_id, portfolio_data in st.session_state.portfolios.items():
                portfolios.append({
                    'portfolio_id': portfolio_id,
                    'name': portfolio_data.get('name', portfolio_id) if isinstance(portfolio_data, dict) else portfolio_id
                })
        
        # Add "All Portfolio Overview" option
        portfolios.insert(0, {
            'portfolio_id': 'all_overview',
            'name': 'All Portfolio Overview'
        })
        
        return portfolios
    except Exception as e:
        st.error(f"Error loading portfolios: {e}")
        return [{
            'portfolio_id': 'all_overview',
            'name': 'All Portfolio Overview'
        }]

@st.cache_data
def get_portfolio_analyses_for_equity(portfolio_id: str):
    """Get all portfolio analyses for a specific portfolio"""
    try:
        db = st.session_state.db_manager
        conn = db.get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, name, start_date, end_date
            FROM portfolio_analyses
            WHERE name ILIKE %s
            ORDER BY created_at DESC
        """, (f"%{portfolio_id}%",))
        
        results = cur.fetchall()
        conn.close()
        
        return [{'id': r[0], 'name': r[1], 'start_date': r[2], 'end_date': r[3]} for r in results]
    except:
        return []

def get_equities_from_portfolio(portfolio_id: str):
    """Get all equities/symbols from a specific portfolio (both active and inactive positions)"""
    try:
        # Validate that portfolio data exists in session state
        if 'portfolios' not in st.session_state or not st.session_state.portfolios:
            if 'debug_mode' in st.session_state and st.session_state.debug_mode:
                st.warning("⚠️ Debug: No portfolio data found in session state")
            return []
        
        if portfolio_id == 'all_overview':
            # For "All Portfolio Overview", get all unique equities from all portfolios
            all_equities = []
            for pid, portfolio_data in st.session_state.portfolios.items():
                if 'positions' in portfolio_data and portfolio_data['positions']:
                    for position in portfolio_data['positions']:
                        equity = {
                            'symbol': position['symbol'],
                            'company_name': position.get('company_name', 'Unknown Company')
                        }
                        # Avoid duplicates by checking if equity already exists
                        if not any(e['symbol'] == equity['symbol'] for e in all_equities):
                            all_equities.append(equity)
            
            # Debug output
            if 'debug_mode' in st.session_state and st.session_state.debug_mode:
                st.info(f"🔍 Debug: Found {len(all_equities)} unique equities across all portfolios")
            
            return all_equities
            
        elif portfolio_id in st.session_state.portfolios:
            # Get positions from the specific portfolio
            portfolio_data = st.session_state.portfolios[portfolio_id]
            if 'positions' in portfolio_data and portfolio_data['positions']:
                equities = []
                active_count = 0
                inactive_count = 0
                
                for position in portfolio_data['positions']:
                    equity = {
                        'symbol': position['symbol'],
                        'company_name': position.get('company_name', 'Unknown Company')
                    }
                    equities.append(equity)
                    
                    # Count active vs inactive for debug
                    if position.get('quantity', 0) > 0:
                        active_count += 1
                    else:
                        inactive_count += 1
                
                # Debug output
                if 'debug_mode' in st.session_state and st.session_state.debug_mode:
                    st.info(f"🔍 Debug: Portfolio {portfolio_id} has {len(equities)} total equities ({active_count} active, {inactive_count} inactive)")
                
                return equities
            else:
                # Portfolio exists but has no positions
                if 'debug_mode' in st.session_state and st.session_state.debug_mode:
                    st.info(f"🔍 Debug: Portfolio {portfolio_id} exists but has no positions")
                return []
        else:
            # Portfolio ID not found
            if 'debug_mode' in st.session_state and st.session_state.debug_mode:
                st.warning(f"⚠️ Debug: Portfolio {portfolio_id} not found in session state")
            return []
            
    except Exception as e:
        st.error(f"❌ Error loading equities for portfolio {portfolio_id}: {str(e)}")
        if 'debug_mode' in st.session_state and st.session_state.debug_mode:
            st.error(f"🔍 Debug: Exception details: {type(e).__name__}: {e}")
        return []

def convert_for_database(value):
    """Convert NumPy/pandas values to database-compatible Python types"""
    import numpy as np
    import pandas as pd
    
    try:
        # Handle None values first
        if value is None:
            return None
        
        # Handle pandas Timestamp early (before numeric checks)
        if isinstance(value, pd.Timestamp):
            return value.date()
        
        # Handle Python native date/datetime objects
        if hasattr(value, 'date') and callable(getattr(value, 'date')):
            if hasattr(value, 'time'):  # datetime object
                return value.date()
            else:  # date object
                return value
        
        # Handle string types early
        # Handle NumPy 2.0 compatibility (np.unicode_ was removed)
        string_types = [str, np.str_]
        try:
            string_types.append(np.unicode_)  # For NumPy < 2.0
        except AttributeError:
            pass  # NumPy 2.0+ doesn't have np.unicode_
        
        if isinstance(value, tuple(string_types)):
            return str(value)
        
        # Handle boolean types (before numeric checks to avoid conversion issues)
        # Handle NumPy 2.0 compatibility (np.bool8 was removed)
        bool_types = [bool, np.bool_]
        try:
            bool_types.append(np.bool8)  # For NumPy < 2.0
        except AttributeError:
            pass  # NumPy 2.0+ doesn't have np.bool8
        
        if isinstance(value, tuple(bool_types)):
            return bool(value)
        
        # Now handle numeric types with proper validation
        # Check for NaN only on numeric-like values
        try:
            if pd.isna(value):
                return None
        except (TypeError, ValueError):
            # pd.isna() failed, value is likely not numeric-compatible
            pass
        
        # Check for infinity only on float types that support it
        try:
            # Only check infinity for float types (int cannot be infinite)
            if isinstance(value, (float, np.floating)) and np.isinf(value):
                return None
        except (TypeError, ValueError):
            # np.isinf() failed, continue with other conversions
            pass
        
        # Convert NumPy numeric types to Python native types
        if isinstance(value, (np.integer, np.signedinteger, np.unsignedinteger)):
            return int(value)
        elif isinstance(value, (np.floating, np.float64, np.float32, np.float16)):
            # Convert to Python float first
            python_float = float(value)
            # Check if this float is actually a whole number (for BIGINT compatibility)
            if python_float.is_integer():
                return int(python_float)
            return python_float
        
        # Handle Python native numeric types
        if isinstance(value, (int, float)):
            # Check if float values are whole numbers (for BIGINT compatibility)
            if isinstance(value, float) and value.is_integer():
                return int(value)
            return value
        
        # Handle complex numbers (convert to None as database can't store them)
        if isinstance(value, (complex, np.complex64, np.complex128)):
            return None
        
        # Handle array-like objects by taking first element or converting to string
        if hasattr(value, '__iter__') and not isinstance(value, str):
            try:
                # If it's a single-element array/series, extract the value
                if hasattr(value, '__len__') and len(value) == 1:
                    return convert_for_database(value[0])
                elif hasattr(value, '__len__') and len(value) == 0:
                    return None
                else:
                    # Multi-element array, convert to string representation
                    return str(value)
            except:
                return str(value)
        
        # Fallback: return as-is for unhandled Python native types
        return value
        
    except Exception as e:
        # Enhanced error handling for conversion failures
        try:
            import streamlit as st
            if hasattr(st, 'session_state') and st.session_state.get('debug_mode', False):
                st.error(f"🔍 Debug: Conversion failed for value: {repr(value)} (type: {type(value)})")
                st.error(f"🔍 Debug: Conversion error: {str(e)}")
        except:
            # If streamlit debug fails, ignore and continue
            pass
        
        # Fallback to string conversion or None
        try:
            return str(value)
        except:
            return None

@st.cache_data
def fetch_and_store_yahoo_data(symbol: str, start_date: str, end_date: str):
    """Fetch data from Yahoo Finance and store in database if missing"""
    try:
        import yfinance as yf
        from datetime import datetime, timedelta
        import pandas as pd
        import numpy as np
        
        # Check existing data coverage in database
        db = st.session_state.db_manager
        conn = db.get_connection()
        
        with conn.cursor() as cur:
            cur.execute("""
                SELECT MIN(trade_date), MAX(trade_date), COUNT(*)
                FROM daily_equity_technicals
                WHERE symbol = %s
                  AND trade_date >= %s
                  AND trade_date <= %s
            """, (symbol, start_date, end_date))
            
            result = cur.fetchone()
            existing_start, existing_end, count = result
            
            # Convert dates to datetime objects
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Calculate expected trading days (rough estimate)
            expected_days = (end_dt - start_dt).days
            data_coverage = count / max(expected_days * 0.7, 1)  # Assume ~70% are trading days
            
            needs_fetching = False
            if count == 0 or data_coverage < 0.8:  # Less than 80% coverage
                needs_fetching = True
            elif existing_start is None or existing_end is None:
                needs_fetching = True
            elif existing_start > start_dt.date() or existing_end < end_dt.date():
                needs_fetching = True
            
            if needs_fetching:
                # Fetch data from Yahoo Finance
                st.info(f"📊 Fetching data for {symbol} from Yahoo Finance...")
                
                ticker = yf.Ticker(symbol)
                hist_data = ticker.history(start=start_dt, end=end_dt + timedelta(days=1))
                
                if not hist_data.empty:
                    # Calculate technical indicators
                    hist_data['rsi_14'] = calculate_rsi(hist_data['Close'], 14)
                    hist_data['sma_20'] = hist_data['Close'].rolling(window=20).mean()
                    hist_data['ema_12'] = hist_data['Close'].ewm(span=12).mean()
                    hist_data['ema_26'] = hist_data['Close'].ewm(span=26).mean()
                    
                    # Calculate MACD
                    hist_data['macd'] = hist_data['ema_12'] - hist_data['ema_26']
                    hist_data['macd_signal'] = hist_data['macd'].ewm(span=9).mean()
                    
                    # Calculate Bollinger Bands
                    bb_period = 20
                    bb_std = 2
                    sma = hist_data['Close'].rolling(window=bb_period).mean()
                    std = hist_data['Close'].rolling(window=bb_period).std()
                    hist_data['bollinger_upper'] = sma + (std * bb_std)
                    hist_data['bollinger_middle'] = sma  # Middle band is the 20-day SMA
                    hist_data['bollinger_lower'] = sma - (std * bb_std)
                    
                    # Volume SMA
                    hist_data['volume_sma_20'] = hist_data['Volume'].rolling(window=20).mean()
                    
                    # Insert/update data in database
                    for date, row in hist_data.iterrows():
                        cur.execute("""
                            INSERT INTO daily_equity_technicals (
                                symbol, trade_date, open_price, close_price, high_price, low_price, volume,
                                rsi_14, macd, macd_signal, bollinger_upper, bollinger_middle, bollinger_lower, 
                                sma_20, ema_12, ema_26, volume_sma_20
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (symbol, trade_date) 
                            DO UPDATE SET
                                open_price = EXCLUDED.open_price,
                                close_price = EXCLUDED.close_price,
                                high_price = EXCLUDED.high_price,
                                low_price = EXCLUDED.low_price,
                                volume = EXCLUDED.volume,
                                rsi_14 = EXCLUDED.rsi_14,
                                macd = EXCLUDED.macd,
                                macd_signal = EXCLUDED.macd_signal,
                                bollinger_upper = EXCLUDED.bollinger_upper,
                                bollinger_middle = EXCLUDED.bollinger_middle,
                                bollinger_lower = EXCLUDED.bollinger_lower,
                                sma_20 = EXCLUDED.sma_20,
                                ema_12 = EXCLUDED.ema_12,
                                ema_26 = EXCLUDED.ema_26,
                                volume_sma_20 = EXCLUDED.volume_sma_20
                        """, (
                            symbol, 
                            convert_for_database(date.date()), 
                            convert_for_database(row['Open']), 
                            convert_for_database(row['Close']), 
                            convert_for_database(row['High']), 
                            convert_for_database(row['Low']), 
                            convert_for_database(row['Volume']),
                            convert_for_database(row.get('rsi_14')), 
                            convert_for_database(row.get('macd')), 
                            convert_for_database(row.get('macd_signal')),
                            convert_for_database(row.get('bollinger_upper')), 
                            convert_for_database(row.get('bollinger_middle')),
                            convert_for_database(row.get('bollinger_lower')),
                            convert_for_database(row.get('sma_20')), 
                            convert_for_database(row.get('ema_12')), 
                            convert_for_database(row.get('ema_26')), 
                            convert_for_database(row.get('volume_sma_20'))
                        ))
                    
                    conn.commit()
                    st.success(f"✅ Successfully fetched and stored {len(hist_data)} days of data for {symbol}")
                    return True
                else:
                    st.warning(f"⚠️ No data available for {symbol} in Yahoo Finance")
                    return False
            else:
                st.info(f"✅ Data for {symbol} already available in database")
                return True
                
    except Exception as e:
        # Enhanced error handling with specific error types
        error_msg = str(e)
        
        if "np." in error_msg or "numpy" in error_msg.lower():
            st.error(f"❌ Data type conversion error for {symbol}: NumPy types detected in database insertion")
            st.error("🔧 This suggests a data conversion issue. Please enable Debug Mode for more details.")
        elif "does not exist" in error_msg and "schema" in error_msg:
            st.error(f"❌ Database schema error for {symbol}: {error_msg}")
            st.error("🔧 This suggests improper data types being passed to PostgreSQL")
        else:
            st.error(f"❌ Error fetching data for {symbol}: {error_msg}")
        
        # Debug information
        if 'debug_mode' in st.session_state and st.session_state.debug_mode:
            st.error(f"🔍 Debug: Full exception details:")
            st.error(f"Exception type: {type(e).__name__}")
            st.error(f"Exception message: {error_msg}")
            
            # Try to show some sample data types if available
            try:
                import yfinance as yf
                from datetime import datetime, timedelta
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                ticker = yf.Ticker(symbol)
                sample_data = ticker.history(start=start_dt, end=end_dt, period="5d")
                
                if not sample_data.empty:
                    row = sample_data.iloc[0]
                    st.error("🔍 Debug: Sample data types:")
                    for col in ['Open', 'Close', 'High', 'Low', 'Volume']:
                        if col in row:
                            st.error(f"  {col}: {type(row[col])} = {row[col]}")
            except:
                pass
        
        return False

def calculate_rsi(prices, window=14):
    """Calculate RSI indicator with enhanced error handling"""
    try:
        import numpy as np
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        
        # Handle division by zero more carefully
        # Replace zero losses with a small value to avoid infinite RS values
        loss = loss.replace(0, np.nan)
        rs = gain / loss
        
        # Handle infinite and NaN values before final calculation
        rs = rs.replace([np.inf, -np.inf], np.nan)
        
        # Calculate RSI, handling NaN values
        rsi = 100 - (100 / (1 + rs))
        
        # Clean up any remaining problematic values
        rsi = rsi.replace([np.inf, -np.inf], np.nan)
        
        return rsi
        
    except Exception as e:
        # Enhanced error reporting
        try:
            import streamlit as st
            if hasattr(st, 'session_state') and st.session_state.get('debug_mode', False):
                st.error(f"🔍 Debug RSI Error: {str(e)}")
                st.error(f"🔍 Debug RSI Prices Shape: {prices.shape if hasattr(prices, 'shape') else 'No shape'}")
                st.error(f"🔍 Debug RSI Prices Type: {type(prices)}")
        except:
            pass
        return None

def calculate_rsi_realtime(prices, period=14):
    """Calculate RSI with configurable period for real-time use"""
    try:
        delta = prices.diff()
        gain = delta.clip(lower=0)  # Positive price changes
        loss = -delta.clip(upper=0)  # Negative price changes (made positive)
        avg_gain = gain.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
        avg_loss = loss.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)
    except Exception as e:
        return pd.Series([50] * len(prices), index=prices.index)

def calculate_macd_realtime(prices, fast=12, slow=26, signal=9):
    """Calculate MACD with configurable parameters for real-time use"""
    try:
        ema_fast = prices.ewm(span=fast, adjust=False, min_periods=fast).mean()
        ema_slow = prices.ewm(span=slow, adjust=False, min_periods=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False, min_periods=signal).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    except Exception as e:
        # Return zeros if calculation fails
        zeros = pd.Series([0] * len(prices), index=prices.index)
        return zeros, zeros, zeros

def calculate_ema_realtime(prices, period):
    """Calculate EMA with configurable period for real-time use"""
    try:
        ema = prices.ewm(span=period, adjust=False, min_periods=period).mean()
        return ema
    except Exception as e:
        # Return original prices if calculation fails
        return prices

@st.cache_data
def get_analysis_period_for_equity(analysis_id: int):
    """Get the analysis period (start_date, end_date) for a specific analysis"""
    try:
        db = st.session_state.db_manager
        conn = db.get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT start_date, end_date, name
            FROM portfolio_analyses
            WHERE id = %s
        """, (analysis_id,))
        
        result = cur.fetchone()
        conn.close()
        
        if result:
            return {'start_date': result[0], 'end_date': result[1], 'name': result[2]}
        return None
    except:
        return None

@st.cache_data
def fetch_technical_analysis_data(symbol: str):
    """Fetch technical analysis data from daily_equity_technicals table"""
    try:
        db = st.session_state.db_manager
        conn = db.get_connection()
        cur = conn.cursor()
        
        # Get latest technical data for this symbol
        cur.execute("""
            SELECT 
                high_price as day_high,
                low_price as day_low,
                week_52_high,
                week_52_low,
                rsi_14,
                ema_12,
                ema_26,
                sma_20,
                macd,
                volume_ratio,
                atr_14,
                support_level,
                close_price,
                trade_date,
                bollinger_upper,
                bollinger_middle,
                bollinger_lower
            FROM daily_equity_technicals 
            WHERE symbol = %s 
            ORDER BY trade_date DESC 
            LIMIT 1
        """, (symbol,))
        
        result = cur.fetchone()
        conn.close()
        
        if result:
            return {
                'day_high': result[0],
                'day_low': result[1],
                'week_52_high': result[2],
                'week_52_low': result[3],
                'rsi_14': result[4],
                'ema_12': result[5],
                'ema_26': result[6],
                'sma_20': result[7],
                'macd': result[8],
                'volume_ratio': result[9],
                'atr_14': result[10],
                'support_level': result[11],
                'close_price': result[12],
                'trade_date': result[13],
                'bollinger_upper': result[14],
                'bollinger_middle': result[15],
                'bollinger_lower': result[16]
            }
        else:
            # Return fallback data if no technical data found
            return get_fallback_technical_data(symbol)
            
    except Exception as e:
        st.error(f"Error fetching technical data: {e}")
        return get_fallback_technical_data(symbol)

def get_fallback_technical_data(symbol: str):
    """Provide fallback technical data when database data is unavailable"""
    # Try to fetch some basic price data from Yahoo Finance
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1y")
        
        if not hist.empty:
            current_price = hist['Close'].iloc[-1]
            day_high = hist['High'].iloc[-1]
            day_low = hist['Low'].iloc[-1]
            week_52_high = hist['High'].max()
            week_52_low = hist['Low'].min()
            
            # Calculate simple RSI approximation
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1] if not rsi.empty else 50.0
            
            # Calculate Bollinger Bands
            sma_20 = hist['Close'].rolling(20).mean().iloc[-1]
            std_20 = hist['Close'].rolling(20).std().iloc[-1]
            bollinger_upper = sma_20 + (2 * std_20)
            bollinger_middle = sma_20
            bollinger_lower = sma_20 - (2 * std_20)
            
            return {
                'day_high': day_high,
                'day_low': day_low,
                'week_52_high': week_52_high,
                'week_52_low': week_52_low,
                'rsi_14': current_rsi,
                'ema_12': current_price * 1.01,  # Approximation
                'ema_26': current_price * 0.99,  # Approximation
                'sma_20': sma_20,
                'macd': 0.5,  # Placeholder
                'volume_ratio': 1.0,  # Placeholder
                'atr_14': (day_high - day_low),
                'support_level': week_52_low * 1.05,
                'close_price': current_price,
                'trade_date': hist.index[-1].date(),
                'bollinger_upper': bollinger_upper,
                'bollinger_middle': bollinger_middle,
                'bollinger_lower': bollinger_lower
            }
    except:
        pass
    
    # Final fallback with placeholder data
    return {
        'day_high': 325.50,
        'day_low': 318.20,
        'week_52_high': 385.00,
        'week_52_low': 245.80,
        'rsi_14': 65.2,
        'ema_12': 321.45,
        'ema_26': 315.80,
        'sma_20': 319.60,
        'macd': 2.45,
        'volume_ratio': 1.35,
        'atr_14': 8.45,
        'support_level': 310.00,
        'close_price': 320.00,
        'trade_date': None,
        'bollinger_upper': 335.20,
        'bollinger_middle': 319.60,
        'bollinger_lower': 304.00
    }

@st.cache_data
def fetch_equity_prices_by_date(symbol: str, target_date):
    """
    Fetch OHLCV data for a specific symbol and date from daily_equity_technicals table
    
    Args:
        symbol: Stock symbol (e.g., '0700.HK')
        target_date: Target date (date object or string)
        
    Returns:
        Dict with open_price, close_price, high_price, low_price, volume, trade_date, data_source
    """
    try:
        db = st.session_state.db_manager
        conn = db.get_connection()
        cur = conn.cursor()
        
        # Convert date to string if needed
        if hasattr(target_date, 'strftime'):
            date_str = target_date.strftime('%Y-%m-%d')
        else:
            date_str = str(target_date)
        
        # First try: exact date match
        cur.execute("""
            SELECT open_price, close_price, high_price, low_price, volume, trade_date
            FROM daily_equity_technicals 
            WHERE symbol = %s AND trade_date = %s
        """, (symbol, date_str))
        
        result = cur.fetchone()
        
        if result:
            return {
                'open_price': float(result[0]) if result[0] else None,
                'close_price': float(result[1]) if result[1] else None,
                'high_price': float(result[2]) if result[2] else None,
                'low_price': float(result[3]) if result[3] else None,
                'volume': int(result[4]) if result[4] else None,
                'trade_date': result[5],
                'data_source': 'database_exact'
            }
        
        # Second try: nearest date (within 7 days)
        cur.execute("""
            SELECT open_price, close_price, high_price, low_price, volume, trade_date
            FROM daily_equity_technicals 
            WHERE symbol = %s 
            AND ABS(trade_date - %s::date) <= 7
            ORDER BY ABS(trade_date - %s::date)
            LIMIT 1
        """, (symbol, date_str, date_str))
        
        result = cur.fetchone()
        
        if result:
            return {
                'open_price': float(result[0]) if result[0] else None,
                'close_price': float(result[1]) if result[1] else None,
                'high_price': float(result[2]) if result[2] else None,
                'low_price': float(result[3]) if result[3] else None,
                'volume': int(result[4]) if result[4] else None,
                'trade_date': result[5],
                'data_source': 'database_nearest'
            }
        
        conn.close()
        
        # Third try: Yahoo Finance fallback for the specific date
        return get_yahoo_finance_price_fallback(symbol, target_date)
        
    except Exception as e:
        st.error(f"Error fetching price data for {symbol}: {e}")
        return get_yahoo_finance_price_fallback(symbol, target_date)

def get_yahoo_finance_price_fallback(symbol: str, target_date):
    """Fallback to Yahoo Finance for specific date price data"""
    try:
        import yfinance as yf
        from datetime import timedelta
        
        # Convert target_date to date object if needed
        if hasattr(target_date, 'strftime'):
            date_obj = target_date
        else:
            from datetime import datetime
            date_obj = datetime.strptime(str(target_date), '%Y-%m-%d').date()
        
        # Fetch data around the target date
        start_date = date_obj - timedelta(days=5)
        end_date = date_obj + timedelta(days=2)
        
        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=start_date, end=end_date)
        
        if not hist.empty:
            # Try to find data for the exact date first
            target_timestamp = date_obj.strftime('%Y-%m-%d')
            
            for idx, row in hist.iterrows():
                if idx.strftime('%Y-%m-%d') == target_timestamp:
                    return {
                        'open_price': float(row['Open']),
                        'close_price': float(row['Close']),
                        'high_price': float(row['High']),
                        'low_price': float(row['Low']),
                        'volume': int(row['Volume']),
                        'trade_date': date_obj,
                        'data_source': 'yahoo_exact'
                    }
            
            # If not found, use the closest date
            latest_row = hist.iloc[-1]
            return {
                'open_price': float(latest_row['Open']),
                'close_price': float(latest_row['Close']),
                'high_price': float(latest_row['High']),
                'low_price': float(latest_row['Low']),
                'volume': int(latest_row['Volume']),
                'trade_date': hist.index[-1].date(),
                'data_source': 'yahoo_nearest'
            }
        
    except Exception as e:
        pass
    
    # Final fallback with mock data
    return {
        'open_price': 50.0,
        'close_price': 52.0,
        'high_price': 53.0,
        'low_price': 49.5,
        'volume': 1000000,
        'trade_date': target_date,
        'data_source': 'mock_fallback'
    }

def clear_modal_states():
    """Clear all modal states to prevent cross-portfolio issues"""
    st.session_state.show_detail_modal = None
    st.session_state.show_transaction_modal = None
    st.session_state.show_technical_modal = None
    st.session_state.selected_analysis_id = None
    st.session_state.selected_analysis_date = None

def load_sample_technical_data():
    """Load sample technical data into the database for demonstration"""
    try:
        db = st.session_state.db_manager
        conn = db.get_connection()
        cur = conn.cursor()
        
        # Sample data for common HK stocks - multiple dates for better testing
        sample_data = [
            # 2025-08-31 data
            ('0700.HK', '2025-08-31', 318.50, 320.00, 314.50, 625.80, 480.30, 65.2, 605.45, 590.80, 602.60, 2.45, 1.35, 8.45, 575.00, 315.00, 15000000),
            ('1810.HK', '2025-08-31', 13.20, 13.50, 12.80, 68.90, 38.50, 58.7, 54.20, 52.30, 53.85, 1.20, 1.12, 2.85, 50.00, 13.10, 25000000),
            ('3690.HK', '2025-08-31', 98.30, 101.80, 95.50, 168.20, 89.40, 62.1, 118.45, 114.20, 116.90, 1.85, 1.45, 5.20, 110.00, 97.20, 18000000),
            ('9618.HK', '2025-08-31', 130.30, 134.70, 128.90, 165.40, 95.80, 56.9, 123.20, 119.60, 122.10, 0.95, 1.28, 4.30, 115.00, 129.10, 12000000),
            ('9988.HK', '2025-08-31', 118.50, 120.30, 116.20, 178.90, 88.20, 48.3, 122.80, 118.40, 120.95, -0.65, 1.55, 6.10, 112.00, 117.80, 22000000),
            ('0005.HK', '2025-08-31', 40.20, 40.50, 39.20, 45.80, 35.20, 45.8, 39.85, 38.90, 39.95, 0.85, 1.25, 1.45, 38.50, 39.50, 8500000),
            ('0939.HK', '2025-08-31', 7.51, 7.62, 7.38, 8.95, 6.20, 52.3, 7.48, 7.35, 7.52, 0.65, 1.18, 0.25, 7.20, 7.45, 45000000),
            
            # 2025-08-30 data (previous trading day)
            ('0700.HK', '2025-08-30', 315.20, 318.50, 312.80, 625.80, 480.30, 64.8, 604.20, 589.50, 601.30, 2.38, 1.32, 8.20, 574.00, 312.50, 14500000),
            ('1810.HK', '2025-08-30', 13.05, 13.20, 12.65, 68.90, 38.50, 57.9, 53.85, 52.10, 53.60, 1.15, 1.10, 2.80, 49.80, 12.95, 24000000),
            ('3690.HK', '2025-08-30', 96.80, 98.30, 94.20, 168.20, 89.40, 61.5, 117.20, 113.80, 116.40, 1.78, 1.42, 5.10, 109.50, 96.10, 17500000),
            ('9618.HK', '2025-08-30', 128.90, 130.30, 127.40, 165.40, 95.80, 56.2, 122.50, 119.20, 121.80, 0.88, 1.25, 4.20, 114.50, 128.20, 11800000),
            ('9988.HK', '2025-08-30', 117.20, 118.50, 115.80, 178.90, 88.20, 47.8, 122.10, 118.00, 120.50, -0.72, 1.52, 6.00, 111.50, 116.90, 21500000),
            ('0005.HK', '2025-08-30', 39.80, 40.20, 39.40, 45.80, 35.20, 45.2, 39.60, 38.70, 39.75, 0.82, 1.22, 1.42, 38.30, 39.25, 8200000),
            ('0939.HK', '2025-08-30', 7.42, 7.51, 7.28, 8.95, 6.20, 51.8, 7.41, 7.32, 7.48, 0.62, 1.15, 0.24, 7.15, 7.38, 44000000),
            
            # 2025-08-29 data
            ('0700.HK', '2025-08-29', 312.50, 315.20, 310.10, 625.80, 480.30, 64.2, 602.80, 588.20, 600.10, 2.31, 1.29, 8.00, 573.00, 310.80, 14200000),
            ('1810.HK', '2025-08-29', 12.85, 13.05, 12.50, 68.90, 38.50, 57.3, 53.50, 51.90, 53.35, 1.10, 1.08, 2.75, 49.60, 12.80, 23500000),
            ('3690.HK', '2025-08-29', 95.50, 96.80, 93.80, 168.20, 89.40, 60.9, 116.00, 113.40, 116.00, 1.72, 1.39, 5.00, 109.00, 95.20, 17200000),
            
            # Add some older dates for comprehensive testing
            ('0700.HK', '2025-01-02', 295.50, 298.20, 292.80, 625.80, 480.30, 58.5, 580.20, 570.50, 585.30, 1.85, 1.15, 7.20, 565.00, 293.10, 16500000),
            ('1810.HK', '2025-01-02', 11.85, 12.15, 11.60, 68.90, 38.50, 52.3, 48.50, 47.90, 48.85, 0.95, 0.98, 2.45, 46.80, 11.75, 28000000),
            ('0005.HK', '2025-01-02', 37.80, 38.20, 37.40, 45.80, 35.20, 42.2, 37.60, 36.70, 37.75, 0.72, 1.12, 1.32, 36.30, 37.65, 9200000),
        ]
        
        for symbol, date, close, high, low, w52h, w52l, rsi, ema12, ema26, sma20, macd, vol_ratio, atr, support, open_price, volume in sample_data:
            cur.execute("""
                INSERT INTO daily_equity_technicals 
                (symbol, trade_date, open_price, close_price, high_price, low_price, week_52_high, week_52_low,
                 rsi_14, ema_12, ema_26, sma_20, macd, volume_ratio, atr_14, support_level, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, trade_date) 
                DO UPDATE SET
                    open_price = EXCLUDED.open_price,
                    close_price = EXCLUDED.close_price,
                    high_price = EXCLUDED.high_price,
                    low_price = EXCLUDED.low_price,
                    week_52_high = EXCLUDED.week_52_high,
                    week_52_low = EXCLUDED.week_52_low,
                    rsi_14 = EXCLUDED.rsi_14,
                    ema_12 = EXCLUDED.ema_12,
                    ema_26 = EXCLUDED.ema_26,
                    sma_20 = EXCLUDED.sma_20,
                    macd = EXCLUDED.macd,
                    volume_ratio = EXCLUDED.volume_ratio,
                    atr_14 = EXCLUDED.atr_14,
                    support_level = EXCLUDED.support_level,
                    volume = EXCLUDED.volume
            """, (symbol, date, open_price, close, high, low, w52h, w52l, rsi, ema12, ema26, sma20, macd, vol_ratio, atr, support, volume))
        
        conn.commit()
        conn.close()
        
        # Clear cache to force refresh of technical data
        st.cache_data.clear()
        st.success(f"✅ Loaded sample technical data for {len(sample_data)} symbols")
        st.rerun()
        
    except Exception as e:
        st.error(f"Error loading sample data: {e}")

def check_database_health():
    """Check PostgreSQL database connectivity with detailed diagnostics"""
    results = {
        "status": False,
        "message": "",
        "version": None,
        "details": [],
        "troubleshooting": []
    }
    
    # Check if psycopg2 is available
    try:
        import psycopg2
        results["details"].append("✅ psycopg2 module available")
    except ImportError:
        results["details"].append("❌ psycopg2 module not found")
        results["message"] = "PostgreSQL adapter not installed"
        results["troubleshooting"].append("Run: pip install psycopg2-binary")
        return results
    
    # Check if PostgreSQL process is running
    import subprocess
    try:
        result = subprocess.run(['pgrep', '-f', 'postgres'], capture_output=True, text=True)
        if result.stdout:
            results["details"].append(f"✅ PostgreSQL processes found: {len(result.stdout.strip().split())}")
        else:
            results["details"].append("❌ No PostgreSQL processes running")
            results["troubleshooting"].append("Start PostgreSQL: sudo systemctl start postgresql")
    except Exception as e:
        results["details"].append(f"⚠️ Process check failed: {str(e)}")
    
    # Try to get database connection from config manager
    try:
        config = get_config()
        primary_conn = config.get_database_url()
        connection_strings = [
            (primary_conn, "Configuration file"),
        ]
        
        # Add fallback connection strings as backup
        fallback_strings = [
            ("postgresql://trader:${DATABASE_PASSWORD}@localhost:5432/hk_strategy", "Legacy configured user"),
            ("postgresql://postgres@localhost:5432/hk_strategy", "Default superuser"),
            ("postgresql://bthia@localhost:5432/hk_strategy", "System user"),
            ("postgresql://postgres:postgres@localhost:5432/postgres", "Default database")
        ]
        
        # Replace password placeholder if environment variable is available
        db_password = os.getenv('DATABASE_PASSWORD', 'YOUR_PASSWORD')
        fallback_strings = [(conn.replace('${DATABASE_PASSWORD}', db_password), desc) for conn, desc in fallback_strings]
        
        results["details"].append("✅ Configuration manager loaded successfully")
        
    except ConfigurationError as e:
        results["details"].append(f"⚠️ Configuration error: {str(e)}")
        results["troubleshooting"].append("Check config/app_config.yaml exists and has valid database credentials")
        connection_strings = []
        fallback_strings = [
            ("postgresql://trader:${DATABASE_PASSWORD}@localhost:5432/hk_strategy", "Legacy configured user"),
            ("postgresql://postgres@localhost:5432/hk_strategy", "Default superuser"),
            ("postgresql://bthia@localhost:5432/hk_strategy", "System user"),
            ("postgresql://postgres:postgres@localhost:5432/postgres", "Default database")
        ]
        # Replace password placeholder if environment variable is available
        db_password = os.getenv('DATABASE_PASSWORD', 'YOUR_PASSWORD')
        fallback_strings = [(conn.replace('${DATABASE_PASSWORD}', db_password), desc) for conn, desc in fallback_strings]
    except Exception as e:
        results["details"].append(f"❌ Failed to load configuration: {str(e)}")
        results["troubleshooting"].append("Ensure src/config_manager.py is available")
        connection_strings = []
        fallback_strings = [
            ("postgresql://trader:${DATABASE_PASSWORD}@localhost:5432/hk_strategy", "Legacy configured user"),
            ("postgresql://postgres@localhost:5432/hk_strategy", "Default superuser"),
            ("postgresql://bthia@localhost:5432/hk_strategy", "System user"),
            ("postgresql://postgres:postgres@localhost:5432/postgres", "Default database")
        ]
        # Replace password placeholder if environment variable is available
        db_password = os.getenv('DATABASE_PASSWORD', 'YOUR_PASSWORD')
        fallback_strings = [(conn.replace('${DATABASE_PASSWORD}', db_password), desc) for conn, desc in fallback_strings]
    
    all_connections = connection_strings + fallback_strings
    
    for conn_str, desc in all_connections:
        try:
            conn = psycopg2.connect(conn_str, connect_timeout=3)
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                
                # Test if hk_strategy database exists
                cur.execute("SELECT datname FROM pg_database WHERE datname = 'hk_strategy';")
                db_exists = cur.fetchone() is not None
                
                # Test if portfolio tables exist
                cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'portfolio_positions');")
                table_exists = cur.fetchone()[0]
                
            conn.close()
            
            results["status"] = True
            results["message"] = f"Connected via {desc}"
            results["version"] = version
            results["details"].append(f"✅ Connection successful: {conn_str.split('@')[0]}@localhost")
            results["details"].append(f"✅ Database 'hk_strategy' exists: {db_exists}")
            results["details"].append(f"✅ Portfolio tables exist: {table_exists}")
            
            if not db_exists:
                results["troubleshooting"].append("Create database: CREATE DATABASE hk_strategy;")
            if not table_exists:
                results["troubleshooting"].append("Run init.sql to create tables")
            
            return results
            
        except psycopg2.OperationalError as e:
            error_msg = str(e)
            results["details"].append(f"❌ Failed {desc}: {error_msg}")
            
            if "password authentication failed" in error_msg:
                results["troubleshooting"].append(f"Fix authentication for {conn_str.split('@')[0]}")
            elif "does not exist" in error_msg:
                results["troubleshooting"].append("Create missing user/database")
            elif "could not connect" in error_msg:
                results["troubleshooting"].append("Check PostgreSQL service is running")
                
        except Exception as e:
            results["details"].append(f"❌ Error {desc}: {str(e)}")
    
    results["message"] = "All connection attempts failed"
    results["troubleshooting"].extend([
        "1. Check PostgreSQL is installed and running",
        "2. Create hk_strategy database and user",
        "3. Run setup commands in terminal"
    ])
    
    return results

def check_redis_health():
    """Check Redis connectivity with detailed diagnostics"""
    results = {
        "status": False,
        "message": "",
        "info": None,
        "details": [],
        "troubleshooting": []
    }
    
    # Check if redis module is available
    try:
        import redis
        results["details"].append("✅ redis module available")
    except ImportError:
        results["details"].append("❌ redis module not found")
        results["message"] = "Redis Python client not installed"
        results["troubleshooting"].append("Run: pip install redis")
        return results
    
    # Check if Redis process is running
    import subprocess
    try:
        result = subprocess.run(['pgrep', '-f', 'redis'], capture_output=True, text=True)
        if result.stdout:
            results["details"].append(f"✅ Redis processes found: {len(result.stdout.strip().split())}")
        else:
            results["details"].append("❌ No Redis processes running")
            results["troubleshooting"].append("Start Redis: sudo systemctl start redis")
    except Exception as e:
        results["details"].append(f"⚠️ Process check failed: {str(e)}")
    
    # Test Redis connection using config manager
    try:
        # Try to get Redis connection from config manager
        try:
            config = get_config()
            redis_config = config.get_redis_config()
            results["details"].append("✅ Redis configuration loaded from config manager")
            r = redis.Redis(**redis_config, decode_responses=True)
        except (ConfigurationError, Exception) as e:
            results["details"].append(f"⚠️ Config manager failed: {str(e)}")
            results["details"].append("Falling back to default Redis connection")
            r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True, socket_connect_timeout=3)
        
        # Test ping
        ping_result = r.ping()
        results["details"].append(f"✅ Ping successful: {ping_result}")
        
        # Get Redis info
        info = r.info()
        results["status"] = True
        results["message"] = f"Redis {info['redis_version']} connected"
        results["info"] = f"Memory: {info['used_memory_human']}, Uptime: {info['uptime_in_seconds']}s"
        results["details"].append(f"✅ Version: {info['redis_version']}")
        results["details"].append(f"✅ Connected clients: {info['connected_clients']}")
        results["details"].append(f"✅ Memory usage: {info['used_memory_human']}")
        
        # Test read/write
        test_key = "health_check_test"
        r.set(test_key, "test_value", ex=10)
        test_value = r.get(test_key)
        if test_value == "test_value":
            results["details"].append("✅ Read/write test successful")
        else:
            results["details"].append("❌ Read/write test failed")
            
    except redis.ConnectionError as e:
        results["details"].append(f"❌ Connection error: {str(e)}")
        results["message"] = "Cannot connect to Redis server"
        results["troubleshooting"].extend([
            "Check Redis is installed: redis-server --version",
            "Start Redis: sudo systemctl start redis",
            "Check port 6379 is available: netstat -tlnp | grep 6379"
        ])
    except redis.AuthenticationError as e:
        results["details"].append(f"❌ Authentication error: {str(e)}")
        results["message"] = "Redis authentication failed"
        results["troubleshooting"].append("Check Redis password configuration")
    except Exception as e:
        results["details"].append(f"❌ Unexpected error: {str(e)}")
        results["message"] = f"Redis check failed: {str(e)}"
        results["troubleshooting"].append("Check Redis configuration and logs")
    
    return results

def check_yfinance_health():
    """Check Yahoo Finance API connectivity with detailed diagnostics"""
    results = {
        "status": False,
        "message": "",
        "test_data": None,
        "details": [],
        "troubleshooting": []
    }
    
    # Check if yfinance module is available
    try:
        import yfinance as yf
        results["details"].append("✅ yfinance module available")
    except ImportError:
        results["details"].append("❌ yfinance module not found")
        results["message"] = "Yahoo Finance library not installed"
        results["troubleshooting"].append("Run: pip install yfinance")
        return results
    
    # Check internet connectivity
    import urllib.request
    try:
        urllib.request.urlopen('https://finance.yahoo.com', timeout=5)
        results["details"].append("✅ Internet connectivity to Yahoo Finance")
    except Exception as e:
        results["details"].append(f"❌ Internet connectivity failed: {str(e)}")
        results["troubleshooting"].append("Check internet connection")
        results["troubleshooting"].append("Check firewall/proxy settings")
    
    # Test with multiple symbols
    test_symbols = [
        ("AAPL", "US Stock"),
        ("0005.HK", "Hong Kong Stock"),
        ("MSFT", "US Stock Alternative")
    ]
    
    successful_tests = 0
    for symbol, desc in test_symbols:
        try:
            stock = yf.Ticker(symbol)
            
            # Test historical data
            hist = stock.history(period="2d")
            if not hist.empty:
                price = hist['Close'].iloc[-1]
                results["details"].append(f"✅ {desc} ({symbol}): ${price:.2f}")
                successful_tests += 1
                
                if successful_tests == 1:  # Use first successful test as main result
                    results["test_data"] = f"{symbol}: ${price:.2f}"
            else:
                results["details"].append(f"❌ {desc} ({symbol}): No historical data")
                
            # Test info data
            try:
                info = stock.info
                if info and len(info) > 1:
                    company_name = info.get('longName', info.get('shortName', 'Unknown'))
                    results["details"].append(f"✅ {symbol} company info: {company_name}")
                else:
                    results["details"].append(f"⚠️ {symbol} info data limited")
            except:
                results["details"].append(f"⚠️ {symbol} info fetch failed")
                
        except Exception as e:
            results["details"].append(f"❌ {desc} ({symbol}) error: {str(e)}")
    
    if successful_tests > 0:
        results["status"] = True
        results["message"] = f"Yahoo Finance API working ({successful_tests}/{len(test_symbols)} symbols)"
    else:
        results["message"] = "Yahoo Finance API failed for all test symbols"
        results["troubleshooting"].extend([
            "Check internet connection",
            "Yahoo Finance may be temporarily unavailable",
            "Try again in a few minutes",
            "Check if Yahoo Finance API has changed"
        ])
    
    # Check rate limiting
    if successful_tests < len(test_symbols):
        results["troubleshooting"].append("Possible rate limiting - reduce API calls frequency")
    
    return results

def trigger_portfolio_refresh_after_save(portfolio_id: str, changes_made: list):
    """Trigger comprehensive portfolio refresh after successful save operations"""
    try:
        # 1. Force recalculation of cached portfolio metrics
        if 'portfolio_metrics_cache' in st.session_state:
            del st.session_state['portfolio_metrics_cache']
        
        # 2. Refresh position-related caches
        if 'position_count_cache' in st.session_state:
            del st.session_state['position_count_cache']
            
        # 3. Auto-update OHLCV data for changed symbols
        if changes_made and portfolio_id:
            # Extract symbols that were updated from changes_made
            updated_symbols = []
            for change in changes_made:
                if "Updated" in change or "Added" in change:
                    # Extract symbol from messages like "Updated 1211.HK" or "Added 0700.HK"
                    parts = change.split(' ')
                    if len(parts) >= 2:
                        symbol = parts[1]
                        if '.' in symbol:  # Basic symbol validation
                            updated_symbols.append(symbol)
            
            if updated_symbols:
                # Initialize portfolio prices cache if needed
                if portfolio_id not in st.session_state.portfolio_prices:
                    st.session_state.portfolio_prices[portfolio_id] = {}
                
                # Background OHLCV update for changed symbols
                st.info(f"🔄 Auto-updating market data for {len(updated_symbols)} changed position(s)...")
                with st.spinner("Fetching latest market prices..."):
                    for symbol in updated_symbols:
                        try:
                            price, status = fetch_hk_price(symbol)
                            st.session_state.portfolio_prices[portfolio_id][symbol] = price
                        except Exception as e:
                            st.warning(f"⚠️ Could not update price for {symbol}: {str(e)}")
                    
                    # Update last update timestamp
                    st.session_state.last_update[portfolio_id] = datetime.now()
                    
                st.success(f"💰 Market data updated for: {', '.join(updated_symbols)}")
        
        return True
    except Exception as e:
        st.warning(f"⚠️ Portfolio refresh partially failed: {str(e)}")
        return False

def check_portfolio_has_analyses(portfolio_id: str) -> tuple[bool, int, str]:
    """
    Check if portfolio has existing analyses that would restrict updates
    
    Returns:
        tuple[bool, int, str]: (has_analyses, count, message)
    """
    try:
        if 'portfolio_analysis_manager' in st.session_state:
            analyses_df = st.session_state.portfolio_analysis_manager.get_analysis_summary(portfolio_id)
            analysis_count = len(analyses_df)
            
            if analysis_count > 0:
                return True, analysis_count, f"Portfolio has {analysis_count} existing analysis/analyses"
            else:
                return False, 0, "No analyses found"
        else:
            return False, 0, "Analysis manager not available"
    except Exception as e:
        return False, 0, f"Error checking analyses: {str(e)}"

def get_system_info():
    """Get system information"""
    try:
        return {
            "Python Version": f"{sys.version.split()[0]}",
            "Platform": platform.platform(),
            "Streamlit Version": st.__version__,
            "Pandas Version": pd.__version__,
            "YFinance Version": yf.__version__ if hasattr(yf, '__version__') else "Unknown",
            "Working Directory": os.getcwd(),
            "Process ID": os.getpid()
        }
    except Exception as e:
        return {"Error": str(e)}

# Initialize unified navigation state
if 'navigation' not in st.session_state:
    st.session_state.navigation = {
        'section': 'portfolios',
        'page': 'overview', 
        'context': {},
        'breadcrumbs': []
    }

# Unified Navigation Structure
navigation_structure = {
    'portfolios': {
        'icon': '📊',
        'label': 'PORTFOLIOS',
        'pages': {
            'overview': '📋 All Portfolios Overview',
            'portfolio': '📊 Portfolio Dashboard', 
            'pv_analysis': '📈 Portfolio Analysis Dashboard'
        }
    },
    'strategy': {
        'icon': '🎯', 
        'label': 'STRATEGY ANALYSIS',
        'pages': {
            'equity_analysis': '📈 Equity Strategy Analysis',
            'strategy_editor': '⚙️ Strategy Editor',
            'strategy_comparison': '📊 Strategy Comparison'
        }
    },
    'system': {
        'icon': '🔧',
        'label': 'SYSTEM & ADMIN',
        'pages': {
            'system_status': '⚙️ System Status',
            'database_admin': '🗄️ Database Management',
            'user_settings': '📋 User Settings'
        }
    }
}

# Sidebar Navigation Header
st.sidebar.markdown("""
<div style='text-align: center; padding: 10px 0;'>
    <h3 style='margin: 0; color: #1f77b4;'>🏠 HK Strategy</h3>
    <p style='margin: 0; font-size: 12px; color: #8e8ea0;'>Multi-Dashboard System</p>
</div>
""", unsafe_allow_html=True)
st.sidebar.markdown("---")

# Build Hierarchical Navigation
for section_key, section_data in navigation_structure.items():
    with st.sidebar.expander(f"{section_data['icon']} {section_data['label']}", 
                           expanded=(st.session_state.navigation['section'] == section_key)):
        
        for page_key, page_label in section_data['pages'].items():
            # Create unique key for each page button
            button_key = f"nav_{section_key}_{page_key}"
            
            # Check if this is the current page
            is_current = (st.session_state.navigation['section'] == section_key and 
                         st.session_state.navigation.get('page') == page_key)
            
            # Handle legacy page mapping for existing functionality
            legacy_page_map = {
                ('portfolios', 'overview'): 'overview',
                ('portfolios', 'portfolio'): 'portfolio', 
                ('portfolios', 'pv_analysis'): 'pv_analysis',
                ('strategy', 'equity_analysis'): 'equity_analysis',
                ('strategy', 'strategy_editor'): 'strategy_editor',
                ('strategy', 'strategy_comparison'): 'strategy_comparison',
                ('system', 'system_status'): 'system'
            }
            
            # Determine if page is available (existing vs future)
            is_available = (section_key, page_key) in legacy_page_map
            
            if is_available:
                button_type = "primary" if is_current else "secondary"
                if st.button(page_label, key=button_key, type=button_type, use_container_width=True):
                    # Update navigation state
                    st.session_state.navigation['section'] = section_key
                    st.session_state.navigation['page'] = page_key
                    
                    # Map to legacy current_page for compatibility
                    legacy_page = legacy_page_map.get((section_key, page_key))
                    if legacy_page:
                        st.session_state.current_page = legacy_page
                    
                    st.rerun()
            else:
                # Future/unavailable pages
                st.markdown(f"<div style='padding: 8px; color: #8e8ea0; font-size: 11px;'>{page_label} <em>(Coming Soon)</em></div>", 
                           unsafe_allow_html=True)

st.sidebar.markdown("---")

# Show different sidebars based on current page
if st.session_state.current_page == 'overview':
    st.sidebar.header("📁 Portfolio Management")
    st.sidebar.info("Use the overview page to manage all portfolios")
elif st.session_state.current_page == 'portfolio':
    st.sidebar.header("📁 Portfolio Management")

# Check if portfolios are available
if not st.session_state.portfolios:
    st.sidebar.error("❌ No portfolios available")
    st.sidebar.info("💡 Try refreshing the page or check database connection")
    
    # Show database health check in main area
    st.error("🚨 No portfolios loaded!")
    st.markdown("""
    **Possible causes:**
    1. Database connection failure
    2. No portfolios in database
    3. Portfolio loading error
    
    **Solutions:**
    1. Check the System Status page for database connectivity
    2. Run database setup: `sudo ./setup_database_from_env.sh`
    3. Refresh the page
    """)
    
    # Add a button to retry loading
    if st.button("🔄 Retry Loading Portfolios"):
        try:
            st.session_state.portfolios = st.session_state.portfolio_manager.get_all_portfolios()
            st.rerun()
        except Exception as e:
            st.error(f"Failed to reload portfolios: {str(e)}")
    
    st.stop()

# Portfolio keys - needed for various selectboxes throughout the app
portfolio_keys = list(st.session_state.portfolios.keys())

# Handle portfolio switch requests before widget creation
if st.session_state.portfolio_switch_request:
    requested_portfolio = st.session_state.portfolio_switch_request
    if requested_portfolio in portfolio_keys:
        # Get actual current selection from session state, not hardcoded first portfolio
        current_selected = st.session_state.current_portfolio_selection
        if not current_selected or current_selected not in portfolio_keys:
            current_selected = portfolio_keys[0] if portfolio_keys else None
            
        was_editing = False
        if current_selected and current_selected in st.session_state.edit_mode:
            was_editing = st.session_state.edit_mode[current_selected]
        
        # Update the selected portfolio and store in session state
        selected_portfolio = requested_portfolio
        st.session_state.current_portfolio_selection = requested_portfolio
        
        # Preserve edit mode if switching to same portfolio (could be a rerun from edit action)
        if requested_portfolio == current_selected and was_editing:
            if requested_portfolio not in st.session_state.edit_mode:
                st.session_state.edit_mode[requested_portfolio] = True
        
        # Clear the request
        st.session_state.portfolio_switch_request = None
    else:
        # Invalid portfolio requested, clear request and use current selection
        st.session_state.portfolio_switch_request = None
        selected_portfolio = st.session_state.current_portfolio_selection
        if not selected_portfolio or selected_portfolio not in portfolio_keys:
            selected_portfolio = portfolio_keys[0] if portfolio_keys else None
            st.session_state.current_portfolio_selection = selected_portfolio
else:
    # Initialize from session state or use first portfolio as fallback
    selected_portfolio = st.session_state.current_portfolio_selection
    if not selected_portfolio or selected_portfolio not in portfolio_keys:
        selected_portfolio = portfolio_keys[0] if portfolio_keys else None
        st.session_state.current_portfolio_selection = selected_portfolio

is_editing = False
current_portfolio = None

# Set portfolio-specific variables for portfolio page
if st.session_state.current_page == 'portfolio' and selected_portfolio:
    # Portfolio selection logic (only for portfolio page)
    # Calculate the index for the selected portfolio
    portfolio_index = portfolio_keys.index(selected_portfolio) if selected_portfolio in portfolio_keys else 0
    
    selected_portfolio = st.sidebar.selectbox(
        "Select Portfolio:",
        options=portfolio_keys,
        format_func=lambda x: f"{x} ({len([p for p in st.session_state.portfolios[x]['positions'] if p['quantity'] > 0])} positions)",
        index=portfolio_index,
        key="portfolio_selector_early"
    )
    
    # Store the actual user selection in session state
    st.session_state.current_portfolio_selection = selected_portfolio
    
    if selected_portfolio:
        current_portfolio = st.session_state.portfolios[selected_portfolio]
        
        # Initialize session state for table editing early to prevent race conditions
        if f'edit_mode_{selected_portfolio}' not in st.session_state:
            st.session_state[f'edit_mode_{selected_portfolio}'] = {}
        if f'deleted_positions_{selected_portfolio}' not in st.session_state:
            st.session_state[f'deleted_positions_{selected_portfolio}'] = set()
        if f'modified_positions_{selected_portfolio}' not in st.session_state:
            st.session_state[f'modified_positions_{selected_portfolio}'] = {}
            
        is_editing = st.session_state.edit_mode.get(selected_portfolio, False)

# Quick copy button for current portfolio
if not is_editing and selected_portfolio:
    if st.sidebar.button(f"📋 Quick Copy '{selected_portfolio}'"):
        copy_id = f"{selected_portfolio}_Copy"
        counter = 1
        while copy_id in st.session_state.portfolios:
            copy_id = f"{selected_portfolio}_Copy_{counter}"
            counter += 1
        
        # Use portfolio manager for proper database integration and isolation
        success = st.session_state.portfolio_manager.copy_portfolio(
            selected_portfolio, copy_id, f"{current_portfolio['name']} - Copy",
            f"Copy of {current_portfolio['name']}"
        )
        
        if success:
            # Reload portfolios from database to get the updated data
            st.session_state.portfolios = st.session_state.portfolio_manager.get_all_portfolios()
            st.sidebar.success(f"✅ Quick copied to '{copy_id}' - Saved to database")
            st.rerun()
        else:
            st.sidebar.error("❌ Failed to quick copy portfolio to database")

# Edit Mode Controls (only for portfolio page)
if st.session_state.current_page == 'portfolio':
    st.sidebar.markdown("---")
    st.sidebar.subheader("✏️ Portfolio Editing")

    if not is_editing:
        if st.sidebar.button("📝 Edit Portfolio", type="primary"):
            # Check for portfolio analysis restrictions before entering edit mode
            has_analyses, analysis_count, message = check_portfolio_has_analyses(selected_portfolio)
            
            if has_analyses:
                # Show restriction warning
                st.sidebar.error(f"🚫 **Cannot edit portfolio**: {message}")
                st.sidebar.warning("⚠️ Updating portfolios that already have analyses is not allowed.")
                st.sidebar.info("💡 **Solution**: Copy this portfolio to a new one to proceed with analysis.")
                
                # Offer quick copy option
                if st.sidebar.button("📋 Copy Portfolio Now", type="secondary", help="Create a copy of this portfolio for editing"):
                    copy_id = f"{selected_portfolio}_Copy"
                    counter = 1
                    while copy_id in st.session_state.portfolios:
                        copy_id = f"{selected_portfolio}_Copy_{counter}"
                        counter += 1
                    
                    # Use portfolio manager for proper database integration
                    success = st.session_state.portfolio_manager.copy_portfolio(
                        selected_portfolio, copy_id, f"{current_portfolio['name']} - Copy",
                        f"Editable copy of {current_portfolio['name']} (original has {analysis_count} analyses)"
                    )
                    
                    if success:
                        # Reload portfolios and switch to the new copy in edit mode
                        st.session_state.portfolios = st.session_state.portfolio_manager.get_all_portfolios()
                        st.session_state.portfolio_switch_request = copy_id
                        st.session_state.edit_mode[copy_id] = True
                        st.session_state.portfolio_backup[copy_id] = copy.deepcopy(st.session_state.portfolios[copy_id])
                        st.sidebar.success(f"✅ Created editable copy: '{copy_id}'")
                        st.rerun()
                    else:
                        st.sidebar.error("❌ Failed to create portfolio copy")
            else:
                # No analyses - proceed with normal edit mode
                st.session_state.edit_mode[selected_portfolio] = True
                st.session_state.portfolio_backup[selected_portfolio] = copy.deepcopy(current_portfolio)
                st.rerun()
    else:
        st.sidebar.warning("🔄 Editing Mode Active")
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("💾 Save", type="primary"):
                # Check for pending changes and show warning
                has_changes = selected_portfolio in st.session_state.pending_changes and st.session_state.pending_changes[selected_portfolio]
                
                if has_changes:
                    st.sidebar.warning("⚠️ You have unsaved changes that will be applied!")
                    
                with st.sidebar.container():
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("💾 Applying changes...")
                    progress_bar.progress(25)
                    
                    # Apply pending changes to current portfolio data
                    if selected_portfolio in st.session_state.pending_changes:
                        for change in st.session_state.pending_changes[selected_portfolio]:
                            if change['action'] == 'update_position':
                                positions = st.session_state.portfolios[selected_portfolio]['positions']
                                for i, pos in enumerate(positions):
                                    if pos['symbol'] == change['data']['symbol']:
                                        positions[i] = change['data']
                                        break
                                else:
                                    positions.append(change['data'])
                            elif change['action'] == 'remove_position':
                                positions = st.session_state.portfolios[selected_portfolio]['positions']
                                st.session_state.portfolios[selected_portfolio]['positions'] = [
                                    pos for pos in positions if pos['symbol'] != change['symbol']
                                ]
                    
                    status_text.text("💿 Saving to database...")
                    progress_bar.progress(50)
                    
                    # Save to database
                    current_data = st.session_state.portfolios[selected_portfolio]
                    success = st.session_state.portfolio_manager.save_portfolio(selected_portfolio, current_data)
                    
                    progress_bar.progress(75)
                    
                    if success:
                        status_text.text("✅ Save successful!")
                        progress_bar.progress(100)
                        
                        # Clean up edit state
                        st.session_state.edit_mode[selected_portfolio] = False
                        if selected_portfolio in st.session_state.portfolio_backup:
                            del st.session_state.portfolio_backup[selected_portfolio]
                        if selected_portfolio in st.session_state.pending_changes:
                            del st.session_state.pending_changes[selected_portfolio]
                        
                        # Update timestamps
                        from datetime import datetime
                        st.session_state.portfolio_timestamps[selected_portfolio] = datetime.now()
                        st.session_state.last_update[selected_portfolio] = datetime.now()
                        
                        # Reload from database
                        st.session_state.portfolios = st.session_state.portfolio_manager.get_all_portfolios()
                        
                        # Store success status
                        st.session_state.last_save_status[selected_portfolio] = {
                            'status': 'success',
                            'message': 'Portfolio saved successfully!',
                            'timestamp': datetime.now()
                        }
                        
                        # Show success and clean up UI
                        time.sleep(1)
                        progress_bar.empty()
                        status_text.empty()
                        st.sidebar.success("✅ Portfolio saved successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        status_text.text("❌ Save failed!")
                        progress_bar.empty()
                        status_text.empty()
                        st.session_state.last_save_status[selected_portfolio] = {
                            'status': 'error',
                            'message': 'Failed to save portfolio to database!',
                            'timestamp': datetime.now()
                        }
                        st.sidebar.error("❌ Failed to save portfolio to database!")
        
        with col2:
            if st.button("❌ Cancel"):
                # Cancel changes - restore backup
                st.session_state.portfolios[selected_portfolio] = st.session_state.portfolio_backup[selected_portfolio]
                st.session_state.edit_mode[selected_portfolio] = False
                del st.session_state.portfolio_backup[selected_portfolio]
                st.sidebar.info("↩️ Changes cancelled")
                st.rerun()

# Copy Portfolio section (only if not editing and on portfolio page)
if st.session_state.current_page == 'portfolio' and not is_editing:
    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Copy Portfolio")
    
    copy_from = st.sidebar.selectbox(
        "Copy from:",
        options=list(st.session_state.portfolios.keys()),
        format_func=lambda x: f"{x} ({len([p for p in st.session_state.portfolios[x]['positions'] if p['quantity'] > 0])} positions)"
    )
    
    copy_to_id = st.sidebar.text_input("New Portfolio ID:", placeholder="e.g., HKEX_Base_Copy")
    copy_to_name = st.sidebar.text_input("New Portfolio Name:", placeholder="e.g., HKEX Base Copy")
    copy_to_desc = st.sidebar.text_area("New Description:", placeholder="Copy of existing portfolio...")
    
    if st.sidebar.button("📋 Copy Portfolio"):
        if copy_to_id and copy_to_name and copy_to_id not in st.session_state.portfolios:
            # Use portfolio manager for proper database integration and isolation
            success = st.session_state.portfolio_manager.copy_portfolio(
                copy_from, copy_to_id, copy_to_name, 
                copy_to_desc or f"Copy of {st.session_state.portfolios[copy_from]['name']}"
            )
            
            if success:
                # Reload portfolios from database to get the updated data
                st.session_state.portfolios = st.session_state.portfolio_manager.get_all_portfolios()
                positions_count = len(st.session_state.portfolios[copy_to_id]['positions'])
                st.sidebar.success(f"✅ Copied '{copy_from}' to '{copy_to_id}' ({positions_count} positions) - Saved to database")
                st.rerun()
            else:
                st.sidebar.error("❌ Failed to copy portfolio to database")
        else:
            st.sidebar.error("❌ Invalid portfolio ID or already exists")

    # Add New Portfolio section (only if not editing)
    st.sidebar.markdown("---")
    st.sidebar.subheader("➕ Create New Portfolio")
    
    new_portfolio_id = st.sidebar.text_input("Portfolio ID:", placeholder="e.g., US_Growth", key="new_port_id")
    new_portfolio_name = st.sidebar.text_input("Portfolio Name:", placeholder="e.g., US Growth Stocks", key="new_port_name")
    new_portfolio_desc = st.sidebar.text_area("Description:", placeholder="Portfolio description...", key="new_port_desc")
    
    if st.sidebar.button("➕ Create Empty Portfolio"):
        if new_portfolio_id and new_portfolio_name and new_portfolio_id not in st.session_state.portfolios:
            # Use portfolio manager to create portfolio in database
            success = st.session_state.portfolio_manager.create_portfolio(
                new_portfolio_id, new_portfolio_name, new_portfolio_desc
            )
            
            if success:
                # Reload portfolios from database
                st.session_state.portfolios = st.session_state.portfolio_manager.get_all_portfolios()
                st.sidebar.success(f"✅ Created portfolio '{new_portfolio_id}' - Saved to database")
                st.rerun()
            else:
                st.sidebar.error("❌ Failed to create portfolio in database")
        else:
            st.sidebar.error("❌ Portfolio ID required or already exists")

# Legacy session-only creation (fallback)
if False:  # Disabled - using database integration above
    if st.sidebar.button("➕ Create Empty Portfolio"):
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


# Breadcrumb Navigation Function
def generate_breadcrumbs():
    """Generate breadcrumb navigation based on current navigation state"""
    breadcrumbs = ["🏠 Home"]
    
    # Get current navigation state
    nav_state = st.session_state.navigation
    current_section = nav_state.get('section', 'portfolios')
    current_page = nav_state.get('page', 'overview')
    
    # Add section to breadcrumbs
    section_labels = {
        'portfolios': '📊 Portfolios',
        'strategy': '🎯 Strategy Analysis', 
        'system': '🔧 System & Admin'
    }
    
    if current_section in section_labels:
        breadcrumbs.append(section_labels[current_section])
    
    # Add current page context
    if current_section == 'portfolios':
        if current_page == 'overview':
            breadcrumbs.append('📋 All Portfolios')
        elif current_page == 'portfolio':
            breadcrumbs.append('📊 Portfolio View')
            # Add portfolio name if available
            portfolio_keys = list(st.session_state.portfolios.keys()) if st.session_state.portfolios else []
            if portfolio_keys and hasattr(st.session_state, 'selected_portfolio_for_pv'):
                selected = st.session_state.selected_portfolio_for_pv
                if selected in st.session_state.portfolios:
                    breadcrumbs.append(f"📂 {st.session_state.portfolios[selected]['name']}")
        elif current_page == 'pv_analysis':
            breadcrumbs.append('📈 Portfolio Analysis')
            # Add portfolio name if available
            selected_for_pv = st.session_state.get('selected_portfolio') or st.session_state.get('selected_portfolio_for_pv')
            if selected_for_pv and selected_for_pv in st.session_state.portfolios:
                breadcrumbs.append(f"📂 {st.session_state.portfolios[selected_for_pv]['name']}")
    elif current_section == 'strategy':
        if current_page == 'equity_analysis':
            breadcrumbs.append('📈 Equity Analysis')
        elif current_page == 'strategy_editor':
            breadcrumbs.append('⚙️ Strategy Editor')
    elif current_section == 'system':
        if current_page == 'system_status':
            breadcrumbs.append('⚙️ System Status')
    
    return breadcrumbs

# Display Breadcrumb Navigation
breadcrumbs = generate_breadcrumbs()
breadcrumb_text = " → ".join(breadcrumbs)
st.markdown(f"<div style='font-size: 14px; color: #8e8ea0; margin-bottom: 10px; padding: 5px 0;'>{breadcrumb_text}</div>", 
            unsafe_allow_html=True)

# Page routing based on current_page
if st.session_state.current_page == 'system':
    # SYSTEM STATUS PAGE
    st.title("⚙️ System Status Dashboard")
    st.markdown("---")
    
    # Run health checks
    if st.button("🔄 Refresh All Checks", type="primary"):
        st.rerun()
    
    st.markdown("### 🏥 System Health Checks")
    
    # Database check
    with st.container():
        st.subheader("🗄️ PostgreSQL Database")
        with st.spinner("Checking database connectivity..."):
            db_results = check_database_health()
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if db_results["status"]:
                st.success("✅ Healthy")
            else:
                st.error("❌ Unhealthy")
        with col2:
            st.write(f"**Status:** {db_results['message']}")
            if db_results["version"]:
                st.write(f"**Version:** {db_results['version']}")
        
        # Show detailed information
        if db_results["details"]:
            with st.expander("🔍 Database Details", expanded=not db_results["status"]):
                for detail in db_results["details"]:
                    st.text(detail)
        
        # Show troubleshooting if there are issues
        if db_results["troubleshooting"]:
            with st.expander("🛠️ Troubleshooting Steps", expanded=True):
                for step in db_results["troubleshooting"]:
                    st.text(f"• {step}")
                
                st.markdown("**Quick Setup Commands:**")
                st.code("""
# Create PostgreSQL user and database
sudo -u postgres psql
CREATE USER trader WITH PASSWORD 'YOUR_SECURE_PASSWORD';
CREATE DATABASE hk_strategy OWNER trader;
GRANT ALL PRIVILEGES ON DATABASE hk_strategy TO trader;
\\q

# Initialize database (replace YOUR_SECURE_PASSWORD)
PGPASSWORD=YOUR_SECURE_PASSWORD psql -U trader -h localhost -d hk_strategy -f init.sql
                """, language="bash")
                st.warning("⚠️ Replace 'YOUR_SECURE_PASSWORD' with your actual secure password. Use the ./setup_security.sh script for automated setup.")
    
    # Redis check
    with st.container():
        st.subheader("🔄 Redis Cache")
        with st.spinner("Checking Redis connectivity..."):
            redis_results = check_redis_health()
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if redis_results["status"]:
                st.success("✅ Healthy")
            else:
                st.error("❌ Unhealthy")
        with col2:
            st.write(f"**Status:** {redis_results['message']}")
            if redis_results["info"]:
                st.write(f"**Info:** {redis_results['info']}")
        
        # Show detailed information
        if redis_results["details"]:
            with st.expander("🔍 Redis Details", expanded=not redis_results["status"]):
                for detail in redis_results["details"]:
                    st.text(detail)
        
        # Show troubleshooting if there are issues
        if redis_results["troubleshooting"]:
            with st.expander("🛠️ Redis Troubleshooting", expanded=True):
                for step in redis_results["troubleshooting"]:
                    st.text(f"• {step}")
                
                st.markdown("**Redis Setup Commands:**")
                st.code("""
# Install Redis (Ubuntu/Debian)
sudo apt update
sudo apt install redis-server

# Start Redis
sudo systemctl start redis
sudo systemctl enable redis

# Test Redis
redis-cli ping
                """, language="bash")
    
    # Yahoo Finance check
    with st.container():
        st.subheader("📈 Yahoo Finance API")
        with st.spinner("Checking Yahoo Finance API..."):
            yf_results = check_yfinance_health()
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if yf_results["status"]:
                st.success("✅ Healthy")
            else:
                st.error("❌ Unhealthy")
        with col2:
            st.write(f"**Status:** {yf_results['message']}")
            if yf_results["test_data"]:
                st.write(f"**Test:** {yf_results['test_data']}")
        
        # Show detailed information
        if yf_results["details"]:
            with st.expander("🔍 Yahoo Finance Details", expanded=not yf_results["status"]):
                for detail in yf_results["details"]:
                    st.text(detail)
        
        # Show troubleshooting if there are issues
        if yf_results["troubleshooting"]:
            with st.expander("🛠️ Yahoo Finance Troubleshooting", expanded=True):
                for step in yf_results["troubleshooting"]:
                    st.text(f"• {step}")
                
                st.markdown("**Network Diagnostics:**")
                st.code("""
# Test internet connectivity
ping -c 3 finance.yahoo.com

# Check DNS resolution
nslookup finance.yahoo.com

# Test HTTPS access
curl -I https://finance.yahoo.com
                """, language="bash")
    
    st.markdown("---")
    
    # System Information
    st.markdown("### 💻 System Information")
    system_info = get_system_info()
    
    info_cols = st.columns(2)
    items = list(system_info.items())
    mid_point = len(items) // 2
    
    with info_cols[0]:
        for key, value in items[:mid_point]:
            st.write(f"**{key}:** {value}")
    
    with info_cols[1]:
        for key, value in items[mid_point:]:
            st.write(f"**{key}:** {value}")
    
    # Portfolio Statistics
    st.markdown("---")
    st.markdown("### 📊 Portfolio Statistics")
    
    total_portfolios = len(st.session_state.portfolios)
    total_positions = sum(len(p['positions']) for p in st.session_state.portfolios.values())
    active_positions = sum(len([pos for pos in p['positions'] if pos['quantity'] > 0]) for p in st.session_state.portfolios.values())
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Portfolios", total_portfolios, help="Number of portfolios in your system")
    with col2:
        st.metric("Total Positions", total_positions, help="Number of unique stock symbols across all portfolios (no duplicates)")
    with col3:
        st.metric("Active Positions", active_positions, help="Number of unique symbols with quantity > 0 across all portfolios")
    with col4:
        st.metric("Cached Prices", len(st.session_state.portfolio_prices), help="Number of portfolios with cached price data")
    
    # Recent Activity
    st.markdown("---")
    st.markdown("### 🕒 Recent Activity")
    
    if st.session_state.last_update:
        for portfolio_id, timestamp in st.session_state.last_update.items():
            st.write(f"**{portfolio_id}:** Last price update at {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.info("No recent price updates")
    
    st.stop()

# PAGE ROUTING LOGIC
if st.session_state.current_page == 'system':
    # System Status Page (existing system check content would go here)
    st.subheader("⚙️ System Status Dashboard")
    # System status content is later in the file

elif st.session_state.current_page == 'pv_analysis':
    # Portfolio Analysis Dashboard
    st.subheader("📈 Portfolio Analysis Dashboard")
    
    # Initialize Portfolio Analysis Manager
    if 'portfolio_analysis_manager' not in st.session_state:
        from portfolio_analysis_manager import PortfolioAnalysisManager
        st.session_state.portfolio_analysis_manager = PortfolioAnalysisManager(st.session_state.db_manager)
    
    # Check if portfolio is selected (either from regular selection or from Advanced button)
    selected_portfolio = st.session_state.get('selected_portfolio') or st.session_state.get('selected_portfolio_for_pv')
    
    # If coming from Advanced Portfolio Analysis button, set the regular selected_portfolio too
    if st.session_state.get('selected_portfolio_for_pv') and not st.session_state.get('selected_portfolio'):
        st.session_state.selected_portfolio = st.session_state.selected_portfolio_for_pv
        selected_portfolio = st.session_state.selected_portfolio_for_pv
        # Clear modal states when switching portfolios
        clear_modal_states()
    
    # Check if portfolio changed and clear modal states
    if 'previous_selected_portfolio' in st.session_state and st.session_state.previous_selected_portfolio != selected_portfolio:
        clear_modal_states()
    st.session_state.previous_selected_portfolio = selected_portfolio
    
    if not selected_portfolio:
        # Show "Load Portfolio" page
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
                st.session_state.current_page = 'overview'
                st.rerun()
        st.stop()
    
    # Portfolio is selected - show analysis interface
    current_portfolio = st.session_state.portfolios[selected_portfolio]
    
    # Header with portfolio name and action buttons
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"### Portfolio Analysis: **{current_portfolio['name']}**")
    with col2:
        if st.button("📈 Update Market Prices", help="Refresh all analyses with current market prices"):
            with st.spinner("Updating market prices..."):
                success, message, count = st.session_state.portfolio_analysis_manager.refresh_all_analyses_for_portfolio(selected_portfolio)
                if success:
                    st.success(f"✅ {message}")
                    # Clear price cache to force fresh data
                    if 'price_data_cache' in st.session_state:
                        st.session_state.price_data_cache.clear()
                        st.session_state.cache_expiry.clear()
                else:
                    st.error(f"❌ {message}")
                st.rerun()
    with col3:
        if st.button("➕ Create New Analysis", type="primary"):
            st.session_state.show_create_analysis_dialog = True
            st.rerun()
    
    # Create New Analysis Dialog
    if st.session_state.get('show_create_analysis_dialog', False):
        with st.container():
            st.markdown("---")
            st.markdown("### ➕ Create New Portfolio Analysis")
            
            # Show which portfolio this analysis will be created for
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
            
            # Validation and buttons
            error_msg = ""
            if not analysis_name.strip():
                error_msg = "Analysis name is required"
            elif end_date <= start_date:
                error_msg = "End date must be after start date"
            elif not st.session_state.portfolio_analysis_manager.validate_analysis_name(selected_portfolio, analysis_name.strip()):
                error_msg = f"Analysis name '{analysis_name.strip()}' already exists for this portfolio"
            
            if error_msg:
                st.error(f"❌ {error_msg}")
            
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.button("💾 Save", disabled=bool(error_msg), type="primary", use_container_width=True):
                    success, message, analysis_id = st.session_state.portfolio_analysis_manager.create_analysis(
                        portfolio_id=selected_portfolio,
                        analysis_name=analysis_name.strip(),
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
            
            with col_cancel:
                if st.button("❌ Cancel", use_container_width=True):
                    st.session_state.show_create_analysis_dialog = False
                    st.rerun()
            
            st.markdown("---")
    
    # Portfolio Analysis Table
    st.markdown("### 📊 Portfolio Analyses")
    
    # Get analyses for this portfolio
    analyses_df = st.session_state.portfolio_analysis_manager.get_analysis_summary(selected_portfolio)
    
    if analyses_df.empty:
        st.info("No portfolio analyses found. Create your first analysis using the button above.")
    else:
        # Initialize comparison state
        if 'selected_for_compare' not in st.session_state:
            st.session_state.selected_for_compare = []
        
        # Custom table layout with simplified columns
        st.markdown("#### Analysis Summary")
        
        # Table header - Updated layout with Detail and Transaction buttons
        header_col1, header_col2, header_col3, header_col4, header_col5, header_col6, header_col7, header_col8 = st.columns([0.8, 2.5, 1.2, 1.2, 1.2, 1.0, 1.0, 1])
        with header_col1:
            st.markdown("**Compare**")
        with header_col2:
            st.markdown("**Name**")
        with header_col3:
            st.markdown("**Start Date**")
        with header_col4:
            st.markdown("**End Date**")
        with header_col5:
            st.markdown("**Start Cash**")
        with header_col6:
            st.markdown("**Detail**")
        with header_col7:
            st.markdown("**Transaction**")
        with header_col8:
            st.markdown("**Delete**")
        
        st.markdown("---")
        
        # Initialize delete confirmation state
        if 'delete_confirm_id' not in st.session_state:
            st.session_state.delete_confirm_id = None
        
        # Initialize modal states
        if 'show_detail_modal' not in st.session_state:
            st.session_state.show_detail_modal = None
        if 'show_transaction_modal' not in st.session_state:
            st.session_state.show_transaction_modal = None
        
        # Table rows
        for idx, row in analyses_df.iterrows():
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([0.8, 2.5, 1.2, 1.2, 1.2, 1.0, 1.0, 1])
            
            with col1:
                # Compare checkbox
                compare_key = f"compare_{row['id']}"
                is_selected = st.checkbox("", key=compare_key, value=row['id'] in st.session_state.selected_for_compare)
                
                # Update selected list
                if is_selected and row['id'] not in st.session_state.selected_for_compare:
                    st.session_state.selected_for_compare.append(row['id'])
                elif not is_selected and row['id'] in st.session_state.selected_for_compare:
                    st.session_state.selected_for_compare.remove(row['id'])
            
            with col2:
                st.markdown(f"**{row['name']}**")
            
            with col3:
                start_date_str = row['start_date'].strftime("%Y-%m-%d") if pd.notna(row['start_date']) else "-"
                st.write(start_date_str)
            
            with col4:
                end_date_str = row['end_date'].strftime("%Y-%m-%d") if pd.notna(row['end_date']) else "-"
                st.write(end_date_str)
            
            with col5:
                start_cash_str = f"${row['start_cash']:,.0f}" if pd.notna(row['start_cash']) else "-"
                st.write(start_cash_str)
            
            with col6:
                # Detail button
                if st.button("📊", key=f"detail_{row['id']}", help=f"View details for {row['name']}"):
                    st.session_state.show_detail_modal = row['id']
                    st.rerun()
            
            with col7:
                # Transaction button  
                if st.button("📝", key=f"transaction_{row['id']}", help=f"View transactions for {row['name']}"):
                    st.session_state.show_transaction_modal = row['id']
                    st.rerun()
            
            with col8:
                # Delete button with confirmation
                if st.session_state.delete_confirm_id == row['id']:
                    # Show confirmation buttons
                    subcol1, subcol2 = st.columns(2)
                    with subcol1:
                        if st.button("✅", key=f"confirm_delete_{row['id']}", help="Confirm delete"):
                            success, message = st.session_state.portfolio_analysis_manager.delete_analysis(row['id'])
                            if success:
                                st.success(f"✅ {message}")
                                st.session_state.delete_confirm_id = None
                                if row['id'] in st.session_state.selected_for_compare:
                                    st.session_state.selected_for_compare.remove(row['id'])
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
                    with subcol2:
                        if st.button("❌", key=f"cancel_delete_{row['id']}", help="Cancel"):
                            st.session_state.delete_confirm_id = None
                            st.rerun()
                else:
                    # Show delete button
                    if st.button("🗑️", key=f"delete_{row['id']}", help=f"Delete '{row['name']}'"):
                        st.session_state.delete_confirm_id = row['id']
                        st.rerun()
            
            # Add a subtle separator
            st.markdown('<hr style="margin:5px 0; border:0.5px solid #e0e0e0">', unsafe_allow_html=True)
        
        # Detail Modal
        if st.session_state.show_detail_modal:
            detail_matches = analyses_df[analyses_df['id'] == st.session_state.show_detail_modal]
            if detail_matches.empty:
                # Analysis not found in current portfolio - clear modal state
                st.session_state.show_detail_modal = None
                st.rerun()
            else:
                detail_analysis = detail_matches.iloc[0]
            
            with st.container():
                st.markdown("---")
                col1, col2, col3 = st.columns([1, 3, 1])
                with col2:
                    st.markdown(f"### 📊 Analysis Details: {detail_analysis['name']}")
                    
                    # Financial Summary
                    st.markdown("#### 💰 Financial Summary")
                    fin_col1, fin_col2 = st.columns(2)
                    
                    with fin_col1:
                        st.metric("Start Cash", f"${detail_analysis['start_cash']:,.2f}")
                        st.metric("Start Equity", f"${detail_analysis['start_equity_value']:,.2f}")
                        st.metric("Start Total", f"${detail_analysis['start_total_value']:,.2f}")
                    
                    with fin_col2:
                        st.metric("End Cash", f"${detail_analysis['end_cash']:,.2f}")
                        st.metric("End Equity", f"${detail_analysis['end_equity_value']:,.2f}", 
                                 delta=f"{detail_analysis['total_equity_gain_loss']:,.2f}")
                        st.metric("End Total", f"${detail_analysis['end_total_value']:,.2f}",
                                 delta=f"{detail_analysis['total_value_gain_loss']:,.2f}")
                    
                    # Performance Metrics
                    st.markdown("#### 📈 Performance Metrics")
                    perf_col1, perf_col2, perf_col3 = st.columns(3)
                    
                    with perf_col1:
                        total_return_pct = (detail_analysis['total_value_gain_loss'] / detail_analysis['start_total_value'] * 100) if detail_analysis['start_total_value'] > 0 else 0
                        st.metric("Total Return", f"{total_return_pct:.2f}%")
                    
                    with perf_col2:
                        equity_return_pct = (detail_analysis['total_equity_gain_loss'] / detail_analysis['start_equity_value'] * 100) if detail_analysis['start_equity_value'] > 0 else 0
                        st.metric("Equity Return", f"{equity_return_pct:.2f}%")
                    
                    with perf_col3:
                        analysis_days = (detail_analysis['end_date'] - detail_analysis['start_date']).days
                        st.metric("Analysis Period", f"{analysis_days} days")
                    
                    # Position Details
                    st.markdown("#### 🏢 Position Details")
                    positions_df = st.session_state.portfolio_analysis_manager.get_current_positions(detail_analysis['id'])
                    
                    if not positions_df.empty:
                        # Format the positions for display
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
                        
                        st.dataframe(pd.DataFrame(display_positions), use_container_width=True, hide_index=True)
                    else:
                        st.info("No position data available for this analysis")
                    
                    # Close button
                    if st.button("✖️ Close", key="close_detail_modal"):
                        st.session_state.show_detail_modal = None
                        st.rerun()
                
                st.markdown("---")
        
        # Transaction Modal
        if st.session_state.show_transaction_modal:
            trans_matches = analyses_df[analyses_df['id'] == st.session_state.show_transaction_modal]
            if trans_matches.empty:
                # Analysis not found in current portfolio - clear modal state
                st.session_state.show_transaction_modal = None
                st.rerun()
            else:
                trans_analysis = trans_matches.iloc[0]
            
            with st.container():
                st.markdown("---")
                col1, col2, col3 = st.columns([1, 3, 1])
                with col2:
                    st.markdown(f"### 📝 Transaction History: {trans_analysis['name']}")
                    
                    # Get transactions for this analysis
                    transactions_df = st.session_state.portfolio_analysis_manager.get_analysis_transactions(st.session_state.show_transaction_modal)
                    
                    if not transactions_df.empty:
                        # Format transactions for better display
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
                        
                        st.dataframe(pd.DataFrame(display_transactions), use_container_width=True, hide_index=True)
                    else:
                        st.info("No transactions found for this analysis")
                    
                    # Close button
                    if st.button("✖️ Close", key="close_transaction_modal"):
                        st.session_state.show_transaction_modal = None
                        st.rerun()
                
                st.markdown("---")
        
        # Analysis Actions Section (simplified since transactions are now in modals)
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh Table"):
                st.rerun()
        with col2:
            st.info("💡 Use Detail and Transaction buttons in the table above")
        
        # Comparison Chart Section
        if st.session_state.selected_for_compare:
            st.markdown("---")
            st.markdown(f"### 📈 Portfolio Performance Comparison ({len(st.session_state.selected_for_compare)} analyses)")
            
            # Initialize price data cache for better performance
            if 'price_data_cache' not in st.session_state:
                st.session_state.price_data_cache = {}
                st.session_state.cache_expiry = {}
            
            # Get timeline data for selected analyses with caching
            cache_key = f"timeline_{sorted(st.session_state.selected_for_compare)}"
            current_time = time.time()
            cache_duration = 300  # 5 minutes cache
            
            # Check if we have cached data that's still valid
            if (cache_key in st.session_state.price_data_cache and 
                cache_key in st.session_state.cache_expiry and
                current_time - st.session_state.cache_expiry[cache_key] < cache_duration):
                
                timeline_df = st.session_state.price_data_cache[cache_key]
                st.info("📊 Using cached data for faster display")
            else:
                # Fetch fresh data and cache it
                with st.spinner("📈 Fetching real-time market data..."):
                    timeline_df = st.session_state.portfolio_analysis_manager.get_analysis_timeline_data(st.session_state.selected_for_compare)
                    
                    # Cache the results
                    st.session_state.price_data_cache[cache_key] = timeline_df
                    st.session_state.cache_expiry[cache_key] = current_time
                    
                    if not timeline_df.empty:
                        st.success("✅ Market data fetched successfully")
            
            if not timeline_df.empty:
                # Create comparison chart
                fig = go.Figure()
                
                # Add trace for each analysis
                for analysis_id in st.session_state.selected_for_compare:
                    analysis_data = timeline_df[timeline_df['analysis_id'] == analysis_id]
                    if not analysis_data.empty:
                        analysis_name = analysis_data.iloc[0]['analysis_name']
                        
                        # Create hover text with detailed information
                        hover_text = []
                        for _, point in analysis_data.iterrows():
                            hover_info = f"<b>{analysis_name}</b><br>"
                            hover_info += f"Date: {point['date'].strftime('%Y-%m-%d')}<br>"
                            hover_info += f"Total Value: ${point['total_value']:,.2f}<br>"
                            hover_info += f"Cash: ${point['cash_position']:,.2f}<br>"
                            hover_info += f"Equity: ${point['equity_value']:,.2f}"
                            if point['transaction_details']:
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
                
                # Format y-axis as currency
                fig.update_layout(yaxis=dict(tickformat='$,.0f'))
                
                # Display chart
                st.plotly_chart(fig, use_container_width=True)
                
                # Portfolio Analysis Summary - Interactive equity analysis
                st.markdown("---")
                st.markdown("### 📈 Portfolio Analysis Summary")
                
                # Initialize selected analysis and date
                if 'selected_analysis_date' not in st.session_state:
                    st.session_state.selected_analysis_date = None
                if 'selected_analysis_id' not in st.session_state:
                    st.session_state.selected_analysis_id = None
                
                # Analysis and Date Selection
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    # Select analysis for detailed view
                    analysis_options = [(row['id'], row['name']) for _, row in analyses_df.iterrows() if row['id'] in st.session_state.selected_for_compare]
                    if analysis_options:
                        selected_option = st.selectbox(
                            "Select Analysis for Details:",
                            options=analysis_options,
                            format_func=lambda x: x[1],
                            key="analysis_detail_selector"
                        )
                        st.session_state.selected_analysis_id = selected_option[0] if selected_option else None
                
                with col2:
                    # Select date within analysis period
                    if st.session_state.selected_analysis_id:
                        analysis_matches = analyses_df[analyses_df['id'] == st.session_state.selected_analysis_id]
                        if analysis_matches.empty:
                            # Analysis not found in current portfolio - clear selection
                            st.session_state.selected_analysis_id = None
                            st.warning("Selected analysis not found in current portfolio. Please select a different analysis.")
                        else:
                            selected_analysis = analysis_matches.iloc[0]
                            start_date = selected_analysis['start_date']
                            end_date = selected_analysis['end_date']
                            
                            selected_date = st.date_input(
                                "📅 Choose Date for Portfolio Analysis:",
                                value=end_date,
                                min_value=start_date,
                                max_value=end_date,
                                key="analysis_date_selector",
                                help="Select any date within the analysis period. Non-trading days will automatically use the previous trading day's data."
                            )
                            
                            # Validate trading day and show feedback
                            if selected_date:
                                effective_date, date_reason = st.session_state.portfolio_analysis_manager.get_effective_trading_date(
                                    selected_date, st.session_state.selected_analysis_id
                                )
                                
                                # Show date validation feedback
                                if effective_date != selected_date:
                                    st.info(f"📊 **Trading Day Adjustment**: {date_reason}")
                                    st.info(f"🗓️ **Effective Analysis Date**: {effective_date.strftime('%A, %B %d, %Y')}")
                                else:
                                    st.success(f"✅ **{date_reason}**: {effective_date.strftime('%A, %B %d, %Y')}")
                                
                                st.session_state.selected_analysis_date = selected_date
                                st.session_state.effective_analysis_date = effective_date
                
                with col3:
                    # Add analyze button for selected date
                    if st.session_state.get('selected_analysis_date') and st.session_state.get('selected_analysis_id'):
                        if st.button("📊 Analyze Portfolio", type="primary", use_container_width=True):
                            # Store the analysis state for the selected date
                            portfolio_state = st.session_state.portfolio_analysis_manager.get_portfolio_state_at_date(
                                st.session_state.selected_analysis_id,
                                st.session_state.selected_analysis_date
                            )
                            st.session_state.portfolio_state_analysis = portfolio_state
                            st.success(f"✅ Portfolio analyzed for {portfolio_state['effective_date']}")
                            st.rerun()
                    
                    # Refresh chart button
                    if st.button("🔄 Refresh Chart"):
                        if 'price_data_cache' in st.session_state:
                            st.session_state.price_data_cache.clear()
                            st.session_state.cache_expiry.clear()
                        st.rerun()
                
                # Show portfolio analysis results
                if st.session_state.get('portfolio_state_analysis'):
                    portfolio_state = st.session_state.portfolio_state_analysis
                    effective_date = portfolio_state['effective_date']
                    selected_analysis = analyses_df[analyses_df['id'] == st.session_state.selected_analysis_id].iloc[0]
                    
                    st.markdown(f"#### 📊 Portfolio State Analysis - {selected_analysis['name']} ({effective_date})")
                    
                    # Show portfolio summary
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("💰 Total Portfolio Value", f"HK${portfolio_state['total_portfolio_value']:,.2f}")
                    with col2:
                        st.metric("📈 Market Value", f"HK${portfolio_state['total_market_value']:,.2f}")
                    with col3:
                        st.metric("💵 Cash Position", f"HK${portfolio_state['cash_position']:,.2f}")
                    with col4:
                        st.metric("📋 Active Positions", portfolio_state['position_count'])
                    
                    # Show date adjustment info if applicable
                    if portfolio_state['target_date'] != portfolio_state['effective_date']:
                        st.info(f"📅 **{portfolio_state['date_reason']}**: Analysis conducted for {effective_date.strftime('%A, %B %d, %Y')}")
                    
                    # Display positions table
                    positions = portfolio_state['positions']
                    if positions:
                        st.markdown("##### 🏢 Individual Holdings")
                        
                        # Create custom table layout for positions
                        header_cols = st.columns([1, 3, 1.2, 1.2, 1.2, 1.5, 1.5, 1])
                        headers = ['Symbol', 'Company', 'Qty', 'Avg Cost', 'Current', 'Market Value', 'P&L', 'Detail']
                        for i, (col, header) in enumerate(zip(header_cols, headers)):
                            with col:
                                st.markdown(f"**{header}**")
                        
                        # Display each position
                        for position in positions:
                            row_cols = st.columns([1, 3, 1.2, 1.2, 1.2, 1.5, 1.5, 1])
                            
                            with row_cols[0]:
                                st.text(position['symbol'])
                            
                            with row_cols[1]:
                                company_name = position['company_name'] or "N/A"
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
                    else:
                        st.info("💼 Portfolio had no active positions on the selected date")
                
                # Fallback: Show standard equity analysis for selected analysis and date
                elif st.session_state.selected_analysis_id and st.session_state.selected_analysis_date:
                    selected_analysis = analyses_df[analyses_df['id'] == st.session_state.selected_analysis_id].iloc[0]
                    st.markdown(f"#### 🏢 Equity Analysis - {selected_analysis['name']} ({st.session_state.selected_analysis_date})")
                    st.info("📊 **Click 'Analyze Portfolio' button above to see the portfolio state for the selected date**")
                    
                
                # Technical Analysis Modal (shared between portfolio state analysis and fallback)
                if st.session_state.get('show_technical_modal'):
                    symbol = st.session_state.show_technical_modal
                    
                    with st.container():
                        st.markdown("---")
                        col1, col2, col3 = st.columns([1, 3, 1])
                        with col2:
                            st.markdown(f"### 📊 Technical Analysis: {symbol}")
                            
                            # Fetch real technical data from database
                            tech_data = fetch_technical_analysis_data(symbol)
                            tech_col1, tech_col2, tech_col3 = st.columns(3)
                            
                            with tech_col1:
                                st.metric("Day High", f"${tech_data['day_high']:.2f}" if tech_data['day_high'] else "N/A")
                                st.metric("Day Low", f"${tech_data['day_low']:.2f}" if tech_data['day_low'] else "N/A")
                                st.metric("52-Week High", f"${tech_data['week_52_high']:.2f}" if tech_data['week_52_high'] else "N/A")
                                st.metric("52-Week Low", f"${tech_data['week_52_low']:.2f}" if tech_data['week_52_low'] else "N/A")
                            
                            with tech_col2:
                                st.metric("RSI (14)", f"{tech_data['rsi_14']:.1f}" if tech_data['rsi_14'] else "N/A")
                                st.metric("RSI (9)", f"{tech_data['rsi_9']:.1f}" if tech_data['rsi_9'] else "N/A")
                                st.metric("Volume", f"{tech_data['volume']:,}" if tech_data['volume'] else "N/A")
                                st.metric("Volume Ratio", f"{tech_data['volume_ratio']:.2f}" if tech_data['volume_ratio'] else "N/A")
                            
                            with tech_col3:
                                st.metric("EMA 12", f"${tech_data['ema_12']:.2f}" if tech_data['ema_12'] else "N/A")
                                st.metric("EMA 26", f"${tech_data['ema_26']:.2f}" if tech_data['ema_26'] else "N/A")
                                st.metric("SMA 50", f"${tech_data['sma_50']:.2f}" if tech_data['sma_50'] else "N/A")
                                st.metric("SMA 200", f"${tech_data['sma_200']:.2f}" if tech_data['sma_200'] else "N/A")
                            
                            # Action buttons
                            close_col1, close_col2 = st.columns([1, 1])
                            with close_col1:
                                if st.button("❌ Close", key="close_modal"):
                                    st.session_state.show_technical_modal = None
                                    st.rerun()
                            with close_col2:
                                if st.button("📈 View Full Chart", key="view_chart"):
                                    # Prepare equity context for navigation
                                    if st.session_state.selected_analysis_id:
                                        analysis_info = analyses_df[analyses_df['id'] == st.session_state.selected_analysis_id].iloc[0]
                                        st.session_state.equity_context = {
                                            'symbol': symbol,
                                            'company_name': tech_data.get('company_name', symbol),
                                            'portfolio_name': selected_portfolio,
                                            'portfolio_analysis_name': analysis_info['name'],
                                            'start_date': str(analysis_info['start_date']),
                                            'end_date': str(analysis_info['end_date'])
                                        }
                                        st.session_state.current_page = 'equity_analysis'
                                        # Update navigation state for correct breadcrumbs
                                        st.session_state.navigation['section'] = 'strategy'
                                        st.session_state.navigation['page'] = 'equity_analysis'
                                        st.rerun()
                            
                            st.markdown("---")
                
                else:
                    st.info("💡 Select an analysis and date above to view detailed portfolio analysis")
                
                # Clear selections button
                if st.button("❌ Clear All Chart Selections"):
                    st.session_state.selected_for_compare = []
                    st.rerun()
            else:
                st.warning("No data available for selected analyses")
elif st.session_state.current_page == 'equity_analysis':
    # Equity Strategy Analysis Dashboard - with compact styling
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
    
    # Debug toggle for troubleshooting
    debug_col1, debug_col2 = st.columns([4, 1])
    with debug_col2:
        debug_mode = st.checkbox("🔍 Debug Mode", help="Enable debug information for troubleshooting equity population")
        st.session_state.debug_mode = debug_mode
    
    # Independent selection interface
    # Get all portfolios for selection
    portfolios = get_all_portfolios_for_equity_analysis()
    
    # Initialize selection state - simplified (no analysis selection needed)
    if 'equity_portfolio_id' not in st.session_state:
        st.session_state.equity_portfolio_id = None
    if 'equity_symbol' not in st.session_state:
        st.session_state.equity_symbol = None
    
    # Check if we came from portfolio analysis or overview navigation
    if 'equity_context' in st.session_state:
        equity_ctx = st.session_state.equity_context
        # Pre-populate selections from context
        for p in portfolios:
            if p['name'] == equity_ctx.get('portfolio_name'):
                st.session_state.equity_portfolio_id = p['portfolio_id']
                break
    
    # Handle navigation from All Portfolio Overview → stock selection
    # This handles the case where user clicks on a stock from the portfolio table
    if not st.session_state.equity_portfolio_id and 'selected_stock_context' in st.session_state:
        # Set default to "All Portfolio Overview" when coming from stock selection
        st.session_state.equity_portfolio_id = 'all_overview'
        stock_ctx = st.session_state.selected_stock_context
        st.session_state.equity_symbol = stock_ctx.get('symbol')
        
    # Initialize date selection state with 12-month default
    from datetime import datetime, timedelta
    if 'equity_start_date' not in st.session_state:
        st.session_state.equity_start_date = datetime.now().date() - timedelta(days=365)  # 12 months ago
    if 'equity_end_date' not in st.session_state:
        st.session_state.equity_end_date = datetime.now().date()
    
    # Date Selection Panel
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
        st.markdown("<br>", unsafe_allow_html=True)  # Align button
        if st.button("📅 Reset to 12M", help="Reset to 12 months ago"):
            st.session_state.equity_start_date = datetime.now().date() - timedelta(days=365)
            st.session_state.equity_end_date = datetime.now().date()
            st.rerun()
    
    st.markdown("---")
    
    # Selection Method Choice
    st.markdown("#### 📊 Analysis Method")
    selection_method = st.radio(
        "Choose how to select equity for analysis:",
        ["Portfolio-based Selection", "Direct Symbol Entry"],
        index=0,
        horizontal=True,
        help="Portfolio-based: Select from existing portfolio holdings. Direct: Select from all known securities."
    )
    
    # Initialize variables to prevent NameError
    go_clicked = False
    can_proceed = False
    
    if selection_method == "Direct Symbol Entry":
        # Direct symbol selection from all available securities
        st.markdown("**Direct Symbol Analysis** - Select from all known securities in portfolios")
        
        # Get all unique securities from all portfolios (active and inactive)
        all_securities = get_equities_from_portfolio('all_overview')
        
        if all_securities:
            direct_col1, direct_go = st.columns([5, 1])
            
            with direct_col1:
                # Create dropdown options in "SYMBOL - Company Name" format
                security_options = []
                for security in all_securities:
                    company_name = security['company_name']
                    if len(company_name) > 30:
                        company_name = company_name[:27] + "..."
                    security_options.append(f"{security['symbol']} - {company_name}")
                
                # Find current selection index if symbol is pre-selected
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
                    # Find the corresponding security info
                    selected_security_info = next(s for s in all_securities if s['symbol'] == selected_symbol)
                    st.session_state.direct_security_info = selected_security_info
            
            with direct_go:
                st.markdown("<br>", unsafe_allow_html=True)
                can_proceed = bool(st.session_state.get('direct_selected_security'))
                go_clicked = st.button("🚀 Analyze", type="primary", disabled=not can_proceed)
        else:
            st.warning("⚠️ No securities found in any portfolios. Please create portfolios with positions first.")
            can_proceed = False
            go_clicked = False
        
        if go_clicked and can_proceed:
            # Set up direct analysis context
            st.session_state.equity_portfolio_id = "direct_analysis"
            st.session_state.equity_symbol = st.session_state.direct_selected_security
            
            # Fetch data directly
            start_date_str = st.session_state.equity_start_date.strftime('%Y-%m-%d')
            end_date_str = st.session_state.equity_end_date.strftime('%Y-%m-%d')
            
            data_fetched = fetch_and_store_yahoo_data(
                st.session_state.direct_selected_security,
                start_date_str,
                end_date_str
            )
            
            if data_fetched:
                # Create simplified context for direct analysis using selected security info
                selected_info = st.session_state.direct_security_info
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
    
    else:
        # Original portfolio-based selection
        st.markdown("**Portfolio-based Selection** - Choose from existing portfolio holdings")
        # Selection interface - optimized layout for better text display
        select_col1, select_col2, go_col = st.columns([4, 5, 1])
        
        with select_col1:
            # Truncate long portfolio names for better display
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
                    st.session_state.equity_symbol = None  # Reset equity selection
                    
                st.session_state.equity_portfolio_id = selected_portfolio_id
    
        with select_col2:
            if st.session_state.equity_portfolio_id:
                equities = get_equities_from_portfolio(st.session_state.equity_portfolio_id)
                
                if equities:
                    # Truncate long company names for better display
                    equity_options = []
                    for e in equities:
                        company_name = e['company_name']
                        if len(company_name) > 25:
                            company_name = company_name[:22] + "..."
                        equity_options.append(f"{e['symbol']} - {company_name}")
                
                    # Show count of available equities
                    portfolio_name = next(p['name'] for p in portfolios if p['portfolio_id'] == st.session_state.equity_portfolio_id)
                    
                    # Find current selection index if symbol is pre-selected
                    current_index = 0
                    if st.session_state.equity_symbol:
                        for i, option in enumerate(equity_options):
                            if option.startswith(st.session_state.equity_symbol):
                                current_index = i
                                break
                    
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
            st.markdown("<br>", unsafe_allow_html=True)  # Align button with selectboxes
            # Enable "Go" button if portfolio and equity are selected
            can_proceed = bool(st.session_state.equity_portfolio_id and st.session_state.equity_symbol)
            go_clicked = st.button("🚀 Go", type="primary", disabled=not can_proceed)
    
    # Process analysis when Go is clicked or update existing analysis (portfolio-based only)
    if go_clicked and can_proceed and st.session_state.equity_portfolio_id != "direct_analysis":
        # Get selected portfolio and equity info
        selected_portfolio = next(p for p in portfolios if p['portfolio_id'] == st.session_state.equity_portfolio_id)
        selected_equity = next(e for e in get_equities_from_portfolio(st.session_state.equity_portfolio_id) 
                             if e['symbol'] == st.session_state.equity_symbol)
        
        # Always use custom date range from date pickers
        start_date_str = st.session_state.equity_start_date.strftime('%Y-%m-%d')
        end_date_str = st.session_state.equity_end_date.strftime('%Y-%m-%d')
        analysis_name = "Custom Date Range"
        
        # Fetch and ensure data availability from Yahoo Finance
        data_fetched = fetch_and_store_yahoo_data(
            st.session_state.equity_symbol,
            start_date_str,
            end_date_str
        )
        
        if data_fetched:
            equity_ctx = {
                'portfolio_id': st.session_state.equity_portfolio_id,
                'portfolio_name': selected_portfolio['name'],
                'portfolio_analysis_name': analysis_name,
                'symbol': st.session_state.equity_symbol,
                'company_name': selected_equity['company_name'],
                'start_date': start_date_str,
                'end_date': end_date_str
            }
            
            # Store in session state
            st.session_state.equity_context = equity_ctx
            st.session_state.chart_data_ready = True
        else:
            st.error("❌ Failed to fetch data. Please try again or select a different date range.")
            st.stop()
    
    # Display chart if data is ready (persists across modal interactions)
    if st.session_state.get('chart_data_ready', False) and 'equity_context' in st.session_state:
        equity_ctx = st.session_state.equity_context
        
        # Display context information in compact single row
        st.markdown("---")
        info_col1, info_col2, info_col3, info_col4, info_col5 = st.columns([1, 1.5, 1.5, 2, 1.5])
        with info_col1:
            st.metric("Analysis", "Equity Strategy")
        with info_col2:
            st.metric("Portfolio", equity_ctx['portfolio_name'])
        with info_col3:
            st.metric("Analysis", equity_ctx['portfolio_analysis_name'][:20] + "..." if len(equity_ctx['portfolio_analysis_name']) > 20 else equity_ctx['portfolio_analysis_name'])
        with info_col4:
            st.metric("Stock", f"{equity_ctx['symbol']} - {equity_ctx['company_name'][:15] + '...' if len(equity_ctx['company_name']) > 15 else equity_ctx['company_name']}")
        with info_col5:
            st.metric("Period", f"{equity_ctx['start_date']} to {equity_ctx['end_date']}")
        
        st.markdown("---")
        
        # Configurable Technical Indicators Selection
        st.markdown("#### ⚙️ Technical Indicators Configuration")
        
        # Maximum number of indicators (configurable, not hardcoded)
        MAX_INDICATORS = 3
        
        # Initialize session state for indicators
        if 'confirmed_indicators' not in st.session_state:
            st.session_state.confirmed_indicators = []
        if 'show_indicators_clicked' not in st.session_state:
            st.session_state.show_indicators_clicked = False
        
        # Single button to open indicator selection modal
        indicator_col1, indicator_col2 = st.columns([3, 1])
        with indicator_col1:
            # Show currently selected indicators or prompt
            if st.session_state.confirmed_indicators:
                # Show selected indicators
                available_indicators = [
                    ("RSI (7)", "rsi_7"), ("RSI (14)", "rsi_14"), ("RSI (21)", "rsi_21"),
                    ("MACD", "macd"), ("MACD Signal", "macd_signal"), ("SMA (20)", "sma_20"),
                    ("EMA (12)", "ema_12"), ("EMA (26)", "ema_26"), ("EMA (50)", "ema_50"),
                    ("EMA (100)", "ema_100"), ("Bollinger Upper", "bollinger_upper"),
                    ("Bollinger Middle", "bollinger_middle"), ("Bollinger Lower", "bollinger_lower"), 
                    ("Volume SMA (20)", "volume_sma_20")
                ]
                selected_names = []
                for code in st.session_state.confirmed_indicators:
                    name = next((name for name, c in available_indicators if c == code), code)
                    selected_names.append(name)
                st.markdown(f"**Selected Indicators:** {', '.join(selected_names)}")
            else:
                st.markdown("**No technical indicators selected**")
        
        with indicator_col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Align button
            if st.button("📊 Select Indicators", type="primary"):
                select_indicators_dialog()
        
        
        # Use confirmed indicators from modal
        selected_indicator_codes = st.session_state.confirmed_indicators if st.session_state.show_indicators_clicked else []
        
        # Set default values for indicator calculation
        use_realtime = True
        rsi_period = 14
        macd_fast = 12
        
        # Technical Indicator Configuration Panel
        if st.session_state.confirmed_indicators:
            with st.expander("⚙️ Indicator Configuration & Calculation Methods", expanded=False):
                st.markdown("#### How Technical Indicators are Calculated:")
                
                # Show calculation methods for selected indicators
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
                    elif code in ['ema_12', 'ema_26', 'ema_50', 'ema_100']:
                        period = code.split('_')[1]
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
        
        # Candlestick Chart Section
        st.markdown(f"### 📊 {equity_ctx['symbol']} Price Chart")
        
        try:
            from datetime import datetime
            
            # Convert date strings to datetime objects
            start_dt = datetime.strptime(equity_ctx['start_date'], '%Y-%m-%d')
            end_dt = datetime.strptime(equity_ctx['end_date'], '%Y-%m-%d')
            
            with st.spinner(f"Loading price data for {equity_ctx['symbol']}..."):
                # Fetch stock data using yfinance
                ticker = yf.Ticker(equity_ctx['symbol'])
                hist_data = ticker.history(start=start_dt, end=end_dt)
            
            # Always display basic price chart first
            if hist_data.empty:
                st.error(f"❌ No price data found for {equity_ctx['symbol']} in the specified period.")
            else:
                # Create basic candlestick chart
                fig = go.Figure(data=go.Candlestick(
                    x=hist_data.index,
                    open=hist_data['Open'],
                    high=hist_data['High'],
                    low=hist_data['Low'],
                    close=hist_data['Close'],
                    name=equity_ctx['symbol']
                ))
                
                # Process and add technical indicators ONLY when button is clicked
                indicator_data = {}
                if st.session_state.show_indicators_clicked and st.session_state.confirmed_indicators:
                    with st.spinner(f"Calculating technical indicators..."):
                        if use_realtime:
                            # Real-time calculation from price data
                            try:
                                for indicator_code in selected_indicator_codes:
                                    # RSI indicators with different periods
                                    if indicator_code in ['rsi_7', 'rsi_14', 'rsi_21']:
                                        period = int(indicator_code.split('_')[1])
                                        rsi_values = calculate_rsi_realtime(hist_data['Close'], period)
                                        indicator_data[indicator_code] = {
                                            'dates': hist_data.index.tolist(),
                                            'values': rsi_values.tolist()
                                        }
                                    # EMA indicators with different periods
                                    elif indicator_code in ['ema_12', 'ema_26', 'ema_50', 'ema_100']:
                                        period = int(indicator_code.split('_')[1])
                                        ema_values = calculate_ema_realtime(hist_data['Close'], period)
                                        indicator_data[indicator_code] = {
                                            'dates': hist_data.index.tolist(),
                                            'values': ema_values.tolist()
                                        }
                                    elif indicator_code == 'macd':
                                        # Calculate MACD with configurable parameters
                                        macd_line, _, _ = calculate_macd_realtime(hist_data['Close'], macd_fast, 26, 9)
                                        indicator_data[indicator_code] = {
                                            'dates': hist_data.index.tolist(),
                                            'values': macd_line.tolist()
                                        }
                                    elif indicator_code == 'macd_signal':
                                        # Calculate MACD Signal line
                                        _, signal_line, _ = calculate_macd_realtime(hist_data['Close'], macd_fast, 26, 9)
                                        indicator_data[indicator_code] = {
                                            'dates': hist_data.index.tolist(),
                                            'values': signal_line.tolist()
                                        }
                                    elif indicator_code == 'sma_20':
                                        # Calculate SMA
                                        sma_values = hist_data['Close'].rolling(window=20).mean()
                                        indicator_data[indicator_code] = {
                                            'dates': hist_data.index.tolist(),
                                            'values': sma_values.tolist()
                                        }
                                    elif indicator_code in ['bollinger_upper', 'bollinger_lower', 'bollinger_middle']:
                                        # Calculate Bollinger Bands (20-period, 2 standard deviations)
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
                                st.warning(f"⚠️ Real-time calculation failed, falling back to database: {str(e)}")
                                use_realtime = False
                        
                        if not use_realtime:
                            # Database lookup (original method)
                            try:
                                conn = st.session_state.db_manager.get_connection()
                                with conn:
                                    with conn.cursor() as cur:
                                        for indicator_code in selected_indicator_codes:
                                            # Query technical indicators from daily_equity_technicals table
                                            cur.execute(f"""
                                                SELECT trade_date, {indicator_code}
                                                FROM daily_equity_technicals
                                                WHERE symbol = %s
                                                  AND trade_date >= %s
                                                  AND trade_date <= %s
                                                  AND {indicator_code} IS NOT NULL
                                                ORDER BY trade_date
                                            """, (equity_ctx['symbol'], equity_ctx['start_date'], equity_ctx['end_date']))
                                            
                                            results = cur.fetchall()
                                            if results:
                                                dates = [r[0] for r in results]
                                                values = [r[1] for r in results]
                                                indicator_data[indicator_code] = {'dates': dates, 'values': values}
                            except Exception as e:
                                st.warning(f"⚠️ Could not load technical indicators: {str(e)}")
                
                # Add indicators to chart if they were calculated
                if indicator_data:
                    # Check for Bollinger Bands special handling
                    bollinger_indicators = {}
                    regular_indicators = {}
                    
                    for indicator_code, data in indicator_data.items():
                        if indicator_code in ['bollinger_upper', 'bollinger_lower', 'bollinger_middle']:
                            bollinger_indicators[indicator_code] = data
                        else:
                            regular_indicators[indicator_code] = data
                    
                    # Handle Bollinger Bands as special overlay (on primary y-axis with price)
                    if bollinger_indicators:
                        # Add Bollinger Upper Band
                        if 'bollinger_upper' in bollinger_indicators:
                            fig.add_trace(go.Scatter(
                                x=bollinger_indicators['bollinger_upper']['dates'],
                                y=bollinger_indicators['bollinger_upper']['values'],
                                mode='lines',
                                name='BB Upper',
                                line=dict(color='rgba(255, 0, 0, 0.8)', width=1, dash='dot'),
                                showlegend=True
                            ))
                        
                        # Add Bollinger Lower Band  
                        if 'bollinger_lower' in bollinger_indicators:
                            fig.add_trace(go.Scatter(
                                x=bollinger_indicators['bollinger_lower']['dates'],
                                y=bollinger_indicators['bollinger_lower']['values'],
                                mode='lines',
                                name='BB Lower',
                                line=dict(color='rgba(0, 255, 0, 0.8)', width=1, dash='dot'),
                                showlegend=True
                            ))
                        
                        # Add Middle Band (20-day SMA) if available
                        if 'bollinger_middle' in bollinger_indicators:
                            fig.add_trace(go.Scatter(
                                x=bollinger_indicators['bollinger_middle']['dates'],
                                y=bollinger_indicators['bollinger_middle']['values'],
                                mode='lines',
                                name='BB Middle (SMA20)',
                                line=dict(color='rgba(128, 128, 128, 0.8)', width=1),
                                showlegend=True
                            ))
                        
                        # Add shaded area between bands if both upper and lower exist
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
                    
                    # Handle regular indicators on secondary y-axis
                    if regular_indicators:
                        colors = ['blue', 'purple', 'orange', 'brown', 'pink']
                        for i, (indicator_code, data) in enumerate(regular_indicators.items()):
                            if i < len(colors):
                                # Get display name for indicator
                                display_name = next((name for name, code in available_indicators if code == indicator_code), indicator_code)
                                
                                fig.add_trace(go.Scatter(
                                    x=data['dates'],
                                    y=data['values'],
                                    mode='lines',
                                    name=display_name,
                                    line=dict(color=colors[i], width=2),
                                    yaxis='y2'  # Use secondary y-axis for non-Bollinger indicators
                                ))
                    
                    # Update layout - enable legend when indicators are shown
                    layout_config = {
                        'title': f"{equity_ctx['company_name']} ({equity_ctx['symbol']}) - Price Chart with Technical Analysis<br><sub>Period: {equity_ctx['start_date']} to {equity_ctx['end_date']}</sub>",
                        'yaxis': dict(title="Price (HKD)", side='left'),
                        'xaxis_title': "Date",
                        'height': 650,
                        'showlegend': True,  # Always show legend when indicators are present
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
                
                # Always display the chart (basic chart or chart with indicators)
                st.plotly_chart(fig, use_container_width=True)
                
                # Show indicator summary if any are selected
                if indicator_data and st.session_state.show_indicators_clicked:
                    with st.expander("📊 Technical Indicators Summary", expanded=False):
                        indicator_col1, indicator_col2, indicator_col3 = st.columns(3)
                        for i, (indicator_code, data) in enumerate(indicator_data.items()):
                            display_name = next((name for name, code in available_indicators if code == indicator_code), indicator_code)
                            latest_value = data['values'][-1] if data['values'] else 'N/A'
                            col = [indicator_col1, indicator_col2, indicator_col3][i % 3]
                            with col:
                                st.metric(display_name, f"{latest_value:.2f}" if isinstance(latest_value, (int, float)) else str(latest_value))
                
                # Display key statistics
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
                    volatility = hist_data['Close'].pct_change().std() * (252 ** 0.5) * 100  # Annualized volatility
                    st.metric("Volatility (Annual)", f"{volatility:.2f}%")
                
                # Volume chart (no header text for compact display)
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
                
                # Reset the indicator click flag after chart processing is complete
                if st.session_state.show_indicators_clicked:
                    st.session_state.show_indicators_clicked = False
                    
        except Exception as e:
            st.error(f"❌ Error loading chart data: {str(e)}")
            st.info("💡 Make sure the stock symbol is correct and has available data on Yahoo Finance.")
    
    # Navigation back to Portfolio Analysis
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("🔙 Back to Portfolios", type="secondary"):
            st.session_state.current_page = 'overview'
            st.session_state.navigation['section'] = 'portfolios'
            st.session_state.navigation['page'] = 'overview'
            st.rerun()
    
    with col2:
        st.markdown("*This dashboard will be triggered from Portfolio Value Analysis*")
    
    with col3:
        if st.button("📊 Go to PV Analysis", type="primary"):
            st.session_state.current_page = 'pv_analysis'
            st.session_state.navigation['section'] = 'portfolios'
            st.session_state.navigation['page'] = 'pv_analysis'
            st.rerun()

elif st.session_state.current_page == 'strategy_editor':
    # Strategy Editor - Updated for correct TXYZN understanding
    st.subheader("⚙️ Strategy Editor")
    st.markdown("*Manage trading strategy bases (BBRK, SBDN, BDIV, etc.) and their signal magnitudes (1-9)*")
    
    # Initialize database connection
    try:
        db_manager = DatabaseManager()
        conn = db_manager.get_connection()
    except Exception as e:
        st.error(f"❌ Database connection failed: {str(e)}")
        st.stop()
    
    # Tab navigation for different areas
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Strategy Bases", 
        "📊 Signal Magnitudes", 
        "📈 Recent Signals", 
        "⚙️ Configuration"
    ])
    
    with tab1:
        # Strategy Base Management (BBRK, SBDN, BDIV, etc.)
        st.markdown("### Strategy Base Catalog")
        st.markdown("*These are the actual strategies - the 'XYZ' part of TXYZN format*")
        
        try:
            cur = conn.cursor()
            
            # Get strategy base statistics from our new strategy_catalog table
            cur.execute("""
            SELECT 
                COUNT(*) as total_base_strategies,
                COUNT(DISTINCT category) as categories,
                COUNT(CASE WHEN signal_side = 'B' THEN 1 END) as buy_strategies,
                COUNT(CASE WHEN signal_side = 'S' THEN 1 END) as sell_strategies,
                COUNT(CASE WHEN signal_side = 'H' THEN 1 END) as hold_strategies
            FROM strategy_catalog
            """)
            stats = cur.fetchone()
            
            if stats:
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("Base Strategies", stats[0] or 0)
                with col2:
                    st.metric("Categories", stats[1] or 0)
                with col3:
                    st.metric("Buy Strategies", stats[2] or 0)
                with col4:
                    st.metric("Sell Strategies", stats[3] or 0)
                with col5:
                    st.metric("Hold Strategies", stats[4] or 0)
            
            # Strategy Base Filters
            col1, col2, col3 = st.columns(3)
            with col1:
                category_filter = st.selectbox(
                    "Category Filter:",
                    ["All", "breakout", "mean-reversion", "trend", "divergence", "level"]
                )
            with col2:
                side_filter = st.selectbox("Signal Side Filter:", ["All", "B", "S", "H"])
            with col3:
                complexity_filter = st.selectbox("Complexity Filter:", ["All", "simple", "moderate", "complex"])
            
            # Build query with filters
            query = """
            SELECT strategy_base, strategy_name, signal_side, category, description, 
                   required_indicators, optional_indicators, usage_guidelines, 
                   risk_considerations, market_conditions, implementation_complexity, priority
            FROM strategy_catalog WHERE 1=1
            """
            params = []
            
            if category_filter != "All":
                query += " AND category = %s"
                params.append(category_filter)
            if side_filter != "All":
                query += " AND signal_side = %s"
                params.append(side_filter)
            if complexity_filter != "All":
                query += " AND implementation_complexity = %s"
                params.append(complexity_filter)
            
            query += " ORDER BY priority, category, strategy_base"
            
            cur.execute(query, params)
            base_strategies = cur.fetchall()
            
            # Display strategy bases
            st.markdown("### Available Strategy Bases")
            if base_strategies:
                for strategy in base_strategies:
                    base, name, side, category, description, req_indicators, opt_indicators, usage, risks, conditions, complexity, priority = strategy
                    
                    # Create TXYZN example with different magnitudes
                    side_name = {"B": "Buy", "S": "Sell", "H": "Hold"}[side]
                    side_color = {"B": "🟢", "S": "🔴", "H": "🟡"}[side]
                    
                    with st.expander(f"{side_color} **{base}** - {name} ({side_name})"):
                        col1, col2 = st.columns([3, 2])
                        
                        with col1:
                            st.markdown(f"**Description:** {description}")
                            st.markdown(f"**Category:** {category.title()}")
                            st.markdown(f"**Complexity:** {complexity.title()}")
                            
                            if usage:
                                st.markdown(f"**Best Used:** {usage}")
                            if risks:
                                st.markdown(f"**Risk Notes:** {risks}")
                            
                            # Show market conditions if available
                            if conditions:
                                conditions_list = conditions if isinstance(conditions, list) else []
                                if conditions_list:
                                    st.markdown(f"**Market Conditions:** {', '.join(conditions_list)}")
                        
                        with col2:
                            st.markdown("**TXYZN Signal Examples:**")
                            st.markdown(f"• `{base}1` - Weak signal (magnitude 1)")
                            st.markdown(f"• `{base}5` - Moderate signal (magnitude 5)")  
                            st.markdown(f"• `{base}9` - Strong signal (magnitude 9)")
                            
                            # Show required indicators
                            if req_indicators:
                                indicators_list = req_indicators if isinstance(req_indicators, list) else []
                                if indicators_list and len(indicators_list) > 0:
                                    st.markdown("**Required Indicators:**")
                                    for indicator in indicators_list[:3]:  # Show first 3
                                        st.markdown(f"• {indicator}")
                                    if len(indicators_list) > 3:
                                        st.markdown(f"• ... and {len(indicators_list) - 3} more")
            else:
                st.info("No strategy bases found matching the selected filters.")
        
        except Exception as e:
            st.error(f"Error loading strategy bases: {str(e)}")
    
    with tab2:
        # Signal Magnitude Management
        st.markdown("### Signal Magnitude Management")
        st.markdown("*Configure how magnitude (1-9) reflects signal strength/confidence*")
        
        # Magnitude explanation
        st.info("""
        **Understanding Signal Magnitude (The 'N' in TXYZN):**
        - Magnitude 1-3: Weak signals (experimental/low confidence)
        - Magnitude 4-6: Moderate signals (standard trading signals)  
        - Magnitude 7-9: Strong signals (high confidence/institutional grade)
        """)
        
        # Interactive magnitude simulator
        st.markdown("### Signal Magnitude Simulator")
        col1, col2 = st.columns([2, 3])
        
        with col1:
            # Get available strategy bases for simulation
            try:
                cur = conn.cursor()
                cur.execute("SELECT strategy_base, strategy_name FROM strategy_catalog ORDER BY strategy_base")
                available_bases = cur.fetchall()
                
                if available_bases:
                    base_options = [f"{base} - {name}" for base, name in available_bases]
                    selected_base_display = st.selectbox("Select Strategy Base:", base_options)
                    selected_base = selected_base_display.split(" - ")[0] if selected_base_display else "BBRK"
                    
                    # Magnitude slider
                    magnitude = st.slider("Signal Magnitude", min_value=1, max_value=9, value=5)
                    
                    # Generate example signal
                    example_signal = f"{selected_base}{magnitude}"
                    st.markdown(f"**Generated Signal:** `{example_signal}`")
                else:
                    st.warning("No strategy bases available")
            
            except Exception as e:
                st.error(f"Error loading strategy bases: {str(e)}")
        
        with col2:
            # Show magnitude characteristics
            st.markdown("### Magnitude Characteristics")
            
            magnitude_info = {
                1: {"label": "Experimental", "color": "🔴", "desc": "New/untested signals"},
                2: {"label": "Weak", "color": "🟠", "desc": "Low confidence signals"},  
                3: {"label": "Light", "color": "🟡", "desc": "Cautionary signals"},
                4: {"label": "Moderate-", "color": "🟡", "desc": "Below-average confidence"},
                5: {"label": "Moderate", "color": "🟢", "desc": "Standard trading signal"},
                6: {"label": "Moderate+", "color": "🟢", "desc": "Above-average confidence"},
                7: {"label": "Strong", "color": "🔵", "desc": "High confidence signal"},
                8: {"label": "Very Strong", "color": "🟣", "desc": "Professional grade"},
                9: {"label": "Extreme", "color": "⚫", "desc": "Institutional grade"}
            }
            
            for mag, info in magnitude_info.items():
                if 'magnitude' in locals() and mag == magnitude:
                    st.markdown(f"**{info['color']} {mag}: {info['label']}** - {info['desc']} ← *Selected*")
                else:
                    st.markdown(f"{info['color']} {mag}: {info['label']} - {info['desc']}")
        
        st.markdown("---")
        
        # Show actual trading signals from database (if any exist)
        try:
            cur = conn.cursor()
            cur.execute("""
            SELECT 
                COUNT(*) as total_signals,
                COUNT(DISTINCT symbol) as symbols_with_signals,
                COUNT(DISTINCT strategy_base) as unique_bases_used,
                AVG(signal_magnitude) as avg_magnitude,
                MAX(created_at) as latest_signal
            FROM trading_signals
            WHERE signal_type IS NOT NULL AND strategy_base IS NOT NULL
            """)
            signal_stats = cur.fetchone()
            
            if signal_stats and signal_stats[0] and signal_stats[0] > 0:
                st.markdown("### Recent Trading Signals")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Signals", signal_stats[0])
                with col2:
                    st.metric("Symbols", signal_stats[1])  
                with col3:
                    st.metric("Strategy Bases", signal_stats[2])
                with col4:
                    st.metric("Avg Magnitude", f"{signal_stats[3]:.1f}" if signal_stats[3] else "N/A")
                
                # Show recent signals
                cur.execute("""
                SELECT ts.symbol, ts.signal_type, ts.strategy_base, ts.signal_magnitude, 
                       ts.price, ts.created_at, sc.strategy_name
                FROM trading_signals ts
                LEFT JOIN strategy_catalog sc ON ts.strategy_base = sc.strategy_base
                WHERE ts.signal_type IS NOT NULL
                ORDER BY ts.created_at DESC
                LIMIT 10
                """)
                recent_signals = cur.fetchall()
                
                if recent_signals:
                    for signal in recent_signals:
                        symbol, signal_type, base, magnitude, price, timestamp, strategy_name = signal
                        magnitude_info_display = magnitude_info.get(magnitude, {"color": "⚪", "label": "Unknown"})
                        
                        with st.expander(f"**{symbol}** - {signal_type} {magnitude_info_display['color']}"):
                            col1, col2 = st.columns([2, 1])
                            with col1:
                                st.markdown(f"**Strategy Base:** {base} ({strategy_name or 'Unknown'})")
                                st.markdown(f"**Signal:** {signal_type}")
                                st.markdown(f"**Price:** ${price:.2f}")
                                st.markdown(f"**Timestamp:** {str(timestamp)[:16]}")
                            with col2:
                                st.markdown(f"**Magnitude:** {magnitude}/9")
                                st.markdown(f"**Level:** {magnitude_info_display['label']}")
            else:
                st.info("No trading signals found in database. Generate some signals to see them here.")
        
        except Exception as e:
            st.error(f"Error loading signals: {str(e)}")
    
    with tab3:
        # Recent Signals from Database
        st.markdown("### Recent TXYZN Signals")
        st.markdown("*View recently generated signals from the trading_signals table*")
        
        try:
            cur = conn.cursor()
            
            # Check if we have trading signals with the new format
            cur.execute("""
            SELECT 
                ts.symbol,
                ts.signal_type,
                ts.strategy_base,
                ts.signal_magnitude,
                ts.signal_strength,
                ts.price,
                ts.volume,
                ts.rsi,
                ts.created_at,
                sc.strategy_name,
                sc.category
            FROM trading_signals ts
            LEFT JOIN strategy_catalog sc ON ts.strategy_base = sc.strategy_base
            WHERE ts.signal_type IS NOT NULL
            ORDER BY ts.created_at DESC
            LIMIT 20
            """)
            signals = cur.fetchall()
            
            if signals:
                # Summary statistics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Recent Signals", len(signals))
                with col2:
                    unique_symbols = len(set([s[0] for s in signals]))
                    st.metric("Unique Symbols", unique_symbols)
                with col3:
                    unique_bases = len(set([s[2] for s in signals if s[2]]))
                    st.metric("Strategy Bases Used", unique_bases)
                with col4:
                    avg_magnitude = sum([s[3] for s in signals if s[3]]) / len([s[3] for s in signals if s[3]]) if any(s[3] for s in signals) else 0
                    st.metric("Avg Magnitude", f"{avg_magnitude:.1f}")
                
                st.markdown("---")
                st.markdown("### Signal Details")
                
                # Group signals by symbol for better display
                from collections import defaultdict
                signals_by_symbol = defaultdict(list)
                for signal in signals:
                    signals_by_symbol[signal[0]].append(signal)
                
                for symbol, symbol_signals in signals_by_symbol.items():
                    with st.expander(f"**{symbol}** ({len(symbol_signals)} signals)"):
                        for signal in symbol_signals:
                            symbol, signal_type, strategy_base, magnitude, strength, price, volume, rsi, timestamp, strategy_name, category = signal
                            
                            col1, col2, col3 = st.columns([3, 2, 2])
                            with col1:
                                # Signal info
                                magnitude_color = "🟢" if magnitude and magnitude >= 7 else "🟡" if magnitude and magnitude >= 4 else "🔴"
                                st.markdown(f"**{magnitude_color} {signal_type}** - {strategy_name or 'Unknown Strategy'}")
                                st.markdown(f"Category: {category or 'Unknown'}")
                                st.markdown(f"Time: {str(timestamp)[:16] if timestamp else 'Unknown'}")
                            
                            with col2:
                                # Strategy details
                                st.markdown(f"**Strategy Base:** {strategy_base or 'N/A'}")
                                st.markdown(f"**Magnitude:** {magnitude or 'N/A'}/9")
                                st.markdown(f"**Strength:** {strength or 'N/A'}")
                            
                            with col3:
                                # Market data
                                st.markdown(f"**Price:** ${price:.2f}" if price else "Price: N/A")
                                st.markdown(f"**Volume:** {volume:,}" if volume else "Volume: N/A")
                                st.markdown(f"**RSI:** {rsi:.1f}" if rsi else "RSI: N/A")
                            
                            st.markdown("---")
            else:
                st.info("No signals found in trading_signals table.")
                st.markdown("**To generate signals:**")
                st.markdown("1. Run the HK Strategy Engine")
                st.markdown("2. Signals will be stored in trading_signals table")
                st.markdown("3. New TXYZN format signals will appear here")
                
                # Show signal generation button
                if st.button("🎯 Generate Test Signals"):
                    # This would normally call the signal generation engine
                    st.info("Signal generation feature would be implemented here")
        
        except Exception as e:
            st.error(f"Error loading signals: {str(e)}")
            st.markdown("**Debugging Info:**")
            st.markdown("- Check if trading_signals table exists")
            st.markdown("- Verify database connection")
            st.markdown("- Ensure migration was successful")
    
    with tab4:
        # Configuration and System Status
        st.markdown("### System Configuration")
        st.markdown("*Configure TXYZN strategy system and monitor database status*")
        
        try:
            cur = conn.cursor()
            
            # Database Schema Status
            st.markdown("### Database Schema Status")
            
            # Check our key tables
            tables_to_check = [
                ('strategy_catalog', 'Strategy Base Definitions'),
                ('trading_signals', 'Generated Trading Signals'),
                ('portfolio_positions', 'Portfolio Holdings'),
                ('signal_analysis_view', 'Signal Analysis View')
            ]
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Table Status:**")
                for table, description in tables_to_check:
                    try:
                        if table == 'signal_analysis_view':
                            # Check if view exists
                            cur.execute("""
                            SELECT COUNT(*) FROM information_schema.views 
                            WHERE table_name = 'signal_analysis_view'
                            """)
                            exists = cur.fetchone()[0] > 0
                            status = "✅" if exists else "⚠️"
                            st.markdown(f"{status} **{table}**: {'Available' if exists else 'Missing'}")
                        else:
                            cur.execute(f"SELECT COUNT(*) FROM {table}")
                            count = cur.fetchone()[0]
                            status = "✅" if count >= 0 else "❌"  # >= 0 because empty tables are still valid
                            st.markdown(f"{status} **{table}**: {count} records")
                    except Exception as e:
                        st.markdown(f"❌ **{table}**: Error ({str(e)[:50]}...)")
            
            with col2:
                st.markdown("**TXYZN Format Validation:**")
                # Test TXYZN format patterns
                test_signals = ["BBRK5", "SOBR7", "HMOM3", "INVALID", "BDIV9"]
                for test_signal in test_signals:
                    import re
                    # Updated pattern to include H for Hold signals
                    is_valid = bool(re.match(r'^[BSH][A-Z]{3}[1-9]$', test_signal))
                    status = "✅" if is_valid else "❌"
                    st.markdown(f"{status} **{test_signal}**: {'Valid TXYZN' if is_valid else 'Invalid'}")
            
            st.markdown("---")
            
            # Strategy Base Configuration
            st.markdown("### Strategy Base Summary")
            
            try:
                # Get strategy catalog summary
                cur.execute("""
                SELECT 
                    signal_side,
                    category,
                    COUNT(*) as count,
                    string_agg(strategy_base, ', ' ORDER BY strategy_base) as bases
                FROM strategy_catalog 
                GROUP BY signal_side, category 
                ORDER BY signal_side, category
                """)
                catalog_summary = cur.fetchall()
                
                if catalog_summary:
                    for side, category, count, bases in catalog_summary:
                        side_name = {"B": "Buy", "S": "Sell", "H": "Hold"}[side]
                        side_color = {"B": "🟢", "S": "🔴", "H": "🟡"}[side]
                        
                        with st.expander(f"{side_color} {side_name} - {category.title()} ({count} strategies)"):
                            st.markdown(f"**Strategy Bases:** {bases}")
                            st.markdown(f"**Category:** {category}")
                            st.markdown(f"**Possible Magnitudes:** 1-9 (each base can generate 9 different signal strengths)")
                            st.markdown(f"**Total Combinations:** {count * 9} possible {side_name.lower()} signals")
                else:
                    st.warning("No strategy bases found in catalog")
            
            except Exception as e:
                st.error(f"Error loading strategy summary: {str(e)}")
            
            st.markdown("---")
            
            # Migration Status
            st.markdown("### Migration Status")
            
            try:
                # Check if migration was successful by looking for new columns
                cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'trading_signals' 
                AND column_name IN ('strategy_base', 'signal_magnitude', 'strategy_category')
                ORDER BY column_name
                """)
                migration_columns = [row[0] for row in cur.fetchall()]
                
                expected_columns = ['signal_magnitude', 'strategy_base', 'strategy_category']
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Migration Columns:**")
                    for col in expected_columns:
                        status = "✅" if col in migration_columns else "❌"
                        st.markdown(f"{status} {col}")
                
                with col2:
                    # Check constraint status
                    st.markdown("**TXYZN Constraints:**")
                    cur.execute("""
                    SELECT constraint_name 
                    FROM information_schema.table_constraints 
                    WHERE table_name = 'trading_signals' 
                    AND constraint_type = 'CHECK'
                    AND constraint_name LIKE '%txyzn%'
                    """)
                    constraints = cur.fetchall()
                    
                    if constraints:
                        for constraint in constraints:
                            st.markdown(f"✅ {constraint[0]}")
                    else:
                        st.markdown("⚠️ TXYZN constraints not found")
                
                # Overall migration status
                migration_success = len(migration_columns) == len(expected_columns)
                if migration_success:
                    st.success("✅ Database migration to TXYZN format completed successfully!")
                else:
                    st.warning(f"⚠️ Migration incomplete. Found {len(migration_columns)}/{len(expected_columns)} expected columns.")
            
            except Exception as e:
                st.error(f"Error checking migration status: {str(e)}")
                
        except Exception as e:
            st.error(f"Error loading system configuration: {str(e)}")
    
    # Close database connection
    try:
        conn.close()
    except:
        pass
    
    # Navigation
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔙 Back to Strategy Section", type="secondary"):
            st.session_state.current_page = 'equity_analysis'
            st.session_state.navigation['section'] = 'strategy'
            st.session_state.navigation['page'] = 'equity_analysis'
            st.rerun()
    with col2:
        if st.button("📊 View Portfolios", type="primary"):
            st.session_state.current_page = 'overview'
            st.session_state.navigation['section'] = 'portfolios'
            st.session_state.navigation['page'] = 'overview'
            st.rerun()
    with col3:
        if st.button("🔄 Refresh Data", type="secondary"):
            st.rerun()

elif st.session_state.current_page == 'strategy_comparison':
    # Strategy Comparison Dashboard  
    st.subheader("📊 Strategy Comparison")
    
    # Placeholder content for Strategy Comparison
    st.info("🚧 **Coming Soon!** Strategy Comparison Dashboard")
    st.markdown("""
    **Planned Features:**
    - Side-by-side strategy performance comparison
    - Multi-period analysis and performance attribution
    - Risk-return profile visualization and analysis
    - Statistical significance testing of strategy differences
    - Best practice recommendations based on comparison results
    """)
    
    # Mock comparison interface
    with st.expander("📊 Preview: Strategy Comparison", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.selectbox("Strategy A:", ["Current HK Strategy", "Conservative Growth", "Aggressive Growth"], disabled=True)
        with col2:
            st.selectbox("Strategy B:", ["Market Index", "Peer Average", "Custom Strategy"], disabled=True)
        with col3:
            st.selectbox("Comparison Period:", ["1 Month", "3 Months", "6 Months", "1 Year"], disabled=True)
        
        st.markdown("*Comparison charts and metrics would appear here*")
    
    # Navigation
    if st.button("🔙 Back to Strategy Analysis", type="secondary"):
        st.session_state.current_page = 'equity_analysis'
        st.rerun()

elif st.session_state.current_page == 'overview':
    # All Portfolios Overview Page
    st.subheader("📋 All Portfolios Management")
    
    
    # Portfolio Statistics
    total_portfolios = len(st.session_state.portfolios)
    
    # FIXED: Count unique symbols only (not duplicate positions across portfolios)
    debug_info = []
    all_positions_count = 0  # Keep for debug info - total position entries
    active_positions_count = 0  # Keep for debug info - active position entries
    inactive_positions_count = 0
    
    # Collect unique symbols with details across all portfolios
    all_unique_symbols = set()
    active_unique_symbols = set()
    all_symbol_details = {}  # {symbol: {company_name, sector}}
    active_symbol_details = {}  # {symbol: {company_name, sector}}
    
    for portfolio_id, portfolio_data in st.session_state.portfolios.items():
        portfolio_total = len(portfolio_data['positions'])
        portfolio_active = len([pos for pos in portfolio_data['positions'] if pos['quantity'] > 0])
        portfolio_inactive = portfolio_total - portfolio_active
        
        debug_info.append(f"{portfolio_id}: {portfolio_total} total ({portfolio_active} active, {portfolio_inactive} inactive)")
        all_positions_count += portfolio_total
        active_positions_count += portfolio_active
        inactive_positions_count += portfolio_inactive
        
        # Add unique symbols with details
        for pos in portfolio_data['positions']:
            symbol = pos['symbol']
            all_unique_symbols.add(symbol)
            
            # Store symbol details (use first occurrence if symbol appears in multiple portfolios)
            if symbol not in all_symbol_details:
                all_symbol_details[symbol] = {
                    'company_name': pos.get('company_name', 'Unknown'),
                    'sector': pos.get('sector', 'Other')
                }
            
            if pos['quantity'] > 0:
                active_unique_symbols.add(symbol)
                if symbol not in active_symbol_details:
                    active_symbol_details[symbol] = {
                        'company_name': pos.get('company_name', 'Unknown'),
                        'sector': pos.get('sector', 'Other')
                    }
    
    # Use unique symbol counts for display metrics
    total_positions = len(all_unique_symbols)
    active_positions = len(active_unique_symbols)
    
    # Show debug info in an expander for troubleshooting
    with st.expander("📊 Position Count Breakdown (Debug)", expanded=False):
        st.write("**Detailed position breakdown by portfolio:**")
        for info in debug_info:
            st.write(f"- {info}")
        st.write(f"**Summary:**")
        st.write(f"- Total Position Entries: {all_positions_count}")
        st.write(f"- Active Positions: {active_positions_count}")
        st.write(f"- Inactive Positions (qty=0): {inactive_positions_count}")
        
        # Show the difference between old method (position entries) and new method (unique symbols)
        st.write(f"- **NEW METHOD (Displayed Above):** Unique Symbols: {len(all_unique_symbols)} total, {len(active_unique_symbols)} active")
        st.write(f"- **OLD METHOD:** Position Entries: {all_positions_count} total, {active_positions_count} active")
        st.write(f"- **Difference:** The new method eliminates duplicate symbols across portfolios")
        
        st.markdown("---")
        st.write("**Expected vs Actual:**")
        st.write(f"- You mentioned 3 portfolios × 33 positions = 99 expected")
        st.write(f"- Actual calculation shows: {all_positions_count} total positions")
        st.write(f"- This suggests some positions have quantity = 0 or there are fewer positions than expected")
    
    # Custom CSS for clickable metrics
    st.markdown("""
    <style>
    .clickable-metric {
        background: white;
        border: 1px solid #d4d4d4;
        border-radius: 4px;
        padding: 1rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s ease;
        height: 100px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    .clickable-metric:hover {
        background: #f8f9fa;
        border-color: #007bff;
        box-shadow: 0 2px 4px rgba(0,123,255,0.1);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 600;
        color: #1f77b4;
        margin: 0;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #666;
        margin: 0.25rem 0 0 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Portfolios", total_portfolios, help="Number of portfolios in your system")
    with col2:
        # Clickable Total Positions metric
        if st.button(f"**{total_positions}**\n\nTotal Positions", 
                    key="total_positions_btn", 
                    help="Click to view all unique symbols",
                    use_container_width=True):
            show_total_positions_dialog(all_symbol_details)
    with col3:
        # Clickable Active Positions metric
        if st.button(f"**{active_positions}**\n\nActive Positions", 
                    key="active_positions_btn", 
                    help="Click to view active symbols only",
                    use_container_width=True):
            show_active_positions_dialog(active_symbol_details)
    
    st.markdown("---")
    
    # Portfolio Overview Table with Actions
    st.subheader("📊 Portfolio Overview")
    
    overview_data = []
    for portfolio_id, portfolio_info in st.session_state.portfolios.items():
        active_pos = [pos for pos in portfolio_info['positions'] if pos['quantity'] > 0]
        
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
        
        # Get last update timestamp
        last_update = st.session_state.portfolio_timestamps.get(portfolio_id)
        if not last_update:
            last_update = st.session_state.last_update.get(portfolio_id)
        
        if last_update and last_update != "Never":
            if hasattr(last_update, 'strftime'):
                last_update_str = last_update.strftime('%Y-%m-%d %H:%M:%S')
            else:
                last_update_str = str(last_update)
        else:
            last_update_str = "Never"
        
        overview_data.append({
            "Name": portfolio_info['name'],
            "Description": portfolio_info['description'][:50] + "..." if len(portfolio_info['description']) > 50 else portfolio_info['description'],
            "All Positions": len(portfolio_info['positions']),
            "Active": len(active_pos),
            "Value": f"HK${total_val:,.0f}",
            "Last Updated": last_update_str,
            "Portfolio ID": portfolio_id  # Keep for internal reference but don't display
        })
    
    if overview_data:
        # Enhanced Interactive Table with Action Buttons and Create Button
        table_header_col1, table_header_col2 = st.columns([3, 1])
        with table_header_col1:
            st.markdown("### 📋 Interactive Portfolio Table")
        with table_header_col2:
            if st.button("➕ Create New Portfolio", type="primary", use_container_width=True):
                create_portfolio_dialog()
        
        # CSS styling for clickable portfolio names
        st.markdown("""
        <style>
        div[data-testid="column"] > div[data-testid="stButton"] > button[kind="secondary"] {
            background: transparent !important;
            border: none !important;
            padding: 4px 8px !important;
            color: #1f77b4 !important;
            text-decoration: underline !important;
            font-weight: normal !important;
            text-align: left !important;
            width: 100% !important;
        }
        div[data-testid="column"] > div[data-testid="stButton"] > button[kind="secondary"]:hover {
            color: #0d5aa7 !important;
            background-color: #f0f8ff !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Table header
        header_cols = st.columns([2.5, 2.3, 1.2, 1.0, 1.5, 2, 2])
        with header_cols[0]:
            st.markdown("**Name**")
        with header_cols[1]:
            st.markdown("**Description**")
        with header_cols[2]:
            st.markdown("**All Positions**")
        with header_cols[3]:
            st.markdown("**Active**")
        with header_cols[4]:
            st.markdown("**Value**")
        with header_cols[5]:
            st.markdown("**Last Updated**")
        with header_cols[6]:
            st.markdown("**Actions**")
        
        st.markdown("---")
        
        # Table rows with action buttons
        for i, portfolio_data in enumerate(overview_data):
            portfolio_id = portfolio_data["Portfolio ID"]
            
            row_cols = st.columns([2.5, 2.3, 1.2, 1.0, 1.5, 2, 2])
            
            with row_cols[0]:
                # Clickable portfolio name that navigates to Portfolio Dashboard
                if st.button(portfolio_data['Name'], 
                           key=f"name_click_{portfolio_id}_{i}", 
                           help=f"View {portfolio_id} dashboard",
                           use_container_width=True,
                           type="secondary"):
                    # Navigate to Portfolio Dashboard in view mode (not edit)
                    st.session_state.current_page = 'portfolio'
                    # Use portfolio_switch_request to properly select the portfolio
                    st.session_state.portfolio_switch_request = portfolio_id
                    # Clear edit mode to ensure view mode
                    if portfolio_id in st.session_state.edit_mode:
                        st.session_state.edit_mode[portfolio_id] = False
                    # Update navigation state for unified navigation system
                    st.session_state.navigation['section'] = 'portfolios'
                    st.session_state.navigation['page'] = 'portfolio'
                    st.success(f"👁️ Viewing {portfolio_id} dashboard...")
                    st.rerun()
            with row_cols[1]:
                st.write(portfolio_data['Description'])
            with row_cols[2]:
                st.write(portfolio_data['All Positions'])
            with row_cols[3]:
                st.write(portfolio_data['Active'])
            with row_cols[4]:
                st.write(portfolio_data['Value'])
            with row_cols[5]:
                st.write(portfolio_data['Last Updated'])
            with row_cols[6]:
                # Action buttons for each portfolio
                action_button_cols = st.columns(3)
                
                with action_button_cols[0]:
                    if st.button("🔄", key=f"update_{portfolio_id}_{i}", help="Edit portfolio positions and details", use_container_width=True, type="primary"):
                        # Check for portfolio analysis restrictions before editing
                        has_analyses, analysis_count, message = check_portfolio_has_analyses(portfolio_id)
                        
                        if has_analyses:
                            # Show restriction error and suggest copying
                            st.error(f"🚫 **Cannot edit portfolio**: {message}")
                            st.warning("⚠️ Updating portfolios that already have analyses is not allowed.")
                            st.info(f"💡 **Solution**: Copy '{portfolio_id}' to a new portfolio first, then edit the copy.")
                        else:
                            # Navigate to Portfolio Dashboard in edit mode
                            st.session_state.current_page = 'portfolio'
                            # Use portfolio_switch_request to properly select the portfolio
                            st.session_state.portfolio_switch_request = portfolio_id
                            st.session_state.edit_mode[portfolio_id] = True
                            st.session_state.portfolio_backup[portfolio_id] = copy.deepcopy(st.session_state.portfolios[portfolio_id])
                            # Update navigation state for unified navigation system
                            st.session_state.navigation['section'] = 'portfolios'
                            st.session_state.navigation['page'] = 'portfolio'
                            st.success(f"🔄 Opening {portfolio_id} for editing...")
                            st.rerun()
                
                with action_button_cols[1]:
                    if st.button("📋", key=f"copy_{portfolio_id}_{i}", help="Create a copy of this portfolio", use_container_width=True):
                        copy_portfolio_dialog(portfolio_id)
                
                with action_button_cols[2]:
                    # Handle delete confirmation state
                    confirm_key = f"confirm_delete_{portfolio_id}"
                    is_confirming = st.session_state.get(confirm_key, False)
                    
                    button_label = "⚠️" if is_confirming else "🗑️"
                    button_type = "secondary" if not is_confirming else "primary"
                    help_text = "Click again to confirm deletion" if is_confirming else "Delete this portfolio"
                    
                    if st.button(button_label, key=f"delete_{portfolio_id}_{i}", help=help_text, use_container_width=True, type=button_type):
                        # Enhanced delete with confirmation
                        if len(st.session_state.portfolios) > 1:
                            if not is_confirming:
                                st.session_state[confirm_key] = True
                                st.warning(f"⚠️ Click the warning icon again to permanently delete '{portfolio_id}'")
                                st.rerun()
                            else:
                                # Actually delete the portfolio
                                success = st.session_state.portfolio_manager.delete_portfolio(portfolio_id)
                                if success:
                                    st.session_state.portfolios = st.session_state.portfolio_manager.get_all_portfolios()
                                    st.success(f"✅ Portfolio '{portfolio_id}' deleted!")
                                    # Clean up confirmation state
                                    if confirm_key in st.session_state:
                                        del st.session_state[confirm_key]
                                    st.rerun()
                                else:
                                    st.error(f"❌ Failed to delete portfolio '{portfolio_id}'")
                        else:
                            st.error("❌ Cannot delete the only portfolio!")
            
            # Add separator between rows
            if i < len(overview_data) - 1:
                st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
    
    # Navigation hint
    st.markdown("---")
    st.info("💡 Use the navigation dropdown to view individual portfolios or check system status")

elif st.session_state.current_page == 'portfolio':
    # PORTFOLIO DASHBOARD (default page)
    # Check if user needs to select a portfolio first (only show if portfolios exist)
    if not st.session_state.portfolios:
        st.error("No portfolios available. Please check the Overview page.")
        st.stop()
        
    # Safety check for selected portfolio
    if selected_portfolio is None or selected_portfolio not in st.session_state.portfolios:
        st.sidebar.error("❌ Invalid portfolio selection")
        st.error("Portfolio selection error - please refresh the page")
        st.stop()

    st.sidebar.markdown(f"**{current_portfolio['name']}**")
    st.sidebar.markdown(f"*{current_portfolio['description']}*")
    
    # Main dashboard content
    if is_editing:
        st.subheader(f"✏️ Editing: {current_portfolio['name']}")
        st.info("You are in edit mode. Make changes below, then Save or Cancel in the sidebar.")
        
        # Show pending changes indicator
        if selected_portfolio in st.session_state.pending_changes and st.session_state.pending_changes[selected_portfolio]:
            st.warning(f"⚠️ You have {len(st.session_state.pending_changes[selected_portfolio])} pending changes. Click Save to apply them.")
    else:
        st.subheader(f"📊 {current_portfolio['name']}")

# PORTFOLIO EDITING INTERFACE
if is_editing:
    # Debug information display
    if 'debug_delete_action' in st.session_state:
        with st.expander("🐛 Debug Info - Delete Action Analysis", expanded=False):
            debug_data = st.session_state['debug_delete_action']
            st.json(debug_data)
            if st.button("Clear Debug"):
                del st.session_state['debug_delete_action']
                st.rerun()
    
    # Add New Symbol button
    col_add_btn, col_spacer = st.columns([2, 8])
    with col_add_btn:
        if st.button("➕ Add New Symbol", type="primary", use_container_width=True):
            add_symbol_dialog(selected_portfolio)
    
    st.markdown("---")
    
    # Edit Existing Positions - Table Format
    st.markdown("### 📋 Current Positions (Click to Edit)")
    
    positions = st.session_state.portfolios[selected_portfolio]['positions']
    
    if not positions:
        st.info("No positions in this portfolio. Add some positions above.")
    else:
        # Table header with custom CSS for better styling
        st.markdown("""
        <style>
        .position-table {
            margin-bottom: 20px;
        }
        .deleted-row {
            background-color: rgba(255, 99, 71, 0.1);
            color: #8B0000;
        }
        .modified-row {
            background-color: rgba(255, 215, 0, 0.1);
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Create table structure
        col_header = st.columns([1.5, 2, 1, 1, 1, 1.5])
        col_header[0].markdown("**Ticker**")
        col_header[1].markdown("**Stock Name**") 
        col_header[2].markdown("**Quantity**")
        col_header[3].markdown("**Avg Cost**")
        col_header[4].markdown("**Sector**")
        col_header[5].markdown("**Action**")
        st.markdown("---")
        
        for i, position in enumerate(positions):
            symbol = position['symbol']
            edit_mode_key = f'edit_mode_{selected_portfolio}'
            deleted_key = f'deleted_positions_{selected_portfolio}'
            modified_key = f'modified_positions_{selected_portfolio}'
            
            is_deleted = symbol in st.session_state[deleted_key]
            is_editing = st.session_state[edit_mode_key].get(symbol, False)
            is_modified = symbol in st.session_state[modified_key]
            
            # Apply styling based on state
            if is_deleted:
                st.markdown('<div class="deleted-row">', unsafe_allow_html=True)
            elif is_modified:
                st.markdown('<div class="modified-row">', unsafe_allow_html=True)
            
            col_data = st.columns([1.5, 2, 1, 1, 1, 1.5])
            
            with col_data[0]:
                if is_deleted:
                    st.markdown(f"~~{symbol}~~ 🗑️")
                else:
                    st.text(symbol)
            
            with col_data[1]:
                if is_editing and not is_deleted:
                    # Get current modified value or original
                    current_company = st.session_state[modified_key].get(symbol, {}).get('company_name', position['company_name'])
                    edit_company = st.text_input("", value=current_company, key=f"edit_company_{i}", label_visibility="collapsed")
                else:
                    company_display = position['company_name'][:25] + "..." if len(position['company_name']) > 25 else position['company_name']
                    if is_deleted:
                        st.markdown(f"~~{company_display}~~")
                    else:
                        st.text(company_display)
            
            with col_data[2]:
                if is_editing and not is_deleted:
                    current_qty = st.session_state[modified_key].get(symbol, {}).get('quantity', position['quantity'])
                    edit_quantity = st.number_input("", min_value=0, value=current_qty, key=f"edit_quantity_{i}", step=1, format="%d", label_visibility="collapsed")
                else:
                    if is_deleted:
                        st.markdown(f"~~{position['quantity']:,}~~")
                    else:
                        st.text(f"{position['quantity']:,}")
            
            with col_data[3]:
                if is_editing and not is_deleted:
                    current_cost = st.session_state[modified_key].get(symbol, {}).get('avg_cost', position['avg_cost'])
                    edit_avg_cost = st.number_input("", min_value=0.0, value=current_cost, key=f"edit_avg_cost_{i}", format="%.2f", step=0.01, label_visibility="collapsed")
                else:
                    if is_deleted:
                        st.markdown(f"~~HK${position['avg_cost']:.2f}~~")
                    else:
                        st.text(f"HK${position['avg_cost']:.2f}")
            
            with col_data[4]:
                if is_editing and not is_deleted:
                    current_sector = st.session_state[modified_key].get(symbol, {}).get('sector', position['sector'])
                    sector_options = ["Tech", "Financials", "REIT", "Energy", "Other"]
                    sector_index = sector_options.index(current_sector) if current_sector in sector_options else 4
                    edit_sector = st.selectbox("", sector_options, index=sector_index, key=f"edit_sector_{i}", label_visibility="collapsed")
                else:
                    if is_deleted:
                        st.markdown(f"~~{position.get('sector', 'Other')}~~")
                    else:
                        st.text(position.get('sector', 'Other'))
            
            with col_data[5]:
                if is_deleted:
                    if st.button("↩️ Restore", key=f"restore_{i}"):
                        st.session_state[deleted_key].remove(symbol)
                        st.rerun()
                elif is_editing:
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.button("💾", key=f"save_{i}", help="Save changes"):
                            # Save modifications to session state
                            st.session_state[modified_key][symbol] = {
                                'company_name': edit_company,
                                'quantity': edit_quantity,
                                'avg_cost': edit_avg_cost,
                                'sector': edit_sector
                            }
                            st.session_state[edit_mode_key][symbol] = False
                            st.success(f"✅ {symbol} changes saved (click Save All to commit)")
                            st.rerun()
                    with col_cancel:
                        if st.button("❌", key=f"cancel_{i}", help="Cancel editing"):
                            st.session_state[edit_mode_key][symbol] = False
                            # Remove from modified if was there
                            if symbol in st.session_state[modified_key]:
                                del st.session_state[modified_key][symbol]
                            st.rerun()
                else:
                    col_update, col_delete = st.columns(2)
                    with col_update:
                        if st.button("✏️", key=f"edit_{i}", help="Edit position"):
                            update_position_dialog(selected_portfolio, position)
                    with col_delete:
                        if st.button("🗑️", key=f"delete_{i}", help="Mark for deletion"):
                            # Debug information to track the issue
                            debug_info = {
                                'before_delete': {
                                    'selected_portfolio': selected_portfolio,
                                    'is_editing': is_editing,
                                    'current_page': st.session_state.current_page,
                                    'edit_mode_state': st.session_state.edit_mode.get(selected_portfolio, 'NOT_SET'),
                                    'portfolio_switch_request': st.session_state.portfolio_switch_request
                                }
                            }
                            
                            # Store debug in session state temporarily
                            st.session_state['debug_delete_action'] = debug_info
                            
                            # Perform the delete action
                            st.session_state[deleted_key].add(symbol)
                            st.info(f"📋 {symbol} marked for deletion")
                            
                            # Force preserve edit state before rerun
                            st.session_state.edit_mode[selected_portfolio] = True
                            st.session_state.current_page = 'portfolio'
                            
                            st.rerun()
            
            if is_deleted or is_modified:
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Add separator between rows
            if i < len(positions) - 1:
                st.markdown("<hr style='margin: 5px 0; border: 0.5px solid #ddd;'>", unsafe_allow_html=True)
        
        # Show status of pending changes
        deleted_count = len(st.session_state[deleted_key])
        modified_count = len(st.session_state[modified_key])
        
        if deleted_count > 0 or modified_count > 0:
            st.markdown("---")
            status_msg = []
            if modified_count > 0:
                status_msg.append(f"**{modified_count}** position(s) modified")
            if deleted_count > 0:
                status_msg.append(f"**{deleted_count}** position(s) marked for deletion")
            
            st.warning(f"⚠️ Pending changes: {', '.join(status_msg)}")
        
        # Table-level Save and Cancel buttons
        st.markdown("---")
        col_save_all, col_cancel_all = st.columns([1, 1])
        
        with col_save_all:
            if st.button("💾 Save All Changes", type="primary", use_container_width=True):
                # Show warning dialog
                if deleted_count > 0 or modified_count > 0:
                    if st.session_state.get('confirm_save', False):
                        # Show change summary
                        st.info(f"📝 **Changes Summary**: Adding/Updating {modified_count} position(s), Deleting {deleted_count} position(s)")
                        
                        # Process all changes
                        success = True
                        changes_made = []
                        
                        # Apply modifications
                        for symbol, changes in st.session_state[modified_key].items():
                            position_data = {
                                "symbol": symbol,
                                "company_name": changes['company_name'],
                                "quantity": changes['quantity'],
                                "avg_cost": changes['avg_cost'],
                                "sector": changes['sector']
                            }
                            
                            update_success, error_message = st.session_state.portfolio_manager.update_position(selected_portfolio, position_data)
                            if not update_success:
                                success = False
                                st.error(f"❌ Failed to update {symbol}: {error_message}")
                                if "connection" in error_message.lower():
                                    st.info("💡 This might be a database connection issue. Check your network connection and try again.")
                            else:
                                changes_made.append(f"Updated {symbol}")
                        
                        # Apply deletions
                        for symbol in st.session_state[deleted_key]:
                            remove_success, error_message = st.session_state.portfolio_manager.remove_position(selected_portfolio, symbol)
                            if not remove_success:
                                success = False
                                st.error(f"❌ Failed to delete {symbol}: {error_message}")
                                if "connection" in error_message.lower():
                                    st.info("💡 This might be a database connection issue. Check your network connection and try again.")
                            else:
                                changes_made.append(f"Deleted {symbol}")
                        
                        if success:
                            # Clear session state
                            st.session_state[modified_key].clear()
                            st.session_state[deleted_key].clear()
                            st.session_state[edit_mode_key].clear()
                            
                            # Reload portfolio data to verify persistence
                            st.session_state.portfolios = st.session_state.portfolio_manager.get_all_portfolios()
                            
                            # Show detailed success message
                            if changes_made:
                                st.success("✅ All changes saved successfully to database!")
                                st.info(f"📋 **Changes Applied**: {', '.join(changes_made)}")
                                
                                # Trigger comprehensive portfolio refresh
                                trigger_portfolio_refresh_after_save(selected_portfolio, changes_made)
                            else:
                                st.success("✅ All changes saved successfully to database!")
                            st.rerun()
                        
                        st.session_state.confirm_save = False
                    else:
                        st.session_state.confirm_save = True
                        st.warning("⚠️ This will permanently save all changes to the database. Click 'Save All Changes' again to confirm.")
                        st.rerun()
                else:
                    # Check if user clicked Save with no changes (implement popup-like behavior)
                    if st.session_state.get('no_changes_clicked', False):
                        st.warning("💡 **Nothing to change**: No modifications have been made to this portfolio.")
                        st.session_state['no_changes_clicked'] = False
                    else:
                        st.session_state['no_changes_clicked'] = True
                        st.info("💡 No changes to save")
                        st.rerun()
        
        with col_cancel_all:
            if st.button("🔙 Back", use_container_width=True):
                # Clear all session state
                st.session_state[modified_key].clear()
                st.session_state[deleted_key].clear() 
                st.session_state[edit_mode_key].clear()
                
                # Exit edit mode and return to All Portfolio Management (overview page)
                st.session_state.edit_mode[selected_portfolio] = False
                if selected_portfolio in st.session_state.portfolio_backup:
                    del st.session_state.portfolio_backup[selected_portfolio]
                st.session_state.current_page = 'overview'
                st.session_state.navigation['section'] = 'portfolios'
                st.session_state.navigation['page'] = 'overview'
                st.success("🔙 Returning to All Portfolio Management...")
                st.rerun()

else:
    # NORMAL VIEWING MODE
    if not current_portfolio:
        st.error("No portfolio selected")
        st.stop()
    
    all_positions = current_portfolio['positions']
    
    if not all_positions:
        st.warning("This portfolio has no positions")
        st.stop()
    
    # Process portfolio data for display (including zero-quantity positions)
    portfolio_display = []
    total_value = total_cost = 0
    
    for position in all_positions:
        symbol = position["symbol"]
        
        if (selected_portfolio in st.session_state.portfolio_prices and 
            symbol in st.session_state.portfolio_prices[selected_portfolio]):
            current_price = st.session_state.portfolio_prices[selected_portfolio][symbol]
        else:
            default_prices = {
                "0005.HK": 39.75, "0316.HK": 98.20, "0388.HK": 285.50, "0700.HK": 315.20,
                "0823.HK": 44.15, "0939.HK": 5.52, "1810.HK": 13.45, "2888.HK": 148.20,
                "3690.HK": 98.50, "9618.HK": 130.10, "9988.HK": 118.75
            }
            current_price = default_prices.get(symbol, 50.0)
        
        market_value = current_price * position["quantity"]
        position_cost = position["avg_cost"] * position["quantity"]
        pnl = market_value - position_cost
        # Protect against divide by zero using helper function
        pnl_pct = _safe_percentage(pnl, position_cost)
        
        # Only add to totals if position has quantity > 0
        if position["quantity"] > 0:
            total_value += market_value
            total_cost += position_cost
        
        # Add visual indicator for zero-quantity positions
        quantity_display = f"{position['quantity']:,}"
        if position["quantity"] == 0:
            quantity_display = f"🚫 {quantity_display}"
        
        portfolio_display.append({
            "Symbol": symbol,
            "Company": position["company_name"][:25] + "..." if len(position["company_name"]) > 25 else position["company_name"],
            "Quantity": quantity_display,
            "Avg Cost": f"HK${position['avg_cost']:.2f}",
            "Current": f"HK${current_price:.2f}",
            "Market Value": market_value,
            "P&L": pnl,
            "P&L %": pnl_pct,
            "Sector": position["sector"]
        })
    
    # Unified Portfolio Summary with Daily Change - Compact Layout
    from datetime import date
    today_date = date.today().strftime('%Y-%m-%d')
    st.markdown(f"<h4 style='margin-bottom: 10px;'>💰 Portfolio Summary - {today_date}</h4>", unsafe_allow_html=True)
    
    total_pnl = total_value - total_cost
    # Protect against divide by zero for total P&L percentage using helper function
    total_pnl_pct = _safe_percentage(total_pnl, total_cost)
    
    # Custom CSS for smaller metrics
    st.markdown("""
    <style>
    .metric-container {
        padding: 8px;
        border-radius: 5px;
        text-align: center;
        margin: 2px;
    }
    .metric-label {
        font-size: 11px;
        color: #8e8ea0;
        margin-bottom: 2px;
    }
    .metric-value {
        font-size: 16px;
        font-weight: bold;
        margin-bottom: 1px;
    }
    .metric-delta {
        font-size: 10px;
        margin-top: 1px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create 6-column layout for consolidated metrics
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">Portfolio Value</div>
            <div class="metric-value">HK${total_value:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Show Previous Value if available
        if hasattr(st.session_state, 'prev_day_data') and st.session_state.prev_day_data:
            prev_value = st.session_state.prev_day_data['prev_total_value']
            prev_display = f"HK${prev_value:,.0f}"
        else:
            prev_display = "N/A"
        
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">Previous Value</div>
            <div class="metric-value">{prev_display}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # Show Daily Change if available
        if hasattr(st.session_state, 'prev_day_data') and st.session_state.prev_day_data:
            daily_change = st.session_state.prev_day_data['daily_change']
            daily_change_pct = st.session_state.prev_day_data['daily_change_pct']
            change_color = "#00ff00" if daily_change >= 0 else "#ff4444"
            change_display = f"HK${daily_change:+,.0f}"
            delta_display = f"({daily_change_pct:+.2f}%)"
        else:
            change_display = "N/A"
            delta_display = ""
            change_color = "#8e8ea0"
        
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">Daily Change</div>
            <div class="metric-value" style="color: {change_color};">{change_display}</div>
            <div class="metric-delta" style="color: {change_color};">{delta_display}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">Total Cost</div>
            <div class="metric-value">HK${total_cost:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        pnl_color = "#00ff00" if total_pnl >= 0 else "#ff4444"
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">Total P&L</div>
            <div class="metric-value" style="color: {pnl_color};">HK${total_pnl:+,.0f}</div>
            <div class="metric-delta" style="color: {pnl_color};">({total_pnl_pct:+.1f}%)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col6:
        active_count = len([pos for pos in all_positions if pos['quantity'] > 0])
        total_count = len(portfolio_display)
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">Positions</div>
            <div class="metric-value">{active_count}/{total_count}</div>
            <div class="metric-delta" style="font-size: 9px; color: #8e8ea0;">Active/Total</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Compact Real-time Data section
    st.markdown("---")
    col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])
    
    with col1:
        if st.button(f"🔄 Get Real-time Data", type="primary"):
            # DEBUG: Track portfolio state before real-time data fetch
            debug_before_fetch = {
                'selected_portfolio_before': selected_portfolio,
                'current_portfolio_selection_before': st.session_state.current_portfolio_selection,
                'current_page': st.session_state.current_page,
                'portfolio_switch_request_before': st.session_state.portfolio_switch_request,
                'portfolio_keys_order': portfolio_keys,
                'expected_portfolio': selected_portfolio  # This should be what gets preserved
            }
            st.session_state['debug_realtime_fetch'] = debug_before_fetch
            
            # CRITICAL FIX: Use the actual current portfolio from session state
            # This ensures we preserve the user's actual selection, not a fallback
            actual_current_portfolio = st.session_state.current_portfolio_selection or selected_portfolio
            st.session_state.portfolio_switch_request = actual_current_portfolio
            
            if selected_portfolio not in st.session_state.portfolio_prices:
                st.session_state.portfolio_prices[selected_portfolio] = {}
            if selected_portfolio not in st.session_state.fetch_details:
                st.session_state.fetch_details[selected_portfolio] = []
                
            st.session_state.fetch_details[selected_portfolio] = []
            st.session_state.portfolio_prices[selected_portfolio] = {}
            
            # Get active positions (quantity > 0) for real-time data fetch
            active_positions = [pos for pos in all_positions if pos['quantity'] > 0]
            
            # Check if there are active positions to fetch
            if not active_positions:
                st.warning("No active positions to fetch real-time data for. All positions have zero quantity.")
                st.stop()
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total_symbols = len(active_positions)
            
            for i, position in enumerate(active_positions):
                symbol = position["symbol"]
                status_text.text(f"Fetching {symbol} ({i+1}/{total_symbols})...")
                
                price, status = fetch_hk_price(symbol)
                st.session_state.portfolio_prices[selected_portfolio][symbol] = price
                st.session_state.fetch_details[selected_portfolio].append(status)
                
                # Safe progress calculation with divide by zero protection
                if total_symbols > 0:
                    progress_bar.progress((i + 1) / total_symbols)
                
            st.session_state.last_update[selected_portfolio] = datetime.now()
            status_text.text("✅ All prices updated!")
            time.sleep(1)
            status_text.empty()
            progress_bar.empty()
            
            # Calculate previous day comparison with real historical prices
            try:
                today = date.today()
                prev_trading_day = hkex_calendar.get_previous_trading_day(today - timedelta(days=1))
                
                # Initialize totals
                current_total_value = 0
                prev_total_value = 0
                historical_fetch_details = []
                
                # Fetch historical prices for each position
                for position in active_positions:
                    symbol = position["symbol"]
                    quantity = position["quantity"]
                    
                    # Get both current and previous prices from historical data
                    current_price, prev_price, status = fetch_hk_historical_prices(symbol)
                    
                    # Calculate position values
                    current_position_value = current_price * quantity
                    prev_position_value = prev_price * quantity
                    
                    current_total_value += current_position_value
                    prev_total_value += prev_position_value
                    historical_fetch_details.append(status)
                    
                    # Update session state with current prices for consistency
                    if selected_portfolio not in st.session_state.portfolio_prices:
                        st.session_state.portfolio_prices[selected_portfolio] = {}
                    st.session_state.portfolio_prices[selected_portfolio][symbol] = current_price
                
                # Store historical fetch details
                st.session_state.fetch_details[selected_portfolio] = historical_fetch_details
                
                # Store previous day comparison data
                st.session_state.prev_day_data = {
                    'prev_trading_day': prev_trading_day,
                    'prev_total_value': prev_total_value,
                    'current_total_value': current_total_value,
                    'daily_change': current_total_value - prev_total_value,
                    'daily_change_pct': _safe_percentage((current_total_value - prev_total_value), prev_total_value)
                }
            except Exception as e:
                import logging
                logging.warning(f"Could not calculate previous day comparison: {e}")
                st.session_state.prev_day_data = None
            
            # DEBUG: Update debug info after fetch completion
            if 'debug_realtime_fetch' in st.session_state:
                st.session_state['debug_realtime_fetch']['selected_portfolio_after'] = selected_portfolio
                st.session_state['debug_realtime_fetch']['current_portfolio_selection_after'] = st.session_state.current_portfolio_selection
                st.session_state['debug_realtime_fetch']['portfolio_switch_request_after'] = st.session_state.portfolio_switch_request
                st.session_state['debug_realtime_fetch']['fetch_completed'] = True
                st.session_state['debug_realtime_fetch']['analysis'] = {
                    'portfolio_preserved': st.session_state['debug_realtime_fetch']['expected_portfolio'] == selected_portfolio,
                    'session_state_consistent': st.session_state.current_portfolio_selection == selected_portfolio
                }
            
            st.rerun()
    
    with col2:
        if st.button("📈 Advanced Portfolio Analysis", type="secondary", use_container_width=True):
            # Store the selected portfolio for PV analysis
            st.session_state.selected_portfolio_for_pv = selected_portfolio
            # Navigate to PV analysis page
            st.session_state.current_page = 'pv_analysis'
            st.session_state.navigation['section'] = 'portfolios'
            st.session_state.navigation['page'] = 'pv_analysis'
            st.rerun()
    
    with col3:
        if selected_portfolio in st.session_state.last_update:
            st.caption(f"Last updated: {st.session_state.last_update[selected_portfolio].strftime('%H:%M:%S')}")
        else:
            st.caption("Using default prices")
    
    with col4:
        # Display current portfolio (non-interactive to prevent conflicts)
        current_portfolio_name = st.session_state.portfolios[selected_portfolio]['name']
        if len(current_portfolio_name) > 20:
            current_portfolio_name = current_portfolio_name[:20] + "..."
        st.caption(f"Current: **{current_portfolio_name}**")
    
    with col5:
        # Show debug info if available
        if 'debug_realtime_fetch' in st.session_state:
            debug_data = st.session_state['debug_realtime_fetch']
            if debug_data.get('fetch_completed', False):
                if st.button("🐛 Debug", help="Show real-time fetch debug info"):
                    st.json(debug_data)
                    # Clear debug after showing
                    if st.button("Clear Debug"):
                        del st.session_state['debug_realtime_fetch']
                        st.rerun()
    
    
    # Debug section for real-time fetch issues
    if 'debug_realtime_fetch' in st.session_state:
        with st.expander("🐛 Real-time Fetch Debug Info", expanded=False):
            debug_data = st.session_state['debug_realtime_fetch']
            st.json(debug_data)
            
            # Show analysis
            if debug_data.get('fetch_completed', False):
                before_portfolio = debug_data.get('selected_portfolio_before')
                after_portfolio = debug_data.get('selected_portfolio_after')
                
                if before_portfolio == after_portfolio:
                    st.success(f"✅ Portfolio stayed consistent: {before_portfolio}")
                else:
                    st.error(f"❌ Portfolio changed: {before_portfolio} → {after_portfolio}")
            
            if st.button("Clear Debug Info"):
                del st.session_state['debug_realtime_fetch']
                st.rerun()
    
    # Portfolio table - moved up for better visibility
    st.subheader(f"📋 {selected_portfolio} Holdings")
    
    # Show helpful note about zero-quantity positions
    zero_positions_count = len([pos for pos in all_positions if pos['quantity'] == 0])
    if zero_positions_count > 0:
        st.info(f"💡 Showing all {len(all_positions)} positions including {zero_positions_count} with zero quantity (marked with 🚫)")
    
    # Show fetch details in compact form below table header
    if selected_portfolio in st.session_state.fetch_details and st.session_state.fetch_details[selected_portfolio]:
        with st.expander("📋 Price Fetching Details", expanded=False):
            for detail in st.session_state.fetch_details[selected_portfolio]:
                st.text(detail)
    if portfolio_display:
        df = pd.DataFrame(portfolio_display)
        
        df_display = df.copy()
        df_display['Market Value'] = df_display['Market Value'].apply(lambda x: f"HK${x:,.0f}")
        df_display['P&L'] = df_display['P&L'].apply(lambda x: f"HK${x:,.0f}")
        df_display['P&L %'] = df_display['P&L %'].apply(lambda x: f"{x:+.1f}%")
        
        # Display portfolio with clickable company names
        st.markdown("**Portfolio Holdings** *(Click on company name for equity strategy analysis)*")
        
        # Add table headers
        col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([1, 2.5, 1, 1, 1, 1.5, 1.5, 1, 1])
        with col1:
            st.markdown("**Symbol**")
        with col2:
            st.markdown("**Company** *(Click to analyze)*")
        with col3:
            st.markdown("**Qty**")
        with col4:
            st.markdown("**Avg Cost**")
        with col5:
            st.markdown("**Current**")
        with col6:
            st.markdown("**Market Value**")
        with col7:
            st.markdown("**P&L**")
        with col8:
            st.markdown("**P&L %**")
        with col9:
            st.markdown("**Sector**")
        
        st.markdown("---")
        
        # Create clickable company names table
        for idx, row in df_display.iterrows():
            col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([1, 2.5, 1, 1, 1, 1.5, 1.5, 1, 1])
            
            with col1:
                st.text(row['Symbol'])
            with col2:
                # Make company name clickable
                if st.button(row['Company'], key=f"company_{idx}_{row['Symbol']}", help=f"Analyze {row['Symbol']} strategy"):
                    # Store equity context for navigation with safe handling of current_analysis
                    current_analysis = st.session_state.get('current_analysis')
                    st.session_state.equity_context = {
                        'symbol': row['Symbol'],
                        'company_name': row['Company'],
                        'portfolio_name': current_portfolio['name'],
                        'portfolio_analysis_name': current_analysis.get('name', 'Current Portfolio Analysis') if current_analysis else 'Portfolio Holdings Analysis',
                        'start_date': current_analysis.get('start_date', (date.today() - timedelta(days=180)).strftime('%Y-%m-%d')) if current_analysis else (date.today() - timedelta(days=180)).strftime('%Y-%m-%d'),
                        'end_date': current_analysis.get('end_date', date.today().strftime('%Y-%m-%d')) if current_analysis else date.today().strftime('%Y-%m-%d')
                    }
                    st.session_state.current_page = 'equity_analysis'
                    st.rerun()
            with col3:
                st.text(row['Quantity'])
            with col4:
                st.text(row['Avg Cost'])
            with col5:
                st.text(row['Current'])
            with col6:
                st.text(row['Market Value'])
            with col7:
                st.text(row['P&L'])
            with col8:
                st.text(row['P&L %'])
            with col9:
                st.text(row['Sector'])
        
        # Also show the original dataframe in an expander for easy viewing/copying
        with st.expander("📊 View as Table", expanded=False):
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

# This section is now handled by the overview page

st.markdown("---")
st.caption("💰 Multi-portfolio dashboard with editing • Real-time prices via Yahoo Finance API")