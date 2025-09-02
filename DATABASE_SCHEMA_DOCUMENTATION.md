# Database Schema Documentation - Strategic Signal System

**Last Updated:** September 2, 2025  
**Schema Version:** 1.0  
**Database:** PostgreSQL 12+  

## 🗄️ Overview

The HK Strategy MVP database now includes the complete Strategic Signal System alongside the original portfolio management tables. The system supports professional TXYZn format signals with evidence tracking, technical indicator integration, and comprehensive strategy management.

## 📊 Table Relationships

```
portfolio_positions ──┐
                      ├── trading_signals (legacy A/B/C/D + new TXYZn)
                      └── daily_equity_technicals
                           │
                           └── indicator_snapshot (Strategic Signal format)
                                │
parameter_set ───────────┬─── signal_run
                         │     │
                         └─────┴── signal_event ─── strategy (108 TXYZn combinations)
                                    │
portfolio_analyses ────────────────┘
```

## 📋 Core Tables

### Portfolio Management (Existing)

#### `portfolio_positions`
**Purpose**: Multi-portfolio equity position tracking
```sql
CREATE TABLE portfolio_positions (
    id              SERIAL PRIMARY KEY,
    symbol          VARCHAR(10) NOT NULL,
    company_name    VARCHAR(200),
    quantity        INTEGER NOT NULL DEFAULT 0,
    avg_cost        DECIMAL(10,3) NOT NULL DEFAULT 0,
    current_price   DECIMAL(10,3) DEFAULT 0,
    market_value    DECIMAL(12,2) GENERATED ALWAYS AS (quantity * current_price) STORED,
    unrealized_pnl  DECIMAL(12,2) GENERATED ALWAYS AS ((current_price - avg_cost) * quantity) STORED,
    sector          VARCHAR(50),
    last_updated    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    portfolio_id    VARCHAR(50),
    
    CONSTRAINT unique_portfolio_symbol UNIQUE (portfolio_id, symbol)
);
```

**Key Features:**
- Multi-portfolio support via `portfolio_id`
- Computed columns for `market_value` and `unrealized_pnl`
- Hong Kong equity format symbols (e.g., '0700.HK')

#### `daily_equity_technicals`
**Purpose**: Comprehensive daily technical indicator storage
```sql  
CREATE TABLE daily_equity_technicals (
    id                  SERIAL PRIMARY KEY,
    symbol              VARCHAR(10) NOT NULL,
    trade_date          DATE NOT NULL,
    
    -- OHLCV Data
    open_price          DECIMAL(10,3) NOT NULL,
    close_price         DECIMAL(10,3) NOT NULL,
    high_price          DECIMAL(10,3) NOT NULL,
    low_price           DECIMAL(10,3) NOT NULL,
    volume              BIGINT DEFAULT 0,
    
    -- Technical Indicators (21 types)
    rsi_14              DECIMAL(5,2),    -- 14-day RSI
    macd                DECIMAL(10,6),   -- MACD line
    macd_signal         DECIMAL(10,6),   -- MACD signal line
    bollinger_upper     DECIMAL(10,3),   -- Upper Bollinger Band
    bollinger_lower     DECIMAL(10,3),   -- Lower Bollinger Band
    sma_20              DECIMAL(10,3),   -- 20-day Simple Moving Average
    ema_12              DECIMAL(10,3),   -- 12-day Exponential Moving Average
    ema_26              DECIMAL(10,3),   -- 26-day Exponential Moving Average
    volume_sma_20       BIGINT,          -- 20-day Volume SMA
    -- ... (additional indicators)
    
    UNIQUE (symbol, trade_date)
);
```

**Data Source**: Yahoo Finance API via `yfinance` library  
**Update Frequency**: Daily after market close  
**Coverage**: 11 HK equity symbols in current portfolio  

### Strategic Signal System (New)

#### `strategy`
**Purpose**: Catalog of all 108 TXYZn strategy combinations
```sql
CREATE TABLE strategy (
    strategy_key    VARCHAR(5) PRIMARY KEY,      -- 'BBRK1' to 'SRES9'
    base_strategy   VARCHAR(4) NOT NULL,         -- 'BBRK', 'BOSR', etc.
    side            CHAR(1) NOT NULL CHECK (side IN ('B', 'S')),
    strength        SMALLINT NOT NULL CHECK (strength BETWEEN 1 AND 9),
    name            VARCHAR(64) NOT NULL,        -- 'Buy • Breakout (Moderate)'
    description     TEXT NOT NULL,               -- Detailed strategy explanation
    category        VARCHAR(32) NOT NULL,        -- 'breakout', 'mean-reversion', etc.
    active          BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**Strategy Categories:**
- `breakout`: Price breaks through resistance/support with volume
- `mean-reversion`: RSI/momentum reversal from overbought/oversold
- `trend`: MACD/moving average trend following
- `divergence`: Price-indicator divergence patterns
- `level`: Support/resistance level interactions

**Base Strategies (12 total):**
```
Buy Strategies (6):
• BBRK - Buy Breakout
• BOSR - Buy Oversold Reversal  
• BMAC - Buy MACD Cross
• BBOL - Buy Bollinger Bounce
• BDIV - Buy Divergence
• BSUP - Buy Support

