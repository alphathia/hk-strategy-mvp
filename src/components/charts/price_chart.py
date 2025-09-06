"""
Price Chart Component.

Candlestick and price line charts for stock analysis.
Extracted from dashboard.py for modular architecture.
"""

import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Optional, Any
import logging

from .base_chart import BaseChart
from src.utils.chart_utils import (
    get_candlestick_layout_config,
    create_candlestick_trace,
    create_line_trace,
    create_volume_trace,
    add_technical_indicator_trace,
    format_chart_for_streamlit
)
from src.utils.indicator_utils import fetch_technical_analysis_data

logger = logging.getLogger(__name__)


class PriceChart(BaseChart):
    """
    Candlestick price chart with technical indicators support.
    """
    
    def __init__(self, symbol: str, chart_type: str = "candlestick", 
                 height: int = 500, show_volume: bool = True):
        """
        Initialize price chart.
        
        Args:
            symbol: Stock symbol
            chart_type: Chart type ('candlestick' or 'line')
            height: Chart height in pixels
            show_volume: Whether to show volume chart
        """
        super().__init__(title=f"{symbol} Price Chart", height=height)
        self.symbol = symbol
        self.chart_type = chart_type
        self.show_volume = show_volume
        self.technical_indicators = []
    
    def add_technical_indicators(self, indicators: List[str]) -> None:
        """
        Add technical indicators to the chart.
        
        Args:
            indicators: List of indicator codes to add
        """
        self.technical_indicators = indicators
    
    def prepare_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Prepare price data for chart creation.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Prepared data dictionary
        """
        try:
            if not self.validate_data(data):
                return {}
            
            # Ensure required columns exist
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_cols = [col for col in required_cols if col not in data.columns]
            if missing_cols:
                logger.error(f"Missing required columns: {missing_cols}")
                return {}
            
            prepared_data = {
                'price_data': data,
                'symbol': self.symbol,
                'dates': data.index.tolist(),
                'technical_data': {}
            }
            
            # Fetch technical indicators if requested
            if self.technical_indicators:
                tech_data = fetch_technical_analysis_data(self.symbol)
                if tech_data:
                    prepared_data['technical_data'] = tech_data
            
            return prepared_data
            
        except Exception as e:
            logger.error(f"Error preparing price data: {e}")
            return {}
    
    def build_chart(self, prepared_data: Dict[str, Any]) -> go.Figure:
        """
        Build the price chart.
        
        Args:
            prepared_data: Prepared data dictionary
            
        Returns:
            Plotly figure
        """
        try:
            if not prepared_data:
                return go.Figure()
            
            price_data = prepared_data['price_data']
            symbol = prepared_data.get('symbol', self.symbol)
            
            # Create figure
            fig = go.Figure()
            
            # Add main price chart
            if self.chart_type == "candlestick":
                candlestick_trace = create_candlestick_trace(price_data, symbol)
                fig.add_trace(candlestick_trace)
            else:  # line chart
                line_trace = create_line_trace(
                    price_data.index, 
                    price_data['Close'], 
                    f"{symbol} Close Price",
                    color="#1f77b4"
                )
                fig.add_trace(line_trace)
            
            # Add technical indicators
            self._add_technical_indicators(fig, prepared_data.get('technical_data', {}))
            
            # Apply layout
            layout_config = get_candlestick_layout_config(
                title=f"{symbol} Price Chart",
                height=self.height
            )
            fig.update_layout(**layout_config)
            
            return fig
            
        except Exception as e:
            logger.error(f"Error building price chart: {e}")
            return go.Figure()
    
    def build_volume_chart(self, data: pd.DataFrame) -> Optional[go.Figure]:
        """
        Build a separate volume chart.
        
        Args:
            data: DataFrame with Volume data
            
        Returns:
            Plotly figure for volume or None
        """
        try:
            if not self.show_volume or 'Volume' not in data.columns:
                return None
            
            fig_volume = go.Figure()
            volume_trace = create_volume_trace(data, "Volume")
            fig_volume.add_trace(volume_trace)
            
            # Volume-specific layout
            layout_config = {
                'height': 150,
                'margin': {'l': 50, 'r': 50, 't': 20, 'b': 50},
                'showlegend': False,
                'xaxis': {'showgrid': True},
                'yaxis': {'title': 'Volume', 'showgrid': True}
            }
            
            fig_volume.update_layout(**layout_config)
            
            return fig_volume
            
        except Exception as e:
            logger.error(f"Error building volume chart: {e}")
            return None
    
    def _add_technical_indicators(self, fig: go.Figure, tech_data: Dict[str, Any]) -> None:
        """
        Add technical indicators to the chart.
        
        Args:
            fig: Plotly figure to add indicators to
            tech_data: Technical analysis data
        """
        try:
            if not tech_data or not self.technical_indicators:
                return
            
            dates = tech_data.get('dates', [])
            
            for indicator in self.technical_indicators:
                if indicator in tech_data:
                    values = tech_data[indicator]
                    if values and any(v is not None for v in values):
                        indicator_data = {
                            'dates': dates,
                            'values': values
                        }
                        add_technical_indicator_trace(fig, indicator_data, indicator)
            
        except Exception as e:
            logger.error(f"Error adding technical indicators: {e}")
    
    def render(self, data: pd.DataFrame) -> Optional[go.Figure]:
        """
        Render the complete price chart.
        
        Args:
            data: OHLCV data
            
        Returns:
            Main price chart figure
        """
        try:
            prepared_data = self.prepare_data(data)
            if not prepared_data:
                logger.warning(f"No data to render for {self.symbol}")
                return None
            
            main_chart = self.build_chart(prepared_data)
            return main_chart
            
        except Exception as e:
            logger.error(f"Error rendering price chart: {e}")
            return None
    
    def render_with_volume(self, data: pd.DataFrame) -> tuple[Optional[go.Figure], Optional[go.Figure]]:
        """
        Render both price and volume charts.
        
        Args:
            data: OHLCV data
            
        Returns:
            Tuple of (price_chart, volume_chart)
        """
        try:
            price_chart = self.render(data)
            volume_chart = self.build_volume_chart(data) if self.show_volume else None
            
            return price_chart, volume_chart
            
        except Exception as e:
            logger.error(f"Error rendering charts with volume: {e}")
            return None, None
    
    def get_streamlit_config(self) -> Dict[str, Any]:
        """
        Get Streamlit-specific chart configuration.
        
        Returns:
            Configuration for st.plotly_chart()
        """
        return format_chart_for_streamlit(go.Figure())


class SimplePriceChart(BaseChart):
    """
    Simple line chart for price display.
    """
    
    def __init__(self, symbol: str, height: int = 300):
        """
        Initialize simple price chart.
        
        Args:
            symbol: Stock symbol
            height: Chart height in pixels
        """
        super().__init__(title=f"{symbol} Price", height=height)
        self.symbol = symbol
    
    def prepare_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Prepare data for simple chart.
        
        Args:
            data: DataFrame with price data
            
        Returns:
            Prepared data dictionary
        """
        try:
            if 'Close' not in data.columns:
                logger.error("Close price column not found")
                return {}
            
            return {
                'dates': data.index.tolist(),
                'prices': data['Close'].tolist(),
                'symbol': self.symbol
            }
            
        except Exception as e:
            logger.error(f"Error preparing simple chart data: {e}")
            return {}
    
    def build_chart(self, prepared_data: Dict[str, Any]) -> go.Figure:
        """
        Build simple price line chart.
        
        Args:
            prepared_data: Prepared data dictionary
            
        Returns:
            Plotly figure
        """
        try:
            if not prepared_data:
                return go.Figure()
            
            fig = go.Figure()
            
            line_trace = create_line_trace(
                prepared_data['dates'],
                prepared_data['prices'],
                prepared_data['symbol'],
                color="#2E86AB"
            )
            
            fig.add_trace(line_trace)
            
            # Simple layout
            fig.update_layout(
                title=self.title,
                height=self.height,
                showlegend=False,
                margin={'l': 20, 'r': 20, 't': 40, 'b': 20}
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error building simple chart: {e}")
            return go.Figure()