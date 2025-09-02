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
('BBRK1', 'BBRK', 'B', 1, 'Buy • Breakout (Weak)', 'Minimal break above 20D-H/UB with light volume', 'breakout'),
('BBRK2', 'BBRK', 'B', 2, 'Buy • Breakout (Very Light)', 'Small break above resistance with some momentum', 'breakout'),
('BBRK3', 'BBRK', 'B', 3, 'Buy • Breakout (Light)', 'Clear break above 20D-H with moderate volume', 'breakout'),
('BBRK4', 'BBRK', 'B', 4, 'Buy • Breakout (Moderate-)', 'Solid break above resistance with good momentum', 'breakout'),
('BBRK5', 'BBRK', 'B', 5, 'Buy • Breakout (Moderate)', 'Break above 20D-H/UB with momentum & volume confirm', 'breakout'),
('BBRK6', 'BBRK', 'B', 6, 'Buy • Breakout (Moderate+)', 'Strong break with high volume and technical confirm', 'breakout'),
('BBRK7', 'BBRK', 'B', 7, 'Buy • Breakout (Strong)', 'Powerful break above resistance with conviction', 'breakout'),
('BBRK8', 'BBRK', 'B', 8, 'Buy • Breakout (Very Strong)', 'Explosive breakout with massive volume surge', 'breakout'),
('BBRK9', 'BBRK', 'B', 9, 'Buy • Breakout (Extreme)', 'Historic breakout with all technical indicators aligned', 'breakout'),

-- BOSR: Buy • Oversold Reclaim (Strength 1-9)
('BOSR1', 'BOSR', 'B', 1, 'Buy • Oversold Reclaim (Weak)', 'Minor RSI recovery from oversold territory', 'mean-reversion'),
('BOSR2', 'BOSR', 'B', 2, 'Buy • Oversold Reclaim (Very Light)', 'RSI up-cross with slight price recovery', 'mean-reversion'),
('BOSR3', 'BOSR', 'B', 3, 'Buy • Oversold Reclaim (Light)', 'RSI/WMSR up-cross with price stabilization', 'mean-reversion'),
('BOSR4', 'BOSR', 'B', 4, 'Buy • Oversold Reclaim (Moderate-)', 'Oversold bounce with EMA20 approach', 'mean-reversion'),
('BOSR5', 'BOSR', 'B', 5, 'Buy • Oversold Reclaim (Moderate)', 'RSI/WMSR up-cross, EMA20 reclaim, vol confirm', 'mean-reversion'),
('BOSR6', 'BOSR', 'B', 6, 'Buy • Oversold Reclaim (Moderate+)', 'Strong oversold recovery with momentum build', 'mean-reversion'),
('BOSR7', 'BOSR', 'B', 7, 'Buy • Oversold Reclaim (Strong)', 'Powerful reversal from oversold with volume', 'mean-reversion'),
('BOSR8', 'BOSR', 'B', 8, 'Buy • Oversold Reclaim (Very Strong)', 'Explosive recovery from deep oversold levels', 'mean-reversion'),
('BOSR9', 'BOSR', 'B', 9, 'Buy • Oversold Reclaim (Extreme)', 'Historic oversold reversal with all confirm', 'mean-reversion'),

-- BMAC: Buy • MA Bullish Crossover (Strength 1-9)
('BMAC1', 'BMAC', 'B', 1, 'Buy • MA Crossover (Weak)', 'Minimal EMA20/EMA50 bullish crossover', 'trend'),
('BMAC2', 'BMAC', 'B', 2, 'Buy • MA Crossover (Very Light)', 'EMA crossover with slight momentum', 'trend'),
('BMAC3', 'BMAC', 'B', 3, 'Buy • MA Crossover (Light)', 'Clear EMA20 above EMA50 crossover', 'trend'),
('BMAC4', 'BMAC', 'B', 4, 'Buy • MA Crossover (Moderate-)', 'EMA crossover with price momentum', 'trend'),
('BMAC5', 'BMAC', 'B', 5, 'Buy • MA Crossover (Moderate)', 'EMA20 crosses above EMA50 with momentum', 'trend'),
('BMAC6', 'BMAC', 'B', 6, 'Buy • MA Crossover (Moderate+)', 'Strong MA crossover with volume confirm', 'trend'),
('BMAC7', 'BMAC', 'B', 7, 'Buy • MA Crossover (Strong)', 'Powerful trend initiation via MA crossover', 'trend'),
('BMAC8', 'BMAC', 'B', 8, 'Buy • MA Crossover (Very Strong)', 'Explosive trend start with all MA aligned', 'trend'),
('BMAC9', 'BMAC', 'B', 9, 'Buy • MA Crossover (Extreme)', 'Perfect trend initiation setup', 'trend'),

