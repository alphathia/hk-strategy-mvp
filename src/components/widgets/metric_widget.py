"""
Metric Widget Components.

Widgets for displaying portfolio metrics, statistics, and KPIs.
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Union
import logging

from .base_widget import BaseWidget
from src.utils.data_utils import format_currency, calculate_percentage_change

logger = logging.getLogger(__name__)


class MetricWidget(BaseWidget):
    """
    Widget for displaying a single metric with value and change.
    """
    
    def __init__(self, widget_id: str, title: str = "", value: Union[float, int, str] = 0, 
                 delta: Union[float, int, str] = None, delta_color: str = "normal"):
        """
        Initialize metric widget.
        
        Args:
            widget_id: Unique widget identifier
            title: Metric title/label
            value: Current value
            delta: Change value (optional)
            delta_color: Delta color ('normal', 'inverse', 'off')
        """
        super().__init__(widget_id, title)
        self.value = value
        self.delta = delta
        self.delta_color = delta_color
    
    def render_content(self) -> Dict[str, Any]:
        """
        Render metric widget content.
        
        Returns:
            Widget render data
        """
        try:
            st.metric(
                label=self.title,
                value=self.value,
                delta=self.delta,
                delta_color=self.delta_color
            )
            
            return {
                'widget_type': 'metric',
                'title': self.title,
                'value': self.value,
                'delta': self.delta
            }
            
        except Exception as e:
            logger.error(f"Error rendering metric widget {self.widget_id}: {e}")
            st.error(f"Error displaying metric: {self.title}")
            return {}


class PortfolioMetricsWidget(BaseWidget):
    """
    Widget for displaying comprehensive portfolio metrics.
    """
    
    def __init__(self, widget_id: str, portfolio_data: Dict[str, Any], 
                 title: str = "Portfolio Metrics"):
        """
        Initialize portfolio metrics widget.
        
        Args:
            widget_id: Unique widget identifier
            portfolio_data: Portfolio data dictionary
            title: Widget title
        """
        super().__init__(widget_id, title)
        self.portfolio_data = portfolio_data
    
    def render_content(self) -> Dict[str, Any]:
        """
        Render portfolio metrics content.
        
        Returns:
            Widget render data
        """
        try:
            if not self.portfolio_data:
                st.info("No portfolio data available")
                return {}
            
            # Calculate metrics
            metrics = self._calculate_portfolio_metrics()
            
            # Display metrics in columns
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Value",
                    format_currency(metrics['total_value']),
                    delta=format_currency(metrics['total_change']) if metrics['total_change'] else None
                )
            
            with col2:
                st.metric(
                    "Total P&L",
                    format_currency(metrics['total_pnl']),
                    delta=f"{metrics['pnl_percent']:+.1f}%" if metrics['pnl_percent'] else None
                )
            
            with col3:
                st.metric(
                    "Positions",
                    str(metrics['total_positions']),
                    delta=f"{metrics['active_positions']} active"
                )
            
            with col4:
                st.metric(
                    "Day Change",
                    format_currency(metrics['day_change']),
                    delta=f"{metrics['day_change_percent']:+.1f}%" if metrics['day_change_percent'] else None
                )
            
            # Additional metrics in expandable section
            with st.expander("📊 Additional Metrics", expanded=False):
                self._render_additional_metrics(metrics)
            
            return {
                'widget_type': 'portfolio_metrics',
                'metrics': metrics
            }
            
        except Exception as e:
            logger.error(f"Error rendering portfolio metrics widget {self.widget_id}: {e}")
            st.error("Error displaying portfolio metrics")
            return {}
    
    def _calculate_portfolio_metrics(self) -> Dict[str, Any]:
        """
        Calculate portfolio metrics from data.
        
        Returns:
            Dictionary with calculated metrics
        """
        try:
            positions = self.portfolio_data.get('positions', [])
            
            total_value = 0
            total_cost_basis = 0
            total_positions = len(positions)
            active_positions = 0
            day_change = 0
            
            for position in positions:
                quantity = position.get('quantity', 0)
                current_price = position.get('current_price', 0)
                avg_cost = position.get('avg_cost', 0)
                price_change = position.get('price_change', 0)
                
                if quantity > 0:
                    active_positions += 1
                
                position_value = quantity * current_price
                position_cost = quantity * avg_cost
                position_day_change = quantity * price_change
                
                total_value += position_value
                total_cost_basis += position_cost
                day_change += position_day_change
            
            total_pnl = total_value - total_cost_basis
            pnl_percent = (total_pnl / total_cost_basis * 100) if total_cost_basis > 0 else 0
            day_change_percent = (day_change / (total_value - day_change) * 100) if (total_value - day_change) > 0 else 0
            
            return {
                'total_value': total_value,
                'total_cost_basis': total_cost_basis,
                'total_pnl': total_pnl,
                'pnl_percent': pnl_percent,
                'total_positions': total_positions,
                'active_positions': active_positions,
                'day_change': day_change,
                'day_change_percent': day_change_percent,
                'total_change': total_pnl  # For delta display
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio metrics: {e}")
            return {
                'total_value': 0, 'total_cost_basis': 0, 'total_pnl': 0, 'pnl_percent': 0,
                'total_positions': 0, 'active_positions': 0, 'day_change': 0, 'day_change_percent': 0,
                'total_change': 0
            }
    
    def _render_additional_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        Render additional portfolio metrics.
        
        Args:
            metrics: Calculated metrics dictionary
        """
        try:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Cost Basis", format_currency(metrics['total_cost_basis']))
                
                # Calculate win/loss ratio
                positions = self.portfolio_data.get('positions', [])
                winners = sum(1 for p in positions if (p.get('quantity', 0) * (p.get('current_price', 0) - p.get('avg_cost', 0))) > 0)
                losers = sum(1 for p in positions if (p.get('quantity', 0) * (p.get('current_price', 0) - p.get('avg_cost', 0))) < 0)
                
                st.metric("Winners", str(winners), delta=f"{losers} losers")
            
            with col2:
                # Sector diversification
                sectors = {}
                for position in positions:
                    sector = position.get('sector', 'Other')
                    value = position.get('quantity', 0) * position.get('current_price', 0)
                    sectors[sector] = sectors.get(sector, 0) + value
                
                top_sector = max(sectors, key=sectors.get) if sectors else "N/A"
                sector_count = len(sectors)
                
                st.metric("Top Sector", top_sector)
                st.metric("Sectors", str(sector_count))
            
            with col3:
                # Concentration metrics
                if positions:
                    position_values = [(p.get('quantity', 0) * p.get('current_price', 0)) for p in positions]
                    position_values.sort(reverse=True)
                    
                    # Top position concentration
                    top_position_percent = (position_values[0] / metrics['total_value'] * 100) if metrics['total_value'] > 0 and position_values else 0
                    
                    # Top 3 positions concentration
                    top_3_value = sum(position_values[:3]) if len(position_values) >= 3 else sum(position_values)
                    top_3_percent = (top_3_value / metrics['total_value'] * 100) if metrics['total_value'] > 0 else 0
                    
                    st.metric("Top Position", f"{top_position_percent:.1f}%")
                    st.metric("Top 3 Positions", f"{top_3_percent:.1f}%")
                
        except Exception as e:
            logger.error(f"Error rendering additional metrics: {e}")


