#!/bin/bash

echo "🏦 HK Strategy Dashboard Startup"
echo "================================"

echo "1. Starting PostgreSQL with Docker..."
docker-compose up -d postgres

echo "2. Waiting for PostgreSQL to be ready..."
sleep 5

echo "3. Installing Python dependencies..."
pip install -r requirements.txt

echo "4. Testing database connection..."
python test_db.py

if [ $? -eq 0 ]; then
    echo "5. Starting Streamlit dashboard..."
    streamlit run dashboard.py
else
    echo "❌ Database test failed. Check PostgreSQL setup."
fi