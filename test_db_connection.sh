#!/bin/bash

echo "🔍 Testing Database Connection with Secure Password"
echo "=================================================="

# Load the password from config
if [ -f "config/.env" ]; then
    export $(grep -v '^#' config/.env | grep DATABASE_PASSWORD | xargs)
    echo "✅ Password loaded from config/.env"
else
    echo "❌ config/.env not found"
    exit 1
fi

if [ -z "$DATABASE_PASSWORD" ]; then
    echo "❌ DATABASE_PASSWORD not found in config/.env"
    exit 1
fi

echo "Password found: ${DATABASE_PASSWORD:0:4}****"

echo ""
echo "🔍 Testing connection..."

# Test connection
if PGPASSWORD="$DATABASE_PASSWORD" psql -U trader -h localhost -d hk_strategy -c "SELECT version();" 2>/dev/null; then
    echo "✅ Database connection successful!"
    
    # Check if tables exist
    TABLE_COUNT=$(PGPASSWORD="$DATABASE_PASSWORD" psql -U trader -h localhost -d hk_strategy -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ')
    
    if [ "$TABLE_COUNT" -gt 0 ]; then
        echo "✅ Found $TABLE_COUNT tables in database"
        
        # Check for portfolio_positions table specifically
        if PGPASSWORD="$DATABASE_PASSWORD" psql -U trader -h localhost -d hk_strategy -c "\dt portfolio_positions" 2>/dev/null | grep -q "portfolio_positions"; then
            echo "✅ portfolio_positions table exists"
            
            # Count rows
            ROW_COUNT=$(PGPASSWORD="$DATABASE_PASSWORD" psql -U trader -h localhost -d hk_strategy -t -c "SELECT COUNT(*) FROM portfolio_positions;" 2>/dev/null | tr -d ' ')
            echo "✅ Portfolio positions: $ROW_COUNT rows"
        else
            echo "⚠️  portfolio_positions table missing - need to run init.sql"
        fi
    else
        echo "⚠️  No tables found - need to initialize database"
    fi
    
else
    echo "❌ Database connection failed"
    echo ""
    echo "This usually means:"
    echo "1. PostgreSQL user 'trader' doesn't exist, OR"
    echo "2. Password doesn't match, OR" 
    echo "3. Database 'hk_strategy' doesn't exist"
    echo ""
    echo "To fix this, run as postgres superuser:"
    echo "sudo -u postgres psql -f fix_database_manual.sql"
fi