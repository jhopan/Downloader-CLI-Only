#!/bin/bash

# ============================================================
# Update Bot Script
# Update systemd service dan reload tanpa perlu reinstall
# ============================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "============================================================"
echo "🔄 Update Bot Telegram Pengunduh Otomatis"
echo "============================================================"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo -e "${RED}❌ JANGAN jalankan script ini sebagai root!${NC}"
    echo -e "${YELLOW}💡 Jalankan sebagai user biasa: ./scripts/update-bot.sh${NC}"
    exit 1
fi

# Get current directory
CURRENT_DIR=$(pwd)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

echo -e "${BLUE}📁 Project directory: $PROJECT_DIR${NC}"
echo ""

# Check if service exists
SERVICE_NAME=$(systemctl list-units --type=service --all | grep -i "download.*\.service" | awk '{print $1}' | head -n 1 | sed 's/\.service//')

if [ -z "$SERVICE_NAME" ]; then
    echo -e "${RED}❌ Service tidak ditemukan!${NC}"
    echo -e "${YELLOW}💡 Install service terlebih dahulu dengan: ./scripts/install-service.sh${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Service ditemukan: $SERVICE_NAME${NC}"
echo ""

# Ask for confirmation
echo -e "${YELLOW}⚠️  Update akan:${NC}"
echo "   1. Stop service yang sedang berjalan"
echo "   2. Pull perubahan terbaru dari git (optional)"
echo "   3. Update dependencies Python"
echo "   4. Reload systemd daemon"
echo "   5. Restart service"
echo ""
read -p "Lanjutkan update? (y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}❌ Update dibatalkan${NC}"
    exit 0
fi

echo ""
echo "============================================================"
echo "🔄 Memulai Update Process..."
echo "============================================================"
echo ""

# Step 1: Stop service
echo -e "${BLUE}1️⃣  Stopping service...${NC}"
sudo systemctl stop "$SERVICE_NAME"
echo -e "${GREEN}   ✅ Service stopped${NC}"
echo ""

# Step 2: Git pull (optional)
echo -e "${BLUE}2️⃣  Update kode dari Git?${NC}"
read -p "   Pull latest changes from Git? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd "$PROJECT_DIR"
    
    # Check if there are uncommitted changes
    if [[ -n $(git status -s) ]]; then
        echo -e "${YELLOW}   ⚠️  Ada perubahan lokal yang belum di-commit${NC}"
        echo -e "${YELLOW}   Files yang berubah:${NC}"
        git status -s
        echo ""
        read -p "   Stash changes dan pull? (y/n): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git stash
            git pull origin main
            echo ""
            read -p "   Apply stashed changes? (y/n): " -n 1 -r
            echo ""
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                git stash pop
            fi
        fi
    else
        git pull origin main
    fi
    echo -e "${GREEN}   ✅ Git pull selesai${NC}"
else
    echo -e "${YELLOW}   ⏭️  Skip git pull${NC}"
fi
echo ""

# Step 3: Update Python dependencies
echo -e "${BLUE}3️⃣  Update Python dependencies...${NC}"
cd "$PROJECT_DIR"

if [ -f "requirements.txt" ]; then
    # Check if venv exists
    if [ -d "venv" ]; then
        echo -e "${BLUE}   📦 Using virtual environment${NC}"
        source venv/bin/activate
    fi
    
    pip install --upgrade pip -q
    pip install -r requirements.txt --upgrade -q
    echo -e "${GREEN}   ✅ Dependencies updated${NC}"
else
    echo -e "${YELLOW}   ⚠️  requirements.txt tidak ditemukan${NC}"
fi
echo ""

# Step 4: Reload systemd daemon
echo -e "${BLUE}4️⃣  Reload systemd daemon...${NC}"
sudo systemctl daemon-reload
echo -e "${GREEN}   ✅ Systemd daemon reloaded${NC}"
echo ""

# Step 5: Restart service
echo -e "${BLUE}5️⃣  Restart service...${NC}"
sudo systemctl restart "$SERVICE_NAME"
sleep 2
echo -e "${GREEN}   ✅ Service restarted${NC}"
echo ""

# Check service status
echo "============================================================"
echo "📊 Service Status"
echo "============================================================"
echo ""
sudo systemctl status "$SERVICE_NAME" --no-pager -l
echo ""

# Check if service is running
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo -e "${GREEN}✅ Update berhasil! Service berjalan dengan baik.${NC}"
else
    echo -e "${RED}❌ Service gagal start setelah update!${NC}"
    echo -e "${YELLOW}💡 Check logs dengan: sudo journalctl -u $SERVICE_NAME -n 50${NC}"
    exit 1
fi

echo ""
echo "============================================================"
echo "🎉 Update Selesai!"
echo "============================================================"
echo ""
echo -e "${GREEN}✅ Service: $SERVICE_NAME${NC}"
echo -e "${GREEN}✅ Status: Running${NC}"
echo ""
echo -e "${BLUE}📋 Useful commands:${NC}"
echo "   • Check status : sudo systemctl status $SERVICE_NAME"
echo "   • View logs    : sudo journalctl -u $SERVICE_NAME -f"
echo "   • Restart      : sudo systemctl restart $SERVICE_NAME"
echo ""

# Show alias commands if available
if command -v "start${SERVICE_NAME//-/_}" &> /dev/null; then
    ALIAS_NAME="${SERVICE_NAME//-/_}"
    echo -e "${BLUE}📋 Atau gunakan aliases:${NC}"
    echo "   • Status : status$ALIAS_NAME"
    echo "   • Logs   : logs$ALIAS_NAME"
    echo "   • Restart: restart$ALIAS_NAME"
    echo ""
fi

echo -e "${YELLOW}💡 Tip: Bot mungkin perlu beberapa detik untuk fully start${NC}"
echo ""
