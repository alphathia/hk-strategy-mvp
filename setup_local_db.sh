#!/bin/bash

echo "🏦 Setting up HK Strategy Database Locally"
echo "=========================================="

# Check if PostgreSQL is running
if ! pgrep -x "postgres" > /dev/null; then
    echo "❌ PostgreSQL is not running"
    echo "Start it with: sudo systemctl start postgresql"
    exit 1
fi

echo "✅ PostgreSQL is running"

# Create user and database as postgres superuser
echo "📝 Creating database user and schema..."

sudo -u postgres psql << EOF
-- Create user
CREATE USER IF NOT EXISTS trader WITH PASSWORD 'YOUR_SECURE_PASSWORD';

-- Create database
DROP DATABASE IF EXISTS hk_strategy;
CREATE DATABASE hk_strategy OWNER trader;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE hk_strategy TO trader;

\q
EOF

if [ $? -eq 0 ]; then
    echo "✅ Database and user created successfully"
else
    echo "❌ Failed to create database"
    exit 1
fi

# Run init.sql to create tables and insert data
echo "📊 Running init.sql to create tables and insert HKEX data..."

PGPASSWORD=trading123 psql -U trader -h localhost -d hk_strategy -f init.sql

if [ $? -eq 0 ]; then
    echo "✅ Database initialized with HKEX portfolio data"
else
    echo "❌ Failed to initialize database"
    exit 1
fi

# Test the connection
echo "🔧 Testing database connection..."
PGPASSWORD=trading123 psql -U trader -h localhost -d hk_strategy -c "\dt"

echo ""
echo "📊 Checking portfolio data..."
PGPASSWORD=trading123 psql -U trader -h localhost -d hk_strategy -c "SELECT symbol, company_name, quantity, avg_cost FROM portfolio_positions LIMIT 5;"

echo ""
echo "🎯 Database setup complete! You can now run:"
echo "streamlit run dashboard.py"