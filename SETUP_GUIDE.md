# 🏦 HK Strategy Dashboard - Complete Setup Guide

## 📋 Table of Contents
- [🎯 Quick Start](#-quick-start)
- [📋 Prerequisites](#-prerequisites)
- [🔧 Installation Methods](#-installation-methods)
- [⚙️ Environment Configuration](#️-environment-configuration)
- [🗄️ Database Setup](#️-database-setup)
- [🚀 Starting the Application](#-starting-the-application)
- [🧪 Testing & Validation](#-testing--validation)
- [🔧 Troubleshooting](#-troubleshooting)
- [📈 Advanced Configuration](#-advanced-configuration)

## 🎯 Quick Start

**For the impatient - get running in 5 minutes:**

```bash
# 1. Clone and enter directory
git clone <repository-url>
cd hk-strategy-mvp

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.template .env
# Edit .env with your database credentials

# 4. Start the modular dashboard
./start_modular_dashboard.sh
```

Visit `http://localhost:8501` in your browser! 🎉

## 📋 Prerequisites

### **System Requirements**
- **Python**: 3.8 or higher
- **Operating System**: Linux, macOS, or Windows
- **Memory**: 4GB RAM minimum (8GB recommended)
- **Disk Space**: 2GB available space

### **Required Software**
- **PostgreSQL**: 12.0 or higher
- **Redis**: 6.0 or higher (optional but recommended)
- **Git**: For version control
- **pip**: Python package manager

### **Recommended Tools**
- **Docker & Docker Compose**: For containerized deployment
- **pgAdmin**: For database administration
- **Redis CLI**: For cache management

## 🔧 Installation Methods

### **Method 1: Docker Deployment (Recommended)**

**Perfect for production and consistent environments**

```bash
# 1. Clone repository
git clone <repository-url>
cd hk-strategy-mvp

# 2. Create configuration (optional)
cp config/app_config.template.yaml config/app_config.yaml
# Edit config/app_config.yaml as needed

# 3. Start all services
docker-compose up --build

# Services will be available at:
# - Streamlit Dashboard: http://localhost:8501
# - PostgreSQL: localhost:5432
# - Redis: localhost:6379
```

### **Method 2: Local Development**

**Best for development and customization**

```bash
# 1. Clone repository
git clone <repository-url>
cd hk-strategy-mvp

# 2. Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup databases (see Database Setup section)
./setup_local_db.sh     # Setup PostgreSQL
./install_redis.sh      # Install Redis (optional)

# 5. Initialize database
./setup_database_from_env.sh

# 6. Start application
./start_modular_dashboard.sh
```

### **Method 3: Manual Installation**

**For complete control over the installation process**

#### **Step 1: System Dependencies**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip postgresql postgresql-contrib redis-server git

# CentOS/RHEL
sudo yum install python3 python3-pip postgresql postgresql-server redis git

# macOS (using Homebrew)
brew install python postgresql redis git
```

#### **Step 2: Python Setup**
```bash
# Verify Python version
python3 --version  # Should be 3.8+

# Create project directory
mkdir hk-strategy-dashboard
cd hk-strategy-dashboard

# Clone repository
git clone <repository-url> .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install --upgrade pip
pip install -r requirements.txt
```

#### **Step 3: Database Configuration**
```bash
# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database user and database
sudo -u postgres createuser -s trader
sudo -u postgres createdb hk_strategy
sudo -u postgres psql -c "ALTER USER trader PASSWORD 'your_secure_password';"
```

#### **Step 4: Application Setup**
```bash
# Create environment configuration
cp .env.template .env
# Edit .env with your credentials

# Initialize database schema
python3 -c "
from src.database import DatabaseManager
db = DatabaseManager()
db.initialize_database()
"

# Start Redis (optional)
sudo systemctl start redis
sudo systemctl enable redis
```

## ⚙️ Environment Configuration

### **Environment Variables (.env)**

Create a `.env` file with your configuration:

```bash
# Database Configuration (Required)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=hk_strategy
DB_USER=trader
DB_PASSWORD=your_secure_password
DATABASE_URL=postgresql://trader:your_secure_password@localhost:5432/hk_strategy

# Redis Configuration (Optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_URL=redis://localhost:6379

# Application Settings
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_HEADLESS=true
DEBUG=true
ENVIRONMENT=development
LOG_LEVEL=INFO

# Cache Configuration
CACHE_ENABLED=true
CACHE_PRICE_TTL=1800
```

### **YAML Configuration (Alternative)**

Create `config/app_config.yaml`:

```yaml
database:
  host: localhost
  port: 5432
  database: hk_strategy
  username: trader
  password: your_secure_password

redis:
  host: localhost
  port: 6379
  enabled: true

strategy:
  lookback_days: 90
  use_live_quotes: true
  baseline_date: "2025-08-03"
  baseline_cash: 200000.0

application:
  debug: true
  cache_enabled: true
  log_level: INFO
```

### **Security Best Practices**

⚠️ **NEVER commit sensitive files:**
- `.env` file (excluded by .gitignore)
- `config/app_config.yaml` (excluded by .gitignore)
- Any files containing passwords or API keys

✅ **Use strong passwords:**
- At least 12 characters
- Mix of uppercase, lowercase, numbers, symbols
- Unique for each service

✅ **File permissions:**
```bash
chmod 600 .env
chmod 600 config/app_config.yaml
```

## 🗄️ Database Setup

### **PostgreSQL Installation & Setup**

#### **Ubuntu/Debian:**
```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE USER trader WITH PASSWORD 'your_secure_password';
CREATE DATABASE hk_strategy OWNER trader;
GRANT ALL PRIVILEGES ON DATABASE hk_strategy TO trader;
\q
EOF
```

#### **CentOS/RHEL:**
```bash
# Install PostgreSQL
sudo yum install postgresql postgresql-server

# Initialize and start
sudo postgresql-setup initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Configure authentication (edit /var/lib/pgsql/data/pg_hba.conf)
# Change 'ident' to 'md5' for local connections
sudo systemctl restart postgresql
```

#### **macOS:**
```bash
# Using Homebrew
brew install postgresql
brew services start postgresql

# Create database
createdb hk_strategy
psql hk_strategy -c "CREATE USER trader WITH PASSWORD 'your_secure_password';"
```

### **Database Schema Initialization**

Run the initialization script:

```bash
# Method 1: Using setup script
./setup_database_from_env.sh

# Method 2: Manual initialization
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

from src.database import DatabaseManager
db = DatabaseManager()
print('Initializing database schema...')
db.initialize_database()
print('Database initialization complete!')
"
```

### **Redis Setup (Optional but Recommended)**

Redis provides caching for improved performance:

#### **Installation:**
```bash
# Ubuntu/Debian
sudo apt install redis-server

# CentOS/RHEL
sudo yum install redis

# macOS
brew install redis
```

#### **Configuration:**
```bash
# Start Redis
sudo systemctl start redis
sudo systemctl enable redis

# Test Redis connection
redis-cli ping
# Should return: PONG
```

## 🚀 Starting the Application

### **Option 1: Modular Dashboard (Recommended)**

The new modular dashboard with complete Phase 1-5 architecture:

```bash
# Using the smart startup script
./start_modular_dashboard.sh

# Or directly with Streamlit
streamlit run dashboard.py --server.port=8501
```

**Features Available:**
- ✅ **Complete Phase 1-5 Architecture**: Core, Services, Navigation, Pages, Components
- ✅ **35+ UI Components**: Dialogs, Charts, Forms, Widgets  
- ✅ **Modular Navigation**: Hierarchical navigation with breadcrumbs
- ✅ **Portfolio Management**: Multi-portfolio tracking and analysis
- ✅ **Strategy Analysis**: Technical indicators and signal generation
- ✅ **System Monitoring**: Health checks and connectivity status

### **Option 2: Original Dashboard (Legacy)**

For compatibility or troubleshooting:

```bash
# Using legacy startup script
./start_legacy_dashboard.sh

# Or manually
python dashboard_old.py
```

### **Option 3: Simple Dashboard**

Lightweight dashboard for basic functionality:

```bash
streamlit run simple_dashboard.py
```

### **Startup Script Options**

The smart startup scripts provide:
- **System requirements checking**
- **Dependency installation**  
- **Environment validation**
- **Database connection testing**
- **Automatic error handling**
- **Helpful troubleshooting tips**

```bash
# Make scripts executable
chmod +x *.sh

# Start with full health checks
./start_modular_dashboard.sh

# Start legacy version if needed
./start_legacy_dashboard.sh
```

## 🧪 Testing & Validation

### **Health Check Scripts**

Verify your installation:

```bash
# Overall system health
./health_check.sh

# Database connectivity
./test_db_connection.sh

# Individual component tests
python test_db.py           # Database connection
python test_prices.py       # Yahoo Finance API
python test_dashboard_integration.py  # Dashboard functionality
```

### **Manual Testing**

1. **Access Dashboard**: Visit `http://localhost:8501`
2. **Navigation Test**: Click through all navigation sections
3. **Portfolio Test**: Create a test portfolio with some positions
4. **Data Test**: Verify price data is loading for HK stocks
5. **Technical Analysis**: Check that indicators are calculating

### **Component Testing**

Test the new Phase 5 components:

```bash
# Run component tests
python tests/test_phase5_components.py

# Test specific component categories
python -c "
from src.components import *
print('Available components:')
print(f'Dialogs: {len(DIALOG_REGISTRY)}')
print(f'Charts: {len(CHART_REGISTRY)}')  
print(f'Forms: {len(FORM_REGISTRY)}')
print(f'Widgets: {len(WIDGET_REGISTRY)}')
"
```

### **Performance Testing**

```bash
# Test startup time
time streamlit run dashboard.py --server.headless true &
sleep 10
curl -f http://localhost:8501 || echo "Startup failed"
pkill -f streamlit
```

## 🔧 Troubleshooting

### **Common Issues & Solutions**

#### **1. Database Connection Issues**

**Error**: `FATAL: password authentication failed`
```bash
# Solution: Reset database password
sudo -u postgres psql -c "ALTER USER trader PASSWORD 'new_password';"
# Update .env file with new password
```

**Error**: `FATAL: database "hk_strategy" does not exist`
```bash
# Solution: Create database
sudo -u postgres createdb hk_strategy
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE hk_strategy TO trader;"
```

#### **2. Python/Streamlit Issues**

**Error**: `ModuleNotFoundError: No module named 'streamlit'`
```bash
# Solution: Install requirements
pip install -r requirements.txt

# Or specific packages
pip install streamlit pandas plotly yfinance psycopg2-binary
```

**Error**: `Permission denied` on startup scripts
```bash
# Solution: Make scripts executable
chmod +x *.sh
```

#### **3. Redis Issues**

**Error**: `ConnectionError: Error 111 connecting to localhost:6379`
```bash
# Solution: Start Redis
sudo systemctl start redis

# Or disable Redis caching
# Set REDIS_ENABLED=false in .env
```

#### **4. Port Already in Use**

**Error**: `Port 8501 is already in use`
```bash
# Solution: Find and kill process
lsof -i :8501
kill -9 <process_id>

# Or use different port
streamlit run dashboard.py --server.port=8502
```

#### **5. Import Errors**

**Error**: Component or module import failures
```bash
# Solution: Check PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or install in development mode
pip install -e .
```

### **Debug Mode**

Enable detailed logging:

```bash
# Set debug environment variables
export DEBUG=true
export LOG_LEVEL=DEBUG

# Start with verbose output
streamlit run dashboard.py --logger.level=debug
```

### **Health Check Commands**

```bash
# Database health
python -c "
from src.database import DatabaseManager
db = DatabaseManager()
status = db.test_connection()
print(f'Database: {status}')
"

# Redis health (if enabled)
redis-cli ping

# Python environment
python --version
pip list | grep -E "(streamlit|pandas|plotly)"
```

## 📈 Advanced Configuration

### **Performance Optimization**

#### **Database Performance**
```sql
-- Add indexes for better query performance
CREATE INDEX idx_portfolio_positions_symbol ON portfolio_positions(symbol);
CREATE INDEX idx_trading_signals_date ON trading_signals(signal_date);
CREATE INDEX idx_price_history_symbol_date ON price_history(symbol, date);
```

#### **Redis Caching**
```bash
# Optimize Redis memory usage
echo "maxmemory 1gb" >> /etc/redis/redis.conf
echo "maxmemory-policy allkeys-lru" >> /etc/redis/redis.conf
sudo systemctl restart redis
```

#### **Streamlit Configuration**
Create `~/.streamlit/config.toml`:
```toml
[server]
port = 8501
headless = true
enableCORS = false

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
```

### **Production Deployment**

#### **Environment Configuration**
```bash
# Production settings in .env
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
STREAMLIT_SERVER_HEADLESS=true
```

#### **Process Management**
```bash
# Using systemd
sudo tee /etc/systemd/system/hk-dashboard.service << EOF
[Unit]
Description=HK Strategy Dashboard
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/hk-strategy-mvp
Environment=PATH=/opt/hk-strategy-mvp/venv/bin
ExecStart=/opt/hk-strategy-mvp/venv/bin/streamlit run dashboard.py --server.port=8501
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable hk-dashboard
sudo systemctl start hk-dashboard
```

#### **Reverse Proxy (Nginx)**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### **Backup & Recovery**

#### **Database Backup**
```bash
# Create backup
pg_dump -h localhost -U trader hk_strategy > backup_$(date +%Y%m%d).sql

# Restore backup
psql -h localhost -U trader hk_strategy < backup_20250906.sql
```

#### **Configuration Backup**
```bash
# Backup configuration files
tar -czf config_backup_$(date +%Y%m%d).tar.gz .env config/ *.sh
```

## 🎉 You're All Set!

Your HK Strategy Dashboard should now be running with:

- ✅ **Modern Modular Architecture** (Phases 1-5 Complete)
- ✅ **35+ UI Components** for consistent user experience  
- ✅ **Comprehensive Portfolio Management**
- ✅ **Advanced Technical Analysis**
- ✅ **Professional Navigation System**
- ✅ **Production-Ready Configuration**

**Next Steps:**
1. Visit `http://localhost:8501` to access your dashboard
2. Create your first portfolio in the "All Portfolio Overviews" section
3. Add some HK stock positions (e.g., 0700.HK, 9988.HK)
4. Explore the Strategy Analysis section for technical indicators
5. Check System Status for health monitoring

**Need Help?**
- 📖 Check the main [README.md](README.md) for feature details
- 🏗️ Review [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- 🐛 Report issues in the project's issue tracker
- 💬 Join community discussions for support

Happy Trading! 📈