# 🔄 Backup Restoration Plan

## 🎯 **EXECUTIVE SUMMARY**

This document provides comprehensive backup restoration procedures for the HK Strategy MVP application in case database issues arise during multi-portfolio operations or schema changes.

**Current Status**: Multi-portfolio migration completed successfully  
**Database Value**: $4,052,660.20 across 12 positions  
**Risk Level**: ✅ LOW (migration successful, no data loss detected)  

---

## 📊 **CURRENT DATABASE STATE**

### **✅ Verified Working State**
- **Schema Version**: 2.0 (Multi-Portfolio Transitional)
- **Total Portfolios**: 5 active portfolios
- **Total Positions**: 12 positions across all portfolios
- **Total Portfolio Value**: $4,052,660.20
- **Primary Portfolio**: `My_HKEX_ALL` (contains all 12 positions)

### **🏢 Portfolio Inventory**
```
1. My_HKEX_ALL: My HKEX Full Portfolio (12 positions, $4M+ value)
2. HKEX_NonTech: HKEX Non Tech (0 positions)
3. Backup_HKEXALL: Backup_HKEXALL (0 positions) 
4. MyHKEX_Tech: MYHKEX_Tech (0 positions)
5. HKEXALL_Backup: HKEXALL_Backup (0 positions)
```

---

## 🚨 **EMERGENCY RESTORATION SCENARIOS**

### **Scenario 1: Database Corruption**
**Symptoms**: Database connection errors, data inconsistencies, schema corruption

**Immediate Actions**:
1. Stop all applications accessing the database
2. Create emergency backup of current state (if accessible)
3. Restore from most recent backup
4. Verify data integrity

### **Scenario 2: Accidental Data Loss**
**Symptoms**: Missing portfolios, deleted positions, incorrect values

**Immediate Actions**:
1. Identify scope of data loss
2. Stop additional modifications
3. Restore affected tables from backup
4. Reconcile with current state

### **Scenario 3: Migration Rollback Required**
**Symptoms**: Application failures, schema incompatibility, performance issues

**Immediate Actions**:
1. Execute controlled rollback procedure
2. Restore single-portfolio schema
3. Migrate data back to legacy format
4. Restart applications in single-portfolio mode

---

## 💾 **BACKUP PROCEDURES**

### **Create Full Database Backup**
```bash
#!/bin/bash
# Create timestamped full database backup
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="hk_strategy_backup_${TIMESTAMP}.sql"

# Full database dump
pg_dump -h localhost -U trader -d hk_strategy -f "${BACKUP_FILE}"

# Compress backup
gzip "${BACKUP_FILE}"

echo "✅ Backup created: ${BACKUP_FILE}.gz"
```

### **Create Data-Only Backup**
```bash
#!/bin/bash
# Create data-only backup (preserves current data for schema changes)
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="hk_strategy_data_${TIMESTAMP}.sql"

# Data-only dump
pg_dump -h localhost -U trader -d hk_strategy --data-only -f "${BACKUP_FILE}"
gzip "${BACKUP_FILE}"

echo "✅ Data backup created: ${BACKUP_FILE}.gz"
```

### **Create Schema-Only Backup**
```bash
#!/bin/bash
# Create schema-only backup (for rollback procedures)
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="hk_strategy_schema_${TIMESTAMP}.sql"

# Schema-only dump
pg_dump -h localhost -U trader -d hk_strategy --schema-only -f "${BACKUP_FILE}"

echo "✅ Schema backup created: ${BACKUP_FILE}"
```

---

## 🔄 **RESTORATION PROCEDURES**

