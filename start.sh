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
        echo -e "${GREEN}✅ File .env berhasil dibuat${NC}"
        echo ""
        echo -e "${BLUE}============================================================${NC}"
        echo -e "${BLUE}⚙️  SETUP KONFIGURASI BOT${NC}"
        echo -e "${BLUE}============================================================${NC}"
        echo ""
        
        # Input BOT_TOKEN
        echo -e "${YELLOW}📍 Langkah 1: Dapatkan Bot Token${NC}"
        echo -e "   1. Buka Telegram, cari ${GREEN}@BotFather${NC}"
        echo -e "   2. Kirim: ${GREEN}/newbot${NC}"
        echo -e "   3. Ikuti instruksi untuk buat bot"
        echo -e "   4. Copy token yang diberikan (contoh: 1234567890:ABCdefGHI...)"
        echo ""
        read -p "Masukkan BOT_TOKEN: " bot_token
        
        # Validasi token format (angka:string)
        if [[ ! "$bot_token" =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]]; then
            echo -e "${RED}❌ Format token tidak valid!${NC}"
            echo -e "${YELLOW}Token harus format: 1234567890:ABCdefGHI...${NC}"
            exit 1
        fi
        
        # Update BOT_TOKEN di .env
        sed -i "s|BOT_TOKEN=your_bot_token_here|BOT_TOKEN=$bot_token|g" .env
        echo -e "${GREEN}✅ BOT_TOKEN tersimpan${NC}"
        echo ""
        
        # Input ADMIN_IDS
        echo -e "${YELLOW}📍 Langkah 2: Dapatkan User ID Telegram${NC}"
        echo -e "   1. Buka Telegram, cari ${GREEN}@userinfobot${NC}"
        echo -e "   2. Bot akan kirim ID Anda (contoh: 123456789)"
        echo -e "   3. Untuk multiple admin, pisahkan dengan koma"
        echo -e "      Contoh: 123456789,987654321"
        echo ""
        read -p "Masukkan ADMIN_IDS: " admin_ids
        
        # Validasi admin IDs (angka atau angka,angka,angka)
        if [[ ! "$admin_ids" =~ ^[0-9]+(,[0-9]+)*$ ]]; then
            echo -e "${RED}❌ Format ADMIN_IDS tidak valid!${NC}"
            echo -e "${YELLOW}Harus angka atau angka,angka (contoh: 123456789 atau 123456789,987654321)${NC}"
            exit 1
        fi
        
        # Update ADMIN_IDS di .env
        sed -i "s|ADMIN_IDS=your_admin_id_here|ADMIN_IDS=$admin_ids|g" .env
        echo -e "${GREEN}✅ ADMIN_IDS tersimpan${NC}"
        echo ""
        
        echo -e "${BLUE}============================================================${NC}"
        echo -e "${GREEN}✅ Konfigurasi berhasil disimpan!${NC}"
        echo -e "${BLUE}============================================================${NC}"
        echo ""
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

# Check BOT_TOKEN
if ! grep -q "BOT_TOKEN=.*[a-zA-Z0-9]" .env || grep -q "BOT_TOKEN=your_bot_token_here" .env; then
    echo -e "${RED}❌ BOT_TOKEN belum diisi dengan benar!${NC}"
    echo ""
    
    # Input BOT_TOKEN
    echo -e "${YELLOW}📍 Masukkan Bot Token dari @BotFather${NC}"
    echo -e "   Format: 1234567890:ABCdefGHI..."
    echo ""
    read -p "BOT_TOKEN: " bot_token
    
    # Validasi token
    if [[ ! "$bot_token" =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]]; then
        echo -e "${RED}❌ Format token tidak valid!${NC}"
        exit 1
    fi
    
    # Update .env
    if grep -q "BOT_TOKEN=" .env; then
        sed -i "s|BOT_TOKEN=.*|BOT_TOKEN=$bot_token|g" .env
    else
        echo "BOT_TOKEN=$bot_token" >> .env
    fi
    echo -e "${GREEN}✅ BOT_TOKEN tersimpan${NC}"
    echo ""
fi

# Check ADMIN_IDS
if ! grep -q "ADMIN_IDS=.*[0-9]" .env || grep -q "ADMIN_IDS=your_admin_id_here" .env; then
    echo -e "${RED}❌ ADMIN_IDS belum diisi dengan benar!${NC}"
    echo ""
    
    # Input ADMIN_IDS
    echo -e "${YELLOW}📍 Masukkan User ID dari @userinfobot${NC}"
    echo -e "   Format: 123456789 atau 123456789,987654321"
    echo ""
    read -p "ADMIN_IDS: " admin_ids
    
    # Validasi admin IDs
    if [[ ! "$admin_ids" =~ ^[0-9]+(,[0-9]+)*$ ]]; then
        echo -e "${RED}❌ Format ADMIN_IDS tidak valid!${NC}"
        exit 1
    fi
    
    # Update .env
    if grep -q "ADMIN_IDS=" .env; then
        sed -i "s|ADMIN_IDS=.*|ADMIN_IDS=$admin_ids|g" .env
    else
        echo "ADMIN_IDS=$admin_ids" >> .env
    fi
    echo -e "${GREEN}✅ ADMIN_IDS tersimpan${NC}"
    echo ""
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
