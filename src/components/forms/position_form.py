"""
Position Form Component.

Forms for stock position entry, editing, and management.
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import date

from .base_form import BaseForm, ValidationMixin
from src.utils.validation_utils import validate_quantity, validate_price, validate_date

logger = logging.getLogger(__name__)


class PositionForm(BaseForm, ValidationMixin):
    """
    Form for entering stock position data (quantity, cost, date).
    """
    
    def __init__(self, form_key: str = "position_form", title: str = "Position Details", 
                 submit_label: str = "Save Position", symbol: str = None, 
                 existing_position: Dict[str, Any] = None):
        """
        Initialize position form.
        
        Args:
            form_key: Unique form key
            title: Form title
            submit_label: Submit button label
            symbol: Stock symbol (for display)
            existing_position: Existing position data for editing
        """
        super().__init__(form_key, title, submit_label)
        self.symbol = symbol
        self.existing_position = existing_position or {}
        self.is_edit_mode = bool(existing_position)
    
    def render_fields(self) -> Dict[str, Any]:
        """
        Render position input fields.
        
        Returns:
            Dictionary with form field values
        """
        try:
            if self.symbol:
                st.info(f"**Symbol**: {self.symbol}")
            
            # Quantity input
            col1, col2 = st.columns(2)
            
            with col1:
                current_qty = self.existing_position.get('quantity', 100 if not self.is_edit_mode else 0)
                quantity = st.number_input(
                    "Quantity:",
                    min_value=0,
                    value=int(current_qty),
                    step=1,
                    format="%d",
                    help="Number of shares (0 allowed for watchlist tracking)",
                    key=f"{self.form_key}_quantity"
                )
            
            with col2:
                current_cost = self.existing_position.get('avg_cost', 50.0 if not self.is_edit_mode else 0.0)
                avg_cost = st.number_input(
                    "Average Cost (HK$):",
                    min_value=0.0,
                    value=float(current_cost),
                    step=0.01,
                    format="%.2f",
                    help="Average cost per share in HK$ (0 allowed for free shares)",
                    key=f"{self.form_key}_avg_cost"
                )
            
            # Optional fields
            with st.expander("Additional Details", expanded=False):
                col3, col4 = st.columns(2)
                
                with col3:
                    purchase_date = st.date_input(
                        "Purchase Date:",
                        value=self.existing_position.get('purchase_date', date.today()),
                        help="Date when position was acquired",
                        key=f"{self.form_key}_purchase_date"
                    )
                
                with col4:
                    notes = st.text_area(
                        "Notes:",
                        value=self.existing_position.get('notes', ''),
                        help="Optional notes about this position",
                        max_chars=200,
                        key=f"{self.form_key}_notes"
                    )
            
            # Show change summary for edit mode
            if self.is_edit_mode:
                self._show_change_summary(quantity, avg_cost)
            
            return {
                'quantity': quantity,
                'avg_cost': avg_cost,
                'purchase_date': purchase_date,
                'notes': notes.strip() if notes else ''
            }
            
        except Exception as e:
            logger.error(f"Error rendering position form fields: {e}")
            st.error("Error rendering form fields")
            return {}
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate position form data.
        
        Args:
            data: Form data dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            # Validate quantity
            quantity_error = validate_quantity(data.get('quantity'))
            if quantity_error:
                errors.append(quantity_error)
            
            # Validate average cost
            cost_error = validate_price(data.get('avg_cost'), "Average cost")
            if cost_error:
                errors.append(cost_error)
            
            # Validate purchase date
            purchase_date = data.get('purchase_date')
            if purchase_date and purchase_date > date.today():
                errors.append("Purchase date cannot be in the future")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            logger.error(f"Error validating position form: {e}")
            return False, [f"Validation error: {str(e)}"]
    
    def _show_change_summary(self, new_quantity: int, new_avg_cost: float) -> None:
        """
        Show summary of changes in edit mode.
        
        Args:
            new_quantity: New quantity value
            new_avg_cost: New average cost value
        """
        try:
            old_quantity = self.existing_position.get('quantity', 0)
            old_avg_cost = self.existing_position.get('avg_cost', 0.0)
            
            qty_change = new_quantity - old_quantity
            cost_change = new_avg_cost - old_avg_cost
            
            if qty_change != 0 or abs(cost_change) > 0.001:
                st.markdown("**Changes:**")
                if qty_change != 0:
                    change_color = "🔴" if qty_change < 0 else "🟢"
                    st.write(f"{change_color} Quantity: {qty_change:+d} shares")
                if abs(cost_change) > 0.001:
                    change_color = "🔴" if cost_change < 0 else "🟢"
                    st.write(f"{change_color} Average Cost: HK${cost_change:+.2f}")
                    
        except Exception as e:
            logger.error(f"Error showing change summary: {e}")
    
    def get_market_value(self, current_price: float) -> Dict[str, float]:
        """
        Calculate market value and P&L for current position.
        
        Args:
            current_price: Current market price
            
        Returns:
            Dictionary with market value calculations
        """
        try:
            quantity = self.existing_position.get('quantity', 0)
            avg_cost = self.existing_position.get('avg_cost', 0.0)
            
            market_value = quantity * current_price
            cost_basis = quantity * avg_cost
            pnl = market_value - cost_basis
            pnl_percent = (pnl / cost_basis * 100) if cost_basis > 0 else 0
            
            return {
                'market_value': market_value,
                'cost_basis': cost_basis,
                'pnl': pnl,
                'pnl_percent': pnl_percent
            }
            
        except Exception as e:
            logger.error(f"Error calculating market value: {e}")
            return {'market_value': 0, 'cost_basis': 0, 'pnl': 0, 'pnl_percent': 0}


class BulkPositionForm(BaseForm):
    """
    Form for bulk position entry via CSV or manual input.
    """
    
    def __init__(self, form_key: str = "bulk_position_form", 
                 title: str = "Bulk Position Entry"):
        """
        Initialize bulk position form.
        
        Args:
            form_key: Unique form key
            title: Form title
        """
        super().__init__(form_key, title, "Import Positions")
    
    def render_fields(self) -> Dict[str, Any]:
        """
        Render bulk position input fields.
        
        Returns:
            Dictionary with form data
        """
        try:
            input_method = st.radio(
                "Input Method:",
                options=["Manual Entry", "CSV Upload"],
                key=f"{self.form_key}_input_method"
            )
            
            if input_method == "CSV Upload":
                return self._render_csv_upload()
            else:
                return self._render_manual_entry()
                
        except Exception as e:
            logger.error(f"Error rendering bulk position form: {e}")
            st.error("Error rendering form")
            return {}
    
    def _render_csv_upload(self) -> Dict[str, Any]:
        """Render CSV upload interface."""
        st.markdown("**CSV Format**: symbol,quantity,avg_cost,notes")
        st.markdown("**Example**: 0700.HK,100,350.50,Tech stock")
        
        uploaded_file = st.file_uploader(
            "Choose CSV file:",
            type=['csv'],
            key=f"{self.form_key}_csv_upload"
        )
        
        positions = []
        if uploaded_file:
            try:
                import pandas as pd
                df = pd.read_csv(uploaded_file)
                
                required_cols = ['symbol', 'quantity', 'avg_cost']
                if all(col in df.columns for col in required_cols):
                    positions = df.to_dict('records')
                    st.success(f"Loaded {len(positions)} positions")
                    
                    # Preview
                    st.dataframe(df.head())
                else:
                    st.error(f"CSV must have columns: {required_cols}")
                    
            except Exception as e:
                st.error(f"Error reading CSV: {e}")
        
        return {'positions': positions, 'input_method': 'csv'}
    
    def _render_manual_entry(self) -> Dict[str, Any]:
        """Render manual entry interface."""
        st.markdown("**Enter positions (one per line)**")
        st.markdown("**Format**: symbol,quantity,avg_cost,notes")
        
        positions_text = st.text_area(
            "Positions:",
            placeholder="0700.HK,100,350.50,Tech stock\n0005.HK,200,80.25,Bank stock",
            height=150,
            key=f"{self.form_key}_manual_text"
        )
        
        positions = []
        if positions_text.strip():
            try:
                lines = positions_text.strip().split('\n')
                for line in lines:
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 3:
                        positions.append({
                            'symbol': parts[0],
                            'quantity': int(float(parts[1])),
                            'avg_cost': float(parts[2]),
                            'notes': parts[3] if len(parts) > 3 else ''
                        })
                        
                if positions:
                    st.success(f"Parsed {len(positions)} positions")
                    
            except Exception as e:
                st.error(f"Error parsing positions: {e}")
        
        return {'positions': positions, 'input_method': 'manual'}
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate bulk position data.
        
        Args:
            data: Form data
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        positions = data.get('positions', [])
        
        if not positions:
            return False, ["No positions to import"]
        
        errors = []
        for i, pos in enumerate(positions):
            # Validate each position
            qty_error = validate_quantity(pos.get('quantity'))
            if qty_error:
                errors.append(f"Position {i+1}: {qty_error}")
            
            cost_error = validate_price(pos.get('avg_cost'))
            if cost_error:
                errors.append(f"Position {i+1}: {cost_error}")
        
        return len(errors) == 0, errors


class PositionSummaryWidget:
    """
    Widget displaying position summary information.
    """
    
    def __init__(self, position_data: Dict[str, Any], current_price: float = None):
        """
        Initialize position summary widget.
        
        Args:
            position_data: Position data dictionary
            current_price: Current market price
        """
        self.position_data = position_data
        self.current_price = current_price
    
    def render(self) -> None:
        """Render position summary."""
        try:
            symbol = self.position_data.get('symbol', 'N/A')
            quantity = self.position_data.get('quantity', 0)
            avg_cost = self.position_data.get('avg_cost', 0.0)
            
            st.markdown(f"### {symbol}")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Quantity", f"{quantity:,}")
            
            with col2:
                st.metric("Avg Cost", f"HK${avg_cost:.2f}")
            
            with col3:
                cost_basis = quantity * avg_cost
                st.metric("Cost Basis", f"HK${cost_basis:,.2f}")
            
            if self.current_price:
                col4, col5, col6 = st.columns(3)
                
                with col4:
                    st.metric("Current Price", f"HK${self.current_price:.2f}")
                
                with col5:
                    market_value = quantity * self.current_price
                    st.metric("Market Value", f"HK${market_value:,.2f}")
                
                with col6:
                    pnl = market_value - cost_basis
                    pnl_percent = (pnl / cost_basis * 100) if cost_basis > 0 else 0
                    st.metric("P&L", f"HK${pnl:,.2f}", f"{pnl_percent:+.1f}%")
                    
        except Exception as e:
            logger.error(f"Error rendering position summary: {e}")
            st.error("Error displaying position summary")