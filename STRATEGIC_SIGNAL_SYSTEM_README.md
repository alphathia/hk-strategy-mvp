# Strategic Signal System

A comprehensive signal management system that replaces basic A/B/C/D signals with professional TXYZn format signals, complete with 21 technical indicators, evidence-based reasoning, and dashboard management.

## 🎯 Overview

The Strategic Signal System provides:
- **TXYZn Signal Format**: Professional signal codes (T=transaction type, XYZ=strategy code, n=strength 1-9)
- **108 Strategy Combinations**: 12 base strategies × 9 strength levels
- **21 Technical Indicators**: RSI family, MACD/PPO, Moving Averages, Bollinger Bands, Volume/Flow, Momentum
- **Evidence-Based Signals**: JSON-structured reasoning with thresholds, reasons, and scoring
- **Dashboard Management**: Web-based interface for strategy and signal management
- **REST API**: Complete CRUD operations for strategies, signals, and indicators
- **Data Integrity**: Comprehensive validation, constraints, and monitoring

## 🏗️ Architecture

### Database Schema
```
strategy (108 records)          - All strategy definitions
parameter_set                   - Reproducible parameter configurations  
signal_run                     - Batch tracking and execution history
signal_event                   - Individual signal occurrences with evidence
indicator_snapshot             - Technical indicator values and metadata
```

### Core Components
```
src/
├── strategic_signal_engine.py     # Core signal generation engine
├── strategic_database_manager.py  # Database operations and management
├── indicator_dictionary.py        # 21 indicator definitions and metadata
├── strategy_dictionary.py         # 12 base strategy definitions
├── signal_dictionary.py           # Signal type management and formatting
├── signal_validation.py           # TXYZn format and data validation
└── strategy_manager_api.py        # REST API for dashboard operations

database/
├── strategic_signal_migration.sql     # Core database schema
├── populate_strategy_catalog.sql      # 108 strategy definitions
├── database_management_functions.sql  # Dynamic strategy creation
├── database_constraints_validation.sql # Data integrity and validation
└── management_views.sql               # Optimized dashboard queries

dashboard/
└── dashboard_management.html          # Complete management interface
```

## 🚀 Deployment

### Quick Start
```bash
# Make deployment script executable
chmod +x deploy_complete_strategic_system.py

# Run complete deployment
python deploy_complete_strategic_system.py
```

### Manual Deployment
```bash
# 1. Deploy database schema (in order)
psql -d your_database -f strategic_signal_migration.sql
psql -d your_database -f populate_strategy_catalog.sql  
psql -d your_database -f database_management_functions.sql
psql -d your_database -f database_constraints_validation.sql
psql -d your_database -f management_views.sql

# 2. Start the API server
python src/strategy_manager_api.py

# 3. Open dashboard in browser
open dashboard_management.html
```

## 📊 Signal Format: TXYZn

### Format Breakdown
- **T**: Transaction Type (`B` = Buy, `S` = Sell)
- **XYZ**: 3-character Strategy Code
- **n**: Strength Level (1-9, where 1=weak, 9=strong)

### Examples
- `BBRK5`: Buy Breakout, Medium Strength
- `SBDN8`: Sell Breakdown, Strong Signal  
- `BMAC3`: Buy MACD Cross, Weak Signal

## 🎯 Base Strategies (12 Total)

### Buy Strategies (6)
- **BBRK**: Buy Breakout - Price breaks above resistance with volume
- **BOSR**: Buy Oversold Reversal - RSI/momentum reversal from oversold
- **BMAC**: Buy MACD Cross - MACD bullish crossover with momentum
- **BBOL**: Buy Bollinger - Price bounces off lower Bollinger Band
- **BDIV**: Buy Divergence - Bullish divergence between price and indicators
- **BSUP**: Buy Support - Price finds support at key technical levels

### Sell Strategies (6)  
- **SBDN**: Sell Breakdown - Price breaks below support with volume
- **SOBR**: Sell Overbought Reversal - RSI/momentum reversal from overbought
- **SMAC**: Sell MACD Cross - MACD bearish crossover with momentum
- **SBND**: Sell Bollinger - Price bounces off upper Bollinger Band
- **SDIV**: Sell Divergence - Bearish divergence between price and indicators
- **SRES**: Sell Resistance - Price fails at key technical resistance

## 📈 Technical Indicators (21 Total)

### RSI Family (4)
- `rsi14`: Classic 14-period RSI
- `rsi21`: Extended 21-period RSI  
- `rsi50`: Long-term 50-period RSI
- `rsi_divergence`: RSI divergence detection

