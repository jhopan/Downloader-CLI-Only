#!/bin/bash
# Script untuk menambahkan alias perintah cepat ke .bashrc
# untuk mengelola systemd service downloader-cli-only

BASHRC="$HOME/.bashrc"
SERVICE_NAME="downloader-cli-only"

echo "🔧 Setup Bash Aliases untuk $SERVICE_NAME"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Cek apakah .bashrc ada
if [ ! -f "$BASHRC" ]; then
    echo "❌ File $BASHRC tidak ditemukan!"
    exit 1
fi

# Tanya nama alias yang diinginkan
echo "📝 Masukkan nama alias yang diinginkan (default: downloader)"
echo "   Contoh: downloader, bot, dl, etc."
read -p "Nama alias [downloader]: " ALIAS_NAME
ALIAS_NAME=${ALIAS_NAME:-downloader}

# Validasi nama alias (hanya huruf, angka, dan underscore)
if [[ ! "$ALIAS_NAME" =~ ^[a-zA-Z0-9_]+$ ]]; then
    echo "❌ Nama alias tidak valid! Hanya boleh huruf, angka, dan underscore."
    exit 1
fi

echo ""
echo "✅ Nama alias: $ALIAS_NAME"
echo ""

# Cek apakah alias sudah ada di sistem
declare -a EXISTING_ALIASES=()
declare -a CONFLICTING_CMDS=()

CMDS=("start" "stop" "restart" "status" "logs" "logs100" "logs500" "enable" "disable" "reload")
for cmd in "${CMDS[@]}"; do
    full_alias="${cmd}${ALIAS_NAME}"
    
    # Cek di .bashrc
    if grep -q "alias $full_alias=" "$BASHRC" 2>/dev/null; then
        EXISTING_ALIASES+=("$full_alias")
    fi
    
    # Cek command yang sudah ada di sistem
    if command -v "$full_alias" &> /dev/null; then
        CONFLICTING_CMDS+=("$full_alias")
    fi
done

# Tampilkan warning jika ada konflik
if [ ${#EXISTING_ALIASES[@]} -gt 0 ] || [ ${#CONFLICTING_CMDS[@]} -gt 0 ]; then
    echo "⚠️  Ditemukan konflik:"
    echo ""
    
    if [ ${#EXISTING_ALIASES[@]} -gt 0 ]; then
        echo "   Alias sudah ada di .bashrc:"
        for alias in "${EXISTING_ALIASES[@]}"; do
            echo "   - $alias"
        done
        echo ""
    fi
    
    if [ ${#CONFLICTING_CMDS[@]} -gt 0 ]; then
        echo "   Command sudah ada di sistem:"
        for cmd in "${CONFLICTING_CMDS[@]}"; do
            echo "   - $cmd"
        done
        echo ""
    fi
    
    read -p "Lanjutkan dan timpa? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Dibatalkan. Silakan gunakan nama alias yang berbeda."
        exit 0
    fi
fi

# Hapus alias lama jika ada
if grep -q "# Downloader CLI Only Aliases - $ALIAS_NAME" "$BASHRC"; then
    echo "🗑️  Menghapus alias lama..."
    sed -i "/# Downloader CLI Only Aliases - $ALIAS_NAME/,/# End Downloader CLI Only Aliases - $ALIAS_NAME/d" "$BASHRC"
fi

# Tambahkan alias baru
echo "➕ Menambahkan alias baru ke $BASHRC..."
cat >> "$BASHRC" << EOF

# Downloader CLI Only Aliases - $ALIAS_NAME
alias start${ALIAS_NAME}='sudo systemctl start $SERVICE_NAME'
alias stop${ALIAS_NAME}='sudo systemctl stop $SERVICE_NAME'
alias restart${ALIAS_NAME}='sudo systemctl restart $SERVICE_NAME'
alias status${ALIAS_NAME}='sudo systemctl status $SERVICE_NAME'
alias logs${ALIAS_NAME}='sudo journalctl -u $SERVICE_NAME -f'
alias logs100${ALIAS_NAME}='sudo journalctl -u $SERVICE_NAME -n 100'
alias logs500${ALIAS_NAME}='sudo journalctl -u $SERVICE_NAME -n 500'
alias enable${ALIAS_NAME}='sudo systemctl enable $SERVICE_NAME'
alias disable${ALIAS_NAME}='sudo systemctl disable $SERVICE_NAME'
alias reload${ALIAS_NAME}='sudo systemctl daemon-reload'
# End Downloader CLI Only Aliases - $ALIAS_NAME
EOF

echo ""
echo "✅ Alias berhasil ditambahkan!"
echo ""
echo "📋 Daftar Perintah Tersedia:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  start${ALIAS_NAME}       - Start service"
echo "  stop${ALIAS_NAME}        - Stop service"
echo "  restart${ALIAS_NAME}     - Restart service"
echo "  status${ALIAS_NAME}      - Cek status service"
echo "  logs${ALIAS_NAME}        - Lihat log realtime (follow)"
echo "  logs100${ALIAS_NAME}     - Lihat 100 log terakhir"
echo "  logs500${ALIAS_NAME}     - Lihat 500 log terakhir"
echo "  enable${ALIAS_NAME}      - Enable autostart saat boot"
echo "  disable${ALIAS_NAME}     - Disable autostart"
echo "  reload${ALIAS_NAME}      - Reload systemd daemon"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🔄 Untuk mengaktifkan alias sekarang, jalankan:"
echo "   source ~/.bashrc"
echo ""
echo "Atau tutup dan buka terminal baru."
echo ""

# Tanya apakah ingin source sekarang
read -p "Apakah Anda ingin mengaktifkan alias sekarang? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    source "$BASHRC"
    echo "✅ Alias sudah aktif! Coba jalankan: status${ALIAS_NAME}"
else
    echo "ℹ️  Jangan lupa jalankan: source ~/.bashrc"
fi
