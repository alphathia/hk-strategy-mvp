# Strategic Signal System - Complete Implementation Guide

## Overview

The Strategic Signal System transforms your basic A/B/C/D signal system into a professional-grade TXYZn strategic signal framework with comprehensive technical analysis, full reproducibility, and evidence-based signal generation.

## 🎯 Key Features

### Signal Format: TXYZn
- **T**: Transaction type (B=Buy, S=Sell)
- **XYZ**: 3-character strategy code (BRK=Breakout, OSR=Oversold Reclaim, etc.)
- **n**: Strength level (1=weak, 9=extreme)

### 12 Strategic Signal Types
**Buy Strategies:**
- **BBRK**: Buy • Breakout - Break above resistance with momentum & volume
- **BOSR**: Buy • Oversold Reclaim - RSI/WMSR recovery with EMA20 reclaim
- **BMAC**: Buy • MA Crossover - EMA20 crosses above EMA50 with momentum
- **BBOL**: Buy • Bollinger Bounce - Recovery from lower Bollinger Band
- **BDIV**: Buy • Bullish Divergence - Price vs indicator divergence
- **BSUP**: Buy • Support Bounce - Bounce off key support levels

**Sell Strategies:**
- **SBDN**: Sell • Breakdown - Break below support with momentum & volume
- **SOBR**: Sell • Overbought Reversal - Reversal from overbought levels
- **SMAC**: Sell • MA Crossover - EMA20 crosses below EMA50 with momentum
- **SBND**: Sell • Bollinger Breakdown - Break below lower Bollinger Band
- **SDIV**: Sell • Bearish Divergence - Price vs indicator divergence
- **SRES**: Sell • Resistance Rejection - Failure at resistance levels

### 21 Technical Indicators
**RSI Family (4):** RSI-6, RSI-12, RSI-14, RSI-24
**MACD & PPO (6):** MACD, MACD Signal, MACD Histogram, PPO, PPO Signal, PPO Histogram
**Moving Averages (6):** EMA-5, EMA-10, EMA-20, EMA-50, SMA-20, SMA-50
**Bollinger & Volatility (4):** BB Upper, BB Middle, BB Lower, ATR-14
**Volume & Flow (3):** Volume Ratio-24, Money Flow Index-14, A/D Line
**Momentum & Trend (4):** Stochastic %K/%D, Williams %R, ADX-14
**Specialized (1):** Parabolic SAR

## 📁 File Structure

```
├── strategic_signal_migration.sql          # Database schema migration
├── populate_strategy_catalog.sql           # Strategy definitions
├── deploy_strategic_signals.py             # Complete deployment script
├── src/
│   ├── strategic_signal_engine.py          # Core signal generation engine
│   ├── strategic_database_manager.py       # Extended database operations
│   ├── indicator_dictionary.py             # Comprehensive indicator docs
│   └── trading_signals.py                  # Legacy (replaced)
```

## 🚀 Installation

### Option 1: Automated Deployment (Recommended)

```bash
# Make deployment script executable
chmod +x deploy_strategic_signals.py

# Run complete deployment
python deploy_strategic_signals.py

# Or with custom database URL
python deploy_strategic_signals.py --db-url "postgresql://user:pass@host:port/db"

# Skip backup (not recommended)
python deploy_strategic_signals.py --no-backup
```

### Option 2: Manual Installation

1. **Deploy Database Schema:**
```bash
psql $DATABASE_URL -f strategic_signal_migration.sql
psql $DATABASE_URL -f populate_strategy_catalog.sql
```

2. **Install Python Dependencies:**
```bash
pip install numpy pandas psycopg2-binary
```

3. **Verify Installation:**
```python
from src.strategic_signal_engine import StrategicSignalEngine
from src.strategic_database_manager import StrategicDatabaseManager
from src.indicator_dictionary import IndicatorDictionary

# Test basic functionality
engine = StrategicSignalEngine()
db_manager = StrategicDatabaseManager()
print("✅ Strategic Signal System ready!")
```

## 📊 Usage Examples

### Basic Signal Generation

```python
from src.strategic_signal_engine import StrategicSignalManager
from datetime import date

# Initialize signal manager
manager = StrategicSignalManager()

# Generate signals for portfolio
symbols = ["0700.HK", "0005.HK", "0939.HK"]
date_range = (date(2024, 1, 1), date.today())

signals = manager.generate_signals_for_portfolio(symbols, date_range)

# Display results
for symbol, symbol_signals in signals.items():
    print(f"\n{symbol}: {len(symbol_signals)} signals")
    for signal in symbol_signals:
        print(f"  {signal.strategy_key}: Strength {signal.strength} @ {signal.close_at_signal:.3f}")
        print(f"    Reasons: {signal.reasons_json}")
```

