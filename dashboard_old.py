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
                # Try to get company info from Yahoo Finance
                try:
                    stock = yf.Ticker(trimmed_symbol)
                    info = stock.info
                    if info and len(info) > 1:
                        company_name = info.get('longName', info.get('shortName', 'Unknown Company'))
                        # Try to determine sector
                        sector = info.get('sector', 'Other')
                        if sector in ["Technology", "Information Technology"]:
                            sector = "Tech"
                        elif sector in ["Financials", "Financial Services"]:
                            sector = "Financials"
                        elif sector in ["Real Estate"]:
                            sector = "REIT"
                        elif sector in ["Energy"]:
                            sector = "Energy"
                        else:
                            sector = "Other"
                        
                        # Store in session state for display
                        st.session_state['validated_symbol'] = trimmed_symbol
                        st.session_state['validated_company'] = company_name
                        st.session_state['validated_sector'] = sector
                        st.session_state['validation_success'] = True
                        st.success(f"✅ Found: {company_name}")
                    else:
                        st.session_state['validation_success'] = False
                        st.error("❌ Symbol not found on Yahoo Finance")
                except Exception as e:
                    st.error(f"❌ Error validating symbol: {str(e)}")
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
    
    if error_msg:
        st.error(f"❌ {error_msg}")
    
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
            
            # Also add to current portfolio for immediate display
            if validated_symbol not in [pos['symbol'] for pos in st.session_state.portfolios[portfolio_id]['positions']]:
                st.session_state.portfolios[portfolio_id]['positions'].append({
                    'symbol': validated_symbol,
                    'company_name': validated_company,
                    'quantity': quantity,
                    'avg_cost': avg_cost,
                    'sector': validated_sector
                })
            else:
                # Update existing position
                for i, pos in enumerate(st.session_state.portfolios[portfolio_id]['positions']):
                    if pos['symbol'] == validated_symbol:
                        st.session_state.portfolios[portfolio_id]['positions'][i] = {
                            'symbol': validated_symbol,
                            'company_name': validated_company,
                            'quantity': quantity,
                            'avg_cost': avg_cost,
                            'sector': validated_sector
                        }
                        break
            
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
                st.markdown(f"<div style='padding: 8px; color: #8e8ea0; font-size: 14px;'>{page_label} <em>(Coming Soon)</em></div>", 
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
            # Enter edit mode - create backup
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
            breadcrumbs.append('📈 Advanced Analysis')
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
        st.metric("Total Positions", total_positions, help="Total number of stock positions across all portfolios (includes positions with quantity = 0)")
    with col3:
        st.metric("Active Positions", active_positions, help="Number of positions with quantity > 0 (stocks you currently hold)")
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
    # Advanced Portfolio Analysis Page
    st.subheader("📈 Advanced Portfolio Analysis")
    
    # Check if a portfolio was selected for analysis
    if not st.session_state.selected_portfolio_for_pv:
        st.error("❌ No portfolio selected for analysis!")
        st.info("Please go back to the Portfolio Dashboard and select a portfolio first.")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔙 Back to Portfolio Dashboard"):
                st.session_state.current_page = 'portfolio'
                st.rerun()
        with col2:
            if st.button("📋 Go to Overview"):
                st.session_state.current_page = 'overview'
                st.rerun()
        st.stop()
    
    # Get selected portfolio information
    selected_portfolio = st.session_state.selected_portfolio_for_pv
    if selected_portfolio not in st.session_state.portfolios:
        st.error(f"❌ Portfolio '{selected_portfolio}' not found!")
        st.session_state.selected_portfolio_for_pv = None
        st.stop()
    
    current_portfolio = st.session_state.portfolios[selected_portfolio]
    
    # Breadcrumb navigation
    st.markdown(f"**Navigation:** Portfolio Dashboard → {current_portfolio['name']} → Advanced Portfolio Analysis")
    
    col_back, col_switch, col_load, col_refresh = st.columns([1, 2, 1, 1])
    with col_back:
        if st.button("🔙 Back to Portfolio", type="secondary"):
            st.session_state.current_page = 'portfolio'
            st.rerun()
    
    with col_switch:
        # Portfolio selector dropdown for switching portfolios
        portfolio_keys = list(st.session_state.portfolios.keys())
        current_index = portfolio_keys.index(selected_portfolio) if selected_portfolio in portfolio_keys else 0
        
        switch_portfolio = st.selectbox(
            "Switch Portfolio:",
            options=portfolio_keys,
            index=current_index,
            format_func=lambda x: f"{st.session_state.portfolios[x]['name'][:20]}..." if len(st.session_state.portfolios[x]['name']) > 20 else st.session_state.portfolios[x]['name'],
            key="pv_analysis_portfolio_selector",
            help="Select a different portfolio to analyze"
        )
    
    with col_load:
        if st.button("🔄 Load Portfolio", type="primary"):
            if switch_portfolio != selected_portfolio:
                # Update the selected portfolio for PV analysis
                st.session_state.selected_portfolio_for_pv = switch_portfolio
                # Clear current analysis to avoid confusion
                st.session_state.current_analysis = None
                st.success(f"✅ Switched to {st.session_state.portfolios[switch_portfolio]['name']}")
                st.rerun()
            else:
                st.info("Same portfolio already selected")
    
    with col_refresh:
        if st.button("🔄 Refresh"):
            st.session_state.current_analysis = None
            st.rerun()
    
    # Display currently selected portfolio info
    st.info(f"📊 **Currently Analyzing:** {current_portfolio['name']} ({selected_portfolio}) | {len([p for p in current_portfolio['positions'] if p['quantity'] > 0])} active positions")
    
    st.markdown("---")
    
    # Create tabs for different views  
    pv_tab1, pv_tab2 = st.tabs(["📈 Create New Analysis", "📁 Load Previous Analysis"])
    
    with pv_tab1:
        st.markdown(f"### 📊 Portfolio Analysis for: {current_portfolio['name']}")
        
        # Date selection controls
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            start_date = st.date_input(
                "Analysis Start Date",
                value=date.today() - timedelta(days=180),  # Default 6 months ago
                max_value=date.today(),
                help="Select the start date for portfolio analysis"
            )
        
        with col2:
            end_date = st.date_input(
                "Analysis End Date", 
                value=date.today(),
                max_value=date.today(),
                help="Select the end date for portfolio analysis"
            )
        
        with col3:
            cash_amount = st.number_input(
                "Cash Amount (HKD)",
                min_value=0.0,
                value=0.0,
                step=10000.0,
                help="Cash component of portfolio"
            )
        
        # Validate dates
        if start_date and end_date:
            is_valid, message, adj_start, adj_end = validate_hkex_analysis_period(start_date, end_date)
            
            if not is_valid:
                st.error(f"❌ {message}")
            else:
                if adj_start != start_date or adj_end != end_date:
                    st.info(f"ℹ️ {message}")
                
                # Analysis controls
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    analysis_name = st.text_input(
                        "Analysis Name",
                        value=f"{selected_portfolio} PV Analysis {adj_start} to {adj_end}",
                        help="Name for this analysis (required if saving)"
                    )
                
                with col2:
                    save_analysis = st.checkbox(
                        "Save Analysis",
                        value=True,
                        help="Save this analysis for future reference"
                    )
                
                with col3:
                    run_analysis = st.button(
                        "🚀 Run Analysis",
                        type="primary",
                        help="Calculate portfolio value for the selected period"
                    )
                
                # Run analysis when button is clicked
                if run_analysis:
                    if save_analysis and not analysis_name.strip():
                        st.error("Please provide an analysis name to save the results.")
                    else:
                        with st.spinner("Running portfolio analysis..."):
                            try:
                                # Get portfolio positions 
                                portfolio_positions = current_portfolio['positions']
                                positions = {}
                                
                                for pos in portfolio_positions:
                                    if pos['quantity'] > 0:  # Only include positions with quantity > 0
                                        positions[pos['symbol']] = pos['quantity']
                                
                                if not positions:
                                    st.error("No active positions found in this portfolio.")
                                else:
                                    # Create analysis
                                    analysis_id, daily_values_df, metrics = st.session_state.analysis_manager.create_analysis(
                                        name=analysis_name,
                                        start_date=adj_start,
                                        end_date=adj_end,
                                        positions=positions,
                                        cash_amount=cash_amount,
                                        save_analysis=save_analysis
                                    )
                                    
                                    # Store results in session state for display
                                    st.session_state.current_analysis = {
                                        'id': analysis_id,
                                        'name': analysis_name,
                                        'daily_values': daily_values_df,
                                        'metrics': metrics,
                                        'start_date': adj_start,
                                        'end_date': adj_end,
                                        'cash_amount': cash_amount,
                                        'portfolio_name': selected_portfolio
                                    }
                                    
                                    st.success(f"✅ Analysis completed! {len(daily_values_df)} trading days analyzed.")
                                    if save_analysis:
                                        if analysis_id:
                                            st.success(f"📁 Analysis saved with ID: {analysis_id}")
                                        else:
                                            st.warning("⚠️ Analysis completed but could not be saved to database. Results are available for viewing.")
                                    
                            except Exception as e:
                                st.error(f"❌ Error running analysis: {str(e)}")
                                import traceback
                                st.expander("Error Details").code(traceback.format_exc())
    
    with pv_tab2:
        # Load previous analysis
        st.markdown("### 📁 Load Portfolio Analysis")
        st.markdown("Select a previously saved analysis to view its results and continue working with it.")
        
        # Get list of saved analyses
        saved_analyses = st.session_state.db_manager.get_portfolio_analyses(limit=20)
        
        if saved_analyses.empty:
            st.info("No saved analyses found. Create a new analysis in the first tab.")
        else:
            # Format analysis list for display
            analysis_options = []
            for _, row in saved_analyses.iterrows():
                return_pct = row['total_return'] * 100
                analysis_options.append(
                    f"ID {row['id']}: {row['name']} ({row['start_date']} to {row['end_date']}) - {return_pct:+.2f}%"
                )
            
            selected_analysis = st.selectbox(
                "Select Analysis to Load:",
                options=range(len(analysis_options)),
                format_func=lambda x: analysis_options[x],
                help="Select a previously saved analysis to view"
            )
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                load_analysis = st.button("📁 Load Portfolio Analysis", type="primary", use_container_width=True)
            
            with col2:
                if st.button("🗑️ Delete Selected", help="Delete the selected analysis"):
                    analysis_id = int(saved_analyses.iloc[selected_analysis]['id'])
                    if st.session_state.db_manager.delete_portfolio_analysis(analysis_id):
                        st.success("✅ Analysis deleted successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to delete analysis.")
            
            # Load selected analysis
            if load_analysis:
                analysis_id = int(saved_analyses.iloc[selected_analysis]['id'])
                
                with st.spinner("Loading analysis..."):
                    try:
                        analysis_info, daily_values_df, metrics = st.session_state.analysis_manager.load_analysis(analysis_id)
                        
                        # Store results in session state for display
                        st.session_state.current_analysis = {
                            'id': analysis_id,
                            'name': analysis_info['name'],
                            'daily_values': daily_values_df,
                            'metrics': metrics,
                            'start_date': analysis_info['start_date'],
                            'end_date': analysis_info['end_date'],
                            'cash_amount': 0.0,
                            'created_at': analysis_info['created_at'],
                            'portfolio_name': selected_portfolio
                        }
                        
                        st.success(f"✅ Loaded analysis: {analysis_info['name']}")
                        
                    except Exception as e:
                        st.error(f"❌ Error loading analysis: {str(e)}")
    
    # Display current analysis results if available
    if 'current_analysis' in st.session_state and st.session_state.current_analysis:
        analysis = st.session_state.current_analysis
        daily_values_df = analysis['daily_values']
        metrics = analysis['metrics']
        
        st.markdown("---")
        st.markdown(f"<h5 style='margin-bottom: 8px;'>📈 {analysis['name']}</h5>", unsafe_allow_html=True)
        
        # Custom CSS for compact PV Analysis metrics
        st.markdown("""
        <style>
        .pv-metric-container {
            padding: 6px;
            border-radius: 4px;
            text-align: center;
            margin: 1px;
        }
        .pv-metric-label {
            font-size: 10px;
            color: #8e8ea0;
            margin-bottom: 1px;
        }
        .pv-metric-value {
            font-size: 14px;
            font-weight: bold;
            margin-bottom: 0px;
        }
        .pv-metric-delta {
            font-size: 9px;
            margin-top: 0px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Display compact KPIs above chart
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown(f"""
            <div class="pv-metric-container">
                <div class="pv-metric-label">Start PV</div>
                <div class="pv-metric-value">HK${metrics.start_value:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            delta_color = "#00ff00" if metrics.total_return >= 0 else "#ff4444"
            st.markdown(f"""
            <div class="pv-metric-container">
                <div class="pv-metric-label">End PV</div>
                <div class="pv-metric-value">HK${metrics.end_value:,.0f}</div>
                <div class="pv-metric-delta" style="color: {delta_color};">HK${metrics.total_return:+,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            return_color = "#00ff00" if metrics.total_return_pct >= 0 else "#ff4444"
            st.markdown(f"""
            <div class="pv-metric-container">
                <div class="pv-metric-label">Total Return</div>
                <div class="pv-metric-value" style="color: {return_color};">{metrics.total_return_pct:+.2f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="pv-metric-container">
                <div class="pv-metric-label">Max Drawdown</div>
                <div class="pv-metric-value" style="color: #ff4444;">{metrics.max_drawdown_pct:.2f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            st.markdown(f"""
            <div class="pv-metric-container">
                <div class="pv-metric-label">Volatility</div>
                <div class="pv-metric-value">{metrics.volatility:.2f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Create interactive PV chart
        fig = go.Figure()
        
        # Prepare hover data with daily changes and contributors
        hover_texts = []
        for _, row in daily_values_df.iterrows():
            hover_text = f"<b>{row['trade_date']}</b><br>"
            hover_text += f"Portfolio Value: HK${row['total_value']:,.0f}<br>"
            
            if pd.notna(row['daily_change']):
                hover_text += f"Daily Change: HK${row['daily_change']:+,.0f}<br>"
            
            if pd.notna(row['daily_return']):
                hover_text += f"Daily Return: {row['daily_return']*100:+.2f}%<br>"
            
            # Add top contributors
            if row['top_contributors'] and len(row['top_contributors']) > 0:
                hover_text += "<br><b>Top Contributors:</b><br>"
                for i, contrib in enumerate(row['top_contributors'][:3]):  # Show top 3
                    hover_text += f"• {contrib['symbol']}: HK${contrib['contribution']:+,.0f}<br>"
            
            hover_texts.append(hover_text)
        
        # Portfolio Value line
        fig.add_trace(go.Scatter(
            x=daily_values_df['trade_date'],
            y=daily_values_df['total_value'],
            mode='lines',
            name='Portfolio Value',
            line=dict(color='#1f77b4', width=2),
            hovertemplate='%{text}<extra></extra>',
            text=hover_texts
        ))
        
        # Add cash line if cash component exists
        if analysis['cash_amount'] > 0:
            fig.add_trace(go.Scatter(
                x=daily_values_df['trade_date'],
                y=daily_values_df['cash_value'],
                mode='lines',
                name='Cash',
                line=dict(color='green', width=1, dash='dash'),
                hovertemplate='<b>%{x}</b><br>' +
                             'Cash Value: HK$%{y:,.0f}<br>' +
                             '<extra></extra>'
            ))
        
        # Customize chart layout with compact title
        fig.update_layout(
            title={
                'text': f"Portfolio Value Chart - {analysis['portfolio_name']} ({analysis['start_date']} to {analysis['end_date']})",
                'font': {'size': 14},
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis_title="Date",
            yaxis_title="Value (HKD)",
            hovermode='x unified',
            showlegend=True,
            height=500,
            margin=dict(t=40)  # Reduce top margin for compact layout
        )
        
        # Format y-axis
        fig.update_yaxes(tickformat=',.0f')
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Additional analysis details
        with st.expander("📊 Detailed Analysis", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Performance Summary:**")
                
                # Trading Days
                col1a, col1b = st.columns([3, 1])
                with col1a:
                    st.write(f"• Trading Days: {metrics.trading_days}")
                with col1b:
                    st.markdown("ℹ️", help="Number of actual HKEX trading days in the analysis period")
                
                # Start Value
                col1a, col1b = st.columns([3, 1])
                with col1a:
                    st.write(f"• Start Value: HK${metrics.start_value:,.0f}")
                with col1b:
                    st.markdown("ℹ️", help="Total portfolio value on the first trading day of the analysis period")
                
                # End Value
                col1a, col1b = st.columns([3, 1])
                with col1a:
                    st.write(f"• End Value: HK${metrics.end_value:,.0f}")
                with col1b:
                    st.markdown("ℹ️", help="Total portfolio value on the last trading day of the analysis period")
                
                # Absolute P&L
                col1a, col1b = st.columns([3, 1])
                with col1a:
                    st.write(f"• Absolute P&L: HK${metrics.total_return:+,.0f}")
                with col1b:
                    st.markdown("ℹ️", help="Total profit/loss in HK$ (End Value - Start Value)")
                
                # Return %
                col1a, col1b = st.columns([3, 1])
                with col1a:
                    st.write(f"• Return %: {metrics.total_return_pct:+.2f}%")
                with col1b:
                    st.markdown("ℹ️", help="Percentage return calculated as (End Value - Start Value) / Start Value × 100")
                
                # Max Drawdown
                col1a, col1b = st.columns([3, 1])
                with col1a:
                    st.write(f"• Max Drawdown: {metrics.max_drawdown_pct:.2f}%")
                with col1b:
                    st.markdown("ℹ️", help="Maximum peak-to-trough decline during the period, expressed as percentage")
                
                # Volatility
                col1a, col1b = st.columns([3, 1])
                with col1a:
                    st.write(f"• Volatility: {metrics.volatility:.2f}%")
                with col1b:
                    st.markdown("ℹ️", help="Annualized standard deviation of daily returns (252 trading days per year)")
                
                # Sharpe Ratio
                if metrics.sharpe_ratio:
                    col1a, col1b = st.columns([3, 1])
                    with col1a:
                        st.write(f"• Sharpe Ratio: {metrics.sharpe_ratio:.3f}")
                    with col1b:
                        st.markdown("ℹ️", help="Risk-adjusted return measure: (Portfolio Return - Risk-free Rate) / Volatility")
            
            with col2:
                st.write("**Best & Worst Days:**")
                
                # Best Day
                col2a, col2b = st.columns([3, 1])
                with col2a:
                    st.write(f"• Best Day: {metrics.best_day[0]} (+HK${metrics.best_day[1]:,.0f})")
                with col2b:
                    st.markdown("ℹ️", help="Trading day with the largest positive change in portfolio value")
                
                # Worst Day
                col2a, col2b = st.columns([3, 1])
                with col2a:
                    st.write(f"• Worst Day: {metrics.worst_day[0]} (HK${metrics.worst_day[1]:,.0f})")
                with col2b:
                    st.markdown("ℹ️", help="Trading day with the largest negative change in portfolio value")
                
                # Show recent top contributors
                if not daily_values_df.empty and daily_values_df.iloc[-1]['top_contributors']:
                    st.write("**Recent Top Contributors:**")
                    st.markdown("ℹ️ *Top 3 stocks that contributed most to the last trading day's change*", help="Shows which positions had the biggest impact on the most recent day's portfolio change")
                    for contrib in daily_values_df.iloc[-1]['top_contributors']:
                        st.write(f"• {contrib['symbol']}: HK${contrib['contribution']:+,.0f} ({contrib['contribution_pct']:+.1f}%)")
        
        # Add Strategy Analysis Trigger Button
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🎯 Analyze Strategy Performance", type="primary", use_container_width=True):
                # Store current analysis context for strategy analysis
                st.session_state.navigation['context']['source_analysis'] = analysis
                st.session_state.current_page = 'equity_analysis'
                st.session_state.navigation['section'] = 'strategy'
                st.session_state.navigation['page'] = 'equity_analysis'
                st.success("🚀 Launching Equity Strategy Analysis...")
                st.rerun()

# Strategy Analysis Dashboard Pages (New)
elif st.session_state.current_page == 'equity_analysis':
    # Equity Strategy Analysis Dashboard
    st.subheader("📈 Equity Strategy Analysis")
    
    # Check if we have equity context from navigation
    if 'equity_context' not in st.session_state:
        st.warning("⚠️ No equity context found. Please navigate here from a portfolio analysis.")
        st.info("To access this page, go to Portfolio Analysis and click on a company name.")
    else:
        equity_ctx = st.session_state.equity_context
        
        # Display context information
        st.info(f"**Portfolio:** {equity_ctx['portfolio_name']}")
        st.info(f"**Portfolio Analysis:** {equity_ctx['portfolio_analysis_name']}")
        st.info(f"**Stock:** {equity_ctx['symbol']} - {equity_ctx['company_name']}")
        st.info(f"**Analysis Period:** {equity_ctx['start_date']} to {equity_ctx['end_date']}")
        
        st.markdown("---")
        
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
                
                if hist_data.empty:
                    st.error(f"❌ No price data found for {equity_ctx['symbol']} in the specified period.")
                else:
                    # Create candlestick chart
                    fig = go.Figure(data=go.Candlestick(
                        x=hist_data.index,
                        open=hist_data['Open'],
                        high=hist_data['High'],
                        low=hist_data['Low'],
                        close=hist_data['Close'],
                        name=equity_ctx['symbol']
                    ))
                    
                    # Update layout
                    fig.update_layout(
                        title=f"{equity_ctx['company_name']} ({equity_ctx['symbol']}) - Price Chart",
                        subtitle=f"Period: {equity_ctx['start_date']} to {equity_ctx['end_date']}",
                        yaxis_title="Price (HKD)",
                        xaxis_title="Date",
                        height=600,
                        showlegend=False,
                        xaxis_rangeslider_visible=False
                    )
                    
                    # Display the chart
                    st.plotly_chart(fig, use_container_width=True)
                    
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
                    
                    # Volume chart
                    st.markdown("### 📊 Trading Volume")
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
    # Strategy Editor Dashboard
    st.subheader("⚙️ Strategy Editor")
    
    # Placeholder content for Strategy Editor
    st.info("🚧 **Coming Soon!** Strategy Editor Dashboard")
    st.markdown("""
    **Planned Features:**
    - Interactive strategy parameter editing interface
    - Strategy backtesting and simulation tools
    - Risk parameter configuration and validation
    - Strategy template library and management
    - Performance impact preview and analysis
    """)
    
    # Mock strategy editing interface
    with st.expander("📋 Preview: Strategy Configuration", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.selectbox("Strategy Template:", ["HK Growth", "Dividend Focus", "Value Investing", "Momentum", "Custom"], disabled=True)
            st.slider("Risk Tolerance:", 1, 10, 5, disabled=True)
            st.number_input("Max Position Size (%):", 1, 25, 10, disabled=True)
        
        with col2:
            st.selectbox("Rebalancing Frequency:", ["Daily", "Weekly", "Monthly", "Quarterly"], index=2, disabled=True)
            st.checkbox("Enable Stop Loss", disabled=True)
            st.checkbox("Enable Take Profit", disabled=True)
    
    # Navigation
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🔙 Back to Strategy Section", type="secondary"):
            st.session_state.current_page = 'equity_analysis'
            st.rerun()
    with col2:
        if st.button("📊 View Portfolios", type="primary"):
            st.session_state.current_page = 'overview'
            st.session_state.navigation['section'] = 'portfolios'
            st.session_state.navigation['page'] = 'overview'
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
    
    # Debug breakdown of position counting
    debug_info = []
    all_positions_count = 0
    active_positions_count = 0
    inactive_positions_count = 0
    
    for portfolio_id, portfolio_data in st.session_state.portfolios.items():
        portfolio_total = len(portfolio_data['positions'])
        portfolio_active = len([pos for pos in portfolio_data['positions'] if pos['quantity'] > 0])
        portfolio_inactive = portfolio_total - portfolio_active
        
        debug_info.append(f"{portfolio_id}: {portfolio_total} total ({portfolio_active} active, {portfolio_inactive} inactive)")
        all_positions_count += portfolio_total
        active_positions_count += portfolio_active
        inactive_positions_count += portfolio_inactive
    
    total_positions = all_positions_count
    active_positions = active_positions_count
    
    # Show debug info in an expander for troubleshooting
    with st.expander("📊 Position Count Breakdown (Debug)", expanded=False):
        st.write("**Detailed position breakdown by portfolio:**")
        for info in debug_info:
            st.write(f"- {info}")
        st.write(f"**Summary:**")
        st.write(f"- Total Position Entries: {all_positions_count}")
        st.write(f"- Active Positions: {active_positions_count}")
        st.write(f"- Inactive Positions (qty=0): {inactive_positions_count}")
        
        # Check for unique symbols across all portfolios
        all_symbols = set()
        for p in st.session_state.portfolios.values():
            for pos in p['positions']:
                all_symbols.add(pos['symbol'])
        st.write(f"- Unique Symbols Across All Portfolios: {len(all_symbols)}")
        
        st.markdown("---")
        st.write("**Expected vs Actual:**")
        st.write(f"- You mentioned 3 portfolios × 33 positions = 99 expected")
        st.write(f"- Actual calculation shows: {all_positions_count} total positions")
        st.write(f"- This suggests some positions have quantity = 0 or there are fewer positions than expected")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Portfolios", total_portfolios, help="Number of portfolios in your system")
    with col2:
        st.metric("Total Positions", total_positions, help="Total number of stock positions across all portfolios (includes positions with quantity = 0)")
    with col3:
        st.metric("Active Positions", active_positions, help="Number of positions with quantity > 0 (stocks you currently hold)")
    
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
            "Portfolio ID": portfolio_id,
            "Name": portfolio_info['name'],
            "Description": portfolio_info['description'][:50] + "..." if len(portfolio_info['description']) > 50 else portfolio_info['description'],
            "Positions": len(active_pos),
            "Value": f"HK${total_val:,.0f}",
            "Last Updated": last_update_str
        })
    
    if overview_data:
        # Enhanced Interactive Table with Action Buttons
        st.markdown("### 📋 Interactive Portfolio Table")
        
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
        header_cols = st.columns([1.5, 2, 2.5, 1, 1.5, 2, 2])
        with header_cols[0]:
            st.markdown("**Portfolio ID**")
        with header_cols[1]:
            st.markdown("**Name**")
        with header_cols[2]:
            st.markdown("**Description**")
        with header_cols[3]:
            st.markdown("**Positions**")
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
            
            row_cols = st.columns([1.5, 2, 2.5, 1, 1.5, 2, 2])
            
            with row_cols[0]:
                st.write(f"**{portfolio_data['Portfolio ID']}**")
            with row_cols[1]:
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
            with row_cols[2]:
                st.write(portfolio_data['Description'])
            with row_cols[3]:
                st.write(portfolio_data['Positions'])
            with row_cols[4]:
                st.write(portfolio_data['Value'])
            with row_cols[5]:
                st.write(portfolio_data['Last Updated'])
            with row_cols[6]:
                # Action buttons for each portfolio
                action_button_cols = st.columns(3)
                
                with action_button_cols[0]:
                    if st.button("🔄", key=f"update_{portfolio_id}_{i}", help="Edit portfolio positions and details", use_container_width=True, type="primary"):
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
        
        # Simplified Portfolio Actions - Only Create New Portfolio
        st.markdown("---")
        st.subheader("🛠️ Portfolio Actions")
        
        # Center the create portfolio form
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("**➕ Create New Portfolio**")
            
            new_portfolio_id = st.text_input(
                "Portfolio ID:",
                placeholder="e.g., TECH_GROWTH",
                key="new_portfolio_id_overview",
                help="Unique identifier for the portfolio"
            )
            
            new_portfolio_name = st.text_input(
                "Portfolio Name:",
                placeholder="e.g., Technology Growth Portfolio", 
                key="new_portfolio_name_overview",
                help="Descriptive name for the portfolio"
            )
            
            new_portfolio_desc = st.text_area(
                "Description:",
                placeholder="Portfolio focused on technology growth stocks...",
                key="new_portfolio_desc_overview",
                help="Brief description of the portfolio strategy"
            )
            
            if st.button("➕ Create Portfolio", key="create_portfolio_overview_btn", type="primary", use_container_width=True):
                if new_portfolio_id and new_portfolio_name and new_portfolio_id not in st.session_state.portfolios:
                    success = st.session_state.portfolio_manager.create_portfolio(
                        new_portfolio_id, new_portfolio_name, new_portfolio_desc
                    )
                    if success:
                        st.session_state.portfolios = st.session_state.portfolio_manager.get_all_portfolios()
                        st.success(f"✅ Portfolio '{new_portfolio_id}' created successfully!")
                        
                        # Automatically switch to edit mode for the new portfolio
                        st.session_state.current_page = 'portfolio'
                        # Use portfolio_switch_request to properly select the new portfolio
                        st.session_state.portfolio_switch_request = new_portfolio_id
                        st.session_state.edit_mode[new_portfolio_id] = True
                        st.session_state.portfolio_backup[new_portfolio_id] = copy.deepcopy(st.session_state.portfolios[new_portfolio_id])
                        # Update navigation state for unified navigation system
                        st.session_state.navigation['section'] = 'portfolios'
                        st.session_state.navigation['page'] = 'portfolio'
                        st.info("🔄 Redirecting to portfolio editor...")
                        st.rerun()
                    else:
                        st.error("❌ Failed to create portfolio!")
                else:
                    st.error("❌ Please provide valid Portfolio ID and Name. Portfolio ID must be unique!")
    
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
                        # Process all changes
                        success = True
                        
                        # Apply modifications
                        for symbol, changes in st.session_state[modified_key].items():
                            position_data = {
                                "symbol": symbol,
                                "company_name": changes['company_name'],
                                "quantity": changes['quantity'],
                                "avg_cost": changes['avg_cost'],
                                "sector": changes['sector']
                            }
                            
                            if not st.session_state.portfolio_manager.update_position(selected_portfolio, position_data):
                                success = False
                                st.error(f"❌ Failed to update {symbol}")
                        
                        # Apply deletions
                        for symbol in st.session_state[deleted_key]:
                            if not st.session_state.portfolio_manager.remove_position(selected_portfolio, symbol):
                                success = False
                                st.error(f"❌ Failed to delete {symbol}")
                        
                        if success:
                            # Clear session state
                            st.session_state[modified_key].clear()
                            st.session_state[deleted_key].clear()
                            st.session_state[edit_mode_key].clear()
                            
                            # Reload portfolio data
                            st.session_state.portfolios = st.session_state.portfolio_manager.get_all_portfolios()
                            
                            # Stay in editing mode - don't navigate away
                            st.success("✅ All changes saved successfully to database!")
                            st.rerun()
                        
                        st.session_state.confirm_save = False
                    else:
                        st.session_state.confirm_save = True
                        st.warning("⚠️ This will permanently save all changes to the database. Click 'Save All Changes' again to confirm.")
                        st.rerun()
                else:
                    st.info("💡 No changes to save")
        
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
    
    active_positions = [pos for pos in current_portfolio['positions'] if pos['quantity'] > 0]
    
    if not active_positions:
        st.warning("This portfolio has no active positions (quantity > 0)")
        st.stop()
    
    # Process portfolio data for display
    portfolio_display = []
    total_value = total_cost = 0
    
    for position in active_positions:
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
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">Positions</div>
            <div class="metric-value">{len(portfolio_display)}</div>
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
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total_symbols = len(active_positions)
            
            for i, position in enumerate(active_positions):
                symbol = position["symbol"]
                status_text.text(f"Fetching {symbol} ({i+1}/{total_symbols})...")
                
                price, status = fetch_hk_price(symbol)
                st.session_state.portfolio_prices[selected_portfolio][symbol] = price
                st.session_state.fetch_details[selected_portfolio].append(status)
                
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
                    # Store equity context for navigation
                    st.session_state.equity_context = {
                        'symbol': row['Symbol'],
                        'company_name': row['Company'],
                        'portfolio_name': current_portfolio['name'],
                        'portfolio_analysis_name': st.session_state.get('current_analysis', {}).get('name', 'Current Portfolio Analysis'),
                        'start_date': st.session_state.get('current_analysis', {}).get('start_date', (date.today() - timedelta(days=180)).strftime('%Y-%m-%d')),
                        'end_date': st.session_state.get('current_analysis', {}).get('end_date', date.today().strftime('%Y-%m-%d'))
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