-- Strategic Signal Strategy Catalog Population
-- Creates all 12 base strategies with strength variants 1-9
-- Total: 108 strategy combinations (12 base × 9 strengths)

-- ==============================================
-- Strategy Catalog Data Population
-- ==============================================

-- Clear existing strategies if any
DELETE FROM strategy WHERE strategy_key SIMILAR TO '[BS][A-Z]{3}[1-9]';

-- ==============================================
-- BUY STRATEGIES (6 base strategies)
-- ==============================================

-- BBRK: Buy • Breakout (Strength 1-9)
INSERT INTO strategy(strategy_key, base_strategy, side, strength, name, description, category) VALUES
('BBRK1', 'BBRK', 'B', 1, 'Buy • Breakout (Weak)', 'Close crosses above Bollinger Upper (20,2σ)', 'breakout'),
('BBRK2', 'BBRK', 'B', 2, 'Buy • Breakout (Very Light)', 'BBRK1 + Volume ≥ 1.0× VolSMA20', 'breakout'),
('BBRK3', 'BBRK', 'B', 3, 'Buy • Breakout (Light)', 'BBRK2 + EMA5 > EMA12 + Close > SMA20', 'breakout'),
('BBRK4', 'BBRK', 'B', 4, 'Buy • Breakout (Moderate-)', 'BBRK3 + MACD > Signal (bullish cross or above)', 'breakout'),
('BBRK5', 'BBRK', 'B', 5, 'Buy • Breakout (Moderate)', 'BBRK4 + EMA12 > EMA26', 'breakout'),
('BBRK6', 'BBRK', 'B', 6, 'Buy • Breakout (Moderate+)', 'BBRK5 + RSI(14) ≥ 55', 'breakout'),
('BBRK7', 'BBRK', 'B', 7, 'Buy • Breakout (Strong)', 'BBRK6 + Close > EMA50 + BBWidth rising ≥3/5 bars', 'breakout'),
('BBRK8', 'BBRK', 'B', 8, 'Buy • Breakout (Very Strong)', 'BBRK7 + MACD > 0 + Volume ≥ 1.3× VolSMA20', 'breakout'),
('BBRK9', 'BBRK', 'B', 9, 'Buy • Breakout (Extreme)', 'BBRK8 + EMA stack + RSI all ≥60 + Volume ≥1.5×', 'breakout'),

-- BOSR: Buy • Oversold Reclaim (Strength 1-9)
('BOSR1', 'BOSR', 'B', 1, 'Buy • Oversold Reclaim (Weak)', 'Close crosses above BB Lower OR RSI(7) crosses up through 30', 'mean-reversion'),
('BOSR2', 'BOSR', 'B', 2, 'Buy • Oversold Reclaim (Very Light)', 'BOSR1 + Close ≥ EMA5', 'mean-reversion'),
('BOSR3', 'BOSR', 'B', 3, 'Buy • Oversold Reclaim (Light)', 'BOSR2 + RSI(14) > 30 + Histogram increasing', 'mean-reversion'),
('BOSR4', 'BOSR', 'B', 4, 'Buy • Oversold Reclaim (Moderate-)', 'BOSR3 + MACD ≥ Signal (bullish)', 'mean-reversion'),
('BOSR5', 'BOSR', 'B', 5, 'Buy • Oversold Reclaim (Moderate)', 'BOSR4 + Close ≥ SMA20 (BB middle)', 'mean-reversion'),
('BOSR6', 'BOSR', 'B', 6, 'Buy • Oversold Reclaim (Moderate+)', 'BOSR5 + EMA12 > EMA26 or fresh cross up today', 'mean-reversion'),
('BOSR7', 'BOSR', 'B', 7, 'Buy • Oversold Reclaim (Strong)', 'BOSR6 + RSI(14) ≥ 50', 'mean-reversion'),
('BOSR8', 'BOSR', 'B', 8, 'Buy • Oversold Reclaim (Very Strong)', 'BOSR7 + Volume ≥ 1.2× VolSMA20 + Close ≥ EMA50', 'mean-reversion'),
('BOSR9', 'BOSR', 'B', 9, 'Buy • Oversold Reclaim (Extreme)', 'BOSR8 + Close ≥ EMA100 + RSI(21) ≥ 55', 'mean-reversion'),

