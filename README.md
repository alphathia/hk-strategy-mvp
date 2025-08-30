# HK Equity Trading Strategy MVP

A comprehensive Docker-based Streamlit application for Hong Kong equity trading strategy with PostgreSQL database, Redis caching, and advanced technical analysis.

## Features

- **Portfolio Management**: Track HK equity positions with real-time P&L calculation
- **Advanced Trading Signals**: Generate TXYZN format signals using technical indicators (RSI, EMA, MACD, Bollinger Bands, ATR)
- **Performance Analytics**: Visualize portfolio performance, risk metrics, and alpha generation
- **Real-time Data**: Yahoo Finance integration with PostgreSQL persistence and Redis caching
- **HK Strategy Engine**: Sophisticated momentum, breakout, and reversal detection system
- **Multi-Portfolio Support**: Support for baseline (H03) and actual portfolio tracking

## Signal Types (TXYZN Format)

The new signal format follows the convention **T-XYZ-N** where:
- **T**: Trading action (B=Buy, S=Sell, H=Hold)
- **XYZ**: Strategy identifier (3 characters)
- **N**: Signal strength (1-9, where 9 is strongest)

### Current Signal Types:
- **BBRK9**: Strong BUY - Breakout above 20-day high + 0.35×ATR (Strength: 9)
- **BRSV7**: Strong BUY - RSI reversal from oversold with EMA reclaim (Strength: 7)
- **HMOM5**: HOLD - Neutral momentum signal (Strength: 5)
- **SBRK3**: SELL - Breakdown below EMA50 - 0.35×ATR (Strength: 3)  
- **SOVB1**: SELL - Overbought reversal at target levels (Strength: 1)

### Strategy Identifiers:
- **BRK**: Breakout/Breakdown strategy
- **RSV**: RSI Reversal strategy
- **MOM**: General Momentum strategy  
- **OVB**: Overbought/Oversold strategy

### Additional Signal Types Beyond Buy/Sell:
- **H** (Hold): For neutral/consolidation periods
- **W** (Watch): For stocks approaching key levels
- **R** (Reduce): For partial position reduction
- **A** (Add): For position accumulation opportunities

## Quick Start

### Option 1: Docker Deployment (Recommended)

1. **Clone and navigate to project directory**
   ```bash
   git clone <repository-url>
   cd hk-strategy-mvp
   ```

2. **Configure environment (optional)**
   ```bash
   cp config/app_config.template.yaml config/app_config.yaml
   # Edit config/app_config.yaml as needed
   ```

3. **Start the application**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - **Streamlit Dashboard**: http://localhost:8501
   - **PostgreSQL Database**: localhost:5432 (username: trader, database: hk_strategy)
   - **Redis Cache**: localhost:6379

### Option 2: Local Development

1. **Setup local databases**
   ```bash
   # Install and start PostgreSQL and Redis
   ./setup_local_db.sh        # Setup PostgreSQL
   ./install_redis.sh         # Install Redis
   ```

2. **Setup Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Initialize database**
   ```bash
   # Run database setup
   ./setup_database_from_env.sh
   ```

4. **Start the application**
   ```bash
   # Option A: Start dashboard only
   streamlit run src/app.py
   
   # Option B: Use the unified multi-dashboard system (recommended)
   python dashboard.py
   
   # Option C: Simple dashboard (basic functionality)
   python simple_dashboard.py
   ```

## Architecture

```
hk-strategy-mvp/
├── docker-compose.yml           # Docker services configuration
├── Dockerfile                   # Streamlit app container
├── requirements.txt            # Python dependencies
├── init.sql                    # Database initialization
├── config/
│   ├── app_config.yaml         # Main configuration file
│   └── app_config.template.yaml # Configuration template
├── src/
│   ├── app.py                  # Main Streamlit application
│   ├── strategy.py             # HK Strategy Engine with TXYZN signals
│   ├── trading_signals.py      # Legacy signal generation logic  
│   ├── database.py             # Database connection and operations
│   ├── database_local.py       # Local database fallback
│   ├── config_manager.py       # Configuration management
│   └── hsidaily.py            # Historical data processing
├── dashboard.py               # Unified multi-dashboard system (main dashboard)
├── portfolio_manager.py        # Portfolio management utilities
├── simple_dashboard.py         # Simple dashboard interface
└── backups/                    # Database backup files
```

