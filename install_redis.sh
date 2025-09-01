#!/bin/bash

echo "🔧 Redis Installation and Setup"
echo "==============================="

# Check if running as root or with sudo access
if [ "$EUID" -eq 0 ]; then
    echo "✅ Running with root privileges"
elif sudo -n true 2>/dev/null; then 
    echo "✅ Sudo access available"
else
    echo "❌ This script requires sudo access to install Redis"
    echo "Please run: sudo ./install_redis.sh"
    exit 1
fi

echo ""
echo "🔍 Step 1: Checking current Redis status..."

# Check if Redis is already installed
if command -v redis-server &> /dev/null; then
    echo "✅ Redis server is already installed"
    redis-server --version
else
    echo "❌ Redis server not found - will install"
fi

if command -v redis-cli &> /dev/null; then
    echo "✅ Redis CLI is available"
else
    echo "❌ Redis CLI not found - will install"
fi

echo ""
echo "🔍 Step 2: Updating package repository..."
sudo apt update

echo ""
echo "📦 Step 3: Installing Redis server..."
sudo apt install -y redis-server

if [ $? -eq 0 ]; then
    echo "✅ Redis installation successful"
else
    echo "❌ Redis installation failed"
    exit 1
fi

echo ""
echo "🔍 Step 4: Checking Redis installation..."
redis-server --version
redis-cli --version

echo ""
echo "🔧 Step 5: Configuring Redis..."

# Backup original config
sudo cp /etc/redis/redis.conf /etc/redis/redis.conf.backup

# Set Redis to start as a service
sudo sed -i 's/^supervised no/supervised systemd/' /etc/redis/redis.conf

# Set working directory
sudo sed -i 's|^dir ./|dir /var/lib/redis|' /etc/redis/redis.conf

echo "✅ Redis configuration updated"

echo ""
echo "🚀 Step 6: Starting and enabling Redis service..."

# Start Redis service
sudo systemctl start redis-server
if [ $? -eq 0 ]; then
    echo "✅ Redis service started successfully"
else
    echo "❌ Failed to start Redis service"
fi

# Enable Redis to start on boot
sudo systemctl enable redis-server
if [ $? -eq 0 ]; then
    echo "✅ Redis service enabled for startup"
else
    echo "❌ Failed to enable Redis service"
fi

echo ""
echo "🔍 Step 7: Testing Redis connectivity..."

# Test Redis connection
redis-cli ping
if [ $? -eq 0 ]; then
    echo "✅ Redis is responding to ping"
else
    echo "❌ Redis is not responding"
fi

# Test basic operations
echo "🧪 Testing Redis operations..."
redis-cli set test_key "Hello Redis"
TEST_VALUE=$(redis-cli get test_key)

if [ "$TEST_VALUE" = "Hello Redis" ]; then
    echo "✅ Redis read/write test successful"
    redis-cli del test_key
else
    echo "❌ Redis read/write test failed"
fi

echo ""
echo "📊 Step 8: Redis status and info..."

# Show Redis service status
echo "Redis service status:"
sudo systemctl status redis-server --no-pager -l

echo ""
echo "Redis server info:"
redis-cli info server

echo ""
echo "Redis memory info:"
redis-cli info memory

echo ""
echo "🎯 Redis Setup Complete!"
echo "======================="
echo "✅ Redis server installed and running"
echo "✅ Service enabled for automatic startup"
echo "✅ Configuration optimized for systemd"
echo ""
echo "Connection details:"
echo "- Host: localhost"
echo "- Port: 6379"
echo "- Service: redis-server"
echo ""
echo "Useful Redis commands:"
echo "- Start: sudo systemctl start redis-server"
echo "- Stop: sudo systemctl stop redis-server"
echo "- Restart: sudo systemctl restart redis-server"
echo "- Status: sudo systemctl status redis-server"
echo "- Test connection: redis-cli ping"
echo ""
echo "🔄 Now refresh the system status in your Streamlit dashboard!"