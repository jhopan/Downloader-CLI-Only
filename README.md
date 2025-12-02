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
chmod +x scripts/start.sh
./scripts/start.sh
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
bash scripts/install-service.sh
```

Service akan:

- ✅ Auto-start saat boot
- ✅ Auto-restart jika crash
- ✅ Run in background 24/7

### 3. Setup Bash Aliases (Opsional tapi Direkomendasikan!)

```bash
./scripts/setup-aliases.sh
```

⚠️ **PENTING: JANGAN pakai sudo!** Script harus dijalankan sebagai user biasa.

Script akan:

1. **Auto-detect service** - Mendeteksi service download\* yang terinstall
2. **Pilih service** - Jika ada multiple service
3. **Tanya nama alias** - Bebas pilih (contoh: `downloader`, `bot`, `dl`, `dcli`)
4. **Cek konflik** - Validasi alias tidak bentrok
5. **Tambahkan ke .bashrc** - Alias tersimpan permanen
6. **Aktifkan langsung** - Bisa langsung dipakai

---

## 🔄 Update & Maintenance

### Update Bot (Setelah Git Pull)

Jika sudah install service dan ada update dari git:

```bash
./scripts/update-bot.sh
```

Script akan:

1. ✅ **Stop service** yang sedang berjalan
2. ✅ **Pull latest changes** dari git (optional)
3. ✅ **Update dependencies** Python otomatis
4. ✅ **Reload systemd** daemon
5. ✅ **Restart service** dengan kode terbaru
6. ✅ **Check status** service setelah update

**Contoh:**

```bash
$ ./scripts/update-bot.sh

============================================================
🔄 Update Bot Telegram Pengunduh Otomatis
============================================================

✅ Service ditemukan: downloader-cli-only

⚠️  Update akan:
   1. Stop service yang sedang berjalan
   2. Pull perubahan terbaru dari git (optional)
   3. Update dependencies Python
   4. Reload systemd daemon
   5. Restart service

Lanjutkan update? (y/n): y

1️⃣  Stopping service...
   ✅ Service stopped

2️⃣  Update kode dari Git?
   Pull latest changes from Git? (y/n): y
   ✅ Git pull selesai

3️⃣  Update Python dependencies...
   ✅ Dependencies updated

4️⃣  Reload systemd daemon...
   ✅ Systemd daemon reloaded

5️⃣  Restart service...
   ✅ Service restarted

✅ Update berhasil! Service berjalan dengan baik.
```

### Uninstall Bot & Service

Untuk menghapus service dan aliases:

```bash
./scripts/uninstall-bot.sh
```

Script akan:

1. ✅ **Detect service** yang terinstall
2. ✅ **Stop & disable** service
3. ✅ **Remove service file** dari systemd
4. ✅ **Remove aliases** dari ~/.bashrc (optional)
5. ✅ **Backup .bashrc** sebelum menghapus aliases

⚠️ **Data TIDAK akan dihapus:**

- downloads/ - File hasil download
- data/ - Database bot
- .env - Konfigurasi bot

**Contoh:**

```bash
$ ./scripts/uninstall-bot.sh

============================================================
🗑️  Uninstall Bot Telegram Pengunduh Otomatis
============================================================

✅ Service yang akan dihapus: downloader-cli-only

⚠️  Uninstall akan:
   1. Stop service downloader-cli-only
   2. Disable autostart
   3. Hapus service file dari systemd
   4. Hapus aliases dari ~/.bashrc (optional)

Apakah Anda YAKIN ingin uninstall? (yes/no): yes

1️⃣  Stopping service...
   ✅ Service stopped

2️⃣  Disabling service...
   ✅ Service disabled

3️⃣  Removing service file...
   ✅ Service file removed

4️⃣  Reload systemd daemon...
   ✅ Systemd daemon reloaded

5️⃣  Remove aliases from ~/.bashrc?
   Hapus aliases? (y/n): y
   ✅ Backup dibuat: ~/.bashrc.backup.20251202_123456
   ✅ Aliases dihapus dari ~/.bashrc

✅ Uninstall Selesai!
```

**Contoh:**

```bash
$ ./scripts/setup-aliases.sh

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

## 🎯 Cara Menggunakan Bot

### 💡 TIDAK PERLU KETIK COMMAND!

Bot ini menggunakan **Inline Keyboard** untuk semua fitur. Tinggal **KLIK TOMBOL** saja! 🎉

### Memulai Bot

