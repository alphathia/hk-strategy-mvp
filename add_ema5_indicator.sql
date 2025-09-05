-- Add EMA-5 indicator to daily_equity_technicals table
-- This completes the EMA indicator set and enables full EMA-5 integration

BEGIN;

-- Step 1: Add ema_5 column to daily_equity_technicals table
ALTER TABLE daily_equity_technicals 
ADD COLUMN IF NOT EXISTS ema_5 DECIMAL(10, 3);

-- Step 2: Create function to calculate EMA-5 from existing close_price data
CREATE OR REPLACE FUNCTION calculate_ema5_backfill() 
RETURNS INTEGER AS $$
DECLARE
    symbol_record RECORD;
    price_record RECORD;
    ema5_value DECIMAL(10, 3);
    alpha DECIMAL(10, 8) := 2.0 / (5 + 1); -- EMA smoothing factor for 5-period
    records_updated INTEGER := 0;
BEGIN
    -- Loop through each symbol
    FOR symbol_record IN 
        SELECT DISTINCT symbol FROM daily_equity_technicals 
        WHERE close_price IS NOT NULL 
        ORDER BY symbol
    LOOP
        ema5_value := NULL;
        
        -- Loop through prices for this symbol in chronological order
        FOR price_record IN
            SELECT id, close_price, trade_date
            FROM daily_equity_technicals 
            WHERE symbol = symbol_record.symbol 
              AND close_price IS NOT NULL
            ORDER BY trade_date ASC
        LOOP
            -- Initialize EMA with first price or calculate next EMA value
            IF ema5_value IS NULL THEN
                ema5_value := price_record.close_price;
            ELSE
                ema5_value := (price_record.close_price * alpha) + (ema5_value * (1 - alpha));
            END IF;
            
            -- Update the record with calculated EMA-5
            UPDATE daily_equity_technicals 
            SET ema_5 = ema5_value
            WHERE id = price_record.id;
            
            records_updated := records_updated + 1;
        END LOOP;
    END LOOP;
    
    RETURN records_updated;
END;
$$ LANGUAGE plpgsql;

-- Step 3: Backfill EMA-5 values for existing data
SELECT calculate_ema5_backfill() as records_updated;

-- Step 4: Add index for EMA-5 queries
CREATE INDEX IF NOT EXISTS idx_daily_technicals_ema5 ON daily_equity_technicals(symbol, ema_5) 
WHERE ema_5 IS NOT NULL;

-- Step 5: Update the technical analysis view to include EMA-5
CREATE OR REPLACE VIEW technical_analysis_view AS
SELECT 
    det.*,
    -- EMA Analysis
    CASE 
        WHEN det.close_price > det.ema_5 THEN 'Above EMA-5'
        WHEN det.close_price < det.ema_5 THEN 'Below EMA-5'
        ELSE 'At EMA-5'
    END as ema5_position,
    
    -- EMA Alignment Analysis
    CASE 
        WHEN det.ema_5 > det.ema_12 AND det.ema_12 > det.ema_26 AND det.ema_26 > det.ema_50 THEN 'Bullish Alignment'
        WHEN det.ema_5 < det.ema_12 AND det.ema_12 < det.ema_26 AND det.ema_26 < det.ema_50 THEN 'Bearish Alignment'
        ELSE 'Mixed Alignment'
    END as ema_alignment,
    
    -- Short-term Trend (EMA-5 vs EMA-12)
    CASE 
        WHEN det.ema_5 > det.ema_12 THEN 'Short-term Bullish'
        WHEN det.ema_5 < det.ema_12 THEN 'Short-term Bearish'
        ELSE 'Short-term Neutral'
    END as short_term_trend
    
FROM daily_equity_technicals det
WHERE det.ema_5 IS NOT NULL;

-- Step 6: Create helper function for EMA-5 signals
CREATE OR REPLACE FUNCTION get_ema5_signal(
    current_price DECIMAL,
    ema5 DECIMAL,
    ema12 DECIMAL,
    prev_ema5 DECIMAL DEFAULT NULL
) RETURNS TEXT AS $$
BEGIN
    IF current_price IS NULL OR ema5 IS NULL THEN
        RETURN 'No Signal';
    END IF;
    
    -- Strong bullish: Price above EMA-5 and EMA-5 rising
    IF current_price > ema5 AND (prev_ema5 IS NULL OR ema5 > prev_ema5) THEN
        IF ema12 IS NOT NULL AND ema5 > ema12 THEN
            RETURN 'Strong Bullish';
        ELSE
            RETURN 'Bullish';
        END IF;
    END IF;
    
    -- Strong bearish: Price below EMA-5 and EMA-5 falling
    IF current_price < ema5 AND (prev_ema5 IS NULL OR ema5 < prev_ema5) THEN
        IF ema12 IS NOT NULL AND ema5 < ema12 THEN
            RETURN 'Strong Bearish';
        ELSE
            RETURN 'Bearish';
        END IF;
    END IF;
    
    RETURN 'Neutral';
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Step 7: Verification queries
SELECT 
    'EMA-5 Integration Summary' as description,
    COUNT(*) as total_records,
    COUNT(ema_5) as ema5_populated,
    ROUND(AVG(ema_5), 2) as avg_ema5,
    MIN(trade_date) as earliest_date,
    MAX(trade_date) as latest_date
FROM daily_equity_technicals;

-- Check EMA-5 vs current price relationships
SELECT 
    symbol,
    trade_date,
    close_price,
    ema_5,
    ROUND((close_price - ema_5) / ema_5 * 100, 2) as pct_above_ema5,
    get_ema5_signal(close_price, ema_5, ema_12) as ema5_signal
FROM daily_equity_technicals 
WHERE ema_5 IS NOT NULL 
  AND trade_date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY symbol, trade_date DESC
LIMIT 20;

-- Drop the temporary backfill function (cleanup)
DROP FUNCTION IF EXISTS calculate_ema5_backfill();

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'EMA-5 indicator successfully added to daily_equity_technicals table';
    RAISE NOTICE 'Backfilled EMA-5 values for all existing close_price data';
    RAISE NOTICE 'Created EMA-5 analysis functions and views';
    RAISE NOTICE 'EMA-5 is now available for technical analysis and strategy development';
END $$;

COMMIT;