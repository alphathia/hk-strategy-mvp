-- Migration Script: Multi-Portfolio Schema Enhancement
-- Phase 2: Foreign Key Constraints and Data Integrity
-- Version: 2.0 → 3.0 (Final)
-- Date: 2024-08-30
--
-- PREREQUISITES:
-- - Phase 1 migration (migration_v1_to_v2.sql) must be completed first
-- - All portfolio_id columns must be populated (no NULL values)
-- - Application should be updated to use multi-portfolio functionality
--
-- SAFETY NOTICE:
-- - This migration adds foreign key constraints for data integrity
-- - Makes portfolio_id columns NOT NULL (no more backward compatibility)
-- - Should only be run after confirming multi-portfolio functionality works
-- - Rollback available but may require data cleanup

-- =============================================================================
-- PRE-MIGRATION VALIDATION
-- =============================================================================

-- Check that Phase 1 migration has been completed
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'portfolios') THEN
        RAISE EXCEPTION 'Phase 1 migration not completed - portfolios table does not exist. Run migration_v1_to_v2.sql first.';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'portfolio_positions' AND column_name = 'portfolio_id') THEN
        RAISE EXCEPTION 'Phase 1 migration not completed - portfolio_id column missing. Run migration_v1_to_v2.sql first.';
    END IF;
END $$;

-- Check for NULL portfolio_id values that would break NOT NULL constraint
DO $$
DECLARE
    null_positions INTEGER;
    null_signals INTEGER;
    null_prices INTEGER;
BEGIN
    SELECT COUNT(*) INTO null_positions FROM portfolio_positions WHERE portfolio_id IS NULL;
    SELECT COUNT(*) INTO null_signals FROM trading_signals WHERE portfolio_id IS NULL;
    SELECT COUNT(*) INTO null_prices FROM price_history WHERE portfolio_id IS NULL;
    
    IF null_positions > 0 OR null_signals > 0 OR null_prices > 0 THEN
        RAISE EXCEPTION 'Cannot proceed - found NULL portfolio_id values: positions=%, signals=%, prices=%. Fix data first.', 
            null_positions, null_signals, null_prices;
    END IF;
    
    RAISE NOTICE 'Pre-migration validation passed - ready for Phase 2';
END $$;

-- =============================================================================
-- PHASE 2: FOREIGN KEY CONSTRAINTS AND FINALIZATION
-- =============================================================================

BEGIN;

-- Create savepoint for rollback safety
SAVEPOINT migration_phase2_start;

-- Record migration start
INSERT INTO portfolio_analyses (name, start_date, end_date, user_notes) 
VALUES ('Database Migration v2→v3', CURRENT_DATE, CURRENT_DATE, 'Adding foreign key constraints and finalizing multi-portfolio schema - Phase 2')
ON CONFLICT DO NOTHING;

-- -----------------------------------------------------------------------------
-- Step 1: Make portfolio_id columns NOT NULL (removes backward compatibility)
-- -----------------------------------------------------------------------------

-- Make portfolio_id NOT NULL in portfolio_positions
ALTER TABLE portfolio_positions ALTER COLUMN portfolio_id SET NOT NULL;
RAISE NOTICE 'Made portfolio_positions.portfolio_id NOT NULL';

-- Make portfolio_id NOT NULL in trading_signals
ALTER TABLE trading_signals ALTER COLUMN portfolio_id SET NOT NULL;
RAISE NOTICE 'Made trading_signals.portfolio_id NOT NULL';

-- Make portfolio_id NOT NULL in price_history
ALTER TABLE price_history ALTER COLUMN portfolio_id SET NOT NULL;
RAISE NOTICE 'Made price_history.portfolio_id NOT NULL';

-- -----------------------------------------------------------------------------
-- Step 2: Update constraints to use composite keys
-- -----------------------------------------------------------------------------

