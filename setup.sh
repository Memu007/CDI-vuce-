#!/bin/bash

# CDI - Setup Script
# Automates the setup of the development environment

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting CDI Setup...${NC}"

# 1. Check Python Version
echo -e "\n${YELLOW}1. Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed. Please install it first.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "   Found Python $PYTHON_VERSION"

# 2. Create Virtual Environment
echo -e "\n${YELLOW}2. Setting up Virtual Environment...${NC}"
if [ -d "venv" ]; then
    echo "   venv already exists. Skipping creation."
else
    python3 -m venv venv
    echo "   ✅ venv created."
fi

# 3. Install Dependencies
echo -e "\n${YELLOW}3. Installing Dependencies...${NC}"
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "   ✅ Dependencies installed."

# 4. Environment Configuration
echo -e "\n${YELLOW}4. Configuring Environment...${NC}"
if [ -f ".env" ]; then
    echo "   .env already exists. Skipping."
else
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "   ✅ Created .env from .env.example"
        echo -e "${YELLOW}   ⚠️  IMPORTANT: Please edit .env and add your GEMINI_API_KEY${NC}"
    else
        echo -e "${RED}   ❌ .env.example not found!${NC}"
    fi
fi

# 5. Database Setup (Migrations)
echo -e "\n${YELLOW}5. Setting up Database...${NC}"
# Add current directory to PYTHONPATH for the script
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Load .env variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

if [ -f "proyecto_maria/scripts/migrate_to_postgres.py" ]; then
    python3 proyecto_maria/scripts/migrate_to_postgres.py
    echo "   ✅ Database initialized (SQLite/Postgres)."
else
    echo "   ⚠️  Migration script not found. Skipping."
fi

echo -e "\n${GREEN}✅ SETUP COMPLETE!${NC}"
echo -e "\nTo start the server, run:"
echo -e "   ${YELLOW}./start_server.sh${NC}"
echo -e "\nOr manually:"
echo -e "   ${YELLOW}source venv/bin/activate${NC}"
echo -e "   ${YELLOW}./start_server.sh${NC}"
