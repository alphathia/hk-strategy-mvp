"""
Position Management Dialog Components.

Modal dialogs for adding and updating stock positions.
Extracted from dashboard.py lines 215-422 and 423-535.
"""

from typing import Dict, Any, Optional
import streamlit as st
import yfinance as yf

from .base_dialog import BaseDialog, dialog_component


@dialog_component("Add New Symbol", width="medium")
class AddSymbolDialog(BaseDialog):
    """Dialog for adding a new symbol to the portfolio."""
    
    def __init__(self, portfolio_id: str):
        """
        Initialize add symbol dialog.
        
        Args:
            portfolio_id: Portfolio ID to add symbol to
        """
        super().__init__("Add New Symbol", width="medium")
        self.portfolio_id = portfolio_id
    
    def render_content(self) -> Optional[Dict[str, Any]]:
        """Render add symbol dialog content."""
        st.markdown("**Add a new stock position to your portfolio**")
        st.markdown("---")
        
        # Symbol input with validation
        col1, col2 = st.columns([2, 1])
        with col1:
            current_symbol = st.session_state.get('validated_symbol', '')
            symbol_input = st.text_input(
                "Stock Symbol:", 
                value=current_symbol,
                placeholder="e.g., 0001.HK, 0700.HK",
                help="Enter Hong Kong stock symbol"
            )
        with col2:
            if st.button("🔍 Check Symbol", use_container_width=True):
                if symbol_input.strip():
                    self._validate_symbol(symbol_input.strip().upper())
                else:
                    st.error("Please enter a symbol")
        
        # Display validated information
        self._display_validated_info()
        
        st.markdown("---")
        
        # Quantity and Cost inputs
        quantity, avg_cost = self._render_position_inputs()
        
        # Validation
        error_msg = self._validate_position_data(quantity, avg_cost)
        
        if error_msg:
            st.error(f"❌ {error_msg}")
            if "already exists in this portfolio" in error_msg:
                st.info("💡 To modify an existing position, use the **Edit** button in the position table.")
        
        st.markdown("---")
        
        # Action buttons
        return self._render_action_buttons(quantity, avg_cost, error_msg)
    
    def _validate_symbol(self, symbol: str) -> None:
        """Validate symbol using Yahoo Finance API."""
        # Clear previous validation state
        st.session_state['validation_success'] = False
        
        # Show loading message
        with st.spinner(f"Looking up {symbol} on Yahoo Finance..."):
            try:
                # Create ticker and fetch info
                stock = yf.Ticker(symbol)
                info = stock.info
                
                # Enhanced validation and name retrieval
                if info and len(info) > 1:
                    # Try multiple name fields for better reliability
                    long_name = info.get('longName', '').strip()
                    short_name = info.get('shortName', '').strip()
                    display_name = info.get('displayName', '').strip()
                    
                    # Choose best available name
                    if long_name:
                        company_name = long_name
                    elif short_name:
                        company_name = short_name
                    elif display_name:
                        company_name = display_name
                    else:
                        # Fallback: use symbol-based name
                        if symbol.endswith('.HK'):
                            code = symbol.replace('.HK', '')
                            company_name = f"HK Stock {code}"
                        else:
                            company_name = 'Unknown Company'
                    
                    # Determine sector
                    sector = self._map_sector(info.get('sector', 'Other'))
                    
                    # Validate that we have meaningful data
                    quote_type = info.get('quoteType', '')
                    if quote_type == 'EQUITY' or info.get('symbol') == symbol:
                        # Store in session state for display
                        st.session_state['validated_symbol'] = symbol
                        st.session_state['validated_company'] = company_name
                        st.session_state['validated_sector'] = sector
                        st.session_state['validation_success'] = True
                        st.success(f"✅ Found: {company_name}")
                        
                        # Show additional info
                        if quote_type:
                            st.info(f"Type: {quote_type} | Sector: {info.get('sector', 'N/A')}")
                    else:
                        st.session_state['validation_success'] = False
                        st.error("❌ Symbol exists but may not be a valid equity")
                        st.info(f"Quote type: {quote_type}, Raw data keys: {len(info)}")
                else:
                    st.session_state['validation_success'] = False
                    st.error("❌ Symbol not found on Yahoo Finance")
                    st.info(f"Received data keys: {len(info) if info else 0}")
                    
            except Exception as e:
                st.session_state['validation_success'] = False
                st.error(f"❌ Error validating symbol: {str(e)}")
                
                # Provide helpful troubleshooting info
                if "404" in str(e):
                    st.info("💡 Make sure to use the correct format (e.g., 0700.HK)")
                elif "timeout" in str(e).lower():
                    st.info("💡 Network timeout - please try again")
                else:
                    st.info("💡 Check internet connection and try again")
    
    def _map_sector(self, raw_sector: str) -> str:
        """Map raw sector to simplified sector."""
        if raw_sector in ["Technology", "Information Technology", "Communication Services"]:
            return "Tech"
        elif raw_sector in ["Financials", "Financial Services"]:
            return "Financials"
        elif raw_sector in ["Real Estate"]:
            return "REIT"
        elif raw_sector in ["Energy"]:
            return "Energy"
        elif raw_sector in ["Consumer Discretionary", "Consumer Staples"]:
            return "Consumer"
        elif raw_sector in ["Healthcare"]:
            return "Healthcare"
        else:
            return "Other"
    
    def _display_validated_info(self) -> None:
        """Display validated symbol information."""
        validated_symbol = st.session_state.get('validated_symbol', '')
        validated_company = st.session_state.get('validated_company', '')
        validated_sector = st.session_state.get('validated_sector', 'Other')
        
        # Show validated info if available
        if validated_symbol:
            st.success(f"**Validated Symbol**: {validated_symbol}")
            st.info(f"**Company**: {validated_company}")
            st.info(f"**Sector**: {validated_sector}")
    
    def _render_position_inputs(self) -> tuple[int, float]:
        """Render quantity and cost input fields."""
        col_qty, col_cost = st.columns(2)
        
        with col_qty:
            quantity = st.number_input(
                "Quantity:",
                min_value=0,
                value=100,
                step=1,
                format="%d",
                help="Number of shares (0 allowed for watchlist tracking)"
            )
        
        with col_cost:
            avg_cost = st.number_input(
                "Average Cost (HK$):",
                min_value=0.0,
                value=50.0,
                step=0.01,
                format="%.2f",
                help="Average cost per share in HK$ (0 allowed for free shares)"
            )
        
        return quantity, avg_cost
    
    def _validate_position_data(self, quantity: int, avg_cost: float) -> str:
        """Validate position data."""
        validated_symbol = st.session_state.get('validated_symbol', '')
        
        if not validated_symbol:
            return "Please check the symbol first"
        elif not isinstance(quantity, int) or quantity < 0:
            return "Quantity must be a non-negative integer"
        elif not isinstance(avg_cost, (int, float)) or avg_cost < 0:
            return "Average cost must be a non-negative number"
        else:
            # Check for duplicate symbol in current portfolio
            if hasattr(st.session_state, 'portfolios') and self.portfolio_id in st.session_state.portfolios:
                existing_symbols = [pos['symbol'] for pos in st.session_state.portfolios[self.portfolio_id]['positions']]
                if validated_symbol in existing_symbols:
                    return f"Symbol {validated_symbol} already exists in this portfolio. You cannot add the same symbol twice."
        
        return ""
    
    def _render_action_buttons(self, quantity: int, avg_cost: float, error_msg: str) -> Optional[Dict[str, Any]]:
        """Render action buttons."""
        col_add, col_cancel, col_spacer = st.columns([1, 1, 2])
        
        with col_add:
            if st.button("➕ Add Position", disabled=bool(error_msg), use_container_width=True, type="primary"):
                return {
                    'action': 'add',
                    'symbol': st.session_state.get('validated_symbol'),
                    'company_name': st.session_state.get('validated_company'),
                    'quantity': quantity,
                    'avg_cost': avg_cost,
                    'sector': st.session_state.get('validated_sector', 'Other')
                }
        
        with col_cancel:
            if st.button("❌ Cancel", use_container_width=True):
                return {
                    'action': 'cancel'
                }
        
        return None
    
    def on_submit(self, data: Dict[str, Any]) -> bool:
        """Handle add symbol submission."""
        try:
            if data['action'] == 'add':
                # Add to session state pending changes
                modified_key = f'modified_positions_{self.portfolio_id}'
                if modified_key not in st.session_state:
                    st.session_state[modified_key] = {}
                
                # Add new position to modified positions
                st.session_state[modified_key][data['symbol']] = {
                    'symbol': data['symbol'],
                    'company_name': data['company_name'],
                    'quantity': data['quantity'],
                    'avg_cost': data['avg_cost'],
                    'sector': data['sector']
                }
                
                # Add to current portfolio for immediate display
                if hasattr(st.session_state, 'portfolios') and self.portfolio_id in st.session_state.portfolios:
                    st.session_state.portfolios[self.portfolio_id]['positions'].append({
                        'symbol': data['symbol'],
                        'company_name': data['company_name'],
                        'quantity': data['quantity'],
                        'avg_cost': data['avg_cost'],
                        'sector': data['sector']
                    })
                
                # Clear validation session state
                self._clear_validation_state()
                
                self.show_success(f"✅ {data['symbol']} added to portfolio!")
                st.rerun()
                return True
            
            elif data['action'] == 'cancel':
                # Clear validation session state
                self._clear_validation_state()
                st.rerun()
                return True
            
            return False
            
        except Exception as e:
            self.show_error(f"Error adding symbol: {str(e)}")
            return False
    
    def _clear_validation_state(self) -> None:
        """Clear validation session state."""
        for key in ['validated_symbol', 'validated_company', 'validated_sector', 'validation_success']:
            if key in st.session_state:
                del st.session_state[key]