-- BMAC: Buy • MA Bullish Crossover (Strength 1-9)
('BMAC1', 'BMAC', 'B', 1, 'Buy • MA Crossover (Weak)', 'EMA12 crosses above EMA26 today', 'trend'),
('BMAC2', 'BMAC', 'B', 2, 'Buy • MA Crossover (Very Light)', 'BMAC1 + Close ≥ SMA20 + EMA5 ≥ EMA12', 'trend'),
('BMAC3', 'BMAC', 'B', 3, 'Buy • MA Crossover (Light)', 'BMAC2 + MACD > Signal', 'trend'),
('BMAC4', 'BMAC', 'B', 4, 'Buy • MA Crossover (Moderate-)', 'BMAC3 + RSI(14) ≥ 50', 'trend'),
('BMAC5', 'BMAC', 'B', 5, 'Buy • MA Crossover (Moderate)', 'BMAC4 + Close ≥ EMA50', 'trend'),
('BMAC6', 'BMAC', 'B', 6, 'Buy • MA Crossover (Moderate+)', 'BMAC5 + MACD > 0', 'trend'),
('BMAC7', 'BMAC', 'B', 7, 'Buy • MA Crossover (Strong)', 'BMAC6 + Volume ≥ 1.2× VolSMA20', 'trend'),
('BMAC8', 'BMAC', 'B', 8, 'Buy • MA Crossover (Very Strong)', 'BMAC7 + Close ≥ EMA100 + BBWidth rising ≥3/5 bars', 'trend'),
('BMAC9', 'BMAC', 'B', 9, 'Buy • MA Crossover (Extreme)', 'BMAC8 + EMA stack positive + RSI(21) ≥ 55', 'trend'),

-- BBOL: Buy • Bollinger Bounce (Strength 1-9)
('BBOL1', 'BBOL', 'B', 1, 'Buy • Bollinger Bounce (Weak)', 'Intraday low touches/breaks Lower, close above Lower', 'mean-reversion'),
('BBOL2', 'BBOL', 'B', 2, 'Buy • Bollinger Bounce (Very Light)', 'BBOL1 + RSI(7) rising and ≥ 30', 'mean-reversion'),
('BBOL3', 'BBOL', 'B', 3, 'Buy • Bollinger Bounce (Light)', 'BBOL2 + Close ≥ EMA5', 'mean-reversion'),
('BBOL4', 'BBOL', 'B', 4, 'Buy • Bollinger Bounce (Moderate-)', 'BBOL3 + Histogram increasing for ≥2 bars', 'mean-reversion'),
('BBOL5', 'BBOL', 'B', 5, 'Buy • Bollinger Bounce (Moderate)', 'BBOL4 + RSI(14) ≥ 40', 'mean-reversion'),
('BBOL6', 'BBOL', 'B', 6, 'Buy • Bollinger Bounce (Moderate+)', 'BBOL5 + Close ≥ SMA20 (BB middle)', 'mean-reversion'),
('BBOL7', 'BBOL', 'B', 7, 'Buy • Bollinger Bounce (Strong)', 'BBOL6 + Volume ≥ 1.1× VolSMA20', 'mean-reversion'),
('BBOL8', 'BBOL', 'B', 8, 'Buy • Bollinger Bounce (Very Strong)', 'BBOL7 + EMA12 ≥ EMA26', 'mean-reversion'),
('BBOL9', 'BBOL', 'B', 9, 'Buy • Bollinger Bounce (Extreme)', 'BBOL8 + Close ≥ EMA50 + RSI(21) ≥ 50', 'mean-reversion'),

-- BDIV: Buy • Bullish Divergence (Strength 1-9)
('BDIV1', 'BDIV', 'B', 1, 'Buy • Bullish Divergence (Weak)', 'RSI(14) or MACD histogram bullish divergence', 'divergence'),
('BDIV2', 'BDIV', 'B', 2, 'Buy • Bullish Divergence (Very Light)', 'BDIV1 + recent bar interacted with BB Lower', 'divergence'),
('BDIV3', 'BDIV', 'B', 3, 'Buy • Bullish Divergence (Light)', 'BDIV2 + Close ≥ EMA5', 'divergence'),
('BDIV4', 'BDIV', 'B', 4, 'Buy • Bullish Divergence (Moderate-)', 'BDIV3 + RSI(14) crosses up through 40', 'divergence'),
('BDIV5', 'BDIV', 'B', 5, 'Buy • Bullish Divergence (Moderate)', 'BDIV4 + MACD ≥ Signal', 'divergence'),
('BDIV6', 'BDIV', 'B', 6, 'Buy • Bullish Divergence (Moderate+)', 'BDIV5 + Close ≥ SMA20', 'divergence'),
('BDIV7', 'BDIV', 'B', 7, 'Buy • Bullish Divergence (Strong)', 'BDIV6 + Volume ≥ 1.2× VolSMA20', 'divergence'),
('BDIV8', 'BDIV', 'B', 8, 'Buy • Bullish Divergence (Very Strong)', 'BDIV7 + EMA12 ≥ EMA26', 'divergence'),
('BDIV9', 'BDIV', 'B', 9, 'Buy • Bullish Divergence (Extreme)', 'BDIV8 + Close ≥ EMA50 + RSI(21) ≥ 50', 'divergence'),

