#!/bin/bash

# HK Strategy Portfolio Dashboard - Secure Database Setup Script

set -e  # Exit on any error

echo "🗄️  PostgreSQL Database Setup - Secure Version"
echo "================================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to generate a secure password
generate_password() {
    if command -v openssl &> /dev/null; then
        openssl rand -base64 32 | tr -d "=+/" | cut -c1-16
    else
        # Fallback if openssl is not available
        cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1
    fi
}

# Check if running as sudo
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ This script requires sudo access${NC}"
    echo "Please run: sudo ./fix_database_secure.sh"
    exit 1
fi

echo "🔧 Setting up PostgreSQL database and user..."

# Check if PostgreSQL is installed and running
if ! systemctl is-active --quiet postgresql; then
    echo "🚀 Starting PostgreSQL service..."
    systemctl start postgresql
    systemctl enable postgresql
fi

# Generate secure password if not provided
if [ -z "$DATABASE_PASSWORD" ]; then
    DATABASE_PASSWORD=$(generate_password)
    echo -e "${GREEN}✅ Generated secure password for database user${NC}"
else
    echo -e "${GREEN}✅ Using provided DATABASE_PASSWORD${NC}"
fi

echo ""
echo "👤 Creating database user and database..."

# Create user and database as postgres user
sudo -u postgres psql -c "
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'trader') THEN
        CREATE USER trader WITH PASSWORD '$DATABASE_PASSWORD';
        RAISE NOTICE 'User trader created';
    ELSE
        ALTER USER trader WITH PASSWORD '$DATABASE_PASSWORD';
        RAISE NOTICE 'User trader password updated';
    END IF;
END
\$\$;

-- Create database if it doesn't exist
SELECT 'CREATE DATABASE hk_strategy OWNER trader'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'hk_strategy')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE hk_strategy TO trader;
" 2>/dev/null

echo -e "${GREEN}✅ Database user 'trader' configured${NC}"
echo -e "${GREEN}✅ Database 'hk_strategy' created/verified${NC}"

# Test connection
echo ""
echo "🔍 Testing database connection..."
if PGPASSWORD="$DATABASE_PASSWORD" psql -U trader -h localhost -d hk_strategy -c "SELECT version();" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Database connection successful${NC}"
else
    echo -e "${RED}❌ Database connection failed${NC}"
    echo "This might be due to PostgreSQL authentication settings."
    
    # Fix authentication if needed
    echo ""
    echo "🔧 Checking PostgreSQL authentication settings..."
    
    PG_VERSION=$(psql --version | awk '{print $3}' | sed 's/\..*//')
    PG_HBA_FILE="/etc/postgresql/$PG_VERSION/main/pg_hba.conf"
    
    if [ -f "$PG_HBA_FILE" ]; then
        echo "Updating PostgreSQL authentication..."
        
        # Backup original
        cp "$PG_HBA_FILE" "$PG_HBA_FILE.backup.$(date +%Y%m%d)"
        
        # Update authentication method
        sed -i 's/local   all             postgres                                peer/local   all             postgres                                md5/' "$PG_HBA_FILE"
        sed -i 's/local   all             all                                     peer/local   all             all                                     md5/' "$PG_HBA_FILE"
        
        echo "Restarting PostgreSQL..."
        systemctl restart postgresql
        
        # Test again
        sleep 3
        if PGPASSWORD="$DATABASE_PASSWORD" psql -U trader -h localhost -d hk_strategy -c "SELECT version();" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Database connection successful after auth fix${NC}"
        else
            echo -e "${RED}❌ Database connection still failing${NC}"
            echo "Manual intervention may be required."
        fi
    fi
fi

# Initialize database with sample data
echo ""
echo "📊 Initializing database with HKEX portfolio data..."
if [ -f "init.sql" ]; then
    if PGPASSWORD="$DATABASE_PASSWORD" psql -U trader -h localhost -d hk_strategy -f init.sql >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Database initialized with portfolio data${NC}"
        
        # Verify data
        ROW_COUNT=$(PGPASSWORD="$DATABASE_PASSWORD" psql -U trader -h localhost -d hk_strategy -t -c "SELECT COUNT(*) FROM portfolio_positions;" 2>/dev/null | tr -d ' ')
        if [ "$ROW_COUNT" -gt 0 ]; then
            echo -e "${GREEN}✅ Portfolio data verified: $ROW_COUNT positions loaded${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Database initialization failed, but user/database are created${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  init.sql not found, skipping data initialization${NC}"
fi

echo ""
echo "💾 Saving database configuration..."

# Create config directory if it doesn't exist
mkdir -p config

# Save password to environment file (will be gitignored)
ENV_FILE="config/.env"
if [ ! -f "$ENV_FILE" ] || ! grep -q "DATABASE_PASSWORD" "$ENV_FILE"; then
    echo "DATABASE_PASSWORD=$DATABASE_PASSWORD" >> "$ENV_FILE"
    echo -e "${GREEN}✅ Database password saved to config/.env${NC}"
else
    # Update existing password
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/DATABASE_PASSWORD=.*/DATABASE_PASSWORD=$DATABASE_PASSWORD/" "$ENV_FILE"
    else
        # Linux
        sed -i "s/DATABASE_PASSWORD=.*/DATABASE_PASSWORD=$DATABASE_PASSWORD/" "$ENV_FILE"
    fi
    echo -e "${GREEN}✅ Database password updated in config/.env${NC}"
fi

# Also update the main config file if it exists
CONFIG_FILE="config/app_config.yaml"
if [ -f "$CONFIG_FILE" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/password: .*/password: \"$DATABASE_PASSWORD\"/" "$CONFIG_FILE"
    else
        # Linux
        sed -i "s/password: .*/password: \"$DATABASE_PASSWORD\"/" "$CONFIG_FILE"
    fi
    echo -e "${GREEN}✅ Database password updated in config/app_config.yaml${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Database setup complete!${NC}"
echo ""
echo "📋 Summary:"
echo "----------"
echo "Database: hk_strategy"
echo "User: trader"
echo "Password: [SAVED IN config/.env]"
echo ""
echo "🔒 Security Notes:"
echo "• Password is saved in config/.env (gitignored)"
echo "• Use environment variables in production"
echo "• Password is also saved in config/app_config.yaml if it exists"
echo ""
echo "🚀 Next steps:"
echo "• Test connection: ./health_check.sh"
echo "• Start application: ./start_app.sh"
echo ""