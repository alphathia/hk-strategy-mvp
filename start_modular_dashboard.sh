#!/bin/bash

echo "🏦 HK Strategy Modular Dashboard Startup"
echo "======================================="
echo "📄 Starting NEW modular dashboard (Phase 1-4 Complete)"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

print_status "🔍 Checking system requirements..."

# Check Python
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    print_success "Python found: $PYTHON_VERSION"
else
    print_error "Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

# Check pip
if command_exists pip3; then
    print_success "pip3 found"
else
    print_error "pip3 not found. Please install pip3."
    exit 1
fi

# Check Streamlit
if python3 -c "import streamlit" 2>/dev/null; then
    STREAMLIT_VERSION=$(python3 -c "import streamlit as st; print(st.__version__)" 2>/dev/null)
    print_success "Streamlit found: $STREAMLIT_VERSION"
else
    print_warning "Streamlit not found. Installing requirements..."
fi

print_status "📦 Installing/updating Python dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    print_error "Failed to install requirements. Please check requirements.txt"
    exit 1
fi

print_success "Dependencies installed successfully"

print_status "🔧 Validating environment variables..."
# Check for .env file
if [ -f .env ]; then
    print_success ".env file found"
    
    # Source .env file to check variables
    source .env
    
    # Check critical environment variables
    if [ -z "$DB_HOST" ] || [ -z "$DB_NAME" ] || [ -z "$DB_USER" ]; then
        print_warning "Missing critical database environment variables"
        echo "Please ensure the following are set in .env:"
        echo "  - DB_HOST"
        echo "  - DB_NAME" 
        echo "  - DB_USER"
        echo "  - DB_PASSWORD (optional but recommended)"
    else
        print_success "Database environment variables configured"
    fi
else
    print_warning ".env file not found. Creating template..."
    cat > .env << EOF
# HK Strategy Dashboard Configuration
# Copy this file and update with your settings

# Database Configuration (Required)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=hk_strategy
DB_USER=trader
DB_PASSWORD=your_secure_password

# Redis Configuration (Optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_ENABLED=false

# Application Configuration
DEBUG=true
ENVIRONMENT=development
LOG_LEVEL=INFO

# Cache Configuration
CACHE_ENABLED=true
CACHE_PRICE_TTL=1800
EOF
    print_warning "Please edit .env file with your database credentials before running again."
    exit 1
fi

print_status "🗄️ Testing database connection..."
# Check PostgreSQL connection
if command_exists psql; then
    print_success "PostgreSQL client found"
else
    print_warning "PostgreSQL client (psql) not found"
fi

# Test database connection if we have test script
if [ -f "test_db.py" ]; then
    python3 test_db.py
    if [ $? -eq 0 ]; then
        print_success "Database connection successful"
    else
        print_error "Database connection failed"
        echo ""
        echo "💡 Troubleshooting tips:"
        echo "  1. Ensure PostgreSQL is running"
        echo "  2. Check database credentials in .env"
        echo "  3. Verify database 'hk_strategy' exists"
        echo "  4. Try running: ./setup_local_db.sh"
        echo ""
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    print_warning "Database test script not found, skipping connection test"
fi

print_status "🚀 Checking dashboard entry points..."

# Check if new modular dashboard exists
if [ -f "src/dashboard/main.py" ]; then
    print_success "Modular dashboard found (src/dashboard/main.py)"
    DASHBOARD_ENTRY="src/dashboard/main.py"
elif [ -f "new_dashboard.py" ]; then
    print_success "New dashboard found (new_dashboard.py)"
    DASHBOARD_ENTRY="new_dashboard.py"
else
    print_warning "Modular dashboard not found, using original dashboard.py"
    DASHBOARD_ENTRY="dashboard.py"
fi

# Check if pages and services are available
if [ -d "src/pages" ] && [ -d "src/services" ] && [ -d "src/navigation" ]; then
    print_success "✅ Phase 1-4 modules detected (Core + Services + Navigation + Pages)"
    MODULAR_READY=true
else
    print_warning "⚠️ Modular components not complete, some features may be limited"
    MODULAR_READY=false
fi

# Check if Phase 5 components are available
if [ -d "src/components" ]; then
    print_success "✅ Phase 5 components detected (UI Components)"
    COMPONENTS_READY=true
else
    print_info "📦 Phase 5 components not yet implemented"
    COMPONENTS_READY=false
fi

echo ""
print_status "🎯 Dashboard Status Summary:"
echo "  📄 Phase 1 (Core): ✅ Complete"
echo "  🔧 Phase 2 (Services): ✅ Complete" 
echo "  🧭 Phase 3 (Navigation): ✅ Complete"
echo "  📄 Phase 4 (Pages): ✅ Complete"
if [ "$COMPONENTS_READY" = true ]; then
    echo "  🎨 Phase 5 (Components): ✅ Available"
else
    echo "  🎨 Phase 5 (Components): 🚧 In Development"
fi
echo ""

print_status "🌐 Starting Streamlit dashboard..."
echo "Dashboard will be available at: http://localhost:8501"
echo ""
echo "💡 Features available in modular dashboard:"
echo "  • 🏗️ Modular architecture with clean separation"
echo "  • 📊 Portfolio management and analysis"
echo "  • 🎯 Strategy analysis and technical indicators"
echo "  • ⚙️ System status and health monitoring"
echo "  • 🧭 Advanced navigation with breadcrumbs"
if [ "$COMPONENTS_READY" = true ]; then
    echo "  • 🎨 Reusable UI components and dialogs"
fi
echo ""

# Set environment for development
export DEBUG=true
export ENVIRONMENT=development

# Start the appropriate dashboard
print_status "🚀 Launching dashboard: $DASHBOARD_ENTRY"
streamlit run "$DASHBOARD_ENTRY" --server.port=8501 --server.address=localhost

# If Streamlit fails, provide troubleshooting info
if [ $? -ne 0 ]; then
    print_error "Dashboard failed to start"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "  1. Check that all dependencies are installed"
    echo "  2. Verify database connection"
    echo "  3. Check .env configuration"
    echo "  4. Try running original dashboard: ./start_legacy_dashboard.sh"
    echo ""
    exit 1
fi