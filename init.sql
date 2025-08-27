-- Initialize HK Strategy Database

CREATE TABLE IF NOT EXISTS portfolio_positions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    company_name VARCHAR(200),
    quantity INTEGER NOT NULL DEFAULT 0,
    avg_cost DECIMAL(10, 3) NOT NULL DEFAULT 0,
    current_price DECIMAL(10, 3) DEFAULT 0,
    market_value DECIMAL(12, 2) GENERATED ALWAYS AS (quantity * current_price) STORED,
    unrealized_pnl DECIMAL(12, 2) GENERATED ALWAYS AS ((current_price - avg_cost) * quantity) STORED,
    sector VARCHAR(50),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol)
);

CREATE TABLE IF NOT EXISTS trading_signals (
    id SERIAL PRIMARY KEY,
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
    FOREIGN KEY (symbol) REFERENCES portfolio_positions(symbol) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS price_history (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    price DECIMAL(10, 3) NOT NULL,
    volume INTEGER DEFAULT 0,
    high DECIMAL(10, 3),
    low DECIMAL(10, 3),
    open_price DECIMAL(10, 3),
    close_price DECIMAL(10, 3),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES portfolio_positions(symbol) ON DELETE CASCADE
);

-- Insert HK equities from strategy watchlist (matching your actual holdings)
INSERT INTO portfolio_positions (symbol, company_name, quantity, avg_cost, current_price, sector) VALUES
('0005.HK', 'HSBC Holdings plc', 13428, 38.50, 39.75, 'Financials'),
('0316.HK', 'Orient Overseas', 100, 95.00, 98.20, 'Other'),
('0388.HK', 'Hong Kong Exchanges', 300, 280.00, 285.50, 'Financials'),
('0700.HK', 'Tencent Holdings Ltd', 3100, 320.50, 315.20, 'Tech'),
('0823.HK', 'Link REIT', 1300, 42.80, 44.15, 'REIT'),
('0857.HK', 'PetroChina Company Ltd', 0, 7.50, 7.80, 'Energy'),
('0939.HK', 'China Construction Bank', 26700, 5.45, 5.52, 'Financials'),
('1810.HK', 'Xiaomi Corporation', 2000, 12.30, 13.45, 'Tech'),
('2888.HK', 'Standard Chartered PLC', 348, 145.00, 148.20, 'Financials'),
('3690.HK', 'Meituan', 340, 95.00, 98.50, 'Tech'),
('9618.HK', 'JD.com', 133, 125.00, 130.10, 'Tech'),
('9988.HK', 'Alibaba Group', 2000, 115.00, 118.75, 'Tech')
ON CONFLICT (symbol) DO NOTHING;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_portfolio_symbol ON portfolio_positions(symbol);
CREATE INDEX IF NOT EXISTS idx_signals_symbol ON trading_signals(symbol);
CREATE INDEX IF NOT EXISTS idx_signals_created ON trading_signals(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_price_symbol_time ON price_history(symbol, timestamp DESC);