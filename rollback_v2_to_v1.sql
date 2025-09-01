-- Rollback Script: Multi-Portfolio → Single Portfolio Architecture  
-- Phase 1 Rollback: Remove Multi-Portfolio Schema Enhancements
-- Version: 2.0 → 1.0
-- Date: 2024-08-30
--
-- SAFETY NOTICE:
-- - This rollback will remove multi-portfolio capabilities
-- - All portfolio data will be merged back into single portfolio
-- - NO DATA LOSS - all position and signal data is preserved
-- - Existing single-portfolio application will work normally

-- =============================================================================
-- ROLLBACK VERIFICATION AND SAFETY CHECKS
-- =============================================================================

-- Check if migration has been applied
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'portfolios') THEN
        RAISE NOTICE 'Migration has not been applied - no rollback needed';
        RAISE EXCEPTION 'No migration to rollback';
    END IF;
END $$;

-- =============================================================================
-- PHASE 1 ROLLBACK: REMOVE MULTI-PORTFOLIO SCHEMA ENHANCEMENTS
-- =============================================================================

BEGIN;

-- Create savepoint for rollback safety
SAVEPOINT rollback_start;

-- Record rollback start
INSERT INTO portfolio_analyses (name, start_date, end_date, user_notes) 
VALUES ('Database Rollback v2→v1', CURRENT_DATE, CURRENT_DATE, 'Rolling back multi-portfolio schema to single portfolio - Phase 1')
ON CONFLICT DO NOTHING;

-- -----------------------------------------------------------------------------
-- Step 1: Verify data safety before rollback
-- -----------------------------------------------------------------------------

-- Check for multiple portfolios (warn if data will be merged)
DO $$
DECLARE
    portfolio_count INTEGER;
BEGIN
    SELECT COUNT(DISTINCT portfolio_id) INTO portfolio_count FROM portfolio_positions WHERE portfolio_id IS NOT NULL;
    
    IF portfolio_count > 1 THEN
        RAISE NOTICE 'WARNING: Multiple portfolios detected (%). Data will be merged into single portfolio.', portfolio_count;
        RAISE NOTICE 'Portfolios found:';
        FOR rec IN SELECT DISTINCT portfolio_id, COUNT(*) as positions FROM portfolio_positions GROUP BY portfolio_id LOOP
            RAISE NOTICE '  - %: % positions', rec.portfolio_id, rec.positions;
        END LOOP;
    ELSE
        RAISE NOTICE 'Single portfolio detected - safe to rollback';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Step 2: Handle data conflicts before removing portfolio_id columns
-- -----------------------------------------------------------------------------

-- Check for symbol conflicts across portfolios
CREATE TEMPORARY TABLE symbol_conflicts AS
SELECT symbol, COUNT(DISTINCT portfolio_id) as portfolio_count, 
       array_agg(DISTINCT portfolio_id) as portfolios
FROM portfolio_positions 
WHERE portfolio_id IS NOT NULL
GROUP BY symbol 
HAVING COUNT(DISTINCT portfolio_id) > 1;

-- Report conflicts
DO $$
DECLARE
    conflict_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO conflict_count FROM symbol_conflicts;
    
    IF conflict_count > 0 THEN
        RAISE NOTICE 'WARNING: % symbols exist in multiple portfolios and will be merged:', conflict_count;
        FOR rec IN SELECT * FROM symbol_conflicts LOOP
            RAISE NOTICE '  - %: exists in portfolios %', rec.symbol, rec.portfolios;
        END LOOP;
        
        -- Merge strategy: Sum quantities, average costs weighted by quantity
        WITH merged_positions AS (
            SELECT 
                symbol,
                company_name,
                sector,
                SUM(quantity) as total_quantity,
                CASE 
                    WHEN SUM(quantity) > 0 THEN 
                        SUM(avg_cost * quantity) / SUM(quantity)
                    ELSE 0
                END as weighted_avg_cost,
                AVG(current_price) as avg_current_price,
                MAX(last_updated) as latest_update
            FROM portfolio_positions pp
            WHERE symbol IN (SELECT symbol FROM symbol_conflicts)
            GROUP BY symbol, company_name, sector
        )
        -- Update the first occurrence of each symbol
        UPDATE portfolio_positions 
        SET 
            quantity = mp.total_quantity,
            avg_cost = mp.weighted_avg_cost,
            current_price = mp.avg_current_price,
            last_updated = mp.latest_update
        FROM merged_positions mp
        WHERE portfolio_positions.symbol = mp.symbol
          AND portfolio_positions.id = (
              SELECT MIN(id) FROM portfolio_positions pp2 
              WHERE pp2.symbol = mp.symbol
          );
          
        -- Remove duplicate entries
        DELETE FROM portfolio_positions 
        WHERE symbol IN (SELECT symbol FROM symbol_conflicts)
          AND id NOT IN (
              SELECT MIN(id) FROM portfolio_positions pp3
              WHERE pp3.symbol IN (SELECT symbol FROM symbol_conflicts)
              GROUP BY symbol
          );
          
        RAISE NOTICE 'Merged % conflicting symbols', conflict_count;
    ELSE
        RAISE NOTICE 'No symbol conflicts found - safe to proceed';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Step 3: Remove portfolio_id columns (reverting to original schema)
