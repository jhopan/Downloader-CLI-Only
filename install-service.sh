#!/bin/bash

# ============================================================
# Script untuk install Bot sebagai systemd service
# ============================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Script ini harus dijalankan sebagai root${NC}"
    echo -e "${YELLOW}💡 Jalankan dengan: sudo ./install-service.sh${NC}"
    exit 1
fi

# Get script directory (the actual project directory, not root's home)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Get the actual user who invoked sudo
ACTUAL_USER="${SUDO_USER:-$USER}"

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}🔧 Install Bot Telegram sebagai System Service${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# 1. Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ File .env tidak ditemukan!${NC}"
    echo -e "${YELLOW}📝 Jalankan ./start.sh terlebih dahulu untuk setup${NC}"
    exit 1
fi

# 2. Check if venv exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment tidak ditemukan!${NC}"
    echo -e "${YELLOW}📝 Jalankan ./start.sh terlebih dahulu untuk setup${NC}"
    exit 1
fi

# 3. Get service name
read -p "Nama service (default: telegram-downloader-bot): " SERVICE_NAME
SERVICE_NAME=${SERVICE_NAME:-telegram-downloader-bot}

# 4. Create systemd service file
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo -e "${BLUE}📝 Membuat service file: ${SERVICE_FILE}${NC}"

cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Telegram Downloader Bot
After=network.target

[Service]
Type=simple
User=$ACTUAL_USER
Group=$ACTUAL_USER
WorkingDirectory=$SCRIPT_DIR
Environment="PATH=$SCRIPT_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=$SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✅ Service file berhasil dibuat${NC}"

# 5. Set permissions
echo -e "${BLUE}🔒 Mengatur permissions...${NC}"
chown "$ACTUAL_USER:$ACTUAL_USER" "$SCRIPT_DIR" -R
chmod 755 "$SCRIPT_DIR/start.sh"
chmod 755 "$SCRIPT_DIR/install-service.sh" 2>/dev/null || true

# 6. Reload systemd
echo -e "${BLUE}🔄 Reload systemd daemon...${NC}"
systemctl daemon-reload

# 7. Enable service
echo -e "${BLUE}✨ Enable service...${NC}"
systemctl enable "$SERVICE_NAME"

# 8. Start service
echo -e "${BLUE}🚀 Starting service...${NC}"
systemctl start "$SERVICE_NAME"

# Wait a moment
sleep 2

# 9. Check status
echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${GREEN}✅ Instalasi Selesai!${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""
echo -e "${GREEN}📊 Status service:${NC}"
systemctl status "$SERVICE_NAME" --no-pager -l

echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${GREEN}🎉 Bot berhasil diinstall sebagai system service!${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""
echo -e "${YELLOW}📝 Perintah yang berguna:${NC}"
echo ""
echo -e "  ${GREEN}# Cek status bot${NC}"
echo -e "  sudo systemctl status $SERVICE_NAME"
echo ""
echo -e "  ${GREEN}# Stop bot${NC}"
echo -e "  sudo systemctl stop $SERVICE_NAME"
echo ""
echo -e "  ${GREEN}# Start bot${NC}"
echo -e "  sudo systemctl start $SERVICE_NAME"
echo ""
echo -e "  ${GREEN}# Restart bot${NC}"
echo -e "  sudo systemctl restart $SERVICE_NAME"
echo ""
echo -e "  ${GREEN}# Lihat log real-time${NC}"
echo -e "  sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo -e "  ${GREEN}# Lihat log 100 baris terakhir${NC}"
echo -e "  sudo journalctl -u $SERVICE_NAME -n 100"
echo ""
echo -e "  ${GREEN}# Disable service (tidak auto-start)${NC}"
echo -e "  sudo systemctl disable $SERVICE_NAME"
echo ""
echo -e "  ${GREEN}# Uninstall service${NC}"
echo -e "  sudo systemctl stop $SERVICE_NAME"
echo -e "  sudo systemctl disable $SERVICE_NAME"
echo -e "  sudo rm /etc/systemd/system/$SERVICE_NAME.service"
echo -e "  sudo systemctl daemon-reload"
echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${GREEN}✅ Bot akan otomatis start saat server reboot${NC}"
echo -e "${BLUE}============================================================${NC}"
