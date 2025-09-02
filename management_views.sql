-- Strategic Signal System: Management Views
-- Creates optimized views for dashboard queries and system monitoring

-- =============================================================================
-- STRATEGY MANAGEMENT VIEWS
-- =============================================================================

-- Comprehensive strategy overview with statistics
CREATE OR REPLACE VIEW v_strategy_overview AS
SELECT 
    s.strategy_key,
    s.base_strategy,
    s.side,
    s.strength,
    s.name,
    s.description,
    s.category,
    COALESCE(stats.signal_count, 0) as total_signals,
    COALESCE(stats.avg_confidence, 0) as avg_confidence,
    stats.last_signal_date,
    stats.first_signal_date,
    CASE 
        WHEN stats.signal_count > 0 THEN 'ACTIVE'
        ELSE 'INACTIVE'
    END as status,
    COALESCE(stats.unique_symbols, 0) as symbols_covered
FROM strategy s
LEFT JOIN (
    SELECT 
        signal,
        COUNT(*) as signal_count,
        AVG(confidence) as avg_confidence,
        MAX(timestamp) as last_signal_date,
        MIN(timestamp) as first_signal_date,
        COUNT(DISTINCT symbol) as unique_symbols
    FROM signal_event
    GROUP BY signal
) stats ON s.strategy_key = stats.signal;

