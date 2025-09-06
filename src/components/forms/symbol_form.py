"""
Symbol Form Component.

Form for stock symbol input, validation, and selection.
"""

import streamlit as st
import yfinance as yf
from typing import Dict, List, Optional, Any, Tuple
import logging

from .base_form import BaseForm, ValidationMixin
from src.utils.validation_utils import validate_symbol, is_valid_hk_symbol
from src.utils.data_utils import get_company_name

logger = logging.getLogger(__name__)


class SymbolForm(BaseForm, ValidationMixin):
    """
    Form for symbol input with Yahoo Finance validation.
    """
    
    def __init__(self, form_key: str = "symbol_form", title: str = "Stock Symbol", 
                 submit_label: str = "Validate Symbol", help_text: str = None):
        """
        Initialize symbol form.
        
        Args:
            form_key: Unique form key
            title: Form title
            submit_label: Submit button label
            help_text: Help text for symbol input
        """
        super().__init__(form_key, title, submit_label)
        self.help_text = help_text or "Enter stock symbol (e.g., 0700.HK, AAPL)"
        self.validated_data = {}
    
    def render_fields(self) -> Dict[str, Any]:
        """
        Render symbol input fields.
        
        Returns:
            Dictionary with form field values
        """
        try:
            # Get current validated symbol if any
            current_symbol = st.session_state.get(f'{self.form_key}_validated_symbol', '')
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                symbol = st.text_input(
                    "Stock Symbol:",
                    value=current_symbol,
                    placeholder="e.g., 0700.HK, AAPL",
                    help=self.help_text,
                    key=f"{self.form_key}_symbol_input"
                )
            
            with col2:
                validate_clicked = st.button(
                    "🔍 Check",
                    help="Validate symbol with Yahoo Finance",
                    key=f"{self.form_key}_validate_btn"
                )
            
            # Show validation results if available
            self._show_validation_results()
            
            return {
                'symbol': symbol.strip().upper() if symbol else '',
                'validate_clicked': validate_clicked
            }
            
        except Exception as e:
            logger.error(f"Error rendering symbol form fields: {e}")
            st.error("Error rendering form fields")
            return {}
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate symbol form data.
        
        Args:
            data: Form data dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        symbol = data.get('symbol', '')
        
        try:
            # Basic symbol validation
            symbol_error = validate_symbol(symbol)
            if symbol_error:
                errors.append(symbol_error)
                return False, errors
            
            # If validate button was clicked, perform Yahoo Finance validation
            if data.get('validate_clicked'):
                self._perform_yahoo_validation(symbol)
            
            # Check if symbol has been validated
            validated_symbol = st.session_state.get(f'{self.form_key}_validated_symbol')
            validation_success = st.session_state.get(f'{self.form_key}_validation_success', False)
            
            if symbol != validated_symbol or not validation_success:
                errors.append("Please validate the symbol first by clicking 'Check'")
                return False, errors
            
            return True, []
            
        except Exception as e:
            logger.error(f"Error validating symbol form: {e}")
            errors.append(f"Validation error: {str(e)}")
            return False, errors
    
    def _perform_yahoo_validation(self, symbol: str) -> None:
        """
        Perform Yahoo Finance API validation.
        
        Args:
            symbol: Symbol to validate
        """
        try:
            # Clear previous validation state
            st.session_state[f'{self.form_key}_validation_success'] = False
            
            with st.spinner(f"Looking up {symbol} on Yahoo Finance..."):
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                if info and len(info) > 1:
                    # Extract company information
                    company_name = self._extract_company_name(info, symbol)
                    sector = self._map_sector(info.get('sector', 'Other'))
                    quote_type = info.get('quoteType', '')
                    
                    # Validate that it's a valid equity
                    if quote_type == 'EQUITY' or info.get('symbol') == symbol:
                        # Store validation results
                        st.session_state[f'{self.form_key}_validated_symbol'] = symbol
                        st.session_state[f'{self.form_key}_company_name'] = company_name
                        st.session_state[f'{self.form_key}_sector'] = sector
                        st.session_state[f'{self.form_key}_quote_type'] = quote_type
                        st.session_state[f'{self.form_key}_validation_success'] = True
                        
                        st.success(f"✅ Found: {company_name}")
                        if quote_type:
                            st.info(f"Type: {quote_type} | Sector: {info.get('sector', 'N/A')}")
                    else:
                        st.session_state[f'{self.form_key}_validation_success'] = False
                        st.error("❌ Symbol exists but may not be a valid equity")
                        st.info(f"Quote type: {quote_type}")
                else:
                    st.session_state[f'{self.form_key}_validation_success'] = False
                    st.error("❌ Symbol not found on Yahoo Finance")
                    
        except Exception as e:
            st.session_state[f'{self.form_key}_validation_success'] = False
            st.error(f"❌ Error validating symbol: {str(e)}")
            
            if "404" in str(e):
                st.info("💡 Make sure to use the correct format (e.g., 0700.HK)")
            elif "timeout" in str(e).lower():
                st.info("💡 Network timeout - please try again")
            else:
                st.info("💡 Check internet connection and try again")
    
    def _extract_company_name(self, info: dict, symbol: str) -> str:
        """
        Extract company name from Yahoo Finance info.
        
        Args:
            info: Yahoo Finance info dictionary
            symbol: Stock symbol
            
        Returns:
            Company name
        """
        # Try multiple name fields
        long_name = info.get('longName', '').strip()
        short_name = info.get('shortName', '').strip()
        display_name = info.get('displayName', '').strip()
        
        if long_name:
            return long_name
        elif short_name:
            return short_name
        elif display_name:
            return display_name
        else:
            # Fallback for HK stocks
            if symbol.endswith('.HK'):
                code = symbol.replace('.HK', '')
                return f"HK Stock {code}"
            return 'Unknown Company'
    
    def _map_sector(self, raw_sector: str) -> str:
        """
        Map raw sector to simplified sector.
        
        Args:
            raw_sector: Raw sector from Yahoo Finance
            
        Returns:
            Simplified sector name
        """
        sector_mapping = {
            "Technology": "Tech",
            "Information Technology": "Tech",
            "Communication Services": "Tech",
            "Financials": "Financials",
            "Financial Services": "Financials",
            "Real Estate": "REIT",
            "Energy": "Energy",
            "Consumer Discretionary": "Consumer",
            "Consumer Staples": "Consumer",
            "Healthcare": "Healthcare"
        }
        
        return sector_mapping.get(raw_sector, "Other")
    
    def _show_validation_results(self) -> None:
        """Show validation results if available."""
        validated_symbol = st.session_state.get(f'{self.form_key}_validated_symbol')
        company_name = st.session_state.get(f'{self.form_key}_company_name')
        sector = st.session_state.get(f'{self.form_key}_sector')
        validation_success = st.session_state.get(f'{self.form_key}_validation_success', False)
        
        if validated_symbol and validation_success:
            st.success(f"**Validated Symbol**: {validated_symbol}")
            if company_name:
                st.info(f"**Company**: {company_name}")
            if sector:
                st.info(f"**Sector**: {sector}")
    
    def get_validated_data(self) -> Dict[str, Any]:
        """
        Get validated symbol data.
        
        Returns:
            Dictionary with validated symbol information
        """
        return {
            'symbol': st.session_state.get(f'{self.form_key}_validated_symbol'),
            'company_name': st.session_state.get(f'{self.form_key}_company_name'),
            'sector': st.session_state.get(f'{self.form_key}_sector'),
            'quote_type': st.session_state.get(f'{self.form_key}_quote_type'),
            'validation_success': st.session_state.get(f'{self.form_key}_validation_success', False)
        }
    
    def clear_validation(self) -> None:
        """Clear validation session state."""
        validation_keys = [
            f'{self.form_key}_validated_symbol',
            f'{self.form_key}_company_name',
            f'{self.form_key}_sector',
            f'{self.form_key}_quote_type',
            f'{self.form_key}_validation_success'
        ]
        
        for key in validation_keys:
            if key in st.session_state:
                del st.session_state[key]


