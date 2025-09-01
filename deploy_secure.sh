#!/bin/bash

echo "🏦 HK Strategy Dashboard - Secure Deployment"
echo "============================================="

# Load environment variables from .env file
if [ -f .env ]; then
    echo "📝 Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
    echo "✅ Environment variables loaded"
else
    echo "❌ .env file not found. Please create one based on .env.example"
    exit 1
fi

echo "🔧 Checking PostgreSQL status..."
if ! pgrep -x "postgres" > /dev/null; then
    echo "❌ PostgreSQL is not running"
    echo "Start it with: sudo systemctl start postgresql"
    exit 1
fi
echo "✅ PostgreSQL is running"

echo "🗄️  Setting up database and user..."

# Create database and user securely using environment variables
sudo -u postgres psql << EOF
-- Create user with password from environment
DO \$\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$DB_USER') THEN
      CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
   END IF;
END
\$\$;

-- Create database
DROP DATABASE IF EXISTS $DB_NAME;
CREATE DATABASE $DB_NAME OWNER $DB_USER;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
GRANT CREATE ON SCHEMA public TO $DB_USER;

\q
EOF

if [ $? -eq 0 ]; then
    echo "✅ Database and user created successfully"
else
    echo "❌ Failed to create database"
    exit 1
fi

echo "📊 Initializing database with updated schema..."
PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -h $DB_HOST -d $DB_NAME -f init.sql

if [ $? -eq 0 ]; then
    echo "✅ Database initialized with HKEX portfolio data and PV analysis tables"
else
    echo "❌ Failed to initialize database"
    exit 1
fi

echo "📦 Installing Python dependencies..."
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "🔧 Testing database connection..."
python3 -c "
import os
from src.database import DatabaseManager
try:
    db = DatabaseManager()
    positions = db.get_portfolio_positions()
    print(f'✅ Database connection successful! Found {len(positions)} portfolio positions')
    
    # Test new PV analysis tables
    analyses = db.get_portfolio_analyses(limit=5)
    print(f'✅ PV analysis tables ready! Found {len(analyses)} saved analyses')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎯 Deployment successful!"
    echo "========================="
    echo ""
    echo "📊 Your database includes:"
    echo "   • Portfolio positions with HKEX stock data"
    echo "   • Trading signals tracking"
    echo "   • NEW: Portfolio Value analysis tables"
    echo "   • NEW: Historical value tracking"
    echo ""
    echo "🚀 To start the dashboard:"
    echo "   source venv/bin/activate"
    echo "   streamlit run dashboard.py"
    echo ""
    echo "🌐 Dashboard will be available at: http://localhost:8501"
    echo ""
    echo "🆕 NEW FEATURES:"
    echo "   • Portfolio Value (PV) Chart analysis"
    echo "   • HKEX trading days filtering"
    echo "   • Save/load analysis functionality"
    echo "   • Performance metrics (returns, drawdown, volatility)"
    echo "   • Interactive tooltips with daily contributors"
else
    echo "❌ Database test failed"
    exit 1
fi