"""
Components Package for HK Strategy Dashboard.

Complete modular UI components library with dialogs, charts, forms, and widgets.
Phase 5 - UI Components Implementation Complete ✅

This package contains reusable UI components extracted from the monolithic dashboard.py,
providing a modern component-based architecture for the HK Strategy Dashboard.
"""

# Import all component packages
from . import dialogs
from . import charts  
from . import forms
from . import widgets
from . import utils as component_utils

# Import base classes
from .dialogs.base_dialog import BaseDialog
from .charts.base_chart import BaseChart
from .forms.base_form import BaseForm
from .widgets.base_widget import BaseWidget

# Import specific components for convenience
from .dialogs import (
    IndicatorsDialog,
    CreatePortfolioDialog, 
    CopyPortfolioDialog,
    AddSymbolDialog,
    UpdatePositionDialog,
    TotalPositionsDialog,
    ActivePositionsDialog
)

from .charts import (
    PriceChart,
    SimplePriceChart,
    PortfolioComparisonChart,
    PortfolioAllocationChart,
    PortfolioPnLChart,
    PortfolioPerformanceChart,
    PortfolioSummaryCharts,
    RSIChart,
    MACDChart,
    BollingerBandsChart,
    MultiIndicatorChart
)

from .forms import (
    SymbolForm,
    SymbolSearchForm,
    PositionForm,
    BulkPositionForm,
    PortfolioForm,
    PortfolioCopyForm,
    PortfolioSelectionForm,
    DateRangeForm,
    SingleDateForm,
    AnalysisPeriodForm,
    TimeframeSelector
)

from .widgets import (
    MetricWidget,
    PortfolioMetricsWidget,
    ComparisonMetricsWidget,
    TechnicalIndicatorWidget,
    PortfolioSelectorWidget,
    SymbolSelectorWidget,
    AnalysisSelectorWidget,
    NavigationWidget,
    StatusWidget,
    SystemHealthWidget,
    ProgressWidget,
    LoadingWidget,
    ConnectivityWidget,
    NotificationWidget
)

# Import component registries
from .dialogs import DIALOG_REGISTRY
from .charts import CHART_REGISTRY
from .forms import FORM_REGISTRY
from .widgets import WIDGET_REGISTRY

# Factory functions
from .dialogs import get_dialog, create_dialog
from .charts import get_chart, create_chart
from .forms import get_form, create_form
from .widgets import get_widget, create_widget

# Export everything
__all__ = [
    # Sub-packages
    'dialogs', 'charts', 'forms', 'widgets', 'component_utils',
    
    # Base classes
    'BaseDialog', 'BaseChart', 'BaseForm', 'BaseWidget',
    
    # Dialog components
    'IndicatorsDialog', 'CreatePortfolioDialog', 'CopyPortfolioDialog',
    'AddSymbolDialog', 'UpdatePositionDialog', 'TotalPositionsDialog', 'ActivePositionsDialog',
    
    # Chart components  
    'PriceChart', 'SimplePriceChart',
    'PortfolioComparisonChart', 'PortfolioAllocationChart', 'PortfolioPnLChart', 
    'PortfolioPerformanceChart', 'PortfolioSummaryCharts',
    'RSIChart', 'MACDChart', 'BollingerBandsChart', 'MultiIndicatorChart',
    
    # Form components
    'SymbolForm', 'SymbolSearchForm', 'PositionForm', 'BulkPositionForm',
    'PortfolioForm', 'PortfolioCopyForm', 'PortfolioSelectionForm',
    'DateRangeForm', 'SingleDateForm', 'AnalysisPeriodForm', 'TimeframeSelector',
    
    # Widget components
    'MetricWidget', 'PortfolioMetricsWidget', 'ComparisonMetricsWidget', 'TechnicalIndicatorWidget',
    'PortfolioSelectorWidget', 'SymbolSelectorWidget', 'AnalysisSelectorWidget', 'NavigationWidget',
    'StatusWidget', 'SystemHealthWidget', 'ProgressWidget', 'LoadingWidget',
    'ConnectivityWidget', 'NotificationWidget',
    
    # Registries and factory functions
    'DIALOG_REGISTRY', 'CHART_REGISTRY', 'FORM_REGISTRY', 'WIDGET_REGISTRY',
    'get_dialog', 'create_dialog', 'get_chart', 'create_chart',
    'get_form', 'create_form', 'get_widget', 'create_widget'
]

# Component statistics for documentation
COMPONENT_STATS = {
    'dialogs': len(DIALOG_REGISTRY),
    'charts': len(CHART_REGISTRY),
    'forms': len(FORM_REGISTRY),
    'widgets': len(WIDGET_REGISTRY),
    'total_components': len(DIALOG_REGISTRY) + len(CHART_REGISTRY) + len(FORM_REGISTRY) + len(WIDGET_REGISTRY)
}