### Database Operations

```python
from src.strategic_database_manager import StrategicDatabaseManager

db = StrategicDatabaseManager()

# Create parameter set
params = {
    "rsi_overbought": 70,
    "rsi_oversold": 30,
    "volume_threshold": 1.5
}
param_id = db.create_parameter_set("Custom Parameters", params)

# Get recent signals
recent_signals = db.get_signal_events(
    symbol="0700.HK",
    min_strength=5,
    limit=10
)

# Get chart overlay data
overlay_data = db.get_chart_overlay_data(
    symbol="0700.HK",
    indicators=["ema20", "bb_upper", "bb_lower"]
)
```

### Indicator Documentation

```python
from src.indicator_dictionary import IndicatorDictionary

# Get indicator explanation for UI
rsi_explanation = IndicatorDictionary.get_indicator_explanation("rsi14", "detailed")
print(rsi_explanation)

# Get chart overlay indicators
overlays = IndicatorDictionary.get_chart_overlay_indicators()
print(f"Chart overlays: {overlays}")

# Get signal interpretation
signal_meaning = IndicatorDictionary.get_signal_interpretation("rsi14", 75.2)
print(f"RSI 75.2: {signal_meaning}")
```

## 🎨 Dashboard Integration

### Chart Overlays

```python
# Get indicators for chart display
from src.indicator_dictionary import IndicatorDictionary

# Available overlay indicators
overlays = IndicatorDictionary.get_chart_overlay_indicators()
# ['ema5', 'ema10', 'ema20', 'ema50', 'sma20', 'sma50', 
#  'bb_upper', 'bb_middle', 'bb_lower', 'parabolic_sar']

# Get data for chart
overlay_data = db.get_chart_overlay_data("0700.HK", ["ema20", "bb_upper", "bb_lower"])

# Get signal highlights for chart
signal_highlights = db.get_signal_highlights("0700.HK")
```

### Signal Highlighting

```python
# Get signals for chart highlighting
signals_for_chart = db.get_signal_events(
    symbol="0700.HK",
    min_strength=5,
    date_range=(date(2024, 1, 1), date.today())
)

# Display format for chart
for _, signal in signals_for_chart.iterrows():
    print(f"Date: {signal['bar_date']}")
    print(f"Signal: {signal['strategy_key']} (Strength: {signal['strength']})")
    print(f"Price: {signal['close_at_signal']}")
    print(f"Reasons: {signal['reasons_json']}")
```

### Indicator Tooltips

```python
# Get contextual explanations for UI
indicators_config = {}
for indicator in IndicatorDictionary.INDICATORS:
    config = IndicatorDictionary.get_ui_display_config(indicator)
    indicators_config[indicator] = config

# Example for RSI-14
rsi_config = indicators_config['rsi14']
# {
#   'name': 'RSI-14',
#   'full_name': '14-day Relative Strength Index',
#   'description': 'Classic overbought (>70) / oversold (<30) momentum indicator',
#   'scale': [0, 100],
#   'overbought': 70,
#   'oversold': 30
# }
```

## 🔧 Configuration

### Parameter Sets

Create custom parameter configurations for different market conditions:

```python
# Conservative parameters
conservative_params = {
    "rsi_overbought": 75,
    "rsi_oversold": 25,
    "volume_threshold": 2.0,
    "breakout_epsilon": 0.01
}

# Aggressive parameters  
aggressive_params = {
    "rsi_overbought": 65,
    "rsi_oversold": 35,
    "volume_threshold": 1.2,
    "breakout_epsilon": 0.003
}

# Create parameter sets
conservative_id = db.create_parameter_set("Conservative", conservative_params)
aggressive_id = db.create_parameter_set("Aggressive", aggressive_params)
```

### Signal Runs

Track signal generation batches for reproducibility:

```python
from datetime import date

# Create signal run
run_id = db.create_signal_run(
    param_set_id=conservative_id,
    universe_name="HK_PORTFOLIO",
    start_date=date(2024, 1, 1),
    end_date=date.today(),
    notes="Daily signal generation run"
)

# Generate and save signals
for symbol in portfolio_symbols:
    signals = engine.generate_signals(symbol, price_data)
    for signal in signals:
        db.save_signal_event(signal, run_id=run_id, param_set_id=conservative_id)

# Complete the run
db.complete_signal_run(run_id)
```

