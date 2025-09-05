-- Migration: Update trading_signals schema for TXYZN format support
-- This migration updates the legacy A/B/C/D format to support modern TXYZN signal format

BEGIN;

-- Step 1: Backup existing data
CREATE TABLE IF NOT EXISTS trading_signals_backup AS 
SELECT * FROM trading_signals;

-- Backed up existing trading_signals data

-- Step 2: Drop the old constraint that limits signal_type to A/B/C/D
ALTER TABLE trading_signals DROP CONSTRAINT IF EXISTS trading_signals_signal_type_check;

-- Step 3: Modify signal_type column to support TXYZN format (5 characters)
ALTER TABLE trading_signals ALTER COLUMN signal_type TYPE VARCHAR(5);

-- Step 4: Add new columns for strategy base and magnitude
ALTER TABLE trading_signals ADD COLUMN IF NOT EXISTS strategy_base VARCHAR(4);
ALTER TABLE trading_signals ADD COLUMN IF NOT EXISTS signal_magnitude INTEGER;
ALTER TABLE trading_signals ADD COLUMN IF NOT EXISTS strategy_category VARCHAR(20);

-- Step 5: Update existing A/B/C/D signals to TXYZN format
UPDATE trading_signals 
SET 
    signal_type = CASE 
        WHEN signal_type = 'A' THEN 'BBRK7'  -- Strong Buy Breakout
        WHEN signal_type = 'B' THEN 'BBRK5'  -- Moderate Buy Breakout  
        WHEN signal_type = 'C' THEN NULL     -- No signal - removed hold signals
        WHEN signal_type = 'D' THEN 'SBRK3'  -- Sell Breakdown
        ELSE signal_type
    END,
    strategy_base = CASE 
        WHEN signal_type = 'A' THEN 'BBRK'
        WHEN signal_type = 'B' THEN 'BBRK'
        WHEN signal_type = 'C' THEN NULL
        WHEN signal_type = 'D' THEN 'SBRK'
        ELSE LEFT(signal_type, 4)
    END,
    signal_magnitude = CASE 
        WHEN signal_type = 'A' THEN 7
        WHEN signal_type = 'B' THEN 5
        WHEN signal_type = 'C' THEN NULL
        WHEN signal_type = 'D' THEN 3
        ELSE CAST(RIGHT(signal_type, 1) AS INTEGER)
    END,
    strategy_category = CASE 
        WHEN signal_type IN ('A', 'B') THEN 'breakout'
        WHEN signal_type = 'C' THEN 'neutral'
        WHEN signal_type = 'D' THEN 'breakout'
        ELSE 'breakout'
    END
WHERE signal_type IN ('A', 'B', 'C', 'D');

-- Step 6: Add new constraints for TXYZN format
ALTER TABLE trading_signals 
ADD CONSTRAINT trading_signals_txyzn_format_check 
CHECK (signal_type ~ '^[BSH][A-Z]{3}[1-9]$');

ALTER TABLE trading_signals 
ADD CONSTRAINT trading_signals_strategy_base_check 
CHECK (strategy_base ~ '^[A-Z]{4}$');

ALTER TABLE trading_signals 
ADD CONSTRAINT trading_signals_magnitude_check 
CHECK (signal_magnitude BETWEEN 1 AND 9);

