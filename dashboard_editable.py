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

st.set_page_config(
    page_title="HK Strategy Multi-Portfolio Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("🏦 HK Strategy Multi-Portfolio Dashboard")
st.markdown("---")

# Initialize session state
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

if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = {}

if 'portfolio_backup' not in st.session_state:
    st.session_state.portfolio_backup = {}

if 'current_page' not in st.session_state:
    st.session_state.current_page = 'portfolio'

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
            r = redis.Redis(**redis_config, decode_responses=True, socket_connect_timeout=3)
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

# Portfolio Selection Sidebar
st.sidebar.header("📁 Portfolio Management")

selected_portfolio = st.sidebar.selectbox(
    "Select Portfolio:",
    options=list(st.session_state.portfolios.keys()),
    format_func=lambda x: f"{x} ({len([p for p in st.session_state.portfolios[x]['positions'] if p['quantity'] > 0])} positions)"
)

current_portfolio = st.session_state.portfolios[selected_portfolio]
st.sidebar.markdown(f"**{current_portfolio['name']}**")
st.sidebar.markdown(f"*{current_portfolio['description']}*")

# Check edit mode first
is_editing = st.session_state.edit_mode.get(selected_portfolio, False)

# Quick copy button for current portfolio
if not is_editing:
    if st.sidebar.button(f"📋 Quick Copy '{selected_portfolio}'"):
        copy_id = f"{selected_portfolio}_Copy"
        counter = 1
        while copy_id in st.session_state.portfolios:
            copy_id = f"{selected_portfolio}_Copy_{counter}"
            counter += 1
        
        new_portfolio = {
            "name": f"{current_portfolio['name']} - Copy",
            "description": f"Copy of {current_portfolio['name']}",
            "positions": copy.deepcopy(current_portfolio['positions'])
        }
        
        st.session_state.portfolios[copy_id] = new_portfolio
        st.sidebar.success(f"✅ Quick copied to '{copy_id}'")
        st.rerun()

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
        if st.button("💾 Save", type="primary"):
            # Save changes - remove backup
            st.session_state.edit_mode[selected_portfolio] = False
            if selected_portfolio in st.session_state.portfolio_backup:
                del st.session_state.portfolio_backup[selected_portfolio]
            st.sidebar.success("✅ Portfolio saved!")
            st.rerun()
    
    with col2:
        if st.button("❌ Cancel"):
            # Cancel changes - restore backup
            st.session_state.portfolios[selected_portfolio] = st.session_state.portfolio_backup[selected_portfolio]
            st.session_state.edit_mode[selected_portfolio] = False
            del st.session_state.portfolio_backup[selected_portfolio]
            st.sidebar.info("↩️ Changes cancelled")
            st.rerun()

# Copy Portfolio section (only if not editing)
if not is_editing:
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
            # Deep copy the source portfolio
            source_portfolio = st.session_state.portfolios[copy_from]
            new_portfolio = {
                "name": copy_to_name,
                "description": copy_to_desc or f"Copy of {source_portfolio['name']}",
                "positions": copy.deepcopy(source_portfolio['positions'])
            }
            
            st.session_state.portfolios[copy_to_id] = new_portfolio
            st.sidebar.success(f"✅ Copied '{copy_from}' to '{copy_to_id}' ({len(new_portfolio['positions'])} positions)")
            st.rerun()
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
            st.session_state.portfolios[new_portfolio_id] = {
                "name": new_portfolio_name,
                "description": new_portfolio_desc or "New portfolio",
                "positions": []
            }
            st.sidebar.success(f"✅ Created portfolio: {new_portfolio_id}")
            st.rerun()
        else:
            st.sidebar.error("❌ Invalid portfolio ID or already exists")

# System Status Button at bottom of sidebar
st.sidebar.markdown("---")
col1, col2 = st.sidebar.columns([1, 1])
with col1:
    if st.button("📊 Portfolio", use_container_width=True):
        st.session_state.current_page = 'portfolio'
        st.rerun()
with col2:
    if st.button("⚙️ System", use_container_width=True):
        st.session_state.current_page = 'system'
        st.rerun()

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
        st.metric("Total Portfolios", total_portfolios)
    with col2:
        st.metric("Total Positions", total_positions)
    with col3:
        st.metric("Active Positions", active_positions)
    with col4:
        st.metric("Cached Prices", len(st.session_state.portfolio_prices))
    
    # Recent Activity
    st.markdown("---")
    st.markdown("### 🕒 Recent Activity")
    
    if st.session_state.last_update:
        for portfolio_id, timestamp in st.session_state.last_update.items():
            st.write(f"**{portfolio_id}:** Last price update at {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.info("No recent price updates")
    
    st.stop()

# PORTFOLIO DASHBOARD (default page)
# Main dashboard content
if is_editing:
    st.subheader(f"✏️ Editing: {current_portfolio['name']}")
    st.info("You are in edit mode. Make changes below, then Save or Cancel in the sidebar.")
else:
    st.subheader(f"📊 {current_portfolio['name']}")

# PORTFOLIO EDITING INTERFACE
if is_editing:
    st.markdown("### 📝 Edit Portfolio Positions")
    
    # Add/Update Symbol Section
    with st.expander("➕ Add/Update Symbol", expanded=True):
        col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])
        
        with col1:
            new_symbol = st.text_input("Symbol:", placeholder="e.g., 0001.HK", key="new_symbol").upper()
        with col2:
            new_company = st.text_input("Company Name:", placeholder="Auto-fetch or enter manually", key="new_company")
        with col3:
            new_quantity = st.number_input("Quantity:", min_value=0, value=0, key="new_quantity")
        with col4:
            new_avg_cost = st.number_input("Avg Cost (HK$):", min_value=0.0, value=0.0, format="%.2f", key="new_avg_cost")
        with col5:
            new_sector = st.selectbox("Sector:", ["Tech", "Financials", "REIT", "Energy", "Other"], key="new_sector")
        
        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn1:
            if st.button("🔍 Auto-fetch Company Name"):
                if new_symbol:
                    company_name = get_company_name(new_symbol)
                    st.session_state.new_company = company_name
                    st.rerun()
        
        with col_btn2:
            if st.button("➕ Add/Update Position"):
                if new_symbol and new_quantity >= 0 and new_avg_cost >= 0:
                    # Find existing position or create new
                    positions = st.session_state.portfolios[selected_portfolio]['positions']
                    existing_idx = None
                    for i, pos in enumerate(positions):
                        if pos['symbol'] == new_symbol:
                            existing_idx = i
                            break
                    
                    new_position = {
                        "symbol": new_symbol,
                        "company_name": new_company or get_company_name(new_symbol),
                        "quantity": new_quantity,
                        "avg_cost": new_avg_cost,
                        "sector": new_sector
                    }
                    
                    if existing_idx is not None:
                        positions[existing_idx] = new_position
                        st.success(f"✅ Updated {new_symbol}")
                    else:
                        positions.append(new_position)
                        st.success(f"✅ Added {new_symbol}")
                    
                    st.rerun()
                else:
                    st.error("❌ Please fill in symbol, quantity (≥0), and avg cost (≥0)")

    # Edit Existing Positions
    st.markdown("### 📋 Current Positions (Click to Edit)")
    
    positions = st.session_state.portfolios[selected_portfolio]['positions']
    
    for i, position in enumerate(positions):
        with st.expander(f"📈 {position['symbol']} - {position['company_name'][:30]}... (Qty: {position['quantity']:,})", expanded=False):
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                edit_company = st.text_input("Company Name:", value=position['company_name'], key=f"edit_company_{i}")
            with col2:
                edit_quantity = st.number_input("Quantity:", min_value=0, value=position['quantity'], key=f"edit_quantity_{i}")
            with col3:
                edit_avg_cost = st.number_input("Avg Cost (HK$):", min_value=0.0, value=position['avg_cost'], format="%.2f", key=f"edit_avg_cost_{i}")
            with col4:
                edit_sector = st.selectbox("Sector:", ["Tech", "Financials", "REIT", "Energy", "Other"], 
                                         index=["Tech", "Financials", "REIT", "Energy", "Other"].index(position.get('sector', 'Other')),
                                         key=f"edit_sector_{i}")
            
            col_update, col_remove = st.columns([1, 1])
            with col_update:
                if st.button(f"💾 Update {position['symbol']}", key=f"update_{i}"):
                    st.session_state.portfolios[selected_portfolio]['positions'][i] = {
                        "symbol": position['symbol'],
                        "company_name": edit_company,
                        "quantity": edit_quantity,
                        "avg_cost": edit_avg_cost,
                        "sector": edit_sector
                    }
                    st.success(f"✅ Updated {position['symbol']}")
                    st.rerun()
            
            with col_remove:
                if st.button(f"🗑️ Remove {position['symbol']}", key=f"remove_{i}"):
                    st.session_state.portfolios[selected_portfolio]['positions'].pop(i)
                    st.success(f"✅ Removed {position['symbol']}")
                    st.rerun()

else:
    # NORMAL VIEWING MODE
    active_positions = [pos for pos in current_portfolio['positions'] if pos['quantity'] > 0]
    
    if not active_positions:
        st.warning("This portfolio has no active positions (quantity > 0)")
        st.stop()
    
    # Price update section
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if st.button(f"🔄 Get Real-time Data for {selected_portfolio}", type="primary"):
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
            st.rerun()
    
    with col2:
        if selected_portfolio in st.session_state.last_update:
            st.info(f"Last updated: {st.session_state.last_update[selected_portfolio].strftime('%H:%M:%S')}")
        else:
            st.info("Using default prices")
    
    with col3:
        st.metric("Active Positions", len(active_positions))
    
    # Show fetch details
    if selected_portfolio in st.session_state.fetch_details and st.session_state.fetch_details[selected_portfolio]:
        with st.expander("📋 Price Fetching Details (Click to expand)", expanded=False):
            for detail in st.session_state.fetch_details[selected_portfolio]:
                st.text(detail)
    
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

# Portfolio overview (only show if not editing)
if not is_editing:
    st.markdown("---")
    st.subheader("📊 All Portfolios Overview")
    
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
st.caption("💰 Multi-portfolio dashboard with editing • Real-time prices via Yahoo Finance API")