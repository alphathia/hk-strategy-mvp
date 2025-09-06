"""
Base Chart Component for HK Strategy Dashboard.

Provides abstract base class for all chart components using Plotly.
Ensures consistent interface and styling across all charts.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
import logging

# Setup logging
logger = logging.getLogger(__name__)


class BaseChart(ABC):
    """
    Abstract base class for all chart components.
    
    Provides common functionality for Plotly chart creation,
    styling, and Streamlit integration.
    """
    
    def __init__(self, title: str = None, height: int = 400, theme: str = "plotly"):
        """
        Initialize base chart.
        
        Args:
            title: Chart title
            height: Chart height in pixels
            theme: Chart theme ("plotly", "plotly_white", "plotly_dark")
        """
        self.title = title
        self.height = height
        self.theme = theme
        self.fig: Optional[go.Figure] = None
        self._data = None
        
    @abstractmethod
    def prepare_data(self, data: Any) -> Any:
        """
        Prepare data for chart rendering.
        
        Args:
            data: Raw data input
            
        Returns:
            Processed data ready for chart creation
        """
        pass
    
    @abstractmethod
    def build_chart(self, prepared_data: Any) -> go.Figure:
        """
        Build the Plotly chart figure.
        
        Args:
            prepared_data: Data prepared by prepare_data()
            
        Returns:
            Plotly Figure object
        """
        pass
    
    def apply_styling(self, fig: go.Figure) -> go.Figure:
        """
        Apply common styling to the chart.
        
        Args:
            fig: Plotly figure to style
            
        Returns:
            Styled figure
        """
        try:
            # Apply title
            if self.title:
                fig.update_layout(title=self.title)
            
            # Apply theme
            fig.update_layout(template=self.theme)
            
            # Set height
            fig.update_layout(height=self.height)
            
            # Common styling
            fig.update_layout(
                margin=dict(l=10, r=10, t=40, b=10),
                showlegend=True,
                hovermode='x unified'
            )
            
            # Apply responsive design
            fig.update_layout(
                autosize=True,
                font=dict(size=12)
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Chart styling error: {str(e)}")
            return fig
    
    def add_technical_indicators(self, fig: go.Figure, data: pd.DataFrame, 
                                indicators: List[str]) -> go.Figure:
        """
        Add technical indicators to the chart.
        
        Args:
            fig: Plotly figure
            data: DataFrame with indicator data
            indicators: List of indicator column names to add
            
        Returns:
            Figure with indicators added
        """
        try:
            for indicator in indicators:
                if indicator in data.columns:
                    fig.add_trace(
                        go.Scatter(
                            x=data.index,
                            y=data[indicator],
                            name=indicator.replace('_', ' ').title(),
                            line=dict(width=1),
                            opacity=0.7
                        )
                    )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error adding indicators: {str(e)}")
            return fig
    
    def validate_data(self, data: Any) -> bool:
        """
        Validate input data.
        
        Args:
            data: Data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        if data is None:
            logger.warning("Chart data is None")
            return False
        
        if isinstance(data, pd.DataFrame) and data.empty:
            logger.warning("Chart data is empty DataFrame")
            return False
        
        return True
    
    def render(self, data: Any, use_container_width: bool = True) -> bool:
        """
        Render the complete chart.
        
        Args:
            data: Data to chart
            use_container_width: Whether to use full container width
            
        Returns:
            True if rendered successfully, False otherwise
        """
        try:
            # Validate data
            if not self.validate_data(data):
                st.warning("❌ No data available for chart")
                return False
            
            # Prepare data
            prepared_data = self.prepare_data(data)
            if prepared_data is None:
                st.error("❌ Failed to prepare chart data")
                return False
            
            # Build chart
            self.fig = self.build_chart(prepared_data)
            if self.fig is None:
                st.error("❌ Failed to build chart")
                return False
            
            # Apply styling
            self.fig = self.apply_styling(self.fig)
            
            # Render with Streamlit
            st.plotly_chart(self.fig, use_container_width=use_container_width)
            
            # Store data reference
            self._data = data
            
            logger.info(f"Chart {self.__class__.__name__} rendered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Chart rendering error: {str(e)}")
            st.error(f"Chart error: {str(e)}")
            return False
    
    def export_data(self) -> Optional[pd.DataFrame]:
        """
        Export chart data as DataFrame.
        
        Returns:
            DataFrame with chart data, or None if no data
        """
        return self._data if isinstance(self._data, pd.DataFrame) else None
    
    def get_figure(self) -> Optional[go.Figure]:
        """
        Get the current Plotly figure.
        
        Returns:
            Current figure or None if not rendered
        """
        return self.fig
    
    def update_title(self, title: str) -> None:
        """
        Update chart title.
        
        Args:
            title: New title
        """
        self.title = title
        if self.fig:
            self.fig.update_layout(title=title)
    
    def update_height(self, height: int) -> None:
        """
        Update chart height.
        
        Args:
            height: New height in pixels
        """
        self.height = height
        if self.fig:
            self.fig.update_layout(height=height)


class CandlestickChart(BaseChart):
    """Base class for candlestick charts."""
    
    def build_candlestick_trace(self, data: pd.DataFrame) -> go.Candlestick:
        """
        Build candlestick trace.
        
        Args:
            data: DataFrame with OHLC data
            
        Returns:
            Candlestick trace
        """
        return go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name='Price'
        )


class LineChart(BaseChart):
    """Base class for line charts."""
    
    def build_line_trace(self, data: pd.DataFrame, column: str, 
                        name: str = None, color: str = None) -> go.Scatter:
        """
        Build line trace.
        
        Args:
            data: DataFrame with data
            column: Column name to plot
            name: Trace name
            color: Line color
            
        Returns:
            Scatter trace configured as line
        """
        return go.Scatter(
            x=data.index,
            y=data[column],
            mode='lines',
            name=name or column,
            line=dict(color=color) if color else None
        )