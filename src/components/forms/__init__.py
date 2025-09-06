"""
Form Components for HK Strategy Dashboard.

This module contains form components for user input and validation.
All forms inherit from BaseForm and provide consistent validation patterns.
"""

from .base_form import BaseForm

# Form registry - populated as forms are implemented
FORM_REGISTRY = {
    # Will be populated with actual form implementations
    # 'symbol': SymbolForm,
    # 'portfolio': PortfolioForm,
    # 'position': PositionForm,
    # 'date_range': DateRangeForm,
}

__all__ = [
    'BaseForm',
    'FORM_REGISTRY'
]


def get_form(form_key: str):
    """Get form class by key."""
    return FORM_REGISTRY.get(form_key)


def create_form(form_key: str, **kwargs):
    """Create form instance by key."""
    form_class = get_form(form_key)
    return form_class(**kwargs) if form_class else None