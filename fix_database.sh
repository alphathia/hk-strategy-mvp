#!/bin/bash

echo "🔧 HK Strategy PostgreSQL Database Setup"
echo "========================================"

# Check if running as root or with sudo access
if [ "$EUID" -eq 0 ]; then
    echo "✅ Running with root privileges"
elif sudo -n true 2>/dev/null; then 
    echo "✅ Sudo access available"
else
    echo "❌ This script requires sudo access to set up PostgreSQL"
    echo "Please run: sudo ./fix_database.sh"
    exit 1
fi

echo ""
echo "🔍 Step 1: Checking PostgreSQL status..."

# Check if PostgreSQL is running
if pgrep -x "postgres" > /dev/null; then
    echo "✅ PostgreSQL is running"
else
    echo "❌ PostgreSQL is not running. Starting it..."
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    sleep 3
fi

echo ""
echo "🔍 Step 2: Checking existing users and databases..."

# List current users (as postgres user)
echo "Current PostgreSQL users:"
sudo -u postgres psql -c "\du"

echo ""
echo "Current databases:"
sudo -u postgres psql -c "\l"

echo ""
echo "🔧 Step 3: Setting up trader user and hk_strategy database..."

# Create the database setup
sudo -u postgres psql << 'EOF'
-- Drop existing user if exists (to start fresh)
DROP USER IF EXISTS trader;

-- Create trader user with password
CREATE USER trader WITH PASSWORD 'xxxxx';

-- Grant necessary privileges
ALTER USER trader CREATEDB;

-- Drop existing database if exists
DROP DATABASE IF EXISTS hk_strategy;

-- Create hk_strategy database with trader as owner
CREATE DATABASE hk_strategy OWNER trader;

-- Grant all privileges on database to trader
GRANT ALL PRIVILEGES ON DATABASE hk_strategy TO trader;

-- List users to confirm
\du

-- List databases to confirm
\l

-- Quit
\q
EOF

if [ $? -eq 0 ]; then
    echo "✅ Database and user created successfully"
else
    echo "❌ Failed to create database and user"
    exit 1
fi

echo ""
echo "🔍 Step 4: Testing connection..."

# Test the connection
PGPASSWORD=trading123 psql -U trader -h localhost -d hk_strategy -c "SELECT version();"

if [ $? -eq 0 ]; then
    echo "✅ Connection test successful"
else
    echo "❌ Connection test failed"
    echo "Trying to fix authentication..."
    
    # Check and potentially fix pg_hba.conf
    PG_VERSION=$(sudo -u postgres psql -t -c "SELECT version();" | grep -oE '[0-9]+\.[0-9]+' | head -1)
    PG_HBA="/etc/postgresql/$PG_VERSION/main/pg_hba.conf"
    
    if [ -f "$PG_HBA" ]; then
        echo "📝 Updating PostgreSQL authentication config..."
        sudo cp "$PG_HBA" "$PG_HBA.backup"
        
        # Ensure local connections use md5 authentication
        sudo sed -i 's/local   all             all                                     peer/local   all             all                                     md5/' "$PG_HBA"
        sudo sed -i 's/local   all             postgres                                peer/local   all             postgres                                md5/' "$PG_HBA"
        
        # Restart PostgreSQL to apply changes
        sudo systemctl restart postgresql
        sleep 3
        
        # Test again
        PGPASSWORD=trading123 psql -U trader -h localhost -d hk_strategy -c "SELECT version();"
        
        if [ $? -eq 0 ]; then
            echo "✅ Connection successful after authentication fix"
        else
            echo "❌ Still having connection issues"
            echo "Please check the troubleshooting section"
        fi
    else
        echo "❌ Could not find pg_hba.conf file"
    fi
fi

echo ""
echo "🔍 Step 5: Initializing database tables..."

if [ -f "init.sql" ]; then
    echo "📊 Running init.sql..."
    PGPASSWORD=trading123 psql -U trader -h localhost -d hk_strategy -f init.sql
    
    if [ $? -eq 0 ]; then
        echo "✅ Database initialized successfully"
        
        # Verify tables were created
        echo ""
        echo "📋 Verifying tables..."
        PGPASSWORD=trading123 psql -U trader -h localhost -d hk_strategy -c "\dt"
        
        # Check if data was inserted
        echo ""
        echo "📊 Checking portfolio data..."
        PGPASSWORD=trading123 psql -U trader -h localhost -d hk_strategy -c "SELECT symbol, company_name, quantity FROM portfolio_positions LIMIT 5;"
        
    else
        echo "❌ Failed to initialize database with init.sql"
    fi
else
    echo "⚠️ init.sql file not found in current directory"
    echo "Please make sure init.sql is in the same directory as this script"
fi

echo ""
echo "🎯 Setup Summary:"
echo "=================="
echo "Database: hk_strategy"
echo "User: trader"
echo "Password: trading123"
echo "Connection: postgresql://trader:trading123@localhost:5432/hk_strategy"
echo ""
echo "Test your connection:"
echo "PGPASSWORD=trading123 psql -U trader -h localhost -d hk_strategy"
echo ""
echo "🔄 Now refresh the system status in your Streamlit dashboard!"