### **Complete Database Restoration**
```bash
#!/bin/bash
# Restore complete database from backup
BACKUP_FILE="$1"  # Pass backup file as parameter

if [ -z "$BACKUP_FILE" ]; then
    echo "❌ Usage: $0 <backup_file.sql.gz>"
    exit 1
fi

echo "🚨 WARNING: This will COMPLETELY REPLACE the current database!"
echo "📂 Restoring from: $BACKUP_FILE"
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Restoration cancelled"
    exit 1
fi

# Stop applications
echo "🛑 Stopping applications..."
pkill -f streamlit || true
pkill -f dashboard || true

# Create emergency backup of current state
echo "💾 Creating emergency backup of current state..."
EMERGENCY_BACKUP="emergency_backup_$(date +%Y%m%d_%H%M%S).sql"
pg_dump -h localhost -U trader -d hk_strategy -f "$EMERGENCY_BACKUP"

# Drop and recreate database
echo "🗑️ Dropping current database..."
dropdb -h localhost -U trader hk_strategy
createdb -h localhost -U trader hk_strategy

# Restore from backup
echo "📥 Restoring from backup..."
if [[ "$BACKUP_FILE" == *.gz ]]; then
    gunzip -c "$BACKUP_FILE" | psql -h localhost -U trader -d hk_strategy
else
    psql -h localhost -U trader -d hk_strategy -f "$BACKUP_FILE"
fi

echo "✅ Database restoration completed"
echo "🔍 Verifying restoration..."

# Quick verification
psql -h localhost -U trader -d hk_strategy -c "
SELECT 
    (SELECT COUNT(*) FROM portfolio_positions) as positions,
    (SELECT COUNT(*) FROM portfolios) as portfolios,
    (SELECT ROUND(SUM(market_value), 2) FROM portfolio_positions) as total_value;
"

echo "✅ Restoration verification completed"
```

### **Rollback to Single-Portfolio Schema**
```bash
#!/bin/bash
# Emergency rollback to single-portfolio schema

echo "🚨 EMERGENCY ROLLBACK: Converting to single-portfolio schema"

# 1. Create backup of current multi-portfolio state
BACKUP_FILE="pre_rollback_backup_$(date +%Y%m%d_%H%M%S).sql"
pg_dump -h localhost -U trader -d hk_strategy -f "$BACKUP_FILE"
echo "💾 Created rollback point: $BACKUP_FILE"

# 2. Export critical portfolio data
psql -h localhost -U trader -d hk_strategy -c "
COPY (
    SELECT symbol, company_name, quantity, avg_cost, current_price,
           market_value, unrealized_pnl, sector, last_updated
    FROM portfolio_positions 
    WHERE portfolio_id = 'My_HKEX_ALL'
) TO '/tmp/main_portfolio_positions.csv' WITH CSV HEADER;
"

# 3. Drop multi-portfolio constraints and columns
psql -h localhost -U trader -d hk_strategy -c "
-- Remove foreign key constraints
ALTER TABLE portfolio_positions DROP CONSTRAINT IF EXISTS portfolio_positions_portfolio_id_fkey;
ALTER TABLE trading_signals DROP CONSTRAINT IF EXISTS trading_signals_portfolio_id_fkey;
ALTER TABLE price_history DROP CONSTRAINT IF EXISTS price_history_portfolio_id_fkey;

-- Remove portfolio_id columns
ALTER TABLE portfolio_positions DROP COLUMN IF EXISTS portfolio_id;
ALTER TABLE trading_signals DROP COLUMN IF EXISTS portfolio_id;  
ALTER TABLE price_history DROP COLUMN IF EXISTS portfolio_id;

-- Drop portfolio-related tables
DROP TABLE IF EXISTS portfolios CASCADE;
DROP VIEW IF EXISTS portfolio_summary CASCADE;
DROP TABLE IF EXISTS portfolio_value_history CASCADE;
DROP TABLE IF EXISTS portfolio_analyses CASCADE;
DROP TABLE IF EXISTS portfolio_analysis_equities CASCADE;
DROP TABLE IF EXISTS portfolio_analysis_equity_strategies CASCADE;
DROP TABLE IF EXISTS equity_strategy_analyses CASCADE;
DROP TABLE IF EXISTS strategy_signals CASCADE;
"

# 4. Clear and reload main portfolio positions (keep only primary portfolio data)
psql -h localhost -U trader -d hk_strategy -c "
-- Keep only main portfolio positions
DELETE FROM portfolio_positions 
WHERE symbol NOT IN (
    SELECT DISTINCT symbol FROM portfolio_positions 
    WHERE market_value > 0  -- Keep positions with actual value
);

-- Update any null values that might cause issues
UPDATE portfolio_positions 
SET last_updated = CURRENT_TIMESTAMP 
WHERE last_updated IS NULL;
"

echo "✅ Rollback to single-portfolio completed"
echo "🔍 Verifying rollback..."

# Verification
psql -h localhost -U trader -d hk_strategy -c "
SELECT 
    COUNT(*) as position_count,
    ROUND(SUM(market_value), 2) as total_value,
    MAX(last_updated) as last_update
FROM portfolio_positions;
"

echo "📂 Main portfolio data backed up to: /tmp/main_portfolio_positions.csv"
echo "💾 Full backup available at: $BACKUP_FILE"
```

---

## 🔧 **SPECIFIC RESTORATION SCENARIOS**

