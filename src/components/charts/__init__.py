"""
Chart Components for HK Strategy Dashboard.

This module contains chart components for displaying financial data
with Plotly integration. All charts inherit from BaseChart.
"""

from .base_chart import BaseChart

# Chart registry - populated as charts are implemented
CHART_REGISTRY = {
    # Will be populated with actual chart implementations
    # 'price': PriceChart,
    # 'portfolio': PortfolioChart,
    # 'indicators': IndicatorsChart,
    # 'comparison': ComparisonChart,
}

__all__ = [
    'BaseChart',
    'CHART_REGISTRY'
]


def get_chart(chart_key: str):
    """Get chart class by key."""
    return CHART_REGISTRY.get(chart_key)


def create_chart(chart_key: str, **kwargs):
    """Create chart instance by key."""
    chart_class = get_chart(chart_key)
    return chart_class(**kwargs) if chart_class else None