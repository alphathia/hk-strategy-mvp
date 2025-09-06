"""
Technical Indicators Selection Dialog Component.

Modal dialog for selecting technical indicators to overlay on price charts.
Extracted from dashboard.py lines 35-116.
"""

from typing import Dict, Any, Optional, List
import streamlit as st

from .base_dialog import BaseDialog, dialog_component


@dialog_component("Select Technical Indicators", width="medium")
class IndicatorsDialog(BaseDialog):
    """Dialog for selecting technical indicators to display on charts."""
    
    def __init__(self):
        """Initialize indicators dialog."""
        super().__init__("Select Technical Indicators", width="medium")
        
        # Available technical indicators
        self.available_indicators = [
            ("RSI (7)", "rsi_7"),
            ("RSI (14)", "rsi_14"), 
            ("RSI (21)", "rsi_21"),
            ("MACD", "macd"),
            ("MACD Signal", "macd_signal"),
            ("SMA (20)", "sma_20"),
            ("EMA (12)", "ema_12"),
            ("EMA (26)", "ema_26"),
            ("EMA (50)", "ema_50"),
            ("EMA (100)", "ema_100"),
            ("Bollinger Upper", "bollinger_upper"),
            ("Bollinger Middle", "bollinger_middle"),
            ("Bollinger Lower", "bollinger_lower"),
            ("Volume SMA (20)", "volume_sma_20")
        ]
        
        self.max_selection = 3
    
    def _initialize_session_state(self) -> None:
        """Initialize session state for indicator selection."""
        if 'selected_indicators_modal' not in st.session_state:
            st.session_state.selected_indicators_modal = []
    
    def _get_current_selection(self) -> List[str]:
        """Get current indicator selection."""
        return st.session_state.get('selected_indicators_modal', [])
    
    def _update_selection(self, indicator_code: str, selected: bool) -> None:
        """Update indicator selection state."""
        current_selection = self._get_current_selection()
        
        if selected and indicator_code not in current_selection:
            if len(current_selection) < self.max_selection:
                st.session_state.selected_indicators_modal.append(indicator_code)
        elif not selected and indicator_code in current_selection:
            st.session_state.selected_indicators_modal.remove(indicator_code)
    
    def render_content(self) -> Optional[Dict[str, Any]]:
        """Render indicators selection dialog content."""
        # Initialize session state
        self._initialize_session_state()
        
        st.markdown("**Select up to 3 technical indicators to overlay on the price chart:**")
        st.markdown("---")
        
        # Get current selection
        current_selection = self._get_current_selection()
        
        # Create checkboxes in a grid layout
        cols = st.columns(3)
        
        for i, (name, code) in enumerate(self.available_indicators):
            col_idx = i % 3
            with cols[col_idx]:
                # Check if this indicator is currently selected
                is_selected = code in current_selection
                
                # Disable checkbox if max selections reached and this one isn't selected
                max_reached = len(current_selection) >= self.max_selection and not is_selected
                
                checkbox_result = st.checkbox(
                    name, 
                    value=is_selected, 
                    disabled=max_reached,
                    key=f"modal_indicator_{code}"
                )
                
                # Update selection state
                self._update_selection(code, checkbox_result)
        
        # Get updated selection count
        selected_count = len(self._get_current_selection())
        
        # Show selection status
        st.markdown("---")
        self._render_selection_status(selected_count)
        
        # Action buttons
        return self._render_action_buttons(selected_count)
    
    def _render_selection_status(self, selected_count: int) -> None:
        """Render selection status message."""
        if selected_count == 0:
            st.info("📊 Select 1-3 indicators to display")
        elif selected_count >= self.max_selection:
            st.success(f"✅ Maximum selected: {selected_count}/{self.max_selection}")
        else:
            st.info(f"📊 Selected: {selected_count}/{self.max_selection}")
    
    def _render_action_buttons(self, selected_count: int) -> Optional[Dict[str, Any]]:
        """Render action buttons and handle clicks."""
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Show Indicators", 
                        disabled=selected_count == 0, 
                        type="primary", 
                        use_container_width=True):
                # Return selection data
                return {
                    'action': 'confirm',
                    'selected_indicators': self._get_current_selection().copy()
                }
        
        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                # Reset selection and cancel
                st.session_state.selected_indicators_modal = []
                return {
                    'action': 'cancel',
                    'selected_indicators': []
                }
        
        return None
    
    def on_submit(self, data: Dict[str, Any]) -> bool:
        """Handle dialog submission."""
        try:
            if data['action'] == 'confirm':
                # Store confirmed selection in session state
                st.session_state.confirmed_indicators = data['selected_indicators']
                st.session_state.show_indicators_clicked = True
                self.show_success(f"✅ Selected {len(data['selected_indicators'])} indicators")
                
            elif data['action'] == 'cancel':
                # Clear selection
                if 'confirmed_indicators' in st.session_state:
                    del st.session_state.confirmed_indicators
                if 'show_indicators_clicked' in st.session_state:
                    del st.session_state.show_indicators_clicked
            
            # Close dialog
            st.rerun()
            return True
            
        except Exception as e:
            self.show_error(f"Error processing indicator selection: {str(e)}")
            return False


# Convenience function for displaying the dialog
def show_indicators_dialog():
    """Show the technical indicators selection dialog."""
    dialog = IndicatorsDialog()
    return dialog._streamlit_dialog()