-- Dynamic Strategy Creation Database Functions
-- Enables dashboard-based strategy and signal management

-- ==============================================
-- Strategy Management Functions  
-- ==============================================

-- Function to create a new base strategy with all strength variants (1-9)
CREATE OR REPLACE FUNCTION create_base_strategy(
    p_base_strategy VARCHAR(4),
    p_side CHAR(1),
    p_name_template VARCHAR(200),
    p_description_template TEXT,
    p_category VARCHAR(32),
    p_metadata JSONB DEFAULT '{}'::jsonb
) RETURNS TABLE(
    created_strategy_key VARCHAR(5),
    created_strength SMALLINT,
    success BOOLEAN
) AS $$
DECLARE
    strength_names TEXT[] := ARRAY['Weak', 'Very Light', 'Light', 'Moderate-', 'Moderate', 'Moderate+', 'Strong', 'Very Strong', 'Extreme'];
    current_strength INTEGER;
    strategy_key VARCHAR(5);
    strategy_name VARCHAR(200);
BEGIN
    -- Validate base strategy format
    IF NOT p_base_strategy ~ '^[BS][A-Z]{3}$' THEN
        RAISE EXCEPTION 'Invalid base strategy format. Must be [B/S][XXX] (e.g., BBRK)';
    END IF;
    
    -- Validate side consistency
    IF LEFT(p_base_strategy, 1) != p_side THEN
        RAISE EXCEPTION 'Side % does not match base strategy prefix %', p_side, LEFT(p_base_strategy, 1);
    END IF;
    
    -- Validate category
    IF p_category NOT IN ('breakout', 'mean-reversion', 'trend', 'divergence', 'level') THEN
        RAISE EXCEPTION 'Invalid category. Must be one of: breakout, mean-reversion, trend, divergence, level';
    END IF;
    
    -- Create strategy variants for each strength level (1-9)
    FOR current_strength IN 1..9 LOOP
        strategy_key := p_base_strategy || current_strength::text;
        strategy_name := replace(p_name_template, '{strength}', strength_names[current_strength]);
        
        BEGIN
            INSERT INTO strategy (
                strategy_key, base_strategy, side, strength, 
                name, description, category, active, created_at
            ) VALUES (
                strategy_key, p_base_strategy, p_side, current_strength,
                strategy_name, p_description_template, p_category, true, now()
            );
            
            -- Return successful creation
            created_strategy_key := strategy_key;
            created_strength := current_strength;
            success := true;
            RETURN NEXT;
            
        EXCEPTION WHEN unique_violation THEN
            -- Strategy already exists, return failure
            created_strategy_key := strategy_key;
            created_strength := current_strength;
            success := false;
            RETURN NEXT;
        END;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Function to update strategy metadata
CREATE OR REPLACE FUNCTION update_strategy_metadata(
    p_base_strategy VARCHAR(4),
    p_name_template VARCHAR(200) DEFAULT NULL,
    p_description_template TEXT DEFAULT NULL,
    p_category VARCHAR(32) DEFAULT NULL,
    p_active BOOLEAN DEFAULT NULL
) RETURNS INTEGER AS $$
DECLARE
    updated_count INTEGER := 0;
    strength_names TEXT[] := ARRAY['Weak', 'Very Light', 'Light', 'Moderate-', 'Moderate', 'Moderate+', 'Strong', 'Very Strong', 'Extreme'];
    current_strength INTEGER;
    strategy_name VARCHAR(200);
BEGIN
    -- Update all strength variants for this base strategy
    FOR current_strength IN 1..9 LOOP
        -- Generate strength-specific name if template provided
        IF p_name_template IS NOT NULL THEN
            strategy_name := replace(p_name_template, '{strength}', strength_names[current_strength]);
        END IF;
        
        UPDATE strategy 
        SET 
            name = COALESCE(strategy_name, name),
            description = COALESCE(p_description_template, description),
            category = COALESCE(p_category, category),
            active = COALESCE(p_active, active),
            updated_at = now()
        WHERE base_strategy = p_base_strategy 
          AND strength = current_strength;
        
        GET DIAGNOSTICS updated_count = updated_count + ROW_COUNT;
    END LOOP;
    
    RETURN updated_count;