-- -----------------------------------------------------------------------------

-- Remove portfolio_id from portfolio_positions
ALTER TABLE portfolio_positions DROP COLUMN IF EXISTS portfolio_id;

-- Remove portfolio_id from trading_signals  
ALTER TABLE trading_signals DROP COLUMN IF EXISTS portfolio_id;

-- Remove portfolio_id from price_history
ALTER TABLE price_history DROP COLUMN IF EXISTS portfolio_id;

-- -----------------------------------------------------------------------------
-- Step 4: Drop multi-portfolio specific objects
-- -----------------------------------------------------------------------------

-- Drop portfolio summary view
DROP VIEW IF EXISTS portfolio_summary;

-- Drop multi-portfolio indexes
DROP INDEX IF EXISTS idx_portfolio_positions_portfolio_id;
DROP INDEX IF EXISTS idx_portfolio_positions_portfolio_symbol;
DROP INDEX IF EXISTS idx_trading_signals_portfolio_id;
DROP INDEX IF EXISTS idx_trading_signals_portfolio_symbol;
DROP INDEX IF EXISTS idx_trading_signals_portfolio_created;
DROP INDEX IF EXISTS idx_price_history_portfolio_id;
DROP INDEX IF EXISTS idx_price_history_portfolio_symbol_time;
DROP INDEX IF EXISTS idx_portfolios_id;
DROP INDEX IF EXISTS idx_portfolios_created;

-- Drop helper functions
DROP FUNCTION IF EXISTS check_migration_status();

-- Drop portfolios table (this removes multi-portfolio capability)
DROP TABLE IF EXISTS portfolios;

-- -----------------------------------------------------------------------------
-- Step 5: Restore original constraints and indexes
-- -----------------------------------------------------------------------------

-- Restore original unique constraint on symbol (single portfolio assumption)
-- First check if constraint already exists
DO $$
BEGIN
    -- Try to add unique constraint if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'portfolio_positions_symbol_key' 
          AND table_name = 'portfolio_positions'
    ) THEN
        ALTER TABLE portfolio_positions ADD CONSTRAINT portfolio_positions_symbol_key UNIQUE (symbol);
        RAISE NOTICE 'Restored unique constraint on portfolio_positions.symbol';
    ELSE
        RAISE NOTICE 'Unique constraint on symbol already exists';
    END IF;
EXCEPTION 
    WHEN unique_violation THEN
        RAISE NOTICE 'Cannot restore unique constraint - duplicate symbols still exist after merge';
        RAISE NOTICE 'Manual cleanup may be required';
END $$;

-- Restore original indexes
CREATE INDEX IF NOT EXISTS idx_portfolio_symbol ON portfolio_positions(symbol);
CREATE INDEX IF NOT EXISTS idx_signals_symbol ON trading_signals(symbol);
CREATE INDEX IF NOT EXISTS idx_signals_created ON trading_signals(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_price_symbol_time ON price_history(symbol, timestamp DESC);

-- -----------------------------------------------------------------------------
-- Step 6: Record successful rollback
-- -----------------------------------------------------------------------------

-- Update rollback record
UPDATE portfolio_analyses 
SET user_notes = user_notes || ' - Phase 1 rollback completed successfully at ' || CURRENT_TIMESTAMP
WHERE name = 'Database Rollback v2→v1' 
  AND DATE(created_at) = CURRENT_DATE;

-- Commit the rollback
COMMIT;

-- =============================================================================
-- ROLLBACK VERIFICATION
-- =============================================================================

-- Verify rollback success
SELECT 'ROLLBACK VERIFICATION' as status;

-- Check that multi-portfolio objects are gone
SELECT 
    CASE 
        WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'portfolios') 
        THEN '❌ portfolios table still exists'
        ELSE '✅ portfolios table removed'
    END as portfolios_table,
    
    CASE 
        WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'portfolio_positions' AND column_name = 'portfolio_id')
        THEN '❌ portfolio_id column still exists in portfolio_positions'
        ELSE '✅ portfolio_id column removed from portfolio_positions'
    END as portfolio_positions_column,
    
    CASE
        WHEN EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = 'portfolio_positions_symbol_key')
        THEN '✅ unique constraint on symbol restored'
        ELSE '⚠️ unique constraint on symbol missing'
    END as unique_constraint;

-- Show final data counts
SELECT 
    (SELECT COUNT(*) FROM portfolio_positions) as total_positions,
    (SELECT COUNT(*) FROM trading_signals) as total_signals,
    (SELECT COUNT(*) FROM price_history) as total_price_records;

-- =============================================================================
-- ROLLBACK COMPLETE
-- =============================================================================

SELECT '✅ ROLLBACK COMPLETED SUCCESSFULLY' as status;
SELECT 'Database has been reverted to single-portfolio schema' as message;
SELECT 'All multi-portfolio data has been merged into single portfolio' as data_status;
SELECT 'Original application functionality restored' as compatibility;