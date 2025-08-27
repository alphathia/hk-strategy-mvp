# HK Equity Trading Strategy MVP

A Docker-based Streamlit application for Hong Kong equity trading strategy with PostgreSQL database and Redis caching.

## Features

- **Portfolio Management**: Track HK equity positions with real-time P&L calculation
- **Trading Signals**: Generate A/B/C/D signals using technical indicators (RSI, Moving Averages, Bollinger Bands)
- **Performance Analytics**: Visualize portfolio performance and risk metrics
- **Real-time Data**: PostgreSQL for persistent storage, Redis for caching

## Signal Types

- **A**: Strong Buy - High conviction bullish signal
- **B**: Buy - Moderate bullish signal  
- **C**: Hold - Neutral/weak signal
- **D**: Sell - Bearish signal

## Quick Start

1. **Clone and navigate to project directory**
   ```bash
   cd hk-strategy-mvp
   ```

2. **Start the application**
   ```bash
   docker-compose up --build
   ```

3. **Access the application**
   - Streamlit App: http://localhost:8501
   - PostgreSQL: localhost:5432
   - Redis: localhost:6379

## Architecture

```
├── docker-compose.yml    # Docker services configuration
├── Dockerfile           # Streamlit app container
├── requirements.txt     # Python dependencies
├── init.sql            # Database initialization
└── src/
    ├── app.py          # Main Streamlit application
    ├── database.py     # Database connection and operations
    └── trading_signals.py # Signal generation logic
```

## Database Schema

- `portfolio_positions`: Stock positions with P&L calculations
- `trading_signals`: Generated A/B/C/D signals with technical indicators
- `price_history`: Historical price data for analysis

## Configuration

Copy `.env.example` to `.env` and modify if needed:

```bash
cp .env.example .env
```

## Development

For local development without Docker:

1. **Start PostgreSQL and Redis locally**
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the app**
   ```bash
   streamlit run src/app.py
   ```

## Sample Data

The application comes pre-loaded with 10 major HK stocks including:
- Tencent (0700.HK)
- HSBC (0005.HK)
- AIA Group (1299.HK)
- China Construction Bank (0939.HK)
- And more...

## Technical Indicators

The strategy uses multiple technical indicators:
- **RSI (14-period)**: Momentum oscillator
- **Moving Averages**: 5, 20, 50-day periods
- **Bollinger Bands**: Price volatility indicator
- **Volume Analysis**: Trading volume consideration