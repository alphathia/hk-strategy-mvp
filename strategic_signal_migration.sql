-- Strategic Signal System Migration
-- Transforms A/B/C/D system to professional TXYZn Strategic Signal framework
-- Phase 1: Database Schema Migration

-- ==============================================
-- 1. Update existing trading_signals table for TXYZn format
-- ==============================================

-- Drop old constraint and update signal_type column
ALTER TABLE trading_signals DROP CONSTRAINT IF EXISTS trading_signals_signal_type_check;
ALTER TABLE trading_signals ALTER COLUMN signal_type TYPE VARCHAR(5);
ALTER TABLE trading_signals ADD CONSTRAINT trading_signals_signal_type_check 
  CHECK (signal_type ~ '^[BS][A-Z]{3}[1-9]$');

-- Add new columns for strategic signals
ALTER TABLE trading_signals ADD COLUMN IF NOT EXISTS strategy_key VARCHAR(5);
ALTER TABLE trading_signals ADD COLUMN IF NOT EXISTS action CHAR(1) CHECK (action IN ('B', 'S'));
ALTER TABLE trading_signals ADD COLUMN IF NOT EXISTS strength SMALLINT CHECK (strength BETWEEN 1 AND 9);
ALTER TABLE trading_signals ADD COLUMN IF NOT EXISTS thresholds_json JSONB;
ALTER TABLE trading_signals ADD COLUMN IF NOT EXISTS reasons_json JSONB;
ALTER TABLE trading_signals ADD COLUMN IF NOT EXISTS score_json JSONB;

-- ==============================================
-- 2. Create Strategy Catalog Table
-- ==============================================