class SymbolSearchForm(BaseForm):
    """
    Form for searching and selecting from multiple symbols.
    """
    
    def __init__(self, symbols_list: List[Dict[str, str]], form_key: str = "symbol_search_form",
                 title: str = "Select Symbol", multi_select: bool = False):
        """
        Initialize symbol search form.
        
        Args:
            symbols_list: List of symbol dictionaries with 'symbol', 'name', 'sector'
            form_key: Unique form key
            title: Form title
            multi_select: Allow multiple symbol selection
        """
        super().__init__(form_key, title, "Select")
        self.symbols_list = symbols_list
        self.multi_select = multi_select
    
    def render_fields(self) -> Dict[str, Any]:
        """
        Render symbol search fields.
        
        Returns:
            Dictionary with selected symbols
        """
        try:
            if not self.symbols_list:
                st.info("No symbols available")
                return {'selected_symbols': []}
            
            # Search filter
            search_term = st.text_input(
                "Search symbols:",
                placeholder="Filter by symbol or company name",
                key=f"{self.form_key}_search"
            )
            
            # Filter symbols based on search
            filtered_symbols = self._filter_symbols(search_term)
            
            if not filtered_symbols:
                st.info("No symbols match your search")
                return {'selected_symbols': []}
            
            # Symbol selection
            if self.multi_select:
                selected = st.multiselect(
                    "Select symbols:",
                    options=[s['symbol'] for s in filtered_symbols],
                    format_func=lambda x: f"{x} - {next((s['name'] for s in filtered_symbols if s['symbol'] == x), 'Unknown')}",
                    key=f"{self.form_key}_multiselect"
                )
                selected_symbols = [s for s in filtered_symbols if s['symbol'] in selected]
            else:
                selected_symbol = st.selectbox(
                    "Select symbol:",
                    options=[s['symbol'] for s in filtered_symbols],
                    format_func=lambda x: f"{x} - {next((s['name'] for s in filtered_symbols if s['symbol'] == x), 'Unknown')}",
                    key=f"{self.form_key}_selectbox"
                )
                selected_symbols = [s for s in filtered_symbols if s['symbol'] == selected_symbol] if selected_symbol else []
            
            return {'selected_symbols': selected_symbols}
            
        except Exception as e:
            logger.error(f"Error rendering symbol search form: {e}")
            st.error("Error rendering form")
            return {'selected_symbols': []}
    
    def _filter_symbols(self, search_term: str) -> List[Dict[str, str]]:
        """
        Filter symbols based on search term.
        
        Args:
            search_term: Search term
            
        Returns:
            Filtered list of symbols
        """
        if not search_term:
            return self.symbols_list
        
        search_term = search_term.lower()
        return [
            symbol for symbol in self.symbols_list
            if (search_term in symbol.get('symbol', '').lower() or
                search_term in symbol.get('name', '').lower())
        ]
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate symbol selection.
        
        Args:
            data: Form data
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        selected_symbols = data.get('selected_symbols', [])
        
        if not selected_symbols:
            return False, ["Please select at least one symbol"]
        
        return True, []