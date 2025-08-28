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
    
    st.subheader("📋 All Portfolios Management")
    
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
    
    # Portfolio Management Actions
    st.subheader("🔧 Portfolio Actions")
    
    action_col1, action_col2 = st.columns(2)
    
    with action_col1:
        # View/Edit Portfolio
        st.markdown("**📊 View/Edit Portfolio:**")
        view_portfolio = st.selectbox(
            "Select portfolio to view/edit:",
            options=list(st.session_state.portfolios.keys()),
            key="view_portfolio_select"
        )
        
        col_view, col_edit = st.columns(2)
        with col_view:
            if st.button("👁️ View", key="view_portfolio_btn"):
                st.session_state.current_page = 'portfolio'
                st.session_state.selected_portfolio = view_portfolio
                st.rerun()
        
        with col_edit:
            if st.button("✏️ Edit", key="edit_portfolio_btn"):
                st.session_state.current_page = 'portfolio'
                st.session_state.selected_portfolio = view_portfolio
                st.session_state.edit_mode[view_portfolio] = True
                st.session_state.portfolio_backup[view_portfolio] = copy.deepcopy(st.session_state.portfolios[view_portfolio])
                st.rerun()
    
    with action_col2:
        # Delete Portfolio
        st.markdown("**🗑️ Delete Portfolio:**")
        delete_portfolio = st.selectbox(
            "Select portfolio to delete:",
            options=list(st.session_state.portfolios.keys()),
            key="delete_portfolio_select"
        )
        
        if st.button("🗑️ Delete Portfolio", key="delete_portfolio_btn", type="secondary"):
            if len(st.session_state.portfolios) > 1:  # Don't delete if only one portfolio
                # Show confirmation
                if f"confirm_delete_{delete_portfolio}" not in st.session_state:
                    st.session_state[f"confirm_delete_{delete_portfolio}"] = False
                
                if not st.session_state[f"confirm_delete_{delete_portfolio}"]:
                    st.session_state[f"confirm_delete_{delete_portfolio}"] = True
                    st.warning(f"⚠️ Are you sure you want to delete '{delete_portfolio}'? This action cannot be undone!")
                    if st.button("✅ Confirm Delete", key=f"confirm_delete_btn_{delete_portfolio}"):
                        success = st.session_state.portfolio_manager.delete_portfolio(delete_portfolio)
                        if success:
                            del st.session_state.portfolios[delete_portfolio]
                            st.session_state.portfolios = st.session_state.portfolio_manager.get_all_portfolios()
                            st.success(f"✅ Portfolio '{delete_portfolio}' deleted!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to delete portfolio!")
            else:
                st.error("❌ Cannot delete the last portfolio!")
    
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
    
    # Edit Mode Controls
    st.sidebar.markdown("---")
    st.sidebar.subheader("✏️ Portfolio Editing")
    if not is_editing:
        if st.sidebar.button("📝 Edit Portfolio", type="primary"):
            # Enter edit mode - create backup
            st.session_state.edit_mode[selected_portfolio] = True
            st.session_state.portfolio_backup[selected_portfolio] = copy.deepcopy(current_portfolio)
            st.rerun()
    else:
        st.sidebar.warning("🔄 Editing Mode Active")
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("💾 Save", type="primary", key="save_btn"):
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
                        st.sidebar.success("✅ Portfolio saved successfully!")
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
                        st.sidebar.error("❌ Failed to save to database!")
                        time.sleep(2)
                        status_text.empty()
        
        with col2:
            if st.button("❌ Cancel", type="secondary", key="cancel_btn"):
                # Cancel edit mode and restore backup
                st.session_state.edit_mode[selected_portfolio] = False
                if selected_portfolio in st.session_state.portfolio_backup:
                    # Restore from backup
                    st.session_state.portfolios[selected_portfolio] = copy.deepcopy(st.session_state.portfolio_backup[selected_portfolio])
                    del st.session_state.portfolio_backup[selected_portfolio]
                if selected_portfolio in st.session_state.pending_changes:
                    del st.session_state.pending_changes[selected_portfolio]
                st.sidebar.info("↩️ Changes cancelled")
                st.rerun()
    
    # Copy Portfolio section (only if not editing)
    if not is_editing:
        st.sidebar.markdown("---")
        st.sidebar.subheader("📋 Copy Portfolio")
        
        copy_to_id = st.sidebar.text_input("New Portfolio ID:", placeholder="e.g., HKEX_Base_Copy")
        copy_to_name = st.sidebar.text_input("New Portfolio Name:", placeholder="e.g., HKEX Base Copy")
        copy_to_desc = st.sidebar.text_area("New Description:", placeholder="Copy of existing portfolio...")
        
        if st.sidebar.button("📋 Copy Portfolio"):
            if copy_to_id and copy_to_name and copy_to_id not in st.session_state.portfolios:
                # Use portfolio manager for proper database integration and isolation
                success = st.session_state.portfolio_manager.copy_portfolio(
                    selected_portfolio, copy_to_id, copy_to_name, 
                    copy_to_desc or f"Copy of {current_portfolio['name']}"
                )
                
                if success:
                    # Reload portfolios from database to get the updated data
                    st.session_state.portfolios = st.session_state.portfolio_manager.get_all_portfolios()
                    st.sidebar.success(f"✅ Portfolio '{copy_to_id}' created!")
                    st.sidebar.info("🔄 Select it from the dropdown to view")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.sidebar.error("❌ Failed to create portfolio!")
            else:
                if not copy_to_id:
                    st.sidebar.error("❌ Please enter Portfolio ID")
                elif not copy_to_name:
                    st.sidebar.error("❌ Please enter Portfolio Name")
                else:
                    st.sidebar.error("❌ Portfolio ID already exists!")
    
    # Show pending changes indicator
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
    
    st.info("System status checks would go here - database health, API connectivity, etc.")

st.markdown("---")
st.caption("💰 Multi-portfolio dashboard with editing • Real-time prices via Yahoo Finance API")