"""
Dialog Components for HK Strategy Dashboard.

This module contains modal dialog components extracted from dashboard.py.
All dialogs inherit from BaseDialog and provide consistent UI patterns.
"""

from .base_dialog import BaseDialog

# Dialog registry - populated as dialogs are implemented
DIALOG_REGISTRY = {
    # Will be populated with actual dialog implementations
    # 'indicators': IndicatorsDialog,
    # 'create_portfolio': CreatePortfolioDialog,
    # 'copy_portfolio': CopyPortfolioDialog,
    # 'add_symbol': AddSymbolDialog,
    # 'update_position': UpdatePositionDialog,
    # 'total_positions': TotalPositionsDialog,
    # 'active_positions': ActivePositionsDialog,
}

__all__ = [
    'BaseDialog',
    'DIALOG_REGISTRY'
]


def get_dialog(dialog_key: str):
    """Get dialog class by key."""
    return DIALOG_REGISTRY.get(dialog_key)


def create_dialog(dialog_key: str, **kwargs):
    """Create dialog instance by key."""
    dialog_class = get_dialog(dialog_key)
    return dialog_class(**kwargs) if dialog_class else None