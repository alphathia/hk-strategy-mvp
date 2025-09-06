"""
Base Dialog Component for HK Strategy Dashboard.

Provides abstract base class for all modal dialog components.
Ensures consistent interface and behavior across all dialogs.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable
import streamlit as st
import logging

# Setup logging
logger = logging.getLogger(__name__)


class BaseDialog(ABC):
    """
    Abstract base class for all modal dialog components.
    
    Provides common functionality for Streamlit @st.dialog decorated functions
    including title management, content rendering, and result handling.
    """
    
    def __init__(self, title: str, width: str = "small"):
        """
        Initialize base dialog.
        
        Args:
            title: Dialog title to display
            width: Dialog width ("small", "medium", "large")
        """
        self.title = title
        self.width = width
        self.result = None
        self._callback: Optional[Callable] = None
        
    @abstractmethod
    def render_content(self) -> Optional[Dict[str, Any]]:
        """
        Render the dialog content.
        
        This method must be implemented by subclasses to define
        the specific UI elements and logic for each dialog.
        
        Returns:
            Dict containing dialog result data, or None if no action taken
        """
        pass
    
    def set_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Set callback function to execute on dialog completion.
        
        Args:
            callback: Function to call with dialog result
        """
        self._callback = callback
    
    def render_header(self) -> None:
        """Render dialog header with title."""
        st.markdown(f"**{self.title}**")
        st.markdown("---")
    
    def render_footer(self) -> None:
        """Render dialog footer (can be overridden by subclasses)."""
        # Default implementation - no footer
        pass
    
    def validate_data(self, data: Dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate dialog data.
        
        Args:
            data: Data to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        # Default implementation - no validation
        return True, []
    
    def on_submit(self, data: Dict[str, Any]) -> bool:
        """
        Handle dialog submission.
        
        Args:
            data: Dialog form data
            
        Returns:
            True if submission successful, False otherwise
        """
        try:
            # Validate data
            is_valid, errors = self.validate_data(data)
            
            if not is_valid:
                for error in errors:
                    st.error(error)
                return False
            
            # Execute callback if provided
            if self._callback:
                self._callback(data)
            
            # Store result
            self.result = data
            
            logger.info(f"Dialog {self.__class__.__name__} submitted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Dialog submission error: {str(e)}")
            st.error(f"Error: {str(e)}")
            return False
    
    def render(self) -> Optional[Dict[str, Any]]:
        """
        Render the complete dialog.
        
        This is the main entry point that orchestrates the dialog rendering.
        It calls render_header(), render_content(), and render_footer() in sequence.
        
        Returns:
            Dialog result data or None
        """
        try:
            # Render dialog header
            self.render_header()
            
            # Render main content
            result = self.render_content()
            
            # Render footer
            self.render_footer()
            
            # Handle submission if result provided
            if result is not None:
                if self.on_submit(result):
                    return result
            
            return None
            
        except Exception as e:
            logger.error(f"Dialog rendering error: {str(e)}")
            st.error(f"Dialog error: {str(e)}")
            return None
    
    def close(self) -> None:
        """Close the dialog (rerun to dismiss)."""
        st.rerun()
    
    def show_success(self, message: str) -> None:
        """Show success message."""
        st.success(message)
    
    def show_error(self, message: str) -> None:
        """Show error message."""
        st.error(message)
    
    def show_warning(self, message: str) -> None:
        """Show warning message."""
        st.warning(message)
    
    def show_info(self, message: str) -> None:
        """Show info message."""
        st.info(message)


# Decorator factory for creating dialog decorators
def dialog_component(title: str, width: str = "small"):
    """
    Decorator factory for creating Streamlit dialog components.
    
    This creates the @st.dialog decorator wrapper around dialog components.
    
    Args:
        title: Dialog title
        width: Dialog width
        
    Returns:
        Decorator function
    """
    def decorator(dialog_class):
        """Decorator that wraps dialog class with @st.dialog."""
        
        @st.dialog(title, width=width)
        def dialog_wrapper(*args, **kwargs):
            """Wrapper function for @st.dialog decorator."""
            dialog_instance = dialog_class(*args, **kwargs)
            return dialog_instance.render()
        
        # Attach the wrapper to the class for easy access
        dialog_class._streamlit_dialog = dialog_wrapper
        return dialog_class
    
    return decorator