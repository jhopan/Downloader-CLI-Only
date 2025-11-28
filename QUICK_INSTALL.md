# 🚀 Panduan Install Cepat

> Instalasi bot dalam 3 langkah mudah!

## Step 1: Clone & Install Python

```bash
# Clone repository
git clone https://github.com/jhopan/Downloader-CLI-Only.git
cd Downloader-CLI-Only

# Install Python (skip jika sudah ada)
sudo apt update && sudo apt install python3 python3-pip python3-venv -y
```

## Step 2: Setup & Jalankan Bot

```bash
# Berikan permission
chmod +x start.sh

# Jalankan (akan auto-setup)
./start.sh
```

**Pertama kali jalankan:**
- Script akan membuat file `.env`
- Edit file `.env`: `nano .env`
- Isi `BOT_TOKEN` (dari @BotFather) dan `ADMIN_IDS` (dari @userinfobot)
- Jalankan lagi: `./start.sh`

## Step 3: Test Bot

1. Buka Telegram
2. Cari bot Anda
3. Klik `/start`
4. Menu akan muncul ✅

## (Opsional) Install sebagai Service

Agar bot auto-start saat server reboot:

```bash
chmod +x install-service.sh
sudo ./install-service.sh
```

Bot akan:
- ✅ Start otomatis saat boot
- ✅ Auto-restart jika crash
- ✅ Jalan di background

## Perintah Berguna

```bash
# Lihat status (jika sudah install service)
sudo systemctl status telegram-downloader-bot

# Lihat log real-time
sudo journalctl -u telegram-downloader-bot -f

# Restart bot
sudo systemctl restart telegram-downloader-bot
```

## Troubleshooting

**Bot tidak jalan?**
- Cek `.env` sudah diisi BOT_TOKEN dan ADMIN_IDS
- Cek: `cat .env`

**Permission denied?**
- Jalankan: `chmod +x start.sh install-service.sh`

**Python tidak ada?**
- Install: `sudo apt install python3 python3-pip python3-venv -y`

---

📖 **Dokumentasi Lengkap:** Lihat [README.md](README.md)

🐛 **Issues?** [GitHub Issues](https://github.com/jhopan/Downloader-CLI-Only/issues)
