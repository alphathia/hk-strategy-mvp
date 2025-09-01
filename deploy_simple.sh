#!/bin/bash

echo "🏦 HK Strategy Dashboard - Simple Deployment"
echo "============================================"

# Load environment variables
if [ -f .env ]; then
    echo "📝 Loading environment variables..."
    export $(grep -v '^#' .env | xargs)
else
    echo "❌ .env file not found"
    exit 1
fi

# Check PostgreSQL
if ! pgrep -x "postgres" > /dev/null; then
    echo "❌ PostgreSQL is not running"
    exit 1
fi
echo "✅ PostgreSQL is running"

# Try to connect to existing database first
echo "🔍 Checking existing database connection..."
PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -h $DB_HOST -d $DB_NAME -c "SELECT 1;" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Database connection successful - using existing database"
else
    echo "⚠️ Cannot connect to database. You may need to:"
    echo "  1. Create the database and user manually, or"
    echo "  2. Update the credentials in .env file"
    echo ""
    echo "Try connecting with existing credentials:"
    echo "PGPASSWORD=trading123 psql -U trader -h localhost -d hk_strategy"
    echo ""
    read -p "Do you want to continue with schema updates anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "📊 Applying schema updates..."
PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -h $DB_HOST -d $DB_NAME -f init.sql

if [ $? -eq 0 ]; then
    echo "✅ Schema updated successfully"
else
    echo "⚠️ Schema update had issues, but continuing..."
fi

echo "📦 Setting up Python environment..."
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "🧪 Testing application..."
python3 -c "
try:
    import streamlit
    import pandas
    import plotly
    import yfinance
    print('✅ Core dependencies loaded successfully')
    
    # Test our new modules
    import sys
    sys.path.append('src')
    from hkex_calendar import hkex_calendar
    from portfolio_calculator import portfolio_calculator
    from analysis_manager import AnalysisManager
    print('✅ New PV analysis modules loaded successfully')
    
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎯 Deployment successful!"
    echo "========================"
    echo ""
    echo "🆕 NEW FEATURES AVAILABLE:"
    echo "   • Portfolio Value (PV) Chart Analysis"
    echo "   • HKEX Trading Days Calendar"
    echo "   • Historical Performance Tracking"
    echo "   • Save/Load Analysis Functionality"
    echo "   • Interactive Tooltips with Contributors"
    echo ""
    echo "🚀 To start the dashboard:"
    echo "   source venv/bin/activate"
    echo "   streamlit run dashboard.py"
    echo ""
    echo "🌐 Then open: http://localhost:8501"
    echo ""
else
    echo "❌ Application test failed"
    exit 1
fi