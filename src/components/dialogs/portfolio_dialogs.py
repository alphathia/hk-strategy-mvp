"""
Portfolio Management Dialog Components.

Modal dialogs for creating, copying, and managing portfolios.
Extracted from dashboard.py lines 117-214 and 536-620.
"""

import time
from typing import Dict, Any, Optional
import streamlit as st

from .base_dialog import BaseDialog, dialog_component


@dialog_component("Create New Portfolio", width="medium")
class CreatePortfolioDialog(BaseDialog):
    """Dialog for creating a new portfolio."""
    
    def __init__(self):
        """Initialize create portfolio dialog."""
        super().__init__("Create New Portfolio", width="medium")
    
    def render_content(self) -> Optional[Dict[str, Any]]:
        """Render portfolio creation dialog content."""
        st.markdown("**Create a new portfolio to track your investments**")
        st.markdown("---")
        
        # Form fields
        new_portfolio_id = st.text_input(
            "Portfolio ID:",
            placeholder="e.g., TECH_GROWTH",
            key="new_portfolio_id_modal",
            help="Unique identifier for the portfolio (no spaces, use underscores)"
        )
        
        new_portfolio_name = st.text_input(
            "Portfolio Name:",
            placeholder="e.g., Technology Growth Stocks",
            key="new_portfolio_name_modal",
            help="Display name for the portfolio"
        )
        
        new_portfolio_desc = st.text_area(
            "Description:",
            placeholder="Brief description of the portfolio strategy...",
            key="new_portfolio_desc_modal",
            help="Optional description of the portfolio"
        )
        
        st.markdown("---")
        
        # Validation
        error_msg = self._validate_portfolio_data(new_portfolio_id, new_portfolio_name)
        
        if error_msg:
            st.error(f"❌ {error_msg}")
        
        # Action buttons
        return self._render_action_buttons(new_portfolio_id, new_portfolio_name, new_portfolio_desc, error_msg)
    
    def _validate_portfolio_data(self, portfolio_id: str, portfolio_name: str) -> str:
        """Validate portfolio form data."""
        if portfolio_id:
            portfolio_id_clean = portfolio_id.strip().upper().replace(' ', '_')
            if hasattr(st.session_state, 'portfolios') and portfolio_id_clean in st.session_state.portfolios:
                return f"Portfolio '{portfolio_id_clean}' already exists!"
            elif not portfolio_name.strip():
                return "Portfolio Name is required"
        elif portfolio_name:
            return "Portfolio ID is required"
        
        return ""
    
    def _render_action_buttons(self, portfolio_id: str, portfolio_name: str, 
                              portfolio_desc: str, error_msg: str) -> Optional[Dict[str, Any]]:
        """Render action buttons and handle clicks."""
        col_create, col_cancel = st.columns(2)
        
        with col_create:
            disabled = bool(error_msg) or not portfolio_id or not portfolio_name
            if st.button("✅ Create Portfolio", use_container_width=True, disabled=disabled):
                return {
                    'action': 'create',
                    'portfolio_id': portfolio_id.strip().upper().replace(' ', '_'),
                    'portfolio_name': portfolio_name.strip(),
                    'portfolio_desc': portfolio_desc.strip()
                }
        
        with col_cancel:
            if st.button("❌ Cancel", use_container_width=True):
                return {
                    'action': 'cancel'
                }
        
        return None
    
    def on_submit(self, data: Dict[str, Any]) -> bool:
        """Handle portfolio creation submission."""
        try:
            if data['action'] == 'create':
                # Create new portfolio using portfolio manager
                portfolio_manager = st.session_state.get('portfolio_manager')
                if not portfolio_manager:
                    self.show_error("❌ Portfolio manager not available")
                    return False
                
                success = portfolio_manager.create_portfolio(
                    data['portfolio_id'],
                    data['portfolio_name'],
                    data['portfolio_desc']
                )
                
                if success:
                    # Refresh portfolios from database
                    st.session_state.portfolios = portfolio_manager.get_all_portfolios()
                    self.show_success(f"✅ Portfolio '{data['portfolio_name']}' created successfully!")
                    
                    # Clear form fields
                    self._clear_form_fields()
                    
                    # Brief delay to show success message
                    time.sleep(1)
                    st.rerun()
                    return True
                else:
                    self.show_error(f"❌ Failed to create portfolio '{data['portfolio_name']}'")
                    st.warning("💡 **Possible reasons:**")
                    st.markdown("- Portfolio ID already exists in database")
                    st.markdown("- Database connection issue")
                    st.info("💡 **Try:** Use a different Portfolio ID or check database connection")
                    return False
            
            elif data['action'] == 'cancel':
                # Clear form fields and close
                self._clear_form_fields()
                st.rerun()
                return True
            
            return False
            
        except Exception as e:
            self.show_error(f"Error creating portfolio: {str(e)}")
            return False
    
    def _clear_form_fields(self) -> None:
        """Clear form fields."""
        for key in ['new_portfolio_id_modal', 'new_portfolio_name_modal', 'new_portfolio_desc_modal']:
            if key in st.session_state:
                del st.session_state[key]


