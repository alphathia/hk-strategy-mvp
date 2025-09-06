"""
Portfolio Chart Components.

Charts for portfolio analysis, comparison, and visualization.
Extracted from dashboard.py for modular architecture.
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Any, Tuple
import logging

from .base_chart import BaseChart
from src.utils.chart_utils import (
    get_default_layout_config,
    create_line_trace,
    create_pie_chart,
    create_bar_chart,
    create_comparison_chart,
    format_chart_for_streamlit
)

logger = logging.getLogger(__name__)


class PortfolioComparisonChart(BaseChart):
    """
    Chart for comparing multiple portfolio analyses over time.
    """
    
    def __init__(self, height: int = 400):
        """
        Initialize portfolio comparison chart.
        
        Args:
            height: Chart height in pixels
        """
        super().__init__(title="Portfolio Total Value Over Time", height=height)
    
    def prepare_data(self, analyses_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Prepare portfolio comparison data.
        
        Args:
            analyses_data: List of analysis data dictionaries
            
        Returns:
            Prepared data dictionary
        """
        try:
            if not analyses_data:
                return {}
            
            prepared_analyses = []
            
            for analysis in analyses_data:
                if 'date' in analysis and 'total_value' in analysis:
                    prepared_analyses.append({
                        'dates': analysis['date'],
                        'total_values': analysis['total_value'],
                        'name': analysis.get('name', f"Analysis {analysis.get('analysis_id', '')}"),
                        'analysis_id': analysis.get('analysis_id')
                    })
            
            return {
                'analyses': prepared_analyses,
                'count': len(prepared_analyses)
            }
            
        except Exception as e:
            logger.error(f"Error preparing portfolio comparison data: {e}")
            return {}
    
    def build_chart(self, prepared_data: Dict[str, Any]) -> go.Figure:
        """
        Build portfolio comparison chart.
        
        Args:
            prepared_data: Prepared data dictionary
            
        Returns:
            Plotly figure
        """
        try:
            if not prepared_data or not prepared_data.get('analyses'):
                return go.Figure()
            
            return create_comparison_chart(
                prepared_data['analyses'], 
                self.title
            )
            
        except Exception as e:
            logger.error(f"Error building portfolio comparison chart: {e}")
            return go.Figure()


