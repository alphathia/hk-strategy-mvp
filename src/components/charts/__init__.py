"""
Chart Components Package.

Plotly-based chart components for data visualization.
All chart components inherit from BaseChart and provide factory pattern access.
"""

from .base_chart import BaseChart, CandlestickChart, LineChart
from .price_chart import PriceChart, SimplePriceChart
from .portfolio_chart import (
    PortfolioComparisonChart, 
    PortfolioAllocationChart, 
    PortfolioPnLChart,
    PortfolioPerformanceChart,
    PortfolioSummaryCharts
)
from .indicator_chart import (
    RSIChart,
    MACDChart, 
    BollingerBandsChart,
    MultiIndicatorChart
)

# Chart registry for factory pattern
CHART_REGISTRY = {
    'base': BaseChart,
    'candlestick': CandlestickChart,
    'line': LineChart,
    'price': PriceChart,
    'simple_price': SimplePriceChart,
    'portfolio_comparison': PortfolioComparisonChart,
    'portfolio_allocation': PortfolioAllocationChart,
    'portfolio_pnl': PortfolioPnLChart,
    'portfolio_performance': PortfolioPerformanceChart,
    'rsi': RSIChart,
    'macd': MACDChart,
    'bollinger_bands': BollingerBandsChart,
    'multi_indicator': MultiIndicatorChart
}

def get_chart(chart_type: str) -> type:
    """
    Get chart class by type.
    
    Args:
        chart_type: Type of chart to get
        
    Returns:
        Chart class or None if not found
    """
    return CHART_REGISTRY.get(chart_type)

def create_chart(chart_type: str, *args, **kwargs):
    """
    Create chart instance by type.
    
    Args:
        chart_type: Type of chart to create
        *args: Positional arguments for chart
        **kwargs: Keyword arguments for chart
        
    Returns:
        Chart instance or None if type not found
    """
    chart_class = get_chart(chart_type)
    return chart_class(*args, **kwargs) if chart_class else None

__all__ = [
    'BaseChart', 'CandlestickChart', 'LineChart',
    'PriceChart', 'SimplePriceChart',
    'PortfolioComparisonChart', 'PortfolioAllocationChart', 'PortfolioPnLChart',
    'PortfolioPerformanceChart', 'PortfolioSummaryCharts',
    'RSIChart', 'MACDChart', 'BollingerBandsChart', 'MultiIndicatorChart',
    'CHART_REGISTRY', 'get_chart', 'create_chart'
]