-- Drop old unique constraint on symbol only (if it exists)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'portfolio_positions_symbol_key' 
          AND table_name = 'portfolio_positions'
    ) THEN
        ALTER TABLE portfolio_positions DROP CONSTRAINT portfolio_positions_symbol_key;
        RAISE NOTICE 'Dropped old unique constraint on symbol';
    END IF;
END $$;

-- Add new unique constraint on (portfolio_id, symbol)
ALTER TABLE portfolio_positions 
ADD CONSTRAINT portfolio_positions_portfolio_symbol_key 
UNIQUE (portfolio_id, symbol);
RAISE NOTICE 'Added unique constraint on (portfolio_id, symbol)';

-- -----------------------------------------------------------------------------
-- Step 3: Add proper foreign key constraints
-- -----------------------------------------------------------------------------

-- Add foreign key from portfolio_positions to portfolios
ALTER TABLE portfolio_positions 
ADD CONSTRAINT portfolio_positions_portfolio_fk 
FOREIGN KEY (portfolio_id) REFERENCES portfolios(portfolio_id) ON DELETE CASCADE;
RAISE NOTICE 'Added foreign key constraint from portfolio_positions to portfolios';

-- Add foreign key from trading_signals to portfolio_positions
ALTER TABLE trading_signals 
ADD CONSTRAINT trading_signals_portfolio_position_fk 
FOREIGN KEY (portfolio_id, symbol) REFERENCES portfolio_positions(portfolio_id, symbol) ON DELETE CASCADE;
RAISE NOTICE 'Added foreign key constraint from trading_signals to portfolio_positions';

-- Add foreign key from price_history to portfolio_positions
ALTER TABLE price_history 
ADD CONSTRAINT price_history_portfolio_position_fk 
FOREIGN KEY (portfolio_id, symbol) REFERENCES portfolio_positions(portfolio_id, symbol) ON DELETE CASCADE;
RAISE NOTICE 'Added foreign key constraint from price_history to portfolio_positions';

-- -----------------------------------------------------------------------------
-- Step 4: Add updated_at trigger for portfolios table
-- -----------------------------------------------------------------------------

-- Create trigger function for updating updated_at timestamp
CREATE OR REPLACE FUNCTION update_portfolio_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
DROP TRIGGER IF EXISTS portfolio_updated_at_trigger ON portfolios;
CREATE TRIGGER portfolio_updated_at_trigger
    BEFORE UPDATE ON portfolios
    FOR EACH ROW
    EXECUTE FUNCTION update_portfolio_timestamp();

RAISE NOTICE 'Added updated_at trigger for portfolios table';

-- -----------------------------------------------------------------------------
-- Step 5: Enhanced portfolio analysis tables for multi-portfolio
-- -----------------------------------------------------------------------------

-- Add portfolio_id to portfolio_analyses if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'portfolio_analyses' AND column_name = 'portfolio_id') THEN
        ALTER TABLE portfolio_analyses ADD COLUMN portfolio_id VARCHAR(50);
        
        -- Set default portfolio for existing analyses
        UPDATE portfolio_analyses SET portfolio_id = 'DEFAULT' WHERE portfolio_id IS NULL;
        
        -- Add foreign key constraint
        ALTER TABLE portfolio_analyses ALTER COLUMN portfolio_id SET NOT NULL;
        ALTER TABLE portfolio_analyses 
        ADD CONSTRAINT portfolio_analyses_portfolio_fk 
        FOREIGN KEY (portfolio_id) REFERENCES portfolios(portfolio_id) ON DELETE CASCADE;
        
        RAISE NOTICE 'Added portfolio_id to portfolio_analyses with foreign key';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Step 6: Create enhanced views and functions
-- -----------------------------------------------------------------------------

