"""
Status Widget Components.

Widgets for displaying system status, health indicators, and progress.
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Union
import logging
from datetime import datetime, timedelta
import time

from .base_widget import BaseWidget
from src.utils.data_utils import get_company_name

logger = logging.getLogger(__name__)


class StatusWidget(BaseWidget):
    """
    Widget for displaying status information with indicators.
    """
    
    def __init__(self, widget_id: str, status: str = "unknown", 
                 message: str = "", details: List[str] = None, 
                 title: str = "Status"):
        """
        Initialize status widget.
        
        Args:
            widget_id: Unique widget identifier
            status: Status level ('success', 'warning', 'error', 'info', 'unknown')
            message: Status message
            details: List of detail messages
            title: Widget title
        """
        super().__init__(widget_id, title)
        self.status = status
        self.message = message
        self.details = details or []
    
    def render_content(self) -> Dict[str, Any]:
        """
        Render status widget content.
        
        Returns:
            Widget render data
        """
        try:
            # Status icon and color mapping
            status_config = {
                'success': {'icon': '✅', 'color': 'green', 'func': st.success},
                'warning': {'icon': '⚠️', 'color': 'orange', 'func': st.warning},
                'error': {'icon': '❌', 'color': 'red', 'func': st.error},
                'info': {'icon': 'ℹ️', 'color': 'blue', 'func': st.info},
                'unknown': {'icon': '❓', 'color': 'gray', 'func': st.info}
            }
            
            config = status_config.get(self.status, status_config['unknown'])
            
            # Display main status
            if self.message:
                status_text = f"{config['icon']} {self.message}"
                config['func'](status_text)
            
            # Display details if available
            if self.details:
                with st.expander("📋 Details", expanded=False):
                    for detail in self.details:
                        st.write(f"• {detail}")
            
            return {
                'widget_type': 'status',
                'status': self.status,
                'message': self.message,
                'details_count': len(self.details)
            }
            
        except Exception as e:
            logger.error(f"Error rendering status widget {self.widget_id}: {e}")
            st.error("Error displaying status")
            return {}


class SystemHealthWidget(BaseWidget):
    """
    Widget for displaying system health and connectivity status.
    """
    
    def __init__(self, widget_id: str, title: str = "System Health"):
        """
        Initialize system health widget.
        
        Args:
            widget_id: Unique widget identifier
            title: Widget title
        """
        super().__init__(widget_id, title)
    
    def render_content(self) -> Dict[str, Any]:
        """
        Render system health content.
        
        Returns:
            Widget render data
        """
        try:
            st.markdown("### 🏥 System Health")
            
            # Check various system components
            health_checks = self._perform_health_checks()
            
            # Overall status
            overall_status = self._determine_overall_status(health_checks)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Overall status indicator
                if overall_status == 'healthy':
                    st.success("🟢 **System Healthy**")
                elif overall_status == 'warning':
                    st.warning("🟡 **System Issues**")
                else:
                    st.error("🔴 **System Problems**")
            
            with col2:
                # Last check time
                current_time = datetime.now().strftime("%H:%M:%S")
                st.info(f"🕐 **Last Check**: {current_time}")
            
            # Detailed status
            with st.expander("🔍 Detailed Status", expanded=overall_status != 'healthy'):
                for check in health_checks:
                    self._render_health_check(check)
            
            return {
                'widget_type': 'system_health',
                'overall_status': overall_status,
                'checks_count': len(health_checks),
                'healthy_checks': sum(1 for c in health_checks if c['status'] == 'success'),
                'failed_checks': sum(1 for c in health_checks if c['status'] == 'error')
            }
            
        except Exception as e:
            logger.error(f"Error rendering system health widget {self.widget_id}: {e}")
            st.error("Error displaying system health")
            return {}
    
    def _perform_health_checks(self) -> List[Dict[str, Any]]:
        """
        Perform various system health checks.
        
        Returns:
            List of health check results
        """
        checks = []
        
        # Database connectivity check
        try:
            from src.database.connection import get_connection
            conn = get_connection()
            if conn:
                checks.append({
                    'name': 'Database Connection',
                    'status': 'success',
                    'message': 'Connected successfully',
                    'details': []
                })
                conn.close()
            else:
                checks.append({
                    'name': 'Database Connection',
                    'status': 'error',
                    'message': 'Failed to connect',
                    'details': ['Check database credentials', 'Verify database is running']
                })
        except Exception as e:
            checks.append({
                'name': 'Database Connection',
                'status': 'error',
                'message': f'Connection error: {str(e)}',
                'details': ['Check database configuration']
            })
        
        # Yahoo Finance API check
        try:
            # Test with a known symbol
            import yfinance as yf
            ticker = yf.Ticker("AAPL")
            info = ticker.info
            if info and len(info) > 1:
                checks.append({
                    'name': 'Yahoo Finance API',
                    'status': 'success',
                    'message': 'API accessible',
                    'details': []
                })
            else:
                checks.append({
                    'name': 'Yahoo Finance API',
                    'status': 'warning',
                    'message': 'Limited response from API',
                    'details': ['May experience data delays']
                })
        except Exception as e:
            checks.append({
                'name': 'Yahoo Finance API',
                'status': 'error',
                'message': f'API error: {str(e)}',
                'details': ['Check internet connection', 'API may be temporarily unavailable']
            })
        
        # Session state check
        try:
            if hasattr(st, 'session_state'):
                session_keys = len(st.session_state.keys()) if hasattr(st.session_state, 'keys') else 0
                checks.append({
                    'name': 'Session State',
                    'status': 'success',
                    'message': f'Active with {session_keys} keys',
                    'details': []
                })
            else:
                checks.append({
                    'name': 'Session State',
                    'status': 'error',
                    'message': 'Session state not available',
                    'details': ['Streamlit session may be corrupted']
                })
        except Exception as e:
            checks.append({
                'name': 'Session State',
                'status': 'warning',
                'message': f'Session state issue: {str(e)}',
                'details': []
            })
        
        # Configuration check
        try:
            from src.core.config import get_config
            config = get_config()
            if config:
                checks.append({
                    'name': 'Configuration',
                    'status': 'success',
                    'message': 'Configuration loaded',
                    'details': []
                })
            else:
                checks.append({
                    'name': 'Configuration',
                    'status': 'error',
                    'message': 'Failed to load configuration',
                    'details': ['Check config files']
                })
        except Exception as e:
            checks.append({
                'name': 'Configuration',
                'status': 'error',
                'message': f'Config error: {str(e)}',
                'details': ['Check configuration files']
            })
        
        return checks
    
    def _determine_overall_status(self, health_checks: List[Dict[str, Any]]) -> str:
        """
        Determine overall system status from individual checks.
        
        Args:
            health_checks: List of health check results
            
        Returns:
            Overall status ('healthy', 'warning', 'error')
        """
        if not health_checks:
            return 'error'
        
        error_count = sum(1 for c in health_checks if c['status'] == 'error')
        warning_count = sum(1 for c in health_checks if c['status'] == 'warning')
        
        if error_count > 0:
            return 'error'
        elif warning_count > 0:
            return 'warning'
        else:
            return 'healthy'
    
    def _render_health_check(self, check: Dict[str, Any]) -> None:
        """
        Render individual health check result.
        
        Args:
            check: Health check result dictionary
        """
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if check['status'] == 'success':
                st.success("✅")
            elif check['status'] == 'warning':
                st.warning("⚠️")
            else:
                st.error("❌")
        
        with col2:
            st.write(f"**{check['name']}**: {check['message']}")
            if check.get('details'):
                for detail in check['details']:
                    st.write(f"  • {detail}")


class ProgressWidget(BaseWidget):
    """
    Widget for displaying progress indicators and loading states.
    """
    
    def __init__(self, widget_id: str, progress: float = 0, 
                 message: str = "", show_percentage: bool = True,
                 title: str = "Progress"):
        """
        Initialize progress widget.
        
        Args:
            widget_id: Unique widget identifier
            progress: Progress value (0.0 to 1.0)
            message: Progress message
            show_percentage: Show percentage text
            title: Widget title
        """
        super().__init__(widget_id, title)
        self.progress = max(0.0, min(1.0, progress))
        self.message = message
        self.show_percentage = show_percentage
    
    def render_content(self) -> Dict[str, Any]:
        """
        Render progress widget content.
        
        Returns:
            Widget render data
        """
        try:
            # Progress message
            if self.message:
                st.write(self.message)
            
            # Progress bar
            progress_bar = st.progress(self.progress)
            
            # Percentage text
            if self.show_percentage:
                percentage = self.progress * 100
                st.write(f"Progress: {percentage:.1f}%")
            
            return {
                'widget_type': 'progress',
                'progress': self.progress,
                'percentage': self.progress * 100,
                'message': self.message
            }
            
        except Exception as e:
            logger.error(f"Error rendering progress widget {self.widget_id}: {e}")
            st.error("Error displaying progress")
            return {}
    
    def update_progress(self, new_progress: float, new_message: str = None) -> None:
        """
        Update progress value and message.
        
        Args:
            new_progress: New progress value (0.0 to 1.0)
            new_message: New progress message (optional)
        """
        self.progress = max(0.0, min(1.0, new_progress))
        if new_message is not None:
            self.message = new_message
        
        # Store in session state for persistence
        self.set_state('progress', self.progress)
        if new_message is not None:
            self.set_state('message', self.message)


class LoadingWidget(BaseWidget):
    """
    Widget for displaying loading states and spinners.
    """
    
    def __init__(self, widget_id: str, message: str = "Loading...", 
                 show_spinner: bool = True, title: str = None):
        """
        Initialize loading widget.
        
        Args:
            widget_id: Unique widget identifier
            message: Loading message
            show_spinner: Show spinner animation
            title: Widget title
        """
        super().__init__(widget_id, title)
        self.message = message
        self.show_spinner = show_spinner
    
    def render_content(self) -> Dict[str, Any]:
        """
        Render loading widget content.
        
        Returns:
            Widget render data
        """
        try:
            if self.show_spinner:
                with st.spinner(self.message):
                    # Simulate some loading time for visual effect
                    time.sleep(0.1)
            else:
                st.info(f"⏳ {self.message}")
            
            return {
                'widget_type': 'loading',
                'message': self.message,
                'show_spinner': self.show_spinner
            }
            
        except Exception as e:
            logger.error(f"Error rendering loading widget {self.widget_id}: {e}")
            st.error("Error displaying loading indicator")
            return {}


class ConnectivityWidget(BaseWidget):
    """
    Widget for displaying connectivity status to external services.
    """
    
    def __init__(self, widget_id: str, title: str = "Connectivity Status"):
        """
        Initialize connectivity widget.
        
        Args:
            widget_id: Unique widget identifier
            title: Widget title
        """
        super().__init__(widget_id, title)
    
    def render_content(self) -> Dict[str, Any]:
        """
        Render connectivity widget content.
        
        Returns:
            Widget render data
        """
        try:
            st.markdown("### 🌐 Connectivity")
            
            # Test connections to various services
            connections = self._test_connections()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**External Services:**")
                for conn in connections:
                    status_icon = "🟢" if conn['status'] else "🔴"
                    latency_text = f"({conn['latency']:.0f}ms)" if conn['latency'] else ""
                    st.write(f"{status_icon} {conn['name']} {latency_text}")
            
            with col2:
                # Summary statistics
                total_services = len(connections)
                available_services = sum(1 for c in connections if c['status'])
                avg_latency = sum(c['latency'] for c in connections if c['latency']) / len([c for c in connections if c['latency']]) if connections else 0
                
                st.metric("Services Available", f"{available_services}/{total_services}")
                if avg_latency > 0:
                    st.metric("Avg Latency", f"{avg_latency:.0f}ms")
            
            return {
                'widget_type': 'connectivity',
                'total_services': total_services,
                'available_services': available_services,
                'avg_latency': avg_latency,
                'connections': connections
            }
            
        except Exception as e:
            logger.error(f"Error rendering connectivity widget {self.widget_id}: {e}")
            st.error("Error displaying connectivity status")
            return {}
    
    def _test_connections(self) -> List[Dict[str, Any]]:
        """
        Test connections to external services.
        
        Returns:
            List of connection test results
        """
        connections = []
        
        # Yahoo Finance API
        try:
            start_time = time.time()
            import yfinance as yf
            ticker = yf.Ticker("AAPL")
            info = ticker.info
            latency = (time.time() - start_time) * 1000
            
            connections.append({
                'name': 'Yahoo Finance',
                'status': bool(info and len(info) > 1),
                'latency': latency
            })
        except Exception:
            connections.append({
                'name': 'Yahoo Finance',
                'status': False,
                'latency': None
            })
        
        # Database connection
        try:
            start_time = time.time()
            from src.database.connection import get_connection
            conn = get_connection()
            latency = (time.time() - start_time) * 1000
            
            connections.append({
                'name': 'Database',
                'status': bool(conn),
                'latency': latency if conn else None
            })
            
            if conn:
                conn.close()
        except Exception:
            connections.append({
                'name': 'Database',
                'status': False,
                'latency': None
            })
        
        return connections


class NotificationWidget(BaseWidget):
    """
    Widget for displaying notifications and alerts.
    """
    
    def __init__(self, widget_id: str, notifications: List[Dict[str, Any]], 
                 title: str = "Notifications", max_display: int = 5):
        """
        Initialize notification widget.
        
        Args:
            widget_id: Unique widget identifier
            notifications: List of notification dictionaries
            title: Widget title
            max_display: Maximum notifications to display
        """
        super().__init__(widget_id, title)
        self.notifications = notifications[-max_display:] if notifications else []
        self.max_display = max_display
    
    def render_content(self) -> Dict[str, Any]:
        """
        Render notifications content.
        
        Returns:
            Widget render data
        """
        try:
            if not self.notifications:
                st.info("No notifications")
                return {'widget_type': 'notifications', 'count': 0}
            
            st.markdown(f"### 🔔 {self.title} ({len(self.notifications)})")
            
            for i, notification in enumerate(self.notifications):
                self._render_notification(notification, i)
            
            # Clear notifications button
            if st.button("🗑️ Clear All", key=f"{self.state_key}_clear"):
                self.notifications.clear()
                self.set_state('notifications', [])
                st.rerun()
            
            return {
                'widget_type': 'notifications',
                'count': len(self.notifications)
            }
            
        except Exception as e:
            logger.error(f"Error rendering notification widget {self.widget_id}: {e}")
            st.error("Error displaying notifications")
            return {'widget_type': 'notifications', 'count': 0}
    
    def _render_notification(self, notification: Dict[str, Any], index: int) -> None:
        """
        Render individual notification.
        
        Args:
            notification: Notification data
            index: Notification index
        """
        level = notification.get('level', 'info')
        message = notification.get('message', '')
        timestamp = notification.get('timestamp', '')
        
        # Container for notification
        with st.container():
            col1, col2, col3 = st.columns([6, 2, 1])
            
            with col1:
                # Message with level styling
                if level == 'error':
                    st.error(f"❌ {message}")
                elif level == 'warning':
                    st.warning(f"⚠️ {message}")
                elif level == 'success':
                    st.success(f"✅ {message}")
                else:
                    st.info(f"ℹ️ {message}")
            
            with col2:
                if timestamp:
                    st.write(f"🕐 {timestamp}")
            
            with col3:
                if st.button("❌", key=f"{self.state_key}_dismiss_{index}", help="Dismiss"):
                    # Remove this notification
                    self.notifications.pop(index)
                    self.set_state('notifications', self.notifications)
                    st.rerun()
            
            st.divider()
    
    def add_notification(self, message: str, level: str = 'info', 
                        timestamp: str = None) -> None:
        """
        Add new notification.
        
        Args:
            message: Notification message
            level: Notification level ('info', 'success', 'warning', 'error')
            timestamp: Notification timestamp
        """
        if not timestamp:
            timestamp = datetime.now().strftime("%H:%M:%S")
        
        notification = {
            'message': message,
            'level': level,
            'timestamp': timestamp
        }
        
        self.notifications.append(notification)
        
        # Keep only the latest notifications
        if len(self.notifications) > self.max_display:
            self.notifications = self.notifications[-self.max_display:]
        
        # Store in session state
        self.set_state('notifications', self.notifications)