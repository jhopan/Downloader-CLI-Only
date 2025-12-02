#!/bin/bash

# ============================================================
# Uninstall Bot Script
# Hapus systemd service dan aliases dengan aman
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
echo "🗑️  Uninstall Bot Telegram Pengunduh Otomatis"
echo "============================================================"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo -e "${RED}❌ JANGAN jalankan script ini sebagai root!${NC}"
    echo -e "${YELLOW}💡 Jalankan sebagai user biasa: ./scripts/uninstall-bot.sh${NC}"
    exit 1
fi

# Detect installed service
echo -e "${BLUE}🔍 Mendeteksi systemd service...${NC}"
SERVICES=$(systemctl list-units --type=service --all | grep -i "download.*\.service" | awk '{print $1}' | sed 's/\.service//')

if [ -z "$SERVICES" ]; then
    echo -e "${YELLOW}⚠️  Tidak ada service yang terdeteksi${NC}"
    echo -e "${YELLOW}💡 Mungkin service sudah dihapus atau belum pernah diinstall${NC}"
    echo ""
    
    # Check for aliases anyway
    echo -e "${BLUE}🔍 Checking for aliases...${NC}"
    if grep -q "# Downloader CLI Only Aliases" ~/.bashrc 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Ditemukan aliases di ~/.bashrc${NC}"
        read -p "Hapus aliases? (y/n): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # Backup bashrc
            cp ~/.bashrc ~/.bashrc.backup.$(date +%Y%m%d_%H%M%S)
            # Remove aliases section
            sed -i '/# Downloader CLI Only Aliases/,/# End Downloader CLI Only Aliases/d' ~/.bashrc
            echo -e "${GREEN}✅ Aliases dihapus dari ~/.bashrc${NC}"
            echo -e "${BLUE}💡 Reload dengan: source ~/.bashrc${NC}"
        fi
    fi
    exit 0
fi

# Show detected services
echo -e "${GREEN}📋 Service yang terdeteksi:${NC}"
echo ""
IFS=$'\n' read -d '' -r -a SERVICE_ARRAY <<< "$SERVICES" || true
for i in "${!SERVICE_ARRAY[@]}"; do
    echo "   $((i+1))) ${SERVICE_ARRAY[$i]}"
done
echo ""