### MACD/PPO (4)
- `macd`: MACD line (12,26,9)
- `ppo`: Percentage Price Oscillator
- `macd_histogram`: MACD histogram
- `ppo_signal`: PPO signal line

### Moving Averages (6)
- `sma20`, `ema20`: 20-period averages
- `sma50`, `ema50`: 50-period averages  
- `sma200`, `ema200`: 200-period averages

### Bollinger Bands (3)
- `bb_upper`: Upper Bollinger Band
- `bb_lower`: Lower Bollinger Band
- `bb_percent`: %B position indicator

### Volume/Flow (3)
- `volume_sma`: Volume simple moving average
- `volume_ratio`: Current vs average volume
- `adl`: Accumulation/Distribution Line

### Momentum (1)
- `momentum`: Rate of change momentum

## 🎛️ Dashboard Features

### Strategy Management
- View all 108 strategies with usage statistics
- Filter by category, side, strength, performance
- Create custom strategies with validation
- Real-time performance metrics

### Signal Monitoring  
- Real-time signal feed with filtering
- Evidence inspection and reasoning
- Symbol-based signal history
- Confidence and strength analysis

### Indicator Configuration
- Manage all 21 technical indicators
- Configure parameters and thresholds
- Monitor data availability and freshness
- Chart overlay configuration

### System Monitoring
- Data quality dashboards
- Signal run execution monitoring  
- Performance metrics and trends
- Consistency checks and validation

## 🔧 API Endpoints

### Strategies
```
GET    /api/strategies              # List all strategies
GET    /api/strategies/{key}        # Get strategy details
POST   /api/strategies              # Create new strategy
PUT    /api/strategies/{key}        # Update strategy
DELETE /api/strategies/{key}        # Delete strategy
```

### Signals
```
GET    /api/signals                 # List recent signals
GET    /api/signals/{symbol}        # Get signals for symbol
POST   /api/signals                 # Create new signal
GET    /api/signals/validate/{code} # Validate signal format
```

### Indicators
```
GET    /api/indicators              # List all indicators
GET    /api/indicators/{name}       # Get indicator details
POST   /api/indicators/{name}/config # Configure indicator
```

### Validation
```
POST   /api/validate/signal         # Validate TXYZn format
POST   /api/validate/strategy       # Validate strategy definition
POST   /api/validate/batch          # Batch validation
```

## 📊 Management Views

### Executive Dashboard
- `v_executive_dashboard`: Key performance indicators
- `v_system_performance`: Daily performance trends  
- `v_data_quality_dashboard`: Data integrity metrics

### Strategy Analysis
- `v_strategy_overview`: Comprehensive strategy statistics
- `v_strategy_performance`: Performance metrics by strategy
- `v_base_strategy_summary`: Aggregated family statistics
- `v_strategy_explorer`: Strategy selection interface

### Signal Analysis
- `v_recent_signals`: Latest signals with enrichment
- `v_signal_frequency`: Pattern analysis by symbol/strategy
- `v_high_confidence_signals`: Top-performing signals

### Monitoring
- `v_signal_run_monitor`: Execution tracking
- `v_symbol_coverage`: Activity by symbol
- `v_indicator_status`: Indicator health monitoring

## 🔍 Validation & Quality

### TXYZn Format Validation
```sql
SELECT validate_signal_format('BBRK5');  -- Returns true
SELECT validate_signal_format('INVALID'); -- Returns false
```

### Strategy Validation
```sql
SELECT validate_strategy_exists('BBRK1'); -- Check if strategy exists
SELECT validate_indicator_config('{"period": 14, "source": "close"}'::jsonb);
```

### Data Consistency
```sql
SELECT * FROM check_data_consistency();  -- Comprehensive checks
SELECT cleanup_invalid_data(true);       -- Dry run cleanup
```

## 📝 Evidence Structure

Each signal includes structured evidence:
```json
{
  "thresholds": {
    "rsi": 70,
    "bb_position": 0.95,
    "volume_ratio": 1.5
  },
  "reasons": [
    "RSI above overbought threshold (70)",
    "Price near upper Bollinger Band (95%)",
    "Volume 50% above average"
  ],
  "score": 75.5,
  "metadata": {
    "calculated_at": "2024-01-15T10:30:00Z",
    "parameters_used": {...}
  }
}
```

## 🔄 Signal Generation Workflow