END;
$$ LANGUAGE plpgsql;

-- Function to delete a base strategy (all variants)
CREATE OR REPLACE FUNCTION delete_base_strategy(
    p_base_strategy VARCHAR(4),
    p_cascade BOOLEAN DEFAULT FALSE
) RETURNS TABLE(
    deleted_strategy_key VARCHAR(5),
    had_signals BOOLEAN
) AS $$
DECLARE
    strategy_record RECORD;
    signal_count INTEGER;
BEGIN
    -- Check if strategy has associated signals
    FOR strategy_record IN 
        SELECT strategy_key FROM strategy WHERE base_strategy = p_base_strategy
    LOOP
        -- Count associated signals
        SELECT COUNT(*) INTO signal_count 
        FROM signal_event 
        WHERE strategy_key = strategy_record.strategy_key;
        
        deleted_strategy_key := strategy_record.strategy_key;
        had_signals := signal_count > 0;
        
        -- Delete strategy (signals will be cascade deleted if p_cascade is true)
        IF p_cascade OR signal_count = 0 THEN
            DELETE FROM strategy WHERE strategy_key = strategy_record.strategy_key;
        ELSE
            RAISE EXCEPTION 'Strategy % has % associated signals. Use cascade=true to force deletion.', 
                strategy_record.strategy_key, signal_count;
        END IF;
        
        RETURN NEXT;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Function to validate strategy key format
CREATE OR REPLACE FUNCTION validate_strategy_key(p_strategy_key VARCHAR(5))
RETURNS BOOLEAN AS $$
BEGIN
    -- Check format: [BS][A-Z]{3}[1-9]
    IF NOT p_strategy_key ~ '^[BS][A-Z]{3}[1-9]$' THEN
        RETURN FALSE;
    END IF;
    
    -- Check if base strategy exists in dictionary
    IF NOT EXISTS (
        SELECT 1 FROM strategy 
        WHERE base_strategy = LEFT(p_strategy_key, 4)
    ) THEN
        RETURN FALSE;
    END IF;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- ==============================================
-- Parameter Set Management Functions
-- ==============================================

-- Function to create parameter set with validation
CREATE OR REPLACE FUNCTION create_parameter_set_safe(
    p_name VARCHAR(128),
    p_params_json JSONB,
    p_owner_user_id UUID DEFAULT NULL,
    p_engine_version VARCHAR(64) DEFAULT '1.0.0'
) RETURNS UUID AS $$
DECLARE
    param_set_id UUID;
    params_hash CHAR(32);
    canonical_json TEXT;
BEGIN
    -- Generate canonical JSON (sorted keys)
    canonical_json := jsonb_pretty(p_params_json);
    params_hash := md5(canonical_json);
    
    -- Check for duplicate parameter sets
    SELECT param_set_id INTO param_set_id
    FROM parameter_set 
    WHERE params_hash = params_hash AND engine_version = p_engine_version;
    
    IF FOUND THEN
        RAISE NOTICE 'Parameter set with identical parameters already exists: %', param_set_id;
        RETURN param_set_id;
    END IF;
    
    -- Create new parameter set
    param_set_id := gen_random_uuid();
    
    INSERT INTO parameter_set (
        param_set_id, name, owner_user_id, params_json, 
        params_hash, engine_version, created_at
    ) VALUES (
        param_set_id, p_name, p_owner_user_id, p_params_json,
        params_hash, p_engine_version, now()
    );
    
    RETURN param_set_id;
END;
$$ LANGUAGE plpgsql;

