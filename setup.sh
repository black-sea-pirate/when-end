#!/bin/bash

# when-end Setup Script for Linux/Mac
# Run: chmod +x setup.sh && ./setup.sh

echo "=================================="
echo "  when-end Application Setup   "
echo "=================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check Docker
echo -e "${YELLOW}Checking Docker...${NC}"
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo -e "${GREEN}✓ Docker found: $DOCKER_VERSION${NC}"
else
    echo -e "${RED}✗ Docker not found! Please install Docker.${NC}"
    echo -e "${RED}  Download from: https://www.docker.com/products/docker-desktop${NC}"
    exit 1
fi

# Check Docker Compose
echo -e "${YELLOW}Checking Docker Compose...${NC}"
if docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version)
    echo -e "${GREEN}✓ Docker Compose found: $COMPOSE_VERSION${NC}"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    echo -e "${GREEN}✓ Docker Compose found: $COMPOSE_VERSION${NC}"
else
    echo -e "${RED}✗ Docker Compose not available!${NC}"
    exit 1
fi

echo ""
echo "=================================="
echo "  Environment Setup               "
echo "=================================="

# Check if .env exists
if [ -f ".env" ]; then
    echo -e "${GREEN}✓ .env file already exists${NC}"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp ops/.env.example .env
        echo -e "${GREEN}✓ Created new .env file from template${NC}"
    else
        echo -e "${YELLOW}Keeping existing .env file${NC}"
    fi
else
    cp ops/.env.example .env
    echo -e "${GREEN}✓ Created .env file from template${NC}"
fi

echo ""
echo "=================================="
echo "  Configuration Required          "
echo "=================================="
echo ""
echo -e "${YELLOW}You need to configure the following in .env file:${NC}"
echo ""
echo -e "${CYAN}1. Google OAuth Credentials${NC}"
echo "   - Go to: https://console.cloud.google.com/"
echo "   - Create OAuth 2.0 credentials"
echo "   - Add redirect URI: http://localhost:3000/api/auth/google/callback"
echo "   - Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env"
echo ""
echo -e "${CYAN}2. JWT Secret Keys${NC}"
echo "   Generate with: "
echo -e "${NC}   openssl rand -hex 32${NC}"
echo "   Set JWT_SECRET_KEY and JWT_REFRESH_SECRET_KEY in .env"
echo ""

read -p "Open .env file now? (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    if command -v nano &> /dev/null; then
        nano .env
    elif command -v vi &> /dev/null; then
        vi .env
    else
        echo -e "${YELLOW}Please edit .env file manually${NC}"
    fi
fi

echo ""
echo "=================================="
echo "  Ready to Start!                 "
echo "=================================="
echo ""
echo -e "${GREEN}After configuring .env, run:${NC}"
echo -e "${CYAN}  docker compose up -d${NC}"
echo ""
echo -e "${GREEN}Then access the application at:${NC}"
echo -e "${CYAN}  http://localhost:3000${NC}"
echo ""
echo -e "${YELLOW}For more help, see:${NC}"
echo "  - README.md"
echo "  - QUICKSTART.md"
echo "  - ARCHITECTURE.md"
echo ""
