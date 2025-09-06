"""
Base Form Component for HK Strategy Dashboard.

Provides abstract base class for all form components with validation.
Ensures consistent form behavior and validation patterns.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Tuple, Callable
import streamlit as st
import logging

# Setup logging
logger = logging.getLogger(__name__)


class BaseForm(ABC):
    """
    Abstract base class for all form components.
    
    Provides common functionality for form rendering, validation,
    and submission handling.
    """
    
    def __init__(self, form_key: str, title: str = None, submit_label: str = "Submit"):
        """
        Initialize base form.
        
        Args:
            form_key: Unique form key for Streamlit
            title: Form title (optional)
            submit_label: Submit button label
        """
        self.form_key = form_key
        self.title = title
        self.submit_label = submit_label
        self.data = {}
        self.errors = []
        self._callback: Optional[Callable] = None
        
    @abstractmethod
    def render_fields(self) -> Dict[str, Any]:
        """
        Render form fields.
        
        This method must be implemented by subclasses to define
        the specific form fields and collect user input.
        
        Returns:
            Dict containing form field values
        """
        pass
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate form data.
        
        Override this method in subclasses for custom validation.
        
        Args:
            data: Form data to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        # Default implementation - no validation
        return True, []
    
    def set_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Set callback function to execute on successful form submission.
        
        Args:
            callback: Function to call with form data
        """
        self._callback = callback
    
    def render_title(self) -> None:
        """Render form title if provided."""
        if self.title:
            st.markdown(f"### {self.title}")
    
    def render_errors(self) -> None:
        """Render validation errors."""
        for error in self.errors:
            st.error(error)
    
    def on_submit(self, data: Dict[str, Any]) -> bool:
        """
        Handle form submission.
        
        Args:
            data: Form data
            
        Returns:
            True if submission successful, False otherwise
        """
        try:
            # Validate data
            is_valid, errors = self.validate(data)
            
            if not is_valid:
                self.errors = errors
                return False
            
            # Clear previous errors
            self.errors = []
            
            # Execute callback if provided
            if self._callback:
                self._callback(data)
            
            # Store data
            self.data = data
            
            logger.info(f"Form {self.form_key} submitted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Form submission error: {str(e)}")
            self.errors = [f"Submission error: {str(e)}"]
            return False
    
    def render(self) -> Optional[Dict[str, Any]]:
        """
        Render the complete form.
        
        Returns:
            Form data if submitted successfully, None otherwise
        """
        try:
            # Render title
            self.render_title()
            
            # Render form
            with st.form(self.form_key, clear_on_submit=False):
                # Render form fields
                data = self.render_fields()
                
                # Submit button
                submitted = st.form_submit_button(self.submit_label, type="primary")
                
                if submitted:
                    if self.on_submit(data):
                        # Success
                        return data
            
            # Render errors outside form
            self.render_errors()
            
            return None
            
        except Exception as e:
            logger.error(f"Form rendering error: {str(e)}")
            st.error(f"Form error: {str(e)}")
            return None
    
    def reset(self) -> None:
        """Reset form data and errors."""
        self.data = {}
        self.errors = []
    
    def get_data(self) -> Dict[str, Any]:
        """Get current form data."""
        return self.data.copy()
    
    def get_errors(self) -> List[str]:
        """Get current form errors."""
        return self.errors.copy()
    
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


class ValidationMixin:
    """Mixin class providing common validation methods."""
    
    @staticmethod
    def validate_required(value: Any, field_name: str) -> Optional[str]:
        """
        Validate required field.
        
        Args:
            value: Field value
            field_name: Field name for error message
            
        Returns:
            Error message if invalid, None if valid
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            return f"{field_name} is required"
        return None
    
    @staticmethod
    def validate_email(email: str) -> Optional[str]:
        """
        Validate email format.
        
        Args:
            email: Email to validate
            
        Returns:
            Error message if invalid, None if valid
        """
        import re
        
        if not email:
            return None
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return "Invalid email format"
        
        return None
    
    @staticmethod
    def validate_number(value: Any, field_name: str, min_val: float = None, 
                       max_val: float = None) -> Optional[str]:
        """
        Validate numeric value.
        
        Args:
            value: Value to validate
            field_name: Field name for error message
            min_val: Minimum value (optional)
            max_val: Maximum value (optional)
            
        Returns:
            Error message if invalid, None if valid
        """
        try:
            num_val = float(value)
            
            if min_val is not None and num_val < min_val:
                return f"{field_name} must be at least {min_val}"
            
            if max_val is not None and num_val > max_val:
                return f"{field_name} must be at most {max_val}"
            
            return None
            
        except (ValueError, TypeError):
            return f"{field_name} must be a number"
    
    @staticmethod
    def validate_symbol(symbol: str) -> Optional[str]:
        """
        Validate stock symbol format.
        
        Args:
            symbol: Symbol to validate
            
        Returns:
            Error message if invalid, None if valid
        """
        if not symbol:
            return "Symbol is required"
        
        # Basic symbol validation
        symbol = symbol.strip().upper()
        
        # Check length
        if len(symbol) < 1 or len(symbol) > 10:
            return "Symbol must be 1-10 characters"
        
        # Check for valid characters (letters, numbers, dots, hyphens)
        import re
        if not re.match(r'^[A-Z0-9.-]+$', symbol):
            return "Symbol contains invalid characters"
        
        return None