-- BBOL: Buy • Bollinger Bounce (Strength 1-9)
('BBOL1', 'BBOL', 'B', 1, 'Buy • Bollinger Bounce (Weak)', 'Minor bounce from lower Bollinger Band', 'mean-reversion'),
('BBOL2', 'BBOL', 'B', 2, 'Buy • Bollinger Bounce (Very Light)', 'Price recovery from BB lower band', 'mean-reversion'),
('BBOL3', 'BBOL', 'B', 3, 'Buy • Bollinger Bounce (Light)', 'Clear bounce off lower Bollinger with momentum', 'mean-reversion'),
('BBOL4', 'BBOL', 'B', 4, 'Buy • Bollinger Bounce (Moderate-)', 'Solid bounce with technical confirmation', 'mean-reversion'),
('BBOL5', 'BBOL', 'B', 5, 'Buy • Bollinger Bounce (Moderate)', 'Close re-enters from LB with momentum', 'mean-reversion'),
('BBOL6', 'BBOL', 'B', 6, 'Buy • Bollinger Bounce (Moderate+)', 'Strong mean reversion with volume', 'mean-reversion'),
('BBOL7', 'BBOL', 'B', 7, 'Buy • Bollinger Bounce (Strong)', 'Powerful bounce with conviction', 'mean-reversion'),
('BBOL8', 'BBOL', 'B', 8, 'Buy • Bollinger Bounce (Very Strong)', 'Explosive recovery from BB extremes', 'mean-reversion'),
('BBOL9', 'BBOL', 'B', 9, 'Buy • Bollinger Bounce (Extreme)', 'Perfect mean reversion setup', 'mean-reversion'),

-- BDIV: Buy • Bullish Divergence (Strength 1-9)
('BDIV1', 'BDIV', 'B', 1, 'Buy • Bullish Divergence (Weak)', 'Minor bullish divergence in indicators', 'divergence'),
('BDIV2', 'BDIV', 'B', 2, 'Buy • Bullish Divergence (Very Light)', 'Slight indicator divergence vs price', 'divergence'),
('BDIV3', 'BDIV', 'B', 3, 'Buy • Bullish Divergence (Light)', 'Clear RSI/MACD bullish divergence', 'divergence'),
('BDIV4', 'BDIV', 'B', 4, 'Buy • Bullish Divergence (Moderate-)', 'Strong divergence with momentum shift', 'divergence'),
('BDIV5', 'BDIV', 'B', 5, 'Buy • Bullish Divergence (Moderate)', 'Lower low in price, higher low in RSI/MACD', 'divergence'),
('BDIV6', 'BDIV', 'B', 6, 'Buy • Bullish Divergence (Moderate+)', 'Multiple indicator bullish divergence', 'divergence'),
('BDIV7', 'BDIV', 'B', 7, 'Buy • Bullish Divergence (Strong)', 'Powerful reversal divergence pattern', 'divergence'),
('BDIV8', 'BDIV', 'B', 8, 'Buy • Bullish Divergence (Very Strong)', 'Extreme divergence with reversal confirm', 'divergence'),
('BDIV9', 'BDIV', 'B', 9, 'Buy • Bullish Divergence (Extreme)', 'Historic divergence reversal setup', 'divergence'),