class PortfolioAllocationChart(BaseChart):
    """
    Pie chart for portfolio allocation visualization.
    """
    
    def __init__(self, portfolio_name: str = "", height: int = 400):
        """
        Initialize portfolio allocation chart.
        
        Args:
            portfolio_name: Name of the portfolio
            height: Chart height in pixels
        """
        title = f"{portfolio_name} Allocation" if portfolio_name else "Portfolio Allocation"
        super().__init__(title=title, height=height)
        self.portfolio_name = portfolio_name
    
    def prepare_data(self, positions_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Prepare portfolio allocation data.
        
        Args:
            positions_data: DataFrame with position data
            
        Returns:
            Prepared data dictionary
        """
        try:
            if positions_data.empty:
                return {}
            
            # Calculate market values
            if 'Market Value' not in positions_data.columns:
                if 'quantity' in positions_data.columns and 'current_price' in positions_data.columns:
                    positions_data['Market Value'] = positions_data['quantity'] * positions_data['current_price']
                else:
                    logger.error("Cannot calculate market values - missing required columns")
                    return {}
            
            # Filter out zero/negative positions
            active_positions = positions_data[positions_data['Market Value'] > 0].copy()
            
            if active_positions.empty:
                return {}
            
            return {
                'symbols': active_positions['Symbol'].tolist() if 'Symbol' in active_positions.columns else active_positions.index.tolist(),
                'market_values': active_positions['Market Value'].tolist(),
                'total_value': active_positions['Market Value'].sum(),
                'count': len(active_positions)
            }
            
        except Exception as e:
            logger.error(f"Error preparing allocation data: {e}")
            return {}
    
    def build_chart(self, prepared_data: Dict[str, Any]) -> go.Figure:
        """
        Build portfolio allocation pie chart.
        
        Args:
            prepared_data: Prepared data dictionary
            
        Returns:
            Plotly figure
        """
        try:
            if not prepared_data:
                return go.Figure()
            
            # Create DataFrame for pie chart
            df = pd.DataFrame({
                'Symbol': prepared_data['symbols'],
                'Market Value': prepared_data['market_values']
            })
            
            return create_pie_chart(
                df,
                values_col='Market Value',
                names_col='Symbol',
                title=self.title
            )
            
        except Exception as e:
            logger.error(f"Error building allocation chart: {e}")
            return go.Figure()


class PortfolioPnLChart(BaseChart):
    """
    Bar chart for portfolio P&L visualization.
    """
    
    def __init__(self, portfolio_name: str = "", height: int = 400):
        """
        Initialize portfolio P&L chart.
        
        Args:
            portfolio_name: Name of the portfolio
            height: Chart height in pixels
        """
        title = f"{portfolio_name} P&L" if portfolio_name else "Portfolio P&L"
        super().__init__(title=title, height=height)
        self.portfolio_name = portfolio_name
    
    def prepare_data(self, positions_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Prepare P&L data.
        
        Args:
            positions_data: DataFrame with position data
            
        Returns:
            Prepared data dictionary
        """
        try:
            if positions_data.empty:
                return {}
            
            # Calculate P&L if not already present
            if 'P&L' not in positions_data.columns:
                if all(col in positions_data.columns for col in ['quantity', 'current_price', 'avg_cost']):
                    positions_data['P&L'] = positions_data['quantity'] * (positions_data['current_price'] - positions_data['avg_cost'])
                else:
                    logger.error("Cannot calculate P&L - missing required columns")
                    return {}
            
            # Filter out positions with no P&L data
            pnl_data = positions_data.dropna(subset=['P&L']).copy()
            
            if pnl_data.empty:
                return {}
            
            return {
                'symbols': pnl_data['Symbol'].tolist() if 'Symbol' in pnl_data.columns else pnl_data.index.tolist(),
                'pnl_values': pnl_data['P&L'].tolist(),
                'total_pnl': pnl_data['P&L'].sum(),
                'winners': len(pnl_data[pnl_data['P&L'] > 0]),
                'losers': len(pnl_data[pnl_data['P&L'] < 0])
            }
            
        except Exception as e:
            logger.error(f"Error preparing P&L data: {e}")
            return {}
    
    def build_chart(self, prepared_data: Dict[str, Any]) -> go.Figure:
        """
        Build P&L bar chart.
        
        Args:
            prepared_data: Prepared data dictionary
            
        Returns:
            Plotly figure
        """
        try:
            if not prepared_data:
                return go.Figure()
            
            # Create DataFrame for bar chart
            df = pd.DataFrame({
                'Symbol': prepared_data['symbols'],
                'P&L': prepared_data['pnl_values']
            })
            
            return create_bar_chart(
                df,
                x_col='Symbol',
                y_col='P&L',
                title=self.title,
                color_column='P&L'
            )
            
        except Exception as e:
            logger.error(f"Error building P&L chart: {e}")
            return go.Figure()


class PortfolioPerformanceChart(BaseChart):
    """
    Line chart for portfolio performance over time.
    """
    
    def __init__(self, portfolio_name: str = "", height: int = 400):
        """
        Initialize portfolio performance chart.
        
        Args:
            portfolio_name: Name of the portfolio
            height: Chart height in pixels
        """
        title = f"{portfolio_name} Performance" if portfolio_name else "Portfolio Performance"
        super().__init__(title=title, height=height)
        self.portfolio_name = portfolio_name
    
    def prepare_data(self, performance_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Prepare performance data.
        
        Args:
            performance_data: DataFrame with performance data over time
            
        Returns:
            Prepared data dictionary
        """
        try:
            if performance_data.empty:
                return {}
            
            # Ensure we have required columns
            required_cols = ['date', 'total_value']
            if not all(col in performance_data.columns for col in required_cols):
                logger.error(f"Missing required columns: {required_cols}")
                return {}
            
            # Sort by date
            performance_data = performance_data.sort_values('date')
            
            # Calculate percentage change from first value
            if len(performance_data) > 1:
                initial_value = performance_data['total_value'].iloc[0]
                performance_data['pct_change'] = ((performance_data['total_value'] - initial_value) / initial_value) * 100
            else:
                performance_data['pct_change'] = 0
            
            return {
                'dates': performance_data['date'].tolist(),
                'values': performance_data['total_value'].tolist(),
                'pct_changes': performance_data['pct_change'].tolist(),
                'start_value': performance_data['total_value'].iloc[0] if len(performance_data) > 0 else 0,
                'end_value': performance_data['total_value'].iloc[-1] if len(performance_data) > 0 else 0,
                'total_return': performance_data['pct_change'].iloc[-1] if len(performance_data) > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error preparing performance data: {e}")
            return {}
    
    def build_chart(self, prepared_data: Dict[str, Any]) -> go.Figure:
        """
        Build performance line chart.
        
        Args:
            prepared_data: Prepared data dictionary
            
        Returns:
            Plotly figure
        """
        try:
            if not prepared_data:
                return go.Figure()
            
            fig = go.Figure()
            
            # Add total value line
            value_trace = create_line_trace(
                prepared_data['dates'],
                prepared_data['values'],
                "Total Value",
                color="#2E86AB"
            )
            fig.add_trace(value_trace)
            
            # Layout configuration
            layout_config = get_default_layout_config(self.title, self.height)
            layout_config.update({
                'yaxis': {
                    **layout_config['yaxis'],
                    'title': 'Total Value (HKD)',
                    'tickformat': '$,.0f'
                },
                'xaxis': {
                    **layout_config['xaxis'],
                    'title': 'Date'
                }
            })
            
            fig.update_layout(**layout_config)
            
            return fig
            
        except Exception as e:
            logger.error(f"Error building performance chart: {e}")
            return go.Figure()


class PortfolioSummaryCharts:
    """
    Container for multiple portfolio summary charts.
    """
    
    def __init__(self, portfolio_name: str = ""):
        """
        Initialize portfolio summary charts.
        
        Args:
            portfolio_name: Name of the portfolio
        """
        self.portfolio_name = portfolio_name
        self.allocation_chart = PortfolioAllocationChart(portfolio_name)
        self.pnl_chart = PortfolioPnLChart(portfolio_name)
    
    def render_allocation_and_pnl(self, positions_data: pd.DataFrame) -> Tuple[Optional[go.Figure], Optional[go.Figure]]:
        """
        Render both allocation and P&L charts.
        
        Args:
            positions_data: DataFrame with position data
            
        Returns:
            Tuple of (allocation_chart, pnl_chart)
        """
        try:
            allocation_data = self.allocation_chart.prepare_data(positions_data)
            pnl_data = self.pnl_chart.prepare_data(positions_data)
            
            allocation_fig = self.allocation_chart.build_chart(allocation_data) if allocation_data else None
            pnl_fig = self.pnl_chart.build_chart(pnl_data) if pnl_data else None
            
            return allocation_fig, pnl_fig
            
        except Exception as e:
            logger.error(f"Error rendering summary charts: {e}")
            return None, None
    
    def get_streamlit_config(self) -> Dict[str, Any]:
        """
        Get Streamlit-specific chart configuration.
        
        Returns:
            Configuration for st.plotly_chart()
        """
        return format_chart_for_streamlit(go.Figure())