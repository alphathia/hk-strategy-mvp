#!/bin/bash

echo "🏦 HK Strategy Dashboard Launcher"
echo "================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_title() {
    echo -e "${CYAN}$1${NC}"
}

print_option() {
    echo -e "${GREEN}$1${NC} $2"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check what's available
MODULAR_AVAILABLE=false
LEGACY_AVAILABLE=false

if [ -f "src/dashboard/main.py" ] || [ -f "new_dashboard.py" ]; then
    MODULAR_AVAILABLE=true
fi

if [ -f "dashboard.py" ]; then
    LEGACY_AVAILABLE=true
fi

print_title "📊 Available Dashboard Versions:"
echo ""

if [ "$MODULAR_AVAILABLE" = true ]; then
    print_option "1." "🚀 Modular Dashboard (NEW - Phases 1-4 Complete)"
    print_info "   ✅ Clean modular architecture"
    print_info "   ✅ Separated concerns (Core/Services/Navigation/Pages)"
    print_info "   ✅ Enhanced error handling and logging"
    print_info "   ✅ Modern development patterns"
    print_info "   📍 Runs on port 8501"
    echo ""
else
    print_warning "Modular dashboard not available (missing src/dashboard/main.py)"
    echo ""
fi

if [ "$LEGACY_AVAILABLE" = true ]; then
    print_option "2." "📜 Legacy Dashboard (ORIGINAL - Monolithic)"
    print_info "   ✅ All features available (6000 lines)"
    print_info "   ✅ Production tested and stable"
    print_info "   ⚠️  Monolithic architecture (harder to maintain)"
    print_info "   📍 Runs on port 8502"
    echo ""
else
    print_warning "Legacy dashboard not available (missing dashboard.py)"
    echo ""
fi

print_option "3." "🔧 Development Mode (Debug enabled)"
print_info "   🐛 Enhanced debugging output"
print_info "   📊 Session state inspection"
print_info "   ⚡ Auto-reload on code changes"
echo ""

print_option "4." "ℹ️  Show Project Status"
print_info "   📈 View decomposition progress"
print_info "   📋 See completed phases"
echo ""

print_option "0." "❌ Exit"
echo ""

# Get user choice
while true; do
    read -p "🎯 Select dashboard version (1-4, or 0 to exit): " choice
    
    case $choice in
        1)
            if [ "$MODULAR_AVAILABLE" = true ]; then
                echo ""
                echo "🚀 Starting Modular Dashboard..."
                exec ./start_modular_dashboard.sh
            else
                echo "❌ Modular dashboard not available"
                continue
            fi
            ;;
        2)
            if [ "$LEGACY_AVAILABLE" = true ]; then
                echo ""
                echo "📜 Starting Legacy Dashboard..."
                exec ./start_legacy_dashboard.sh
            else
                echo "❌ Legacy dashboard not available"
                continue
            fi
            ;;
        3)
            echo ""
            echo "🔧 Starting in Development Mode..."
            echo "Choose which version for development:"
            echo "  a) Modular (recommended)"
            echo "  b) Legacy"
            read -p "Choice (a/b): " dev_choice
            
            export DEBUG=true
            export LOG_LEVEL=DEBUG
            export ENVIRONMENT=development
            
            case $dev_choice in
                a|A)
                    if [ "$MODULAR_AVAILABLE" = true ]; then
                        exec ./start_modular_dashboard.sh
                    else
                        echo "❌ Modular dashboard not available"
                    fi
                    ;;
                b|B)
                    if [ "$LEGACY_AVAILABLE" = true ]; then
                        exec ./start_legacy_dashboard.sh
                    else
                        echo "❌ Legacy dashboard not available"
                    fi
                    ;;
                *)
                    echo "Invalid choice"
                    continue
                    ;;
            esac
            ;;
        4)
            echo ""
            print_title "📊 HK Strategy Dashboard - Project Status"
            echo "========================================="
            echo ""
            
            # Check phase completion
            if [ -d "src/dashboard" ]; then
                echo "✅ Phase 1: Core Modules (Complete)"
            else
                echo "❌ Phase 1: Core Modules (Missing)"
            fi
            
            if [ -d "src/services" ]; then
                echo "✅ Phase 2: Services Layer (Complete)"
            else
                echo "❌ Phase 2: Services Layer (Missing)"
            fi
            
            if [ -d "src/navigation" ]; then
                echo "✅ Phase 3: Navigation System (Complete)"
            else
                echo "❌ Phase 3: Navigation System (Missing)"
            fi
            
            if [ -d "src/pages" ]; then
                echo "✅ Phase 4: Page Modules (Complete)"
                PAGE_COUNT=$(find src/pages -name "*.py" -type f | wc -l)
                echo "   📄 $PAGE_COUNT page module files created"
            else
                echo "❌ Phase 4: Page Modules (Missing)"
            fi
            
            if [ -d "src/components" ]; then
                echo "✅ Phase 5: UI Components (In Progress)"
                COMPONENT_COUNT=$(find src/components -name "*.py" -type f | wc -l)
                echo "   🎨 $COMPONENT_COUNT component files created"
            else
                echo "🚧 Phase 5: UI Components (Not Started)"
            fi
            
            echo ""
            
            # Calculate progress
            COMPLETED_PHASES=0
            [ -d "src/dashboard" ] && COMPLETED_PHASES=$((COMPLETED_PHASES + 1))
            [ -d "src/services" ] && COMPLETED_PHASES=$((COMPLETED_PHASES + 1))
            [ -d "src/navigation" ] && COMPLETED_PHASES=$((COMPLETED_PHASES + 1))
            [ -d "src/pages" ] && COMPLETED_PHASES=$((COMPLETED_PHASES + 1))
            [ -d "src/components" ] && COMPLETED_PHASES=$((COMPLETED_PHASES + 1))
            
            PROGRESS=$((COMPLETED_PHASES * 20))
            echo "📈 Overall Progress: ${PROGRESS}% ($COMPLETED_PHASES/5 phases)"
            
            if [ -f "dashboard.py" ]; then
                ORIGINAL_LINES=$(wc -l < dashboard.py)
                echo "📜 Original dashboard.py: $ORIGINAL_LINES lines"
            fi
            
            if [ -d "src" ]; then
                MODULAR_LINES=$(find src -name "*.py" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}' || echo "0")
                echo "🏗️  Modular architecture: $MODULAR_LINES lines"
            fi
            
            echo ""
            echo "Press Enter to continue..."
            read
            echo ""
            ;;
        0)
            echo ""
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid option. Please choose 1-4 or 0."
            continue
            ;;
    esac
done