-- Strategy performance metrics
CREATE OR REPLACE VIEW v_strategy_performance AS
SELECT 
    s.strategy_key,
    s.name,
    s.category,
    s.side,
    COUNT(se.id) as total_signals,
    AVG(se.confidence) as avg_confidence,
    STDDEV(se.confidence) as confidence_stddev,
    COUNT(DISTINCT se.symbol) as symbols_count,
    COUNT(DISTINCT DATE(se.timestamp)) as active_days,
    MIN(se.timestamp) as first_signal,
    MAX(se.timestamp) as last_signal,
    -- Strength distribution
    COUNT(CASE WHEN se.strength BETWEEN 1 AND 3 THEN 1 END) as weak_signals,
    COUNT(CASE WHEN se.strength BETWEEN 4 AND 6 THEN 1 END) as medium_signals,
    COUNT(CASE WHEN se.strength BETWEEN 7 AND 9 THEN 1 END) as strong_signals,
    -- Recent activity (last 30 days)
    COUNT(CASE WHEN se.timestamp >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as recent_signals
FROM strategy s
LEFT JOIN signal_event se ON s.strategy_key = se.signal
GROUP BY s.strategy_key, s.name, s.category, s.side;

-- Base strategy summary (aggregated by strategy family)
CREATE OR REPLACE VIEW v_base_strategy_summary AS
SELECT 
    base_strategy,
    side,
    category,
    COUNT(*) as variant_count,
    MIN(strength) as min_strength,
    MAX(strength) as max_strength,
    COALESCE(SUM(perf.total_signals), 0) as total_signals,
    COALESCE(AVG(perf.avg_confidence), 0) as avg_confidence,
    COALESCE(SUM(perf.symbols_count), 0) as total_symbols_covered
FROM strategy s
LEFT JOIN v_strategy_performance perf ON s.strategy_key = perf.strategy_key
GROUP BY base_strategy, side, category;

-- =============================================================================
-- SIGNAL EVENT VIEWS
-- =============================================================================

-- Recent signals with enriched data
CREATE OR REPLACE VIEW v_recent_signals AS
SELECT 
    se.id,
    se.symbol,
    se.signal,
    s.name as strategy_name,
    s.category,
    s.side,
    se.strength,
    se.confidence,
    se.timestamp,
    se.evidence->'score' as evidence_score,
    jsonb_array_length(se.evidence->'reasons') as reason_count,
    se.run_id,
    sr.status as run_status,
    sr.symbol_count as run_symbol_count,
    -- Time since signal
    EXTRACT(EPOCH FROM (NOW() - se.timestamp))/3600 as hours_ago,
    -- Rank within symbol (most recent first)
    ROW_NUMBER() OVER (PARTITION BY se.symbol ORDER BY se.timestamp DESC) as symbol_rank
FROM signal_event se
JOIN strategy s ON se.signal = s.strategy_key
LEFT JOIN signal_run sr ON se.run_id = sr.run_id
WHERE se.timestamp >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY se.timestamp DESC;

-- Signal frequency analysis
CREATE OR REPLACE VIEW v_signal_frequency AS
SELECT 
    symbol,
    signal,
    s.name as strategy_name,
    s.category,
    COUNT(*) as signal_count,
    AVG(confidence) as avg_confidence,
    MIN(timestamp) as first_signal,
    MAX(timestamp) as last_signal,
    -- Calculate average days between signals
    CASE 
        WHEN COUNT(*) > 1 THEN 
            EXTRACT(DAYS FROM (MAX(timestamp) - MIN(timestamp))) / (COUNT(*) - 1)
        ELSE NULL 
    END as avg_days_between_signals,
    -- Recent activity
    COUNT(CASE WHEN timestamp >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as recent_count
FROM signal_event se
JOIN strategy s ON se.signal = s.strategy_key
GROUP BY symbol, signal, s.name, s.category
HAVING COUNT(*) >= 2;

-- High confidence signals (top 10%)
CREATE OR REPLACE VIEW v_high_confidence_signals AS
SELECT 
    se.*,
    s.name as strategy_name,
    s.category,
    PERCENT_RANK() OVER (ORDER BY se.confidence) as confidence_percentile
FROM signal_event se
JOIN strategy s ON se.signal = s.strategy_key
WHERE se.confidence >= (
    SELECT PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY confidence) 
    FROM signal_event
);

-- =============================================================================
-- SYMBOL AND INDICATOR VIEWS
-- =============================================================================

-- Symbol coverage and activity
CREATE OR REPLACE VIEW v_symbol_coverage AS
SELECT 
    symbol,
    COUNT(DISTINCT signal) as strategy_count,
    COUNT(*) as total_signals,
    AVG(confidence) as avg_confidence,
    MIN(timestamp) as first_signal,
    MAX(timestamp) as last_signal,
    -- Activity metrics
    COUNT(CASE WHEN timestamp >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as signals_7d,
    COUNT(CASE WHEN timestamp >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as signals_30d,
    COUNT(CASE WHEN timestamp >= CURRENT_DATE - INTERVAL '90 days' THEN 1 END) as signals_90d,
    -- Strategy distribution
    COUNT(DISTINCT CASE WHEN s.side = 'B' THEN signal END) as buy_strategies,
    COUNT(DISTINCT CASE WHEN s.side = 'S' THEN signal END) as sell_strategies,
    COUNT(DISTINCT s.category) as categories_covered
FROM signal_event se
JOIN strategy s ON se.signal = s.strategy_key
GROUP BY symbol;

-- Indicator availability and freshness
CREATE OR REPLACE VIEW v_indicator_status AS
SELECT 
    indicator_name,
    COUNT(DISTINCT symbol) as symbol_count,
    COUNT(*) as total_snapshots,
    MIN(timestamp) as oldest_snapshot,
    MAX(timestamp) as newest_snapshot,
    -- Freshness check (indicators updated in last 24 hours)
    COUNT(CASE WHEN timestamp >= CURRENT_TIMESTAMP - INTERVAL '24 hours' THEN 1 END) as fresh_count,
    COUNT(CASE WHEN timestamp >= CURRENT_TIMESTAMP - INTERVAL '7 days' THEN 1 END) as recent_count,
    -- Calculate average update frequency per symbol
    CASE 
        WHEN COUNT(*) > 0 THEN
            COUNT(*)::DECIMAL / COUNT(DISTINCT symbol)
        ELSE 0 
    END as avg_snapshots_per_symbol
FROM indicator_snapshot
GROUP BY indicator_name;

-- Symbol-indicator matrix (what indicators are available for each symbol)
CREATE OR REPLACE VIEW v_symbol_indicator_matrix AS
SELECT 
    symbol,
    indicator_name,
    COUNT(*) as snapshot_count,
    MIN(timestamp) as first_snapshot,
    MAX(timestamp) as last_snapshot,
    -- Data quality indicators
    COUNT(CASE WHEN value IS NOT NULL THEN 1 END) as valid_values,
    COUNT(CASE WHEN value IS NULL THEN 1 END) as null_values,
    -- Recent data availability
    COUNT(CASE WHEN timestamp >= CURRENT_TIMESTAMP - INTERVAL '24 hours' THEN 1 END) as last_24h,
    COUNT(CASE WHEN timestamp >= CURRENT_TIMESTAMP - INTERVAL '7 days' THEN 1 END) as last_7d
FROM indicator_snapshot
GROUP BY symbol, indicator_name;

-- =============================================================================
-- SYSTEM MONITORING VIEWS
-- =============================================================================

-- Signal run monitoring
CREATE OR REPLACE VIEW v_signal_run_monitor AS
SELECT 
    sr.run_id,
    sr.start_time,
    sr.end_time,
    sr.status,
    sr.symbol_count,
    sr.parameter_set_id,
    ps.parameters,
    -- Execution metrics
    EXTRACT(EPOCH FROM (sr.end_time - sr.start_time)) as duration_seconds,
    COUNT(se.id) as signals_generated,
    COUNT(DISTINCT se.symbol) as symbols_with_signals,
    AVG(se.confidence) as avg_signal_confidence,
    -- Success rate
    CASE 
        WHEN sr.symbol_count > 0 THEN
            (COUNT(DISTINCT se.symbol)::DECIMAL / sr.symbol_count) * 100
        ELSE 0
    END as symbol_success_rate
FROM signal_run sr
LEFT JOIN parameter_set ps ON sr.parameter_set_id = ps.id
LEFT JOIN signal_event se ON sr.run_id = se.run_id
GROUP BY sr.run_id, sr.start_time, sr.end_time, sr.status, sr.symbol_count, sr.parameter_set_id, ps.parameters;

-- Data quality dashboard
CREATE OR REPLACE VIEW v_data_quality_dashboard AS
SELECT 
    'Signal Events' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN confidence < 0.5 THEN 1 END) as low_quality_count,
    COUNT(CASE WHEN evidence IS NULL OR evidence = 'null'::jsonb THEN 1 END) as missing_evidence,
    MIN(timestamp) as oldest_record,
    MAX(timestamp) as newest_record
FROM signal_event
UNION ALL
SELECT 
    'Indicator Snapshots' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN value IS NULL THEN 1 END) as low_quality_count,
    COUNT(CASE WHEN metadata IS NULL OR metadata = 'null'::jsonb THEN 1 END) as missing_evidence,
    MIN(timestamp) as oldest_record,
    MAX(timestamp) as newest_record
FROM indicator_snapshot
UNION ALL
SELECT 
    'Signal Runs' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as low_quality_count,
    COUNT(CASE WHEN end_time IS NULL THEN 1 END) as missing_evidence,
    MIN(start_time) as oldest_record,
    MAX(start_time) as newest_record
FROM signal_run;

-- System performance metrics
CREATE OR REPLACE VIEW v_system_performance AS
SELECT 
    DATE(timestamp) as date,
    COUNT(*) as daily_signals,
    COUNT(DISTINCT symbol) as symbols_active,
    COUNT(DISTINCT signal) as strategies_active,
    AVG(confidence) as avg_confidence,
    -- Performance tiers
    COUNT(CASE WHEN strength BETWEEN 1 AND 3 THEN 1 END) as weak_signals,
    COUNT(CASE WHEN strength BETWEEN 4 AND 6 THEN 1 END) as medium_signals,
    COUNT(CASE WHEN strength BETWEEN 7 AND 9 THEN 1 END) as strong_signals,
    -- Side distribution
    COUNT(CASE WHEN LEFT(signal, 1) = 'B' THEN 1 END) as buy_signals,
    COUNT(CASE WHEN LEFT(signal, 1) = 'S' THEN 1 END) as sell_signals
FROM signal_event
WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(timestamp)
ORDER BY date DESC;

-- =============================================================================
-- DASHBOARD SUMMARY VIEWS
-- =============================================================================

-- Executive dashboard - key metrics
CREATE OR REPLACE VIEW v_executive_dashboard AS
SELECT 
    -- Strategy metrics
    (SELECT COUNT(*) FROM strategy) as total_strategies,
    (SELECT COUNT(*) FROM strategy WHERE strategy_key IN (
        SELECT DISTINCT signal FROM signal_event WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
    )) as active_strategies,
    
    -- Signal metrics
    (SELECT COUNT(*) FROM signal_event) as total_signals,
    (SELECT COUNT(*) FROM signal_event WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days') as signals_30d,
    (SELECT COUNT(*) FROM signal_event WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days') as signals_7d,
    (SELECT COUNT(*) FROM signal_event WHERE timestamp >= CURRENT_DATE - INTERVAL '1 day') as signals_24h,
    
    -- Coverage metrics
    (SELECT COUNT(DISTINCT symbol) FROM signal_event) as symbols_with_signals,
    (SELECT COUNT(DISTINCT symbol) FROM signal_event WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days') as active_symbols_7d,
    
    -- Quality metrics
    (SELECT AVG(confidence) FROM signal_event WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days') as avg_confidence_30d,
    (SELECT COUNT(*) FROM signal_event WHERE confidence >= 0.8 AND timestamp >= CURRENT_DATE - INTERVAL '7 days') as high_conf_signals_7d,
    
    -- System health
    (SELECT COUNT(*) FROM signal_run WHERE status = 'completed' AND start_time >= CURRENT_DATE - INTERVAL '7 days') as successful_runs_7d,
    (SELECT COUNT(*) FROM signal_run WHERE status = 'failed' AND start_time >= CURRENT_DATE - INTERVAL '7 days') as failed_runs_7d;

-- Strategy explorer - for strategy selection interface
CREATE OR REPLACE VIEW v_strategy_explorer AS
SELECT 
    s.strategy_key,
    s.base_strategy,
    s.side,
    s.strength,
    s.name,
    s.category,
    s.description,
    -- Usage statistics
    COALESCE(COUNT(se.id), 0) as usage_count,
    COALESCE(AVG(se.confidence), 0) as avg_confidence,
    COUNT(DISTINCT se.symbol) as symbols_used,
    MAX(se.timestamp) as last_used,
    -- Performance indicators
    CASE 
        WHEN COUNT(se.id) = 0 THEN 'UNUSED'
        WHEN MAX(se.timestamp) < CURRENT_DATE - INTERVAL '30 days' THEN 'DORMANT'
        WHEN AVG(se.confidence) >= 0.7 THEN 'HIGH_PERFORMANCE'
        WHEN AVG(se.confidence) >= 0.5 THEN 'MEDIUM_PERFORMANCE'
        ELSE 'LOW_PERFORMANCE'
    END as performance_tier,
    -- Recommended for new users based on reliability
    CASE 
        WHEN COUNT(se.id) >= 10 AND AVG(se.confidence) >= 0.6 
        THEN TRUE ELSE FALSE 
    END as recommended
FROM strategy s
LEFT JOIN signal_event se ON s.strategy_key = se.signal
GROUP BY s.strategy_key, s.base_strategy, s.side, s.strength, s.name, s.category, s.description
ORDER BY s.category, s.base_strategy, s.strength;

-- =============================================================================
-- INDEXES FOR VIEW PERFORMANCE
-- =============================================================================

-- Create indexes to support view performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_signal_event_date 
    ON signal_event (DATE(timestamp));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_signal_event_confidence_desc 
    ON signal_event (confidence DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_signal_run_start_time 
    ON signal_run (start_time DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_indicator_snapshot_name_timestamp 
    ON indicator_snapshot (indicator_name, timestamp DESC);

-- =============================================================================
-- VIEW PERMISSIONS
-- =============================================================================

-- Grant SELECT permissions on all views to appropriate roles
GRANT SELECT ON v_strategy_overview TO PUBLIC;
GRANT SELECT ON v_strategy_performance TO PUBLIC;
GRANT SELECT ON v_base_strategy_summary TO PUBLIC;
GRANT SELECT ON v_recent_signals TO PUBLIC;
GRANT SELECT ON v_signal_frequency TO PUBLIC;
GRANT SELECT ON v_high_confidence_signals TO PUBLIC;
GRANT SELECT ON v_symbol_coverage TO PUBLIC;
GRANT SELECT ON v_indicator_status TO PUBLIC;
GRANT SELECT ON v_symbol_indicator_matrix TO PUBLIC;
GRANT SELECT ON v_signal_run_monitor TO PUBLIC;
GRANT SELECT ON v_data_quality_dashboard TO PUBLIC;
GRANT SELECT ON v_system_performance TO PUBLIC;
GRANT SELECT ON v_executive_dashboard TO PUBLIC;
GRANT SELECT ON v_strategy_explorer TO PUBLIC;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON VIEW v_strategy_overview IS 'Comprehensive overview of all strategies with usage statistics';
COMMENT ON VIEW v_strategy_performance IS 'Performance metrics for each strategy including confidence and activity';
COMMENT ON VIEW v_base_strategy_summary IS 'Aggregated statistics by base strategy family';
COMMENT ON VIEW v_recent_signals IS 'Recent signals with enriched strategy and run information';
COMMENT ON VIEW v_signal_frequency IS 'Analysis of signal frequency patterns by symbol and strategy';
COMMENT ON VIEW v_high_confidence_signals IS 'Top 10% confidence signals for quality analysis';
COMMENT ON VIEW v_symbol_coverage IS 'Symbol-level activity and strategy coverage metrics';
COMMENT ON VIEW v_indicator_status IS 'Indicator availability and freshness monitoring';
COMMENT ON VIEW v_symbol_indicator_matrix IS 'Matrix of indicator availability by symbol';
COMMENT ON VIEW v_signal_run_monitor IS 'Monitoring view for signal run execution and performance';
COMMENT ON VIEW v_data_quality_dashboard IS 'Data quality metrics across all tables';
COMMENT ON VIEW v_system_performance IS 'Daily performance trends and activity metrics';
COMMENT ON VIEW v_executive_dashboard IS 'High-level KPIs for executive reporting';
COMMENT ON VIEW v_strategy_explorer IS 'Strategy selection interface with usage and performance data';