## 📈 Performance Analytics

### Strategy Performance

```python
# Get strategy performance summary
performance = db.get_strategy_performance_summary()
print(performance)

# Get latest portfolio signals
portfolio_signals = db.get_latest_portfolio_signals(
    portfolio_symbols=["0700.HK", "0005.HK", "0939.HK"],
    days_back=30,
    min_strength=6
)
```

### Migration from Legacy System

```python
# Migrate old A/B/C/D signals to TXYZn format
migrated_count = db.migrate_legacy_signals(batch_size=1000)
print(f"Migrated {migrated_count} legacy signals")

# Clean up old provisional signals
cleanup_count = db.cleanup_provisional_signals(days_old=7)
print(f"Cleaned up {cleanup_count} old provisional signals")
```

## 🎯 Signal Interpretation Guide

### Signal Strength Levels
- **9**: Extreme conviction - Historic setup with all indicators aligned
- **7-8**: Strong conviction - Powerful signal with high probability
- **5-6**: Moderate conviction - Good signal requiring confirmation
- **3-4**: Light conviction - Weak signal, use with caution
- **1-2**: Minimal conviction - Informational only

### Strategy Categories
- **Breakout**: BBRK, SBDN, SBND - Price breaking key levels
- **Mean Reversion**: BOSR, BBOL, SOBR - Reversal from extremes  
- **Trend Following**: BMAC, SMAC - Moving average crossovers
- **Divergence**: BDIV, SDIV - Price vs indicator divergence
- **Level Trading**: BSUP, SRES - Support and resistance plays

## 🛠 Maintenance

### Regular Tasks

```python
# Clean up old provisional signals (run daily)
db.cleanup_provisional_signals(days_old=1)

# Update indicator snapshots (run daily after market close)
from src.strategic_signal_engine import TechnicalIndicatorCalculator

for symbol in portfolio_symbols:
    price_data = get_latest_price_data(symbol)
    indicators = TechnicalIndicatorCalculator.calculate_all_indicators(price_data)
    db.save_indicator_snapshot(indicators)

# Generate signals (run daily after indicators update)
manager = StrategicSignalManager(db)
signals = manager.generate_signals_for_portfolio(portfolio_symbols, date_range)
```

### Monitoring

```python
# Check system health
strategy_count = db.execute_query("SELECT COUNT(*) FROM strategy")[0][0]
signal_count = db.execute_query("SELECT COUNT(*) FROM signal_event WHERE bar_date >= CURRENT_DATE - INTERVAL '30 days'")[0][0]
indicator_count = db.execute_query("SELECT COUNT(*) FROM indicator_snapshot WHERE bar_date >= CURRENT_DATE - INTERVAL '7 days'")[0][0]

print(f"Strategies: {strategy_count}/108")
print(f"Recent signals: {signal_count}")
print(f"Recent indicators: {indicator_count}")
```

## 📚 API Reference

### StrategicSignalEngine
- `generate_signals(symbol, price_data, provisional=False)` - Generate all signals for a symbol
- `_evaluate_strategy(base_strategy, indicators, provisional)` - Evaluate specific strategy

### StrategicDatabaseManager  
- `create_parameter_set(name, params, owner_user_id=None)` - Create parameter configuration
- `save_signal_event(signal, run_id=None, param_set_id=None)` - Save signal to database
- `get_signal_events(symbol=None, strategy_key=None, ...)` - Query signal events
- `get_chart_overlay_data(symbol, indicators, date_range=None)` - Get chart data
- `migrate_legacy_signals(batch_size=1000)` - Migrate A/B/C/D signals

### IndicatorDictionary
- `get_indicator_explanation(indicator_key, context="basic")` - Get indicator explanation
- `get_chart_overlay_indicators()` - Get list of overlay indicators  
- `get_signal_interpretation(indicator_key, value)` - Interpret indicator value

## 🔍 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `src/` is in Python path
2. **Database Connection**: Check `DATABASE_URL` environment variable
3. **Missing Indicators**: Run `calculate_all_indicators()` to populate data
4. **Signal Generation**: Verify sufficient price history (50+ days)

### Logs

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Support

- Check deployment report: `STRATEGIC_SIGNAL_DEPLOYMENT_REPORT.md`
- Review database schema: `strategic_signal_migration.sql`  
- Examine signal logic: `src/strategic_signal_engine.py`

---

🎉 **The Strategic Signal System is now fully operational with professional-grade TXYZn signals, comprehensive technical analysis, and full reproducibility!**