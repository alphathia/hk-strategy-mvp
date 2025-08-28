#!/bin/bash

# HK Strategy Portfolio Dashboard - System Health Check Script

echo "🔍 HK Strategy Portfolio Dashboard - System Health Check"
echo "======================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo "🐍 Python Environment:"
echo "---------------------"

# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✅ Python: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}❌ Python 3 not found${NC}"
fi

# Check virtual environment
if [ -d "venv" ]; then
    echo -e "${GREEN}✅ Virtual environment exists${NC}"
    if [ -n "$VIRTUAL_ENV" ]; then
        echo -e "${GREEN}✅ Virtual environment is activated${NC}"
    else
        echo -e "${YELLOW}⚠️  Virtual environment not activated${NC}"
        echo "   Run: source venv/bin/activate"
    fi
else
    echo -e "${RED}❌ Virtual environment not found${NC}"
    echo "   Run: python3 -m venv venv"
fi

echo ""
echo "📦 Python Dependencies:"
echo "----------------------"

# Check if in virtual environment for dependency check
if [ -n "$VIRTUAL_ENV" ] || [ -f "venv/bin/python" ]; then
    PYTHON_CMD="${VIRTUAL_ENV:-./venv}/bin/python"
    
    # Check critical dependencies
    dependencies=("streamlit" "psycopg2" "redis" "yfinance" "pandas" "plotly")
    for dep in "${dependencies[@]}"; do
        if $PYTHON_CMD -c "import $dep" 2>/dev/null; then
            VERSION=$($PYTHON_CMD -c "import $dep; print(getattr($dep, '__version__', 'unknown'))" 2>/dev/null)
            echo -e "${GREEN}✅ $dep: $VERSION${NC}"
        else
            echo -e "${RED}❌ $dep not installed${NC}"
        fi
    done
else
    echo -e "${YELLOW}⚠️  Virtual environment not available for dependency check${NC}"
fi

echo ""
echo "🗄️  Database (PostgreSQL):"
echo "-------------------------"

# Check PostgreSQL service
if pgrep -f postgres > /dev/null; then
    echo -e "${GREEN}✅ PostgreSQL processes running${NC}"
    
    # Try to connect to database
    if command -v psql &> /dev/null; then
        # Try to connect using environment variable or prompt for password
        if [ -n "$DATABASE_PASSWORD" ]; then
            DB_PASS="$DATABASE_PASSWORD"
        elif [ -f "config/.env" ] && grep -q "DATABASE_PASSWORD" config/.env; then
            DB_PASS=$(grep "DATABASE_PASSWORD" config/.env | cut -d'=' -f2)
        else
            DB_PASS="YOUR_PASSWORD"
            echo -e "${YELLOW}⚠️  Set DATABASE_PASSWORD environment variable for connection test${NC}"
        fi
        
        if PGPASSWORD="$DB_PASS" psql -U trader -h localhost -d hk_strategy -c "SELECT 1;" &>/dev/null 2>&1; then
            echo -e "${GREEN}✅ Database connection successful${NC}"
            
            # Check if tables exist
            TABLE_COUNT=$(PGPASSWORD="$DB_PASS" psql -U trader -h localhost -d hk_strategy -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ')
            if [ "$TABLE_COUNT" -gt 0 ]; then
                echo -e "${GREEN}✅ Database tables found: $TABLE_COUNT${NC}"
            else
                echo -e "${YELLOW}⚠️  No tables found - run initialization${NC}"
            fi
        else
            echo -e "${RED}❌ Database connection failed${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  psql command not found${NC}"
    fi
else
    echo -e "${RED}❌ PostgreSQL not running${NC}"
    echo "   Start with: sudo systemctl start postgresql"
fi

echo ""
echo "🔄 Cache (Redis):"
echo "----------------"

# Check Redis service
if pgrep -f redis > /dev/null; then
    echo -e "${GREEN}✅ Redis processes running${NC}"
    
    # Try to connect to Redis
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping &>/dev/null; then
            echo -e "${GREEN}✅ Redis connection successful${NC}"
            REDIS_VERSION=$(redis-cli INFO server | grep "redis_version" | cut -d: -f2 | tr -d '\r')
            echo -e "${GREEN}✅ Redis version: $REDIS_VERSION${NC}"
        else
            echo -e "${RED}❌ Redis connection failed${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  redis-cli command not found${NC}"
    fi
else
    echo -e "${RED}❌ Redis not running${NC}"
    echo "   Start with: sudo systemctl start redis-server"
fi

echo ""
echo "⚙️  Configuration:"
echo "-----------------"

# Check configuration files
if [ -f "config/app_config.yaml" ]; then
    echo -e "${GREEN}✅ Main config file exists${NC}"
else
    echo -e "${RED}❌ config/app_config.yaml not found${NC}"
    echo "   Run: ./setup_security.sh"
fi

if [ -f "config/.env" ]; then
    echo -e "${GREEN}✅ Environment file exists${NC}"
else
    echo -e "${YELLOW}⚠️  config/.env not found (optional)${NC}"
fi

# Check src/config_manager.py
if [ -f "src/config_manager.py" ]; then
    echo -e "${GREEN}✅ Configuration manager available${NC}"
else
    echo -e "${RED}❌ src/config_manager.py not found${NC}"
fi

echo ""
echo "🌐 Network & APIs:"
echo "-----------------"

# Test internet connectivity
if ping -c 1 finance.yahoo.com &>/dev/null; then
    echo -e "${GREEN}✅ Internet connectivity to Yahoo Finance${NC}"
else
    echo -e "${RED}❌ Cannot reach Yahoo Finance${NC}"
fi

# Check if ports are available
if command -v netstat &> /dev/null; then
    if netstat -tlnp 2>/dev/null | grep :8501 > /dev/null; then
        echo -e "${YELLOW}⚠️  Port 8501 already in use${NC}"
    else
        echo -e "${GREEN}✅ Port 8501 available${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  netstat not available for port check${NC}"
fi

echo ""
echo "📁 File System:"
echo "--------------"

# Check important files
files=("dashboard_editable.py" "requirements.txt" "init.sql" ".gitignore")
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file exists${NC}"
    else
        echo -e "${RED}❌ $file missing${NC}"
    fi
done

# Check directories
dirs=("logs" "config")
for dir in "${dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✅ $dir/ directory exists${NC}"
    else
        echo -e "${YELLOW}⚠️  $dir/ directory missing${NC}"
    fi
done

echo ""
echo "📋 Summary:"
echo "----------"
echo "If all checks show ✅, you can start the application with:"
echo "   ./start_app.sh"
echo ""
echo "For any ❌ or ⚠️ issues, check the installation manual:"
echo "   INSTALLATION_MANUAL.md"
echo ""