-- BSUP: Buy • Support Bounce (Strength 1-9)
('BSUP1', 'BSUP', 'B', 1, 'Buy • Support Bounce (Weak)', 'Touch/undercut SMA20/EMA50/EMA100/BB Mid, close above', 'level'),
('BSUP2', 'BSUP', 'B', 2, 'Buy • Support Bounce (Very Light)', 'BSUP1 + RSI(7) rising from below 45', 'level'),
('BSUP3', 'BSUP', 'B', 3, 'Buy • Support Bounce (Light)', 'BSUP2 + Close ≥ EMA5', 'level'),
('BSUP4', 'BSUP', 'B', 4, 'Buy • Support Bounce (Moderate-)', 'BSUP3 + MACD ≥ Signal', 'level'),
('BSUP5', 'BSUP', 'B', 5, 'Buy • Support Bounce (Moderate)', 'BSUP4 + support = EMA50+ (EMA50/EMA100)', 'level'),
('BSUP6', 'BSUP', 'B', 6, 'Buy • Support Bounce (Moderate+)', 'BSUP5 + RSI(14) ≥ 50', 'level'),
('BSUP7', 'BSUP', 'B', 7, 'Buy • Support Bounce (Strong)', 'BSUP6 + Volume ≥ 1.1× VolSMA20', 'level'),
('BSUP8', 'BSUP', 'B', 8, 'Buy • Support Bounce (Very Strong)', 'BSUP7 + EMA12 ≥ EMA26 + Close ≥ SMA20', 'level'),
('BSUP9', 'BSUP', 'B', 9, 'Buy • Support Bounce (Extreme)', 'BSUP8 + Close ≥ EMA100 + EMA stack positive', 'level');

-- ==============================================
-- SELL STRATEGIES (6 base strategies)
-- ==============================================

-- SBDN: Sell • Breakdown (Strength 1-9)
INSERT INTO strategy(strategy_key, base_strategy, side, strength, name, description, category) VALUES
('SBDN1', 'SBDN', 'S', 1, 'Sell • Breakdown (Weak)', 'Close crosses below Bollinger Lower', 'breakout'),
('SBDN2', 'SBDN', 'S', 2, 'Sell • Breakdown (Very Light)', 'SBDN1 + Volume ≥ 1.0× VolSMA20', 'breakout'),
('SBDN3', 'SBDN', 'S', 3, 'Sell • Breakdown (Light)', 'SBDN2 + EMA5 < EMA12 and Close < SMA20', 'breakout'),
('SBDN4', 'SBDN', 'S', 4, 'Sell • Breakdown (Moderate-)', 'SBDN3 + MACD < Signal', 'breakout'),
('SBDN5', 'SBDN', 'S', 5, 'Sell • Breakdown (Moderate)', 'SBDN4 + EMA12 < EMA26', 'breakout'),
('SBDN6', 'SBDN', 'S', 6, 'Sell • Breakdown (Moderate+)', 'SBDN5 + RSI(14) ≤ 45', 'breakout'),
('SBDN7', 'SBDN', 'S', 7, 'Sell • Breakdown (Strong)', 'SBDN6 + Close < EMA50 + BBWidth rising ≥3/5 bars', 'breakout'),
('SBDN8', 'SBDN', 'S', 8, 'Sell • Breakdown (Very Strong)', 'SBDN7 + MACD < 0 + Volume ≥ 1.3× VolSMA20', 'breakout'),
('SBDN9', 'SBDN', 'S', 9, 'Sell • Breakdown (Extreme)', 'SBDN8 + EMA stack bearish + RSI all ≤ 40 + Volume ≥ 1.5×', 'breakout'),

