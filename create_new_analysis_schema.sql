-- New Simplified Portfolio Analysis Schema (Option 3 - Ultra Simple)
-- Single transaction table approach for maximum simplicity and flexibility

-- Main Portfolio Analysis table
CREATE TABLE portfolio_analyses (
    id SERIAL PRIMARY KEY,
    portfolio_id VARCHAR(50) NOT NULL,
    analysis_name VARCHAR(200) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    start_cash DECIMAL(15,2) NOT NULL DEFAULT 0,
    -- Calculated fields (computed from transactions)
    end_cash DECIMAL(15,2) NULL,
    start_equity_value DECIMAL(15,2) NULL,
    end_equity_value DECIMAL(15,2) NULL,
    start_total_value DECIMAL(15,2) NULL,
    end_total_value DECIMAL(15,2) NULL,
    total_equity_gain_loss DECIMAL(15,2) NULL,
    total_value_gain_loss DECIMAL(15,2) NULL,
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Constraints
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
    UNIQUE(portfolio_id, analysis_name),
    CHECK (end_date >= start_date),
    CHECK (start_cash >= 0)
);

-- Single transaction log table - handles all position and cash changes
CREATE TABLE portfolio_analysis_state_changes (
    id SERIAL PRIMARY KEY,
    analysis_id INT NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,
    quantity_change INT NOT NULL DEFAULT 0,
    price_per_share DECIMAL(10,3) NULL,
    cash_change DECIMAL(15,2) NOT NULL DEFAULT 0,
    transaction_date DATE NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Constraints
    FOREIGN KEY (analysis_id) REFERENCES portfolio_analyses(id) ON DELETE CASCADE,
    CHECK (transaction_type IN ('INITIAL', 'BUY', 'SELL', 'DIVIDEND', 'SPLIT', 'CASH_ADJUSTMENT'))
);

-- Create indexes for performance
CREATE INDEX idx_portfolio_analyses_portfolio ON portfolio_analyses(portfolio_id);
CREATE INDEX idx_portfolio_analyses_dates ON portfolio_analyses(start_date, end_date);
CREATE INDEX idx_state_changes_analysis ON portfolio_analysis_state_changes(analysis_id);
CREATE INDEX idx_state_changes_symbol_date ON portfolio_analysis_state_changes(analysis_id, symbol, transaction_date);
CREATE INDEX idx_state_changes_type ON portfolio_analysis_state_changes(transaction_type);

