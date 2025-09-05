-- Add daily_equity_technicals table for comprehensive technical analysis
-- This table supports the Equity Strategy Analysis dashboard

BEGIN;

-- Create daily_equity_technicals table if it doesn't exist
CREATE TABLE IF NOT EXISTS daily_equity_technicals (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    
    -- OHLCV Data
    open_price DECIMAL(10, 3),
    high_price DECIMAL(10, 3), 
    low_price DECIMAL(10, 3),
    close_price DECIMAL(10, 3),
    volume BIGINT,
    
    -- RSI Indicators
    rsi_7 DECIMAL(5, 2),
    rsi_14 DECIMAL(5, 2),
    rsi_21 DECIMAL(5, 2),
    
    -- MACD Indicators  
    macd DECIMAL(8, 4),
    macd_signal DECIMAL(8, 4),
    macd_histogram DECIMAL(8, 4),
    
    -- Moving Averages
    sma_20 DECIMAL(10, 3),
    ema_12 DECIMAL(10, 3),
    ema_26 DECIMAL(10, 3),
    ema_50 DECIMAL(10, 3),
    ema_100 DECIMAL(10, 3),
    
    -- Bollinger Bands (standardized naming)
    bollinger_upper DECIMAL(10, 3),
    bollinger_middle DECIMAL(10, 3),  -- 20-day SMA
    bollinger_lower DECIMAL(10, 3),
    bollinger_width DECIMAL(8, 4),    -- (Upper - Lower) / Middle
    bollinger_percent_b DECIMAL(6, 4), -- %B indicator: (Price - Lower) / (Upper - Lower)
    
    -- Volume Indicators
    volume_sma_20 BIGINT,
    volume_ratio DECIMAL(6, 3),       -- Current volume / 20-day avg volume
    
    -- Additional Technical Indicators
    atr_14 DECIMAL(8, 4),             -- Average True Range
    stochastic_k DECIMAL(5, 2),       -- Stochastic %K
    stochastic_d DECIMAL(5, 2),       -- Stochastic %D
    williams_r DECIMAL(6, 2),         -- Williams %R
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(symbol, trade_date),
    FOREIGN KEY (symbol) REFERENCES portfolio_positions(symbol) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_daily_technicals_symbol_date ON daily_equity_technicals(symbol, trade_date DESC);
CREATE INDEX IF NOT EXISTS idx_daily_technicals_date ON daily_equity_technicals(trade_date DESC);
CREATE INDEX IF NOT EXISTS idx_daily_technicals_symbol ON daily_equity_technicals(symbol);

-- Create trigger for updated_at timestamp
CREATE OR REPLACE FUNCTION update_daily_technicals_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_daily_technicals_updated_at
    BEFORE UPDATE ON daily_equity_technicals
    FOR EACH ROW
    EXECUTE FUNCTION update_daily_technicals_updated_at();

-- Migrate existing Bollinger data from trading_signals if it exists
-- This handles backward compatibility
INSERT INTO daily_equity_technicals (
    symbol, trade_date, close_price, bollinger_upper, bollinger_lower
)
SELECT DISTINCT
    symbol,
    created_at::date as trade_date,
    price as close_price,
    bollinger_upper,
    bollinger_lower
FROM trading_signals 
WHERE bollinger_upper IS NOT NULL 
  AND bollinger_lower IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM daily_equity_technicals det 
      WHERE det.symbol = trading_signals.symbol 
      AND det.trade_date = trading_signals.created_at::date
  )
ON CONFLICT (symbol, trade_date) DO NOTHING;

-- Create helper function to calculate Bollinger %B
CREATE OR REPLACE FUNCTION calculate_bollinger_percent_b(
    price DECIMAL, 
    bb_upper DECIMAL, 
    bb_lower DECIMAL
) RETURNS DECIMAL AS $$
BEGIN
    IF bb_upper IS NULL OR bb_lower IS NULL OR price IS NULL THEN
        RETURN NULL;
    END IF;
    
    IF bb_upper = bb_lower THEN
        RETURN 0.5; -- Neutral when bands are flat
    END IF;
    
    RETURN (price - bb_lower) / (bb_upper - bb_lower);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Create helper function to calculate Bollinger Band Width
CREATE OR REPLACE FUNCTION calculate_bollinger_width(
    bb_upper DECIMAL,
    bb_lower DECIMAL, 
    bb_middle DECIMAL
) RETURNS DECIMAL AS $$
BEGIN
    IF bb_upper IS NULL OR bb_lower IS NULL OR bb_middle IS NULL THEN
        RETURN NULL;
    END IF;
    
    IF bb_middle = 0 THEN
        RETURN NULL;
    END IF;
    
    RETURN (bb_upper - bb_lower) / bb_middle;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Create view for Bollinger analysis
CREATE OR REPLACE VIEW bollinger_analysis_view AS
SELECT 
    det.*,
    calculate_bollinger_percent_b(det.close_price, det.bollinger_upper, det.bollinger_lower) as calculated_percent_b,
    calculate_bollinger_width(det.bollinger_upper, det.bollinger_lower, det.bollinger_middle) as calculated_width,
    CASE 
        WHEN det.close_price > det.bollinger_upper THEN 'Above Upper Band'
        WHEN det.close_price < det.bollinger_lower THEN 'Below Lower Band'  
        WHEN det.close_price > det.bollinger_middle THEN 'Above Middle Band'
        ELSE 'Below Middle Band'
    END as price_position,
    CASE
        WHEN calculate_bollinger_width(det.bollinger_upper, det.bollinger_lower, det.bollinger_middle) < 0.1 THEN 'Squeeze'
        WHEN calculate_bollinger_width(det.bollinger_upper, det.bollinger_lower, det.bollinger_middle) > 0.25 THEN 'Expansion' 
        ELSE 'Normal'
    END as volatility_state
FROM daily_equity_technicals det
WHERE det.bollinger_upper IS NOT NULL 
  AND det.bollinger_lower IS NOT NULL
  AND det.bollinger_middle IS NOT NULL;

RAISE NOTICE 'Successfully created daily_equity_technicals table with Bollinger Bands support';
RAISE NOTICE 'Migrated existing Bollinger data from trading_signals table';
RAISE NOTICE 'Created helper functions for Bollinger analysis';

COMMIT;