## Database Schema

### Core Tables:
- **`portfolio_positions`**: Stock positions with real-time P&L calculations
- **`trading_signals`**: Generated TXYZN signals with technical indicators
- **`price_history`**: Historical price data for backtesting and analysis
- **`strategy_performance`**: Performance metrics and alpha tracking

### Signal Storage:
- `signal_type`: TXYZN format (e.g., 'BBRK9', 'SRSV3')
- `signal_strength`: Numeric strength (0.1-1.0)
- `strategy_name`: Strategy identifier (Breakout, RSI_Reversal, etc.)
- Technical indicators: RSI, EMA5/20/50, MACD, ATR, Volume ratios

## Configuration

### Using YAML Configuration:
```bash
cp config/app_config.template.yaml config/app_config.yaml
```

Edit `config/app_config.yaml`:
```yaml
database:
  host: localhost
  port: 5432
  database: hk_strategy
  username: trader
  password: your_password

redis:
  host: localhost
  port: 6379
  password: your_redis_password

strategy:
  lookback_days: 90
  use_live_quotes: true
  baseline_date: "2025-08-03"
  baseline_cash: 200000.0
```

### Environment Variables (Alternative):
Create `.env` file:
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=hk_strategy
DB_USER=trader
DB_PASSWORD=your_password
REDIS_URL=redis://localhost:6379
```

## Usage Guide

### 1. Dashboard Overview

The main dashboard (`http://localhost:8501`) provides a unified navigation system with **6 key dashboard sections**:

#### 📊 PORTFOLIOS
- **📋 All Portfolio Overviews**: View and compare all portfolios, manage portfolio creation/editing/copying
- **📊 Portfolio Dashboard**: View, analyze and compare same portfolio over different periods with different strategies  
- **📈 Portfolio Value Analysis**: Analyze portfolio performance across different time periods

#### 🎯 STRATEGY ANALYSIS
- **📈 Equity Strategy Analysis**: Analyze equity strategies from Portfolio Analysis dashboard
- **⚙️ Strategy Editor**: Work on the analysis and editing of trading strategies
- **📊 Strategy Comparison**: Compare different strategy performances (Coming Soon)

#### 🔧 SYSTEM & ADMIN
- **⚙️ System Status**: Health check on system status, database connectivity, and Redis cache
- **🗄️ Database Management**: Portfolio database management and backup utilities (Coming Soon)
- **📋 User Settings**: Configuration and user preferences management (Coming Soon)

### Navigation Features:
- **Hierarchical Navigation**: Clean left-panel navigation with expandable sections
- **Breadcrumb Navigation**: Track your current location within the dashboard system
- **Context-Aware Sidebars**: Dynamic sidebar content based on current page and portfolio selection
- **Unified State Management**: Seamless navigation between different dashboard areas

### 2. Signal Generation

#### Manual Signal Generation:
```python
from src.strategy import HKStrategyEngine

engine = HKStrategyEngine()
results = engine.generate_signals_for_watchlist()
performance = engine.get_portfolio_performance(results)
print(f"Alpha: HK$ {performance['alpha']:,.0f}")
```

#### Understanding TXYZN Signals:

**BBRK9** (Strong Buy Breakout):
- Price breaks above 20-day high + 0.35×ATR
- EMA5 > EMA20 (momentum confirmation)
- High volume (≥1.5× average)
- RSI ≥ 58 or positive MACD momentum

