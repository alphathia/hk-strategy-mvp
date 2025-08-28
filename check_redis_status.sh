#!/bin/bash

# Redis Status Check Script - For users who can't install with sudo

echo "🔄 Redis Status Check"
echo "===================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo "🔍 Checking Redis availability..."

# Check if Redis is installed
if command -v redis-server &> /dev/null; then
    echo -e "${GREEN}✅ Redis server binary found${NC}"
    REDIS_VERSION=$(redis-server --version | head -n1)
    echo "   Version: $REDIS_VERSION"
else
    echo -e "${RED}❌ Redis server binary not found${NC}"
    echo -e "${YELLOW}   Installation required: sudo apt install -y redis-server${NC}"
fi

if command -v redis-cli &> /dev/null; then
    echo -e "${GREEN}✅ Redis CLI found${NC}"
else
    echo -e "${RED}❌ Redis CLI not found${NC}"
fi

echo ""
echo "🔍 Checking Redis service status..."

# Check if Redis process is running
if pgrep -f redis-server > /dev/null; then
    echo -e "${GREEN}✅ Redis server process is running${NC}"
    
    # Test connection
    if redis-cli ping &>/dev/null; then
        echo -e "${GREEN}✅ Redis connection successful${NC}"
        
        # Get Redis info
        REDIS_INFO=$(redis-cli INFO server 2>/dev/null | grep "redis_version" | cut -d: -f2 | tr -d '\r')
        if [ ! -z "$REDIS_INFO" ]; then
            echo "   Redis Version: $REDIS_INFO"
        fi
        
        echo -e "${GREEN}✅ Redis is fully functional${NC}"
        
    else
        echo -e "${YELLOW}⚠️  Redis process running but connection failed${NC}"
        echo "   This might be due to authentication or configuration issues"
    fi
else
    echo -e "${RED}❌ Redis server process not running${NC}"
    
    # Check if systemd service exists
    if systemctl list-units --type=service | grep -q redis; then
        echo -e "${YELLOW}   Redis service found but not running${NC}"
        echo -e "${YELLOW}   Start with: sudo systemctl start redis-server${NC}"
    else
        echo -e "${YELLOW}   Redis service not configured${NC}"
        echo -e "${YELLOW}   Install with: sudo apt install -y redis-server${NC}"
    fi
fi

echo ""
echo "🔍 Alternative Redis options..."

# Check for Docker
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✅ Docker available - can run Redis in container${NC}"
    echo "   Run: docker run -d -p 6379:6379 redis:alpine"
else
    echo -e "${YELLOW}⚠️  Docker not available${NC}"
fi

# Check network connectivity for cloud Redis
if ping -c 1 google.com &>/dev/null; then
    echo -e "${GREEN}✅ Network connectivity available - can use cloud Redis${NC}"
    echo "   Consider: Redis Cloud, AWS ElastiCache, or DigitalOcean Redis"
else
    echo -e "${YELLOW}⚠️  Limited network connectivity${NC}"
fi

echo ""
echo "📋 Summary & Recommendations:"
echo "-----------------------------"

if pgrep -f redis-server > /dev/null && redis-cli ping &>/dev/null; then
    echo -e "${GREEN}🎉 Redis is working perfectly!${NC}"
    echo "Your HK Strategy Dashboard should work without Redis issues."
    
elif pgrep -f redis-server > /dev/null; then
    echo -e "${YELLOW}⚠️  Redis is running but connection issues exist${NC}"
    echo "Check Redis configuration and authentication settings."
    
elif command -v redis-server &> /dev/null; then
    echo -e "${YELLOW}⚠️  Redis is installed but not running${NC}"
    echo "Start Redis with: sudo systemctl start redis-server"
    
else
    echo -e "${RED}❌ Redis is not installed${NC}"
    echo ""
    echo "Choose one of these options:"
    echo ""
    echo "1. 🏠 Install locally (requires sudo):"
    echo "   sudo apt install -y redis-server"
    echo "   sudo systemctl start redis-server"
    echo ""
    echo "2. 🐳 Use Docker:"
    echo "   docker run -d --name redis -p 6379:6379 redis:alpine"
    echo ""
    echo "3. ☁️  Use cloud Redis service:"
    echo "   Update config/app_config.yaml with your cloud Redis URL"
    echo ""
    echo "4. 🚫 Disable Redis (degraded performance):"
    echo "   The dashboard will work without Redis but will be slower"
fi

echo ""