-- Enhanced portfolio performance view
CREATE OR REPLACE VIEW portfolio_performance AS
SELECT 
    p.portfolio_id,
    p.name,
    p.description,
    COUNT(pp.symbol) as total_positions,
    COUNT(CASE WHEN pp.quantity > 0 THEN 1 END) as active_positions,
    COALESCE(SUM(pp.market_value), 0) as total_market_value,
    COALESCE(SUM(pp.avg_cost * pp.quantity), 0) as total_cost,
    COALESCE(SUM(pp.unrealized_pnl), 0) as total_unrealized_pnl,
    CASE 
        WHEN SUM(pp.avg_cost * pp.quantity) > 0 THEN 
            SUM(pp.unrealized_pnl) / SUM(pp.avg_cost * pp.quantity) * 100
        ELSE 0 
    END as return_percentage,
    COUNT(DISTINCT pp.sector) as sector_count,
    -- Recent activity
    (SELECT COUNT(*) FROM trading_signals ts WHERE ts.portfolio_id = p.portfolio_id AND ts.created_at > CURRENT_DATE - INTERVAL '7 days') as signals_last_7_days,
    p.created_at,
    p.updated_at
FROM portfolios p
LEFT JOIN portfolio_positions pp ON p.portfolio_id = pp.portfolio_id
GROUP BY p.portfolio_id, p.name, p.description, p.created_at, p.updated_at;

RAISE NOTICE 'Created enhanced portfolio_performance view';

-- Function to validate portfolio data integrity
CREATE OR REPLACE FUNCTION validate_portfolio_integrity(check_portfolio_id VARCHAR(50) DEFAULT NULL)
RETURNS TABLE(
    portfolio_id VARCHAR(50),
    issue_type TEXT,
    issue_count BIGINT,
    issue_details TEXT
) AS $$
BEGIN
    -- Check for orphaned trading signals
    RETURN QUERY
    SELECT 
        COALESCE(ts.portfolio_id, 'UNKNOWN') as portfolio_id,
        'Orphaned Trading Signals' as issue_type,
        COUNT(*) as issue_count,
        'Trading signals without matching portfolio positions' as issue_details
    FROM trading_signals ts
    LEFT JOIN portfolio_positions pp ON ts.portfolio_id = pp.portfolio_id AND ts.symbol = pp.symbol
    WHERE pp.symbol IS NULL
      AND (check_portfolio_id IS NULL OR ts.portfolio_id = check_portfolio_id)
    GROUP BY ts.portfolio_id
    HAVING COUNT(*) > 0;
    
    -- Check for orphaned price history
    RETURN QUERY
    SELECT 
        COALESCE(ph.portfolio_id, 'UNKNOWN') as portfolio_id,
        'Orphaned Price History' as issue_type,
        COUNT(*) as issue_count,
        'Price history without matching portfolio positions' as issue_details
    FROM price_history ph
    LEFT JOIN portfolio_positions pp ON ph.portfolio_id = pp.portfolio_id AND ph.symbol = pp.symbol
    WHERE pp.symbol IS NULL
      AND (check_portfolio_id IS NULL OR ph.portfolio_id = check_portfolio_id)
    GROUP BY ph.portfolio_id
    HAVING COUNT(*) > 0;
    
    -- Check for empty portfolios
    RETURN QUERY
    SELECT 
        p.portfolio_id,
        'Empty Portfolio' as issue_type,
        0 as issue_count,
        'Portfolio has no positions' as issue_details
    FROM portfolios p
    LEFT JOIN portfolio_positions pp ON p.portfolio_id = pp.portfolio_id
    WHERE pp.portfolio_id IS NULL
      AND (check_portfolio_id IS NULL OR p.portfolio_id = check_portfolio_id);
END;
$$ LANGUAGE plpgsql;

RAISE NOTICE 'Created portfolio integrity validation function';

-- -----------------------------------------------------------------------------
-- Step 7: Update indexes for optimal performance
-- -----------------------------------------------------------------------------

