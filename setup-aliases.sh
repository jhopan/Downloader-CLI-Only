#!/bin/bash
# Script untuk menambahkan alias perintah cepat ke .bashrc
# untuk mengelola systemd service

# JANGAN JALANKAN DENGAN SUDO!
if [ "$EUID" -eq 0 ]; then
    echo "❌ JANGAN jalankan script ini dengan sudo!"
    echo "   Jalankan tanpa sudo: ./setup-aliases.sh"
    echo ""
    echo "   Alias akan ditambahkan ke user biasa, bukan root."
    exit 1
fi

BASHRC="$HOME/.bashrc"

echo "🔧 Setup Bash Aliases untuk Systemd Service"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Cek apakah .bashrc ada
if [ ! -f "$BASHRC" ]; then
    echo "❌ File $BASHRC tidak ditemukan!"
    exit 1
fi

# Deteksi service yang tersedia dengan pattern download*
echo "🔍 Mendeteksi systemd service..."
AVAILABLE_SERVICES=$(systemctl list-unit-files --type=service 2>/dev/null | grep -E "download.*\.service" | awk '{print $1}' | sed 's/\.service$//' | head -5)

if [ -z "$AVAILABLE_SERVICES" ]; then
    echo "⚠️  Tidak ada service download* yang terdeteksi."
    echo ""
    read -p "Masukkan nama service manual (contoh: downloader-cli-only): " SERVICE_NAME
else
    echo "📋 Service yang terdeteksi:"
    echo ""
    select svc in $AVAILABLE_SERVICES "Manual Input"; do
        if [ "$svc" = "Manual Input" ]; then
            read -p "Masukkan nama service: " SERVICE_NAME
            break
        elif [ -n "$svc" ]; then
            SERVICE_NAME="$svc"
            break
        fi
    done
fi

if [ -z "$SERVICE_NAME" ]; then
    echo "❌ Nama service tidak boleh kosong!"
    exit 1
fi

echo ""
echo "✅ Service yang dipilih: $SERVICE_NAME"
echo ""

# Tanya nama alias yang diinginkan
echo "📝 Masukkan nama alias yang diinginkan (default: downloader)"
echo "   Contoh: downloader, bot, dl, dcli, etc."
echo "   Nama alias akan menjadi prefix perintah (contoh: start<alias>)"
read -p "Nama alias [downloader]: " ALIAS_NAME
ALIAS_NAME=${ALIAS_NAME:-downloader}

# Validasi nama alias (huruf, angka, underscore, dash)
if [[ ! "$ALIAS_NAME" =~ ^[a-zA-Z0-9_-]+$ ]]; then
    echo "❌ Nama alias tidak valid! Hanya boleh huruf, angka, underscore, dan dash."
    exit 1
fi

# Remove dash dari alias name untuk command (dash tidak bisa di command name)
ALIAS_CMD=$(echo "$ALIAS_NAME" | tr '-' '_')

# Remove dash dari alias name untuk command (dash tidak bisa di command name)
ALIAS_CMD=$(echo "$ALIAS_NAME" | tr '-' '_')

echo ""
echo "✅ Nama alias: $ALIAS_NAME"
echo "✅ Command prefix: $ALIAS_CMD"
echo ""

# Cek apakah alias sudah ada di sistem
declare -a EXISTING_ALIASES=()
declare -a CONFLICTING_CMDS=()

CMDS=("start" "stop" "restart" "status" "logs" "logs100" "logs500" "enable" "disable" "reload")
for cmd in "${CMDS[@]}"; do
    full_alias="${cmd}${ALIAS_CMD}"
    
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

# Hapus alias lama jika ada (pakai ALIAS_CMD untuk marker)
if grep -q "# Systemd Service Aliases - $ALIAS_CMD" "$BASHRC"; then
    echo "🗑️  Menghapus alias lama..."
    sed -i "/# Systemd Service Aliases - $ALIAS_CMD/,/# End Systemd Service Aliases - $ALIAS_CMD/d" "$BASHRC"
fi

# Tambahkan alias baru
echo "➕ Menambahkan alias baru ke $BASHRC..."
cat >> "$BASHRC" << EOF

# Systemd Service Aliases - $ALIAS_CMD
# Service: $SERVICE_NAME
alias start${ALIAS_CMD}='sudo systemctl start $SERVICE_NAME'
alias stop${ALIAS_CMD}='sudo systemctl stop $SERVICE_NAME'
alias restart${ALIAS_CMD}='sudo systemctl restart $SERVICE_NAME'
alias status${ALIAS_CMD}='sudo systemctl status $SERVICE_NAME'
alias logs${ALIAS_CMD}='sudo journalctl -u $SERVICE_NAME -f'
alias logs100${ALIAS_CMD}='sudo journalctl -u $SERVICE_NAME -n 100'
alias logs500${ALIAS_CMD}='sudo journalctl -u $SERVICE_NAME -n 500'
alias enable${ALIAS_CMD}='sudo systemctl enable $SERVICE_NAME'
alias disable${ALIAS_CMD}='sudo systemctl disable $SERVICE_NAME'
alias reload${ALIAS_CMD}='sudo systemctl daemon-reload'
# End Systemd Service Aliases - $ALIAS_CMD
EOF

echo ""
echo "✅ Alias berhasil ditambahkan!"
echo ""
echo "📋 Daftar Perintah Tersedia:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  start${ALIAS_CMD}       - Start service"
echo "  stop${ALIAS_CMD}        - Stop service"
echo "  restart${ALIAS_CMD}     - Restart service"
echo "  status${ALIAS_CMD}      - Cek status service"
echo "  logs${ALIAS_CMD}        - Lihat log realtime (follow)"
echo "  logs100${ALIAS_CMD}     - Lihat 100 log terakhir"
echo "  logs500${ALIAS_CMD}     - Lihat 500 log terakhir"
echo "  enable${ALIAS_CMD}      - Enable autostart saat boot"
echo "  disable${ALIAS_CMD}     - Disable autostart"
echo "  reload${ALIAS_CMD}      - Reload systemd daemon"
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
    # Source bashrc
    source "$BASHRC"
    echo "✅ Alias sudah aktif! Coba jalankan: status${ALIAS_CMD}"
    echo ""
    echo "ℹ️  Catatan: Jika masih tidak berfungsi, tutup dan buka terminal baru."
else
    echo "ℹ️  Jangan lupa jalankan: source ~/.bashrc"
fi
