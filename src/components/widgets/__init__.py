"""
Widget Components Package.

Reusable widget components for UI elements and data display.
All widgets inherit from BaseWidget and provide consistent behavior.
"""

from .base_widget import BaseWidget, MetricWidget, SelectorWidget
from .metric_widget import (
    MetricWidget, 
    PortfolioMetricsWidget, 
    ComparisonMetricsWidget,
    TechnicalIndicatorWidget
)
from .selector_widget import (
    SelectorWidget,
    PortfolioSelectorWidget,
    SymbolSelectorWidget,
    AnalysisSelectorWidget,
    NavigationWidget
)
from .status_widget import (
    StatusWidget,
    SystemHealthWidget,
    ProgressWidget,
    LoadingWidget,
    ConnectivityWidget,
    NotificationWidget
)

# Widget registry for factory pattern
WIDGET_REGISTRY = {
    'base': BaseWidget,
    'metric': MetricWidget,
    'selector': SelectorWidget,
    'portfolio_metrics': PortfolioMetricsWidget,
    'comparison_metrics': ComparisonMetricsWidget,
    'technical_indicators': TechnicalIndicatorWidget,
    'portfolio_selector': PortfolioSelectorWidget,
    'symbol_selector': SymbolSelectorWidget,
    'analysis_selector': AnalysisSelectorWidget,
    'navigation': NavigationWidget,
    'status': StatusWidget,
    'system_health': SystemHealthWidget,
    'progress': ProgressWidget,
    'loading': LoadingWidget,
    'connectivity': ConnectivityWidget,
    'notifications': NotificationWidget
}

def get_widget(widget_type: str) -> type:
    """
    Get widget class by type.
    
    Args:
        widget_type: Type of widget to get
        
    Returns:
        Widget class or None if not found
    """
    return WIDGET_REGISTRY.get(widget_type)

def create_widget(widget_type: str, *args, **kwargs):
    """
    Create widget instance by type.
    
    Args:
        widget_type: Type of widget to create
        *args: Positional arguments for widget
        **kwargs: Keyword arguments for widget
        
    Returns:
        Widget instance or None if type not found
    """
    widget_class = get_widget(widget_type)
    return widget_class(*args, **kwargs) if widget_class else None

__all__ = [
    'BaseWidget', 'MetricWidget', 'SelectorWidget',
    'PortfolioMetricsWidget', 'ComparisonMetricsWidget', 'TechnicalIndicatorWidget',
    'PortfolioSelectorWidget', 'SymbolSelectorWidget', 'AnalysisSelectorWidget', 'NavigationWidget',
    'StatusWidget', 'SystemHealthWidget', 'ProgressWidget', 'LoadingWidget', 
    'ConnectivityWidget', 'NotificationWidget',
    'WIDGET_REGISTRY', 'get_widget', 'create_widget'
]