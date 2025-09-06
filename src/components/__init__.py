"""
Components Package for HK Strategy Dashboard.

This package contains reusable UI components for the modular dashboard architecture.
Components are organized into dialogs, charts, forms, widgets, and utilities.

Phase 5 - UI Components Implementation
Final phase extracting remaining ~1,500 lines from dashboard.py into reusable components.
"""

# Import base classes
from .dialogs.base_dialog import BaseDialog
from .charts.base_chart import BaseChart
from .forms.base_form import BaseForm
from .widgets.base_widget import BaseWidget

# Component registry - will be populated as components are created
DIALOG_REGISTRY = {}
CHART_REGISTRY = {}
FORM_REGISTRY = {}
WIDGET_REGISTRY = {}

# Export all base classes and registries
__all__ = [
    'BaseDialog',
    'BaseChart', 
    'BaseForm',
    'BaseWidget',
    'DIALOG_REGISTRY',
    'CHART_REGISTRY',
    'FORM_REGISTRY',
    'WIDGET_REGISTRY'
]


def get_dialog(dialog_key: str):
    """Get dialog class by key."""
    return DIALOG_REGISTRY.get(dialog_key)


def get_chart(chart_key: str):
    """Get chart class by key."""
    return CHART_REGISTRY.get(chart_key)


def get_form(form_key: str):
    """Get form class by key."""
    return FORM_REGISTRY.get(form_key)


def get_widget(widget_key: str):
    """Get widget class by key."""
    return WIDGET_REGISTRY.get(widget_key)