-- SOBR: Sell • Overbought Reversal (Strength 1-9)
('SOBR1', 'SOBR', 'S', 1, 'Sell • Overbought Reversal (Weak)', 'Close rejects BB Upper OR RSI(7) crosses down through 70', 'mean-reversion'),
('SOBR2', 'SOBR', 'S', 2, 'Sell • Overbought Reversal (Very Light)', 'SOBR1 + Close ≤ EMA5', 'mean-reversion'),
('SOBR3', 'SOBR', 'S', 3, 'Sell • Overbought Reversal (Light)', 'SOBR2 + RSI(14) < 70 + Histogram decreasing', 'mean-reversion'),
('SOBR4', 'SOBR', 'S', 4, 'Sell • Overbought Reversal (Moderate-)', 'SOBR3 + MACD ≤ Signal (bearish)', 'mean-reversion'),
('SOBR5', 'SOBR', 'S', 5, 'Sell • Overbought Reversal (Moderate)', 'SOBR4 + Close ≤ SMA20 (BB middle)', 'mean-reversion'),
('SOBR6', 'SOBR', 'S', 6, 'Sell • Overbought Reversal (Moderate+)', 'SOBR5 + EMA12 < EMA26 or fresh cross down today', 'mean-reversion'),
('SOBR7', 'SOBR', 'S', 7, 'Sell • Overbought Reversal (Strong)', 'SOBR6 + RSI(14) ≤ 50', 'mean-reversion'),
('SOBR8', 'SOBR', 'S', 8, 'Sell • Overbought Reversal (Very Strong)', 'SOBR7 + Volume ≥ 1.2× VolSMA20 + Close ≤ EMA50', 'mean-reversion'),
('SOBR9', 'SOBR', 'S', 9, 'Sell • Overbought Reversal (Extreme)', 'SOBR8 + Close ≤ EMA100 + RSI(21) ≤ 45', 'mean-reversion'),

-- SMAC: Sell • MA Bearish Crossover (Strength 1-9)
('SMAC1', 'SMAC', 'S', 1, 'Sell • MA Crossover (Weak)', 'EMA12 crosses below EMA26', 'trend'),
('SMAC2', 'SMAC', 'S', 2, 'Sell • MA Crossover (Very Light)', 'SMAC1 + Close ≤ SMA20 + EMA5 ≤ EMA12', 'trend'),
('SMAC3', 'SMAC', 'S', 3, 'Sell • MA Crossover (Light)', 'SMAC2 + MACD < Signal', 'trend'),
('SMAC4', 'SMAC', 'S', 4, 'Sell • MA Crossover (Moderate-)', 'SMAC3 + RSI(14) ≤ 50', 'trend'),
('SMAC5', 'SMAC', 'S', 5, 'Sell • MA Crossover (Moderate)', 'SMAC4 + Close ≤ EMA50', 'trend'),
('SMAC6', 'SMAC', 'S', 6, 'Sell • MA Crossover (Moderate+)', 'SMAC5 + MACD < 0', 'trend'),
('SMAC7', 'SMAC', 'S', 7, 'Sell • MA Crossover (Strong)', 'SMAC6 + Volume ≥ 1.2× VolSMA20', 'trend'),
('SMAC8', 'SMAC', 'S', 8, 'Sell • MA Crossover (Very Strong)', 'SMAC7 + Close ≤ EMA100 + BBWidth rising ≥3/5 bars', 'trend'),
('SMAC9', 'SMAC', 'S', 9, 'Sell • MA Crossover (Extreme)', 'SMAC8 + EMA stack bearish + RSI(21) ≤ 45', 'trend'),

-- SRES: Sell • Resistance Rejection (Strength 1-9)
('SRES1', 'SRES', 'S', 1, 'Sell • Resistance Rejection (Weak)', 'Touch/overrun resistance from below, close back below', 'level'),
('SRES2', 'SRES', 'S', 2, 'Sell • Resistance Rejection (Very Light)', 'SRES1 + RSI(7) falling from above 55', 'level'),
('SRES3', 'SRES', 'S', 3, 'Sell • Resistance Rejection (Light)', 'SRES2 + Close ≤ EMA5', 'level'),
('SRES4', 'SRES', 'S', 4, 'Sell • Resistance Rejection (Moderate-)', 'SRES3 + MACD ≤ Signal', 'level'),
('SRES5', 'SRES', 'S', 5, 'Sell • Resistance Rejection (Moderate)', 'SRES4 + resistance = EMA50+ (EMA50/EMA100/BB Upper)', 'level'),
('SRES6', 'SRES', 'S', 6, 'Sell • Resistance Rejection (Moderate+)', 'SRES5 + RSI(14) ≤ 50', 'level'),
('SRES7', 'SRES', 'S', 7, 'Sell • Resistance Rejection (Strong)', 'SRES6 + Volume ≥ 1.1× VolSMA20', 'level'),
('SRES8', 'SRES', 'S', 8, 'Sell • Resistance Rejection (Very Strong)', 'SRES7 + EMA12 ≤ EMA26 + Close ≤ SMA20', 'level'),
('SRES9', 'SRES', 'S', 9, 'Sell • Resistance Rejection (Extreme)', 'SRES8 + Close ≤ EMA100 + EMA stack bearish', 'level'),

