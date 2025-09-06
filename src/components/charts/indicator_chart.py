"""
Technical Indicator Chart Components.

Specialized charts for technical indicator visualization.
Extracted from dashboard.py for modular architecture.
"""

import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Optional, Any
import logging

from .base_chart import BaseChart
from src.utils.chart_utils import (
    get_default_layout_config,
    create_line_trace,
    add_technical_indicator_trace
)
from src.utils.indicator_utils import (
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    get_available_indicators
)

logger = logging.getLogger(__name__)


class RSIChart(BaseChart):
    """
    RSI (Relative Strength Index) indicator chart.
    """
    
    def __init__(self, symbol: str, period: int = 14, height: int = 200):
        """
        Initialize RSI chart.
        
        Args:
            symbol: Stock symbol
            period: RSI calculation period
            height: Chart height in pixels
        """
        super().__init__(title=f"{symbol} RSI({period})", height=height)
        self.symbol = symbol
        self.period = period
    
    def prepare_data(self, price_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Prepare RSI data.
        
        Args:
            price_data: DataFrame with Close prices
            
        Returns:
            Prepared data dictionary
        """
        try:
            if 'Close' not in price_data.columns:
                return {}
            
            rsi_values = calculate_rsi(price_data['Close'], window=self.period)
            
            return {
                'dates': price_data.index.tolist(),
                'rsi_values': rsi_values.tolist(),
                'current_rsi': rsi_values.iloc[-1] if not rsi_values.empty else 50
            }
            
        except Exception as e:
            logger.error(f"Error preparing RSI data: {e}")
            return {}
    
    def build_chart(self, prepared_data: Dict[str, Any]) -> go.Figure:
        """
        Build RSI chart.
        
        Args:
            prepared_data: Prepared data dictionary
            
        Returns:
            Plotly figure
        """
        try:
            if not prepared_data:
                return go.Figure()
            
            fig = go.Figure()
            
            # RSI line
            rsi_trace = create_line_trace(
                prepared_data['dates'],
                prepared_data['rsi_values'],
                f"RSI({self.period})",
                color="#9467bd"
            )
            fig.add_trace(rsi_trace)
            
            # Overbought/Oversold lines
            dates = prepared_data['dates']
            fig.add_hline(y=70, line_dash="dash", line_color="red", 
                         annotation_text="Overbought (70)")
            fig.add_hline(y=30, line_dash="dash", line_color="green", 
                         annotation_text="Oversold (30)")
            fig.add_hline(y=50, line_dash="dot", line_color="gray", 
                         annotation_text="Neutral (50)")
            
            # Layout
            layout_config = get_default_layout_config(self.title, self.height)
            layout_config.update({
                'yaxis': {
                    **layout_config['yaxis'],
                    'title': 'RSI',
                    'range': [0, 100]
                }
            })
            
            fig.update_layout(**layout_config)
            
            return fig
            
        except Exception as e:
            logger.error(f"Error building RSI chart: {e}")
            return go.Figure()


class MACDChart(BaseChart):
    """
    MACD (Moving Average Convergence Divergence) indicator chart.
    """
    
    def __init__(self, symbol: str, fast: int = 12, slow: int = 26, signal: int = 9, height: int = 200):
        """
        Initialize MACD chart.
        
        Args:
            symbol: Stock symbol
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line EMA period
            height: Chart height in pixels
        """
        super().__init__(title=f"{symbol} MACD({fast},{slow},{signal})", height=height)
        self.symbol = symbol
        self.fast = fast
        self.slow = slow
        self.signal = signal
    
    def prepare_data(self, price_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Prepare MACD data.
        
        Args:
            price_data: DataFrame with Close prices
            
        Returns:
            Prepared data dictionary
        """
        try:
            if 'Close' not in price_data.columns:
                return {}
            
            macd_data = calculate_macd(price_data['Close'], self.fast, self.slow, self.signal)
            
            return {
                'dates': price_data.index.tolist(),
                'macd_values': macd_data['macd'].tolist(),
                'signal_values': macd_data['signal'].tolist(),
                'histogram_values': macd_data['histogram'].tolist(),
                'current_macd': macd_data['macd'].iloc[-1] if not macd_data['macd'].empty else 0
            }
            
        except Exception as e:
            logger.error(f"Error preparing MACD data: {e}")
            return {}
    
    def build_chart(self, prepared_data: Dict[str, Any]) -> go.Figure:
        """
        Build MACD chart.
        
        Args:
            prepared_data: Prepared data dictionary
            
        Returns:
            Plotly figure
        """
        try:
            if not prepared_data:
                return go.Figure()
            
            fig = go.Figure()
            
            dates = prepared_data['dates']
            
            # MACD line
            macd_trace = create_line_trace(
                dates,
                prepared_data['macd_values'],
                "MACD",
                color="#d62728"
            )
            fig.add_trace(macd_trace)
            
            # Signal line
            signal_trace = create_line_trace(
                dates,
                prepared_data['signal_values'],
                "Signal",
                color="#ff7f0e"
            )
            fig.add_trace(signal_trace)
            
            # Histogram
            fig.add_trace(go.Bar(
                x=dates,
                y=prepared_data['histogram_values'],
                name="Histogram",
                marker_color=['green' if val >= 0 else 'red' for val in prepared_data['histogram_values']],
                opacity=0.6
            ))
            
            # Zero line
            fig.add_hline(y=0, line_dash="dash", line_color="gray")
            
            # Layout
            layout_config = get_default_layout_config(self.title, self.height)
            layout_config.update({
                'yaxis': {
                    **layout_config['yaxis'],
                    'title': 'MACD'
                }
            })
            
            fig.update_layout(**layout_config)
            
            return fig
            
        except Exception as e:
            logger.error(f"Error building MACD chart: {e}")
            return go.Figure()


class BollingerBandsChart(BaseChart):
    """
    Bollinger Bands overlay chart.
    """
    
    def __init__(self, symbol: str, period: int = 20, std_dev: float = 2, height: int = 400):
        """
        Initialize Bollinger Bands chart.
        
        Args:
            symbol: Stock symbol
            period: Moving average period
            std_dev: Standard deviation multiplier
            height: Chart height in pixels
        """
        super().__init__(title=f"{symbol} with Bollinger Bands({period},{std_dev})", height=height)
        self.symbol = symbol
        self.period = period
        self.std_dev = std_dev
    
    def prepare_data(self, price_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Prepare Bollinger Bands data.
        
        Args:
            price_data: DataFrame with OHLCV data
            
        Returns:
            Prepared data dictionary
        """
        try:
            if 'Close' not in price_data.columns:
                return {}
            
            bb_data = calculate_bollinger_bands(price_data['Close'], self.period, self.std_dev)
            
            return {
                'dates': price_data.index.tolist(),
                'close_prices': price_data['Close'].tolist(),
                'upper_band': bb_data['upper'].tolist(),
                'middle_band': bb_data['middle'].tolist(),
                'lower_band': bb_data['lower'].tolist()
            }
            
        except Exception as e:
            logger.error(f"Error preparing Bollinger Bands data: {e}")
            return {}
    
    def build_chart(self, prepared_data: Dict[str, Any]) -> go.Figure:
        """
        Build Bollinger Bands chart.
        
        Args:
            prepared_data: Prepared data dictionary
            
        Returns:
            Plotly figure
        """
        try:
            if not prepared_data:
                return go.Figure()
            
            fig = go.Figure()
            
            dates = prepared_data['dates']
            
            # Price line
            price_trace = create_line_trace(
                dates,
                prepared_data['close_prices'],
                f"{self.symbol} Close",
                color="#1f77b4"
            )
            fig.add_trace(price_trace)
            
            # Upper band
            fig.add_trace(go.Scatter(
                x=dates,
                y=prepared_data['upper_band'],
                mode='lines',
                name='BB Upper',
                line=dict(color='rgba(128,128,128,0.5)', width=1),
                showlegend=False
            ))
            
            # Lower band (with fill)
            fig.add_trace(go.Scatter(
                x=dates,
                y=prepared_data['lower_band'],
                mode='lines',
                name='Bollinger Bands',
                line=dict(color='rgba(128,128,128,0.5)', width=1),
                fill='tonexty',
                fillcolor='rgba(128,128,128,0.1)'
            ))
            
            # Middle band
            middle_trace = create_line_trace(
                dates,
                prepared_data['middle_band'],
                'BB Middle',
                color='orange'
            )
            fig.add_trace(middle_trace)
            
            # Layout
            layout_config = get_default_layout_config(self.title, self.height)
            layout_config.update({
                'yaxis': {
                    **layout_config['yaxis'],
                    'title': 'Price'
                }
            })
            
            fig.update_layout(**layout_config)
            
            return fig
            
        except Exception as e:
            logger.error(f"Error building Bollinger Bands chart: {e}")
            return go.Figure()


class MultiIndicatorChart(BaseChart):
    """
    Chart displaying multiple technical indicators in subplots.
    """
    
    def __init__(self, symbol: str, indicators: List[str], height: int = 600):
        """
        Initialize multi-indicator chart.
        
        Args:
            symbol: Stock symbol
            indicators: List of indicator codes
            height: Chart height in pixels
        """
        super().__init__(title=f"{symbol} Technical Indicators", height=height)
        self.symbol = symbol
        self.indicators = indicators
    
    def prepare_data(self, price_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Prepare multi-indicator data.
        
        Args:
            price_data: DataFrame with OHLCV data
            
        Returns:
            Prepared data dictionary
        """
        try:
            if 'Close' not in price_data.columns:
                return {}
            
            prepared_data = {
                'dates': price_data.index.tolist(),
                'close_prices': price_data['Close'].tolist(),
                'indicators': {}
            }
            
            # Calculate requested indicators
            for indicator in self.indicators:
                if indicator == 'rsi_14':
                    rsi = calculate_rsi(price_data['Close'], 14)
                    prepared_data['indicators']['rsi_14'] = rsi.tolist()
                elif indicator == 'macd':
                    macd = calculate_macd(price_data['Close'])
                    prepared_data['indicators']['macd'] = macd['macd'].tolist()
                    prepared_data['indicators']['macd_signal'] = macd['signal'].tolist()
                elif indicator.startswith('sma_'):
                    period = int(indicator.split('_')[1])
                    sma = price_data['Close'].rolling(window=period).mean()
                    prepared_data['indicators'][indicator] = sma.tolist()
                elif indicator.startswith('ema_'):
                    period = int(indicator.split('_')[1])
                    ema = price_data['Close'].ewm(span=period).mean()
                    prepared_data['indicators'][indicator] = ema.tolist()
            
            return prepared_data
            
        except Exception as e:
            logger.error(f"Error preparing multi-indicator data: {e}")
            return {}
    
    def build_chart(self, prepared_data: Dict[str, Any]) -> go.Figure:
        """
        Build multi-indicator chart.
        
        Args:
            prepared_data: Prepared data dictionary
            
        Returns:
            Plotly figure with subplots
        """
        try:
            if not prepared_data:
                return go.Figure()
            
            from plotly.subplots import make_subplots
            
            # Determine number of subplots
            indicator_count = len([i for i in self.indicators if i in ['rsi_14', 'macd']])
            subplot_count = 1 + indicator_count  # Price + indicators
            
            fig = make_subplots(
                rows=subplot_count,
                cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                subplot_titles=[f"{self.symbol} Price"] + [ind.upper() for ind in self.indicators if ind in ['rsi_14', 'macd']]
            )
            
            dates = prepared_data['dates']
            
            # Price chart (main)
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=prepared_data['close_prices'],
                    mode='lines',
                    name=f"{self.symbol} Close",
                    line=dict(color="#1f77b4")
                ),
                row=1, col=1
            )
            
            # Add overlays to price chart
            for indicator in self.indicators:
                if indicator.startswith(('sma_', 'ema_')):
                    if indicator in prepared_data['indicators']:
                        fig.add_trace(
                            go.Scatter(
                                x=dates,
                                y=prepared_data['indicators'][indicator],
                                mode='lines',
                                name=indicator.upper(),
                                line=dict(width=1.5)
                            ),
                            row=1, col=1
                        )
            
            # Add indicator subplots
            subplot_row = 2
            if 'rsi_14' in self.indicators and 'rsi_14' in prepared_data['indicators']:
                fig.add_trace(
                    go.Scatter(
                        x=dates,
                        y=prepared_data['indicators']['rsi_14'],
                        mode='lines',
                        name='RSI(14)',
                        line=dict(color="#9467bd")
                    ),
                    row=subplot_row, col=1
                )
                fig.add_hline(y=70, line_dash="dash", line_color="red", row=subplot_row, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="green", row=subplot_row, col=1)
                subplot_row += 1
            
            if 'macd' in self.indicators and 'macd' in prepared_data['indicators']:
                fig.add_trace(
                    go.Scatter(
                        x=dates,
                        y=prepared_data['indicators']['macd'],
                        mode='lines',
                        name='MACD',
                        line=dict(color="#d62728")
                    ),
                    row=subplot_row, col=1
                )
                if 'macd_signal' in prepared_data['indicators']:
                    fig.add_trace(
                        go.Scatter(
                            x=dates,
                            y=prepared_data['indicators']['macd_signal'],
                            mode='lines',
                            name='Signal',
                            line=dict(color="#ff7f0e")
                        ),
                        row=subplot_row, col=1
                    )
                fig.add_hline(y=0, line_dash="dash", line_color="gray", row=subplot_row, col=1)
            
            fig.update_layout(
                height=self.height,
                title=self.title,
                showlegend=True
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error building multi-indicator chart: {e}")
            return go.Figure()