1. **Parameter Configuration**: Define indicator periods, thresholds
2. **Indicator Calculation**: Compute all 21 technical indicators  
3. **Strategy Evaluation**: Apply strategy logic with evidence collection
4. **Signal Generation**: Create TXYZn signals with confidence scoring
5. **Evidence Storage**: Store reasoning, thresholds, and metadata
6. **Validation**: Ensure format compliance and data integrity
7. **Dashboard Display**: Present signals with full context

## 📈 Usage Examples

### Generate Signals
```python
from src.strategic_signal_engine import StrategicSignalEngine

engine = StrategicSignalEngine()
signals = engine.generate_signals(
    symbol='AAPL',
    price_data=price_df,
    provisional=False
)

for signal in signals:
    print(f"{signal.signal}: {signal.confidence:.2%} confidence")
```

### Query Recent Signals
```sql
SELECT 
    symbol,
    signal,
    strategy_name,
    confidence,
    strength,
    timestamp
FROM v_recent_signals 
WHERE symbol = 'AAPL'
ORDER BY timestamp DESC
LIMIT 10;
```

### Dashboard Integration
```javascript
// Fetch strategies for dropdown
fetch('/api/strategies')
  .then(response => response.json())
  .then(strategies => populateStrategyList(strategies));

// Validate signal format
fetch('/api/validate/signal', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({signal: 'BBRK5'})
})
.then(response => response.json())
.then(result => console.log('Valid:', result.is_valid));
```

## 🛠️ Customization

### Adding New Base Strategies
1. Update `src/strategy_dictionary.py` with new strategy metadata
2. Add strategy logic to `src/strategic_signal_engine.py`
3. Run database function: `SELECT create_base_strategy('BNEW', 'B', 'Buy • New Strategy')`
4. Update dashboard filters and documentation

### Adding New Indicators
1. Add indicator definition to `src/indicator_dictionary.py`
2. Implement calculation in `TechnicalIndicatorCalculator`
3. Update database constraints in `database_constraints_validation.sql`
4. Add to dashboard indicator management

### Custom Signal Types
1. Extend `signal_dictionary.py` with new signal types
2. Update validation in `signal_validation.py`  
3. Modify API endpoints if needed
4. Update dashboard UI components

## 🔍 Troubleshooting

### Common Issues

**Signals not generating**
- Check indicator data availability: `SELECT * FROM v_indicator_status`
- Verify parameter sets: `SELECT * FROM parameter_set`
- Review validation errors: `SELECT * FROM check_data_consistency()`

**Database constraints failing**
- Run consistency check: `SELECT * FROM check_data_consistency()`
- Fix invalid data: `SELECT cleanup_invalid_data(false)` (removes invalid records)
- Check constraint definitions in `database_constraints_validation.sql`

**API connection issues**
- Verify Flask server is running on correct port
- Check CORS configuration in `strategy_manager_api.py`
- Ensure database connection string is correct

**Dashboard not loading data**
- Verify API endpoints are accessible
- Check browser console for JavaScript errors
- Confirm management views exist: `\dv` in psql

## 📚 File Reference

### Core Files
- `deploy_complete_strategic_system.py`: Complete deployment automation
- `strategic_signal_migration.sql`: Database schema creation
- `populate_strategy_catalog.sql`: 108 strategy definitions
- `src/strategic_signal_engine.py`: Core signal generation logic
- `dashboard_management.html`: Complete management interface

### Supporting Files  
- `database_management_functions.sql`: Dynamic strategy creation
- `database_constraints_validation.sql`: Data integrity and validation
- `management_views.sql`: Optimized dashboard queries
- `src/strategy_dictionary.py`: Base strategy metadata
- `src/signal_validation.py`: TXYZn format validation

## 🎉 Success Metrics

After deployment, you should see:
- ✅ 108 strategies in database (`SELECT COUNT(*) FROM strategy`)
- ✅ All validation functions working (`SELECT validate_signal_format('BBRK5')`)
- ✅ Management views accessible (`SELECT * FROM v_executive_dashboard`)  
- ✅ API endpoints responding (`curl http://localhost:5000/api/strategies`)
- ✅ Dashboard loading with no errors
- ✅ Sample signals generating successfully

## 🚀 Next Steps

1. **Integration**: Connect with existing stock data pipelines
2. **Backtesting**: Implement historical signal validation
3. **Alerting**: Add real-time signal notifications
4. **Portfolio Integration**: Connect with portfolio analysis
5. **Machine Learning**: Enhance signal confidence with ML models
6. **Mobile Dashboard**: Create responsive mobile interface
7. **Advanced Visualizations**: Add candlestick charts with signal overlays

---

*Strategic Signal System - Professional signal management for modern trading platforms*