Sell Strategies (6):
• SBDN - Sell Breakdown
• SOBR - Sell Overbought Reversal
• SMAC - Sell MACD Cross
• SBND - Sell Bollinger Bounce
• SDIV - Sell Divergence
• SRES - Sell Resistance
```

#### `parameter_set`
**Purpose**: Reproducible parameter configurations for signal generation
```sql
CREATE TABLE parameter_set (
    param_set_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name             VARCHAR(128) NOT NULL,
    owner_user_id    UUID,
    price_basis      VARCHAR(16) NOT NULL DEFAULT 'close',
    params_json      JSONB NOT NULL,              -- Technical indicator parameters
    params_hash      CHAR(32) NOT NULL,           -- MD5 hash for uniqueness
    engine_version   VARCHAR(64) NOT NULL,        -- Signal engine version
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    UNIQUE (params_hash, engine_version)
);
```

**Sample Parameter Set:**
```json
{
  "rsi_period": 14,
  "bb_period": 20,
  "bb_std_dev": 2.0,
  "macd_fast": 12,
  "macd_slow": 26,
  "macd_signal": 9,
  "volume_sma_period": 20
}
```

#### `signal_run`
**Purpose**: Batch tracking for signal generation execution
```sql
CREATE TABLE signal_run (
    run_id           VARCHAR(64) PRIMARY KEY,     -- 'YYYYMMDD_HHMMSS_identifier'
    parameter_set_id UUID NOT NULL REFERENCES parameter_set(param_set_id),
    symbol_count     INTEGER DEFAULT 0,
    status           VARCHAR(20) DEFAULT 'running',  -- 'running', 'completed', 'failed'
    start_time       TIMESTAMPTZ NOT NULL DEFAULT now(),
    end_time         TIMESTAMPTZ,
    notes            TEXT
);
```

**Workflow:**
1. Create parameter set with technical indicator configurations
2. Start signal run referencing parameter set
3. Generate signal events for each symbol/date combination
4. Complete signal run with final statistics

#### `signal_event`
**Purpose**: Individual TXYZn signal occurrences with evidence
```sql
CREATE TABLE signal_event (
    id           BIGSERIAL PRIMARY KEY,
    run_id       VARCHAR(64) REFERENCES signal_run(run_id),
    symbol       VARCHAR(10) NOT NULL,
    timestamp    TIMESTAMPTZ NOT NULL DEFAULT now(),
    signal       VARCHAR(5) NOT NULL REFERENCES strategy(strategy_key),
    confidence   DECIMAL(5,4) NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    strength     INTEGER NOT NULL CHECK (strength BETWEEN 1 AND 9),
    evidence     JSONB NOT NULL,                  -- Structured reasoning
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    UNIQUE (run_id, symbol, timestamp, signal)
);
```

**Evidence Structure:**
```json
{
  "thresholds": {
    "rsi_overbought": 70,
    "bb_position": 0.95,
    "volume_ratio": 1.5
  },
  "reasons": [
    "RSI 75.5 above overbought threshold (70)",
    "Price near upper Bollinger Band (95%)",
    "Volume 50% above 20-day average"
  ],
  "score": 85.2,
  "metadata": {
    "calculated_at": "2025-09-02T10:30:00Z",
    "price_at_signal": 315.20
  }
}
```

#### `indicator_snapshot`
**Purpose**: Technical indicator values in Strategic Signal format
```sql
CREATE TABLE indicator_snapshot (
    id               BIGSERIAL PRIMARY KEY,
    symbol           VARCHAR(10) NOT NULL,
    timestamp        TIMESTAMPTZ NOT NULL DEFAULT now(),
    indicator_name   VARCHAR(50) NOT NULL,        -- 'rsi14', 'macd', 'bb_upper', etc.
    value            DECIMAL(18,6),
    metadata         JSONB,                       -- Indicator parameters
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    UNIQUE (symbol, timestamp, indicator_name)
);
```

**Supported Indicators (21 types):**
```
RSI Family (4): rsi14, rsi21, rsi50, rsi_divergence
MACD/PPO (4): macd, ppo, macd_histogram, ppo_signal
Moving Averages (6): sma20, ema20, sma50, ema50, sma200, ema200
Bollinger Bands (3): bb_upper, bb_lower, bb_percent
Volume/Flow (3): volume_sma, volume_ratio, adl
Momentum (1): momentum
```

## 🔗 Data Integration

### Technical Indicator Bridge
```sql
-- Example: Populate Strategic Signal format from existing data
INSERT INTO indicator_snapshot (symbol, timestamp, indicator_name, value, metadata)
SELECT 
    symbol,
    trade_date::timestamp,
    'rsi14',
    rsi_14,
    '{"period": 14, "source": "close"}'::jsonb
