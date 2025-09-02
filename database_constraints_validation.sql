-- Strategic Signal System: Database Constraints and Validation Functions
-- Adds comprehensive constraints and validation to ensure data integrity

-- =============================================================================
-- CONSTRAINTS AND INDEXES
-- =============================================================================

-- Add unique constraint on strategy key format
ALTER TABLE strategy ADD CONSTRAINT chk_strategy_key_format 
    CHECK (strategy_key ~ '^[BS][A-Z]{3}[1-9]$');

-- Add constraint to ensure base_strategy matches strategy_key prefix
ALTER TABLE strategy ADD CONSTRAINT chk_base_strategy_match 
    CHECK (base_strategy = SUBSTRING(strategy_key, 2, 4));

-- Add constraint to ensure side matches strategy_key first character
ALTER TABLE strategy ADD CONSTRAINT chk_side_match 
    CHECK (side = SUBSTRING(strategy_key, 1, 1));

-- Add constraint to ensure strength matches strategy_key last character
ALTER TABLE strategy ADD CONSTRAINT chk_strength_match 
    CHECK (strength = CAST(SUBSTRING(strategy_key, 5, 1) AS INTEGER));

-- Add constraint on category values
ALTER TABLE strategy ADD CONSTRAINT chk_category_valid 
    CHECK (category IN ('breakout', 'mean-reversion', 'trend', 'divergence', 'level'));

-- Parameter set constraints
ALTER TABLE parameter_set ADD CONSTRAINT chk_hash_format 
    CHECK (parameter_hash ~ '^[a-f0-9]{32}$');

ALTER TABLE parameter_set ADD CONSTRAINT chk_parameters_not_empty 
    CHECK (jsonb_array_length(parameters) > 0);

-- Signal run constraints
ALTER TABLE signal_run ADD CONSTRAINT chk_run_id_format 
    CHECK (run_id ~ '^[0-9]{8}_[0-9]{6}_[a-f0-9]{8}$');

ALTER TABLE signal_run ADD CONSTRAINT chk_end_after_start 
    CHECK (end_time >= start_time);

-- Signal event constraints
ALTER TABLE signal_event ADD CONSTRAINT chk_signal_format 
    CHECK (signal ~ '^[BS][A-Z]{3}[1-9]$');

ALTER TABLE signal_event ADD CONSTRAINT chk_confidence_range 
    CHECK (confidence >= 0.0 AND confidence <= 1.0);

ALTER TABLE signal_event ADD CONSTRAINT chk_strength_range 
    CHECK (strength >= 1 AND strength <= 9);

-- Indicator snapshot constraints
ALTER TABLE indicator_snapshot ADD CONSTRAINT chk_indicator_name_valid 
    CHECK (indicator_name IN (
        'rsi14', 'rsi21', 'rsi50', 'rsi_divergence',
        'macd', 'ppo', 'macd_histogram', 'ppo_signal',
        'sma20', 'ema20', 'sma50', 'ema50', 'sma200', 'ema200',
        'bb_upper', 'bb_lower', 'bb_percent',
        'volume_sma', 'volume_ratio', 'adl',
        'momentum'
    ));