-- Step 7: Create strategy_catalog table
CREATE TABLE IF NOT EXISTS strategy_catalog (
    id SERIAL PRIMARY KEY,
    strategy_base VARCHAR(4) NOT NULL UNIQUE,
    strategy_name VARCHAR(100) NOT NULL,
    signal_side CHAR(1) NOT NULL CHECK (signal_side IN ('B', 'S', 'H')),
    category VARCHAR(20) NOT NULL,
    description TEXT,
    required_indicators TEXT[], -- Array of required indicator names
    optional_indicators TEXT[], -- Array of optional indicator names
    default_parameters JSONB,   -- Default parameter values
    parameter_ranges JSONB,     -- Parameter min/max ranges
    usage_guidelines TEXT,
    risk_considerations TEXT,
    market_conditions TEXT[],   -- Array of suitable market conditions
    implementation_complexity VARCHAR(10) CHECK (implementation_complexity IN ('simple', 'moderate', 'complex')),
    computational_cost VARCHAR(10) CHECK (computational_cost IN ('low', 'medium', 'high')),
    color_scheme JSONB,         -- Colors for different strength levels
    icon VARCHAR(50),
    priority INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Step 8: Insert base strategies from strategy_dictionary.py
INSERT INTO strategy_catalog (
    strategy_base, strategy_name, signal_side, category, description,
    required_indicators, optional_indicators, default_parameters,
    usage_guidelines, risk_considerations, market_conditions,
    implementation_complexity, computational_cost, priority
) VALUES 
-- BUY STRATEGIES
('BBRK', 'Buy Breakout', 'B', 'breakout', 
 'Breakout strategy identifies when price breaks above key resistance levels with volume confirmation',
 ARRAY['bb_upper', 'ema20', 'close_price', 'volume'],
 ARRAY['rsi14', 'adx14', 'atr14', 'vr24'],
 '{"breakout_epsilon": 0.005, "volume_threshold": 1.5, "rsi_max": 85}',
 'Best used in trending markets with clear resistance levels',
 'False breakouts are common - requires volume confirmation',
 ARRAY['trending', 'volatile'],
 'moderate', 'medium', 1),

('BOSR', 'Buy Oversold Reclaim', 'B', 'mean-reversion',
 'Mean reversion strategy identifying oversold conditions followed by recovery signals',
 ARRAY['rsi14', 'williams_r', 'ema20', 'close_price'],
 ARRAY['rsi6', 'rsi12', 'stoch_k', 'stoch_d', 'volume'],
 '{"rsi_oversold": 30, "rsi_recovery_min": 35, "volume_confirmation": 1.2}',
 'Best used in ranging markets after sharp selloffs',
 'Can catch falling knives - requires confirmation',
 ARRAY['ranging', 'stable'],
 'moderate', 'low', 2),

('BMAC', 'Buy MA Crossover', 'B', 'trend',
 'Classic trend-following strategy based on moving average crossovers',
 ARRAY['ema20', 'ema50', 'macd', 'close_price'],
 ARRAY['ema5', 'ema10', 'ppo', 'adx14', 'volume'],
 '{"ma_separation_min": 0.01, "macd_confirmation": true, "volume_threshold": 1.2}',
 'Best used in trending markets after consolidation breakouts',
 'Can give late signals - prone to whipsaws in ranging markets',
 ARRAY['trending'],
 'simple', 'low', 3),

('BBOL', 'Buy Bollinger Bounce', 'B', 'mean-reversion',
 'Mean reversion strategy focusing on bounces from lower Bollinger Band',
 ARRAY['bb_lower', 'bb_middle', 'close_price', 'rsi14'],
 ARRAY['bb_upper', 'stoch_k', 'williams_r', 'volume'],
 '{"bb_touch_tolerance": 0.002, "rsi_oversold_threshold": 35, "bounce_confirmation": 0.005}',
 'Best used in ranging markets with normal volatility',
 'Bands can expand during volatility - may signal too early',
 ARRAY['ranging', 'stable'],
 'simple', 'low', 4),

('BDIV', 'Buy Bullish Divergence', 'B', 'divergence',
 'Advanced pattern recognition identifying bullish divergences between price and momentum indicators',
 ARRAY['rsi14', 'macd', 'close_price'],
 ARRAY['rsi12', 'ppo', 'stoch_k', 'mfi14'],
 '{"lookback_periods": 5, "divergence_threshold": 0.02, "confirmation_periods": 3}',
 'Best used in established trends showing fatigue',
 'Divergences can continue longer than expected - requires patience',
 ARRAY['ranging', 'volatile'],
 'complex', 'high', 5),

('BSUP', 'Buy Support Bounce', 'B', 'level',
 'Level-based strategy identifying bounces from established support levels',
 ARRAY['close_price', 'low_price', 'volume'],
 ARRAY['sma20', 'sma50', 'rsi14', 'atr14'],
 '{"support_touch_tolerance": 0.01, "bounce_confirmation": 0.005, "volume_threshold": 1.3}',
 'Best used in markets with clear support/resistance structure',
 'Support levels can break - requires strict stops',
 ARRAY['ranging', 'trending'],
 'moderate', 'medium', 6),

-- SELL STRATEGIES  
('SBDN', 'Sell Breakdown', 'S', 'breakout',
 'Bearish breakout strategy identifying breaks below key support levels',
 ARRAY['bb_lower', 'ema20', 'close_price', 'volume'],
 ARRAY['rsi14', 'adx14', 'atr14', 'vr24'],
 '{"breakdown_epsilon": 0.005, "volume_threshold": 1.5, "rsi_min": 15}',
 'Best used in downtrends after distribution with volume confirmation',
 'False breakdowns possible - use volume confirmation',
 ARRAY['trending', 'volatile'],
 'moderate', 'medium', 7),

('SOBR', 'Sell Overbought Reversal', 'S', 'mean-reversion',
 'Mean reversion sell strategy for overbought reversals',
 ARRAY['rsi14', 'close_price', 'ema20'],
 ARRAY['williams_r', 'stoch_k', 'mfi14'],
 '{"rsi_overbought": 70, "rsi_reversal_max": 65, "volume_threshold": 1.2}',
 'Best in ranging markets at resistance with momentum confirmation',
 'Can fight strong uptrends - requires confirmation',
 ARRAY['ranging', 'stable'],
 'moderate', 'low', 8),

('SMAC', 'Sell MA Crossover', 'S', 'trend',
 'Trend-following sell strategy based on bearish MA crossover',
 ARRAY['ema20', 'ema50', 'macd'],
 ARRAY['ppo', 'adx14', 'volume'],
 '{"ma_separation_min": 0.01, "macd_confirmation": true, "volume_threshold": 1.2}',
 'Best in downtrending markets with MACD confirmation',
 'Late signals - whipsaws in ranging markets',
 ARRAY['trending'],
 'simple', 'low', 9),

('SRES', 'Sell Resistance Rejection', 'S', 'level',
 'Resistance level rejection strategy',
 ARRAY['close_price', 'high_price', 'volume'],
 ARRAY['sma20', 'sma50', 'rsi14'],
 '{"resistance_touch_tolerance": 0.01, "rejection_confirmation": 0.005, "volume_threshold": 1.3}',
 'Best at established resistance with volume confirmation',
 'Resistance can break - use stops above resistance',
 ARRAY['ranging', 'trending'],
 'moderate', 'medium', 10),

-- HOLD STRATEGIES REMOVED - No longer supporting hold signals

-- Step 9: Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_trading_signals_strategy_base 
ON trading_signals(strategy_base);

CREATE INDEX IF NOT EXISTS idx_trading_signals_magnitude 
ON trading_signals(signal_magnitude);

CREATE INDEX IF NOT EXISTS idx_trading_signals_txyzn 
ON trading_signals(signal_type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_strategy_catalog_category 
ON strategy_catalog(category);

CREATE INDEX IF NOT EXISTS idx_strategy_catalog_side 
ON strategy_catalog(signal_side);

-- Step 10: Create updated view for signal analysis
CREATE OR REPLACE VIEW signal_analysis_view AS
SELECT 
    ts.id,
    ts.symbol,
    ts.signal_type,
    ts.strategy_base,
    ts.signal_magnitude,
    ts.signal_strength,
    sc.strategy_name,
    sc.category as strategy_category,
    sc.signal_side,
    ts.price,
    ts.volume,
    ts.rsi,
    ts.created_at
FROM trading_signals ts
LEFT JOIN strategy_catalog sc ON ts.strategy_base = sc.strategy_base
ORDER BY ts.created_at DESC;

-- Migration completed successfully
-- Check results:
-- SELECT COUNT(*) as updated_signals FROM trading_signals;
-- SELECT COUNT(*) as base_strategies FROM strategy_catalog;

COMMIT;