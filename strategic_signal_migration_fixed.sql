-- Strategic Signal System Migration - Fixed Version
-- Handles multi-portfolio schema and existing constraints

-- ==============================================
-- 1. Create Strategy Catalog Table
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
-- 2. Create Parameter Set Table for Reproducibility
-- ==============================================

CREATE TABLE IF NOT EXISTS parameter_set (
    id               SERIAL PRIMARY KEY,       -- Use SERIAL instead of UUID for compatibility
    parameters       JSONB NOT NULL,           -- canonicalized JSON parameters
    parameter_hash   CHAR(32) NOT NULL,        -- md5 of canonical parameters
    name             VARCHAR(128),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (parameter_hash)
);

CREATE INDEX IF NOT EXISTS idx_param_set_hash ON parameter_set(parameter_hash);

-- ==============================================
-- 3. Create Signal Run Table for Batch Tracking
-- ==============================================

CREATE TABLE IF NOT EXISTS signal_run (
    run_id           VARCHAR(64) PRIMARY KEY,  -- Use VARCHAR instead of UUID
    parameter_set_id INTEGER NOT NULL REFERENCES parameter_set(id),
    symbol_count     INTEGER DEFAULT 0,
    status           VARCHAR(20) DEFAULT 'running',
    start_time       TIMESTAMPTZ NOT NULL DEFAULT now(),
    end_time         TIMESTAMPTZ,
    notes            TEXT
);

CREATE INDEX IF NOT EXISTS idx_signal_run_param ON signal_run(parameter_set_id);
CREATE INDEX IF NOT EXISTS idx_signal_run_status ON signal_run(status);

-- ==============================================
-- 4. Create Enhanced Signal Event Table
-- ==============================================

CREATE TABLE IF NOT EXISTS signal_event (
    id               BIGSERIAL PRIMARY KEY,
    run_id           VARCHAR(64) REFERENCES signal_run(run_id),
    symbol           VARCHAR(10) NOT NULL,     -- Remove FK constraint for flexibility
    timestamp        TIMESTAMPTZ NOT NULL DEFAULT now(),
    signal           VARCHAR(5) NOT NULL REFERENCES strategy(strategy_key),
    confidence       DECIMAL(5,4) NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    strength         INTEGER NOT NULL CHECK (strength BETWEEN 1 AND 9),
    evidence         JSONB NOT NULL,           -- thresholds, reasons, score
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    -- Ensure unique signals per run/symbol/timestamp
    UNIQUE (run_id, symbol, timestamp, signal)
);

-- Create indexes for signal event queries
CREATE INDEX IF NOT EXISTS idx_signal_event_symbol_timestamp ON signal_event(symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_signal_event_signal ON signal_event(signal);
CREATE INDEX IF NOT EXISTS idx_signal_event_run ON signal_event(run_id);

-- ==============================================
-- 5. Create Enhanced Indicator Snapshot Table
-- ==============================================

CREATE TABLE IF NOT EXISTS indicator_snapshot (
    id               BIGSERIAL PRIMARY KEY,
    symbol           VARCHAR(10) NOT NULL,
    timestamp        TIMESTAMPTZ NOT NULL DEFAULT now(),
    indicator_name   VARCHAR(50) NOT NULL,     -- 'rsi14', 'macd', 'bb_upper', etc.
    value            DECIMAL(18,6),
    metadata         JSONB,                    -- indicator parameters and context
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    -- Ensure unique indicators per symbol/timestamp
    UNIQUE (symbol, timestamp, indicator_name)
);

-- Create indexes for indicator queries
CREATE INDEX IF NOT EXISTS idx_indicator_snapshot_symbol ON indicator_snapshot(symbol);
CREATE INDEX IF NOT EXISTS idx_indicator_snapshot_timestamp ON indicator_snapshot(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_indicator_snapshot_indicator ON indicator_snapshot(indicator_name);

-- ==============================================
-- 6. Update trading_signals table for compatibility
-- ==============================================

-- Update signal_type column to support TXYZn format
ALTER TABLE trading_signals ALTER COLUMN signal_type TYPE VARCHAR(5);
ALTER TABLE trading_signals ADD CONSTRAINT trading_signals_signal_type_check 
  CHECK (signal_type ~ '^[BS][A-Z]{3}[1-9]$' OR signal_type IN ('A', 'B', 'C', 'D'));

-- Add new columns for strategic signals (if not exist)
ALTER TABLE trading_signals ADD COLUMN IF NOT EXISTS strategy_key VARCHAR(5);
ALTER TABLE trading_signals ADD COLUMN IF NOT EXISTS action CHAR(1) CHECK (action IN ('B', 'S'));
ALTER TABLE trading_signals ADD COLUMN IF NOT EXISTS strength SMALLINT CHECK (strength BETWEEN 1 AND 9);
ALTER TABLE trading_signals ADD COLUMN IF NOT EXISTS evidence JSONB;

-- ==============================================
-- 7. Create Views for Easy Querying
-- ==============================================

-- View for latest indicator data per symbol
CREATE OR REPLACE VIEW latest_indicator_snapshot AS
SELECT DISTINCT ON (symbol, indicator_name) *
FROM indicator_snapshot
ORDER BY symbol, indicator_name, timestamp DESC;

-- View for recent signal events
CREATE OR REPLACE VIEW recent_signal_events AS
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

-- ==============================================
-- 8. Grant Permissions
-- ==============================================

GRANT SELECT ON strategy TO PUBLIC;
GRANT SELECT ON parameter_set TO PUBLIC;
GRANT SELECT ON signal_run TO PUBLIC;
GRANT SELECT ON signal_event TO PUBLIC;
GRANT SELECT ON indicator_snapshot TO PUBLIC;
GRANT SELECT ON latest_indicator_snapshot TO PUBLIC;
GRANT SELECT ON recent_signal_events TO PUBLIC;