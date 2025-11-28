#!/bin/bash

# ============================================================
# Script untuk menjalankan Bot Telegram Pengunduh Otomatis
# ============================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}🤖 Bot Telegram Pengunduh Otomatis${NC}"
echo -e "${BLUE}============================================================${NC}"

# 1. Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ File .env tidak ditemukan!${NC}"
    echo -e "${YELLOW}📝 Membuat file .env dari template...${NC}"
    
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ File .env berhasil dibuat dari .env.example${NC}"
        echo -e "${YELLOW}⚠️  PENTING: Edit file .env dan isi BOT_TOKEN dan ADMIN_IDS${NC}"
        echo -e "${YELLOW}    Jalankan: nano .env${NC}"
        echo ""
        read -p "Tekan Enter setelah mengisi .env atau Ctrl+C untuk keluar..."
    else
        echo -e "${RED}❌ File .env.example tidak ditemukan!${NC}"
        exit 1
    fi
fi

# 2. Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 tidak ditemukan!${NC}"
    echo -e "${YELLOW}📦 Install Python3 dengan: sudo apt install python3 python3-pip python3-venv -y${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python3 terdeteksi: $(python3 --version)${NC}"

# 3. Check if venv exists, if not create it
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Virtual environment tidak ditemukan, membuat...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment berhasil dibuat${NC}"
else
    echo -e "${GREEN}✅ Virtual environment sudah ada${NC}"
fi

# 4. Activate virtual environment
echo -e "${BLUE}🔄 Mengaktifkan virtual environment...${NC}"
source venv/bin/activate

# 5. Check if dependencies are installed
if [ ! -f "venv/.dependencies_installed" ]; then
    echo -e "${YELLOW}📦 Installing dependencies...${NC}"
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Mark dependencies as installed
    touch venv/.dependencies_installed
    echo -e "${GREEN}✅ Dependencies berhasil diinstall${NC}"
else
    echo -e "${GREEN}✅ Dependencies sudah terinstall${NC}"
fi

# 6. Check if config is valid
echo -e "${BLUE}🔍 Memeriksa konfigurasi...${NC}"

if ! grep -q "BOT_TOKEN=.*[a-zA-Z0-9]" .env; then
    echo -e "${RED}❌ BOT_TOKEN belum diisi di file .env!${NC}"
    echo -e "${YELLOW}📝 Edit file .env dan isi BOT_TOKEN dari @BotFather${NC}"
    echo -e "${YELLOW}    Jalankan: nano .env${NC}"
    exit 1
fi

if ! grep -q "ADMIN_IDS=.*[0-9]" .env; then
    echo -e "${RED}❌ ADMIN_IDS belum diisi di file .env!${NC}"
    echo -e "${YELLOW}📝 Edit file .env dan isi ADMIN_IDS dari @userinfobot${NC}"
    echo -e "${YELLOW}    Jalankan: nano .env${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Konfigurasi valid${NC}"

# 7. Create directories if not exist
mkdir -p downloads
mkdir -p data

echo -e "${BLUE}============================================================${NC}"
echo -e "${GREEN}🚀 Menjalankan bot...${NC}"
echo -e "${BLUE}============================================================${NC}"
echo -e "${YELLOW}💡 Untuk stop bot: Tekan Ctrl+C${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# 8. Run the bot
python main.py
