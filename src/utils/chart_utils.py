"""
Chart Creation and Styling Utilities.

Utility functions for creating and styling Plotly charts.
Extracted from dashboard.py for modular architecture.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, List, Optional, Any, Union
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def get_default_layout_config(title: str = "", height: int = 400) -> Dict[str, Any]:
    """
    Get default layout configuration for charts.
    
    Args:
        title: Chart title
        height: Chart height in pixels
        
    Returns:
        Layout configuration dictionary
    """
    return {
        'title': {
            'text': title,
            'x': 0.5,
            'font': {'size': 16, 'color': '#2E4057'}
        },
        'height': height,
        'margin': {'l': 50, 'r': 50, 't': 80, 'b': 50},
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'font': {'family': 'Arial, sans-serif', 'size': 12},
        'showlegend': True,
        'legend': {
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': 1.02,
            'xanchor': 'right',
            'x': 1
        },
        'xaxis': {
            'showgrid': True,
            'gridwidth': 1,
            'gridcolor': 'rgba(128,128,128,0.2)',
            'showline': True,
            'linewidth': 1,
            'linecolor': 'rgba(128,128,128,0.3)',
            'mirror': True
        },
        'yaxis': {
            'showgrid': True,
            'gridwidth': 1,
            'gridcolor': 'rgba(128,128,128,0.2)',
            'showline': True,
            'linewidth': 1,
            'linecolor': 'rgba(128,128,128,0.3)',
            'mirror': True
        }
    }


def get_candlestick_layout_config(title: str = "", height: int = 500) -> Dict[str, Any]:
    """
    Get layout configuration specific to candlestick charts.
    
    Args:
        title: Chart title
        height: Chart height in pixels
        
    Returns:
        Layout configuration dictionary
    """
    config = get_default_layout_config(title, height)
    config.update({
        'xaxis': {
            **config['xaxis'],
            'rangeslider': {'visible': False},
            'type': 'category'
        },
        'yaxis': {
            **config['yaxis'],
            'title': 'Price (HKD)',
            'side': 'right'
        }
    })
    return config


def create_candlestick_trace(data: pd.DataFrame, name: str = "Price") -> go.Candlestick:
    """
    Create a candlestick trace from OHLCV data.
    
    Args:
        data: DataFrame with OHLCV columns
        name: Trace name
        
    Returns:
        Plotly Candlestick trace
    """
    try:
        return go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name=name,
            increasing_line_color='#26C281',
            decreasing_line_color='#E74C3C',
            increasing_fillcolor='#26C281',
            decreasing_fillcolor='#E74C3C'
        )
    except KeyError as e:
        logger.error(f"Missing required OHLCV columns: {e}")
        raise
    except Exception as e:
        logger.error(f"Error creating candlestick trace: {e}")
        raise


def create_line_trace(x_data: Union[List, pd.Series], y_data: Union[List, pd.Series], 
                     name: str, color: str = "#1f77b4", width: int = 2) -> go.Scatter:
    """
    Create a line trace.
    
    Args:
        x_data: X-axis data
        y_data: Y-axis data
        name: Trace name
        color: Line color
        width: Line width
        
    Returns:
        Plotly Scatter trace in line mode
    """
    try:
        return go.Scatter(
            x=x_data,
            y=y_data,
            mode='lines',
            name=name,
            line=dict(color=color, width=width),
            hovertemplate=f'<b>{name}</b><br>' +
                         'Date: %{x}<br>' +
                         'Value: %{y:.2f}<br>' +
                         '<extra></extra>'
        )
    except Exception as e:
        logger.error(f"Error creating line trace for {name}: {e}")
        raise


def create_volume_trace(data: pd.DataFrame, name: str = "Volume") -> go.Bar:
    """
    Create a volume bar trace.
    
    Args:
        data: DataFrame with Volume column
        name: Trace name
        
    Returns:
        Plotly Bar trace for volume
    """
    try:
        return go.Bar(
            x=data.index,
            y=data['Volume'],
            name=name,
            marker_color='rgba(158,185,243,0.8)',
            hovertemplate='<b>Volume</b><br>' +
                         'Date: %{x}<br>' +
                         'Volume: %{y:,}<br>' +
                         '<extra></extra>'
        )
    except KeyError as e:
        logger.error(f"Missing Volume column: {e}")
        raise
    except Exception as e:
        logger.error(f"Error creating volume trace: {e}")
        raise


def create_bollinger_bands_traces(dates: List, upper: List[float], middle: List[float], 
                                 lower: List[float]) -> List[go.Scatter]:
    """
    Create Bollinger Bands traces.
    
    Args:
        dates: Date values
        upper: Upper band values
        middle: Middle band values
        lower: Lower band values
        
    Returns:
        List of Plotly traces for Bollinger Bands
    """
    try:
        traces = []
        
        # Upper band
        traces.append(go.Scatter(
            x=dates,
            y=upper,
            mode='lines',
            name='BB Upper',
            line=dict(color='rgba(68, 68, 68, 0.5)', width=1),
            showlegend=False
        ))
        
        # Lower band (with fill)
        traces.append(go.Scatter(
            x=dates,
            y=lower,
            mode='lines',
            name='Bollinger Bands',
            line=dict(color='rgba(68, 68, 68, 0.5)', width=1),
            fill='tonexty',
            fillcolor='rgba(68, 68, 68, 0.1)'
        ))
        
        # Middle band
        traces.append(go.Scatter(
            x=dates,
            y=middle,
            mode='lines',
            name='BB Middle',
            line=dict(color='orange', width=1.5)
        ))
        
        return traces
        
    except Exception as e:
        logger.error(f"Error creating Bollinger Bands traces: {e}")
        return []


def add_technical_indicator_trace(fig: go.Figure, indicator_data: Dict[str, Any], 
                                 indicator_name: str) -> None:
    """
    Add a technical indicator trace to an existing figure.
    
    Args:
        fig: Plotly figure to add trace to
        indicator_data: Dictionary with indicator data
        indicator_name: Name of the indicator
    """
    try:
        dates = indicator_data.get('dates', [])
        values = indicator_data.get('values', [])
        
        if not dates or not values:
            logger.warning(f"No data available for indicator {indicator_name}")
            return
        
        # Color mapping for different indicators
        color_map = {
            'rsi_14': '#9467bd',
            'macd': '#d62728',
            'macd_signal': '#ff7f0e',
            'sma_20': '#2ca02c',
            'sma_50': '#1f77b4',
            'ema_12': '#ff7f0e',
            'ema_26': '#2ca02c'
        }
        
        color = color_map.get(indicator_name.lower(), '#1f77b4')
        
        trace = create_line_trace(dates, values, indicator_name, color)
        fig.add_trace(trace)
        
    except Exception as e:
        logger.error(f"Error adding indicator trace {indicator_name}: {e}")


def create_pie_chart(data: pd.DataFrame, values_col: str, names_col: str, 
                    title: str = "") -> go.Figure:
    """
    Create a pie chart.
    
    Args:
        data: DataFrame with data
        values_col: Column name for values
        names_col: Column name for labels
        title: Chart title
        
    Returns:
        Plotly pie chart figure
    """
    try:
        fig = px.pie(
            data,
            values=values_col,
            names=names_col,
            title=title
        )
        
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            textfont_size=12
        )
        
        fig.update_layout(get_default_layout_config(title))
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating pie chart: {e}")
        return go.Figure()


def create_bar_chart(data: pd.DataFrame, x_col: str, y_col: str, 
                    title: str = "", color_column: Optional[str] = None) -> go.Figure:
    """
    Create a bar chart.
    
    Args:
        data: DataFrame with data
        x_col: Column name for x-axis
        y_col: Column name for y-axis
        title: Chart title
        color_column: Optional column for color coding
        
    Returns:
        Plotly bar chart figure
    """
    try:
        if color_column and color_column in data.columns:
            # Color-coded bars based on values
            colors = ['#26C281' if val >= 0 else '#E74C3C' for val in data[color_column]]
        else:
            colors = '#3498DB'
        
        fig = go.Figure(data=[
            go.Bar(
                x=data[x_col],
                y=data[y_col],
                marker_color=colors,
                name=y_col
            )
        ])
        
        layout_config = get_default_layout_config(title)
        layout_config['showlegend'] = False
        fig.update_layout(**layout_config)
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating bar chart: {e}")
        return go.Figure()


def create_comparison_chart(analysis_data: List[Dict[str, Any]], 
                          title: str = "Portfolio Comparison") -> go.Figure:
    """
    Create a comparison chart for multiple portfolio analyses.
    
    Args:
        analysis_data: List of analysis data dictionaries
        title: Chart title
        
    Returns:
        Plotly line chart for comparison
    """
    try:
        fig = go.Figure()
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        
        for i, analysis in enumerate(analysis_data):
            color = colors[i % len(colors)]
            
            fig.add_trace(go.Scatter(
                x=analysis.get('dates', []),
                y=analysis.get('total_values', []),
                mode='lines+markers',
                name=analysis.get('name', f'Analysis {i+1}'),
                line=dict(color=color, width=2),
                marker=dict(size=4)
            ))
        
        layout_config = get_default_layout_config(title, 400)
        layout_config.update({
            'xaxis': {
                **layout_config['xaxis'],
                'title': 'Date'
            },
            'yaxis': {
                **layout_config['yaxis'],
                'title': 'Total Value (HKD)',
                'tickformat': '$,.0f'
            }
        })
        
        fig.update_layout(**layout_config)
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating comparison chart: {e}")
        return go.Figure()


def apply_responsive_layout(fig: go.Figure) -> None:
    """
    Apply responsive layout settings to a figure.
    
    Args:
        fig: Plotly figure to make responsive
    """
    try:
        fig.update_layout(
            autosize=True,
            margin=dict(l=20, r=20, t=40, b=20),
            font=dict(size=10)
        )
        
        # Make legend responsive
        fig.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(size=9)
            )
        )
        
    except Exception as e:
        logger.error(f"Error applying responsive layout: {e}")


def format_chart_for_streamlit(fig: go.Figure) -> Dict[str, Any]:
    """
    Format chart configuration for Streamlit display.
    
    Args:
        fig: Plotly figure
        
    Returns:
        Configuration dictionary for Streamlit
    """
    return {
        'displayModeBar': True,
        'displaylogo': False,
        'modeBarButtonsToRemove': [
            'pan2d', 'lasso2d', 'select2d', 'autoScale2d',
            'hoverClosestCartesian', 'hoverCompareCartesian'
        ],
        'toImageButtonOptions': {
            'format': 'png',
            'filename': 'chart',
            'height': 500,
            'width': 800,
            'scale': 2
        }
    }


def validate_chart_data(data: Any, required_columns: List[str] = None) -> bool:
    """
    Validate data for chart creation.
    
    Args:
        data: Data to validate
        required_columns: Required column names for DataFrame
        
    Returns:
        True if data is valid, False otherwise
    """
    try:
        if data is None:
            return False
        
        if isinstance(data, pd.DataFrame):
            if data.empty:
                return False
                
            if required_columns:
                missing_cols = set(required_columns) - set(data.columns)
                if missing_cols:
                    logger.error(f"Missing required columns: {missing_cols}")
                    return False
        
        elif isinstance(data, (list, tuple)):
            if len(data) == 0:
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating chart data: {e}")
        return False


def get_chart_theme_config(theme: str = "plotly") -> Dict[str, Any]:
    """
    Get theme-specific chart configuration.
    
    Args:
        theme: Theme name ('plotly', 'plotly_white', 'plotly_dark')
        
    Returns:
        Theme configuration dictionary
    """
    themes = {
        "plotly": {
            'plot_bgcolor': 'rgba(0,0,0,0)',
            'paper_bgcolor': 'rgba(0,0,0,0)'
        },
        "plotly_white": {
            'plot_bgcolor': 'white',
            'paper_bgcolor': 'white'
        },
        "plotly_dark": {
            'plot_bgcolor': '#2F2F2F',
            'paper_bgcolor': '#2F2F2F',
            'font': {'color': 'white'}
        }
    }
    
    return themes.get(theme, themes["plotly"])