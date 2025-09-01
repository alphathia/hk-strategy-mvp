# 🛠️ PostgreSQL Database Setup Manual

## 🔍 Problem Analysis
Based on your system diagnostics:
- ✅ PostgreSQL is running (15 processes)
- ✅ psycopg2 module is available 
- ❌ User `trader` authentication fails
- ❌ User `postgres` requires password
- ❌ System user `bthia` has no PostgreSQL access

## 🎯 Solution: Step-by-Step Process

### **Option A: Automated Setup (Recommended)**

Run the automated setup script:

```bash
# Make the script executable (already done)
chmod +x fix_database.sh

# Run the setup script with sudo
sudo ./fix_database.sh
```

**This script will:**
1. ✅ Create the `trader` user with password `trading123`
2. ✅ Create the `hk_strategy` database 
3. ✅ Set proper permissions
4. ✅ Fix authentication configuration if needed
5. ✅ Run `init.sql` to create tables and insert data
6. ✅ Test the connection

---

### **Option B: Manual Setup**

If you prefer to do it manually, follow these steps:

#### **Step 1: Access PostgreSQL as superuser**
```bash
sudo -u postgres psql
```

#### **Step 2: Create user and database**
```sql
-- Create trader user
CREATE USER trader WITH PASSWORD 'trading123';

-- Give trader permission to create databases
ALTER USER trader CREATEDB;

-- Create the hk_strategy database
CREATE DATABASE hk_strategy OWNER trader;

-- Grant all privileges
GRANT ALL PRIVILEGES ON DATABASE hk_strategy TO trader;

-- Check users and databases
\du
\l

-- Exit PostgreSQL
\q
```

#### **Step 3: Test the connection**
```bash
PGPASSWORD=trading123 psql -U trader -h localhost -d hk_strategy -c "SELECT version();"
```

#### **Step 4: If connection fails, fix authentication**

Edit the PostgreSQL configuration:
```bash
# Find your PostgreSQL version
sudo -u postgres psql -c "SELECT version();"

# Edit pg_hba.conf (replace XX with your PostgreSQL version)
sudo nano /etc/postgresql/XX/main/pg_hba.conf

# Change these lines from 'peer' to 'md5':
# local   all             postgres                                md5
# local   all             all                                     md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

#### **Step 5: Initialize database with tables**
```bash
# Run the init.sql script
PGPASSWORD=trading123 psql -U trader -h localhost -d hk_strategy -f init.sql

# Verify tables were created
PGPASSWORD=trading123 psql -U trader -h localhost -d hk_strategy -c "\dt"

# Check sample data
PGPASSWORD=trading123 psql -U trader -h localhost -d hk_strategy -c "SELECT symbol, company_name, quantity FROM portfolio_positions LIMIT 5;"
```

---

## 🔧 Troubleshooting Common Issues

### **Issue 1: "peer authentication failed"**
**Solution:** Change authentication method in `pg_hba.conf` from `peer` to `md5`

### **Issue 2: "role trader does not exist"**
**Solution:** Create the trader user (see Step 2 above)

### **Issue 3: "database hk_strategy does not exist"**
**Solution:** Create the database (see Step 2 above)

### **Issue 4: "password authentication failed"**
**Solution:** Reset the password:
```sql
sudo -u postgres psql
ALTER USER trader WITH PASSWORD 'trading123';
\q
```

### **Issue 5: "connection refused"**
**Solution:** Start PostgreSQL:
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

---

## ✅ Verification Steps

After setup, verify everything works:

1. **Test connection:**
   ```bash
   PGPASSWORD=trading123 psql -U trader -h localhost -d hk_strategy -c "SELECT version();"
   ```

2. **Check tables exist:**
   ```bash
   PGPASSWORD=trading123 psql -U trader -h localhost -d hk_strategy -c "\dt"
   ```

3. **Verify portfolio data:**
   ```bash
   PGPASSWORD=trading123 psql -U trader -h localhost -d hk_strategy -c "SELECT COUNT(*) FROM portfolio_positions;"
   ```

4. **Test from dashboard:**
   - Go to your Streamlit dashboard
   - Click "⚙️ System" 
   - Click "🔄 Refresh All Checks"
   - PostgreSQL should show ✅ Healthy

---

## 📊 Expected Final Connection String

After successful setup, your dashboard will connect using:
```
postgresql://trader:trading123@localhost:5432/hk_strategy
```

## 🚨 Quick Fix Commands

If you just need the essential commands:

```bash
# 1. Create user and database
sudo -u postgres psql -c "CREATE USER trader WITH PASSWORD 'trading123';"
sudo -u postgres psql -c "CREATE DATABASE hk_strategy OWNER trader;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE hk_strategy TO trader;"

# 2. Initialize database
PGPASSWORD=trading123 psql -U trader -h localhost -d hk_strategy -f init.sql

# 3. Test connection  
PGPASSWORD=trading123 psql -U trader -h localhost -d hk_strategy -c "SELECT version();"
```

---

**🎯 Once you've run the setup, refresh the System Status page in your dashboard to see the green checkmarks!**