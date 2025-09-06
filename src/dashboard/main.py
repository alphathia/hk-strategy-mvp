"""
Main entry point for the HK Strategy Dashboard.
Handles application initialization, configuration, and high-level navigation.
"""

import streamlit as st
import logging
import sys
import os
from datetime import datetime
from typing import Optional

# Add src to path for imports
sys.path.append('src')
sys.path.append('.')

from src.dashboard.config import get_config, setup_logging, validate_environment
from src.dashboard.state_manager import SessionStateManager


class DashboardApp:
    """Main dashboard application class."""
    
    def __init__(self):
        self.config = get_config()
        self.logger = self._setup_logging()
        self.initialized = False
    
    def _setup_logging(self) -> logging.Logger:
        """Setup application logging."""
        setup_logging()
        return logging.getLogger(__name__)
    
    def initialize_app(self) -> bool:
        """Initialize the Streamlit application with configuration."""
        try:
            self.logger.info("Initializing HK Strategy Dashboard")
            
            # Validate environment
            if not validate_environment():
                st.error("❌ Missing required environment variables. Please check your configuration.")
                st.stop()
                return False
            
            # Setup Streamlit page configuration
            self.setup_page_config()
            
            # Initialize session state
            SessionStateManager.init_session_state()
            
            # Load environment and dependencies
            self.load_environment()
            
            # Initialize database connections (will be handled by session state manager)
            self._verify_database_connections()
            
            self.initialized = True
            self.logger.info("Dashboard application initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize dashboard: {str(e)}")
            st.error(f"❌ Application initialization failed: {str(e)}")
            st.stop()
            return False
    
    def setup_page_config(self) -> None:
        """Configure Streamlit page settings."""
        app_config = self.config.get('app')
        
        st.set_page_config(
            page_title=app_config['page_title'],
            page_icon=app_config['page_icon'],
            layout=app_config['layout']
        )
        
        self.logger.debug("Streamlit page configuration set")
    
    def load_environment(self) -> None:
        """Load environment variables and configuration."""
        # Environment is already loaded by config module
        # This is a placeholder for any additional environment setup
        
        if self.config.get('app', 'debug'):
            self.logger.info("Debug mode enabled")
        
        environment = self.config.get('app', 'environment')
        self.logger.info(f"Running in {environment} environment")
    
    def _verify_database_connections(self) -> None:
        """Verify database connections are working."""
        try:
            # Database connection is handled by session state manager
            # This just verifies the connections are accessible
            db_manager = st.session_state.get('db_manager')
            if db_manager:
                # Test connection
                conn = db_manager.get_connection()
                if conn:
                    self.logger.info("Database connection verified")
                    conn.close()
                else:
                    raise Exception("Failed to establish database connection")
            else:
                raise Exception("Database manager not initialized in session state")
                
        except Exception as e:
            self.logger.error(f"Database connection verification failed: {str(e)}")
            st.error(f"❌ Database connection failed: {str(e)}")
            st.error("Please check your database configuration and ensure the database is running.")
            st.stop()
    
    def render_app_header(self) -> None:
        """Render the application header and title."""
        st.title("🏦 HK Strategy Dashboard")
        st.caption("Multi-portfolio HK stock tracking system")
        
        # Show environment indicator in debug mode
        if self.config.get('app', 'debug'):
            env = self.config.get('app', 'environment')
            version = self.config.get('app', 'version')
            st.caption(f"🔧 **Environment:** {env} | **Version:** {version}")
        
        st.markdown("---")
    
    def handle_global_error(self, error: Exception) -> None:
        """Global error handler for unhandled exceptions."""
        self.logger.error(f"Unhandled application error: {str(error)}")
        st.error(f"❌ An unexpected error occurred: {str(error)}")
        
        # In debug mode, show more details
        if self.config.get('app', 'debug'):
            st.exception(error)
    
    def render_sidebar_info(self) -> None:
        """Render application info in sidebar."""
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 📊 System Info")
            
            # Show current session state summary in debug mode
            if self.config.get('app', 'debug'):
                with st.expander("🔍 Debug Info", expanded=False):
                    state_summary = SessionStateManager.get_state_summary()
                    st.json(state_summary)
            
            # Show application version
            version = self.config.get('app', 'version')
            environment = self.config.get('app', 'environment')
            st.caption(f"Version: {version}")
            st.caption(f"Environment: {environment}")
            st.caption(f"Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    def run(self) -> None:
        """Main application entry point."""
        if not self.initialized:
            if not self.initialize_app():
                return
        
        try:
            # Render application header
            self.render_app_header()
            
            # Import and run the main dashboard content
            # For now, we'll import the original dashboard logic
            # In future phases, this will be replaced with proper page routing
            self._run_legacy_dashboard()
            
            # Render sidebar info
            self.render_sidebar_info()
            
        except Exception as e:
            self.handle_global_error(e)
    
    def _run_legacy_dashboard(self) -> None:
        """Run the original dashboard content (temporary during migration)."""
        # This is a temporary approach to run the existing dashboard logic
        # while we gradually migrate to the new modular structure
        
        st.info("🚧 **Migration in Progress**: Core modules (Phase 1) have been implemented. "
               "The full dashboard will be migrated in upcoming phases.")
        
        # Show current session state for verification
        current_portfolio = SessionStateManager.get_current_portfolio()
        nav_state = SessionStateManager.get_navigation_state()
        
        st.markdown("### 🔍 Current State (Phase 1 Demo)")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Navigation State:**")
            st.json(nav_state)
        
        with col2:
            st.markdown("**Portfolio State:**")
            if current_portfolio:
                st.json({
                    'name': current_portfolio.get('name', 'Unknown'),
                    'positions_count': len(current_portfolio.get('positions', []))
                })
            else:
                st.json({'status': 'No portfolio selected'})
        
        # Add some interactive controls to test state management
        st.markdown("### 🎮 State Management Test")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🏠 Go to Overview"):
                SessionStateManager.set_current_page('overview')
                st.rerun()
        
        with col2:
            if st.button("💼 Go to Portfolio"):
                SessionStateManager.set_current_page('portfolio')
                st.rerun()
        
        with col3:
            if st.button("📈 Go to Analysis"):
                SessionStateManager.set_current_page('pv_analysis')
                st.rerun()
        
        # Show configuration summary
        with st.expander("⚙️ Configuration Summary", expanded=False):
            config_summary = {
                'Database': {
                    'Host': self.config.get('database', 'host'),
                    'Port': self.config.get('database', 'port'),
                    'Name': self.config.get('database', 'name')
                },
                'Cache': {
                    'Price Data TTL': f"{self.config.get('cache', 'price_data_ttl')} seconds",
                    'Enabled': self.config.get('cache', 'enabled')
                },
                'Charts': {
                    'Theme': self.config.get('charts', 'theme'),
                    'Default Height': self.config.get('charts', 'height_default')
                }
            }
            st.json(config_summary)


def main() -> None:
    """Main application entry point."""
    # Create and run the dashboard application
    app = DashboardApp()
    app.run()


# For direct execution and testing
if __name__ == "__main__":
    main()