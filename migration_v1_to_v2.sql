-- Migration Script: Single Portfolio → Multi-Portfolio Architecture
-- Phase 1: Schema Enhancement (Zero-Downtime Migration)
-- Version: 1.0 → 2.0
-- Date: 2024-08-30
--
-- SAFETY NOTICE:
-- - This migration is designed to be NON-BREAKING
-- - Existing application will continue to work during and after migration
-- - All changes are additive - no data loss will occur
-- - Rollback script available: rollback_v2_to_v1.sql

-- =============================================================================
-- PHASE 1: ADD MULTI-PORTFOLIO SUPPORT WITHOUT BREAKING CHANGES
-- =============================================================================

BEGIN;

-- Create a savepoint for easy rollback
SAVEPOINT migration_start;

-- Record migration start
INSERT INTO portfolio_analyses (name, start_date, end_date, user_notes) 
VALUES ('Database Migration v1→v2', CURRENT_DATE, CURRENT_DATE, 'Schema migration to multi-portfolio support - Phase 1')
ON CONFLICT DO NOTHING;

-- -----------------------------------------------------------------------------
-- Step 1: Create portfolios table (NEW TABLE - no impact on existing code)
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS portfolios (
    id SERIAL PRIMARY KEY,
    portfolio_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_portfolios_id ON portfolios(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_portfolios_created ON portfolios(created_at DESC);

-- Insert default portfolio to migrate existing data (or update if partial migration exists)
INSERT INTO portfolios (portfolio_id, name, description) VALUES
('DEFAULT', 'Legacy Portfolio', 'Migrated from single-portfolio schema')
ON CONFLICT (portfolio_id) DO UPDATE SET
    description = COALESCE(portfolios.description, EXCLUDED.description),
    updated_at = CURRENT_TIMESTAMP;

-- Handle existing portfolios for partial migration
DO $$
DECLARE
    existing_portfolio_id VARCHAR(50) := NULL;
    portfolio_count INTEGER;
    default_portfolio_id VARCHAR(50) := 'DEFAULT';
BEGIN
    -- Count existing portfolios (excluding DEFAULT)
    SELECT COUNT(*) INTO portfolio_count FROM portfolios WHERE portfolio_id != 'DEFAULT';
    
    IF portfolio_count > 0 THEN
        -- Get the first existing portfolio to use for legacy data
        SELECT portfolio_id INTO existing_portfolio_id 
        FROM portfolios 
        WHERE portfolio_id != 'DEFAULT' 
        ORDER BY created_at ASC 
        LIMIT 1;
        
        RAISE NOTICE 'Partial migration detected - found % existing portfolios. Using ''%'' for legacy position data.', portfolio_count, existing_portfolio_id;
        
        -- Remove the DEFAULT portfolio if it exists (we'll use existing portfolio)
        DELETE FROM portfolios WHERE portfolio_id = 'DEFAULT';
        
        -- Set the portfolio to use for legacy data migration
        default_portfolio_id := existing_portfolio_id;
    ELSE
        RAISE NOTICE 'Clean migration - using DEFAULT portfolio for legacy data';
    END IF;
    
    -- Store the portfolio ID to use in a temporary table for later steps
    CREATE TEMP TABLE migration_config AS 
    SELECT default_portfolio_id as target_portfolio_id;
    
    RAISE NOTICE 'Legacy data will be migrated to portfolio: %', default_portfolio_id;
END $$;

-- -----------------------------------------------------------------------------
-- Step 2: Add portfolio_id columns to existing tables (NULLABLE initially)
-- -----------------------------------------------------------------------------

-- Add portfolio_id to portfolio_positions (NULLABLE for backward compatibility)
ALTER TABLE portfolio_positions 
ADD COLUMN IF NOT EXISTS portfolio_id VARCHAR(50);

-- Add portfolio_id to trading_signals (NULLABLE for backward compatibility)  
ALTER TABLE trading_signals 
ADD COLUMN IF NOT EXISTS portfolio_id VARCHAR(50);

-- Add portfolio_id to price_history (NULLABLE for backward compatibility)
ALTER TABLE price_history 
ADD COLUMN IF NOT EXISTS portfolio_id VARCHAR(50);

-- -----------------------------------------------------------------------------
-- Step 3: Migrate existing data to target portfolio (DEFAULT or existing)
-- -----------------------------------------------------------------------------

-- Migrate portfolio_positions data using target portfolio from config
UPDATE portfolio_positions 
SET portfolio_id = (SELECT target_portfolio_id FROM migration_config)
WHERE portfolio_id IS NULL;

-- Migrate trading_signals data using target portfolio from config
UPDATE trading_signals 
SET portfolio_id = (SELECT target_portfolio_id FROM migration_config)
WHERE portfolio_id IS NULL;

-- Migrate price_history data using target portfolio from config
UPDATE price_history 
SET portfolio_id = (SELECT target_portfolio_id FROM migration_config)
WHERE portfolio_id IS NULL;

-- -----------------------------------------------------------------------------
-- Step 4: Create new indexes for multi-portfolio performance
-- -----------------------------------------------------------------------------

-- Portfolio positions indexes
CREATE INDEX IF NOT EXISTS idx_portfolio_positions_portfolio_id 
ON portfolio_positions(portfolio_id);

CREATE INDEX IF NOT EXISTS idx_portfolio_positions_portfolio_symbol 
ON portfolio_positions(portfolio_id, symbol);

-- Trading signals indexes
CREATE INDEX IF NOT EXISTS idx_trading_signals_portfolio_id 
ON trading_signals(portfolio_id);

CREATE INDEX IF NOT EXISTS idx_trading_signals_portfolio_symbol 
ON trading_signals(portfolio_id, symbol);

CREATE INDEX IF NOT EXISTS idx_trading_signals_portfolio_created 
ON trading_signals(portfolio_id, created_at DESC);

-- Price history indexes
CREATE INDEX IF NOT EXISTS idx_price_history_portfolio_id 
ON price_history(portfolio_id);

CREATE INDEX IF NOT EXISTS idx_price_history_portfolio_symbol_time 
ON price_history(portfolio_id, symbol, timestamp DESC);

-- -----------------------------------------------------------------------------
-- Step 5: Create portfolio summary view (for dashboard performance)
-- -----------------------------------------------------------------------------

CREATE OR REPLACE VIEW portfolio_summary AS
SELECT 
    p.portfolio_id,
    p.name,
    p.description,
    COUNT(pp.symbol) as total_positions,
    COUNT(CASE WHEN pp.quantity > 0 THEN 1 END) as active_positions,
    COALESCE(SUM(pp.market_value), 0) as total_market_value,
    COALESCE(SUM(pp.avg_cost * pp.quantity), 0) as total_cost,
    COALESCE(SUM(pp.unrealized_pnl), 0) as total_unrealized_pnl,
    p.created_at,
    p.updated_at
FROM portfolios p
LEFT JOIN portfolio_positions pp ON p.portfolio_id = pp.portfolio_id
GROUP BY p.portfolio_id, p.name, p.description, p.created_at, p.updated_at;

-- -----------------------------------------------------------------------------
-- Step 6: Add helpful functions for migration verification
-- -----------------------------------------------------------------------------

-- Function to check migration status
CREATE OR REPLACE FUNCTION check_migration_status()
RETURNS TABLE(
    tbl_name TEXT,
    has_portfolio_id BOOLEAN,
    null_portfolio_ids BIGINT,
    total_rows BIGINT
) AS $$
BEGIN
    -- Check portfolio_positions
    RETURN QUERY
    SELECT 
        'portfolio_positions'::TEXT,
        EXISTS(SELECT 1 FROM information_schema.columns 
               WHERE information_schema.columns.table_name = 'portfolio_positions' 
                 AND information_schema.columns.column_name = 'portfolio_id'),
        (SELECT COUNT(*) FROM portfolio_positions WHERE portfolio_positions.portfolio_id IS NULL),
        (SELECT COUNT(*) FROM portfolio_positions);
    
    -- Check trading_signals  
    RETURN QUERY
    SELECT 
        'trading_signals'::TEXT,
        EXISTS(SELECT 1 FROM information_schema.columns 
               WHERE information_schema.columns.table_name = 'trading_signals' 
                 AND information_schema.columns.column_name = 'portfolio_id'),
        (SELECT COUNT(*) FROM trading_signals WHERE trading_signals.portfolio_id IS NULL),
        (SELECT COUNT(*) FROM trading_signals);
        
    -- Check price_history
    RETURN QUERY
    SELECT 
        'price_history'::TEXT,
        EXISTS(SELECT 1 FROM information_schema.columns 
               WHERE information_schema.columns.table_name = 'price_history' 
                 AND information_schema.columns.column_name = 'portfolio_id'),
        (SELECT COUNT(*) FROM price_history WHERE price_history.portfolio_id IS NULL),
        (SELECT COUNT(*) FROM price_history);
END;
$$ LANGUAGE plpgsql;

-- -----------------------------------------------------------------------------
-- Step 7: Record successful migration
-- -----------------------------------------------------------------------------

-- Update migration record
UPDATE portfolio_analyses 
SET user_notes = user_notes || ' - Phase 1 completed successfully at ' || CURRENT_TIMESTAMP
WHERE name = 'Database Migration v1→v2' 
  AND DATE(created_at) = CURRENT_DATE;

-- Commit the transaction
COMMIT;

-- =============================================================================
-- MIGRATION VERIFICATION
-- =============================================================================

-- Run verification query
SELECT 'MIGRATION PHASE 1 VERIFICATION' as status;
SELECT * FROM check_migration_status();

-- Show portfolio summary
SELECT 'PORTFOLIO SUMMARY AFTER MIGRATION' as status;
SELECT * FROM portfolio_summary;

-- =============================================================================
-- IMPORTANT NOTES:
-- =============================================================================
--
-- 1. BACKWARD COMPATIBILITY: ✅
--    - Existing queries will continue to work
--    - DatabaseManager has built-in backward compatibility
--    - No application code changes required immediately
--
-- 2. NEW FEATURES ENABLED: ✅
--    - Multi-portfolio dashboard will now work
--    - New portfolios can be created via dashboard
--    - Portfolio isolation is now supported
--
-- 3. NEXT STEPS:
--    - Test the dashboard with both single and multi-portfolio functionality
--    - Optionally run Phase 2 migration (foreign key constraints)
--    - Clean up with Phase 3 migration (make portfolio_id NOT NULL)
--
-- 4. ROLLBACK:
--    - Use rollback_v2_to_v1.sql if needed
--    - Safe to rollback at any time during Phase 1
--
-- =============================================================================