@dialog_component("Copy Portfolio", width="medium")
class CopyPortfolioDialog(BaseDialog):
    """Dialog for copying an existing portfolio."""
    
    def __init__(self, source_portfolio_id: str):
        """
        Initialize copy portfolio dialog.
        
        Args:
            source_portfolio_id: ID of portfolio to copy
        """
        super().__init__("Copy Portfolio", width="medium")
        self.source_portfolio_id = source_portfolio_id
    
    def render_content(self) -> Optional[Dict[str, Any]]:
        """Render portfolio copy dialog content."""
        # Check if source portfolio exists
        if not hasattr(st.session_state, 'portfolios') or self.source_portfolio_id not in st.session_state.portfolios:
            st.error(f"❌ Portfolio '{self.source_portfolio_id}' not found in current session")
            return None
        
        source_portfolio = st.session_state.portfolios[self.source_portfolio_id]
        
        st.markdown(f"**Copy portfolio: {source_portfolio.get('name', self.source_portfolio_id)}**")
        st.markdown("---")
        
        # Show source portfolio info
        st.info(f"📊 Source Portfolio: **{source_portfolio.get('name', self.source_portfolio_id)}** ({self.source_portfolio_id})")
        
        position_count = len(source_portfolio.get('positions', []))
        st.info(f"📈 Positions to copy: **{position_count}** positions")
        
        st.markdown("---")
        
        # Form fields for new portfolio
        new_portfolio_id = st.text_input(
            "New Portfolio ID:",
            placeholder="e.g., TECH_GROWTH_COPY",
            key="copy_portfolio_id_modal",
            help="Unique identifier for the copied portfolio"
        )
        
        new_portfolio_name = st.text_input(
            "New Portfolio Name:",
            placeholder="e.g., Technology Growth Stocks (Copy)",
            key="copy_portfolio_name_modal", 
            help="Display name for the copied portfolio"
        )
        
        copy_positions = st.checkbox(
            "Copy all positions",
            value=True,
            key="copy_positions_modal",
            help="Include all stock positions from the source portfolio"
        )
        
        st.markdown("---")
        
        # Validation
        error_msg = self._validate_copy_data(new_portfolio_id, new_portfolio_name)
        
        if error_msg:
            st.error(f"❌ {error_msg}")
        
        # Action buttons
        return self._render_copy_buttons(new_portfolio_id, new_portfolio_name, copy_positions, error_msg)
    
    def _validate_copy_data(self, portfolio_id: str, portfolio_name: str) -> str:
        """Validate portfolio copy data."""
        if portfolio_id:
            portfolio_id_clean = portfolio_id.strip().upper().replace(' ', '_')
            if hasattr(st.session_state, 'portfolios') and portfolio_id_clean in st.session_state.portfolios:
                return f"Portfolio '{portfolio_id_clean}' already exists!"
            elif not portfolio_name.strip():
                return "Portfolio Name is required"
        elif portfolio_name:
            return "Portfolio ID is required"
        
        return ""
    
    def _render_copy_buttons(self, portfolio_id: str, portfolio_name: str, 
                           copy_positions: bool, error_msg: str) -> Optional[Dict[str, Any]]:
        """Render copy action buttons."""
        col_copy, col_cancel = st.columns(2)
        
        with col_copy:
            disabled = bool(error_msg) or not portfolio_id or not portfolio_name
            if st.button("📋 Copy Portfolio", use_container_width=True, disabled=disabled):
                return {
                    'action': 'copy',
                    'new_portfolio_id': portfolio_id.strip().upper().replace(' ', '_'),
                    'new_portfolio_name': portfolio_name.strip(),
                    'copy_positions': copy_positions,
                    'source_portfolio_id': self.source_portfolio_id
                }
        
        with col_cancel:
            if st.button("❌ Cancel", use_container_width=True):
                return {
                    'action': 'cancel'
                }
        
        return None
    
    def on_submit(self, data: Dict[str, Any]) -> bool:
        """Handle portfolio copy submission."""
        try:
            if data['action'] == 'copy':
                # Copy portfolio using portfolio manager
                portfolio_manager = st.session_state.get('portfolio_manager')
                if not portfolio_manager:
                    self.show_error("❌ Portfolio manager not available")
                    return False
                
                success = portfolio_manager.copy_portfolio(
                    data['source_portfolio_id'],
                    data['new_portfolio_id'],
                    data['new_portfolio_name'],
                    copy_positions=data['copy_positions']
                )
                
                if success:
                    # Refresh portfolios from database
                    st.session_state.portfolios = portfolio_manager.get_all_portfolios()
                    self.show_success(f"✅ Portfolio '{data['new_portfolio_name']}' copied successfully!")
                    
                    # Clear form fields
                    self._clear_copy_fields()
                    
                    # Brief delay to show success message
                    time.sleep(1)
                    st.rerun()
                    return True
                else:
                    self.show_error(f"❌ Failed to copy portfolio")
                    return False
            
            elif data['action'] == 'cancel':
                # Clear form fields and close
                self._clear_copy_fields()
                st.rerun()
                return True
            
            return False
            
        except Exception as e:
            self.show_error(f"Error copying portfolio: {str(e)}")
            return False
    
    def _clear_copy_fields(self) -> None:
        """Clear copy form fields."""
        for key in ['copy_portfolio_id_modal', 'copy_portfolio_name_modal', 'copy_positions_modal']:
            if key in st.session_state:
                del st.session_state[key]


# Convenience functions for displaying dialogs
def show_create_portfolio_dialog():
    """Show the create portfolio dialog."""
    dialog = CreatePortfolioDialog()
    return dialog._streamlit_dialog()


def show_copy_portfolio_dialog(source_portfolio_id: str):
    """Show the copy portfolio dialog."""
    dialog = CopyPortfolioDialog(source_portfolio_id)
    return dialog._streamlit_dialog(source_portfolio_id)