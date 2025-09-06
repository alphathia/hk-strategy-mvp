"""
Form Components Package.

Form components for user input and validation.
All forms inherit from BaseForm and provide consistent validation patterns.
"""

from .base_form import BaseForm, ValidationMixin
from .symbol_form import SymbolForm, SymbolSearchForm
from .position_form import PositionForm, BulkPositionForm, PositionSummaryWidget
from .portfolio_form import PortfolioForm, PortfolioCopyForm, PortfolioSelectionForm
from .date_form import DateRangeForm, SingleDateForm, AnalysisPeriodForm, TimeframeSelector

# Form registry for factory pattern
FORM_REGISTRY = {
    'base': BaseForm,
    'symbol': SymbolForm,
    'symbol_search': SymbolSearchForm,
    'position': PositionForm,
    'bulk_position': BulkPositionForm,
    'portfolio': PortfolioForm,
    'portfolio_copy': PortfolioCopyForm,
    'portfolio_selection': PortfolioSelectionForm,
    'date_range': DateRangeForm,
    'single_date': SingleDateForm,
    'analysis_period': AnalysisPeriodForm
}

def get_form(form_type: str) -> type:
    """
    Get form class by type.
    
    Args:
        form_type: Type of form to get
        
    Returns:
        Form class or None if not found
    """
    return FORM_REGISTRY.get(form_type)

def create_form(form_type: str, *args, **kwargs):
    """
    Create form instance by type.
    
    Args:
        form_type: Type of form to create
        *args: Positional arguments for form
        **kwargs: Keyword arguments for form
        
    Returns:
        Form instance or None if type not found
    """
    form_class = get_form(form_type)
    return form_class(*args, **kwargs) if form_class else None

__all__ = [
    'BaseForm', 'ValidationMixin',
    'SymbolForm', 'SymbolSearchForm',
    'PositionForm', 'BulkPositionForm', 'PositionSummaryWidget',
    'PortfolioForm', 'PortfolioCopyForm', 'PortfolioSelectionForm',
    'DateRangeForm', 'SingleDateForm', 'AnalysisPeriodForm', 'TimeframeSelector',
    'FORM_REGISTRY', 'get_form', 'create_form'
]