CREATE TABLE IF NOT EXISTS strategy (
    strategy_key     VARCHAR(5) PRIMARY KEY,   -- 'BBRK1'-'BBRK9','BOSR1'-'BOSR9', etc.
    base_strategy    VARCHAR(4) NOT NULL,      -- 'BBRK','BOSR','SMAC','BMAC', etc.
    side             CHAR(1) NOT NULL CHECK (side IN ('B', 'S')),
    strength         SMALLINT NOT NULL CHECK (strength BETWEEN 1 AND 9),
    name             VARCHAR(64) NOT NULL,
    description      TEXT NOT NULL,
    category         VARCHAR(32) NOT NULL,     -- 'breakout','mean-reversion','trend','divergence','level'
    active           BOOLEAN NOT NULL DEFAULT true,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create index for strategy queries
CREATE INDEX IF NOT EXISTS idx_strategy_base ON strategy(base_strategy);
CREATE INDEX IF NOT EXISTS idx_strategy_side_strength ON strategy(side, strength DESC);
CREATE INDEX IF NOT EXISTS idx_strategy_category ON strategy(category);

-- ==============================================
-- 3. Create Parameter Set Table for Reproducibility
-- ==============================================

CREATE TABLE IF NOT EXISTS parameter_set (
    param_set_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name             VARCHAR(128) NOT NULL,
    owner_user_id    UUID,                         -- nullable for shared parameters
    price_basis      VARCHAR(16) NOT NULL DEFAULT 'close', -- 'close', 'adj_close'
    params_json      JSONB NOT NULL,               -- canonicalized JSON (RSI gates, VR gates, ATR k, etc.)
    params_hash      CHAR(32) NOT NULL,            -- md5 of canonical params_json
    engine_version   VARCHAR(64) NOT NULL,         -- git sha/tag of signal engine
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (owner_user_id, name),
    UNIQUE (params_hash, engine_version)
);

CREATE INDEX IF NOT EXISTS idx_param_set_hash ON parameter_set(params_hash);

-- ==============================================
-- 4. Create Signal Run Table for Batch Tracking
-- ==============================================

CREATE TABLE IF NOT EXISTS signal_run (
    run_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    param_set_id     UUID NOT NULL REFERENCES parameter_set(param_set_id),
    universe_name    VARCHAR(128) NOT NULL,     -- e.g., 'HK_PORTFOLIO' or 'ALL_HK'
    start_date       DATE NOT NULL,
    end_date         DATE NOT NULL,
    tf               VARCHAR(8) NOT NULL DEFAULT '1d',  -- timeframe: '1d', '1h', '15m'
    calendar_version VARCHAR(64),               -- HKEX calendar version/hash
    notes            TEXT,
    started_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at     TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_signal_run_dates ON signal_run(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_signal_run_param ON signal_run(param_set_id);

-- ==============================================
-- 5. Create Enhanced Signal Event Table
-- ==============================================

CREATE TABLE IF NOT EXISTS signal_event (
    signal_id        BIGSERIAL PRIMARY KEY,
    run_id           UUID REFERENCES signal_run(run_id),
    param_set_id     UUID NOT NULL REFERENCES parameter_set(param_set_id),
    symbol           VARCHAR(10) NOT NULL REFERENCES portfolio_positions(symbol),
    bar_date         DATE NOT NULL,            -- EOD date in HKT
    tf               VARCHAR(8) NOT NULL DEFAULT '1d',
    strategy_key     VARCHAR(5) NOT NULL REFERENCES strategy(strategy_key),
    action           CHAR(1) NOT NULL,          -- 'B' or 'S' (redundant to strategy.side but denormalized)
    strength         SMALLINT NOT NULL CHECK (strength BETWEEN 1 AND 9),
    provisional      BOOLEAN NOT NULL DEFAULT false,

    -- Price and volume context
    close_at_signal  NUMERIC(18,6),
    volume_at_signal BIGINT,

    -- Evidence & scoring breakdowns (JSONB for flexibility)
    thresholds_json  JSONB NOT NULL,           -- e.g., break_level, eps, gates
    reasons_json     JSONB NOT NULL,           -- array of "Close>X | EMA>... | VR..."
    score_json       JSONB NOT NULL,           -- {magnitude:.., momentum:.., trend:.., participation:.., context:.., raw:..}

    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Uniqueness for reproducibility inside a run:
    UNIQUE (run_id, symbol, bar_date, tf, strategy_key)
);

-- Create indexes for signal event queries
CREATE INDEX IF NOT EXISTS idx_signal_event_symbol_date ON signal_event(symbol, bar_date);
CREATE INDEX IF NOT EXISTS idx_signal_event_strategy ON signal_event(strategy_key);
CREATE INDEX IF NOT EXISTS idx_signal_event_side_strength ON signal_event(action, strength DESC);
CREATE INDEX IF NOT EXISTS idx_signal_event_final_only ON signal_event(bar_date) WHERE provisional = false;
CREATE INDEX IF NOT EXISTS idx_signal_event_run ON signal_event(run_id);

-- ==============================================
-- 6. Create Enhanced Indicator Snapshot Table (21 Indicators)
-- ==============================================

DROP TABLE IF EXISTS indicator_snapshot CASCADE;

CREATE TABLE indicator_snapshot (
    symbol           VARCHAR(10) NOT NULL REFERENCES portfolio_positions(symbol),
    bar_date         DATE NOT NULL,
    
    -- Core OHLCV cache (optional but handy for tooltips)
    open_price       NUMERIC(10,3), 
    high_price       NUMERIC(10,3), 
    low_price        NUMERIC(10,3),
    close_price      NUMERIC(10,3), 
    volume           BIGINT,

    -- RSI Family (4 indicators): RSI-6, RSI-12, RSI-14, RSI-24
    rsi6             NUMERIC(8,4),  
    rsi12            NUMERIC(8,4), 
    rsi14            NUMERIC(8,4), 
    rsi24            NUMERIC(8,4),

    -- MACD & PPO (6 indicators)
    macd             NUMERIC(10,6), 
    macd_sig         NUMERIC(10,6), 
    macd_hist        NUMERIC(10,6),
    ppo              NUMERIC(10,6), 
    ppo_sig          NUMERIC(10,6), 
    ppo_hist         NUMERIC(10,6),

    -- Moving Averages (6 indicators)
    ema5             NUMERIC(18,6), 
    ema10            NUMERIC(18,6), 
    ema20            NUMERIC(18,6),
    ema50            NUMERIC(18,6), 
    sma20            NUMERIC(18,6), 
    sma50            NUMERIC(18,6),

    -- Bollinger Bands & Volatility (4 indicators)
    bb_upper         NUMERIC(18,6), 
    bb_middle        NUMERIC(18,6), 
    bb_lower         NUMERIC(18,6),
    atr14            NUMERIC(10,6),

    -- Volume & Flow Analysis (3 indicators): VR-24, MFI-14, A/D Line
    vr24             NUMERIC(12,4), 
    mfi14            NUMERIC(8,4), 
    ad_line          NUMERIC(15,3),

    -- Momentum & Trend Indicators (4 indicators): Stochastic, Williams %R, ADX
    stoch_k          NUMERIC(8,4),  
    stoch_d          NUMERIC(8,4), 
    williams_r       NUMERIC(8,4),  
    adx14            NUMERIC(8,4),

    -- Specialized Indicators (1 indicator): Parabolic SAR
    parabolic_sar    NUMERIC(18,6),

    PRIMARY KEY (symbol, bar_date)
);

-- Create indexes for indicator queries
CREATE INDEX IF NOT EXISTS idx_indicator_snapshot_symbol ON indicator_snapshot(symbol);
CREATE INDEX IF NOT EXISTS idx_indicator_snapshot_date ON indicator_snapshot(bar_date);
CREATE INDEX IF NOT EXISTS idx_indicator_snapshot_rsi14 ON indicator_snapshot(rsi14);
CREATE INDEX IF NOT EXISTS idx_indicator_snapshot_adx ON indicator_snapshot(adx14);

-- ==============================================
-- 7. Create Portfolio Analysis Signal Mapping (Optional)
-- ==============================================

CREATE TABLE IF NOT EXISTS analysis_signal_map (
    analysis_signal_id BIGSERIAL PRIMARY KEY,
    analysis_id        INTEGER NOT NULL REFERENCES portfolio_analyses(id) ON DELETE CASCADE,
    signal_id          BIGINT NOT NULL REFERENCES signal_event(signal_id) ON DELETE CASCADE,

    -- snapshot of portfolio context at that date (for audit)
    position_qty       NUMERIC(18,6),
    cash_balance       NUMERIC(18,4),

    included           BOOLEAN NOT NULL DEFAULT true,    -- allow future filtering
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (analysis_id, signal_id)
);

CREATE INDEX IF NOT EXISTS idx_analysis_signal_analysis ON analysis_signal_map(analysis_id);
CREATE INDEX IF NOT EXISTS idx_analysis_signal_signal ON analysis_signal_map(signal_id);

-- ==============================================
-- 8. Create Views for Easy Querying
-- ==============================================

-- View for latest indicator data per symbol
CREATE OR REPLACE VIEW latest_indicator_snapshot AS
SELECT DISTINCT ON (symbol) *
FROM indicator_snapshot
ORDER BY symbol, bar_date DESC;

-- View for latest signals per symbol
CREATE OR REPLACE VIEW latest_signal_events AS
SELECT DISTINCT ON (symbol, strategy_key) *
FROM signal_event
WHERE provisional = false
ORDER BY symbol, strategy_key, bar_date DESC;

-- View for signal summary with strategy details
CREATE OR REPLACE VIEW signal_summary AS
SELECT 
    se.signal_id,
    se.symbol,
    se.bar_date,
    se.strategy_key,
    s.name as strategy_name,
    s.category as strategy_category,
    se.action,
    se.strength,
    se.close_at_signal,
    se.volume_at_signal,
    se.reasons_json,
    se.score_json,
    se.created_at
FROM signal_event se
JOIN strategy s ON se.strategy_key = s.strategy_key
WHERE se.provisional = false
ORDER BY se.bar_date DESC, se.strength DESC;

-- ==============================================
-- 9. Migration Comments and Status
-- ==============================================

COMMENT ON TABLE strategy IS 'Catalog of all TXYZn strategic signal strategies with base strategy, side, and strength';
COMMENT ON TABLE parameter_set IS 'Versioned parameter configurations for reproducible signal generation';
COMMENT ON TABLE signal_run IS 'Batch execution tracking for signal computation runs';
COMMENT ON TABLE signal_event IS 'Individual TXYZn signal events with full evidence and scoring';
COMMENT ON TABLE indicator_snapshot IS 'Daily technical indicators (21 total) for all symbols';
COMMENT ON TABLE analysis_signal_map IS 'Links signals to specific portfolio analyses for historical context';

SELECT 'Strategic Signal database schema migration completed successfully' AS status;