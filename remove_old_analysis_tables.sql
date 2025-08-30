-- Remove Old Portfolio Analysis Tables
-- This script safely removes existing portfolio analysis tables to prepare for the new simplified schema

-- Drop tables in dependency order (child tables first)
DROP TABLE IF EXISTS strategy_signals CASCADE;
DROP TABLE IF EXISTS portfolio_analysis_equity_strategies CASCADE;
DROP TABLE IF EXISTS portfolio_analysis_equities CASCADE;
DROP TABLE IF EXISTS equity_strategy_analyses CASCADE;
DROP TABLE IF EXISTS portfolio_analysis_equity_summary CASCADE;
DROP TABLE IF EXISTS strategy_performance_summary CASCADE;
DROP TABLE IF EXISTS portfolio_analyses CASCADE;

-- Drop any remaining views that might reference these tables
DROP VIEW IF EXISTS portfolio_analysis_summary CASCADE;
DROP VIEW IF EXISTS equity_strategy_performance CASCADE;

-- Note: We keep the core portfolio management tables (portfolios, portfolio_positions, etc.)
-- as they are used by the main dashboard functionality

SELECT 'Old portfolio analysis tables removed successfully' AS status;