1. **Kirim `/start` ke bot**
2. **Menu utama** akan muncul dengan tombol-tombol:

   - 📥 Download
   - 📊 Status
   - 🎯 Smart Features
   - 🔒 Security
   - 📁 File Manager
   - ⚙️ Settings
   - 📈 Statistics
   - ℹ️ Help

3. **Klik tombol** yang Anda inginkan
4. **Navigasi menggunakan tombol** - tidak perlu ketik command manual!

### 📥 Download Menu

Klik **📥 Download** untuk akses:

- **🔗 Direct Download** - Download 1 URL langsung
  - Klik tombol → Send URL → Done!
- **📦 Batch Download** - Download hingga 20 URLs sekaligus
  - Klik tombol → Send URLs (satu per baris) → Klik "Done"
  - Real-time progress monitoring untuk semua files
- **⏰ Schedule Download** - Jadwalkan download
  - Pilih waktu via tombol: 1h, 3h, 6h, 12h, besok
  - Atau custom date & time picker
- **☁️ Cloud Download** - Download dari cloud storage
  - Google Drive, Dropbox, OneDrive
  - Auto-detect service type
- **🔄 Resume Download** - Lanjutkan download terputus
  - Lihat incomplete downloads
  - Klik tombol untuk resume
- **⚡ Bandwidth Limiter** - Kontrol kecepatan download
  - Set speed limit (KB/s)
  - Schedule bandwidth limits

### 📊 Status Menu

Klik **📊 Status** untuk melihat:

- **📊 Active Downloads** - Download yang sedang berjalan
- **📜 History** - Riwayat download lengkap
- **📅 Scheduled Downloads** - Daftar download terjadwal
- **📋 Queue Status** - Status antrian download
- **❌ Cancel Downloads** - Batalkan download dengan tombol

### 🎯 Smart Features Menu

Klik **🎯 Smart Features** untuk akses:

- **📋 Queue Manager** - Kelola antrian download
  - View, pause, resume, prioritize
  - Reorder queue items
- **👁️ File Preview** - Preview file & metadata
  - Image: dimensions, EXIF data
  - Video: duration, resolution, codec
  - Audio: title, artist, bitrate
  - Document: pages, format
- **🔍 Duplicate Check** - Deteksi file duplikat
  - MD5/SHA256 hash-based
  - Size & filename matching
- **🤖 Auto-Categorize** - Kategorisasi otomatis
  - 8 categories: Video, Audio, Image, Document, Archive, Code, Ebook, Software
  - Pattern learning from user actions
- **☁️ Cloud Manager** - Manage OAuth tokens
  - Google Drive, Dropbox, OneDrive
- **📈 Dashboard** - Statistics & analytics
  - Total downloads, bandwidth usage
  - Success rate, trending files

### 🔒 Security Menu

Klik **🔒 Security** untuk akses:

- **🛡️ Virus Scan** - Scan files dengan antivirus
  - ClamAV (local, fast)
  - VirusTotal (70+ engines)
  - Auto-quarantine infected files
- **🔐 Encrypt File** - Enkripsi file
  - AES-256-GCM encryption
  - Auto-generated atau custom password
- **🔓 Decrypt File** - Dekripsi file .enc
  - Password verification
- **📜 Scan History** - Riwayat virus scan
- **🔒 Encrypted Files** - Daftar file terenkripsi
- **🔄 Resume Downloads** - Lanjutkan download terputus
  - HTTP Range requests
  - Auto-save state every 1MB

### 📁 File Manager Menu

Klik **📁 File Manager** untuk:

- **📂 List All Files** - Tampilkan semua file
- **📁 By Category** - Tampilkan per kategori
- **🗑️ Delete Files** - Hapus file dengan konfirmasi
- **📦 Extract Archives** - Extract ZIP/RAR/TAR/7Z
- **🗂️ Categorize Files** - Pindahkan ke folder kategori
- **🧹 Clean All Files** - Hapus semua file (double confirmation!)
- **💾 Storage Info** - Informasi penyimpanan disk

### ⚙️ Settings Menu

Klik **⚙️ Settings** untuk konfigurasi:

- **📂 Download Path** - Atur lokasi download (Default/Custom)
  - Toggle Default ↔ Custom path
  - Set custom download directory
  - Support CasaOS `/DATA/` folders
  - Real-time path validation
- **⚡ Bandwidth** - Pengaturan bandwidth limiter
- **🔔 Notifications** - Pengaturan notifikasi
- **🎨 Categories** - Manage kategori file
- **🔑 API Keys** - Manage VirusTotal & Cloud APIs
- **🗄️ Database Info** - Informasi database

#### 📁 Mengubah Lokasi Download via Telegram

**Cara 1: Via Settings Menu (Recommended)**

