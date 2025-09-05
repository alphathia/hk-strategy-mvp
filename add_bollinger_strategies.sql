-- Add Bollinger Band strategies to strategy_catalog
-- Based on John Bollinger's methodology and professional trading practices

BEGIN;

-- Insert Bollinger Band strategies into strategy_catalog
INSERT INTO strategy_catalog (
    strategy_base, strategy_name, signal_side, category, description,
    required_indicators, optional_indicators, default_parameters,
    usage_guidelines, risk_considerations, market_conditions,
    implementation_complexity, computational_cost, priority
) VALUES 

-- BBOL - Bollinger Bounce (Buy)
('BBOL', 'Bollinger Bounce Buy', 'B', 'mean-reversion', 
 'Mean reversion strategy: Buy when price touches lower Bollinger Band with oversold confirmation',
 ARRAY['bollinger_lower', 'bollinger_middle', 'close_price', 'rsi_14'],
 ARRAY['bollinger_upper', 'volume_ratio', 'stochastic_k', 'williams_r'],
 '{"percent_b_threshold": 0.2, "rsi_oversold": 30, "volume_confirmation": 1.3, "bounce_tolerance": 0.002}',
 'Best used in ranging markets when price touches lower band with RSI oversold. Requires volume confirmation.',
 'False signals in strong downtrends. Use tight stops below lower band. Not suitable for trending markets.',
 ARRAY['ranging', 'stable', 'oversold'],
 'moderate', 'medium', 12),

-- SBOS - Bollinger Bounce (Sell) 
('SBOS', 'Bollinger Bounce Sell', 'S', 'mean-reversion',
 'Mean reversion strategy: Sell when price touches upper Bollinger Band with overbought confirmation',
 ARRAY['bollinger_upper', 'bollinger_middle', 'close_price', 'rsi_14'],
 ARRAY['bollinger_lower', 'volume_ratio', 'stochastic_k', 'williams_r'],
 '{"percent_b_threshold": 0.8, "rsi_overbought": 70, "volume_confirmation": 1.3, "rejection_tolerance": 0.002}',
 'Best used in ranging markets when price touches upper band with RSI overbought. Requires volume confirmation.',
 'False signals in strong uptrends. Use tight stops above upper band. Not suitable for trending markets.',
 ARRAY['ranging', 'stable', 'overbought'],
 'moderate', 'medium', 13),

-- BBSU - Bollinger Squeeze Breakout (Up)
('BBSU', 'Bollinger Squeeze Up', 'B', 'breakout',
 'Volatility breakout strategy: Buy on upward breakout from Bollinger Squeeze (low volatility)',
 ARRAY['bollinger_upper', 'bollinger_middle', 'bollinger_lower', 'volume_ratio'],
 ARRAY['band_width', 'atr_14', 'rsi_14', 'close_price'],
 '{"squeeze_periods": 20, "breakout_threshold": 0.01, "volume_threshold": 1.5, "band_width_percentile": 10}',
 'Best after extended consolidation when volatility contracts. Requires high volume breakout confirmation.',
 'Squeeze can continue longer than expected. Use wide stops. High reward potential but lower frequency.',
 ARRAY['consolidation', 'pre-breakout', 'low-volatility'],
 'complex', 'high', 14),

-- SBSD - Bollinger Squeeze Breakdown (Down)
('SBSD', 'Bollinger Squeeze Down', 'S', 'breakout',
 'Volatility breakdown strategy: Sell on downward breakdown from Bollinger Squeeze (low volatility)',
 ARRAY['bollinger_upper', 'bollinger_middle', 'bollinger_lower', 'volume_ratio'],
 ARRAY['band_width', 'atr_14', 'rsi_14', 'close_price'],
 '{"squeeze_periods": 20, "breakdown_threshold": 0.01, "volume_threshold": 1.5, "band_width_percentile": 10}',
 'Best after extended consolidation when volatility contracts. Requires high volume breakdown confirmation.',
 'Squeeze can continue longer than expected. Use wide stops. High reward potential but lower frequency.',
 ARRAY['consolidation', 'pre-breakdown', 'low-volatility'],
 'complex', 'high', 15),

-- BBWU - Bollinger Band Walking (Up)
('BBWU', 'Bollinger Walk Up', 'B', 'trend',
 'Trend following strategy: Buy when price consistently walks along upper Bollinger Band',
 ARRAY['bollinger_upper', 'bollinger_middle', 'close_price', 'percent_b'],
 ARRAY['rsi_14', 'volume_ratio', 'atr_14'],
 '{"walking_periods": 5, "percent_b_threshold": 0.8, "rsi_max": 80, "trend_strength": 0.02}',
 'Best in strong uptrends when price hugs upper band. RSI should not be extremely overbought.',
 'Can signal late in trends. Watch for RSI divergence. Use trailing stops below lower band.',
 ARRAY['uptrending', 'strong-momentum'],
 'moderate', 'medium', 16),

-- SBWD - Bollinger Band Walking (Down)  
('SBWD', 'Bollinger Walk Down', 'S', 'trend',
 'Trend following strategy: Sell when price consistently walks along lower Bollinger Band',
 ARRAY['bollinger_lower', 'bollinger_middle', 'close_price', 'percent_b'],
 ARRAY['rsi_14', 'volume_ratio', 'atr_14'],
 '{"walking_periods": 5, "percent_b_threshold": 0.2, "rsi_min": 20, "trend_strength": 0.02}',
 'Best in strong downtrends when price hugs lower band. RSI should not be extremely oversold.',
 'Can signal late in trends. Watch for RSI divergence. Use trailing stops above upper band.',
 ARRAY['downtrending', 'strong-momentum'],
 'moderate', 'medium', 17),