# Select service if multiple
if [ ${#SERVICE_ARRAY[@]} -gt 1 ]; then
    read -p "Pilih service yang akan dihapus (1-${#SERVICE_ARRAY[@]}): " SERVICE_CHOICE
    SERVICE_NAME="${SERVICE_ARRAY[$((SERVICE_CHOICE-1))]}"
else
    SERVICE_NAME="${SERVICE_ARRAY[0]}"
fi

echo ""
echo -e "${YELLOW}⚠️  Service yang akan dihapus: $SERVICE_NAME${NC}"
echo ""

# Warning and confirmation
echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${RED}                     ⚠️  PERINGATAN ⚠️${NC}"
echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}Uninstall akan:${NC}"
echo "   1. Stop service $SERVICE_NAME"
echo "   2. Disable autostart"
echo "   3. Hapus service file dari systemd"
echo "   4. Hapus aliases dari ~/.bashrc (optional)"
echo ""
echo -e "${RED}⚠️  File download dan database TIDAK akan dihapus${NC}"
echo -e "${BLUE}💡 Untuk hapus data, hapus manual folder downloads/ dan data/${NC}"
echo ""
echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

read -p "Apakah Anda YAKIN ingin uninstall? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo -e "${YELLOW}❌ Uninstall dibatalkan${NC}"
    exit 0
fi

echo ""
echo "============================================================"
echo "🗑️  Memulai Uninstall Process..."
echo "============================================================"
echo ""

# Step 1: Stop service
echo -e "${BLUE}1️⃣  Stopping service...${NC}"
if systemctl is-active --quiet "$SERVICE_NAME"; then
    sudo systemctl stop "$SERVICE_NAME"
    echo -e "${GREEN}   ✅ Service stopped${NC}"
else
    echo -e "${YELLOW}   ⏭️  Service sudah tidak berjalan${NC}"
fi
echo ""

# Step 2: Disable service
echo -e "${BLUE}2️⃣  Disabling service...${NC}"
if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
    sudo systemctl disable "$SERVICE_NAME"
    echo -e "${GREEN}   ✅ Service disabled${NC}"
else
    echo -e "${YELLOW}   ⏭️  Service sudah disabled${NC}"
fi
echo ""

# Step 3: Remove service file
echo -e "${BLUE}3️⃣  Removing service file...${NC}"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
if [ -f "$SERVICE_FILE" ]; then
    sudo rm "$SERVICE_FILE"
    echo -e "${GREEN}   ✅ Service file removed: $SERVICE_FILE${NC}"
else
    echo -e "${YELLOW}   ⏭️  Service file tidak ditemukan${NC}"
fi
echo ""

# Step 4: Reload systemd daemon
echo -e "${BLUE}4️⃣  Reload systemd daemon...${NC}"
sudo systemctl daemon-reload
sudo systemctl reset-failed 2>/dev/null || true
echo -e "${GREEN}   ✅ Systemd daemon reloaded${NC}"
echo ""

# Step 5: Remove aliases
echo -e "${BLUE}5️⃣  Remove aliases from ~/.bashrc?${NC}"
if grep -q "# Downloader CLI Only Aliases" ~/.bashrc 2>/dev/null; then
    echo -e "${YELLOW}   ⚠️  Ditemukan aliases di ~/.bashrc${NC}"
    echo ""
    
    # Show aliases that will be removed
    echo -e "${BLUE}   Aliases yang akan dihapus:${NC}"
    sed -n '/# Downloader CLI Only Aliases/,/# End Downloader CLI Only Aliases/p' ~/.bashrc | grep "alias" | head -5
    echo "   ..."
    echo ""
    
    read -p "   Hapus aliases? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Backup bashrc first
        BACKUP_FILE=~/.bashrc.backup.$(date +%Y%m%d_%H%M%S)
        cp ~/.bashrc "$BACKUP_FILE"
        echo -e "${GREEN}   ✅ Backup dibuat: $BACKUP_FILE${NC}"
        
        # Remove all Downloader CLI Only Aliases sections
        sed -i '/# Downloader CLI Only Aliases/,/# End Downloader CLI Only Aliases/d' ~/.bashrc
        
        echo -e "${GREEN}   ✅ Aliases dihapus dari ~/.bashrc${NC}"
        echo -e "${BLUE}   💡 Reload dengan: source ~/.bashrc${NC}"
    else
        echo -e "${YELLOW}   ⏭️  Skip remove aliases${NC}"
    fi
else
    echo -e "${YELLOW}   ⏭️  Tidak ada aliases yang ditemukan${NC}"
fi
echo ""

# Verify uninstall
echo "============================================================"
echo "✅ Uninstall Selesai!"
echo "============================================================"
echo ""

# Check if service still exists
if systemctl list-units --type=service --all | grep -q "$SERVICE_NAME"; then
    echo -e "${RED}⚠️  Service masih terdeteksi di systemd${NC}"
    echo -e "${YELLOW}💡 Coba reboot sistem atau jalankan: sudo systemctl daemon-reload${NC}"
else
    echo -e "${GREEN}✅ Service berhasil dihapus dari systemd${NC}"
fi

echo ""
echo -e "${BLUE}📊 Summary:${NC}"
echo "   • Service: $SERVICE_NAME - ${GREEN}REMOVED${NC}"
echo "   • Autostart: ${GREEN}DISABLED${NC}"
echo "   • Service file: ${GREEN}DELETED${NC}"

if grep -q "# Downloader CLI Only Aliases" ~/.bashrc 2>/dev/null; then
    echo "   • Aliases: ${YELLOW}STILL EXISTS${NC} (not removed)"
else
    echo "   • Aliases: ${GREEN}REMOVED${NC}"
fi

echo ""
echo -e "${BLUE}📁 Data yang TIDAK dihapus:${NC}"
echo "   • downloads/ - File hasil download"
echo "   • data/      - Database bot"
echo "   • .env       - Konfigurasi bot"
echo "   • Source code - Project folder"
echo ""
echo -e "${YELLOW}💡 Untuk hapus data sepenuhnya:${NC}"
echo "   rm -rf downloads/ data/ .env"
echo ""
echo -e "${YELLOW}💡 Untuk reinstall di kemudian hari:${NC}"
echo "   ./scripts/install-service.sh"
echo ""
