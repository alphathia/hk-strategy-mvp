# HK Strategy Multi-Portfolio Dashboard

A comprehensive Streamlit-based multi-portfolio dashboard system for Hong Kong equity strategy management with real-time data integration and advanced analytics.

## Features

### 📊 **Multi-Portfolio Management**
- **Portfolio Overview**: Compare and manage multiple portfolios with unified interface
- **Database-Driven Storage**: PostgreSQL backend for persistent portfolio data
- **Real-time Portfolio Editing**: Add, modify, and delete positions with live updates
- **Portfolio Copying & Creation**: Duplicate portfolios and create new ones with guided workflows
- **Interactive Position Management**: Modal dialogs for streamlined position editing

### 🎯 **Advanced Trading & Analysis**
- **TXYZN Signal System**: Modern trading signals with strength indicators (B/S/H-XYZ-1-9)
- **Hong Kong Equity Focus**: Optimized for HKEX market with HK-specific indicators
- **Strategy Analysis Engine**: Compare different trading strategies across portfolios
- **Performance Analytics**: Real-time P&L tracking, alpha generation, risk metrics

### 🏗️ **Unified Navigation System**
- **6 Key Dashboard Sections**: Portfolios, Strategy Analysis, System Admin
- **Hierarchical Navigation**: Organized left-panel with expandable sections
- **Context-Aware Sidebars**: Dynamic content based on current page and selection
- **Breadcrumb Navigation**: Visual navigation trail for complex workflows

## How to Run

### Option 1: Full Setup with Database (Recommended)
```bash
# 1. Setup Python environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Setup PostgreSQL and Redis
./setup_local_db.sh        # PostgreSQL setup
./install_redis.sh         # Redis setup

# 3. Initialize database
./setup_database_from_env.sh

# 4. Start the dashboard
python dashboard.py
```

### Option 2: Quick Start with Docker
```bash
# Start all services (PostgreSQL, Redis, Dashboard)
docker-compose up --build
```

### Access Points
- **Main Dashboard**: http://localhost:8501
- **Database**: PostgreSQL on localhost:5432
- **Cache**: Redis on localhost:6379

## Dashboard Sections

### 📊 **PORTFOLIOS Section**

#### All Portfolio Overviews
- **Portfolio Comparison Table**: Side-by-side comparison of all portfolios
- **Portfolio Actions**: Create, copy, edit, delete portfolio operations  
- **Aggregate Metrics**: Total portfolios, positions, active positions
- **Quick Navigation**: Click portfolio names to access detailed views

#### Portfolio Dashboard
- **Real-time Position Table**: Live prices with P&L calculations
- **Portfolio Editing Mode**: Add/modify/delete positions with validation
- **Interactive Dialogs**: Modal forms for position management
- **Performance Tracking**: Value, cost basis, profit/loss analysis

#### Portfolio Value Analysis  
- **Historical Performance**: Track portfolio value over time periods
- **Strategy Comparison**: Compare same portfolio with different strategies
- **Risk Analysis**: Volatility, drawdown, and performance metrics

### 🎯 **STRATEGY ANALYSIS Section**

#### Equity Strategy Analysis
- **TXYZN Signal Generation**: Modern B/S/H-XYZ-1-9 signal format
- **Technical Indicators**: RSI, EMA, MACD, ATR, Bollinger Bands
- **Signal Strength Scoring**: 1-9 confidence levels for trade decisions
- **Hong Kong Market Focus**: HKEX-optimized indicators and rules

#### Strategy Editor
- **Strategy Configuration**: Modify signal parameters and thresholds
- **Backtesting Tools**: Historical performance analysis
- **Custom Rules**: Stock-specific RAILS configuration
- **Strategy Comparison**: A/B testing of different approaches

### 🔧 **SYSTEM & ADMIN Section**

#### System Status
- **Health Monitoring**: Database and Redis connectivity status
- **Performance Metrics**: System resource usage and response times
- **Data Validation**: Yahoo Finance API status and data quality checks
- **Error Logging**: System error tracking and troubleshooting

### Position Management Features
- **Smart Symbol Validation**: Yahoo Finance integration for symbol verification
- **Bulk Operations**: Import/export portfolio data
- **Position History**: Track changes over time
- **Risk Validation**: Position size and allocation checks

## Sample Data
The system comes with pre-configured Hong Kong equity portfolios including:
- **0700.HK (Tencent)**: Major technology position
- **9988.HK (Alibaba)**: E-commerce and cloud leader
- **0005.HK (HSBC)**: Banking sector exposure
- **0939.HK (CCB)**: Chinese banking sector
- **1299.HK (AIA)**: Insurance sector representative

## Data Sources & Integration
- **Yahoo Finance API**: Real-time and historical price data
- **PostgreSQL Database**: Persistent portfolio storage with ACID compliance
- **Redis Cache**: High-performance caching for frequently accessed data
- **HKEX Calendar Integration**: Hong Kong trading calendar for analysis periods

## Technical Architecture
- **Multi-layer Caching**: 1-hour cache for historical data, 60-second cache for live quotes
- **Database Connection Pooling**: Optimized database connections with automatic failover
- **Session State Management**: Persistent user experience across page navigation
- **Real-time Price Updates**: Live price fetching with rate limiting and error handling

## Performance & Reliability
- **Database Persistence**: All portfolio changes saved to PostgreSQL immediately
- **Automatic Backup**: Database backup utilities for data protection
- **Error Recovery**: Graceful handling of API failures and database issues
- **Scalable Architecture**: Designed to handle multiple portfolios and users

## Navigation & User Experience
- **Unified Navigation**: Single-page application with section-based organization
- **Responsive Design**: Optimized for various screen sizes and resolutions
- **Modal Dialogs**: Streamlined workflows for portfolio operations
- **Progress Tracking**: Visual feedback for long-running operations like signal generation