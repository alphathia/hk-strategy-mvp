"""
Utility Modules Package.

Collection of utility functions for data processing, indicators, charts, and validation.
Extracted from dashboard.py for modular architecture.
"""

# Data utilities
from .data_utils import (
    fetch_hk_price,
    fetch_hk_historical_prices,
    get_company_name,
    fetch_and_store_yahoo_data,
    get_portfolio_data,
    get_all_portfolios_for_equity_analysis,
    get_portfolio_analyses_for_equity,
    get_equities_from_portfolio,
    get_analysis_period_for_equity,
    fetch_equity_prices_by_date,
    get_yahoo_finance_price_fallback,
    validate_date_range,
    format_currency,
    calculate_percentage_change
)

# Indicator utilities
from .indicator_utils import (
    calculate_rsi,
    calculate_rsi_realtime,
    calculate_macd,
    calculate_macd_realtime,
    calculate_ema,
    calculate_ema_realtime,
    calculate_sma,
    calculate_bollinger_bands,
    calculate_stochastic,
    fetch_technical_analysis_data,
    get_fallback_technical_data,
    get_available_indicators,
    validate_indicator_selection,
    calculate_indicator_signals
)

# Chart utilities
from .chart_utils import (
    get_default_layout_config,
    get_candlestick_layout_config,
    create_candlestick_trace,
    create_line_trace,
    create_volume_trace,
    create_bollinger_bands_traces,
    add_technical_indicator_trace,
    create_pie_chart,
    create_bar_chart,
    create_comparison_chart,
    apply_responsive_layout,
    format_chart_for_streamlit,
    validate_chart_data,
    get_chart_theme_config
)

# Validation utilities
from .validation_utils import (
    validate_required,
    validate_number,
    validate_integer,
    validate_symbol,
    validate_email,
    validate_date,
    validate_date_range,
    validate_portfolio_id,
    validate_portfolio_name,
    validate_quantity,
    validate_price,
    validate_percentage,
    validate_form_data,
    sanitize_input,
    is_valid_hk_symbol,
    validate_technical_indicator_selection
)

__all__ = [
    # Data utilities
    'fetch_hk_price',
    'fetch_hk_historical_prices', 
    'get_company_name',
    'fetch_and_store_yahoo_data',
    'get_portfolio_data',
    'get_all_portfolios_for_equity_analysis',
    'get_portfolio_analyses_for_equity',
    'get_equities_from_portfolio',
    'get_analysis_period_for_equity',
    'fetch_equity_prices_by_date',
    'get_yahoo_finance_price_fallback',
    'validate_date_range',
    'format_currency',
    'calculate_percentage_change',
    
    # Indicator utilities
    'calculate_rsi',
    'calculate_rsi_realtime',
    'calculate_macd',
    'calculate_macd_realtime',
    'calculate_ema',
    'calculate_ema_realtime',
    'calculate_sma',
    'calculate_bollinger_bands',
    'calculate_stochastic',
    'fetch_technical_analysis_data',
    'get_fallback_technical_data',
    'get_available_indicators',
    'validate_indicator_selection',
    'calculate_indicator_signals',
    
    # Chart utilities
    'get_default_layout_config',
    'get_candlestick_layout_config',
    'create_candlestick_trace',
    'create_line_trace',
    'create_volume_trace',
    'create_bollinger_bands_traces',
    'add_technical_indicator_trace',
    'create_pie_chart',
    'create_bar_chart',
    'create_comparison_chart',
    'apply_responsive_layout',
    'format_chart_for_streamlit',
    'validate_chart_data',
    'get_chart_theme_config',
    
    # Validation utilities
    'validate_required',
    'validate_number',
    'validate_integer',
    'validate_symbol',
    'validate_email',
    'validate_date',
    'validate_date_range',
    'validate_portfolio_id',
    'validate_portfolio_name',
    'validate_quantity',
    'validate_price',
    'validate_percentage',
    'validate_form_data',
    'sanitize_input',
    'is_valid_hk_symbol',
    'validate_technical_indicator_selection'
]