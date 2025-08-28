#!/bin/bash

# Secure Database Setup Script - Uses password from .env file only

echo "🔐 Secure Database Setup (from .env)"
echo "===================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Load password from .env file
if [ ! -f "config/.env" ]; then
    echo -e "${RED}❌ config/.env file not found${NC}"
    echo "Run ./setup_security.sh first to create secure configuration files"
    exit 1
fi

# Extract DATABASE_PASSWORD from .env
DATABASE_PASSWORD=$(grep "^DATABASE_PASSWORD=" config/.env | cut -d'=' -f2)

if [ -z "$DATABASE_PASSWORD" ]; then
    echo -e "${RED}❌ DATABASE_PASSWORD not found in config/.env${NC}"
    echo "Run ./setup_security.sh to generate secure passwords"
    exit 1
fi

echo -e "${GREEN}✅ Password loaded from config/.env${NC}"
echo "Password: ${DATABASE_PASSWORD:0:4}****"

# Check if running with proper privileges
if [ "$EUID" -eq 0 ]; then
    echo -e "${GREEN}✅ Running with root privileges${NC}"
elif sudo -n true 2>/dev/null; then 
    echo -e "${GREEN}✅ Sudo access available${NC}"
else
    echo -e "${RED}❌ This script requires sudo access${NC}"
    echo "Please run: sudo ./setup_database_from_env.sh"
    exit 1
fi

echo ""
echo "🔧 Setting up PostgreSQL user and database..."

# Create user and database using the password from .env
sudo -u postgres psql -c "
DO \$\$
BEGIN
    IF EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'trader') THEN
        ALTER USER trader WITH PASSWORD '$DATABASE_PASSWORD';
        RAISE NOTICE 'User trader password updated from .env file';
    ELSE
        CREATE USER trader WITH PASSWORD '$DATABASE_PASSWORD';
        RAISE NOTICE 'User trader created with password from .env file';
    END IF;
END
\$\$;

SELECT 'CREATE DATABASE hk_strategy OWNER trader'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'hk_strategy')\gexec

GRANT ALL PRIVILEGES ON DATABASE hk_strategy TO trader;
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Database user and database created successfully${NC}"
else
    echo -e "${RED}❌ Database setup failed${NC}"
    exit 1
fi

echo ""
echo "🔍 Testing database connection..."

# Test connection using the password from .env
if PGPASSWORD="$DATABASE_PASSWORD" psql -U trader -h localhost -d hk_strategy -c "SELECT version();" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Database connection successful${NC}"
    
    # Initialize with portfolio data if init.sql exists
    if [ -f "init.sql" ]; then
        echo ""
        echo "📊 Initializing database with portfolio data..."
        if PGPASSWORD="$DATABASE_PASSWORD" psql -U trader -h localhost -d hk_strategy -f init.sql >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Portfolio data loaded successfully${NC}"
            
            # Verify data
            ROW_COUNT=$(PGPASSWORD="$DATABASE_PASSWORD" psql -U trader -h localhost -d hk_strategy -t -c "SELECT COUNT(*) FROM portfolio_positions;" 2>/dev/null | tr -d ' ')
            if [ "$ROW_COUNT" -gt 0 ]; then
                echo -e "${GREEN}✅ Verified: $ROW_COUNT portfolio positions loaded${NC}"
            fi
        else
            echo -e "${YELLOW}⚠️  Failed to load portfolio data${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  init.sql not found, skipping portfolio data initialization${NC}"
    fi
else
    echo -e "${RED}❌ Database connection test failed${NC}"
    echo "Check PostgreSQL configuration and try again"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Database setup complete!${NC}"
echo ""
echo "📋 Summary:"
echo "----------"
echo "• Database: hk_strategy"
echo "• User: trader" 
echo "• Password: [Loaded from config/.env]"
echo ""
echo "🔒 Security:"
echo "• Password stored ONLY in config/.env (gitignored)"
echo "• No passwords in code or other files"
echo ""
echo "🧪 Test connection:"
echo "./test_db_connection.sh"
echo ""