-- Function to clone parameter set with modifications
CREATE OR REPLACE FUNCTION clone_parameter_set(
    p_source_param_set_id UUID,
    p_new_name VARCHAR(128),
    p_modifications JSONB DEFAULT '{}'::jsonb,
    p_owner_user_id UUID DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    source_params JSONB;
    new_params JSONB;
    new_param_set_id UUID;
BEGIN
    -- Get source parameters
    SELECT params_json INTO source_params
    FROM parameter_set
    WHERE param_set_id = p_source_param_set_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Source parameter set not found: %', p_source_param_set_id;
    END IF;
    
    -- Merge modifications
    new_params := source_params || p_modifications;
    
    -- Create new parameter set
    new_param_set_id := create_parameter_set_safe(
        p_new_name, new_params, p_owner_user_id
    );
    
    RETURN new_param_set_id;
END;
$$ LANGUAGE plpgsql;

-- ==============================================
-- Signal Event Management Functions
-- ==============================================

-- Function to create signal event with validation
CREATE OR REPLACE FUNCTION create_signal_event_safe(
    p_symbol VARCHAR(10),
    p_bar_date DATE,
    p_strategy_key VARCHAR(5),
    p_close_at_signal NUMERIC(18,6),
    p_volume_at_signal BIGINT DEFAULT NULL,
    p_thresholds_json JSONB DEFAULT '{}'::jsonb,
    p_reasons_json JSONB DEFAULT '[]'::jsonb,
    p_score_json JSONB DEFAULT '{}'::jsonb,
    p_run_id UUID DEFAULT NULL,
    p_param_set_id UUID DEFAULT NULL,
    p_provisional BOOLEAN DEFAULT false
) RETURNS BIGINT AS $$
DECLARE
    signal_id BIGINT;
    parsed_strategy RECORD;
BEGIN
    -- Validate strategy key format
    IF NOT validate_strategy_key(p_strategy_key) THEN
        RAISE EXCEPTION 'Invalid strategy key format: %', p_strategy_key;
    END IF;
    
    -- Parse strategy key
    SELECT 
        LEFT(p_strategy_key, 1) as action,
        LEFT(p_strategy_key, 4) as base_strategy,
        RIGHT(p_strategy_key, 1)::SMALLINT as strength
    INTO parsed_strategy;
    
    -- Validate symbol format (basic HK stock format)
    IF NOT p_symbol ~ '^[0-9]{4}\.HK$' THEN
        RAISE EXCEPTION 'Invalid symbol format: %. Expected format: ####.HK', p_symbol;
    END IF;
    
    -- Validate price is positive
    IF p_close_at_signal <= 0 THEN
        RAISE EXCEPTION 'Price must be positive: %', p_close_at_signal;
    END IF;
    
    -- Create signal event
    INSERT INTO signal_event (
        run_id, param_set_id, symbol, bar_date, tf, strategy_key,
        action, strength, provisional, close_at_signal, volume_at_signal,
        thresholds_json, reasons_json, score_json, created_at
    ) VALUES (
        p_run_id, p_param_set_id, p_symbol, p_bar_date, '1d', p_strategy_key,
        parsed_strategy.action, parsed_strategy.strength, p_provisional,
        p_close_at_signal, p_volume_at_signal, p_thresholds_json,
        p_reasons_json, p_score_json, now()
    )
    RETURNING signal_id INTO signal_id;
    
    RETURN signal_id;
END;
$$ LANGUAGE plpgsql;

-- Function to batch create signal events
CREATE OR REPLACE FUNCTION create_signal_events_batch(
    p_signals JSONB
) RETURNS TABLE(
    batch_index INTEGER,
    signal_id BIGINT,
    success BOOLEAN,
    error_message TEXT
) AS $$
DECLARE
    signal_data JSONB;
    i INTEGER := 0;
    created_signal_id BIGINT;
BEGIN
    FOR signal_data IN SELECT * FROM jsonb_array_elements(p_signals)
    LOOP
        i := i + 1;
        batch_index := i;
        
        BEGIN
            created_signal_id := create_signal_event_safe(
                (signal_data->>'symbol')::VARCHAR(10),
                (signal_data->>'bar_date')::DATE,
                (signal_data->>'strategy_key')::VARCHAR(5),
                (signal_data->>'close_at_signal')::NUMERIC(18,6),
                (signal_data->>'volume_at_signal')::BIGINT,
                COALESCE(signal_data->'thresholds_json', '{}'::jsonb),
                COALESCE(signal_data->'reasons_json', '[]'::jsonb),
                COALESCE(signal_data->'score_json', '{}'::jsonb),
                (signal_data->>'run_id')::UUID,
                (signal_data->>'param_set_id')::UUID,
                COALESCE((signal_data->>'provisional')::BOOLEAN, false)
            );
            
            signal_id := created_signal_id;
            success := true;
            error_message := NULL;
            
        EXCEPTION WHEN OTHERS THEN
            signal_id := NULL;
            success := false;
            error_message := SQLERRM;
        END;
        
        RETURN NEXT;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- ==============================================
-- Indicator Snapshot Management Functions
-- ==============================================

-- Function to upsert indicator snapshot
CREATE OR REPLACE FUNCTION upsert_indicator_snapshot(
    p_symbol VARCHAR(10),
    p_bar_date DATE,
    p_indicators JSONB
) RETURNS BOOLEAN AS $$
DECLARE
    indicator_key TEXT;
    indicator_value NUMERIC;
BEGIN
    -- Validate symbol format
    IF NOT p_symbol ~ '^[0-9]{4}\.HK$' THEN
        RAISE EXCEPTION 'Invalid symbol format: %. Expected format: ####.HK', p_symbol;
    END IF;
    
    -- Insert or update indicator snapshot
    INSERT INTO indicator_snapshot (symbol, bar_date)
    VALUES (p_symbol, p_bar_date)
    ON CONFLICT (symbol, bar_date) DO NOTHING;
    
    -- Update individual indicators
    FOR indicator_key, indicator_value IN 
        SELECT * FROM jsonb_each_text(p_indicators)
    LOOP
        -- Dynamic update based on indicator key
        EXECUTE format(
            'UPDATE indicator_snapshot SET %I = $1 WHERE symbol = $2 AND bar_date = $3',
            indicator_key
        ) USING indicator_value::NUMERIC, p_symbol, p_bar_date;
    END LOOP;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- ==============================================
-- Dashboard Query Functions
-- ==============================================

-- Function to get strategy performance summary
CREATE OR REPLACE FUNCTION get_strategy_performance_dashboard(
    p_days_back INTEGER DEFAULT 30,
    p_min_strength INTEGER DEFAULT 1
) RETURNS TABLE(
    base_strategy VARCHAR(4),
    strategy_name VARCHAR(64),
    side CHAR(1),
    category VARCHAR(32),
    total_signals BIGINT,
    avg_strength NUMERIC(4,2),
    strong_signals BIGINT,
    unique_symbols BIGINT,
    latest_signal_date DATE,
    performance_score NUMERIC(5,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.base_strategy,
        MAX(s.name) as strategy_name,
        s.side,
        s.category,
        COUNT(se.*) as total_signals,
        AVG(se.strength::numeric) as avg_strength,
        COUNT(se.*) FILTER (WHERE se.strength >= 7) as strong_signals,
        COUNT(DISTINCT se.symbol) as unique_symbols,
        MAX(se.bar_date) as latest_signal_date,
        -- Performance score: weighted by signal count and average strength
        (COUNT(se.*) * AVG(se.strength::numeric) / 10.0)::numeric(5,2) as performance_score
    FROM strategy s
    LEFT JOIN signal_event se ON s.strategy_key = se.strategy_key
        AND se.bar_date >= CURRENT_DATE - INTERVAL '%s days'
        AND se.strength >= p_min_strength
        AND se.provisional = false
    WHERE s.active = true
    GROUP BY s.base_strategy, s.side, s.category
    ORDER BY performance_score DESC NULLS LAST, total_signals DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get signal events for dashboard charts
CREATE OR REPLACE FUNCTION get_signal_events_chart_data(
    p_symbol VARCHAR(10) DEFAULT NULL,
    p_strategy_key VARCHAR(5) DEFAULT NULL,
    p_days_back INTEGER DEFAULT 90,
    p_min_strength INTEGER DEFAULT 1
) RETURNS TABLE(
    signal_date DATE,
    symbol VARCHAR(10),
    strategy_key VARCHAR(5),
    action CHAR(1),
    strength SMALLINT,
    close_price NUMERIC(18,6),
    volume_ratio NUMERIC,
    signal_color VARCHAR(7),
    tooltip_text TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        se.bar_date as signal_date,
        se.symbol,
        se.strategy_key,
        se.action,
        se.strength,
        se.close_at_signal as close_price,
        COALESCE((se.score_json->>'participation')::numeric, 1.0) as volume_ratio,
        -- Color coding based on action and strength
        CASE 
            WHEN se.action = 'B' AND se.strength >= 7 THEN '#006400'  -- Dark green
            WHEN se.action = 'B' AND se.strength >= 4 THEN '#32CD32'  -- Lime green  
            WHEN se.action = 'B' THEN '#90EE90'                       -- Light green
            WHEN se.action = 'S' AND se.strength >= 7 THEN '#DC143C'  -- Crimson
            WHEN se.action = 'S' AND se.strength >= 4 THEN '#FF1493'  -- Deep pink
            ELSE '#FFB6C1'                                            -- Light pink
        END as signal_color,
        -- Tooltip text
        format('%s%s: Strength %s at %s', 
            se.action, 
            SUBSTRING(se.strategy_key, 2, 3), 
            se.strength, 
            se.close_at_signal
        ) as tooltip_text
    FROM signal_event se
    JOIN strategy s ON se.strategy_key = s.strategy_key
    WHERE se.provisional = false
      AND se.strength >= p_min_strength
      AND se.bar_date >= CURRENT_DATE - INTERVAL '%s days'
      AND (p_symbol IS NULL OR se.symbol = p_symbol)
      AND (p_strategy_key IS NULL OR se.strategy_key = p_strategy_key)
    ORDER BY se.bar_date DESC, se.strength DESC;
END;
$$ LANGUAGE plpgsql;

-- ==============================================
-- Maintenance and Cleanup Functions
-- ==============================================

-- Function to cleanup old provisional signals
CREATE OR REPLACE FUNCTION cleanup_provisional_signals(
    p_hours_old INTEGER DEFAULT 24
) RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM signal_event
    WHERE provisional = true
      AND created_at < now() - INTERVAL '%s hours';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to archive old signals
CREATE OR REPLACE FUNCTION archive_old_signals(
    p_days_old INTEGER DEFAULT 365,
    p_create_archive_table BOOLEAN DEFAULT true
) RETURNS INTEGER AS $$
DECLARE
    archived_count INTEGER;
    archive_table_name TEXT;
BEGIN
    archive_table_name := 'signal_event_archive_' || to_char(now(), 'YYYY_MM');
    
    -- Create archive table if requested
    IF p_create_archive_table THEN
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS %I (LIKE signal_event INCLUDING ALL)
        ', archive_table_name);
    END IF;
    
    -- Move old signals to archive
    EXECUTE format('
        INSERT INTO %I 
        SELECT * FROM signal_event 
        WHERE bar_date < CURRENT_DATE - INTERVAL ''%s days''
          AND provisional = false
    ', archive_table_name, p_days_old);
    
    GET DIAGNOSTICS archived_count = ROW_COUNT;
    
    -- Delete archived signals from main table
    EXECUTE format('
        DELETE FROM signal_event 
        WHERE bar_date < CURRENT_DATE - INTERVAL ''%s days''
          AND provisional = false
    ', p_days_old);
    
    RETURN archived_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get system statistics
CREATE OR REPLACE FUNCTION get_system_statistics()
RETURNS TABLE(
    metric_name VARCHAR(50),
    metric_value BIGINT,
    metric_description TEXT
) AS $$
BEGIN
    -- Strategy statistics
    metric_name := 'total_strategies';
    SELECT COUNT(*) INTO metric_value FROM strategy WHERE active = true;
    metric_description := 'Total active strategies in system';
    RETURN NEXT;
    
    metric_name := 'base_strategies';
    SELECT COUNT(DISTINCT base_strategy) INTO metric_value FROM strategy WHERE active = true;
    metric_description := 'Unique base strategies';
    RETURN NEXT;
    
    -- Signal statistics  
    metric_name := 'total_signals';
    SELECT COUNT(*) INTO metric_value FROM signal_event WHERE provisional = false;
    metric_description := 'Total confirmed signal events';
    RETURN NEXT;
    
    metric_name := 'signals_last_30_days';
    SELECT COUNT(*) INTO metric_value FROM signal_event 
    WHERE provisional = false AND bar_date >= CURRENT_DATE - INTERVAL '30 days';
    metric_description := 'Signals generated in last 30 days';
    RETURN NEXT;
    
    metric_name := 'strong_signals_last_30_days';
    SELECT COUNT(*) INTO metric_value FROM signal_event 
    WHERE provisional = false AND strength >= 7 AND bar_date >= CURRENT_DATE - INTERVAL '30 days';
    metric_description := 'Strong signals (7-9) in last 30 days';
    RETURN NEXT;
    
    -- Parameter set statistics
    metric_name := 'parameter_sets';
    SELECT COUNT(*) INTO metric_value FROM parameter_set;
    metric_description := 'Total parameter configurations';
    RETURN NEXT;
    
    -- Indicator statistics
    metric_name := 'indicator_snapshots';
    SELECT COUNT(*) INTO metric_value FROM indicator_snapshot 
    WHERE bar_date >= CURRENT_DATE - INTERVAL '7 days';
    metric_description := 'Indicator snapshots in last 7 days';
    RETURN NEXT;
    
    metric_name := 'unique_symbols';
    SELECT COUNT(DISTINCT symbol) INTO metric_value FROM signal_event 
    WHERE bar_date >= CURRENT_DATE - INTERVAL '30 days';
    metric_description := 'Unique symbols with signals in last 30 days';
    RETURN NEXT;
    
END;
$$ LANGUAGE plpgsql;

-- ==============================================
-- Database Comments and Documentation
-- ==============================================

COMMENT ON FUNCTION create_base_strategy IS 'Creates a new base strategy with all 9 strength variants for dashboard management';
COMMENT ON FUNCTION update_strategy_metadata IS 'Updates metadata for all variants of a base strategy';
COMMENT ON FUNCTION delete_base_strategy IS 'Deletes a base strategy and all its variants, with optional cascade';
COMMENT ON FUNCTION validate_strategy_key IS 'Validates TXYZn strategy key format and existence';
COMMENT ON FUNCTION create_parameter_set_safe IS 'Creates parameter set with duplicate detection';
COMMENT ON FUNCTION create_signal_event_safe IS 'Creates signal event with comprehensive validation';
COMMENT ON FUNCTION get_strategy_performance_dashboard IS 'Returns strategy performance metrics for dashboard charts';
COMMENT ON FUNCTION cleanup_provisional_signals IS 'Removes old provisional signals to maintain database performance';

-- Grant execute permissions (adjust as needed for your security model)
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO traders, dashboard_users;

SELECT 'Dynamic strategy creation database functions installed successfully' AS status;