**BRSV7** (Buy RSI Reversal):
- RSI crosses from ≤32 to ≥36
- Price reclaims EMA20 and above EMA5
- Bullish reversal pattern (close in top 70% of range)
- Volume confirmation (≥1.3× average)

**SBRK3** (Sell Breakdown):
- Price breaks below EMA50 - 0.35×ATR
- Negative MACD momentum
- RSI ≤ 42
- High volume (≥1.5× average)

**SOVB1** (Sell Overbought):
- Price at target sell level (stock-specific)
- RSI ≥ 68
- Bearish reversal pattern or pullback ≥0.35×ATR
- Volume confirmation (≥1.3× average)

### 3. Portfolio Management

#### Adding New Positions:
```python
from portfolio_manager import PortfolioManager

pm = PortfolioManager()
pm.add_position("0700.HK", quantity=1000, avg_cost=580.0)
pm.update_position_price("0700.HK", current_price=620.0)
```

#### Tracking Performance:
- **Alpha Calculation**: Actual portfolio value vs H03 baseline
- **Baseline Portfolio**: H03_BASELINE_QTY with fixed quantities
- **Current Portfolio**: CURRENT_QTY with actual holdings
- **Performance Metrics**: Real-time P&L, alpha generation, risk metrics

### 4. Advanced Features

#### Stock-Specific Rules (RAILS):
```python
RAILS = {
    "0700.HK": {"target_sell": 660.0, "stop": 520.0},
    "9988.HK": {"trim_min": 132.0, "add_zone": (112.0, 115.0)},
    "0005.HK": {"target_sell": 111.0, "add_zone": (94.0, 96.0)},
}
```

#### Multi-Dashboard Support:
- `dashboard.py`: Unified multi-dashboard system with 6 key dashboard sections
- `simple_dashboard.py`: Lightweight signal monitoring for basic users
- `src/app.py`: Core Streamlit application for development/testing

### 5. Data Sources

#### Supported Tickers:
The application tracks major HK stocks including:
- **Technology**: 0700.HK (Tencent), 9988.HK (Alibaba)
- **Banking**: 0005.HK (HSBC), 0939.HK (CCB), 1299.HK (AIA)
- **Industrial**: 0388.HK (HK Exchanges), 0857.HK (PetroChina)
- **And more**: See `WATCHLIST` in strategy.py

#### Technical Indicators:
- **EMA (5, 20, 50-period)**: Exponential moving averages
- **RSI (14-period)**: Relative Strength Index momentum oscillator
- **MACD (12, 26, 9)**: Moving Average Convergence Divergence
- **ATR (14-period)**: Average True Range volatility measure
- **Bollinger Bands**: Price volatility bands
- **Volume Analysis**: 20-period volume moving average comparison

### 6. API Reference

#### Core Classes:
- `HKStrategyEngine`: Main strategy execution engine
- `TradingSignalGenerator`: Legacy signal generation (A/B/C/D format)
- `DatabaseManager`: PostgreSQL and Redis data management
- `PortfolioManager`: Portfolio position tracking

#### Key Methods:
```python
# Generate signals for all tickers
results = engine.generate_signals_for_watchlist()

# Get portfolio performance vs baseline
performance = engine.get_portfolio_performance(results) 

# Calculate technical indicators
indicators = engine.compute_indicators(df, use_live=True, ticker="0700.HK")

# Evaluate trading signals
signals = engine.evaluate_signals("0700.HK", df, indicators, today)
```

## Troubleshooting

### Common Issues:

#### Database Connection Issues:
```bash
# Check PostgreSQL status
./test_db_connection.sh

# Reset database
./fix_database.sh

# Manual database setup
./setup_db_manual.sql
```

#### Redis Connection Issues:
```bash
# Check Redis status  
./check_redis_status.sh

# Install Redis
./install_redis.sh

# Start Redis manually
redis-server
```