-- BSUP: Buy • Support Bounce (Strength 1-9)
('BSUP1', 'BSUP', 'B', 1, 'Buy • Support Bounce (Weak)', 'Minor bounce off support level', 'level'),
('BSUP2', 'BSUP', 'B', 2, 'Buy • Support Bounce (Very Light)', 'Price holds at support with stability', 'level'),
('BSUP3', 'BSUP', 'B', 3, 'Buy • Support Bounce (Light)', 'Clear bounce off key support level', 'level'),
('BSUP4', 'BSUP', 'B', 4, 'Buy • Support Bounce (Moderate-)', 'Solid support hold with momentum', 'level'),
('BSUP5', 'BSUP', 'B', 5, 'Buy • Support Bounce (Moderate)', 'Bounce off support/resume uptrend', 'level'),
('BSUP6', 'BSUP', 'B', 6, 'Buy • Support Bounce (Moderate+)', 'Strong support defense with volume', 'level'),
('BSUP7', 'BSUP', 'B', 7, 'Buy • Support Bounce (Strong)', 'Powerful bounce with conviction', 'level'),
('BSUP8', 'BSUP', 'B', 8, 'Buy • Support Bounce (Very Strong)', 'Explosive recovery from support test', 'level'),
('BSUP9', 'BSUP', 'B', 9, 'Buy • Support Bounce (Extreme)', 'Perfect support bounce setup', 'level');

-- ==============================================
-- SELL STRATEGIES (6 base strategies)
-- ==============================================

-- SBDN: Sell • Breakdown (Strength 1-9)
INSERT INTO strategy(strategy_key, base_strategy, side, strength, name, description, category) VALUES
('SBDN1', 'SBDN', 'S', 1, 'Sell • Breakdown (Weak)', 'Minor break below 20D-L with light volume', 'breakout'),
('SBDN2', 'SBDN', 'S', 2, 'Sell • Breakdown (Very Light)', 'Small break below support with some momentum', 'breakout'),
('SBDN3', 'SBDN', 'S', 3, 'Sell • Breakdown (Light)', 'Clear break below 20D-L with moderate volume', 'breakout'),
('SBDN4', 'SBDN', 'S', 4, 'Sell • Breakdown (Moderate-)', 'Solid break below support with momentum', 'breakout'),
('SBDN5', 'SBDN', 'S', 5, 'Sell • Breakdown (Moderate)', 'Break below 20D-L/LB with momentum & volume', 'breakout'),
('SBDN6', 'SBDN', 'S', 6, 'Sell • Breakdown (Moderate+)', 'Strong breakdown with volume confirmation', 'breakout'),
('SBDN7', 'SBDN', 'S', 7, 'Sell • Breakdown (Strong)', 'Powerful breakdown with conviction', 'breakout'),
('SBDN8', 'SBDN', 'S', 8, 'Sell • Breakdown (Very Strong)', 'Explosive breakdown with massive volume', 'breakout'),
('SBDN9', 'SBDN', 'S', 9, 'Sell • Breakdown (Extreme)', 'Historic breakdown with all indicators aligned', 'breakout'),

-- SOBR: Sell • Overbought Reversal (Strength 1-9)
('SOBR1', 'SOBR', 'S', 1, 'Sell • Overbought Reversal (Weak)', 'Minor RSI decline from overbought', 'mean-reversion'),
('SOBR2', 'SOBR', 'S', 2, 'Sell • Overbought Reversal (Very Light)', 'RSI down-turn with price weakness', 'mean-reversion'),
('SOBR3', 'SOBR', 'S', 3, 'Sell • Overbought Reversal (Light)', 'Overbought reversal with momentum shift', 'mean-reversion'),
('SOBR4', 'SOBR', 'S', 4, 'Sell • Overbought Reversal (Moderate-)', 'Clear overbought peak with reversal', 'mean-reversion'),
('SOBR5', 'SOBR', 'S', 5, 'Sell • Overbought Reversal (Moderate)', 'Overbought downturn with reversal pattern', 'mean-reversion'),
('SOBR6', 'SOBR', 'S', 6, 'Sell • Overbought Reversal (Moderate+)', 'Strong reversal from overbought levels', 'mean-reversion'),
('SOBR7', 'SOBR', 'S', 7, 'Sell • Overbought Reversal (Strong)', 'Powerful reversal with distribution', 'mean-reversion'),
('SOBR8', 'SOBR', 'S', 8, 'Sell • Overbought Reversal (Very Strong)', 'Explosive reversal from extreme levels', 'mean-reversion'),
('SOBR9', 'SOBR', 'S', 9, 'Sell • Overbought Reversal (Extreme)', 'Historic reversal from peak overbought', 'mean-reversion'),