1. `/start` → Klik **⚙️ Settings**
2. Klik **📝 Atur Lokasi Custom**
3. Kirim path download baru:
   ```
   /DATA/Downloads/telegram-bot
   ```
   atau
   ```
   /home/user/MyDownloads
   ```
4. Bot akan validasi dan create folder otomatis
5. Klik **📍 Lokasi Unduhan** untuk toggle Default ↔ Custom

**Cara 2: Saat Install Service**

```bash
sudo ./scripts/install-service.sh

# Saat ditanya path:
Pilih (1 atau 2): 2
Masukkan path download: /DATA/Downloads/telegram-bot
```

**Tips untuk CasaOS Users:**
- Gunakan path `/DATA/Downloads/telegram-bot` agar file accessible via file browser
- Folder `/DATA/` ter-expose di Samba share dan web file manager
- Folder `/home/` tidak accessible via CasaOS UI

### 💬 Contoh Penggunaan

**Download Single File:**

1. `/start` → Klik **📥 Download**
2. Klik **🔗 Direct Download**
3. Send URL file yang ingin didownload
4. Bot mulai download dengan progress bar!

**Batch Download:**

1. `/start` → Klik **📥 Download**
2. Klik **📦 Batch Download**
3. Klik **📤 Send URLs**
4. Send URLs (satu per baris):
   ```
   https://example.com/file1.mp4
   https://example.com/file2.zip
   https://example.com/file3.pdf
   ```
5. Klik tombol **"Done"** atau ketik `done`
6. Monitor batch progress secara real-time!

**Scan Virus:**

1. `/start` → Klik **🔒 Security**
2. Klik **🛡️ Virus Scan**
3. Klik **📁 Select File to Scan**
4. Pilih file dari list
5. Pilih scanner (ClamAV atau VirusTotal)
6. Lihat hasil scan!

**View Statistics:**

1. `/start` → Klik **📈 Statistics**
2. Lihat dashboard lengkap dengan:
   - Total downloads & bandwidth
   - Success rate
   - Top files
   - Charts & trending

### 🚫 Tidak Perlu Ketik Command Manual

❌ **TIDAK PERLU:**

- Ketik `/download https://example.com/file.mp4`
- Ketik `/scan filename.zip`
- Ketik `/encrypt myfile.pdf`
- Ketik `/done` atau command lainnya

✅ **CUKUP:**

- Klik tombol menu
- Send data yang diminta (URL, filename, etc)
- Klik tombol action
- Selesai!

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
│       ├── download_handler.py       # Download logic & validation
│       ├── file_handler.py           # List files with categories
│       ├── file_operations.py        # Delete/Extract/Categorize/Clean
│       ├── advanced_handler.py       # Batch & scheduled downloads
│       ├── bandwidth_handler.py      # Bandwidth limiter settings
│       ├── smart_features_handler.py # Smart features (queue/preview/stats/cloud/smartcat)
│       ├── security_handler.py       # Security features (scan/encrypt/decrypt/resume)
│       └── button_handler.py         # Button callbacks
├── src/
│   ├── managers/
│   │   ├── download_manager.py       # 3-method fallback downloader
│   │   ├── scheduler_service.py      # Background scheduler for scheduled downloads
│   │   ├── queue_manager.py          # Priority-based download queue
│   │   ├── statistics_manager.py     # Download statistics & dashboard
│   │   ├── cloud_downloader.py       # Cloud storage downloads (GDrive/Dropbox/OneDrive)
│   │   └── resume_downloader.py      # Resume interrupted downloads (HTTP Range)
│   ├── database/
│   │   └── db_manager.py             # SQLite database with 14 tables
│   └── utils/
│       ├── file_hasher.py            # Hash calculation for duplicate detection
│       ├── file_preview.py           # Metadata extraction & thumbnails
│       ├── smart_categorizer.py      # Pattern-based file categorization
│       ├── file_encryption.py        # AES-256-GCM encryption/decryption
│       └── virus_scanner.py          # ClamAV & VirusTotal integration
├── utils/
│   └── link_validator.py             # Link validation (HEAD/GET)
├── scripts/
│   ├── start.sh                      # Auto-setup & run bot
│   ├── install-service.sh            # Install systemd service
│   └── setup-aliases.sh              # Setup bash aliases
├── downloads/                         # Default download folder
│   ├── Video/                        # Created by categorize
│   ├── Audio/
│   ├── Image/
│   ├── Document/
│   ├── Archive/
│   └── Other/
├── config/
│   └── settings.py                   # Load from .env
├── main.py                           # Main bot file
├── .env                              # Configuration
├── requirements.txt                  # Python dependencies
└── README.md                         # This file
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
cryptography>=41.0.0         # AES-256-GCM encryption
Pillow>=10.0.0               # Image processing & thumbnails
mutagen>=1.47.0              # Audio metadata extraction
PyPDF2>=3.0.0                # PDF document metadata
rarfile>=4.0                 # RAR archive extraction
py7zr>=0.20.0                # 7Z archive extraction
```

### Optional Dependencies (System Packages)

```bash
# UnRAR (REQUIRED untuk extract file .rar)
sudo apt install unrar

