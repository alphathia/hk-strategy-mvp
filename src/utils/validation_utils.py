"""
Validation Utilities.

Common validation functions for forms, data, and user input.
Extracted from dashboard.py and form components for modular architecture.
"""

import re
from typing import Optional, List, Any, Tuple
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


def validate_required(value: Any, field_name: str) -> Optional[str]:
    """
    Validate that a required field has a value.
    
    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        
    Returns:
        Error message if invalid, None if valid
    """
    if value is None:
        return f"{field_name} is required"
    
    if isinstance(value, str) and not value.strip():
        return f"{field_name} is required"
    
    return None


def validate_number(value: str, field_name: str, min_val: float = None, 
                   max_val: float = None, allow_zero: bool = True) -> Optional[str]:
    """
    Validate numeric input.
    
    Args:
        value: String value to validate
        field_name: Name of the field for error messages
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        allow_zero: Whether zero is allowed
        
    Returns:
        Error message if invalid, None if valid
    """
    if not value or not value.strip():
        return f"{field_name} is required"
    
    try:
        num_value = float(value.strip())
        
        if not allow_zero and num_value == 0:
            return f"{field_name} cannot be zero"
        
        if min_val is not None and num_value < min_val:
            return f"{field_name} must be at least {min_val}"
        
        if max_val is not None and num_value > max_val:
            return f"{field_name} cannot exceed {max_val}"
        
        return None
        
    except ValueError:
        return f"{field_name} must be a valid number"


def validate_integer(value: str, field_name: str, min_val: int = None, 
                    max_val: int = None) -> Optional[str]:
    """
    Validate integer input.
    
    Args:
        value: String value to validate
        field_name: Name of the field for error messages
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        Error message if invalid, None if valid
    """
    if not value or not value.strip():
        return f"{field_name} is required"
    
    try:
        int_value = int(float(value.strip()))  # Handle "100.0" -> 100
        
        if min_val is not None and int_value < min_val:
            return f"{field_name} must be at least {min_val}"
        
        if max_val is not None and int_value > max_val:
            return f"{field_name} cannot exceed {max_val}"
        
        return None
        
    except ValueError:
        return f"{field_name} must be a valid whole number"


def validate_symbol(symbol: str) -> Optional[str]:
    """
    Validate stock symbol format.
    
    Args:
        symbol: Stock symbol to validate
        
    Returns:
        Error message if invalid, None if valid
    """
    if not symbol or not symbol.strip():
        return "Symbol is required"
    
    symbol = symbol.strip().upper()
    
    # Check length
    if len(symbol) > 10:
        return "Symbol cannot exceed 10 characters"
    
    if len(symbol) < 1:
        return "Symbol must have at least 1 character"
    
    # Check for valid characters (letters, numbers, dots)
    if not re.match(r'^[A-Z0-9.]+$', symbol):
        return "Symbol can only contain letters, numbers, and dots"
    
    return None


