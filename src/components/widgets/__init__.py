"""
Widget Components for HK Strategy Dashboard.

This module contains reusable widget components for UI elements.
All widgets inherit from BaseWidget and provide consistent behavior.
"""

from .base_widget import BaseWidget

# Widget registry - populated as widgets are implemented
WIDGET_REGISTRY = {
    # Will be populated with actual widget implementations
    # 'metrics': MetricsWidget,
    # 'status': StatusWidget,
    # 'portfolio_selector': PortfolioSelectorWidget,
    # 'symbol_selector': SymbolSelectorWidget,
}

__all__ = [
    'BaseWidget',
    'WIDGET_REGISTRY'
]


def get_widget(widget_key: str):
    """Get widget class by key."""
    return WIDGET_REGISTRY.get(widget_key)


def create_widget(widget_key: str, **kwargs):
    """Create widget instance by key."""
    widget_class = get_widget(widget_key)
    return widget_class(**kwargs) if widget_class else None