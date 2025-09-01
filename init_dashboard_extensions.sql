-- Database Extensions for 6-Dashboard Architecture
-- Supports Portfolio-Analysis-Equity-Strategy and Equity-Strategy Analysis dashboards

-- 1. Strategies Table
CREATE TABLE IF NOT EXISTS strategies (
    id SERIAL PRIMARY KEY,
    strategy_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    strategy_type VARCHAR(50) NOT NULL, -- 'momentum', 'mean_reversion', 'value', 'growth', etc.
    parameters JSONB DEFAULT '{}', -- Strategy configuration parameters
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Insert default strategies
INSERT INTO strategies (strategy_name, description, strategy_type, parameters) VALUES
('Buy & Hold', 'Simple buy and hold strategy', 'passive', '{"rebalance_frequency": "quarterly"}'),
('RSI Mean Reversion', 'Buy when RSI < 30, sell when RSI > 70', 'mean_reversion', '{"rsi_oversold": 30, "rsi_overbought": 70}'),
('Moving Average Crossover', '5-day MA crosses above 20-day MA', 'momentum', '{"short_ma": 5, "long_ma": 20}'),
('Bollinger Bands', 'Buy at lower band, sell at upper band', 'mean_reversion', '{"period": 20, "std_dev": 2}')
ON CONFLICT (strategy_name) DO NOTHING;

-- 2. Portfolio Analysis Equities Table
-- Links specific equities to portfolio analyses with their analysis-specific data
CREATE TABLE IF NOT EXISTS portfolio_analysis_equities (
    id SERIAL PRIMARY KEY,
    portfolio_analysis_id INTEGER NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    avg_cost DECIMAL(10, 3) NOT NULL DEFAULT 0,
    analysis_start_price DECIMAL(10, 3),
    analysis_end_price DECIMAL(10, 3),
    analysis_notes TEXT,
    weight_in_portfolio DECIMAL(5, 4), -- Percentage weight (0.0000 to 1.0000)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (portfolio_analysis_id) REFERENCES portfolio_analyses(id) ON DELETE CASCADE,
    UNIQUE(portfolio_analysis_id, symbol)
);

-- 3. Portfolio Analysis Equity Strategies Table
-- Links strategies to specific equities within portfolio analyses
CREATE TABLE IF NOT EXISTS portfolio_analysis_equity_strategies (
    id SERIAL PRIMARY KEY,
    portfolio_analysis_equity_id INTEGER NOT NULL,
    strategy_id INTEGER NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    parameters_override JSONB DEFAULT '{}', -- Strategy-specific parameter overrides
    performance_metrics JSONB DEFAULT '{}', -- Calculated performance metrics
    total_return DECIMAL(10, 4),
    max_drawdown DECIMAL(10, 4),
    sharpe_ratio DECIMAL(6, 3),
    win_rate DECIMAL(5, 2), -- Percentage of winning trades
    total_trades INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    FOREIGN KEY (portfolio_analysis_equity_id) REFERENCES portfolio_analysis_equities(id) ON DELETE CASCADE,
    FOREIGN KEY (strategy_id) REFERENCES strategies(id) ON DELETE RESTRICT,
    UNIQUE(portfolio_analysis_equity_id, strategy_id)
);

-- 4. Equity Strategy Analyses Table
-- Cross-portfolio equity analysis storage for individual equity performance
CREATE TABLE IF NOT EXISTS equity_strategy_analyses (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    strategy_id INTEGER NOT NULL,
    analysis_name VARCHAR(200) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_price DECIMAL(10, 3),
    final_price DECIMAL(10, 3),
    performance_data JSONB DEFAULT '{}', -- Daily performance, signals, etc.
    total_return DECIMAL(10, 4),
    volatility DECIMAL(10, 4),
    max_drawdown DECIMAL(10, 4),
    sharpe_ratio DECIMAL(6, 3),
    sortino_ratio DECIMAL(6, 3),
    win_rate DECIMAL(5, 2),
    profit_factor DECIMAL(8, 3), -- Gross profit / Gross loss
    total_trades INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_notes TEXT,
    FOREIGN KEY (strategy_id) REFERENCES strategies(id) ON DELETE RESTRICT,
    CONSTRAINT valid_analysis_period CHECK (end_date >= start_date),
    CONSTRAINT max_2_year_analysis CHECK (end_date <= start_date + INTERVAL '2 years')
);

-- 5. Strategy Performance Tracking
-- Track strategy signals and trade executions
CREATE TABLE IF NOT EXISTS strategy_signals (
    id SERIAL PRIMARY KEY,
    equity_strategy_analysis_id INTEGER NOT NULL,
    signal_date DATE NOT NULL,
    signal_type VARCHAR(10) NOT NULL CHECK (signal_type IN ('BUY', 'SELL', 'HOLD')),
    price DECIMAL(10, 3) NOT NULL,
    quantity INTEGER DEFAULT 0,
    signal_strength DECIMAL(3, 2) DEFAULT 0.5, -- 0.0 to 1.0
    technical_indicators JSONB DEFAULT '{}', -- RSI, MA, etc. at signal time
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (equity_strategy_analysis_id) REFERENCES equity_strategy_analyses(id) ON DELETE CASCADE
);

-- 6. Performance Indexes
CREATE INDEX IF NOT EXISTS idx_strategies_type ON strategies(strategy_type, is_active);
CREATE INDEX IF NOT EXISTS idx_strategies_updated ON strategies(updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_portfolio_analysis_equities_analysis ON portfolio_analysis_equities(portfolio_analysis_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_analysis_equities_symbol ON portfolio_analysis_equities(symbol);

CREATE INDEX IF NOT EXISTS idx_portfolio_analysis_equity_strategies_equity ON portfolio_analysis_equity_strategies(portfolio_analysis_equity_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_analysis_equity_strategies_strategy ON portfolio_analysis_equity_strategies(strategy_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_analysis_equity_strategies_performance ON portfolio_analysis_equity_strategies(total_return DESC);

CREATE INDEX IF NOT EXISTS idx_equity_strategy_analyses_symbol ON equity_strategy_analyses(symbol);
CREATE INDEX IF NOT EXISTS idx_equity_strategy_analyses_strategy ON equity_strategy_analyses(strategy_id);
CREATE INDEX IF NOT EXISTS idx_equity_strategy_analyses_dates ON equity_strategy_analyses(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_equity_strategy_analyses_performance ON equity_strategy_analyses(total_return DESC);

CREATE INDEX IF NOT EXISTS idx_strategy_signals_analysis_date ON strategy_signals(equity_strategy_analysis_id, signal_date);
CREATE INDEX IF NOT EXISTS idx_strategy_signals_date_type ON strategy_signals(signal_date DESC, signal_type);

-- 7. Dashboard Summary Views

-- Portfolio Analysis Equity Summary View
CREATE OR REPLACE VIEW portfolio_analysis_equity_summary AS
SELECT 
    pae.id,
    pae.portfolio_analysis_id,
    pa.name as analysis_name,
    pae.symbol,
    pae.quantity,
    pae.avg_cost,
    pae.analysis_start_price,
    pae.analysis_end_price,
    pae.weight_in_portfolio,
    COUNT(paes.id) as strategies_applied,
    MAX(paes.total_return) as best_strategy_return,
    AVG(paes.total_return) as avg_strategy_return,
    pae.created_at
FROM portfolio_analysis_equities pae
LEFT JOIN portfolio_analyses pa ON pae.portfolio_analysis_id = pa.id
LEFT JOIN portfolio_analysis_equity_strategies paes ON pae.id = paes.portfolio_analysis_equity_id
WHERE paes.is_active = TRUE OR paes.id IS NULL
GROUP BY pae.id, pae.portfolio_analysis_id, pa.name, pae.symbol, pae.quantity, 
         pae.avg_cost, pae.analysis_start_price, pae.analysis_end_price, 
         pae.weight_in_portfolio, pae.created_at;

-- Strategy Performance Summary View
CREATE OR REPLACE VIEW strategy_performance_summary AS
SELECT 
    s.id,
    s.strategy_name,
    s.strategy_type,
    COUNT(esa.id) as total_analyses,
    COUNT(DISTINCT esa.symbol) as unique_symbols,
    AVG(esa.total_return) as avg_return,
    AVG(esa.sharpe_ratio) as avg_sharpe_ratio,
    AVG(esa.win_rate) as avg_win_rate,
    AVG(esa.max_drawdown) as avg_max_drawdown,
    SUM(esa.total_trades) as total_trades_across_analyses,
    s.created_at,
    s.updated_at
FROM strategies s
LEFT JOIN equity_strategy_analyses esa ON s.id = esa.strategy_id
GROUP BY s.id, s.strategy_name, s.strategy_type, s.created_at, s.updated_at;

-- Cross-Portfolio Equity Performance View
CREATE OR REPLACE VIEW equity_cross_portfolio_performance AS
SELECT 
    esa.symbol,
    COUNT(DISTINCT esa.strategy_id) as strategies_tested,
    COUNT(esa.id) as total_analyses,
    AVG(esa.total_return) as avg_return_across_strategies,
    MAX(esa.total_return) as best_return,
    MIN(esa.total_return) as worst_return,
    AVG(esa.sharpe_ratio) as avg_sharpe_ratio,
    AVG(esa.volatility) as avg_volatility,
    AVG(esa.max_drawdown) as avg_max_drawdown,
    SUM(esa.total_trades) as total_trades,
    MAX(esa.updated_at) as last_analysis_update
FROM equity_strategy_analyses esa
GROUP BY esa.symbol;

-- Update trigger for strategies table
CREATE OR REPLACE FUNCTION update_strategy_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_strategy_timestamp
    BEFORE UPDATE ON strategies
    FOR EACH ROW
    EXECUTE FUNCTION update_strategy_timestamp();

-- Update trigger for equity_strategy_analyses table
CREATE TRIGGER trigger_update_equity_strategy_analysis_timestamp
    BEFORE UPDATE ON equity_strategy_analyses
    FOR EACH ROW
    EXECUTE FUNCTION update_strategy_timestamp();