def validate_email(email: str) -> Optional[str]:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        Error message if invalid, None if valid
    """
    if not email or not email.strip():
        return None  # Email is optional in most cases
    
    email = email.strip().lower()
    
    # Basic email regex pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        return "Please enter a valid email address"
    
    return None


def validate_date(date_str: str, field_name: str = "Date") -> Optional[str]:
    """
    Validate date string format.
    
    Args:
        date_str: Date string to validate (YYYY-MM-DD)
        field_name: Name of the field for error messages
        
    Returns:
        Error message if invalid, None if valid
    """
    if not date_str or not date_str.strip():
        return f"{field_name} is required"
    
    try:
        datetime.strptime(date_str.strip(), '%Y-%m-%d')
        return None
    except ValueError:
        return f"{field_name} must be in YYYY-MM-DD format"


def validate_date_range(start_date: str, end_date: str) -> Optional[str]:
    """
    Validate date range.
    
    Args:
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)
        
    Returns:
        Error message if invalid, None if valid
    """
    # First validate individual dates
    start_error = validate_date(start_date, "Start date")
    if start_error:
        return start_error
    
    end_error = validate_date(end_date, "End date")
    if end_error:
        return end_error
    
    try:
        start = datetime.strptime(start_date.strip(), '%Y-%m-%d').date()
        end = datetime.strptime(end_date.strip(), '%Y-%m-%d').date()
        
        if start > end:
            return "Start date must be before end date"
        
        if end > date.today():
            return "End date cannot be in the future"
        
        # Check for reasonable range (not more than 5 years)
        if (end - start).days > 365 * 5:
            return "Date range cannot exceed 5 years"
        
        return None
        
    except ValueError as e:
        return f"Invalid date range: {e}"


def validate_portfolio_id(portfolio_id: str) -> Optional[str]:
    """
    Validate portfolio ID format.
    
    Args:
        portfolio_id: Portfolio ID to validate
        
    Returns:
        Error message if invalid, None if valid
    """
    if not portfolio_id or not portfolio_id.strip():
        return "Portfolio ID is required"
    
    portfolio_id = portfolio_id.strip().upper()
    
    # Check length
    if len(portfolio_id) > 20:
        return "Portfolio ID cannot exceed 20 characters"
    
    if len(portfolio_id) < 2:
        return "Portfolio ID must have at least 2 characters"
    
    # Check for valid characters (letters, numbers, underscores, hyphens)
    if not re.match(r'^[A-Z0-9_-]+$', portfolio_id):
        return "Portfolio ID can only contain letters, numbers, underscores, and hyphens"
    
    return None


def validate_portfolio_name(name: str) -> Optional[str]:
    """
    Validate portfolio name.
    
    Args:
        name: Portfolio name to validate
        
    Returns:
        Error message if invalid, None if valid
    """
    if not name or not name.strip():
        return "Portfolio name is required"
    
    name = name.strip()
    
    # Check length
    if len(name) > 50:
        return "Portfolio name cannot exceed 50 characters"
    
    if len(name) < 2:
        return "Portfolio name must have at least 2 characters"
    
    return None


def validate_quantity(quantity: Any) -> Optional[str]:
    """
    Validate stock quantity.
    
    Args:
        quantity: Quantity value to validate
        
    Returns:
        Error message if invalid, None if valid
    """
    try:
        if isinstance(quantity, str):
            quantity = int(float(quantity.strip()))
        elif isinstance(quantity, float):
            quantity = int(quantity)
        
        if not isinstance(quantity, int):
            return "Quantity must be a whole number"
        
        if quantity < 0:
            return "Quantity cannot be negative"
        
        if quantity > 1000000:  # Reasonable upper limit
            return "Quantity cannot exceed 1,000,000"
        
        return None
        
    except (ValueError, TypeError):
        return "Quantity must be a valid whole number"


def validate_price(price: Any, field_name: str = "Price") -> Optional[str]:
    """
    Validate price/cost values.
    
    Args:
        price: Price value to validate
        field_name: Name of the field for error messages
        
    Returns:
        Error message if invalid, None if valid
    """
    try:
        if isinstance(price, str):
            price = float(price.strip())
        
        if not isinstance(price, (int, float)):
            return f"{field_name} must be a number"
        
        if price < 0:
            return f"{field_name} cannot be negative"
        
        if price > 1000000:  # Reasonable upper limit
            return f"{field_name} cannot exceed 1,000,000"
        
        # Check for reasonable decimal places (max 4)
        if isinstance(price, float):
            decimal_places = len(str(price).split('.')[-1]) if '.' in str(price) else 0
            if decimal_places > 4:
                return f"{field_name} cannot have more than 4 decimal places"
        
        return None
        
    except (ValueError, TypeError):
        return f"{field_name} must be a valid number"


def validate_percentage(percentage: Any, field_name: str = "Percentage") -> Optional[str]:
    """
    Validate percentage values.
    
    Args:
        percentage: Percentage value to validate
        field_name: Name of the field for error messages
        
    Returns:
        Error message if invalid, None if valid
    """
    try:
        if isinstance(percentage, str):
            # Remove % symbol if present
            percentage = percentage.strip().replace('%', '')
            percentage = float(percentage)
        
        if not isinstance(percentage, (int, float)):
            return f"{field_name} must be a number"
        
        if percentage < -100:
            return f"{field_name} cannot be less than -100%"
        
        if percentage > 1000:  # Allow for high growth percentages
            return f"{field_name} seems unusually high (>1000%)"
        
        return None
        
    except (ValueError, TypeError):
        return f"{field_name} must be a valid number"


def validate_form_data(data: dict, validation_rules: dict) -> Tuple[bool, List[str]]:
    """
    Validate form data against a set of rules.
    
    Args:
        data: Form data dictionary
        validation_rules: Dictionary of field -> validation function mappings
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    try:
        for field, validator in validation_rules.items():
            if callable(validator):
                value = data.get(field, '')
                error = validator(value)
                if error:
                    errors.append(error)
            elif isinstance(validator, dict):
                # Handle complex validation rules
                value = data.get(field, '')
                func = validator.get('function')
                params = validator.get('params', {})
                
                if callable(func):
                    error = func(value, **params)
                    if error:
                        errors.append(error)
        
        return len(errors) == 0, errors
        
    except Exception as e:
        logger.error(f"Error validating form data: {e}")
        return False, [f"Validation error: {str(e)}"]


def sanitize_input(value: str, max_length: int = None, 
                  allowed_chars: str = None) -> str:
    """
    Sanitize user input.
    
    Args:
        value: Input value to sanitize
        max_length: Maximum allowed length
        allowed_chars: Regex pattern for allowed characters
        
    Returns:
        Sanitized input string
    """
    if not isinstance(value, str):
        value = str(value)
    
    # Basic sanitization
    value = value.strip()
    
    # Remove control characters
    value = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)
    
    # Apply character restrictions
    if allowed_chars:
        value = re.sub(f'[^{allowed_chars}]', '', value)
    
    # Truncate to max length
    if max_length and len(value) > max_length:
        value = value[:max_length]
    
    return value


def is_valid_hk_symbol(symbol: str) -> bool:
    """
    Check if symbol follows Hong Kong stock format.
    
    Args:
        symbol: Stock symbol to check
        
    Returns:
        True if valid HK symbol format, False otherwise
    """
    if not symbol:
        return False
    
    symbol = symbol.strip().upper()
    
    # HK stocks typically end with .HK and have 4 digits
    # Examples: 0700.HK, 0005.HK, 9988.HK
    hk_pattern = r'^[0-9]{4}\.HK$'
    
    return bool(re.match(hk_pattern, symbol))


def validate_technical_indicator_selection(selected: List[str], 
                                         available: List[str], 
                                         max_selection: int = 3) -> Optional[str]:
    """
    Validate technical indicator selection.
    
    Args:
        selected: List of selected indicator codes
        available: List of available indicator codes
        max_selection: Maximum number of indicators allowed
        
    Returns:
        Error message if invalid, None if valid
    """
    if len(selected) > max_selection:
        return f"Maximum {max_selection} indicators allowed"
    
    for indicator in selected:
        if indicator not in available:
            return f"Invalid indicator: {indicator}"
    
    return None