-- Add performance indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_signal_event_symbol_timestamp 
    ON signal_event (symbol, timestamp DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_signal_event_signal_timestamp 
    ON signal_event (signal, timestamp DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_signal_event_run_id 
    ON signal_event (run_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_indicator_snapshot_symbol_timestamp 
    ON indicator_snapshot (symbol, timestamp DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_indicator_snapshot_name_symbol 
    ON indicator_snapshot (indicator_name, symbol);

-- =============================================================================
-- VALIDATION FUNCTIONS
-- =============================================================================

-- Validate TXYZn signal format
CREATE OR REPLACE FUNCTION validate_signal_format(signal_code TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN signal_code ~ '^[BS][A-Z]{3}[1-9]$';
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Validate strategy exists
CREATE OR REPLACE FUNCTION validate_strategy_exists(strategy_key TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (SELECT 1 FROM strategy WHERE strategy.strategy_key = validate_strategy_exists.strategy_key);
END;
$$ LANGUAGE plpgsql STABLE;

-- Validate indicator configuration
CREATE OR REPLACE FUNCTION validate_indicator_config(config JSONB)
RETURNS TABLE(is_valid BOOLEAN, error_message TEXT) AS $$
DECLARE
    required_fields TEXT[] := ARRAY['period', 'source'];
    field TEXT;
BEGIN
    -- Check for required fields
    FOREACH field IN ARRAY required_fields
    LOOP
        IF NOT (config ? field) THEN
            RETURN QUERY SELECT FALSE, 'Missing required field: ' || field;
            RETURN;
        END IF;
    END LOOP;
    
    -- Validate period is positive integer
    IF NOT (jsonb_typeof(config->'period') = 'number' AND (config->>'period')::INTEGER > 0) THEN
        RETURN QUERY SELECT FALSE, 'Period must be a positive integer';
        RETURN;
    END IF;
    
    -- Validate source field
    IF NOT (config->>'source' IN ('close', 'high', 'low', 'volume', 'hlc3', 'ohlc4')) THEN
        RETURN QUERY SELECT FALSE, 'Invalid source field';
        RETURN;
    END IF;
    
    RETURN QUERY SELECT TRUE, NULL::TEXT;
END;
$$ LANGUAGE plpgsql STABLE;

-- Validate signal event data integrity
CREATE OR REPLACE FUNCTION validate_signal_event(
    p_symbol TEXT,
    p_signal TEXT,
    p_timestamp TIMESTAMP,
    p_confidence DECIMAL(5,4),
    p_strength INTEGER,
    p_evidence JSONB
) RETURNS TABLE(is_valid BOOLEAN, error_message TEXT) AS $$
BEGIN
    -- Validate signal format
    IF NOT validate_signal_format(p_signal) THEN
        RETURN QUERY SELECT FALSE, 'Invalid signal format: ' || p_signal;
        RETURN;
    END IF;
    
    -- Validate strategy exists
    IF NOT validate_strategy_exists(p_signal) THEN
        RETURN QUERY SELECT FALSE, 'Strategy does not exist: ' || p_signal;
        RETURN;
    END IF;
    
    -- Validate confidence range
    IF p_confidence < 0.0 OR p_confidence > 1.0 THEN
        RETURN QUERY SELECT FALSE, 'Confidence must be between 0.0 and 1.0';
        RETURN;
    END IF;
    
    -- Validate strength range
    IF p_strength < 1 OR p_strength > 9 THEN
        RETURN QUERY SELECT FALSE, 'Strength must be between 1 and 9';
        RETURN;
    END IF;
    
    -- Validate evidence structure
    IF NOT (p_evidence ? 'thresholds' AND p_evidence ? 'reasons' AND p_evidence ? 'score') THEN
        RETURN QUERY SELECT FALSE, 'Evidence must contain thresholds, reasons, and score';
        RETURN;
    END IF;
    
    -- Validate score is numeric
    IF NOT (jsonb_typeof(p_evidence->'score') = 'number') THEN
        RETURN QUERY SELECT FALSE, 'Evidence score must be numeric';
        RETURN;
    END IF;
    
    RETURN QUERY SELECT TRUE, NULL::TEXT;
END;
$$ LANGUAGE plpgsql STABLE;

-- Batch validate signal events
CREATE OR REPLACE FUNCTION batch_validate_signal_events(events JSONB[])
RETURNS TABLE(
    index INTEGER,
    is_valid BOOLEAN,
    error_message TEXT
) AS $$
DECLARE
    event JSONB;
    i INTEGER := 1;
    validation_result RECORD;
BEGIN
    FOREACH event IN ARRAY events
    LOOP
        SELECT * FROM validate_signal_event(
            event->>'symbol',
            event->>'signal',
            (event->>'timestamp')::TIMESTAMP,
            (event->>'confidence')::DECIMAL(5,4),
            (event->>'strength')::INTEGER,
            event->'evidence'
        ) INTO validation_result;
        
        RETURN QUERY SELECT i, validation_result.is_valid, validation_result.error_message;
        i := i + 1;
    END LOOP;
END;
$$ LANGUAGE plpgsql STABLE;

-- =============================================================================
-- DATA INTEGRITY TRIGGERS
-- =============================================================================

-- Trigger function to validate signal events before insert/update
CREATE OR REPLACE FUNCTION trigger_validate_signal_event()
RETURNS TRIGGER AS $$
DECLARE
    validation_result RECORD;
BEGIN
    SELECT * FROM validate_signal_event(
        NEW.symbol,
        NEW.signal,
        NEW.timestamp,
        NEW.confidence,
        NEW.strength,
        NEW.evidence
    ) INTO validation_result;
    
    IF NOT validation_result.is_valid THEN
        RAISE EXCEPTION 'Signal event validation failed: %', validation_result.error_message;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
DROP TRIGGER IF EXISTS validate_signal_event_trigger ON signal_event;
CREATE TRIGGER validate_signal_event_trigger
    BEFORE INSERT OR UPDATE ON signal_event
    FOR EACH ROW EXECUTE FUNCTION trigger_validate_signal_event();

-- Trigger to ensure parameter hash matches parameters
CREATE OR REPLACE FUNCTION trigger_validate_parameter_hash()
RETURNS TRIGGER AS $$
BEGIN
    -- Recalculate hash to ensure consistency
    NEW.parameter_hash := md5(NEW.parameters::TEXT);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS validate_parameter_hash_trigger ON parameter_set;
CREATE TRIGGER validate_parameter_hash_trigger
    BEFORE INSERT OR UPDATE ON parameter_set
    FOR EACH ROW EXECUTE FUNCTION trigger_validate_parameter_hash();

-- =============================================================================
-- UTILITY FUNCTIONS
-- =============================================================================

-- Get signal components (transaction type, strategy, strength)
CREATE OR REPLACE FUNCTION parse_signal(signal_code TEXT)
RETURNS TABLE(
    transaction_type CHAR(1),
    strategy_code CHAR(4),
    strength INTEGER,
    is_valid BOOLEAN
) AS $$
BEGIN
    IF NOT validate_signal_format(signal_code) THEN
        RETURN QUERY SELECT NULL::CHAR(1), NULL::CHAR(4), NULL::INTEGER, FALSE;
        RETURN;
    END IF;
    
    RETURN QUERY SELECT 
        SUBSTRING(signal_code, 1, 1)::CHAR(1),
        SUBSTRING(signal_code, 2, 4)::CHAR(4),
        SUBSTRING(signal_code, 5, 1)::INTEGER,
        TRUE;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Check data consistency across tables
CREATE OR REPLACE FUNCTION check_data_consistency()
RETURNS TABLE(
    check_name TEXT,
    status TEXT,
    details TEXT
) AS $$
BEGIN
    -- Check for orphaned signal events
    RETURN QUERY
    SELECT 
        'Orphaned Signal Events'::TEXT,
        CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
        'Found ' || COUNT(*) || ' signal events without matching strategies'
    FROM signal_event se
    LEFT JOIN strategy s ON se.signal = s.strategy_key
    WHERE s.strategy_key IS NULL;
    
    -- Check for invalid signal formats
    RETURN QUERY
    SELECT 
        'Invalid Signal Formats'::TEXT,
        CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
        'Found ' || COUNT(*) || ' signal events with invalid formats'
    FROM signal_event
    WHERE NOT validate_signal_format(signal);
    
    -- Check for confidence out of range
    RETURN QUERY
    SELECT 
        'Confidence Range'::TEXT,
        CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
        'Found ' || COUNT(*) || ' signal events with confidence out of range'
    FROM signal_event
    WHERE confidence < 0.0 OR confidence > 1.0;
    
    -- Check for strength out of range
    RETURN QUERY
    SELECT 
        'Strength Range'::TEXT,
        CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
        'Found ' || COUNT(*) || ' signal events with strength out of range'
    FROM signal_event
    WHERE strength < 1 OR strength > 9;
    
    -- Check parameter hash consistency
    RETURN QUERY
    SELECT 
        'Parameter Hash Consistency'::TEXT,
        CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
        'Found ' || COUNT(*) || ' parameter sets with inconsistent hashes'
    FROM parameter_set
    WHERE parameter_hash != md5(parameters::TEXT);
END;
$$ LANGUAGE plpgsql STABLE;

-- Clean up invalid data (use with caution)
CREATE OR REPLACE FUNCTION cleanup_invalid_data(dry_run BOOLEAN DEFAULT TRUE)
RETURNS TABLE(
    action TEXT,
    affected_rows INTEGER,
    details TEXT
) AS $$
DECLARE
    orphaned_count INTEGER;
    invalid_format_count INTEGER;
    out_of_range_count INTEGER;
BEGIN
    -- Count orphaned signal events
    SELECT COUNT(*) INTO orphaned_count
    FROM signal_event se
    LEFT JOIN strategy s ON se.signal = s.strategy_key
    WHERE s.strategy_key IS NULL;
    
    -- Count invalid signal formats
    SELECT COUNT(*) INTO invalid_format_count
    FROM signal_event
    WHERE NOT validate_signal_format(signal);
    
    -- Count out of range values
    SELECT COUNT(*) INTO out_of_range_count
    FROM signal_event
    WHERE confidence < 0.0 OR confidence > 1.0 OR strength < 1 OR strength > 9;
    
    -- Return planned actions
    RETURN QUERY SELECT 'DELETE Orphaned Events'::TEXT, orphaned_count, 'Signal events without matching strategies';
    RETURN QUERY SELECT 'DELETE Invalid Formats'::TEXT, invalid_format_count, 'Signal events with invalid TXYZn format';
    RETURN QUERY SELECT 'DELETE Out of Range'::TEXT, out_of_range_count, 'Signal events with invalid confidence/strength';
    
    -- Execute cleanup if not dry run
    IF NOT dry_run THEN
        -- Delete orphaned signal events
        DELETE FROM signal_event se
        WHERE NOT EXISTS (SELECT 1 FROM strategy s WHERE se.signal = s.strategy_key);
        
        -- Delete invalid signal formats
        DELETE FROM signal_event WHERE NOT validate_signal_format(signal);
        
        -- Delete out of range values
        DELETE FROM signal_event 
        WHERE confidence < 0.0 OR confidence > 1.0 OR strength < 1 OR strength > 9;
        
        -- Fix parameter hashes
        UPDATE parameter_set SET parameter_hash = md5(parameters::TEXT) 
        WHERE parameter_hash != md5(parameters::TEXT);
    END IF;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON FUNCTION validate_signal_format(TEXT) IS 'Validates TXYZn signal format compliance';
COMMENT ON FUNCTION validate_strategy_exists(TEXT) IS 'Checks if strategy exists in strategy table';
COMMENT ON FUNCTION validate_indicator_config(JSONB) IS 'Validates indicator configuration parameters';
COMMENT ON FUNCTION validate_signal_event(TEXT, TEXT, TIMESTAMP, DECIMAL, INTEGER, JSONB) IS 'Comprehensive signal event validation';
COMMENT ON FUNCTION batch_validate_signal_events(JSONB[]) IS 'Batch validation for multiple signal events';
COMMENT ON FUNCTION parse_signal(TEXT) IS 'Parses TXYZn signal into components';
COMMENT ON FUNCTION check_data_consistency() IS 'Comprehensive data consistency check';
COMMENT ON FUNCTION cleanup_invalid_data(BOOLEAN) IS 'Cleanup invalid data with dry run option';

-- Grant permissions
GRANT EXECUTE ON FUNCTION validate_signal_format(TEXT) TO PUBLIC;
GRANT EXECUTE ON FUNCTION validate_strategy_exists(TEXT) TO PUBLIC;
GRANT EXECUTE ON FUNCTION validate_indicator_config(JSONB) TO PUBLIC;
GRANT EXECUTE ON FUNCTION validate_signal_event(TEXT, TEXT, TIMESTAMP, DECIMAL, INTEGER, JSONB) TO PUBLIC;
GRANT EXECUTE ON FUNCTION batch_validate_signal_events(JSONB[]) TO PUBLIC;
GRANT EXECUTE ON FUNCTION parse_signal(TEXT) TO PUBLIC;
GRANT EXECUTE ON FUNCTION check_data_consistency() TO PUBLIC;