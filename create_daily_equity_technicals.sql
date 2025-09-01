-- Daily Equity Technical Indicators Table
-- Stores comprehensive daily technical analysis data for each equity

CREATE TABLE daily_equity_technicals (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    
    -- OHLCV Data
    open_price DECIMAL(10,3) NOT NULL,
    close_price DECIMAL(10,3) NOT NULL, 
    high_price DECIMAL(10,3) NOT NULL,
    low_price DECIMAL(10,3) NOT NULL,
    volume BIGINT DEFAULT 0,
    
    -- Daily Extremes
    day_high DECIMAL(10,3),           -- Day's highest price (same as high_price but kept for clarity)
    day_low DECIMAL(10,3),            -- Day's lowest price (same as low_price but kept for clarity)
    
    -- Historical Extremes (52-week rolling)
    week_52_high DECIMAL(10,3),       -- 52-week rolling high
    week_52_low DECIMAL(10,3),        -- 52-week rolling low
    
    -- Technical Indicators
    rsi_14 DECIMAL(5,2),              -- 14-day RSI (0-100)
    rsi_9 DECIMAL(5,2),               -- 9-day RSI (0-100)
    
    -- Moving Averages
    ema_12 DECIMAL(10,3),             -- 12-day EMA
    ema_26 DECIMAL(10,3),             -- 26-day EMA
    ema_50 DECIMAL(10,3),             -- 50-day EMA
    sma_20 DECIMAL(10,3),             -- 20-day SMA
    sma_50 DECIMAL(10,3),             -- 50-day SMA
    sma_200 DECIMAL(10,3),            -- 200-day SMA
    
    -- Bollinger Bands (20-day, 2 std dev)
    bollinger_upper DECIMAL(10,3),    -- Upper Bollinger Band
    bollinger_middle DECIMAL(10,3),   -- Middle Bollinger Band (SMA 20)
    bollinger_lower DECIMAL(10,3),    -- Lower Bollinger Band
    
    -- MACD Components
    macd DECIMAL(10,6),               -- MACD line (12 EMA - 26 EMA)
    macd_signal DECIMAL(10,6),        -- MACD signal line (9 EMA of MACD)
    macd_histogram DECIMAL(10,6),     -- MACD histogram (MACD - Signal)
    
    -- Volatility Indicators
    atr_14 DECIMAL(10,3),             -- 14-day Average True Range
    
    -- Volume Indicators
    volume_sma_20 BIGINT,             -- 20-day average volume
    volume_ratio DECIMAL(8,4),        -- Current volume / 20-day average volume
    
    -- Price Position Indicators
    price_vs_52w_high DECIMAL(8,4),   -- (Current - 52w low) / (52w high - 52w low)
    price_vs_52w_low DECIMAL(8,4),    -- Distance from 52-week high as percentage
    
    -- Momentum Indicators
    roc_1d DECIMAL(8,4),              -- 1-day rate of change (%)
    roc_5d DECIMAL(8,4),              -- 5-day rate of change (%)
    roc_20d DECIMAL(8,4),             -- 20-day rate of change (%)
    
    -- Support/Resistance Levels
    support_level DECIMAL(10,3),      -- Calculated support level
    resistance_level DECIMAL(10,3),   -- Calculated resistance level
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_symbol_date UNIQUE(symbol, trade_date),
    CONSTRAINT valid_ohlc CHECK (high_price >= low_price AND high_price >= open_price AND high_price >= close_price AND low_price <= open_price AND low_price <= close_price),
    CONSTRAINT valid_volume CHECK (volume >= 0),
    CONSTRAINT valid_rsi CHECK (rsi_14 BETWEEN 0 AND 100 AND rsi_9 BETWEEN 0 AND 100)
);

-- Create indexes for performance
CREATE INDEX idx_daily_technicals_symbol_date ON daily_equity_technicals(symbol, trade_date DESC);
CREATE INDEX idx_daily_technicals_date ON daily_equity_technicals(trade_date DESC);
CREATE INDEX idx_daily_technicals_symbol ON daily_equity_technicals(symbol);
CREATE INDEX idx_daily_technicals_rsi ON daily_equity_technicals(rsi_14);
CREATE INDEX idx_daily_technicals_volume_ratio ON daily_equity_technicals(volume_ratio);

-- Create a view for easy querying of latest technical data
CREATE OR REPLACE VIEW latest_equity_technicals AS
SELECT DISTINCT ON (symbol) *
FROM daily_equity_technicals
ORDER BY symbol, trade_date DESC;

-- Function to calculate technical indicators (placeholder - would be implemented in Python)
CREATE OR REPLACE FUNCTION update_technical_indicators(p_symbol VARCHAR(10), p_trade_date DATE)
RETURNS BOOLEAN AS $$
BEGIN
    -- This would call Python functions to calculate indicators
    -- For now, it's a placeholder that returns true
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Sample data insertion (for testing)
INSERT INTO daily_equity_technicals (
    symbol, trade_date, open_price, close_price, high_price, low_price, volume,
    day_high, day_low, rsi_14, sma_20, sma_50, ema_12, ema_26
) VALUES 
(
    '0700.HK', CURRENT_DATE, 315.0, 318.5, 320.0, 314.5, 15000000,
    320.0, 314.5, 65.5, 316.8, 310.2, 317.2, 312.8
),
(
    '0005.HK', CURRENT_DATE, 39.5, 40.2, 40.5, 39.2, 8500000,
    40.5, 39.2, 58.2, 39.8, 38.9, 40.0, 39.1
)
ON CONFLICT (symbol, trade_date) DO NOTHING;

SELECT 'Daily equity technicals table created successfully' AS status;