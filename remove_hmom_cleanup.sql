-- HMOM Cleanup Script
-- Removes all HMOM references from database
-- Run this script to clean up unused HMOM (Hold Momentum) signals

BEGIN;

-- Step 1: Remove HMOM signals from trading_signals table
DELETE FROM trading_signals 
WHERE signal_type LIKE 'HMOM%' OR strategy_base = 'HMOM';

-- Step 2: Remove HMOM from strategy_catalog if it exists
DELETE FROM strategy_catalog 
WHERE strategy_base = 'HMOM';

-- Step 3: Update any remaining C signals to NULL instead of HMOM5
-- (C signals were mapped to HMOM5 in the migration but HMOM is being removed)
UPDATE trading_signals 
SET 
    signal_type = NULL,
    strategy_base = NULL,
    signal_magnitude = NULL
WHERE signal_type = 'HMOM5';

-- Step 4: Remove HMOM-related constraints if they exist
ALTER TABLE trading_signals 
DROP CONSTRAINT IF EXISTS trading_signals_hmom_check;

-- Step 5: Update any views that might reference HMOM
DROP VIEW IF EXISTS signal_analysis_view;
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
WHERE ts.signal_type IS NOT NULL 
    AND ts.strategy_base IS NOT NULL
    AND ts.strategy_base != 'HMOM'
ORDER BY ts.created_at DESC;

-- Verification queries
SELECT 'HMOM cleanup completed' AS status;
SELECT COUNT(*) as remaining_hmom_signals 
FROM trading_signals 
WHERE signal_type LIKE 'HMOM%' OR strategy_base = 'HMOM';

COMMIT;