class ComparisonMetricsWidget(BaseWidget):
    """
    Widget for comparing metrics between portfolios or time periods.
    """
    
    def __init__(self, widget_id: str, comparison_data: List[Dict[str, Any]], 
                 title: str = "Portfolio Comparison"):
        """
        Initialize comparison metrics widget.
        
        Args:
            widget_id: Unique widget identifier
            comparison_data: List of portfolio data for comparison
            title: Widget title
        """
        super().__init__(widget_id, title)
        self.comparison_data = comparison_data
    
    def render_content(self) -> Dict[str, Any]:
        """
        Render comparison metrics content.
        
        Returns:
            Widget render data
        """
        try:
            if len(self.comparison_data) < 2:
                st.info("Need at least 2 portfolios for comparison")
                return {}
            
            # Calculate metrics for each portfolio
            portfolio_metrics = []
            for portfolio in self.comparison_data:
                metrics = self._calculate_single_portfolio_metrics(portfolio)
                portfolio_metrics.append({
                    'name': portfolio.get('name', 'Unknown'),
                    'metrics': metrics
                })
            
            # Display comparison table
            self._render_comparison_table(portfolio_metrics)
            
            # Display relative performance
            self._render_relative_performance(portfolio_metrics)
            
            return {
                'widget_type': 'comparison_metrics',
                'portfolios': len(portfolio_metrics)
            }
            
        except Exception as e:
            logger.error(f"Error rendering comparison metrics widget {self.widget_id}: {e}")
            st.error("Error displaying comparison metrics")
            return {}
    
    def _calculate_single_portfolio_metrics(self, portfolio_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate metrics for a single portfolio."""
        positions = portfolio_data.get('positions', [])
        
        total_value = sum(p.get('quantity', 0) * p.get('current_price', 0) for p in positions)
        total_cost = sum(p.get('quantity', 0) * p.get('avg_cost', 0) for p in positions)
        total_pnl = total_value - total_cost
        pnl_percent = (total_pnl / total_cost * 100) if total_cost > 0 else 0
        
        return {
            'total_value': total_value,
            'total_cost': total_cost,
            'total_pnl': total_pnl,
            'pnl_percent': pnl_percent,
            'positions': len([p for p in positions if p.get('quantity', 0) > 0])
        }
    
    def _render_comparison_table(self, portfolio_metrics: List[Dict[str, Any]]) -> None:
        """Render portfolio comparison table."""
        import pandas as pd
        
        # Create comparison DataFrame
        data = []
        for pm in portfolio_metrics:
            data.append({
                'Portfolio': pm['name'],
                'Total Value': format_currency(pm['metrics']['total_value']),
                'P&L': format_currency(pm['metrics']['total_pnl']),
                'P&L %': f"{pm['metrics']['pnl_percent']:+.1f}%",
                'Positions': pm['metrics']['positions']
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
    
    def _render_relative_performance(self, portfolio_metrics: List[Dict[str, Any]]) -> None:
        """Render relative performance comparison."""
        st.markdown("**Relative Performance:**")
        
        # Find best and worst performing portfolios
        best_portfolio = max(portfolio_metrics, key=lambda x: x['metrics']['pnl_percent'])
        worst_portfolio = min(portfolio_metrics, key=lambda x: x['metrics']['pnl_percent'])
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.success(f"🏆 **Best Performer**: {best_portfolio['name']}")
            st.write(f"Return: {best_portfolio['metrics']['pnl_percent']:+.1f}%")
        
        with col2:
            st.error(f"📉 **Worst Performer**: {worst_portfolio['name']}")
            st.write(f"Return: {worst_portfolio['metrics']['pnl_percent']:+.1f}%")


class TechnicalIndicatorWidget(BaseWidget):
    """
    Widget for displaying technical indicator values and signals.
    """
    
    def __init__(self, widget_id: str, symbol: str, indicator_data: Dict[str, Any], 
                 title: str = None):
        """
        Initialize technical indicator widget.
        
        Args:
            widget_id: Unique widget identifier
            symbol: Stock symbol
            indicator_data: Technical indicator data
            title: Widget title
        """
        super().__init__(widget_id, title or f"{symbol} Technical Indicators")
        self.symbol = symbol
        self.indicator_data = indicator_data
    
    def render_content(self) -> Dict[str, Any]:
        """
        Render technical indicator content.
        
        Returns:
            Widget render data
        """
        try:
            if not self.indicator_data:
                st.info(f"No technical data available for {self.symbol}")
                return {}
            
            st.markdown(f"### 📈 {self.symbol}")
            
            # Display current values
            col1, col2, col3 = st.columns(3)
            
            # RSI
            if 'rsi_14' in self.indicator_data:
                rsi_value = self.indicator_data['rsi_14'][0] if self.indicator_data['rsi_14'][0] else 50
                rsi_signal = self._get_rsi_signal(rsi_value)
                
                with col1:
                    st.metric("RSI (14)", f"{rsi_value:.1f}", delta=rsi_signal['label'])
                    if rsi_signal['color']:
                        st.markdown(f"<span style='color: {rsi_signal['color']}'>{rsi_signal['description']}</span>", 
                                  unsafe_allow_html=True)
            
            # MACD
            if 'macd' in self.indicator_data and 'macd_signal' in self.indicator_data:
                macd_value = self.indicator_data['macd'][0] if self.indicator_data['macd'][0] else 0
                signal_value = self.indicator_data['macd_signal'][0] if self.indicator_data['macd_signal'][0] else 0
                macd_signal = self._get_macd_signal(macd_value, signal_value)
                
                with col2:
                    st.metric("MACD", f"{macd_value:.3f}", delta=macd_signal['label'])
                    if macd_signal['color']:
                        st.markdown(f"<span style='color: {macd_signal['color']}'>{macd_signal['description']}</span>", 
                                  unsafe_allow_html=True)
            
            # Moving Averages
            if 'sma_20' in self.indicator_data and 'sma_50' in self.indicator_data:
                sma_20 = self.indicator_data['sma_20'][0] if self.indicator_data['sma_20'][0] else 0
                sma_50 = self.indicator_data['sma_50'][0] if self.indicator_data['sma_50'][0] else 0
                ma_signal = self._get_ma_signal(sma_20, sma_50)
                
                with col3:
                    st.metric("MA Cross", f"20: {sma_20:.2f}", delta=ma_signal['label'])
                    if ma_signal['color']:
                        st.markdown(f"<span style='color: {ma_signal['color']}'>{ma_signal['description']}</span>", 
                                  unsafe_allow_html=True)
            
            return {
                'widget_type': 'technical_indicators',
                'symbol': self.symbol,
                'indicators_count': len(self.indicator_data)
            }
            
        except Exception as e:
            logger.error(f"Error rendering technical indicator widget {self.widget_id}: {e}")
            st.error(f"Error displaying technical indicators for {self.symbol}")
            return {}
    
    def _get_rsi_signal(self, rsi_value: float) -> Dict[str, str]:
        """Get RSI signal interpretation."""
        if rsi_value > 70:
            return {'label': 'Overbought', 'color': 'red', 'description': '⚠️ Potentially overbought'}
        elif rsi_value < 30:
            return {'label': 'Oversold', 'color': 'green', 'description': '📈 Potentially oversold'}
        else:
            return {'label': 'Neutral', 'color': 'gray', 'description': '➖ Neutral range'}
    
    def _get_macd_signal(self, macd_value: float, signal_value: float) -> Dict[str, str]:
        """Get MACD signal interpretation."""
        if macd_value > signal_value:
            return {'label': 'Bullish', 'color': 'green', 'description': '📈 MACD above signal'}
        elif macd_value < signal_value:
            return {'label': 'Bearish', 'color': 'red', 'description': '📉 MACD below signal'}
        else:
            return {'label': 'Neutral', 'color': 'gray', 'description': '➖ MACD at signal'}
    
    def _get_ma_signal(self, sma_20: float, sma_50: float) -> Dict[str, str]:
        """Get moving average signal interpretation."""
        if sma_20 > sma_50:
            return {'label': 'Golden Cross', 'color': 'green', 'description': '📈 Short MA above Long MA'}
        elif sma_20 < sma_50:
            return {'label': 'Death Cross', 'color': 'red', 'description': '📉 Short MA below Long MA'}
        else:
            return {'label': 'Neutral', 'color': 'gray', 'description': '➖ MAs converged'}