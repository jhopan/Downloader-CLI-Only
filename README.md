# 🤖 Bot Telegram Pengunduh Otomatis (CLI Only)

> Bot Telegram yang dapat mengunduh file dari link apapun dengan fitur lengkap seperti penjadwalan, multiple downloads, real-time progress, dan custom download path. Dirancang untuk berjalan di server Linux/Debian/Ubuntu tanpa GUI.

[![GitHub](https://img.shields.io/badge/GitHub-jhopan-blue?logo=github)](https://github.com/jhopan/Downloader-CLI-Only)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## ✨ Fitur Utama

### 📥 Download Manager (Seperti IDM!)

- **Real-time Progress Bar** - Lihat progress unduhan dengan bar dan persentase
- **Download Speed Monitor** - Monitor kecepatan download (MB/s)
- **File Size Tracking** - Lihat ukuran file yang sudah/akan diunduh
- **Multiple Concurrent Downloads** - Unduh beberapa file sekaligus (max 5)
- **Auto Completion Notification** - Notifikasi otomatis saat download selesai
- **Resume Support** - Download otomatis dilanjutkan jika terputus

### ⚡ Fitur Lainnya

- ⏰ **Unduh Berjadwal** - Jadwalkan unduhan untuk waktu tertentu
- ✅ **Validasi Link** - Validasi link sebelum mengunduh
- 📋 **Manajemen Jadwal** - Lihat dan kelola jadwal unduhan
- ❌ **Batalkan Unduhan** - Batalkan unduhan yang sedang berjalan
- 📍 **Custom Download Path** - Pilih lokasi download atau gunakan default
- 💾 **Database Storage** - Simpan preferences dan history di SQLite
- 📜 **Download History** - Lihat riwayat unduhan lengkap
- ⚙️ **Settings Menu** - Atur lokasi download dan preferensi
- 🔒 **Admin Only** - Hanya admin terdaftar yang dapat menggunakan
- 📋 **Persistent Menu Button** - Tombol menu selalu tersedia
- 🎯 **Inline Keyboard** - Semua interaksi menggunakan button
- 🔄 **Clean UI** - Pesan diupdate, tidak spam chat baru
- 🔄 **Network Resilience** - Auto-reconnect saat koneksi terputus

---

## 🚀 Quick Start (3 Langkah!)

```bash
# 1. Clone repository
git clone https://github.com/jhopan/Downloader-CLI-Only.git
cd Downloader-CLI-Only

# 2. Install Python (jika belum)
sudo apt update && sudo apt install python3 python3-pip python3-venv -y

# 3. Jalankan bot dengan script otomatis
chmod +x start.sh
./start.sh
```

**Pertama kali jalankan:**

- Script akan minta **BOT_TOKEN** (dari @BotFather)
- Script akan minta **ADMIN_IDS** (dari @userinfobot)
- Input, simpan, dan bot langsung jalan! ✅

**Install sebagai service (opsional):**

```bash
chmod +x install-service.sh
sudo ./install-service.sh
```

Bot akan:

- ✅ Auto-start saat server boot
- ✅ Auto-restart jika crash
- ✅ Jalan di background 24/7

---

## 📊 Preview Fitur Download

**Real-time Progress:**

```
📥 Sedang Mengunduh...

██████████░░░░░░░░░░ 50.0%

Downloaded: 50.00 MB / 100.00 MB
Speed: 2.50 MB/s
ID: 5c5b1217
```

**Completion Notification:**

```
✅ Download Selesai!

File: document.pdf
Ukuran: 100.00 MB
Lokasi: ./downloads
ID: 5c5b1217
```

---

## 📋 Prerequisites

- Python 3.8 atau lebih baru
- Akses root/sudo (untuk instalasi di server)
- Bot Token dari [@BotFather](https://t.me/BotFather)
- User ID Telegram (dapatkan dari [@userinfobot](https://t.me/userinfobot))

## 🚀 Instalasi Lengkap

### Step 1: Clone Repository

Buka terminal dan jalankan perintah berikut:

```bash
# Masuk ke direktori yang diinginkan
cd /opt

# Clone repository dari GitHub
git clone https://github.com/jhopan/Downloader-CLI-Only.git

# Masuk ke folder project
cd Downloader-CLI-Only
```

> **💡 Tips:** Anda bisa clone ke folder lain sesuai kebutuhan, misalnya `~/projects/` atau `/home/user/`

---

### Step 2: Install Python & Dependencies

**Untuk Debian/Ubuntu/Linux Mint:**

```bash
# Update package list
sudo apt update

# Install Python dan tools yang diperlukan
sudo apt install python3 python3-pip python3-venv -y

# Verifikasi instalasi
python3 --version  # Harus Python 3.8 atau lebih baru
pip3 --version
```

**Untuk CentOS/RHEL:**

```bash
sudo yum install python3 python3-pip python3-venv -y
```

**Untuk Arch Linux:**

```bash
sudo pacman -S python python-pip
```

> **✅ Pastikan:** Python versi 3.8 atau lebih baru terinstall

---

### Step 3: Jalankan Bot dengan Script Otomatis 🚀

**Cara Mudah (Recommended):**

Kami menyediakan script `start.sh` yang akan otomatis:

- ✅ Membuat virtual environment (jika belum ada)
- ✅ Install dependencies (jika belum)
- ✅ Validasi konfigurasi .env
- ✅ Menjalankan bot

```bash
# Berikan permission execute
chmod +x start.sh

# Jalankan bot
./start.sh
```

Script akan:

1. Cek apakah `.env` sudah ada, jika belum akan dibuat dari template
2. Cek apakah `venv` sudah ada, jika belum akan dibuat otomatis
3. Install dependencies jika belum terinstall
4. Validasi BOT_TOKEN dan ADMIN_IDS sudah diisi
5. Menjalankan bot

**Pertama kali menjalankan:**

- Script akan membuat file `.env` dan meminta Anda mengisinya
- Edit `.env`: `nano .env`
- Isi `BOT_TOKEN` dan `ADMIN_IDS`
- Jalankan lagi `./start.sh`

> **💡 Tips:** Anda hanya perlu menjalankan `./start.sh` setiap kali ingin start bot. Tidak perlu aktifkan venv manual!

---

<details>
<summary><b>📖 Cara Manual (Klik untuk expand)</b></summary>

Jika Anda ingin setup manual tanpa script:

**A. Buat Virtual Environment:**

```bash
# Buat virtual environment
python3 -m venv venv

# Aktifkan virtual environment
source venv/bin/activate

# Terminal akan berubah menjadi: (venv) user@server:~$
```

> **📝 Catatan:** Setiap kali membuka terminal baru, Anda harus mengaktifkan venv dengan `source venv/bin/activate`

**B. Install Dependencies:**

```bash
pip install -r requirements.txt
```

**C. Buat file .env:**

```bash
cp .env.example .env
nano .env
```

**D. Jalankan bot:**

```bash
python main.py
```

</details>

---

### Step 4: Install Dependencies Python

Setelah virtual environment aktif, install semua dependencies:

```bash
# Install semua package yang dibutuhkan
pip install -r requirements.txt

# Verifikasi instalasi
pip list  # Akan menampilkan semua package yang terinstall
```

Dependencies yang akan terinstall:

- `python-telegram-bot` - Library untuk bot Telegram
- `aiohttp` - HTTP client untuk download async
- `aiofiles` - File operations async
- `python-dotenv` - Untuk membaca file .env

---

### Step 5: Dapatkan Bot Token & User ID

**A. Dapatkan Bot Token dari BotFather:**

1. Buka Telegram dan cari [@BotFather](https://t.me/BotFather)
2. Kirim command `/newbot`
3. Ikuti instruksi:
   - Masukkan nama bot (contoh: `My Downloader Bot`)
   - Masukkan username bot (harus diakhiri `bot`, contoh: `my_downloader_bot`)
4. **SIMPAN TOKEN** yang diberikan, contoh: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

**B. Dapatkan User ID Telegram:**

1. Buka Telegram dan cari [@userinfobot](https://t.me/userinfobot)
2. Bot akan otomatis memberikan informasi Anda
3. **SIMPAN ID** yang ditampilkan, contoh: `123456789`

> **⚠️ PENTING:** Jangan share token bot kepada siapapun! Token ini seperti password.

---

### Step 6: Konfigurasi Bot

**A. Copy template konfigurasi:**

```bash
cp .env.example .env
```

**B. Edit file .env:**

```bash
nano .env
# Atau gunakan editor favorit: vim, vi, atau mcedit
```

**C. Isi konfigurasi dengan data Anda:**

```env
# ===== WAJIB DIISI =====
# Bot Token dari @BotFather (ganti dengan token Anda)
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Admin User IDs - Pisahkan dengan koma untuk multiple admin
# Contoh: ADMIN_IDS=123456789,987654321,555666777
ADMIN_IDS=123456789

# ===== OPSIONAL (Bisa dibiarkan default) =====
# Direktori download default
DEFAULT_DOWNLOAD_DIR=./downloads

# Maksimal download bersamaan
MAX_CONCURRENT_DOWNLOADS=5

# Ukuran chunk download (bytes)
CHUNK_SIZE=8192

# Path database SQLite
DATABASE_PATH=./data/bot.db
```

**D. Simpan file:**

- Jika pakai nano: Tekan `Ctrl+X`, lalu `Y`, lalu `Enter`
- Jika pakai vim: Tekan `ESC`, lalu ketik `:wq`, lalu `Enter`

**E. Verifikasi konfigurasi:**

```bash
# Lihat isi file untuk memastikan sudah benar
cat .env
```

> **🔒 KEAMANAN:** File `.env` berisi data sensitif. Jangan upload ke GitHub atau share ke orang lain!

---

### Step 7: Jalankan Bot

Pastikan virtual environment masih aktif (ada tulisan `(venv)` di terminal).

**A. Jalankan bot (Mode Testing):**

```bash
python main.py
```

Output yang muncul jika berhasil:

```
✅ Konfigurasi dimuat:
   - Admin IDs: [123456789]
   - Default Download Dir: ./downloads
   - Max Concurrent: 5
   - Database: ./data/bot.db
============================================================
🤖 Bot Telegram Pengunduh Otomatis
============================================================
✅ Bot berhasil dijalankan!
📁 Default download folder: ./downloads
💾 Database: ./data/bot.db
👥 Admin IDs: [123456789]
📊 Max concurrent downloads: 5
============================================================
Bot siap menerima perintah...
Tekan Ctrl+C untuk menghentikan bot
============================================================
```

**B. Test bot di Telegram:**

1. Buka Telegram
2. Cari bot Anda (username yang dibuat di BotFather)
3. Klik **Start** atau kirim `/start`
4. Bot akan menampilkan menu utama dengan tombol-tombol

> **✅ Jika muncul menu, instalasi berhasil!**

**C. Stop bot:**

- Tekan `Ctrl+C` di terminal

---

## 🔧 Install Bot sebagai System Service (Auto-Start)

Agar bot otomatis berjalan saat server reboot dan tidak stop saat terminal ditutup:

### Cara Mudah dengan Script:

```bash
# Berikan permission execute
chmod +x install-service.sh

# Install sebagai service (perlu sudo)
sudo ./install-service.sh
```

Script akan:

1. ✅ Membuat systemd service file
2. ✅ Enable service auto-start saat boot
3. ✅ Start service
4. ✅ Menampilkan status dan perintah berguna

**Setelah terinstall, bot akan:**

- 🚀 Otomatis start saat server boot/reboot
- 🔄 Auto-restart jika crash
- 📝 Log tersimpan di system journal

### Perintah Berguna:

```bash
# Cek status bot
sudo systemctl status telegram-downloader-bot

# Stop bot
sudo systemctl stop telegram-downloader-bot

# Start bot
sudo systemctl start telegram-downloader-bot

# Restart bot
sudo systemctl restart telegram-downloader-bot

# Lihat log real-time
sudo journalctl -u telegram-downloader-bot -f

# Lihat log 100 baris terakhir
sudo journalctl -u telegram-downloader-bot -n 100

# Disable auto-start
sudo systemctl disable telegram-downloader-bot

# Uninstall service
sudo systemctl stop telegram-downloader-bot
sudo systemctl disable telegram-downloader-bot
sudo rm /etc/systemd/system/telegram-downloader-bot.service
sudo systemctl daemon-reload
```

---

<details>
<summary><b>📖 Cara Manual Install Service (Klik untuk expand)</b></summary>

Jika Anda ingin install service manual tanpa script:

**C. Stop bot (untuk testing):**

- Tekan `Ctrl+C` di terminal

---

### Step 8: Jalankan Bot Permanent (Background)

Setelah yakin bot berjalan dengan baik, jalankan di background agar tidak stop saat terminal ditutup.

**Opsi 1: Menggunakan nohup (Simple)**

```bash
# Jalankan bot di background
nohup python main.py > bot.log 2>&1 &

# Cek apakah bot berjalan
ps aux | grep main.py

# Lihat log real-time
tail -f bot.log

# Stop bot (jika perlu)
pkill -f main.py
```

**Opsi 2: Menggunakan screen (Recommended)**

```bash
# Install screen jika belum ada
sudo apt install screen -y

# Buat session baru
screen -S telegram-bot

# Aktifkan venv di dalam screen
source venv/bin/activate

# Jalankan bot
python main.py

# Detach dari screen (bot tetap jalan)
# Tekan: Ctrl+A kemudian D

# Kembali ke session
screen -r telegram-bot

# List semua session
screen -ls
```

**Opsi 3: Menggunakan systemd (Production Ready)** - Lihat section berikutnya.

---

## 🔧 Menjalankan sebagai Service (Recommended)

Untuk menjalankan bot secara otomatis saat server restart:

### 1. Buat file service

```bash
sudo nano /etc/systemd/system/telegram-bot.service
```

### 2. Isi dengan konfigurasi berikut:

```ini
[Unit]
Description=Telegram Bot Downloader
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/bot-telegram-downloader
Environment="PATH=/opt/bot-telegram-downloader/venv/bin"
ExecStart=/opt/bot-telegram-downloader/venv/bin/python /opt/bot-telegram-downloader/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3. Aktifkan dan jalankan service

```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot.service
sudo systemctl start telegram-bot.service
```

### 4. Cek status service

```bash
sudo systemctl status telegram-bot.service
```

### 5. Perintah berguna lainnya

```bash
# Stop bot
sudo systemctl stop telegram-bot.service

# Restart bot
sudo systemctl restart telegram-bot.service

# Lihat log
sudo journalctl -u telegram-bot.service -f
```

## 📱 Cara Penggunaan

1. **Start Bot**: Kirim `/start` ke bot Telegram Anda
2. **Menu Utama**: Pilih menu yang diinginkan menggunakan button:
   - 📥 **Unduh Langsung** - Untuk unduh file sekarang
   - ⏰ **Unduh Berjadwal** - Untuk jadwalkan unduhan
   - 📊 **Status Unduhan** - Lihat progress unduhan
   - 📋 **Lihat Jadwal** - Lihat daftar jadwal
   - ⚙️ **Pengaturan** - Atur lokasi download & preferensi
   - ❌ **Batalkan Unduhan** - Batalkan unduhan aktif

### Contoh Unduh Langsung:

1. Klik "📥 Unduh Langsung"
2. Kirim link file yang ingin diunduh
3. Bot akan validasi link
4. Jika valid, unduhan dimulai otomatis
5. File tersimpan di lokasi yang dipilih (default atau custom)

### Contoh Unduh Berjadwal:

1. Klik "⏰ Unduh Berjadwal"
2. Kirim link file
3. Kirim waktu jadwal, format:
   - `28/11/2025 14:30` (tanggal dan jam spesifik)
   - `1h` (1 jam dari sekarang)
   - `30m` (30 menit dari sekarang)
   - `2d` (2 hari dari sekarang)
4. Unduhan akan dimulai otomatis sesuai jadwal

### Contoh Atur Lokasi Download:

1. Klik "⚙️ Pengaturan"
2. Klik "📝 Atur Lokasi Custom"
3. Kirim path folder, contoh: `/home/user/downloads`
4. Klik "📍 Lokasi Unduhan" untuk toggle antara custom/default
5. Semua unduhan akan tersimpan di lokasi yang dipilih

## 📁 Struktur File

```
bot-telegram-downloader/
├── main.py                      # File utama untuk menjalankan bot
├── config.py                    # Konfigurasi dan environment variables
├── requirements.txt             # Dependencies Python
├── .env                         # Konfigurasi (buat sendiri)
├── .env.example                # Contoh konfigurasi
├── README.md                   # Dokumentasi ini
│
├── app/                        # Application layer
│   ├── handlers/              # Request handlers
│   │   ├── start_handler.py   # Handler untuk /start
│   │   ├── button_handler.py  # Handler untuk button callbacks
│   │   ├── download_handler.py # Handler unduh langsung
│   │   ├── schedule_handler.py # Handler unduh berjadwal
│   │   ├── settings_handler.py # Handler pengaturan
│   │   ├── status_handler.py  # Handler status & cancel
│   │   ├── common.py          # Helper functions
│   │   └── states.py          # Conversation states
│   │
│   └── keyboards/             # Keyboard layouts
│       └── inline_keyboards.py # Inline keyboard definitions
│
├── src/                       # Source/Core layer
│   ├── managers/             # Business logic managers
│   │   ├── download_manager.py # Download management
│   │   └── scheduler_manager.py # Schedule management
│   │
│   └── database/             # Database layer
│       └── db_manager.py     # SQLite database operations
│
├── utils/                    # Utilities
│   └── validators.py        # URL validation
│
├── data/                    # Data storage (auto-created)
│   └── bot.db              # SQLite database
│
└── downloads/              # Default download folder (auto-created)
```

## 🔍 Troubleshooting

### Bot tidak merespons

- Cek apakah bot sudah running: `ps aux | grep main.py`
- Cek log: `tail -f bot.log` atau `sudo journalctl -u telegram-bot.service -f`
- Pastikan BOT_TOKEN benar di file `.env`

### "Anda tidak memiliki akses"

- Pastikan User ID Anda ada di ADMIN_IDS di file `.env`
- Restart bot setelah mengubah konfigurasi

### Download gagal

- Cek koneksi internet server
- Cek apakah link valid dan bisa diakses
- Cek permission folder downloads: `ls -la downloads/`
- Pastikan ada space yang cukup: `df -h`

### Custom path tidak bisa diset

- Pastikan folder exist dan bot punya write permission
- Coba: `sudo chmod 755 /path/to/folder`
- Cek log untuk detail error

### Bot berhenti sendiri

- Gunakan systemd service agar auto-restart
- Atau gunakan screen/tmux untuk session persistent

## 🛠️ Development

### Struktur Project

Project ini menggunakan arsitektur berlapis:

- **app/** - Application layer (handlers, keyboards)
- **src/** - Core business logic (managers, database)
- **utils/** - Helper utilities (validators, formatters)

### Menambah fitur baru

- **Handler baru**: Buat file di `app/handlers/`
- **Keyboard baru**: Tambahkan di `app/keyboards/inline_keyboards.py`
- **Fitur download**: Edit `src/managers/download_manager.py`
- **Fitur scheduler**: Edit `src/managers/scheduler_manager.py`
- **Database**: Edit `src/database/db_manager.py`

### Testing

```bash
# Jalankan bot dalam mode verbose
python main.py
```

## ⚠️ Catatan Penting

- ⚠️ **Keamanan**: Jangan share file `.env` yang berisi BOT_TOKEN
- 📦 **Storage**: Pastikan server memiliki space yang cukup untuk download
- 🔒 **Permission**: Bot hanya bisa digunakan oleh admin yang terdaftar
- 🌐 **Network**: Pastikan server memiliki koneksi internet yang stabil
- 💾 **Backup**: Backup file `.env` dan database `data/bot.db` di tempat aman
- 📍 **Custom Path**: Pastikan folder custom memiliki write permission

## 📄 License

Free to use. Silakan modifikasi sesuai kebutuhan.

## 🤝 Kontribusi

Jika ada bug atau saran fitur, silakan buat issue atau pull request.

## 📞 Support

Jika ada pertanyaan, silakan hubungi admin bot.

---

**Selamat menggunakan! 🚀**