-- SDIV: Sell • Bearish Divergence (Strength 1-9)
('SDIV1', 'SDIV', 'S', 1, 'Sell • Bearish Divergence (Weak)', 'RSI(14) or MACD histogram bearish divergence', 'divergence'),
('SDIV2', 'SDIV', 'S', 2, 'Sell • Bearish Divergence (Very Light)', 'SDIV1 + recent bar interacted with BB Upper', 'divergence'),
('SDIV3', 'SDIV', 'S', 3, 'Sell • Bearish Divergence (Light)', 'SDIV2 + Close ≤ EMA5', 'divergence'),
('SDIV4', 'SDIV', 'S', 4, 'Sell • Bearish Divergence (Moderate-)', 'SDIV3 + RSI(14) crosses down through 60', 'divergence'),
('SDIV5', 'SDIV', 'S', 5, 'Sell • Bearish Divergence (Moderate)', 'SDIV4 + MACD ≤ Signal', 'divergence'),
('SDIV6', 'SDIV', 'S', 6, 'Sell • Bearish Divergence (Moderate+)', 'SDIV5 + Close ≤ SMA20', 'divergence'),
('SDIV7', 'SDIV', 'S', 7, 'Sell • Bearish Divergence (Strong)', 'SDIV6 + Volume ≥ 1.2× VolSMA20', 'divergence'),
('SDIV8', 'SDIV', 'S', 8, 'Sell • Bearish Divergence (Very Strong)', 'SDIV7 + EMA12 ≤ EMA26', 'divergence'),
('SDIV9', 'SDIV', 'S', 9, 'Sell • Bearish Divergence (Extreme)', 'SDIV8 + Close ≤ EMA50 + RSI(21) ≤ 45', 'divergence'),

-- SRES: Sell • Resistance Rejection (Strength 1-9)
('SRES1', 'SRES', 'S', 1, 'Sell • Resistance Rejection (Weak)', 'Minor rejection at resistance level', 'level'),
('SRES2', 'SRES', 'S', 2, 'Sell • Resistance Rejection (Very Light)', 'Price fails at resistance with weakness', 'level'),
('SRES3', 'SRES', 'S', 3, 'Sell • Resistance Rejection (Light)', 'Clear rejection at key resistance', 'level'),
('SRES4', 'SRES', 'S', 4, 'Sell • Resistance Rejection (Moderate-)', 'Solid resistance rejection with momentum', 'level'),
('SRES5', 'SRES', 'S', 5, 'Sell • Resistance Rejection (Moderate)', 'Fail at resistance with bearish candle', 'level'),
('SRES6', 'SRES', 'S', 6, 'Sell • Resistance Rejection (Moderate+)', 'Strong resistance defense with volume', 'level'),
('SRES7', 'SRES', 'S', 7, 'Sell • Resistance Rejection (Strong)', 'Powerful rejection with distribution', 'level'),
('SRES8', 'SRES', 'S', 8, 'Sell • Resistance Rejection (Very Strong)', 'Explosive rejection from resistance test', 'level'),
('SRES9', 'SRES', 'S', 9, 'Sell • Resistance Rejection (Extreme)', 'Perfect resistance rejection setup', 'level');

-- ==============================================
-- Summary and Verification
-- ==============================================

-- Verify strategy count
SELECT 
    base_strategy,
    side,
    COUNT(*) as strategy_count,
    MIN(strength) as min_strength,
    MAX(strength) as max_strength
FROM strategy 
GROUP BY base_strategy, side 
ORDER BY base_strategy, side;

-- Total strategy count
SELECT 
    'Total Strategies Created' as description,
    COUNT(*) as total_count
FROM strategy;

-- Strategies by category
SELECT 
    category,
    COUNT(*) as strategy_count,
    ARRAY_AGG(DISTINCT base_strategy ORDER BY base_strategy) as base_strategies
FROM strategy 
GROUP BY category 
ORDER BY strategy_count DESC;

SELECT 'Strategy catalog populated successfully with 108 TXYZn combinations (12 base × 9 strengths)' AS status;