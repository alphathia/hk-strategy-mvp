"""
System Status Page for HK Strategy Dashboard.
Provides system health monitoring, database status, and administrative tools.

Extracted from dashboard.py lines 2648-2832
"""

import os
import sys
import platform
import subprocess
import urllib.request
from typing import Dict, List, Any, Optional
import streamlit as st
import pandas as pd
import yfinance as yf

from .base_page import BasePage
from ..config.config_manager import get_config, ConfigurationError


class SystemStatusPage(BasePage):
    """System status and health monitoring page."""
    
    def __init__(self):
        """Initialize system status page."""
        super().__init__('system_status')
        
    def _render_content(self) -> None:
        """Render the system status page content."""
        st.title("⚙️ System Status Dashboard")
        st.markdown("---")
        
        # Refresh button
        if st.button("🔄 Refresh All Checks", type="primary"):
            st.rerun()
        
        # System Health Checks
        st.markdown("### 🏥 System Health Checks")
        
        # Database check
        self._render_database_status()
        
        # Redis check
        self._render_redis_status()
        
        # Yahoo Finance API check
        self._render_yfinance_status()
        
        st.markdown("---")
        
        # System Information
        self._render_system_information()
        
        # Portfolio Statistics
        self._render_portfolio_statistics()
        
        # Recent Activity
        self._render_recent_activity()
        
    def _render_database_status(self) -> None:
        """Render database health status section."""
        with st.container():
            st.subheader("🗄️ PostgreSQL Database")
            with st.spinner("Checking database connectivity..."):
                db_results = self._check_database_health()
            
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
    
    def _render_redis_status(self) -> None:
        """Render Redis health status section."""
        with st.container():
            st.subheader("🔄 Redis Cache")
            with st.spinner("Checking Redis connectivity..."):
                redis_results = self._check_redis_health()
            
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
    
    def _render_yfinance_status(self) -> None:
        """Render Yahoo Finance API status section."""
        with st.container():
            st.subheader("📈 Yahoo Finance API")
            with st.spinner("Checking Yahoo Finance API..."):
                yf_results = self._check_yfinance_health()
            
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
    
    def _render_system_information(self) -> None:
        """Render system information section."""
        st.markdown("### 💻 System Information")
        system_info = self._get_system_info()
        
        info_cols = st.columns(2)
        items = list(system_info.items())
        mid_point = len(items) // 2
        
        with info_cols[0]:
            for key, value in items[:mid_point]:
                st.write(f"**{key}:** {value}")
        
        with info_cols[1]:
            for key, value in items[mid_point:]:
                st.write(f"**{key}:** {value}")
    
    def _render_portfolio_statistics(self) -> None:
        """Render portfolio statistics section."""
        st.markdown("---")
        st.markdown("### 📊 Portfolio Statistics")
        
        total_portfolios = len(st.session_state.portfolios) if hasattr(st.session_state, 'portfolios') and st.session_state.portfolios else 0
        
        if total_portfolios > 0:
            total_positions = sum(len(p['positions']) for p in st.session_state.portfolios.values())
            active_positions = sum(len([pos for pos in p['positions'] if pos['quantity'] > 0]) for p in st.session_state.portfolios.values())
            cached_prices = len(st.session_state.portfolio_prices) if hasattr(st.session_state, 'portfolio_prices') and st.session_state.portfolio_prices else 0
        else:
            total_positions = 0
            active_positions = 0
            cached_prices = 0
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Portfolios", total_portfolios, help="Number of portfolios in your system")
        with col2:
            st.metric("Total Positions", total_positions, help="Number of unique stock symbols across all portfolios (no duplicates)")
        with col3:
            st.metric("Active Positions", active_positions, help="Number of unique symbols with quantity > 0 across all portfolios")
        with col4:
            st.metric("Cached Prices", cached_prices, help="Number of portfolios with cached price data")
    
    def _render_recent_activity(self) -> None:
        """Render recent activity section."""
        st.markdown("---")
        st.markdown("### 🕒 Recent Activity")
        
        if hasattr(st.session_state, 'last_update') and st.session_state.last_update:
            for portfolio_id, timestamp in st.session_state.last_update.items():
                st.write(f"**{portfolio_id}:** Last price update at {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            st.info("No recent price updates")
    
    def _check_database_health(self) -> Dict[str, Any]:
        """Check PostgreSQL database connectivity with detailed diagnostics."""
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
                import psycopg2
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
                
            except Exception as e:
                error_msg = str(e)
                results["details"].append(f"❌ Failed {desc}: {error_msg}")
                
                if "password authentication failed" in error_msg:
                    results["troubleshooting"].append(f"Fix authentication for {conn_str.split('@')[0]}")
                elif "does not exist" in error_msg:
                    results["troubleshooting"].append("Create missing user/database")
                elif "could not connect" in error_msg:
                    results["troubleshooting"].append("Check PostgreSQL service is running")
        
        results["message"] = "All connection attempts failed"
        results["troubleshooting"].extend([
            "1. Check PostgreSQL is installed and running",
            "2. Create hk_strategy database and user", 
            "3. Run setup commands in terminal"
        ])
        
        return results
    
    def _check_redis_health(self) -> Dict[str, Any]:
        """Check Redis connectivity with detailed diagnostics."""
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
            import redis
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
                
        except Exception as e:
            import redis
            error_msg = str(e)
            if isinstance(e, redis.ConnectionError):
                results["details"].append(f"❌ Connection error: {error_msg}")
                results["message"] = "Cannot connect to Redis server"
                results["troubleshooting"].extend([
                    "Check Redis is installed: redis-server --version",
                    "Start Redis: sudo systemctl start redis",
                    "Check port 6379 is available: netstat -tlnp | grep 6379"
                ])
            elif isinstance(e, redis.AuthenticationError):
                results["details"].append(f"❌ Authentication error: {error_msg}")
                results["message"] = "Redis authentication failed"
                results["troubleshooting"].append("Check Redis password configuration")
            else:
                results["details"].append(f"❌ Unexpected error: {error_msg}")
                results["message"] = f"Redis check failed: {error_msg}"
                results["troubleshooting"].append("Check Redis configuration and logs")
        
        return results
    
    def _check_yfinance_health(self) -> Dict[str, Any]:
        """Check Yahoo Finance API connectivity with detailed diagnostics."""
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
    
    def _get_system_info(self) -> Dict[str, str]:
        """Get system information."""
        try:
            return {
                "Python Version": f"{sys.version.split()[0]}",
                "Platform": platform.platform(),
                "Streamlit Version": st.__version__,
                "Pandas Version": pd.__version__,
                "YFinance Version": yf.__version__ if hasattr(yf, '__version__') else "Unknown",
                "Working Directory": os.getcwd(),
                "Process ID": str(os.getpid())
            }
        except Exception as e:
            return {"Error": str(e)}