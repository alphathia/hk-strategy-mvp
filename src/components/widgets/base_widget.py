"""
Base Widget Component for HK Strategy Dashboard.

Provides abstract base class for all widget components.
Ensures consistent interface and behavior across all widgets.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Callable
import streamlit as st
import logging

# Setup logging
logger = logging.getLogger(__name__)


class BaseWidget(ABC):
    """
    Abstract base class for all widget components.
    
    Provides common functionality for widget rendering, state management,
    and user interaction handling.
    """
    
    def __init__(self, widget_id: str, title: str = None, description: str = None):
        """
        Initialize base widget.
        
        Args:
            widget_id: Unique widget identifier
            title: Widget title (optional)
            description: Widget description (optional)
        """
        self.widget_id = widget_id
        self.title = title
        self.description = description
        self.data = {}
        self.state_key = f"widget_{widget_id}"
        self._callback: Optional[Callable] = None
        
    @abstractmethod
    def render_content(self) -> Any:
        """
        Render the widget content.
        
        This method must be implemented by subclasses to define
        the specific widget UI and functionality.
        
        Returns:
            Widget data or interaction result
        """
        pass
    
    def set_callback(self, callback: Callable[[Any], None]) -> None:
        """
        Set callback function to execute on widget interaction.
        
        Args:
            callback: Function to call with widget data
        """
        self._callback = callback
    
    def render_title(self) -> None:
        """Render widget title if provided."""
        if self.title:
            st.subheader(self.title)
    
    def render_description(self) -> None:
        """Render widget description if provided."""
        if self.description:
            st.markdown(self.description)
    
    def get_state(self, key: str = None, default: Any = None) -> Any:
        """
        Get widget state value.
        
        Args:
            key: State key (uses widget_id if None)
            default: Default value if key not found
            
        Returns:
            State value
        """
        state_key = key or self.state_key
        return st.session_state.get(state_key, default)
    
    def set_state(self, value: Any, key: str = None) -> None:
        """
        Set widget state value.
        
        Args:
            value: Value to set
            key: State key (uses widget_id if None)
        """
        state_key = key or self.state_key
        st.session_state[state_key] = value
    
    def clear_state(self, key: str = None) -> None:
        """
        Clear widget state.
        
        Args:
            key: State key to clear (uses widget_id if None)
        """
        state_key = key or self.state_key
        if state_key in st.session_state:
            del st.session_state[state_key]
    
    def on_change(self, value: Any) -> None:
        """
        Handle widget value change.
        
        Args:
            value: New widget value
        """
        try:
            # Store value in state
            self.set_state(value)
            
            # Execute callback if provided
            if self._callback:
                self._callback(value)
            
            logger.debug(f"Widget {self.widget_id} changed: {value}")
            
        except Exception as e:
            logger.error(f"Widget change handler error: {str(e)}")
    
    def render(self) -> Any:
        """
        Render the complete widget.
        
        Returns:
            Widget result/data
        """
        try:
            # Render title
            self.render_title()
            
            # Render description
            self.render_description()
            
            # Render content
            result = self.render_content()
            
            # Store result
            if result is not None:
                self.data = result
            
            return result
            
        except Exception as e:
            logger.error(f"Widget rendering error: {str(e)}")
            st.error(f"Widget error: {str(e)}")
            return None
    
    def get_data(self) -> Dict[str, Any]:
        """Get current widget data."""
        return self.data.copy() if isinstance(self.data, dict) else {'value': self.data}
    
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


class ContainerWidget(BaseWidget):
    """Base class for widgets that contain other elements."""
    
    def __init__(self, widget_id: str, title: str = None, description: str = None,
                 container_type: str = "container"):
        """
        Initialize container widget.
        
        Args:
            widget_id: Unique widget identifier
            title: Widget title (optional)
            description: Widget description (optional)
            container_type: Type of container ("container", "columns", "expander", "tabs")
        """
        super().__init__(widget_id, title, description)
        self.container_type = container_type
        self.children = []
    
    def add_child(self, child_widget: 'BaseWidget') -> None:
        """Add child widget."""
        self.children.append(child_widget)
    
    def render_container(self):
        """Render appropriate container type."""
        if self.container_type == "container":
            return st.container()
        elif self.container_type == "expander":
            return st.expander(self.title or "Details", expanded=True)
        else:
            return st.container()  # Default fallback


class MetricWidget(BaseWidget):
    """Base class for metric display widgets."""
    
    def render_metric(self, label: str, value: Any, delta: Any = None, 
                     help: str = None) -> None:
        """
        Render a metric display.
        
        Args:
            label: Metric label
            value: Metric value
            delta: Delta value (optional)
            help: Help text (optional)
        """
        st.metric(
            label=label,
            value=value,
            delta=delta,
            help=help
        )


class SelectorWidget(BaseWidget):
    """Base class for selection widgets."""
    
    def __init__(self, widget_id: str, title: str = None, description: str = None,
                 options: List[Any] = None, default_option: Any = None):
        """
        Initialize selector widget.
        
        Args:
            widget_id: Unique widget identifier
            title: Widget title (optional)
            description: Widget description (optional)
            options: Available options
            default_option: Default selected option
        """
        super().__init__(widget_id, title, description)
        self.options = options or []
        self.default_option = default_option
    
    def set_options(self, options: List[Any]) -> None:
        """Update widget options."""
        self.options = options
    
    def get_selected_option(self) -> Any:
        """Get currently selected option."""
        return self.get_state(default=self.default_option)