-- Drop temporary indexes from Phase 1 and create optimized ones
DROP INDEX IF EXISTS idx_portfolio_positions_portfolio_id;
DROP INDEX IF EXISTS idx_trading_signals_portfolio_id; 
DROP INDEX IF EXISTS idx_price_history_portfolio_id;

-- Create composite indexes for foreign key performance
CREATE INDEX IF NOT EXISTS idx_portfolio_positions_portfolio_symbol_optimized 
ON portfolio_positions(portfolio_id, symbol, quantity) WHERE quantity > 0;

CREATE INDEX IF NOT EXISTS idx_trading_signals_portfolio_symbol_time 
ON trading_signals(portfolio_id, symbol, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_price_history_portfolio_symbol_timestamp 
ON price_history(portfolio_id, symbol, timestamp DESC);

-- Index for portfolio analyses
CREATE INDEX IF NOT EXISTS idx_portfolio_analyses_portfolio_dates 
ON portfolio_analyses(portfolio_id, start_date, end_date);

RAISE NOTICE 'Created optimized indexes for multi-portfolio operations';

-- -----------------------------------------------------------------------------
-- Step 8: Data validation and cleanup
-- -----------------------------------------------------------------------------

-- Run integrity validation
DO $$
DECLARE
    integrity_issues INTEGER;
BEGIN
    SELECT COUNT(*) INTO integrity_issues FROM validate_portfolio_integrity();
    
    IF integrity_issues > 0 THEN
        RAISE NOTICE 'Found % data integrity issues - check validate_portfolio_integrity() output', integrity_issues;
        -- Don't fail the migration, but log the issues
        FOR rec IN SELECT * FROM validate_portfolio_integrity() LOOP
            RAISE NOTICE 'Integrity Issue - Portfolio: %, Type: %, Count: %, Details: %', 
                rec.portfolio_id, rec.issue_type, rec.issue_count, rec.issue_details;
        END LOOP;
    ELSE
        RAISE NOTICE 'No data integrity issues found';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Step 9: Record successful migration
-- -----------------------------------------------------------------------------

-- Update migration record
UPDATE portfolio_analyses 
SET user_notes = user_notes || ' - Phase 2 completed successfully at ' || CURRENT_TIMESTAMP
WHERE name = 'Database Migration v2→v3' 
  AND DATE(created_at) = CURRENT_DATE;

-- Commit the transaction
COMMIT;

-- =============================================================================
-- MIGRATION VERIFICATION
-- =============================================================================

SELECT 'MIGRATION PHASE 2 VERIFICATION' as status;

-- Verify foreign key constraints
SELECT 
    'Foreign Key Constraints' as check_type,
    COUNT(*) as constraint_count
FROM information_schema.table_constraints 
WHERE constraint_type = 'FOREIGN KEY' 
  AND table_name IN ('portfolio_positions', 'trading_signals', 'price_history', 'portfolio_analyses');

-- Verify NOT NULL constraints
SELECT 
    'NOT NULL Constraints' as check_type,
    table_name,
    column_name,
    is_nullable
FROM information_schema.columns 
WHERE table_name IN ('portfolio_positions', 'trading_signals', 'price_history')
  AND column_name = 'portfolio_id';

-- Show enhanced portfolio performance
SELECT 'ENHANCED PORTFOLIO PERFORMANCE' as status;
SELECT * FROM portfolio_performance;

-- Run final integrity check
SELECT 'DATA INTEGRITY CHECK' as status;
SELECT * FROM validate_portfolio_integrity();

-- =============================================================================
-- MIGRATION PHASE 2 COMPLETE
-- =============================================================================

SELECT '✅ PHASE 2 MIGRATION COMPLETED SUCCESSFULLY' as status;
SELECT 'Multi-portfolio schema with full referential integrity' as result;
SELECT 'Foreign key constraints ensure data consistency' as benefit;
SELECT 'Enhanced views and functions for better performance' as enhancement;
SELECT 'Schema is now production-ready for multi-portfolio operations' as conclusion;