### **Restore Main Portfolio Only** 
```sql
-- Emergency query to restore only the main active portfolio
TRUNCATE TABLE portfolio_positions RESTART IDENTITY CASCADE;

-- Insert verified positions from My_HKEX_ALL portfolio
INSERT INTO portfolio_positions (symbol, company_name, quantity, avg_cost, current_price, market_value, unrealized_pnl, sector, portfolio_id)
SELECT symbol, company_name, quantity, avg_cost, current_price, market_value, unrealized_pnl, sector, 'My_HKEX_ALL'
FROM portfolio_positions_backup  -- From emergency backup table
WHERE portfolio_id = 'My_HKEX_ALL';
```

### **Restore Missing Portfolios**
```sql
-- Restore portfolio metadata if accidentally deleted
INSERT INTO portfolios (portfolio_id, name, description, created_at, updated_at)
VALUES 
    ('My_HKEX_ALL', 'My HKEX Full Portfolio', 'The full portfolio of my HKEX Companies', NOW(), NOW()),
    ('HKEX_NonTech', 'HKEX Non Tech', 'List of my non-Tech HKEX Stock', NOW(), NOW()),
    ('Backup_HKEXALL', 'Backup_HKEXALL', 'Backup of my full portfolio', NOW(), NOW()),
    ('MyHKEX_Tech', 'MYHKEX_Tech', 'My HKEX Tech Portfolio', NOW(), NOW()),
    ('HKEXALL_Backup', 'HKEXALL_Backup', 'My HKEX All Stock backup', NOW(), NOW())
ON CONFLICT (portfolio_id) DO NOTHING;
```

### **Data Integrity Verification**
```sql
-- Comprehensive data integrity check
SELECT 
    'Portfolio Summary' as check_type,
    COUNT(*) as count,
    ROUND(SUM(market_value), 2) as total_value
FROM portfolio_positions

UNION ALL

SELECT 
    'Portfolio Count' as check_type,
    COUNT(*) as count,
    0 as total_value
FROM portfolios

UNION ALL

SELECT 
    'Trading Signals' as check_type, 
    COUNT(*) as count,
    0 as total_value
FROM trading_signals

ORDER BY check_type;
```

---

## 📋 **RECOVERY VALIDATION CHECKLIST**

### **Post-Restoration Validation**
- [ ] Database connection successful
- [ ] All expected portfolios present (5 portfolios)
- [ ] Main portfolio contains 12 positions
- [ ] Total portfolio value = $4,052,660.20 (±5% acceptable)
- [ ] Dashboard loads without errors
- [ ] Portfolio switching works correctly
- [ ] Position data displays accurately
- [ ] Trading signals function properly

### **Application Testing**
- [ ] Dashboard starts without errors
- [ ] Multi-portfolio navigation works
- [ ] Position filtering by portfolio functions
- [ ] Portfolio creation/editing operations work
- [ ] Charts and visualizations display correctly
- [ ] No Python/SQL errors in logs

---

## 📞 **EMERGENCY CONTACTS & RESOURCES**

### **Key Files for Recovery**
- `init_multi_portfolio.sql` - Complete schema definition
- `migration_v1_to_v2.sql` - Migration procedures
- `src/database_enhanced.py` - Enhanced database manager
- This document - `BACKUP_RESTORATION_PLAN.md`

### **Quick Commands Reference**
```bash
# Check current database state
python investigate_db_state.py

# Test multi-portfolio functionality  
python test_portfolio_operations.py

# Create immediate backup
pg_dump -h localhost -U trader -d hk_strategy -f "emergency_$(date +%s).sql"

# Check portfolio values
psql -h localhost -U trader -d hk_strategy -c "SELECT portfolio_id, COUNT(*) as positions, ROUND(SUM(market_value), 2) as value FROM portfolio_positions GROUP BY portfolio_id;"
```

---

## ✅ **CURRENT STATUS CONFIRMATION**

**As of 2025-08-30 12:31 UTC:**

✅ **Database Status**: Healthy and operational  
✅ **Schema Version**: 2.0 Multi-Portfolio (transitional but stable)  
✅ **Data Integrity**: All 12 positions and $4M+ value confirmed  
✅ **Application Status**: Dashboard functional with multi-portfolio support  
✅ **Backup Status**: Emergency procedures documented and ready  

**Risk Assessment**: 🟢 LOW - System is stable and functional

---

*Last Updated: 2025-08-30*  
*Document Version: 1.0*  
*Status: Ready for Production Use*