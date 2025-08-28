# 🏦 HK Strategy Portfolio Dashboard - Installation Manual

## 📋 Table of Contents
1. [System Requirements](#system-requirements)
2. [Pre-Installation Checklist](#pre-installation-checklist)
3. [Step-by-Step Installation](#step-by-step-installation)
4. [Security Configuration](#security-configuration)
5. [Database Setup](#database-setup)
6. [Redis Setup](#redis-setup)
7. [Application Configuration](#application-configuration)
8. [Starting the Application](#starting-the-application)
9. [Verification](#verification)
10. [Troubleshooting](#troubleshooting)
11. [Maintenance](#maintenance)

---

## 🖥️ System Requirements

### **Minimum Requirements:**
- **OS**: Ubuntu 18.04+ / Debian 10+ / CentOS 7+ / WSL2
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 5GB free space
- **Python**: 3.8 or higher
- **Network**: Internet connection for Yahoo Finance API

### **Recommended Environment:**
- **OS**: Ubuntu 20.04 LTS or Ubuntu 22.04 LTS
- **RAM**: 8GB for optimal performance
- **CPU**: 2+ cores
- **Storage**: 10GB+ SSD storage

---

## ✅ Pre-Installation Checklist

```bash
# 1. Update system packages
sudo apt update && sudo apt upgrade -y

# 2. Install essential tools
sudo apt install -y curl wget git python3 python3-pip python3-venv

# 3. Verify Python version (should be 3.8+)
python3 --version

# 4. Check available disk space (should have 5GB+)
df -h

# 5. Test internet connectivity
ping -c 3 finance.yahoo.com
```

---

## 🚀 Step-by-Step Installation

### **Step 1: Clone the Repository**

```bash
# Clone the project
git clone <your-repo-url>
cd hk-strategy-mvp

# Or if you have the files locally, navigate to the directory
cd /path/to/hk-strategy-mvp
```

### **Step 2: Create Python Virtual Environment**

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### **Step 3: Install Python Dependencies**

```bash
# Install all required Python packages
pip install -r requirements.txt

# Verify critical packages are installed
python -c "import streamlit, psycopg2, redis, yfinance; print('✅ All packages installed')"
```

### **Step 4: Install PostgreSQL**

```bash
# Install PostgreSQL
sudo apt update
sudo apt install -y postgresql postgresql-contrib

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Verify installation
sudo systemctl status postgresql
```

### **Step 5: Install Redis**

```bash
# Method 1: Install from Ubuntu repository (recommended)
sudo apt install -y redis-server

# Method 2: Or use the provided script (requires sudo)
chmod +x install_redis.sh
sudo ./install_redis.sh

# Verify Redis installation
redis-server --version
redis-cli ping
```

**Note**: Redis installation requires sudo privileges. If you don't have sudo access, you can run Redis in Docker or use a cloud Redis service by updating the configuration file.

### **Step 6: Setup Security Configuration**

```bash
# Run the security setup (creates config files with secure passwords)
./setup_security.sh

# Configuration files are automatically populated with secure values
# Edit config/app_config.yaml if you need to customize any settings
```

### **Step 7: Database Setup**

```bash
# Run the SECURE database setup script (recommended)
chmod +x fix_database_secure.sh
sudo ./fix_database_secure.sh

# Or use legacy setup (less secure)
sudo ./fix_database.sh
```

### **Step 8: Initialize Application**

```bash
# Activate virtual environment if not already active
source venv/bin/activate

# Start the dashboard
streamlit run dashboard_editable.py

# Or use the startup script
./start_app.sh
```

---

## 🔒 Security Configuration

### **Configuration File Structure**

The application uses a secure configuration system with the following files:

```
config/
├── app_config.yaml          # Main configuration (NEVER commit)
├── app_config.template.yaml # Template file (safe to commit)
└── .env                     # Environment variables (NEVER commit)
```

### **Setting Up Secure Configuration:**

1. **Copy the template:**
```bash
cp config/app_config.template.yaml config/app_config.yaml
```

2. **Edit with your credentials:**
```bash
nano config/app_config.yaml
```

3. **Verify .gitignore includes config files:**
```bash
# These should be in .gitignore:
config/app_config.yaml
config/.env
*.log
__pycache__/
```

---

## 🗄️ Database Setup

### **Automated Setup (Recommended):**

**Option 1: Secure Setup from .env (Recommended)**
```bash
sudo ./setup_database_from_env.sh  # Loads password from config/.env only
```

**Option 2: Auto-generated Setup**
```bash
sudo ./fix_database_secure.sh      # Uses auto-generated secure passwords
```

**Option 3: Legacy Setup**  
```bash
sudo ./fix_database.sh             # Uses default passwords (less secure)
```

**Note**: Option 1 is most secure - it only uses the password from your `.env` file and never exposes it in command line or other files.

### **Manual Setup:**

```bash
# 1. Switch to postgres user
sudo -u postgres psql

# 2. Create user and database
CREATE USER trader WITH PASSWORD 'YOUR_SECURE_PASSWORD_HERE';
ALTER USER trader CREATEDB;
CREATE DATABASE hk_strategy OWNER trader;
GRANT ALL PRIVILEGES ON DATABASE hk_strategy TO trader;

# 3. List users and databases to verify
\du
\l
\q

# 4. Test connection
PGPASSWORD=YOUR_SECURE_PASSWORD psql -U trader -h localhost -d hk_strategy -c "SELECT version();"

# 5. Initialize database with HKEX data
PGPASSWORD=YOUR_SECURE_PASSWORD psql -U trader -h localhost -d hk_strategy -f init.sql

# 6. Verify data was inserted
PGPASSWORD=YOUR_SECURE_PASSWORD psql -U trader -h localhost -d hk_strategy -c "SELECT COUNT(*) FROM portfolio_positions;"
```

### **PostgreSQL Authentication Fix:**

If you get authentication errors:

```bash
# Find PostgreSQL version
sudo -u postgres psql -c "SELECT version();"

# Edit pg_hba.conf (replace XX with your version)
sudo nano /etc/postgresql/XX/main/pg_hba.conf

# Change these lines from 'peer' to 'md5':
local   all             postgres                                md5
local   all             all                                     md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

---

## 🔄 Redis Setup

### **Automated Setup:**

```bash
sudo ./install_redis.sh
```

### **Manual Setup:**

```bash
# 1. Install Redis
sudo apt update
sudo apt install -y redis-server

# 2. Configure Redis for systemd
sudo nano /etc/redis/redis.conf

# Find and change:
supervised no → supervised systemd
dir ./ → dir /var/lib/redis

# 3. Start and enable Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# 4. Test Redis
redis-cli ping  # Should return PONG
redis-cli set test "Hello"
redis-cli get test  # Should return "Hello"
redis-cli del test
```

### **Redis Security (Optional):**

```bash
# Set Redis password
sudo nano /etc/redis/redis.conf

# Uncomment and set:
# requirepass your_redis_password

# Restart Redis
sudo systemctl restart redis-server

# Test with password
redis-cli -a your_redis_password ping
```

---

## ⚙️ Application Configuration

### **Configuration File (config/app_config.yaml):**

```yaml
# Database Configuration
database:
  host: localhost
  port: 5432
  name: hk_strategy
  user: trader
  password: YOUR_SECURE_PASSWORD_HERE

# Redis Configuration  
redis:
  host: localhost
  port: 6379
  password: null  # Set if Redis password is configured

# Yahoo Finance API
api:
  yahoo_finance:
    enabled: true
    rate_limit: 100  # requests per minute
    timeout: 10      # seconds

# Application Settings
app:
  debug: false
  log_level: INFO
  port: 8501
  host: 0.0.0.0

# Security Settings
security:
  session_timeout: 3600  # seconds
  max_login_attempts: 5
```

### **Environment Variables (.env):**

```bash
# Application Environment
FLASK_ENV=production
DEBUG=False

# Database Connection (backup method)
DATABASE_URL=postgresql://trader:YOUR_SECURE_PASSWORD@localhost:5432/hk_strategy
REDIS_URL=redis://localhost:6379

# API Keys (if needed)
# YAHOO_API_KEY=your_api_key_here

# Security
SECRET_KEY=generate_a_random_secret_key_here
```

---

## 🚀 Starting the Application

### **Method 1: Direct Start**

```bash
# Activate virtual environment
source venv/bin/activate

# Start Streamlit dashboard
streamlit run dashboard_editable.py --server.port 8501
```

### **Method 2: Using Startup Script**

```bash
# Make sure script is executable
chmod +x start_app.sh

# Start the application
./start_app.sh
```

### **Method 3: Production Deployment**

```bash
# Install process manager
sudo apt install -y supervisor

# Copy supervisor config
sudo cp configs/supervisor_hk_strategy.conf /etc/supervisor/conf.d/

# Start with supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start hk_strategy
```

---

## ✅ Verification

### **System Health Check:**

1. **Open the dashboard:**
   - Navigate to: `http://localhost:8501`

2. **Click System Status:**
   - Click "⚙️ System" in the sidebar
   - Click "🔄 Refresh All Checks"

3. **Verify all components are healthy:**
   - ✅ PostgreSQL Database: Connected
   - ✅ Redis Cache: Connected  
   - ✅ Yahoo Finance API: Working

### **Manual Verification:**

```bash
# Test database connection
PGPASSWORD=YOUR_SECURE_PASSWORD psql -U trader -h localhost -d hk_strategy -c "\dt"

# Test Redis connection
redis-cli ping

# Test Python modules
python -c "import streamlit, psycopg2, redis, yfinance; print('✅ All modules working')"

# Test Yahoo Finance API
python -c "import yfinance as yf; print('AAPL:', yf.Ticker('AAPL').history(period='1d')['Close'].iloc[-1])"
```

---

## 🔧 Troubleshooting

### **Common Issues:**

#### **Database Connection Errors:**
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Check if user exists
sudo -u postgres psql -c "\du"

# Reset password if needed
sudo -u postgres psql -c "ALTER USER trader WITH PASSWORD 'YOUR_NEW_SECURE_PASSWORD';"
```

#### **Redis Connection Errors:**
```bash
# Check if Redis is running
sudo systemctl status redis-server

# Check Redis logs
sudo journalctl -u redis-server -f

# Restart Redis if needed
sudo systemctl restart redis-server
```

#### **Python Module Errors:**
```bash
# Reinstall requirements
pip install --force-reinstall -r requirements.txt

# Check virtual environment
which python
which pip
```

#### **Port Already in Use:**
```bash
# Find what's using port 8501
sudo netstat -tlnp | grep 8501

# Kill the process if needed
sudo pkill -f streamlit

# Or use a different port
streamlit run dashboard_editable.py --server.port 8502
```

### **Log Files:**

```bash
# Application logs
tail -f logs/app.log

# PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-*-main.log

# Redis logs
sudo journalctl -u redis-server -f

# System logs
sudo journalctl -f
```

---

## 🔄 Maintenance

### **Regular Updates:**

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Python packages
pip list --outdated
pip install --upgrade streamlit yfinance

# Update application
git pull origin main
pip install -r requirements.txt
```

### **Backup:**

```bash
# Backup database
PGPASSWORD=YOUR_SECURE_PASSWORD pg_dump -U trader -h localhost hk_strategy > backup_$(date +%Y%m%d).sql

# Backup configuration
cp config/app_config.yaml config/app_config_backup_$(date +%Y%m%d).yaml
```

### **Monitoring:**

```bash
# Check system resources
htop
df -h
free -h

# Check application status
ps aux | grep streamlit
ps aux | grep postgres
ps aux | grep redis
```

---

## 🛡️ Security Best Practices

1. **Never commit passwords or API keys to git**
2. **Use strong, unique passwords**
3. **Regularly update all components**
4. **Monitor log files for suspicious activity**
5. **Use firewall to restrict access**
6. **Enable SSL/TLS in production**
7. **Regular security audits**

---

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review system logs
3. Use the built-in system status checker
4. Create an issue in the project repository

---

**🎯 Quick Start Summary (Secure):**
```bash
git clone <repo>
cd hk-strategy-mvp
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
sudo apt install -y redis-server      # or sudo ./install_redis.sh
./setup_security.sh                   # Creates secure config files with passwords
sudo ./setup_database_from_env.sh     # Uses ONLY passwords from .env file
./start_app.sh                         # Starts the application
```

**🔒 Security Features:**
- Auto-generated secure passwords
- Config files excluded from git
- Environment variable support
- No hardcoded credentials