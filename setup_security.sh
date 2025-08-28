#!/bin/bash

# HK Strategy Portfolio Dashboard - Security Setup Script
# This script sets up secure configuration files from templates

set -e  # Exit on any error

echo "🔒 Setting up secure configuration files..."
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Create config directory if it doesn't exist
if [ ! -d "config" ]; then
    mkdir -p config
    echo -e "${GREEN}✅ Created config directory${NC}"
fi

# Create logs directory if it doesn't exist
if [ ! -d "logs" ]; then
    mkdir -p logs
    echo -e "${GREEN}✅ Created logs directory${NC}"
fi

# Create backups directory if it doesn't exist
if [ ! -d "backups" ]; then
    mkdir -p backups
    echo -e "${GREEN}✅ Created backups directory${NC}"
fi

echo ""
echo "🔧 Setting up configuration files..."
echo "-----------------------------------"

# Setup app_config.yaml from template
if [ ! -f "config/app_config.yaml" ]; then
    if [ -f "config/app_config.template.yaml" ]; then
        cp config/app_config.template.yaml config/app_config.yaml
        echo -e "${GREEN}✅ Created config/app_config.yaml from template${NC}"
        echo -e "${YELLOW}⚠️  IMPORTANT: You must edit config/app_config.yaml and set your passwords!${NC}"
    else
        echo -e "${RED}❌ Template file config/app_config.template.yaml not found${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  config/app_config.yaml already exists, skipping...${NC}"
fi

# Setup .env from template
if [ ! -f "config/.env" ]; then
    if [ -f "config/.env.template" ]; then
        cp config/.env.template config/.env
        echo -e "${GREEN}✅ Created config/.env from template${NC}"
        echo -e "${YELLOW}⚠️  IMPORTANT: You must edit config/.env and set your values!${NC}"
    else
        echo -e "${RED}❌ Template file config/.env.template not found${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  config/.env already exists, skipping...${NC}"
fi

echo ""
echo "🔐 Generating secure secrets..."
echo "------------------------------"

# Generate secrets if openssl is available
if command -v openssl &> /dev/null; then
    SECRET_KEY=$(openssl rand -hex 32)
    DATABASE_PASSWORD=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-16)
    
    echo "Generated secret key and database password"
    
    # Update the secret key in the config file
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/CHANGE_ME_TO_A_RANDOM_SECRET_KEY/$SECRET_KEY/g" config/app_config.yaml
        sed -i '' "s/generate_a_random_secret_key_here_with_openssl_rand_hex_32/$SECRET_KEY/g" config/.env
        sed -i '' "s/CHANGE_ME_TO_YOUR_SECURE_PASSWORD/$DATABASE_PASSWORD/g" config/app_config.yaml
        sed -i '' "s/YOUR_PASSWORD_HERE/$DATABASE_PASSWORD/g" config/.env
    else
        # Linux
        sed -i "s/CHANGE_ME_TO_A_RANDOM_SECRET_KEY/$SECRET_KEY/g" config/app_config.yaml
        sed -i "s/generate_a_random_secret_key_here_with_openssl_rand_hex_32/$SECRET_KEY/g" config/.env
        sed -i "s/CHANGE_ME_TO_YOUR_SECURE_PASSWORD/$DATABASE_PASSWORD/g" config/app_config.yaml
        sed -i "s/YOUR_PASSWORD_HERE/$DATABASE_PASSWORD/g" config/.env
    fi
    
    # Add DATABASE_PASSWORD to .env if not present
    if ! grep -q "DATABASE_PASSWORD" config/.env; then
        echo "DATABASE_PASSWORD=$DATABASE_PASSWORD" >> config/.env
    fi
    
    echo -e "${GREEN}✅ Secrets updated in configuration files${NC}"
else
    echo -e "${YELLOW}⚠️  openssl not found. Please manually generate secrets:${NC}"
    echo "   Secret Key: openssl rand -hex 32"
    echo "   DB Password: openssl rand -base64 24 | tr -d '=+/' | cut -c1-16"
    echo "   Then update config/app_config.yaml and config/.env"
fi

echo ""
echo "🛡️  Security checklist..."
echo "------------------------"

# Check .gitignore
if grep -q "config/app_config.yaml" .gitignore; then
    echo -e "${GREEN}✅ .gitignore properly configured for security${NC}"
else
    echo -e "${YELLOW}⚠️  Adding security entries to .gitignore${NC}"
    cat >> .gitignore << EOF

# Security - Configuration files with sensitive data (NEVER commit these)
config/app_config.yaml
config/.env
*.yaml.backup
*.env.backup

# Application logs
logs/
*.log

# Backup files
backups/
EOF
    echo -e "${GREEN}✅ Updated .gitignore with security entries${NC}"
fi

echo ""
echo "📝 Next steps:"
echo "-------------"
echo "1. Edit config/app_config.yaml and set your database password"
echo "2. Edit config/.env if you want to override any settings"
echo "3. NEVER commit these files to git (they're in .gitignore)"
echo "4. Run the database setup: sudo ./fix_database.sh"
echo "5. Install Redis: sudo ./install_redis.sh"
echo "6. Start the application: streamlit run dashboard_editable.py"

echo ""
echo -e "${GREEN}🎉 Security setup complete!${NC}"
echo ""
echo -e "${RED}SECURITY REMINDER:${NC}"
echo -e "${RED}=================${NC}"
echo -e "${RED}• NEVER commit config/app_config.yaml or config/.env to git${NC}"
echo -e "${RED}• Use strong, unique passwords${NC}"
echo -e "${RED}• Keep these files secure and backed up separately${NC}"
echo ""