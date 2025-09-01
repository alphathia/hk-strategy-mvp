-- Enhanced HK Strategy Database with Multi-Portfolio Support

-- Create portfolios table to store portfolio metadata
CREATE TABLE IF NOT EXISTS portfolios (
    id SERIAL PRIMARY KEY,
    portfolio_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Update portfolio_positions table to include portfolio_id
DROP TABLE IF EXISTS portfolio_positions CASCADE;

CREATE TABLE portfolio_positions (
    id SERIAL PRIMARY KEY,
    portfolio_id VARCHAR(50) NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    company_name VARCHAR(200),
    quantity INTEGER NOT NULL DEFAULT 0,
    avg_cost DECIMAL(10, 3) NOT NULL DEFAULT 0,
    current_price DECIMAL(10, 3) DEFAULT 0,
    market_value DECIMAL(12, 2) GENERATED ALWAYS AS (quantity * current_price) STORED,
    unrealized_pnl DECIMAL(12, 2) GENERATED ALWAYS AS ((current_price - avg_cost) * quantity) STORED,
    sector VARCHAR(50),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(portfolio_id, symbol),
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(portfolio_id) ON DELETE CASCADE
);

-- Update trading_signals table to include portfolio_id
DROP TABLE IF EXISTS trading_signals CASCADE;

CREATE TABLE trading_signals (
    id SERIAL PRIMARY KEY,
    portfolio_id VARCHAR(50) NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    signal_type VARCHAR(1) NOT NULL CHECK (signal_type IN ('A', 'B', 'C', 'D')),
    signal_strength DECIMAL(3, 2) NOT NULL DEFAULT 0.5,
    price DECIMAL(10, 3) NOT NULL,
    volume INTEGER DEFAULT 0,
    rsi DECIMAL(5, 2),
    ma_5 DECIMAL(10, 3),
    ma_20 DECIMAL(10, 3),
    ma_50 DECIMAL(10, 3),
    bollinger_upper DECIMAL(10, 3),
    bollinger_lower DECIMAL(10, 3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (portfolio_id, symbol) REFERENCES portfolio_positions(portfolio_id, symbol) ON DELETE CASCADE
);

-- Update price_history table to include portfolio_id
DROP TABLE IF EXISTS price_history CASCADE;

CREATE TABLE price_history (
    id SERIAL PRIMARY KEY,
    portfolio_id VARCHAR(50) NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    price DECIMAL(10, 3) NOT NULL,
    volume INTEGER DEFAULT 0,
    high DECIMAL(10, 3),
    low DECIMAL(10, 3),
    open_price DECIMAL(10, 3),
    close_price DECIMAL(10, 3),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (portfolio_id, symbol) REFERENCES portfolio_positions(portfolio_id, symbol) ON DELETE CASCADE
);

-- Insert portfolio metadata
INSERT INTO portfolios (portfolio_id, name, description) VALUES
('HKEX_Base', 'HKEX Base Portfolio', 'Primary Hong Kong equity holdings from original strategy')
ON CONFLICT (portfolio_id) DO NOTHING;

-- Insert HKEX_Base portfolio positions (from original init.sql)
INSERT INTO portfolio_positions (portfolio_id, symbol, company_name, quantity, avg_cost, current_price, sector) VALUES
('HKEX_Base', '0005.HK', 'HSBC Holdings plc', 13428, 38.50, 39.75, 'Financials'),
('HKEX_Base', '0316.HK', 'Orient Overseas', 100, 95.00, 98.20, 'Other'),
('HKEX_Base', '0388.HK', 'Hong Kong Exchanges', 300, 280.00, 285.50, 'Financials'),
('HKEX_Base', '0700.HK', 'Tencent Holdings Ltd', 3100, 320.50, 315.20, 'Tech'),
('HKEX_Base', '0823.HK', 'Link REIT', 1300, 42.80, 44.15, 'REIT'),
('HKEX_Base', '0857.HK', 'PetroChina Company Ltd', 0, 7.50, 7.80, 'Energy'),
('HKEX_Base', '0939.HK', 'China Construction Bank', 26700, 5.45, 5.52, 'Financials'),
('HKEX_Base', '1810.HK', 'Xiaomi Corporation', 2000, 12.30, 13.45, 'Tech'),
('HKEX_Base', '2888.HK', 'Standard Chartered PLC', 348, 145.00, 148.20, 'Financials'),
('HKEX_Base', '3690.HK', 'Meituan', 340, 95.00, 98.50, 'Tech'),
('HKEX_Base', '9618.HK', 'JD.com', 133, 125.00, 130.10, 'Tech'),
('HKEX_Base', '9988.HK', 'Alibaba Group', 2000, 115.00, 118.75, 'Tech')
ON CONFLICT (portfolio_id, symbol) DO NOTHING;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_portfolios_id ON portfolios(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_positions_portfolio_symbol ON portfolio_positions(portfolio_id, symbol);
CREATE INDEX IF NOT EXISTS idx_trading_signals_portfolio_symbol ON trading_signals(portfolio_id, symbol);
CREATE INDEX IF NOT EXISTS idx_trading_signals_created ON trading_signals(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_price_history_portfolio_symbol_time ON price_history(portfolio_id, symbol, timestamp DESC);

-- Create view for easy portfolio summary
CREATE OR REPLACE VIEW portfolio_summary AS
SELECT 
    p.portfolio_id,
    p.name,
    p.description,
    COUNT(pp.symbol) as total_positions,
    COUNT(CASE WHEN pp.quantity > 0 THEN 1 END) as active_positions,
    SUM(pp.market_value) as total_market_value,
    SUM(pp.avg_cost * pp.quantity) as total_cost,
    SUM(pp.unrealized_pnl) as total_unrealized_pnl,
    p.updated_at
FROM portfolios p
LEFT JOIN portfolio_positions pp ON p.portfolio_id = pp.portfolio_id
GROUP BY p.portfolio_id, p.name, p.description, p.updated_at;