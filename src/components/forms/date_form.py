"""
Date Form Components.

Forms for date and date range selection with validation.
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import date, datetime, timedelta

from .base_form import BaseForm, ValidationMixin
from src.utils.validation_utils import validate_date, validate_date_range

logger = logging.getLogger(__name__)


class DateRangeForm(BaseForm, ValidationMixin):
    """
    Form for selecting date ranges with validation and presets.
    """
    
    def __init__(self, form_key: str = "date_range_form", title: str = "Select Date Range", 
                 submit_label: str = "Apply Date Range", max_range_days: int = None,
                 default_start: date = None, default_end: date = None):
        """
        Initialize date range form.
        
        Args:
            form_key: Unique form key
            title: Form title
            submit_label: Submit button label
            max_range_days: Maximum allowed range in days
            default_start: Default start date
            default_end: Default end date
        """
        super().__init__(form_key, title, submit_label)
        self.max_range_days = max_range_days
        self.default_start = default_start or (date.today() - timedelta(days=30))
        self.default_end = default_end or date.today()
    
    def render_fields(self) -> Dict[str, Any]:
        """
        Render date range input fields.
        
        Returns:
            Dictionary with date range values
        """
        try:
            # Quick preset buttons
            st.markdown("**Quick Presets:**")
            preset_cols = st.columns(5)
            
            preset_applied = None
            with preset_cols[0]:
                if st.button("Last 7 Days", key=f"{self.form_key}_7d"):
                    preset_applied = 7
            with preset_cols[1]:
                if st.button("Last 30 Days", key=f"{self.form_key}_30d"):
                    preset_applied = 30
            with preset_cols[2]:
                if st.button("Last 90 Days", key=f"{self.form_key}_90d"):
                    preset_applied = 90
            with preset_cols[3]:
                if st.button("Last Year", key=f"{self.form_key}_1y"):
                    preset_applied = 365
            with preset_cols[4]:
                if st.button("Reset", key=f"{self.form_key}_reset"):
                    preset_applied = "reset"
            
            # Apply preset if selected
            if preset_applied:
                if preset_applied == "reset":
                    start_date = self.default_start
                    end_date = self.default_end
                else:
                    end_date = date.today()
                    start_date = end_date - timedelta(days=preset_applied)
                
                # Update session state to reflect preset
                st.session_state[f"{self.form_key}_start_date"] = start_date
                st.session_state[f"{self.form_key}_end_date"] = end_date
            
            st.markdown("---")
            
            # Date inputs
            col1, col2 = st.columns(2)
            
            with col1:
                start_date = st.date_input(
                    "Start Date:",
                    value=st.session_state.get(f"{self.form_key}_start_date", self.default_start),
                    max_value=date.today(),
                    key=f"{self.form_key}_start_date"
                )
            
            with col2:
                end_date = st.date_input(
                    "End Date:",
                    value=st.session_state.get(f"{self.form_key}_end_date", self.default_end),
                    max_value=date.today(),
                    key=f"{self.form_key}_end_date"
                )
            
            # Show range summary
            if start_date and end_date:
                range_days = (end_date - start_date).days
                if range_days >= 0:
                    st.info(f"📅 Selected range: {range_days + 1} days ({start_date} to {end_date})")
                else:
                    st.error("Start date must be before end date")
            
            return {
                'start_date': start_date,
                'end_date': end_date,
                'range_days': (end_date - start_date).days if start_date and end_date else 0
            }
            
        except Exception as e:
            logger.error(f"Error rendering date range form: {e}")
            st.error("Error rendering date form")
            return {}
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate date range data.
        
        Args:
            data: Form data dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            
            if not start_date or not end_date:
                errors.append("Both start and end dates are required")
                return False, errors
            
            # Validate date range
            range_error = validate_date_range(
                start_date.strftime('%Y-%m-%d'), 
                end_date.strftime('%Y-%m-%d')
            )
            if range_error:
                errors.append(range_error)
            
            # Check maximum range if specified
            if self.max_range_days:
                range_days = (end_date - start_date).days
                if range_days > self.max_range_days:
                    errors.append(f"Date range cannot exceed {self.max_range_days} days")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            logger.error(f"Error validating date range form: {e}")
            return False, [f"Validation error: {str(e)}"]


class SingleDateForm(BaseForm):
    """
    Form for selecting a single date.
    """
    
    def __init__(self, form_key: str = "single_date_form", title: str = "Select Date",
                 submit_label: str = "Apply Date", allow_future: bool = False,
                 default_date: date = None):
        """
        Initialize single date form.
        
        Args:
            form_key: Unique form key
            title: Form title
            submit_label: Submit button label
            allow_future: Whether to allow future dates
            default_date: Default date
        """
        super().__init__(form_key, title, submit_label)
        self.allow_future = allow_future
        self.default_date = default_date or date.today()
    
    def render_fields(self) -> Dict[str, Any]:
        """
        Render single date input field.
        
        Returns:
            Dictionary with date value
        """
        try:
            max_date = None if self.allow_future else date.today()
            
            selected_date = st.date_input(
                "Date:",
                value=self.default_date,
                max_value=max_date,
                help="Select the date for analysis" if not self.allow_future else "Select any date",
                key=f"{self.form_key}_date"
            )
            
            return {'selected_date': selected_date}
            
        except Exception as e:
            logger.error(f"Error rendering single date form: {e}")
            st.error("Error rendering date form")
            return {}
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate single date data.
        
        Args:
            data: Form data
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        selected_date = data.get('selected_date')
        
        if not selected_date:
            return False, ["Date is required"]
        
        if not self.allow_future and selected_date > date.today():
            return False, ["Future dates are not allowed"]
        
        return True, []


class AnalysisPeriodForm(BaseForm):
    """
    Form for selecting analysis periods with predefined options.
    """
    
    def __init__(self, form_key: str = "analysis_period_form", 
                 title: str = "Analysis Period"):
        """
        Initialize analysis period form.
        
        Args:
            form_key: Unique form key
            title: Form title
        """
        super().__init__(form_key, title, "Apply Period")
    
    def render_fields(self) -> Dict[str, Any]:
        """
        Render analysis period fields.
        
        Returns:
            Dictionary with period data
        """
        try:
            # Period type selection
            period_type = st.radio(
                "Period Type:",
                options=["Predefined Period", "Custom Date Range"],
                key=f"{self.form_key}_period_type"
            )
            
            if period_type == "Predefined Period":
                return self._render_predefined_period()
            else:
                return self._render_custom_period()
                
        except Exception as e:
            logger.error(f"Error rendering analysis period form: {e}")
            st.error("Error rendering form")
            return {}
    
    def _render_predefined_period(self) -> Dict[str, Any]:
        """Render predefined period selection."""
        period_options = {
            "1W": "Last Week",
            "1M": "Last Month", 
            "3M": "Last 3 Months",
            "6M": "Last 6 Months",
            "1Y": "Last Year",
            "2Y": "Last 2 Years",
            "5Y": "Last 5 Years",
            "YTD": "Year to Date",
            "MTD": "Month to Date"
        }
        
        selected_period = st.selectbox(
            "Select Period:",
            options=list(period_options.keys()),
            format_func=lambda x: period_options[x],
            key=f"{self.form_key}_predefined"
        )
        
        # Calculate actual dates
        end_date = date.today()
        start_date = self._calculate_start_date(selected_period, end_date)
        
        st.info(f"Period: {start_date} to {end_date}")
        
        return {
            'period_type': 'predefined',
            'period_code': selected_period,
            'start_date': start_date,
            'end_date': end_date
        }
    
    def _render_custom_period(self) -> Dict[str, Any]:
        """Render custom date range selection."""
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input(
                "Start Date:",
                value=date.today() - timedelta(days=30),
                max_value=date.today(),
                key=f"{self.form_key}_custom_start"
            )
        
        with col2:
            end_date = st.date_input(
                "End Date:",
                value=date.today(),
                max_value=date.today(),
                key=f"{self.form_key}_custom_end"
            )
        
        return {
            'period_type': 'custom',
            'start_date': start_date,
            'end_date': end_date
        }
    
    def _calculate_start_date(self, period_code: str, end_date: date) -> date:
        """
        Calculate start date for predefined period.
        
        Args:
            period_code: Period code
            end_date: End date
            
        Returns:
            Calculated start date
        """
        if period_code == "1W":
            return end_date - timedelta(weeks=1)
        elif period_code == "1M":
            return end_date - timedelta(days=30)
        elif period_code == "3M":
            return end_date - timedelta(days=90)
        elif period_code == "6M":
            return end_date - timedelta(days=180)
        elif period_code == "1Y":
            return end_date - timedelta(days=365)
        elif period_code == "2Y":
            return end_date - timedelta(days=730)
        elif period_code == "5Y":
            return end_date - timedelta(days=1825)
        elif period_code == "YTD":
            return date(end_date.year, 1, 1)
        elif period_code == "MTD":
            return date(end_date.year, end_date.month, 1)
        else:
            return end_date - timedelta(days=30)  # Default to 1 month
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate analysis period data.
        
        Args:
            data: Form data
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if not start_date or not end_date:
            return False, ["Invalid date range"]
        
        if start_date > end_date:
            return False, ["Start date must be before end date"]
        
        # Check for reasonable range (not more than 10 years)
        if (end_date - start_date).days > 365 * 10:
            return False, ["Analysis period cannot exceed 10 years"]
        
        return True, []


class TimeframeSelector:
    """
    Widget for selecting chart timeframes.
    """
    
    def __init__(self, key_prefix: str = "timeframe"):
        """
        Initialize timeframe selector.
        
        Args:
            key_prefix: Key prefix for session state
        """
        self.key_prefix = key_prefix
    
    def render(self) -> str:
        """
        Render timeframe selector.
        
        Returns:
            Selected timeframe code
        """
        try:
            timeframes = {
                "1D": "1 Day",
                "1W": "1 Week", 
                "1M": "1 Month",
                "3M": "3 Months",
                "6M": "6 Months",
                "1Y": "1 Year",
                "2Y": "2 Years",
                "5Y": "5 Years"
            }
            
            cols = st.columns(len(timeframes))
            
            current_timeframe = st.session_state.get(f"{self.key_prefix}_selected", "3M")
            
            for i, (code, label) in enumerate(timeframes.items()):
                with cols[i]:
                    if st.button(
                        label,
                        key=f"{self.key_prefix}_{code}",
                        type="primary" if current_timeframe == code else "secondary"
                    ):
                        st.session_state[f"{self.key_prefix}_selected"] = code
                        current_timeframe = code
            
            return current_timeframe
            
        except Exception as e:
            logger.error(f"Error rendering timeframe selector: {e}")
            return "3M"  # Default fallback