-- SMAC: Sell • MA Bearish Crossover (Strength 1-9)
('SMAC1', 'SMAC', 'S', 1, 'Sell • MA Crossover (Weak)', 'Minimal EMA20/EMA50 bearish crossover', 'trend'),
('SMAC2', 'SMAC', 'S', 2, 'Sell • MA Crossover (Very Light)', 'EMA crossover with slight momentum', 'trend'),
('SMAC3', 'SMAC', 'S', 3, 'Sell • MA Crossover (Light)', 'Clear EMA20 below EMA50 crossover', 'trend'),
('SMAC4', 'SMAC', 'S', 4, 'Sell • MA Crossover (Moderate-)', 'EMA crossover with price momentum', 'trend'),
('SMAC5', 'SMAC', 'S', 5, 'Sell • MA Crossover (Moderate)', 'EMA20 crosses below EMA50 with momentum', 'trend'),
('SMAC6', 'SMAC', 'S', 6, 'Sell • MA Crossover (Moderate+)', 'Strong MA crossover with volume confirm', 'trend'),
('SMAC7', 'SMAC', 'S', 7, 'Sell • MA Crossover (Strong)', 'Powerful trend reversal via MA crossover', 'trend'),
('SMAC8', 'SMAC', 'S', 8, 'Sell • MA Crossover (Very Strong)', 'Explosive downtrend start with MA aligned', 'trend'),
('SMAC9', 'SMAC', 'S', 9, 'Sell • MA Crossover (Extreme)', 'Perfect downtrend initiation setup', 'trend'),

-- SBND: Sell • Bollinger Breakdown (Strength 1-9)
('SBND1', 'SBND', 'S', 1, 'Sell • Bollinger Breakdown (Weak)', 'Minor breakdown from lower Bollinger', 'breakout'),
('SBND2', 'SBND', 'S', 2, 'Sell • Bollinger Breakdown (Very Light)', 'Price exits below BB lower band', 'breakout'),
('SBND3', 'SBND', 'S', 3, 'Sell • Bollinger Breakdown (Light)', 'Clear breakdown below lower Bollinger', 'breakout'),
('SBND4', 'SBND', 'S', 4, 'Sell • Bollinger Breakdown (Moderate-)', 'Solid breakdown with momentum', 'breakout'),
('SBND5', 'SBND', 'S', 5, 'Sell • Bollinger Breakdown (Moderate)', 'Close exits below LB with momentum', 'breakout'),
('SBND6', 'SBND', 'S', 6, 'Sell • Bollinger Breakdown (Moderate+)', 'Strong breakdown with volume', 'breakout'),
('SBND7', 'SBND', 'S', 7, 'Sell • Bollinger Breakdown (Strong)', 'Powerful breakdown with conviction', 'breakout'),
('SBND8', 'SBND', 'S', 8, 'Sell • Bollinger Breakdown (Very Strong)', 'Explosive breakdown from BB extremes', 'breakout'),
('SBND9', 'SBND', 'S', 9, 'Sell • Bollinger Breakdown (Extreme)', 'Historic breakdown setup', 'breakout'),

-- SDIV: Sell • Bearish Divergence (Strength 1-9)
('SDIV1', 'SDIV', 'S', 1, 'Sell • Bearish Divergence (Weak)', 'Minor bearish divergence in indicators', 'divergence'),
('SDIV2', 'SDIV', 'S', 2, 'Sell • Bearish Divergence (Very Light)', 'Slight indicator divergence vs price', 'divergence'),
('SDIV3', 'SDIV', 'S', 3, 'Sell • Bearish Divergence (Light)', 'Clear RSI/MACD bearish divergence', 'divergence'),
('SDIV4', 'SDIV', 'S', 4, 'Sell • Bearish Divergence (Moderate-)', 'Strong divergence with momentum shift', 'divergence'),
('SDIV5', 'SDIV', 'S', 5, 'Sell • Bearish Divergence (Moderate)', 'Higher high in price, lower high in RSI/MACD', 'divergence'),
('SDIV6', 'SDIV', 'S', 6, 'Sell • Bearish Divergence (Moderate+)', 'Multiple indicator bearish divergence', 'divergence'),
('SDIV7', 'SDIV', 'S', 7, 'Sell • Bearish Divergence (Strong)', 'Powerful reversal divergence pattern', 'divergence'),
('SDIV8', 'SDIV', 'S', 8, 'Sell • Bearish Divergence (Very Strong)', 'Extreme divergence with reversal confirm', 'divergence'),
('SDIV9', 'SDIV', 'S', 9, 'Sell • Bearish Divergence (Extreme)', 'Historic divergence reversal setup', 'divergence'),

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