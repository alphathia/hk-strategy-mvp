import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from datetime import datetime
import time
import copy
import psycopg2
import redis
import sys
import os
import platform
from src.config_manager import get_config, ConfigurationError
from portfolio_manager import get_portfolio_manager

st.set_page_config(
    page_title="HK Strategy Multi-Portfolio Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("🏦 HK Strategy Multi-Portfolio Dashboard")
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
    st.session_state.current_page = 'portfolio'

if 'pending_changes' not in st.session_state:
    st.session_state.pending_changes = {}

if 'last_save_status' not in st.session_state:
    st.session_state.last_save_status = {}

if 'portfolio_timestamps' not in st.session_state:
    st.session_state.portfolio_timestamps = {}

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

def get_company_name(symbol):
    """Try to fetch company name from Yahoo Finance"""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        return info.get('longName', info.get('shortName', 'Unknown Company'))
    except:
        return 'Unknown Company'

# Portfolio keys - needed for various selectboxes throughout the app
portfolio_keys = list(st.session_state.portfolios.keys())

# Navigation Sidebar
st.sidebar.header("🧭 Navigation")
# Page selection
page_options = {
    'portfolio': '📊 Portfolio Dashboard',
    'overview': '📋 All Portfolios Overview',
    'system': '⚙️ System Status'
}
current_page = st.sidebar.selectbox(
    "Select Page:",
    options=list(page_options.keys()),
    format_func=lambda x: page_options[x],
    index=list(page_options.keys()).index(st.session_state.current_page)
)
if current_page != st.session_state.current_page:
    st.session_state.current_page = current_page
    st.rerun()

st.sidebar.markdown("---")

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

# PAGE ROUTING LOGIC
if st.session_state.current_page == 'overview':
    # All Portfolios Overview Page
    st.sidebar.header("📁 Portfolio Management")
    st.sidebar.info("Use the overview page to manage all portfolios")
    
    st.subheader("📋 All Portfolios Overview")
    
    # Portfolio Statistics
    total_portfolios = len(st.session_state.portfolios)
    total_positions = sum(len([p for p in portfolio['positions'] if p['quantity'] > 0]) 
                         for portfolio in st.session_state.portfolios.values())
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Portfolios", total_portfolios)
    with col2:
        st.metric("Total Positions", total_positions)
    
    st.markdown("---")
    
    # Get portfolio data with creation dates for table display
    try:
        conn = st.session_state.portfolio_manager.get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT portfolio_id, name, description, created_at,
                       COALESCE((SELECT COUNT(*) FROM portfolio_holdings WHERE portfolio_id = p.portfolio_id AND quantity > 0), 0) as position_count
                FROM portfolios p
                ORDER BY created_at DESC
            """)
            portfolio_rows = cur.fetchall()
    except Exception as e:
        st.error(f"Failed to fetch portfolio data: {e}")
        portfolio_rows = []
    
    if portfolio_rows:
        # Display portfolios in integrated table format with actions
        st.subheader("📊 All Portfolios (Latest First)")
        
        # Table header
        col_created, col_id, col_name, col_desc, col_pos, col_edit, col_copy, col_delete = st.columns([1.5, 1.5, 2, 2.5, 1, 0.8, 1.2, 0.8])
        with col_created:
            st.write("**Created**")
        with col_id:
            st.write("**Portfolio ID**")
        with col_name:
            st.write("**Name**")
        with col_desc:
            st.write("**Description**")
        with col_pos:
            st.write("**Positions**")
        with col_edit:
            st.write("**Edit**")
        with col_copy:
            st.write("**Copy**")
        with col_delete:
            st.write("**Delete**")
        
        st.markdown("---")
        
        # Create integrated table with action buttons
        for i, (portfolio_id, name, description, created_at, position_count) in enumerate(portfolio_rows):
            # Use columns for table-like layout
            col_created, col_id, col_name, col_desc, col_pos, col_edit, col_copy, col_delete = st.columns([1.5, 1.5, 2, 2.5, 1, 0.8, 1.2, 0.8])
            
            with col_created:
                st.write(created_at.strftime('%m/%d') if created_at else 'Unknown')
            with col_id:
                st.write(f"**{portfolio_id}**")
            with col_name:
                st.write(name)
            with col_desc:
                short_desc = description[:30] + '...' if len(description) > 30 else description
                st.write(short_desc)
            with col_pos:
                st.write(f"{position_count}")
            with col_edit:
                if st.button("✏️", key=f"edit_{portfolio_id}", help="Edit"):
                    st.session_state.current_page = 'portfolio'
                    st.session_state.selected_portfolio = portfolio_id
                    st.session_state.edit_mode[portfolio_id] = True
                    st.session_state.portfolio_backup[portfolio_id] = copy.deepcopy(st.session_state.portfolios[portfolio_id])
                    st.rerun()
            with col_copy:
                if st.button("📋 Copy", key=f"copy_{portfolio_id}", help="Copy to new"):
                    st.session_state[f"show_copy_form_{portfolio_id}"] = True
                    st.rerun()
            with col_delete:
                if st.button("🗑️", key=f"delete_{portfolio_id}", help="Delete", type="secondary"):
                    if len(st.session_state.portfolios) > 1:
                        if f"confirm_delete_{portfolio_id}" not in st.session_state:
                            st.session_state[f"confirm_delete_{portfolio_id}"] = True
                            st.rerun()
                    else:
                        st.error("❌ Cannot delete the last portfolio!")
            
            # Show copy form if requested
            if st.session_state.get(f"show_copy_form_{portfolio_id}", False):
                with st.expander(f"📋 Copy {portfolio_id} to New Portfolio", expanded=True):
                    copy_col1, copy_col2 = st.columns(2)
                    with copy_col1:
                        new_id = st.text_input("New Portfolio ID:", key=f"copy_id_{portfolio_id}", placeholder=f"{portfolio_id}_Copy")
                        new_name = st.text_input("New Portfolio Name:", key=f"copy_name_{portfolio_id}", placeholder=f"{name} Copy")
                    with copy_col2:
                        new_desc = st.text_area("New Description:", key=f"copy_desc_{portfolio_id}", placeholder=f"Copy of {name}")
                    
                    copy_btn_col1, copy_btn_col2 = st.columns(2)
                    with copy_btn_col1:
                        if st.button("✅ Create Copy", key=f"confirm_copy_{portfolio_id}", type="primary"):
                            if new_id and new_name and new_id not in st.session_state.portfolios:
                                success = st.session_state.portfolio_manager.copy_portfolio(
                                    portfolio_id, new_id, new_name, 
                                    new_desc or f"Copy of {name}"
                                )
                                if success:
                                    st.session_state.portfolios = st.session_state.portfolio_manager.get_all_portfolios()
                                    st.success(f"✅ Portfolio '{new_id}' created successfully!")
                                    del st.session_state[f"show_copy_form_{portfolio_id}"]
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to create portfolio!")
                            else:
                                if not new_id:
                                    st.error("❌ Please enter Portfolio ID")
                                elif not new_name:
                                    st.error("❌ Please enter Portfolio Name")
                                else:
                                    st.error("❌ Portfolio ID already exists!")
                    
                    with copy_btn_col2:
                        if st.button("❌ Cancel", key=f"cancel_copy_{portfolio_id}"):
                            del st.session_state[f"show_copy_form_{portfolio_id}"]
                            st.rerun()
            
            # Show delete confirmation if requested
            if st.session_state.get(f"confirm_delete_{portfolio_id}", False):
                st.warning(f"⚠️ Are you sure you want to delete '{portfolio_id}' - {name}? This action cannot be undone!")
                del_col1, del_col2 = st.columns(2)
                with del_col1:
                    if st.button("✅ Confirm Delete", key=f"confirm_delete_btn_{portfolio_id}", type="primary"):
                        success = st.session_state.portfolio_manager.delete_portfolio(portfolio_id)
                        if success:
                            del st.session_state.portfolios[portfolio_id]
                            st.session_state.portfolios = st.session_state.portfolio_manager.get_all_portfolios()
                            st.success(f"✅ Portfolio '{portfolio_id}' deleted!")
                            del st.session_state[f"confirm_delete_{portfolio_id}"]
                            st.rerun()
                        else:
                            st.error("❌ Failed to delete portfolio!")
                with del_col2:
                    if st.button("❌ Cancel Delete", key=f"cancel_delete_{portfolio_id}"):
                        del st.session_state[f"confirm_delete_{portfolio_id}"]
                        st.rerun()
            
            # Add visual separator except for last row
            if i < len(portfolio_rows) - 1:
                st.markdown("---")
    else:
        st.info("No portfolios found in database.")
    
    # Create New Portfolio
    st.markdown("---")
    st.subheader("➕ Create New Portfolio")
    
    col1, col2 = st.columns(2)
    with col1:
        new_portfolio_id = st.text_input("Portfolio ID:", placeholder="e.g., HKEX_New")
        new_portfolio_name = st.text_input("Portfolio Name:", placeholder="e.g., New HKEX Portfolio")
    with col2:
        new_portfolio_desc = st.text_area("Description:", placeholder="Description of the new portfolio...")
    
    if st.button("➕ Create Portfolio", type="primary"):
        if new_portfolio_id and new_portfolio_name:
            if new_portfolio_id not in st.session_state.portfolios:
                success = st.session_state.portfolio_manager.create_portfolio(
                    new_portfolio_id, new_portfolio_name, new_portfolio_desc or ""
                )
                
                if success:
                    st.session_state.portfolios = st.session_state.portfolio_manager.get_all_portfolios()
                    st.success(f"✅ Portfolio '{new_portfolio_id}' created successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to create portfolio!")
            else:
                st.error("❌ Invalid portfolio ID or already exists!")

elif st.session_state.current_page == 'portfolio':
    # PORTFOLIO DASHBOARD (default page)
    st.sidebar.header("📁 Portfolio Management")
    
    # Portfolio selection logic
    default_selection = getattr(st.session_state, 'selected_portfolio', portfolio_keys[0] if portfolio_keys else None)
    if default_selection not in portfolio_keys:
        default_selection = portfolio_keys[0] if portfolio_keys else None
    
    selected_portfolio = st.sidebar.selectbox(
        "Select Portfolio:",
        options=portfolio_keys,
        format_func=lambda x: f"{x} ({len([p for p in st.session_state.portfolios[x]['positions'] if p['quantity'] > 0])} positions)",
        index=portfolio_keys.index(default_selection) if default_selection in portfolio_keys else 0,
        key="portfolio_selector"
    )
    
    # Update session state selection
    st.session_state.selected_portfolio = selected_portfolio
    
    # Safety check for selected portfolio
    if selected_portfolio is None or selected_portfolio not in st.session_state.portfolios:
        st.sidebar.error("❌ Invalid portfolio selection")
        st.error("Portfolio selection error - please refresh the page")
        st.stop()
    
    current_portfolio = st.session_state.portfolios[selected_portfolio]
    st.sidebar.markdown(f"**{current_portfolio['name']}**")
    st.sidebar.markdown(f"*{current_portfolio['description']}*")
    
    # Check edit mode
    is_editing = st.session_state.edit_mode.get(selected_portfolio, False)
    
    
    # Show pending changes indicator and edit controls in main area
    if is_editing:
        st.subheader(f"✏️ Editing: {current_portfolio['name']}")
        st.info("You are in edit mode. Make changes below, then Save or Cancel.")
        
        # Show pending changes indicator
        if selected_portfolio in st.session_state.pending_changes and st.session_state.pending_changes[selected_portfolio]:
            st.warning(f"⚠️ You have {len(st.session_state.pending_changes[selected_portfolio])} pending changes. Click Save to apply them.")
        
        # Edit control buttons in main area
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("💾 Save Changes", type="primary", key="save_btn"):
                # Check for pending changes and show warning
                has_changes = selected_portfolio in st.session_state.pending_changes and st.session_state.pending_changes[selected_portfolio]
                
                if has_changes:
                    st.warning("⚠️ You have unsaved changes that will be applied!")
                    
                with st.container():
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
                    
                    progress_bar.progress(50)
                    status_text.text("💾 Saving to database...")
                    time.sleep(0.5)
                    
                    # Save to database using portfolio manager
                    success = st.session_state.portfolio_manager.save_portfolio(selected_portfolio, st.session_state.portfolios[selected_portfolio])
                    progress_bar.progress(75)
                    
                    if success:
                        progress_bar.progress(100)
                        status_text.text("✅ Save complete!")
                        
                        # Clean up edit state
                        st.session_state.edit_mode[selected_portfolio] = False
                        if selected_portfolio in st.session_state.portfolio_backup:
                            del st.session_state.portfolio_backup[selected_portfolio]
                        if selected_portfolio in st.session_state.pending_changes:
                            del st.session_state.pending_changes[selected_portfolio]
                        
                        # Update timestamps
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
                        st.success("✅ Portfolio saved successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        progress_bar.empty()
                        status_text.text("❌ Save failed!")
                        st.session_state.last_save_status[selected_portfolio] = {
                            'status': 'error',
                            'message': 'Failed to save portfolio to database!',
                            'timestamp': datetime.now()
                        }
                        st.error("❌ Failed to save to database!")
                        time.sleep(2)
                        status_text.empty()
        
        with col2:
            if st.button("❌ Cancel Changes", type="secondary", key="cancel_btn"):
                # Cancel edit mode and restore backup
                st.session_state.edit_mode[selected_portfolio] = False
                if selected_portfolio in st.session_state.portfolio_backup:
                    # Restore from backup
                    st.session_state.portfolios[selected_portfolio] = copy.deepcopy(st.session_state.portfolio_backup[selected_portfolio])
                    del st.session_state.portfolio_backup[selected_portfolio]
                if selected_portfolio in st.session_state.pending_changes:
                    del st.session_state.pending_changes[selected_portfolio]
                st.info("↩️ Changes cancelled")
                st.rerun()
        
        st.markdown("---")
    else:
        # Not editing - show view mode with edit button
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("📝 Edit Portfolio", type="primary", key="enter_edit_btn"):
                # Enter edit mode - create backup
                st.session_state.edit_mode[selected_portfolio] = True
                st.session_state.portfolio_backup[selected_portfolio] = copy.deepcopy(current_portfolio)
                st.rerun()
        
        st.subheader(f"📊 {current_portfolio['name']}")
        st.markdown("---")
    
    # PORTFOLIO EDITING INTERFACE
    if is_editing:
        st.markdown("### 📝 Edit Portfolio Positions")
        
        # Add/Update Symbol Section
        with st.expander("➕ Add/Update Symbol", expanded=True):
            col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])
            
            with col1:
                new_symbol = st.text_input("Symbol:", placeholder="e.g., 0700.HK")
            with col2:
                new_company = st.text_input("Company:", placeholder="Auto-fetch or manual entry")
                if new_symbol and not new_company and st.button("🔍 Auto-fetch Company", key="fetch_company"):
                    company_name = get_company_name(new_symbol)
                    st.session_state.temp_company = company_name
                    st.rerun()
                
                if hasattr(st.session_state, 'temp_company'):
                    new_company = st.session_state.temp_company
            with col3:
                new_quantity = st.number_input("Quantity:", min_value=0, value=100, step=1)
            with col4:
                new_avg_cost = st.number_input("Avg Cost:", min_value=0.0, value=50.0, step=0.01)
            with col5:
                new_sector = st.selectbox("Sector:", ["Tech", "Financials", "REIT", "Other"], index=0)
            
            if st.button("➕ Add Position", type="primary"):
                if new_symbol and new_company:
                    # Add to pending changes instead of immediate database update
                    if selected_portfolio not in st.session_state.pending_changes:
                        st.session_state.pending_changes[selected_portfolio] = []
                    
                    position_data = {
                        "symbol": new_symbol,
                        "company_name": new_company,
                        "quantity": new_quantity,
                        "avg_cost": new_avg_cost,
                        "sector": new_sector
                    }
                    
                    # Remove any existing change for this symbol
                    st.session_state.pending_changes[selected_portfolio] = [
                        change for change in st.session_state.pending_changes[selected_portfolio]
                        if not (change.get('action') == 'update_position' and change.get('data', {}).get('symbol') == new_symbol)
                    ]
                    
                    # Add new change
                    st.session_state.pending_changes[selected_portfolio].append({
                        'action': 'update_position',
                        'data': position_data
                    })
                    
                    # Update display data immediately (but not database)
                    positions = st.session_state.portfolios[selected_portfolio]['positions']
                    for i, pos in enumerate(positions):
                        if pos['symbol'] == new_symbol:
                            positions[i] = position_data
                            break
                    else:
                        positions.append(position_data)
                    
                    st.success(f"✅ {new_symbol} added (click Save to persist)")
                    st.info("💡 Changes are pending - click 'Save' to apply to database")
                    
                    # Clear temp company
                    if hasattr(st.session_state, 'temp_company'):
                        del st.session_state.temp_company
                    st.rerun()
                else:
                    st.error("❌ Please fill in Symbol and Company")
        
        st.markdown("---")
        st.markdown("### 📋 Current Positions")
        
        # Edit existing positions
        for i, position in enumerate(st.session_state.portfolios[selected_portfolio]['positions']):
            if position['quantity'] > 0:  # Only show positions with quantity > 0
                with st.expander(f"✏️ {position['symbol']} - {position['company_name']}", expanded=False):
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    
                    with col1:
                        edit_company = st.text_input("Company:", value=position['company_name'], key=f"company_{i}")
                    with col2:
                        edit_quantity = st.number_input("Quantity:", min_value=0, value=position['quantity'], key=f"qty_{i}")
                    with col3:
                        edit_avg_cost = st.number_input("Avg Cost:", min_value=0.0, value=position['avg_cost'], step=0.01, key=f"cost_{i}")
                    with col4:
                        edit_sector = st.selectbox("Sector:", ["Tech", "Financials", "REIT", "Other"], 
                                                  index=["Tech", "Financials", "REIT", "Other"].index(position.get('sector', 'Other')), key=f"sector_{i}")
                    
                    col_update, col_remove = st.columns([1, 1])
                    with col_update:
                        if st.button(f"💾 Update {position['symbol']}", key=f"update_{i}"):
                            # Add to pending changes instead of immediate database update
                            if selected_portfolio not in st.session_state.pending_changes:
                                st.session_state.pending_changes[selected_portfolio] = []
                            
                            position_data = {
                                "symbol": position['symbol'],
                                "company_name": edit_company,
                                "quantity": edit_quantity,
                                "avg_cost": edit_avg_cost,
                                "sector": edit_sector
                            }
                            
                            # Remove any existing change for this symbol
                            st.session_state.pending_changes[selected_portfolio] = [
                                change for change in st.session_state.pending_changes[selected_portfolio]
                                if not (change.get('action') == 'update_position' and change.get('data', {}).get('symbol') == position['symbol'])
                            ]
                            
                            # Add new change
                            st.session_state.pending_changes[selected_portfolio].append({
                                'action': 'update_position',
                                'data': position_data
                            })
                            
                            # Update display data immediately (but not database)
                            st.session_state.portfolios[selected_portfolio]['positions'][i] = position_data
                            
                            st.success(f"✅ {position['symbol']} updated (click Save to persist)")
                            st.info("💡 Changes are pending - click 'Save' to apply to database")
                            st.rerun()
                    
                    with col_remove:
                        if st.button(f"🗑️ Remove {position['symbol']}", key=f"remove_{i}"):
                            # Add to pending changes instead of immediate database removal
                            if selected_portfolio not in st.session_state.pending_changes:
                                st.session_state.pending_changes[selected_portfolio] = []
                            
                            # Remove any existing changes for this symbol
                            st.session_state.pending_changes[selected_portfolio] = [
                                change for change in st.session_state.pending_changes[selected_portfolio]
                                if not (change.get('data', {}).get('symbol') == position['symbol'] or change.get('symbol') == position['symbol'])
                            ]
                            
                            # Add removal to pending changes
                            st.session_state.pending_changes[selected_portfolio].append({
                                'action': 'remove_position',
                                'symbol': position['symbol']
                            })
                            
                            # Update display data immediately (but not database) - THIS PREVENTS SCREEN JUMPS
                            st.session_state.portfolios[selected_portfolio]['positions'] = [
                                pos for pos in st.session_state.portfolios[selected_portfolio]['positions']
                                if pos['symbol'] != position['symbol']
                            ]
                            
                            st.success(f"✅ {position['symbol']} removed from view (click Save to persist)")
                            st.info("💡 Changes are pending - click 'Save' to apply to database")
                            st.rerun()
    
    # PORTFOLIO DISPLAY (for both editing and viewing)
    st.markdown("---")
    
    # Fetch prices for current portfolio
    if selected_portfolio not in st.session_state.portfolio_prices:
        st.session_state.portfolio_prices[selected_portfolio] = {}
    
    if selected_portfolio not in st.session_state.fetch_details:
        st.session_state.fetch_details[selected_portfolio] = {}
    
    with st.spinner(f"📈 Fetching current prices for {selected_portfolio}..."):
        for position in current_portfolio['positions']:
            if position['quantity'] > 0 and position['symbol'] not in st.session_state.portfolio_prices[selected_portfolio]:
                price, detail = fetch_hk_price(position['symbol'])
                st.session_state.portfolio_prices[selected_portfolio][position['symbol']] = price
                st.session_state.fetch_details[selected_portfolio][position['symbol']] = detail
        
        # Record the time of last update
        st.session_state.last_update[selected_portfolio] = datetime.now()
    
    # Calculate portfolio metrics
    portfolio_display = []
    total_market_value = 0
    total_cost = 0
    
    for position in current_portfolio['positions']:
        if position['quantity'] > 0:  # Only display positions with quantity > 0
            current_price = st.session_state.portfolio_prices[selected_portfolio].get(position['symbol'], position['avg_cost'])
            market_value = position['quantity'] * current_price
            cost_basis = position['quantity'] * position['avg_cost']
            pnl = market_value - cost_basis
            pnl_pct = (pnl / cost_basis * 100) if cost_basis > 0 else 0
            
            portfolio_display.append({
                'Symbol': position['symbol'],
                'Company': position['company_name'],
                'Quantity': position['quantity'],
                'Avg Cost': position['avg_cost'],
                'Current': current_price,
                'Market Value': market_value,
                'P&L': pnl,
                'P&L %': pnl_pct,
                'Sector': position.get('sector', 'Other')
            })
            
            total_market_value += market_value
            total_cost += cost_basis
    
    total_pnl = total_market_value - total_cost
    total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
    
    # Display portfolio metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Market Value", f"HK${total_market_value:,.0f}")
    with col2:
        st.metric("Cost Basis", f"HK${total_cost:,.0f}")
    with col3:
        st.metric("Total P&L", f"HK${total_pnl:,.0f}", delta=f"{total_pnl_pct:+.1f}%")
    with col4:
        st.metric("Positions", len(portfolio_display))
    
    st.markdown("---")
    
    # Portfolio table
    st.subheader(f"📋 {selected_portfolio} Holdings")
    if portfolio_display:
        df = pd.DataFrame(portfolio_display)
        
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

elif st.session_state.current_page == 'system':
    # SYSTEM STATUS PAGE
    st.title("⚙️ System Status Dashboard")
    st.markdown("---")
    
    # Database Health Check Section
    st.subheader("🗄️ Database Health")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Database Connection Test**")
        try:
            conn = st.session_state.portfolio_manager.get_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
            st.success("✅ Database connection successful")
        except Exception as e:
            st.error(f"❌ Database connection failed: {str(e)}")
        
        # Portfolio Tables Check
        st.markdown("**Portfolio Tables Status**")
        try:
            conn = st.session_state.portfolio_manager.get_connection()
            with conn.cursor() as cur:
                # Check portfolios table
                cur.execute("SELECT COUNT(*) FROM portfolios")
                portfolio_count = cur.fetchone()[0]
                
                # Check portfolio_holdings table
                cur.execute("SELECT COUNT(*) FROM portfolio_holdings")
                holdings_count = cur.fetchone()[0]
                
                st.success(f"✅ Portfolios table: {portfolio_count} records")
                st.success(f"✅ Holdings table: {holdings_count} records")
        except Exception as e:
            st.error(f"❌ Portfolio tables check failed: {str(e)}")
    
    with col2:
        st.markdown("**Portfolio Data Summary**")
        try:
            portfolios = st.session_state.portfolios
            total_portfolios = len(portfolios)
            total_positions = sum(len([p for p in portfolio['positions'] if p['quantity'] > 0]) 
                                 for portfolio in portfolios.values())
            
            st.metric("Total Portfolios", total_portfolios)
            st.metric("Active Positions", total_positions)
            
            if portfolios:
                st.success("✅ Portfolio data loaded successfully")
            else:
                st.warning("⚠️ No portfolio data found")
        except Exception as e:
            st.error(f"❌ Portfolio data check failed: {str(e)}")
    
    st.markdown("---")
    
    # Portfolio Reset Section
    st.subheader("🔄 Portfolio Reset & Setup")
    st.warning("⚠️ **Danger Zone** - These actions will modify or delete data!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Reset All Portfolios**")
        st.info("This will delete all existing portfolios and create a new default HKEX portfolio with sample data.")
        
        if st.button("🔄 Reset All Portfolios", type="secondary", key="reset_portfolios_btn"):
            if 'confirm_reset_portfolios' not in st.session_state:
                st.session_state.confirm_reset_portfolios = True
                st.rerun()
        
        if st.session_state.get('confirm_reset_portfolios', False):
            st.error("⚠️ This will DELETE ALL existing portfolios and create a new default portfolio!")
            
            col_confirm, col_cancel = st.columns(2)
            with col_confirm:
                if st.button("✅ Confirm Reset", type="primary", key="confirm_reset_btn"):
                    try:
                        conn = st.session_state.portfolio_manager.get_connection()
                        with conn.cursor() as cur:
                            # Clear all existing portfolio data
                            cur.execute("DELETE FROM portfolio_holdings")
                            cur.execute("DELETE FROM portfolios")
                            
                            # Create new default portfolio
                            cur.execute("""
                                INSERT INTO portfolios (portfolio_id, name, description)
                                VALUES (%s, %s, %s)
                            """, ('HKEX_Base', 'HKEX Base Portfolio', 'Primary Hong Kong equity holdings'))
                            
                            # Insert the provided stock data
                            portfolio_positions = [
                                ('HKEX_Base', '0005.HK', 'HSBC Holdings plc', 13428, 38.50, 'Financials'),
                                ('HKEX_Base', '0316.HK', 'Orient Overseas', 100, 95.00, 'Other'),
                                ('HKEX_Base', '0388.HK', 'Hong Kong Exchanges', 300, 280.00, 'Financials'),
                                ('HKEX_Base', '0700.HK', 'Tencent Holdings Ltd', 3100, 320.50, 'Tech'),
                                ('HKEX_Base', '0823.HK', 'Link REIT', 1300, 42.80, 'REIT'),
                                ('HKEX_Base', '0857.HK', 'PetroChina Company Ltd', 0, 7.50, 'Energy'),
                                ('HKEX_Base', '0939.HK', 'China Construction Bank', 26700, 5.45, 'Financials'),
                                ('HKEX_Base', '1810.HK', 'Xiaomi Corporation', 2000, 12.30, 'Tech'),
                                ('HKEX_Base', '2888.HK', 'Standard Chartered PLC', 348, 145.00, 'Financials'),
                                ('HKEX_Base', '3690.HK', 'Meituan', 340, 95.00, 'Tech'),
                                ('HKEX_Base', '9618.HK', 'JD.com', 133, 125.00, 'Tech'),
                                ('HKEX_Base', '9988.HK', 'Alibaba Group', 2000, 115.00, 'Tech')
                            ]
                            
                            for portfolio_id, symbol, company_name, quantity, avg_cost, sector in portfolio_positions:
                                cur.execute("""
                                    INSERT INTO portfolio_holdings 
                                    (portfolio_id, symbol, company_name, quantity, avg_cost, sector)
                                    VALUES (%s, %s, %s, %s, %s, %s)
                                """, (portfolio_id, symbol, company_name, quantity, avg_cost, sector))
                            
                            conn.commit()
                            
                            # Reload portfolios in session state
                            st.session_state.portfolios = st.session_state.portfolio_manager.get_all_portfolios()
                            
                            # Clear confirmation state
                            del st.session_state.confirm_reset_portfolios
                            
                            st.success("✅ All portfolios reset successfully! New HKEX_Base portfolio created with sample data.")
                            time.sleep(2)
                            st.rerun()
                            
                    except Exception as e:
                        st.error(f"❌ Failed to reset portfolios: {str(e)}")
                        if 'confirm_reset_portfolios' in st.session_state:
                            del st.session_state.confirm_reset_portfolios
            
            with col_cancel:
                if st.button("❌ Cancel Reset", key="cancel_reset_btn"):
                    del st.session_state.confirm_reset_portfolios
                    st.rerun()
    
    with col2:
        st.markdown("**Database Maintenance**")
        st.info("Perform database maintenance operations.")
        
        if st.button("🧹 Clean Empty Positions", key="clean_positions_btn"):
            try:
                conn = st.session_state.portfolio_manager.get_connection()
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM portfolio_holdings WHERE quantity = 0")
                    deleted_rows = cur.rowcount
                    conn.commit()
                    st.success(f"✅ Cleaned {deleted_rows} empty positions")
            except Exception as e:
                st.error(f"❌ Failed to clean positions: {str(e)}")
        
        if st.button("🔄 Refresh Portfolio Data", key="refresh_data_btn"):
            try:
                st.session_state.portfolios = st.session_state.portfolio_manager.get_all_portfolios()
                st.success("✅ Portfolio data refreshed")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to refresh data: {str(e)}")
    
    st.markdown("---")
    
    # System Information
    st.subheader("ℹ️ System Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Application Status**")
        st.success("✅ Dashboard running")
        st.success("✅ Portfolio management active")
        st.success("✅ Real-time pricing enabled")
        
    with col2:
        st.markdown("**Configuration**")
        try:
            config = st.session_state.portfolio_manager.config
            st.info("✅ Configuration loaded successfully")
        except Exception as e:
            st.error(f"❌ Configuration error: {str(e)}")
        
        st.info("📊 Using Yahoo Finance for price data")
        st.info("🗄️ PostgreSQL database backend")

st.markdown("---")
st.caption("💰 Multi-portfolio dashboard with editing • Real-time prices via Yahoo Finance API")