"""
Portfolio Form Component.

Forms for portfolio creation, editing, and management.
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import date

from .base_form import BaseForm, ValidationMixin
from src.utils.validation_utils import validate_portfolio_id, validate_portfolio_name, validate_required

logger = logging.getLogger(__name__)


class PortfolioForm(BaseForm, ValidationMixin):
    """
    Form for creating and editing portfolios.
    """
    
    def __init__(self, form_key: str = "portfolio_form", title: str = "Portfolio Details", 
                 submit_label: str = "Save Portfolio", existing_portfolio: Dict[str, Any] = None,
                 existing_portfolios: List[str] = None):
        """
        Initialize portfolio form.
        
        Args:
            form_key: Unique form key
            title: Form title
            submit_label: Submit button label
            existing_portfolio: Existing portfolio data for editing
            existing_portfolios: List of existing portfolio IDs for validation
        """
        super().__init__(form_key, title, submit_label)
        self.existing_portfolio = existing_portfolio or {}
        self.existing_portfolios = existing_portfolios or []
        self.is_edit_mode = bool(existing_portfolio)
    
    def render_fields(self) -> Dict[str, Any]:
        """
        Render portfolio input fields.
        
        Returns:
            Dictionary with form field values
        """
        try:
            col1, col2 = st.columns(2)
            
            with col1:
                # Portfolio ID (disabled in edit mode)
                current_id = self.existing_portfolio.get('portfolio_id', '')
                portfolio_id = st.text_input(
                    "Portfolio ID:",
                    value=current_id,
                    placeholder="e.g., MAIN_PORTFOLIO",
                    help="Unique identifier for the portfolio",
                    disabled=self.is_edit_mode,
                    key=f"{self.form_key}_portfolio_id"
                )
            
            with col2:
                # Portfolio Name
                current_name = self.existing_portfolio.get('name', '')
                portfolio_name = st.text_input(
                    "Portfolio Name:",
                    value=current_name,
                    placeholder="e.g., Main Investment Portfolio",
                    help="Display name for the portfolio",
                    key=f"{self.form_key}_portfolio_name"
                )
            
            # Description
            current_desc = self.existing_portfolio.get('description', '')
            description = st.text_area(
                "Description:",
                value=current_desc,
                placeholder="Optional description of the portfolio strategy or purpose",
                help="Detailed description of the portfolio",
                max_chars=500,
                key=f"{self.form_key}_description"
            )
            
            # Portfolio Settings
            with st.expander("Portfolio Settings", expanded=self.is_edit_mode):
                col3, col4 = st.columns(2)
                
                with col3:
                    # Currency
                    current_currency = self.existing_portfolio.get('currency', 'HKD')
                    currency = st.selectbox(
                        "Base Currency:",
                        options=['HKD', 'USD', 'CNY', 'EUR', 'GBP'],
                        index=['HKD', 'USD', 'CNY', 'EUR', 'GBP'].index(current_currency),
                        key=f"{self.form_key}_currency"
                    )
                
                with col4:
                    # Risk Level
                    current_risk = self.existing_portfolio.get('risk_level', 'Medium')
                    risk_level = st.selectbox(
                        "Risk Level:",
                        options=['Conservative', 'Medium', 'Aggressive'],
                        index=['Conservative', 'Medium', 'Aggressive'].index(current_risk),
                        key=f"{self.form_key}_risk_level"
                    )
                
                # Investment Strategy
                current_strategy = self.existing_portfolio.get('strategy', '')
                strategy = st.selectbox(
                    "Investment Strategy:",
                    options=['', 'Growth', 'Value', 'Income', 'Balanced', 'Speculative', 'Index', 'Other'],
                    index=0 if not current_strategy else ['', 'Growth', 'Value', 'Income', 'Balanced', 'Speculative', 'Index', 'Other'].index(current_strategy),
                    key=f"{self.form_key}_strategy"
                )
                
                # Active status
                is_active = st.checkbox(
                    "Active Portfolio",
                    value=self.existing_portfolio.get('is_active', True),
                    help="Whether this portfolio is actively managed",
                    key=f"{self.form_key}_is_active"
                )
            
            return {
                'portfolio_id': portfolio_id.strip().upper() if portfolio_id else '',
                'name': portfolio_name.strip() if portfolio_name else '',
                'description': description.strip() if description else '',
                'currency': currency,
                'risk_level': risk_level,
                'strategy': strategy if strategy else None,
                'is_active': is_active
            }
            
        except Exception as e:
            logger.error(f"Error rendering portfolio form fields: {e}")
            st.error("Error rendering form fields")
            return {}
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate portfolio form data.
        
        Args:
            data: Form data dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            portfolio_id = data.get('portfolio_id', '')
            portfolio_name = data.get('name', '')
            
            # Validate portfolio ID (only in create mode)
            if not self.is_edit_mode:
                id_error = validate_portfolio_id(portfolio_id)
                if id_error:
                    errors.append(id_error)
                elif portfolio_id in self.existing_portfolios:
                    errors.append("Portfolio ID already exists")
            
            # Validate portfolio name
            name_error = validate_portfolio_name(portfolio_name)
            if name_error:
                errors.append(name_error)
            
            # Validate required fields
            required_error = validate_required(portfolio_name, "Portfolio name")
            if required_error:
                errors.append(required_error)
            
            return len(errors) == 0, errors
            
        except Exception as e:
            logger.error(f"Error validating portfolio form: {e}")
            return False, [f"Validation error: {str(e)}"]


class PortfolioCopyForm(BaseForm):
    """
    Form for copying an existing portfolio.
    """
    
    def __init__(self, source_portfolio_id: str, source_portfolio_name: str,
                 form_key: str = "portfolio_copy_form", existing_portfolios: List[str] = None):
        """
        Initialize portfolio copy form.
        
        Args:
            source_portfolio_id: ID of portfolio to copy
            source_portfolio_name: Name of portfolio to copy
            form_key: Unique form key
            existing_portfolios: List of existing portfolio IDs
        """
        super().__init__(form_key, "Copy Portfolio", "Copy Portfolio")
        self.source_portfolio_id = source_portfolio_id
        self.source_portfolio_name = source_portfolio_name
        self.existing_portfolios = existing_portfolios or []
    
    def render_fields(self) -> Dict[str, Any]:
        """
        Render copy portfolio fields.
        
        Returns:
            Dictionary with form field values
        """
        try:
            st.info(f"**Source Portfolio**: {self.source_portfolio_id} - {self.source_portfolio_name}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                new_portfolio_id = st.text_input(
                    "New Portfolio ID:",
                    value=f"{self.source_portfolio_id}_COPY",
                    placeholder="e.g., MAIN_PORTFOLIO_COPY",
                    key=f"{self.form_key}_new_id"
                )
            
            with col2:
                new_portfolio_name = st.text_input(
                    "New Portfolio Name:",
                    value=f"{self.source_portfolio_name} (Copy)",
                    placeholder="e.g., Main Portfolio Copy",
                    key=f"{self.form_key}_new_name"
                )
            
            # Copy options
            st.markdown("**Copy Options:**")
            
            copy_positions = st.checkbox(
                "Copy all positions",
                value=True,
                help="Copy all stock positions from source portfolio",
                key=f"{self.form_key}_copy_positions"
            )
            
            copy_settings = st.checkbox(
                "Copy portfolio settings",
                value=True,
                help="Copy currency, risk level, and strategy settings",
                key=f"{self.form_key}_copy_settings"
            )
            
            # Position copy options
            if copy_positions:
                with st.expander("Position Copy Options"):
                    copy_quantities = st.radio(
                        "How to handle quantities:",
                        options=["Keep original quantities", "Set all to zero (watchlist)", "Custom scaling"],
                        key=f"{self.form_key}_quantity_option"
                    )
                    
                    quantity_multiplier = 1.0
                    if copy_quantities == "Custom scaling":
                        quantity_multiplier = st.number_input(
                            "Quantity multiplier:",
                            min_value=0.0,
                            value=1.0,
                            step=0.1,
                            help="Multiply all quantities by this factor",
                            key=f"{self.form_key}_multiplier"
                        )
            else:
                copy_quantities = "Keep original quantities"
                quantity_multiplier = 1.0
            
            return {
                'new_portfolio_id': new_portfolio_id.strip().upper() if new_portfolio_id else '',
                'new_portfolio_name': new_portfolio_name.strip() if new_portfolio_name else '',
                'copy_positions': copy_positions,
                'copy_settings': copy_settings,
                'quantity_option': copy_quantities,
                'quantity_multiplier': quantity_multiplier
            }
            
        except Exception as e:
            logger.error(f"Error rendering copy portfolio form: {e}")
            st.error("Error rendering form")
            return {}
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate copy portfolio data.
        
        Args:
            data: Form data
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            new_id = data.get('new_portfolio_id', '')
            new_name = data.get('new_portfolio_name', '')
            
            # Validate new portfolio ID
            id_error = validate_portfolio_id(new_id)
            if id_error:
                errors.append(id_error)
            elif new_id in self.existing_portfolios:
                errors.append("Portfolio ID already exists")
            elif new_id == self.source_portfolio_id:
                errors.append("New portfolio ID must be different from source")
            
            # Validate new portfolio name
            name_error = validate_portfolio_name(new_name)
            if name_error:
                errors.append(name_error)
            
            return len(errors) == 0, errors
            
        except Exception as e:
            logger.error(f"Error validating copy portfolio form: {e}")
            return False, [f"Validation error: {str(e)}"]


class PortfolioSelectionForm(BaseForm):
    """
    Form for selecting portfolios for analysis or operations.
    """
    
    def __init__(self, portfolios: List[Dict[str, str]], form_key: str = "portfolio_select_form",
                 title: str = "Select Portfolios", multi_select: bool = True, 
                 max_selection: int = None):
        """
        Initialize portfolio selection form.
        
        Args:
            portfolios: List of portfolio dictionaries
            form_key: Unique form key
            title: Form title
            multi_select: Allow multiple selection
            max_selection: Maximum number of portfolios to select
        """
        super().__init__(form_key, title, "Select")
        self.portfolios = portfolios
        self.multi_select = multi_select
        self.max_selection = max_selection
    
    def render_fields(self) -> Dict[str, Any]:
        """
        Render portfolio selection fields.
        
        Returns:
            Dictionary with selected portfolios
        """
        try:
            if not self.portfolios:
                st.info("No portfolios available")
                return {'selected_portfolios': []}
            
            # Filter options
            with st.expander("Filter Options", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    filter_currency = st.selectbox(
                        "Filter by Currency:",
                        options=['All'] + list(set(p.get('currency', 'HKD') for p in self.portfolios)),
                        key=f"{self.form_key}_filter_currency"
                    )
                
                with col2:
                    filter_status = st.selectbox(
                        "Filter by Status:",
                        options=['All', 'Active', 'Inactive'],
                        key=f"{self.form_key}_filter_status"
                    )
            
            # Apply filters
            filtered_portfolios = self._apply_filters(filter_currency, filter_status)
            
            if not filtered_portfolios:
                st.info("No portfolios match the selected filters")
                return {'selected_portfolios': []}
            
            # Portfolio selection
            if self.multi_select:
                selected_ids = st.multiselect(
                    "Select portfolios:",
                    options=[p['portfolio_id'] for p in filtered_portfolios],
                    format_func=lambda x: f"{x} - {next((p['name'] for p in filtered_portfolios if p['portfolio_id'] == x), 'Unknown')}",
                    help=f"Select up to {self.max_selection} portfolios" if self.max_selection else None,
                    key=f"{self.form_key}_multiselect"
                )
                selected_portfolios = [p for p in filtered_portfolios if p['portfolio_id'] in selected_ids]
            else:
                selected_id = st.selectbox(
                    "Select portfolio:",
                    options=[p['portfolio_id'] for p in filtered_portfolios],
                    format_func=lambda x: f"{x} - {next((p['name'] for p in filtered_portfolios if p['portfolio_id'] == x), 'Unknown')}",
                    key=f"{self.form_key}_selectbox"
                )
                selected_portfolios = [p for p in filtered_portfolios if p['portfolio_id'] == selected_id] if selected_id else []
            
            # Show selection summary
            if selected_portfolios:
                st.success(f"Selected {len(selected_portfolios)} portfolio(s)")
                for portfolio in selected_portfolios:
                    st.write(f"• {portfolio['portfolio_id']} - {portfolio['name']}")
            
            return {
                'selected_portfolios': selected_portfolios,
                'selected_ids': [p['portfolio_id'] for p in selected_portfolios]
            }
            
        except Exception as e:
            logger.error(f"Error rendering portfolio selection form: {e}")
            st.error("Error rendering form")
            return {'selected_portfolios': []}
    
    def _apply_filters(self, filter_currency: str, filter_status: str) -> List[Dict[str, str]]:
        """
        Apply filters to portfolio list.
        
        Args:
            filter_currency: Currency filter
            filter_status: Status filter
            
        Returns:
            Filtered portfolio list
        """
        filtered = self.portfolios.copy()
        
        if filter_currency != 'All':
            filtered = [p for p in filtered if p.get('currency', 'HKD') == filter_currency]
        
        if filter_status != 'All':
            is_active = filter_status == 'Active'
            filtered = [p for p in filtered if p.get('is_active', True) == is_active]
        
        return filtered
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate portfolio selection.
        
        Args:
            data: Form data
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        selected_portfolios = data.get('selected_portfolios', [])
        
        if not selected_portfolios:
            return False, ["Please select at least one portfolio"]
        
        if self.max_selection and len(selected_portfolios) > self.max_selection:
            return False, [f"Maximum {self.max_selection} portfolios allowed"]
        
        return True, []