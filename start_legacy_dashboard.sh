#!/bin/bash

echo "🏦 HK Strategy Legacy Dashboard Startup"
echo "======================================="
echo "📜 Starting ORIGINAL monolithic dashboard (6000 lines)"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_status "🔍 Preparing legacy dashboard..."

# Check if original dashboard exists
if [ ! -f "dashboard.py" ]; then
    print_error "dashboard.py not found!"
    exit 1
fi

print_success "Legacy dashboard found (dashboard.py)"

print_status "1. Starting PostgreSQL with Docker..."
if command -v docker-compose >/dev/null 2>&1; then
    docker-compose up -d postgres
    if [ $? -eq 0 ]; then
        print_success "PostgreSQL started with Docker"
    else
        print_warning "Failed to start PostgreSQL with Docker, continuing anyway"
    fi
else
    print_warning "Docker Compose not found, assuming PostgreSQL is running"
fi

print_status "2. Waiting for PostgreSQL to be ready..."
sleep 5

print_status "3. Installing Python dependencies..."
pip3 install -r requirements.txt
if [ $? -eq 0 ]; then
    print_success "Dependencies installed"
else
    print_error "Failed to install dependencies"
    exit 1
fi

print_status "4. Testing database connection..."
if [ -f "test_db.py" ]; then
    python3 test_db.py
    if [ $? -eq 0 ]; then
        print_success "Database connection successful"
        print_status "5. Starting original Streamlit dashboard..."
        echo ""
        echo "💡 Original dashboard features:"
        echo "  • 📊 Complete portfolio management"
        echo "  • 🎯 Full strategy analysis suite"
        echo "  • 📈 Advanced technical indicators"
        echo "  • ⚙️ System monitoring and admin tools"
        echo "  • 🗄️ Database management utilities"
        echo ""
        echo "⚠️  Note: This is the original 6000-line monolithic version"
        echo "   For the new modular version, use: ./start_modular_dashboard.sh"
        echo ""
        
        streamlit run dashboard.py --server.port=8502 --server.address=localhost
    else
        print_error "Database test failed. Check PostgreSQL setup."
        echo ""
        echo "🔧 Quick troubleshooting:"
        echo "  • Run: ./setup_local_db.sh"
        echo "  • Check .env file configuration"
        echo "  • Verify PostgreSQL is running"
        exit 1
    fi
else
    print_warning "Database test script not found, starting dashboard anyway..."
    streamlit run dashboard.py --server.port=8502 --server.address=localhost
fi