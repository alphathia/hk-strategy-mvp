# 🔄 Database Migration Guide: Single → Multi-Portfolio Architecture

## 📋 Overview

This guide provides step-by-step instructions for safely migrating your HK Strategy database from single-portfolio to multi-portfolio architecture without breaking the running application.

## 🎯 Migration Goals

- **Zero Downtime**: Application continues running during migration
- **Backward Compatibility**: Existing features work throughout the process
- **Data Safety**: No data loss, comprehensive rollback options
- **Progressive Enhancement**: Gradual feature enablement

## 📊 Current State Analysis

Run the schema checker to understand your current database state:

```bash
python run_migration.py check
```

This will show:
- Current schema version
- Available features
- Migration recommendations
- Health status of all components

## 🔄 Migration Phases

### **Phase 1: Schema Enhancement (Zero-Downtime)**
- ✅ Adds multi-portfolio support
- ✅ Maintains backward compatibility  
- ✅ Existing application continues working
- ✅ Enables new multi-portfolio features

### **Phase 2: Data Integrity (Optional)**
- ✅ Adds foreign key constraints
- ⚠️ Removes backward compatibility
- ✅ Ensures referential integrity
- ✅ Production-ready schema

## 🚀 Migration Execution

### **Step 1: Backup and Preparation**

1. **Activate virtual environment**:
   ```bash
   source venv/bin/activate
   ```

2. **Install missing dependencies** (if needed):
   ```bash
   pip install redis pyyaml python-dotenv
   ```

3. **Verify database connection**:
   ```bash
   python run_migration.py check
   ```

### **Step 2: Phase 1 Migration (Recommended)**

Execute Phase 1 migration with automatic backup:

```bash
python run_migration.py phase1
```

This will:
- 🛡️ Create automatic database backup
- ➕ Add `portfolios` table
- ➕ Add `portfolio_id` columns (nullable)
- 📦 Migrate existing data to 'DEFAULT' portfolio
- 🔍 Create performance indexes
- ✅ Run validation tests

**What happens after Phase 1:**
- ✅ Your existing single-portfolio application continues working
- ✅ Multi-portfolio dashboard features become available  
- ✅ You can create new portfolios via the dashboard
- ✅ Both old and new code paths work simultaneously

### **Step 3: Test Multi-Portfolio Features**

After Phase 1, test the enhanced functionality:

1. **Start the multi-portfolio dashboard**:
   ```bash
   python dashboard.py
   ```

2. **Verify existing data**:
   - Check that all your positions appear in the "DEFAULT" portfolio
   - Verify P&L calculations are correct
   - Test creating a new portfolio

3. **Run comprehensive tests**:
   ```bash
   python test_migration.py
   ```

### **Step 4: Phase 2 Migration (Optional)**

⚠️ **Only run Phase 2 after confirming Phase 1 works correctly**

Phase 2 adds full referential integrity but removes backward compatibility:

```bash
python run_migration.py phase2
```

This will:
- 🔒 Make `portfolio_id` columns NOT NULL
- 🔗 Add foreign key constraints
- 🚫 Remove backward compatibility
- 🏗️ Create enhanced views and functions

## 🔙 Rollback Options

### **Rollback from Phase 1**

If you need to return to single-portfolio schema:

```bash
python run_migration.py rollback
```

⚠️ **Rollback Notes:**
- All multi-portfolio data will be merged into single portfolio
- Symbol conflicts will be automatically resolved (quantities summed, costs averaged)
- No data loss, but multi-portfolio isolation will be lost

### **Rollback from Phase 2**

Phase 2 rollback is more complex and may require manual intervention. Contact support or restore from backup if needed.

## 📋 Verification and Monitoring

### **Schema Status Check**
```bash
python run_migration.py check
```

### **Run Test Suite**
```bash
python test_migration.py
```

### **Database Health Check**
Access the dashboard System Status page to verify:
- ✅ PostgreSQL connection healthy
- ✅ Redis connection working  
- ✅ Multi-portfolio features enabled

## 🚨 Troubleshooting

### **Common Issues**

#### 1. **Module Import Errors**
```bash
# Install missing Python packages
pip install redis pyyaml python-dotenv pandas psycopg2-binary
```

#### 2. **Database Connection Failed**
- Verify PostgreSQL is running: `sudo systemctl status postgresql`
- Check credentials in `.env` file
- Test connection manually: `psql -U trader -d hk_strategy`

#### 3. **Migration Prerequisites Not Met**
- For Phase 1: Ensure `portfolio_positions` table exists
- For Phase 2: Ensure Phase 1 completed successfully
- For rollback: Ensure migration tables exist

#### 4. **Permission Errors**
```bash
# Ensure proper database permissions
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE hk_strategy TO trader;"
```

#### 5. **Schema Inconsistency**
```bash
# Check current schema state
python run_migration.py check

# View detailed schema information
psql -U trader -d hk_strategy -c "SELECT * FROM check_migration_status();"
```

## 📝 File Reference

| File | Purpose |
|------|---------|
| `migration_v1_to_v2.sql` | Phase 1: Add multi-portfolio support |
| `migration_v2_to_v3.sql` | Phase 2: Add foreign key constraints |
| `rollback_v2_to_v1.sql` | Rollback to single-portfolio |
| `run_migration.py` | Migration execution script |
| `test_migration.py` | Comprehensive test suite |
| `src/database_enhanced.py` | Enhanced DatabaseManager with migration awareness |

## ⏱️ Timeline Estimates

| Phase | Duration | Complexity | Risk |
|-------|----------|------------|------|
| Phase 1 | 5-10 minutes | Low | Very Low |
| Testing | 10-15 minutes | Medium | Low |
| Phase 2 | 5-10 minutes | Medium | Low |
| Rollback | 5-10 minutes | Medium | Medium |

## 🎯 Success Criteria

### **Phase 1 Success Indicators:**
- ✅ `python run_migration.py check` shows "multi-portfolio (v2.0)"
- ✅ `python test_migration.py` passes all tests
- ✅ Dashboard shows DEFAULT portfolio with all existing positions
- ✅ You can create new portfolios via dashboard
- ✅ All P&L calculations remain accurate

### **Phase 2 Success Indicators:**
- ✅ `python run_migration.py check` shows "multi-portfolio (v3.0)"
- ✅ Foreign key constraints prevent data inconsistencies
- ✅ Enhanced portfolio performance views work correctly
- ✅ Data integrity validation passes

## 🆘 Emergency Contacts

If you encounter critical issues:

1. **Stop the migration** - Don't proceed if errors occur
2. **Restore from backup** - Use the automatically created backup
3. **Check logs** - Review migration log files for detailed errors
4. **Run diagnostics** - Use `python run_migration.py check` for current state

## 📚 Additional Resources

- **Database Schema Documentation**: See `init.sql` vs `init_multi_portfolio.sql`
- **Application Code**: Dashboard automatically detects schema version
- **API Reference**: DatabaseManager adapts queries based on schema state
- **Performance**: Multi-portfolio indexes optimize query performance

## 🎉 Post-Migration Benefits

After successful migration:

- 🏢 **Multiple Portfolio Support**: Create and manage separate portfolios
- 🔄 **Portfolio Copying**: Duplicate portfolios for strategy testing
- 📊 **Portfolio Comparison**: Side-by-side portfolio analysis
- 🛡️ **Data Isolation**: Positions isolated by portfolio
- 📈 **Enhanced Analytics**: Portfolio-specific performance metrics
- 🔍 **Better Organization**: Group positions by strategy or theme

---

**Need Help?** Run `python run_migration.py check` for current status or `python test_migration.py` for comprehensive diagnostics.