#### Permission Issues:
```bash
# Fix file permissions
chmod +x *.sh

# Fix database setup permissions
./setup_security.sh
```

#### Python Dependencies:
```bash
# Reinstall requirements
pip install -r requirements.txt --upgrade

# Clear pip cache
pip cache purge
```

### Performance Issues:

#### Slow Signal Generation:
- **Reduce lookback period**: Set `LOOKBACK_DAYS = 30` in strategy.py
- **Disable live quotes**: Set `USE_LIVE_QUOTES = False` 
- **Use Redis caching**: Ensure Redis is running and connected

#### Memory Issues:
- **Restart containers**: `docker-compose restart`
- **Clear Redis cache**: `redis-cli FLUSHALL`
- **Reduce watchlist size**: Modify `WATCHLIST` in strategy.py

### Data Issues:

#### Yahoo Finance API Limits:
- Requests are cached for 1 hour to avoid rate limits
- Live quotes cached for 60 seconds
- Historical data cached for 1 hour

#### Missing Price Data:
```python
# Check data availability
from src.strategy import HKStrategy
strategy = HKStrategy()
df = strategy.yf_history("0700.HK", days=30)
print(f"Data points: {len(df)}")
```

## Monitoring & Maintenance

### Health Checks:
```bash
# Overall system health
./health_check.sh

# Database health
python test_db.py

# Price data test
python test_prices.py
```

### Backup & Recovery:
```bash
# Database backup
pg_dump hk_strategy > backups/hk_strategy_backup.sql

# Restore database
psql hk_strategy < backups/hk_strategy_backup.sql
```

### Log Monitoring:
- **Application logs**: Check Streamlit console output
- **Database logs**: PostgreSQL log files
- **Docker logs**: `docker-compose logs -f`

## Development & Customization

### Adding New Signals:

1. **Define new strategy identifier** in TXYZN format:
   ```python
   # Example: BVWP5 (Buy Volume Weighted Price, strength 5)
   def _determine_custom_signal_type(self, score: float, volume_ratio: float) -> str:
       if score > 0.5 and volume_ratio > 2.0:
           return 'BVWP7'  # Strong volume breakout
       return 'HMOM5'  # Default to hold
   ```

2. **Add signal logic** in strategy.py:
   ```python
   def evaluate_custom_signals(self, ticker: str, indicators: Indicators) -> bool:
       volume_spike = indicators.volume > (indicators.vol20_avg * 2.0)
       price_momentum = indicators.price > indicators.ema20 * 1.02
       return volume_spike and price_momentum
   ```

3. **Update UI descriptions** in app.py:
   ```python
   signal_descriptions['BVWP7'] = 'Strong BUY - Volume breakout (Strength: 7)'
   signal_colors['BVWP7'] = '#00FF00'  # Bright green
   ```

### Adding New Tickers:
```python
# Update watchlist in strategy.py
WATCHLIST.extend(['1398.HK', '2318.HK', '2388.HK'])

# Add to quantity tracking
CURRENT_QTY['1398.HK'] = 5000
H03_BASELINE_QTY['1398.HK'] = 5000
```

### Custom Technical Indicators:
```python
def custom_indicator(df: pd.DataFrame) -> pd.Series:
    # Example: Price relative to 200-day high
    high_200 = df["High"].rolling(200).max()
    return (df["Close"] / high_200) * 100
```

## Version History

- **v2.0**: TXYZN signal format implementation, enhanced dashboard
- **v1.5**: Multi-portfolio support, Redis caching, live quotes
- **v1.0**: Initial HK Strategy MVP with A/B/C/D signals

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-signal-type`
3. Commit changes: `git commit -am 'Add new signal type'`
4. Push to branch: `git push origin feature/new-signal-type`
5. Submit pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review existing issues in the repository
3. Create new issue with detailed description and logs

---

**Disclaimer**: This application is for educational and research purposes only. Not intended as investment advice. Trading involves risk of loss.