-- HBOL - Hold Bollinger (Neutral)
('HBOL', 'Hold Bollinger Neutral', 'H', 'trend',
 'Neutral strategy: Hold when price is between Bollinger Bands with no clear directional bias',
 ARRAY['bollinger_upper', 'bollinger_lower', 'bollinger_middle', 'close_price'],
 ARRAY['percent_b', 'band_width', 'rsi_14'],
 '{"percent_b_min": 0.3, "percent_b_max": 0.7, "volatility_state": "normal"}',
 'Used when price is in middle zone of Bollinger Bands with normal volatility.',
 'May miss trending moves. Monitor for band squeeze or expansion signals.',
 ARRAY['ranging', 'normal-volatility'],
 'simple', 'low', 18)

ON CONFLICT (strategy_base) 
DO UPDATE SET
    strategy_name = EXCLUDED.strategy_name,
    description = EXCLUDED.description,
    required_indicators = EXCLUDED.required_indicators,
    optional_indicators = EXCLUDED.optional_indicators,
    default_parameters = EXCLUDED.default_parameters,
    usage_guidelines = EXCLUDED.usage_guidelines,
    risk_considerations = EXCLUDED.risk_considerations,
    market_conditions = EXCLUDED.market_conditions,
    updated_at = CURRENT_TIMESTAMP;

-- Update color schemes for Bollinger strategies
UPDATE strategy_catalog SET color_scheme = '{
    "1": "#8B0000", "2": "#A52A2A", "3": "#CD5C5C",
    "4": "#FFA500", "5": "#FFD700", "6": "#ADFF2F", 
    "7": "#32CD32", "8": "#228B22", "9": "#006400"
}'::jsonb WHERE strategy_base IN ('BBOL', 'SBOS', 'BBSU', 'SBSD', 'BBWU', 'SBWD', 'HBOL');

-- Update icons for Bollinger strategies
UPDATE strategy_catalog SET icon = 
    CASE strategy_base
        WHEN 'BBOL' THEN '🎯'  -- Bounce Buy
        WHEN 'SBOS' THEN '🔻'  -- Bounce Sell
        WHEN 'BBSU' THEN '🚀'  -- Squeeze Up
        WHEN 'SBSD' THEN '📉'  -- Squeeze Down  
        WHEN 'BBWU' THEN '📈'  -- Walk Up
        WHEN 'SBWD' THEN '⬇️'  -- Walk Down
        WHEN 'HBOL' THEN '⚪'  -- Hold
    END
WHERE strategy_base IN ('BBOL', 'SBOS', 'BBSU', 'SBSD', 'BBWU', 'SBWD', 'HBOL');

-- Create Bollinger-specific analysis view
CREATE OR REPLACE VIEW bollinger_strategy_analysis AS
SELECT 
    sc.strategy_base,
    sc.strategy_name,
    sc.signal_side,
    sc.category,
    sc.description,
    sc.usage_guidelines,
    sc.risk_considerations,
    sc.market_conditions,
    sc.default_parameters,
    -- Recent signal statistics
    COUNT(ts.id) as recent_signals_30d,
    AVG(ts.signal_magnitude) as avg_magnitude,
    MAX(ts.created_at) as last_signal_date
FROM strategy_catalog sc
LEFT JOIN trading_signals ts ON sc.strategy_base = ts.strategy_base 
    AND ts.created_at >= CURRENT_DATE - INTERVAL '30 days'
WHERE sc.strategy_base IN ('BBOL', 'SBOS', 'BBSU', 'SBSD', 'BBWU', 'SBWD', 'HBOL')
GROUP BY sc.strategy_base, sc.strategy_name, sc.signal_side, sc.category, 
         sc.description, sc.usage_guidelines, sc.risk_considerations, 
         sc.market_conditions, sc.default_parameters
ORDER BY sc.priority;

-- Create helper function to detect Bollinger Squeeze
CREATE OR REPLACE FUNCTION detect_bollinger_squeeze(
    symbol_param VARCHAR(10),
    lookback_days INTEGER DEFAULT 20
) RETURNS BOOLEAN AS $$
DECLARE
    is_squeeze BOOLEAN := FALSE;
    min_band_width DECIMAL;
    current_band_width DECIMAL;
BEGIN
    -- Get current band width
    SELECT bollinger_width INTO current_band_width
    FROM daily_equity_technicals
    WHERE symbol = symbol_param
    ORDER BY trade_date DESC
    LIMIT 1;
    
    -- Get minimum band width in lookback period
    SELECT MIN(bollinger_width) INTO min_band_width
    FROM daily_equity_technicals
    WHERE symbol = symbol_param
      AND trade_date >= CURRENT_DATE - lookback_days
      AND bollinger_width IS NOT NULL;
    
    -- Check if current width equals minimum (squeeze condition)
    IF current_band_width IS NOT NULL AND min_band_width IS NOT NULL THEN
        is_squeeze := (current_band_width = min_band_width);
    END IF;
    
    RETURN is_squeeze;
END;
$$ LANGUAGE plpgsql;

COMMIT;

-- Display results
SELECT 'Bollinger Band Strategies Added Successfully' as status;
SELECT strategy_base, strategy_name, signal_side, category 
FROM strategy_catalog 
WHERE strategy_base IN ('BBOL', 'SBOS', 'BBSU', 'SBSD', 'BBWU', 'SBWD', 'HBOL')
ORDER BY priority;