# ClamAV (untuk virus scanning lokal)
sudo apt-get install clamav clamav-daemon

# FFmpeg (untuk video thumbnail & metadata)
sudo apt-get install ffmpeg
```

**📦 Archive Extraction Support:**
- **ZIP** - Built-in Python support ✅
- **TAR, TAR.GZ, TAR.BZ2** - Built-in Python support ✅
- **RAR** - Requires `rarfile` + `unrar` tool ⚠️
- **7Z** - Requires `py7zr` library ✅

Install semua dengan:

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install system tools (Linux/Ubuntu/Debian/CasaOS)
sudo apt update
sudo apt install unrar ffmpeg -y
```

---

## 🌟 Feature Highlights

### 18 Total Features Implemented

**Core Downloads (3)**

- Multi-URL Batch Downloads
- Scheduled Downloads
- Bandwidth Limiter

**Smart Features (6)**

- Smart Duplicate Detection
- Download Queue Management
- File Preview & Metadata
- Statistics Dashboard
- Cloud Storage Downloads
- Smart Auto-Categorization

**Security Features (3)**

- Virus Scanning (ClamAV + VirusTotal)
- File Encryption (AES-256-GCM)
- Resume Downloads (HTTP Range)

**File Operations (6)**

- List Files
- Delete Files
- Extract Archives
- Categorize Files
- Clean All Files
- File Statistics

---

## 🎯 Advanced Configuration

### Environment Variables

```bash
# .env file
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789,987654321
DOWNLOAD_DIR=/custom/path/downloads

# Optional: VirusTotal API (untuk online scanning)
VT_API_KEY=your_virustotal_api_key

# Optional: Database path
DB_PATH=/custom/path/bot_database.db
```

### Database Schema

Bot menggunakan SQLite dengan 14 tabel:

1. **downloads** - Download history
2. **active_downloads** - Current downloads
3. **scheduled_downloads** - Scheduled tasks
4. **bandwidth_schedules** - Bandwidth limits
5. **file_hashes** - Duplicate detection
6. **download_queue** - Queue management
7. **file_metadata** - File preview data
8. **download_statistics** - Stats tracking
9. **cloud_tokens** - OAuth tokens
10. **categorization_rules** - Smart categorization patterns
11. **virus_scan_results** - Scan history
12. **encryption_passwords** - Encrypted file info
13. **download_states** - Resume download states
14. **user_preferences** - User settings

---

## 🚀 Performance & Scalability

- **Async/Await** - Non-blocking operations
- **Connection Pooling** - Efficient HTTP connections
- **Chunk Processing** - Memory-efficient large files
- **Background Tasks** - Scheduler & queue processor
- **State Persistence** - Auto-save every 1MB (resume)
- **Concurrent Downloads** - Max 3 simultaneous (configurable)

---

## 🔒 Security Best Practices

- **AES-256-GCM** - Military-grade encryption
- **PBKDF2** - 100,000 iterations key derivation
- **No Password Storage** - Passwords never stored
- **Auto-Quarantine** - Infected files isolated
- **Authenticated Encryption** - Tamper-proof files
- **Access Control** - Admin whitelist only

---

## 📈 Statistics

- **Total Code**: 10,000+ lines
- **New Files**: 17+ files created
- **Database Tables**: 14 tables
- **Features**: 18 complete features
- **Commands**: 20+ bot commands
- **Dependencies**: 9 Python packages

---

## 🤝 Contributing

1. Fork repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file

---

## 👤 Author

**jhopan**

- GitHub: [@jhopan](https://github.com/jhopan)
- Repository: [Downloader-CLI-Only](https://github.com/jhopan/Downloader-CLI-Only)

---

## 🙏 Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot API wrapper
- [aiohttp](https://github.com/aio-libs/aiohttp) - Async HTTP client
- [ClamAV](https://www.clamav.net/) - Open-source antivirus
- [VirusTotal](https://www.virustotal.com/) - Multi-engine malware scanner
- [cryptography](https://cryptography.io/) - Modern cryptography for Python
