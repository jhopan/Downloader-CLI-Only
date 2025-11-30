# 🤖 Bot Telegram Pengunduh Otomatis (CLI Only)

> Bot Telegram yang dapat mengunduh file dari link apapun dengan fitur lengkap seperti download manager, file operations, real-time progress, dan multiple fallback methods. Dirancang untuk berjalan di server Linux/Debian/Ubuntu sebagai systemd service.

[![GitHub](https://img.shields.io/badge/GitHub-jhopan-blue?logo=github)](https://github.com/jhopan/Downloader-CLI-Only)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## ✨ Fitur Utama

### 📥 Download Manager dengan 3 Fallback Methods

- **aiohttp** (Primary) - Async HTTP client, cepat dengan enhanced headers
- **urllib** (Secondary) - Built-in Python, reliable untuk berbagai server
- **requests** (Tertiary) - Popular library, excellent compatibility
- **Smart Fallback** - Otomatis coba metode berikutnya jika gagal
- **Real-time Progress** - Progress bar dengan kecepatan download (MB/s)
- **Link Validation** - Validasi link sebelum download (HEAD/GET request)
- **Smart Filename Detection** - Deteksi dari URL/Content-Disposition/Content-Type
- **Concurrent Downloads** - Multiple download bersamaan

### 🚀 Advanced Download Features

- **Multi-URL Batch Download** - Download hingga 20 URL sekaligus
  - Real-time batch progress monitoring
  - Individual file progress tracking
  - Auto-retry untuk failed downloads
  
- **Scheduled Downloads** - Jadwalkan download untuk waktu tertentu
  - Quick time picker (1h, 3h, 6h, 12h, besok)
  - Custom date & time picker
  - Background scheduler service (check setiap 60 detik)
  - Notification saat schedule dimulai
  
- **Bandwidth Limiter** - Kontrol kecepatan download
  - Set global speed limit (KB/s)
  - Schedule bandwidth (batas waktu tertentu)
  - Dynamic limit based on current time
  - Unlimited mode available

### 🎯 Smart Features (NEW!)

- **🔍 Smart Duplicate Detection**
  - MD5/SHA256 hash-based detection
  - Size and filename matching
  - Skip atau replace options
  - Duplicate prevention notification
  
- **📋 Download Queue Management**
  - Priority-based queue system (Low/Normal/High/Urgent)
  - Pause/Resume individual downloads
  - Reorder queue items
  - Max concurrent downloads control (default: 3)
  - Real-time queue visualization
  
- **👁️ File Preview**
  - Image preview dengan EXIF data
  - Video metadata (duration, resolution, codec)
  - Audio metadata (title, artist, album, bitrate)
  - Document info (PDF pages, etc)
  - Auto thumbnail generation
  
- **📊 Statistics Dashboard**
  - Total downloads & bandwidth usage
  - Success rate tracking
  - Top 10 largest files
  - Daily/Weekly/Monthly charts
  - Trending file types
  - Time distribution analysis
  
- **☁️ Cloud Storage Download**
  - Google Drive support
  - Dropbox support
  - OneDrive/SharePoint support
  - Direct link extraction
  - OAuth token management
  
- **🤖 Smart Auto-Categorization**
  - Pattern-based categorization
  - Learning dari user actions
  - 8 default categories (Video, Audio, Image, Document, Archive, Code, Ebook, Software)
  - Custom pattern rules
  - Confidence scoring
  - Auto-organize downloads folder

### 🔒 Security & Advanced Features (NEW!)

- **🛡️ Virus Scanning**
  - ClamAV integration (local, fast)
  - VirusTotal API support (70+ engines)
  - Auto-quarantine infected files
  - Scan history tracking
  
- **🔐 File Encryption**
  - AES-256-GCM encryption
  - PBKDF2 key derivation (100,000 iterations)
  - Auto-generated secure passwords
  - Authenticated encryption (tamper-proof)
  
- **🔄 Resume Downloads**
  - HTTP Range requests support
  - Auto-save download state every 1MB
  - Resume from exact byte position
  - Works with interrupted/failed downloads
  - Supports files of any size

### 📁 File Manager & Operations

- **List Files** - Tampilkan files dengan kategori (Video/Audio/Image/Document/Archive/Other)
- **Delete** - Hapus file individual dengan konfirmasi
- **Extract Archives** - Extract zip, tar.gz, 7z, rar otomatis
- **Categorize Files** - Pindahkan files ke folder sesuai tipe
- **Clean All** - Hapus semua file dengan double confirmation
- **Statistics** - Total size dan count per kategori

### 🔧 Systemd Service & Management

- **Systemd Integration** - Berjalan sebagai service
- **Auto Start** - Start otomatis saat boot
- **Auto Restart** - Restart otomatis jika crash
- **Bash Aliases** - Perintah cepat untuk management
- **Journalctl Logging** - Log terintegrasi dengan systemd

---

## 🚀 Quick Start (3 Langkah!)

### 1. Jalankan Bot (Otomatis Setup Semua!)

```bash
chmod +x start.sh
./start.sh
```

Script `start.sh` akan otomatis:

1. **Membuat file .env** dari .env.example
2. **Minta BOT_TOKEN** - Copy dari @BotFather
3. **Minta ADMIN_IDS** - Copy dari @userinfobot
4. **Install dependencies** - Otomatis pip install
5. **Jalankan bot** - Langsung running!

**Contoh interaksi:**

```bash
$ ./start.sh

============================================================
🤖 Bot Telegram Pengunduh Otomatis
============================================================

⚙️  SETUP KONFIGURASI BOT
============================================================

📍 Langkah 1: Dapatkan Bot Token
   1. Buka Telegram, cari @BotFather
   2. Kirim: /newbot
   3. Ikuti instruksi untuk buat bot
   4. Copy token yang diberikan

Masukkan BOT_TOKEN: 1234567890:ABCdef...
✅ BOT_TOKEN tersimpan di .env

📍 Langkah 2: Dapatkan User ID Telegram
   1. Buka Telegram, cari @userinfobot
   2. Bot akan kirim ID Anda
   3. Untuk multiple admin, pisahkan dengan koma

Masukkan ADMIN_IDS: 123456789
✅ ADMIN_IDS tersimpan di .env

✅ Konfigurasi berhasil!
🚀 Bot sedang berjalan...
```

### 2. Install sebagai Systemd Service (Opsional)

```bash
bash install-service.sh
```

Service akan:

- ✅ Auto-start saat boot
- ✅ Auto-restart jika crash
- ✅ Run in background 24/7

### 3. Setup Bash Aliases (Opsional tapi Direkomendasikan!)

```bash
./setup-aliases.sh
```

⚠️ **PENTING: JANGAN pakai sudo!** Script harus dijalankan sebagai user biasa.

Script akan:

1. **Auto-detect service** - Mendeteksi service download\* yang terinstall
2. **Pilih service** - Jika ada multiple service
3. **Tanya nama alias** - Bebas pilih (contoh: `downloader`, `bot`, `dl`, `dcli`)
4. **Cek konflik** - Validasi alias tidak bentrok
5. **Tambahkan ke .bashrc** - Alias tersimpan permanen
6. **Aktifkan langsung** - Bisa langsung dipakai

**Contoh:**

```bash
$ ./setup-aliases.sh

🔧 Setup Bash Aliases untuk Systemd Service
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 Mendeteksi systemd service...
📋 Service yang terdeteksi:

1) downloader-cli-only
2) Manual Input
#? 1

✅ Service yang dipilih: downloader-cli-only

📝 Masukkan nama alias yang diinginkan (default: downloader)
   Contoh: downloader, bot, dl, dcli, etc.
   Nama alias akan menjadi prefix perintah (contoh: start<alias>)
Nama alias [downloader]: dcli

✅ Nama alias: dcli
✅ Command prefix: dcli

✅ Nama alias: dcli
✅ Command prefix: dcli

➕ Menambahkan alias baru ke ~/.bashrc...

✅ Alias berhasil ditambahkan!

📋 Daftar Perintah Tersedia:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  startdcli       - Start service
  stopdcli        - Stop service
  restartdcli     - Restart service
  statusdcli      - Cek status service
  logsdcli        - Lihat log realtime (follow)
  logs100dcli     - Lihat 100 log terakhir
  logs500dcli     - Lihat 500 log terakhir
  enabledcli      - Enable autostart saat boot
  disabledcli     - Disable autostart
  reloaddcli      - Reload systemd daemon
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔄 Untuk mengaktifkan alias sekarang, jalankan:
   source ~/.bashrc

Apakah Anda ingin mengaktifkan alias sekarang? (y/n): y
✅ Alias sudah aktif! Coba jalankan: statusdcli

ℹ️  Catatan: Jika masih tidak berfungsi, tutup dan buka terminal baru.
```

**Setelah setup, Anda bisa pakai perintah cepat:**

```bash
# Contoh jika pilih nama "dcli"
startdcli         # Start service
stopdcli          # Stop service
statusdcli        # Cek status
logsdcli          # Lihat log realtime

# Contoh jika pilih nama "bot"
startbot          # Start service
stopbot           # Stop service
statusbot         # Cek status
logsbot           # Lihat log realtime

# Jika pilih nama "downloader"
startdownloader   # Start service
stopdownloader    # Stop service
statusdownloader  # Cek status
logsdownloader    # Lihat log realtime
```

**Catatan Penting:**

- ❌ **JANGAN jalankan dengan sudo** (`sudo ./setup-aliases.sh`) - ini akan menambahkan alias ke root, bukan user Anda
- ✅ **Jalankan sebagai user biasa** (`./setup-aliases.sh`)
- ✅ Jika alias tidak berfungsi setelah `source ~/.bashrc`, **tutup dan buka terminal baru**
- ✅ Dash (`-`) di nama alias akan otomatis diganti jadi underscore (`_`) untuk command name

---

## 🎯 Perintah Bot di Telegram

Kirim perintah ini ke bot:

### Download

- Kirim URL langsung - Bot otomatis detect dan download
- `/download <url>` - Download file dari URL

### Advanced Downloads

- `/batch` - Download multiple URLs sekaligus (max 20 URLs)
  - Kirim URLs (satu per baris)
  - Real-time batch progress monitoring
  - Individual progress per file
  
- `/schedule` - Jadwalkan download untuk nanti
  - Quick picker: 1h, 3h, 6h, 12h, besok
  - Custom date & time picker
  - Notifikasi saat schedule dimulai
  
- `/myschedules` - Lihat daftar schedule aktif
  - Cancel schedule dengan tombol
  
- `/bandwidth` - Pengaturan bandwidth limiter
  - Set speed limit (KB/s)
  - Schedule bandwidth (limit waktu tertentu)
  - Reset to unlimited

### Smart Features

- `/queue` - Lihat download queue status
  - Priority management
  - Pause/Resume downloads
  - Queue statistics
  
- `/preview` - Preview file dengan metadata
  - Image: dimensions, format, EXIF
  - Video: duration, resolution, codec
  - Audio: title, artist, bitrate
  - Auto thumbnail generation
  
- `/stats` - Download statistics dashboard
  - Total downloads & bandwidth
  - Success rate tracking
  - Top largest files
  - Daily/Weekly charts
  - Trending file types
  
- `/cloud` - Download dari cloud storage
  - Google Drive
  - Dropbox
  - OneDrive
  - Auto-detect service
  
- `/smartcat` - Smart auto-categorization
  - Pattern-based categorization
  - Learning dari user actions
  - Auto-organize files
  - View learned patterns
  
- `/duplicates` - Check duplicate files
  - Hash-based detection
  - Size & filename matching
  - Duplicate report

### Security Features

- `/scan` - Virus scanning
  - ClamAV local scan
  - VirusTotal online scan
  - Auto-quarantine infected files
  - Scan history
  
- `/encrypt` - Encrypt file
  - AES-256-GCM encryption
  - Auto-generated password
  - Secure & authenticated
  
- `/decrypt` - Decrypt file
  - Decrypt .enc files
  - Password verification
  
- `/resume` - Resume downloads
  - Show incomplete downloads
  - Resume from last position
  - Auto-save state every 1MB

### Scheduled & Batch Downloads

- `/batch` - Download multiple URLs sekaligus (max 20 URLs)
  - Kirim URLs (satu per baris)
  - Real-time batch progress monitoring
  - Individual progress per file
  
- `/schedule` - Jadwalkan download untuk nanti
  - Quick picker: 1h, 3h, 6h, 12h, besok
  - Custom date & time picker
  - Notifikasi saat schedule dimulai
  
- `/myschedules` - Lihat daftar schedule aktif
  - Cancel schedule dengan tombol
  
- `/bandwidth` - Pengaturan bandwidth limiter
  - Set speed limit (KB/s)
  - Schedule bandwidth (limit waktu tertentu)
  - Reset to unlimited

### File Manager

- `/files` - List semua file dengan kategori
  - Tampilkan: Video, Audio, Image, Document, Archive, Other
  - Total size dan count per kategori
  - Button operasi per file

### File Operations

**Per File:**

- 🗑️ **Delete** - Hapus file dengan konfirmasi
- 📦 **Extract** - Extract archive (zip/tar.gz/7z/rar)

**All Files:**

- 📁 **Categorize Files** - Pindahkan ke folder kategori (Video/, Audio/, dll)
- 🗑️ **Clean All Files** - Hapus semua file (double confirmation!)

### Status & History

- `/status` - Status download aktif
- `/history` - Riwayat download

---

## 📊 Download Flow

```
1. User kirim URL
2. Bot validasi link (HEAD/GET request)
   └─ ✅ Valid? Lanjut download
   └─ ❌ Invalid? Coba download tetap (fallback)

3. Bot mulai download dengan fallback:
   ┌─ Try: aiohttp (async, fast, enhanced headers)
   │  └─ ✅ Success? Done!
   │  └─ ❌ Failed? Next method...
   │
   ├─ Try: urllib (built-in, reliable)
   │  └─ ✅ Success? Done!
   │  └─ ❌ Failed? Next method...
   │
   └─ Try: requests (popular, great compatibility)
      └─ ✅ Success? Done!
      └─ ❌ Failed? Report all errors

4. Progress update setiap 10%
   └─ Show: percentage, speed, size

5. File saved with smart filename
   └─ From: URL → Content-Disposition → Content-Type

6. Update database & notify user
```

---

## 📁 Struktur Folder

```
Downloader-CLI-Only/
├── app/
│   └── handlers/
│       ├── download_handler.py    # Download logic & validation
│       ├── file_handler.py        # List files with categories
│       ├── file_operations.py     # Delete/Extract/Categorize/Clean
│       ├── advanced_handler.py    # Batch & scheduled downloads
│       ├── bandwidth_handler.py   # Bandwidth limiter settings
│       └── button_handler.py      # Button callbacks
├── src/
│   ├── managers/
│   │   ├── download_manager.py    # 3-method fallback downloader
│   │   └── scheduler_service.py   # Background scheduler for scheduled downloads
│   └── database/
│       └── db_manager.py          # SQLite database with advanced features
├── utils/
│   └── link_validator.py          # Link validation (HEAD/GET)
├── downloads/                      # Default download folder
│   ├── Video/                     # Created by categorize
│   ├── Audio/
│   ├── Image/
│   ├── Document/
│   ├── Archive/
│   └── Other/
├── config/
│   └── settings.py                # Load from .env
├── bot.py                         # Main bot file
├── .env                           # Configuration
├── requirements.txt               # Python dependencies
├── install-service.sh             # Install systemd service
├── setup-aliases.sh               # Setup bash aliases
└── README.md                      # This file
```

---

## 🔧 Management Commands

### Manual Commands (Tanpa Aliases)

```bash
# Service management
sudo systemctl start downloader-cli-only
sudo systemctl stop downloader-cli-only
sudo systemctl restart downloader-cli-only
sudo systemctl status downloader-cli-only

# Logs
sudo journalctl -u downloader-cli-only -f         # Follow realtime
sudo journalctl -u downloader-cli-only -n 100     # Last 100 lines
sudo journalctl -u downloader-cli-only --no-pager # All logs
sudo journalctl -u downloader-cli-only -p err     # Errors only
```

### Dengan Aliases (Setelah Setup)

Tergantung nama alias yang Anda pilih saat setup:

```bash
# Contoh jika pilih "bot"
startbot          # Start service
stopbot           # Stop service
restartbot        # Restart service
statusbot         # Status check
logsbot           # Realtime logs
logs100bot        # Last 100 lines
logs500bot        # Last 500 lines
enablebot         # Enable autostart
disablebot        # Disable autostart
reloadbot         # Reload systemd
```

---

## 🛠️ Troubleshooting

### Service Tidak Start

```bash
# Cek status (ganti 'bot' dengan nama alias Anda)
statusbot

# Atau manual
sudo systemctl status downloader-cli-only

# Lihat error di log
logsbot
# Atau manual
sudo journalctl -u downloader-cli-only -n 50
```

### Download Gagal Semua Metode

Cek log untuk melihat alasan setiap metode gagal:

```bash
logsbot
```

Log akan tampilkan:

```
❌ Semua metode gagal!
   - aiohttp: HTTP 403
   - urllib: HTTP 403
   - requests: Connection timeout
```

**Solusi:**

- Cek koneksi internet
- Cek apakah URL masih valid
- Beberapa server block automated downloads
- Coba download ulang (link mungkin temporary down)

### Alias Tidak Berfungsi

```bash
# Reload .bashrc
source ~/.bashrc

# Atau buka terminal baru
```

### Update Bot Setelah Git Pull

```bash
# Pull perubahan
git pull origin main

# Restart service (pakai alias atau manual)
restartbot
# Atau manual:
sudo systemctl restart downloader-cli-only
```

### Uninstall Service

```bash
sudo systemctl stop downloader-cli-only
sudo systemctl disable downloader-cli-only
sudo rm /etc/systemd/system/downloader-cli-only.service
sudo systemctl daemon-reload
```

### Remove Aliases

Edit `~/.bashrc`:

```bash
nano ~/.bashrc
```

Hapus section:

```bash
# Downloader CLI Only Aliases - <nama_alias>
...
# End Downloader CLI Only Aliases - <nama_alias>
```

Lalu reload:

```bash
source ~/.bashrc
```

---

## 📝 Log Examples

### Successful Download

```
📥 Memulai download: video.mp4
💾 Lokasi: /home/user/downloads/video.mp4
📦 Ukuran file: 50.2 MB
⏳ Progress: 10.0% | 5.0 MB / 50.2 MB | Speed: 2.5 MB/s
⏳ Progress: 20.0% | 10.0 MB / 50.2 MB | Speed: 2.6 MB/s
⏳ Progress: 30.0% | 15.0 MB / 50.2 MB | Speed: 2.7 MB/s
...
✅ Download selesai: video.mp4 (50.2 MB)
📁 File tersimpan di: /home/user/downloads/video.mp4
```

### Download with Fallback

```
📥 Memulai download: file.zip
💾 Lokasi: /home/user/downloads/file.zip
⚠️ aiohttp gagal: HTTP 403
🔄 Mencoba dengan urllib...
🔧 Menggunakan urllib untuk download
📦 Ukuran file: 100.5 MB
⏳ Progress: 10.0% | 10.0 MB / 100.5 MB | Speed: 5.2 MB/s
...
✅ Download selesai: file.zip (100.5 MB)
```

### All Methods Failed

```
📥 Memulai download: blocked.file
💾 Lokasi: /home/user/downloads/blocked.file
⚠️ aiohttp gagal: HTTP 403
🔄 Mencoba dengan urllib...
⚠️ urllib juga gagal: HTTP 403
🔄 Mencoba dengan requests (fallback terakhir)...
❌ Semua metode gagal!
   - aiohttp: HTTP 403
   - urllib: HTTP 403
   - requests: HTTP 403
```

---

## 🔐 Keamanan

- ✅ **Whitelist User** - Hanya user di ALLOWED_USERS yang bisa pakai
- ✅ **Non-Root Service** - Service berjalan sebagai user biasa (bukan root)
- ✅ **Isolated Downloads** - Download folder dapat dikustomisasi
- ✅ **Validation** - Link divalidasi sebelum download
- ✅ **Confirmation** - Double confirmation untuk operasi destructive (clean all)

---

## 📦 Dependencies

```
python-telegram-bot>=21.0    # Telegram Bot API
aiohttp==3.9.1               # Async HTTP (primary download)
aiofiles==23.2.1             # Async file operations
python-dotenv==1.0.0         # Environment variables
requests>=2.31.0             # HTTP library (3rd fallback)
```

Install semua dengan:

```bash
pip install -r requirements.txt
```