FROM daily_equity_technicals 
WHERE rsi_14 IS NOT NULL;
```

### Signal Generation Pipeline
1. **Data Collection**: `daily_equity_technicals` populated from Yahoo Finance
2. **Indicator Conversion**: Transform to `indicator_snapshot` format
3. **Strategy Evaluation**: Apply 108 strategy rules to indicator data
4. **Signal Creation**: Generate TXYZn signals with evidence in `signal_event`
5. **Dashboard Display**: Real-time signal monitoring and analysis

## 📊 Management Views

### `recent_signal_events`
**Purpose**: Dashboard-ready signal data with strategy details
```sql
CREATE VIEW recent_signal_events AS
SELECT 
    se.id,
    se.symbol,
    se.signal,
    s.name as strategy_name,
    s.category as strategy_category,
    se.confidence,
    se.strength,
    se.timestamp,
    se.evidence,
    se.run_id
FROM signal_event se
JOIN strategy s ON se.signal = s.strategy_key
ORDER BY se.timestamp DESC;
```

### `latest_indicator_snapshot`
**Purpose**: Most recent indicator values per symbol
```sql
CREATE VIEW latest_indicator_snapshot AS
SELECT DISTINCT ON (symbol, indicator_name) *
FROM indicator_snapshot
ORDER BY symbol, indicator_name, timestamp DESC;
```

## 🎯 TXYZn Signal Format

### Format Specification
```
Pattern: ^[BS][A-Z]{3}[1-9]$

Components:
T    - Transaction type (B=Buy, S=Sell)
XYZ  - 3-character strategy code
n    - Strength level (1-9)

Examples:
BBRK5 - Buy Breakout, Moderate Strength
SOBR8 - Sell Overbought Reversal, Very Strong
BMAC3 - Buy MACD Cross, Light Signal
```

### Strength Levels
```
1-2: Weak signals (experimental, low confidence)
3-4: Light signals (early indicators, moderate confidence)
5-6: Moderate signals (balanced risk/reward)  
7-8: Strong signals (high confidence, clear patterns)
9:   Extreme signals (rare, very high confidence)
```

## 🔍 Usage Examples

### Query Recent Signals
```sql
SELECT 
    symbol,
    signal,
    strategy_name,
    confidence,
    strength,
    timestamp
FROM recent_signal_events 
WHERE symbol = '0700.HK'
  AND timestamp >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY timestamp DESC;
```

### Find Overbought Conditions
```sql
SELECT 
    symbol,
    value as rsi_value,
    timestamp
FROM indicator_snapshot 
WHERE indicator_name = 'rsi14'
  AND value > 70
ORDER BY timestamp DESC;
```

### Strategy Performance Analysis
```sql
SELECT 
    s.category,
    s.side,
    COUNT(se.id) as signal_count,
    AVG(se.confidence) as avg_confidence,
    AVG(se.strength) as avg_strength
FROM signal_event se
JOIN strategy s ON se.signal = s.strategy_key
WHERE se.timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY s.category, s.side
ORDER BY signal_count DESC;
```

## 🔧 Maintenance

### Daily Tasks
- Technical indicator data update via `daily_equity_technicals`
- Signal generation runs for new market data
- Dashboard data refresh and monitoring

### Weekly Tasks
- Signal performance analysis and validation
- Strategy effectiveness review
- Data quality checks and cleanup

### Monthly Tasks
- Parameter optimization based on performance
- Strategy catalog updates and refinements
- Historical data archival and maintenance

## 🚀 Dashboard Integration

### Data Access Patterns
```javascript
// Fetch strategies for management interface
fetch('/api/strategies')
  .then(response => response.json())
  .then(strategies => populateStrategyList(strategies));

// Get recent signals for monitoring
fetch('/api/signals?limit=50')
  .then(response => response.json())  
  .then(signals => updateSignalFeed(signals));

// Validate TXYZn format
fetch('/api/validate/signal', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({signal: 'BBRK5'})
})
.then(response => response.json())
.then(result => console.log('Valid:', result.is_valid));
```

### Required Permissions
```sql
GRANT SELECT ON strategy TO dashboard_user;
GRANT SELECT ON signal_event TO dashboard_user;  
GRANT SELECT ON indicator_snapshot TO dashboard_user;
GRANT SELECT ON recent_signal_events TO dashboard_user;
GRANT INSERT ON signal_event TO dashboard_user;  -- For manual signal creation
```

---

## 📝 Schema Evolution

**Version 1.0** (September 2025)
- Initial Strategic Signal System deployment
- 108 TXYZn strategy combinations
- Evidence-based signal tracking
- Technical indicator integration
- Dashboard management interface

**Future Enhancements**
- Advanced validation functions
- Machine learning signal confidence scoring
- Real-time signal streaming
- Portfolio performance attribution
- Risk management integration

---

*Database Schema Documentation v1.0 - Strategic Signal System*