-- Function to get current position for a symbol in an analysis
CREATE OR REPLACE FUNCTION get_current_position(
    p_analysis_id INT,
    p_symbol VARCHAR(10)
) RETURNS TABLE(
    symbol VARCHAR(10),
    current_quantity INT,
    avg_cost DECIMAL(10,3)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p_symbol,
        COALESCE(SUM(sc.quantity_change), 0)::INT as current_quantity,
        CASE 
            WHEN SUM(sc.quantity_change) > 0 THEN
                ABS(SUM(CASE WHEN sc.quantity_change > 0 THEN sc.cash_change ELSE 0 END) / 
                    SUM(CASE WHEN sc.quantity_change > 0 THEN sc.quantity_change ELSE 0 END))
            ELSE 0
        END::DECIMAL(10,3) as avg_cost
    FROM portfolio_analysis_state_changes sc
    WHERE sc.analysis_id = p_analysis_id 
      AND sc.symbol = p_symbol;
END;
$$ LANGUAGE plpgsql;

-- Function to get current cash position for an analysis
CREATE OR REPLACE FUNCTION get_current_cash(p_analysis_id INT) 
RETURNS DECIMAL(15,2) AS $$
BEGIN
    RETURN (
        SELECT 
            pa.start_cash + COALESCE(SUM(sc.cash_change), 0)
        FROM portfolio_analyses pa
        LEFT JOIN portfolio_analysis_state_changes sc ON pa.id = sc.analysis_id
        WHERE pa.id = p_analysis_id
        GROUP BY pa.start_cash
    );
END;
$$ LANGUAGE plpgsql;

-- Function to validate transactions (quantity and date range)
CREATE OR REPLACE FUNCTION validate_transaction() 
RETURNS TRIGGER AS $$
DECLARE
    current_qty INT;
    new_qty INT;
    analysis_start_date DATE;
    analysis_end_date DATE;
BEGIN
    -- Get analysis date range
    SELECT start_date, end_date 
    INTO analysis_start_date, analysis_end_date
    FROM portfolio_analyses 
    WHERE id = NEW.analysis_id;
    
    -- Validate transaction date (skip for INITIAL transactions)
    IF NEW.transaction_type != 'INITIAL' THEN
        IF NEW.transaction_date < analysis_start_date OR NEW.transaction_date > analysis_end_date THEN
            RAISE EXCEPTION 'Transaction date % must be between analysis start date % and end date %', 
                NEW.transaction_date, analysis_start_date, analysis_end_date;
        END IF;
    END IF;
    
    -- Skip quantity validation for INITIAL transactions
    IF NEW.transaction_type = 'INITIAL' THEN
        RETURN NEW;
    END IF;
    
    -- Get current quantity for this symbol
    SELECT COALESCE(SUM(quantity_change), 0) 
    INTO current_qty
    FROM portfolio_analysis_state_changes 
    WHERE analysis_id = NEW.analysis_id AND symbol = NEW.symbol;
    
    -- Calculate new quantity after this change
    new_qty := current_qty + NEW.quantity_change;
    
    -- Ensure quantity doesn't go negative
    IF new_qty < 0 THEN
        RAISE EXCEPTION 'Transaction would result in negative quantity for symbol %. Current: %, Change: %, Result: %', 
            NEW.symbol, current_qty, NEW.quantity_change, new_qty;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to validate transactions
CREATE TRIGGER trigger_validate_transaction
    BEFORE INSERT OR UPDATE ON portfolio_analysis_state_changes
    FOR EACH ROW
    EXECUTE FUNCTION validate_transaction();

-- Function to update calculated fields in portfolio_analyses
CREATE OR REPLACE FUNCTION update_analysis_calculations(p_analysis_id INT)
RETURNS VOID AS $$
DECLARE
    v_start_equity DECIMAL(15,2) := 0;
    v_end_equity DECIMAL(15,2) := 0;
    v_end_cash DECIMAL(15,2) := 0;
    v_start_total DECIMAL(15,2) := 0;
    v_end_total DECIMAL(15,2) := 0;
BEGIN
    -- Calculate start equity value (from INITIAL transactions)
    SELECT COALESCE(SUM(ABS(sc.cash_change)), 0)
    INTO v_start_equity
    FROM portfolio_analysis_state_changes sc
    WHERE sc.analysis_id = p_analysis_id 
      AND sc.transaction_type = 'INITIAL'
      AND sc.quantity_change > 0;
    
    -- Get current cash position
    v_end_cash := get_current_cash(p_analysis_id);
    
    -- Calculate end equity value (current positions * current prices)
    -- Note: This would need current price data - for now, we'll use a placeholder
    -- In real implementation, this would join with current price data
    v_end_equity := v_start_equity; -- Placeholder - would calculate from current positions and prices
    
    -- Calculate totals
    SELECT start_cash INTO v_start_total FROM portfolio_analyses WHERE id = p_analysis_id;
    v_start_total := v_start_total + v_start_equity;
    v_end_total := v_end_cash + v_end_equity;
    
    -- Update the analysis record
    UPDATE portfolio_analyses SET
        start_equity_value = v_start_equity,
        end_equity_value = v_end_equity,
        end_cash = v_end_cash,
        start_total_value = v_start_total,
        end_total_value = v_end_total,
        total_equity_gain_loss = v_end_equity - v_start_equity,
        total_value_gain_loss = v_end_total - v_start_total,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = p_analysis_id;
END;
$$ LANGUAGE plpgsql;

-- Create view for easy analysis summary
CREATE OR REPLACE VIEW portfolio_analysis_summary AS
SELECT 
    pa.id,
    pa.portfolio_id,
    p.name as portfolio_name,
    pa.analysis_name,
    pa.start_date,
    pa.end_date,
    pa.start_cash,
    pa.end_cash,
    pa.start_equity_value,
    pa.end_equity_value,
    pa.start_total_value,
    pa.end_total_value,
    pa.total_equity_gain_loss,
    pa.total_value_gain_loss,
    CASE 
        WHEN pa.start_total_value > 0 THEN 
            ROUND((pa.total_value_gain_loss / pa.start_total_value * 100), 2)
        ELSE 0 
    END as total_return_percentage,
    pa.created_at,
    pa.updated_at
FROM portfolio_analyses pa
LEFT JOIN portfolios p ON pa.portfolio_id = p.portfolio_id
ORDER BY pa.created_at DESC;

SELECT 'New simplified portfolio analysis schema created successfully' AS status;