@dialog_component("Update Position", width="medium")
class UpdatePositionDialog(BaseDialog):
    """Dialog for updating an existing position."""
    
    def __init__(self, portfolio_id: str, position: Dict[str, Any]):
        """
        Initialize update position dialog.
        
        Args:
            portfolio_id: Portfolio ID
            position: Position data to update
        """
        super().__init__("Update Position", width="medium")
        self.portfolio_id = portfolio_id
        self.position = position
    
    def render_content(self) -> Optional[Dict[str, Any]]:
        """Render update position dialog content."""
        st.markdown(f"**Update Position: {self.position['symbol']}**")
        st.markdown("---")
        
        # Display current position info
        st.info(f"**Company**: {self.position.get('company_name', 'Unknown')}")
        st.info(f"**Current Quantity**: {self.position.get('quantity', 0)}")
        st.info(f"**Current Avg Cost**: HK${self.position.get('avg_cost', 0.0):.2f}")
        
        st.markdown("---")
        
        # Input fields for new values
        col_qty, col_cost = st.columns(2)
        
        with col_qty:
            new_quantity = st.number_input(
                "New Quantity:",
                min_value=0,
                value=self.position.get('quantity', 0),
                step=1,
                format="%d",
                help="Updated number of shares (0 to remove from active positions)"
            )
        
        with col_cost:
            new_avg_cost = st.number_input(
                "New Average Cost (HK$):",
                min_value=0.0,
                value=float(self.position.get('avg_cost', 0.0)),
                step=0.01,
                format="%.2f",
                help="Updated average cost per share in HK$"
            )
        
        # Show change summary
        qty_change = new_quantity - self.position.get('quantity', 0)
        cost_change = new_avg_cost - float(self.position.get('avg_cost', 0.0))
        
        if qty_change != 0 or cost_change != 0:
            st.markdown("**Changes:**")
            if qty_change != 0:
                change_color = "🔴" if qty_change < 0 else "🟢"
                st.write(f"{change_color} Quantity: {qty_change:+d} shares")
            if abs(cost_change) > 0.001:
                change_color = "🔴" if cost_change < 0 else "🟢"
                st.write(f"{change_color} Average Cost: HK${cost_change:+.2f}")
        
        st.markdown("---")
        
        # Action buttons
        return self._render_update_buttons(new_quantity, new_avg_cost)
    
    def _render_update_buttons(self, new_quantity: int, new_avg_cost: float) -> Optional[Dict[str, Any]]:
        """Render update action buttons."""
        col_update, col_cancel = st.columns(2)
        
        with col_update:
            # Check if there are changes
            has_changes = (new_quantity != self.position.get('quantity', 0) or 
                          abs(new_avg_cost - float(self.position.get('avg_cost', 0.0))) > 0.001)
            
            if st.button("✅ Update Position", disabled=not has_changes, use_container_width=True, type="primary"):
                return {
                    'action': 'update',
                    'symbol': self.position['symbol'],
                    'new_quantity': new_quantity,
                    'new_avg_cost': new_avg_cost,
                    'old_quantity': self.position.get('quantity', 0),
                    'old_avg_cost': self.position.get('avg_cost', 0.0)
                }
        
        with col_cancel:
            if st.button("❌ Cancel", use_container_width=True):
                return {
                    'action': 'cancel'
                }
        
        return None
    
    def on_submit(self, data: Dict[str, Any]) -> bool:
        """Handle update position submission."""
        try:
            if data['action'] == 'update':
                # Update the position in session state
                if hasattr(st.session_state, 'portfolios') and self.portfolio_id in st.session_state.portfolios:
                    # Find and update the position
                    positions = st.session_state.portfolios[self.portfolio_id]['positions']
                    for i, pos in enumerate(positions):
                        if pos['symbol'] == data['symbol']:
                            positions[i]['quantity'] = data['new_quantity']
                            positions[i]['avg_cost'] = data['new_avg_cost']
                            break
                
                # Track modifications for saving
                modified_key = f'modified_positions_{self.portfolio_id}'
                if modified_key not in st.session_state:
                    st.session_state[modified_key] = {}
                
                st.session_state[modified_key][data['symbol']] = {
                    'symbol': data['symbol'],
                    'company_name': self.position.get('company_name'),
                    'quantity': data['new_quantity'],
                    'avg_cost': data['new_avg_cost'],
                    'sector': self.position.get('sector', 'Other')
                }
                
                self.show_success(f"✅ Position {data['symbol']} updated successfully!")
                st.rerun()
                return True
            
            elif data['action'] == 'cancel':
                st.rerun()
                return True
            
            return False
            
        except Exception as e:
            self.show_error(f"Error updating position: {str(e)}")
            return False


# Convenience functions for displaying dialogs
def show_add_symbol_dialog(portfolio_id: str):
    """Show the add symbol dialog."""
    dialog = AddSymbolDialog(portfolio_id)
    return dialog._streamlit_dialog(portfolio_id)


def show_update_position_dialog(portfolio_id: str, position: Dict[str, Any]):
    """Show the update position dialog."""
    dialog = UpdatePositionDialog(portfolio_id, position)
    return dialog._streamlit_dialog(portfolio_id, position)