#!/bin/bash

# HK Strategy Portfolio Dashboard - Application Startup Script

set -e  # Exit on any error

echo "🚀 Starting HK Strategy Portfolio Dashboard..."
echo "=============================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating one...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if requirements are installed
echo "📦 Checking Python dependencies..."
if ! python -c "import streamlit, psycopg2, redis, yfinance" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Some dependencies missing. Installing requirements...${NC}"
    pip install --upgrade pip
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${GREEN}✅ All dependencies available${NC}"
fi

# Check if configuration files exist
echo "⚙️  Checking configuration..."
if [ ! -f "config/app_config.yaml" ]; then
    echo -e "${YELLOW}⚠️  Configuration file not found. Running security setup...${NC}"
    ./setup_security.sh
fi

# Load environment variables from config if available
if [ -f "config/.env" ]; then
    echo "🔧 Loading environment variables from config/.env..."
    export $(grep -v '^#' config/.env | xargs)
    echo -e "${GREEN}✅ Environment variables loaded${NC}"
fi

# Create logs directory if it doesn't exist
mkdir -p logs

echo ""
echo "🏃 Starting Streamlit application..."
echo "Application will be available at: http://localhost:8501"
echo "Press Ctrl+C to stop the application"
echo ""

# Start the application
streamlit run dashboard_editable.py --server.port 8501 --server.address 0.0.0.0