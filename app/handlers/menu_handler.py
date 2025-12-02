"""
Comprehensive menu handler with inline keyboards for all features
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.handlers.common import is_admin
from app.handlers.states import MAIN_MENU
import logging

logger = logging.getLogger(__name__)


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, edit_message=True):
    """Display main menu with all features"""
    keyboard = [
        [
            InlineKeyboardButton("📥 Download", callback_data="menu_download"),
            InlineKeyboardButton("📊 Status", callback_data="menu_status")
        ],
        [
            InlineKeyboardButton("🎯 Smart Features", callback_data="menu_smart"),
            InlineKeyboardButton("🔒 Security", callback_data="menu_security")
        ],
        [
            InlineKeyboardButton("📁 File Manager", callback_data="menu_files"),
            InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings")
        ],
        [
            InlineKeyboardButton("📈 Statistics", callback_data="show_stats"),
            InlineKeyboardButton("ℹ️ Help", callback_data="show_help")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "🤖 <b>Bot Telegram Pengunduh Otomatis</b>\n\n"
        "Pilih menu di bawah untuk memulai:\n\n"
        "📥 <b>Download</b> - Download file dari URL\n"
        "📊 <b>Status</b> - Lihat download aktif & history\n"
        "🎯 <b>Smart Features</b> - Queue, Preview, Cloud, etc\n"
        "🔒 <b>Security</b> - Scan, Encrypt, Resume\n"
        "📁 <b>File Manager</b> - Kelola file hasil download\n"
        "⚙️ <b>Settings</b> - Konfigurasi bot\n"
        "📈 <b>Statistics</b> - Dashboard statistik\n"
        "ℹ️ <b>Help</b> - Panduan penggunaan"
    )
    
    if edit_message and update.callback_query:
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    else:
        message = update.message or update.callback_query.message
        await message.reply_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    return MAIN_MENU


async def show_download_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Download menu"""
    keyboard = [
        [
            InlineKeyboardButton("🔗 Direct Download", callback_data="download_direct"),
            InlineKeyboardButton("📦 Batch Download", callback_data="download_batch")
        ],
        [
            InlineKeyboardButton("⏰ Schedule Download", callback_data="download_schedule"),
            InlineKeyboardButton("☁️ Cloud Download", callback_data="download_cloud")
        ],
        [
            InlineKeyboardButton("🔄 Resume Download", callback_data="download_resume"),
            InlineKeyboardButton("⚡ Bandwidth Limiter", callback_data="download_bandwidth")
        ],
        [InlineKeyboardButton("◀️ Back to Main Menu", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "📥 <b>Download Menu</b>\n\n"
        "Pilih jenis download:\n\n"
        "🔗 <b>Direct Download</b> - Download 1 URL\n"
        "📦 <b>Batch Download</b> - Download multiple URLs (max 20)\n"
        "⏰ <b>Schedule Download</b> - Jadwalkan download\n"
        "☁️ <b>Cloud Download</b> - Download dari Google Drive/Dropbox/OneDrive\n"
        "🔄 <b>Resume Download</b> - Lanjutkan download yang terputus\n"
        "⚡ <b>Bandwidth Limiter</b> - Atur kecepatan download"
    )
    
    await update.callback_query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    return MAIN_MENU


async def show_status_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Status menu"""
    keyboard = [
        [
            InlineKeyboardButton("📊 Active Downloads", callback_data="status_active"),
            InlineKeyboardButton("📜 History", callback_data="status_history")
        ],
        [
            InlineKeyboardButton("📅 Scheduled Downloads", callback_data="status_schedules"),
            InlineKeyboardButton("📋 Queue Status", callback_data="status_queue")
        ],
        [
            InlineKeyboardButton("❌ Cancel Downloads", callback_data="status_cancel")
        ],
        [InlineKeyboardButton("◀️ Back to Main Menu", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "📊 <b>Status & History Menu</b>\n\n"
        "📊 <b>Active Downloads</b> - Download yang sedang berjalan\n"
        "📜 <b>History</b> - Riwayat download\n"
        "📅 <b>Scheduled Downloads</b> - Download terjadwal\n"
        "📋 <b>Queue Status</b> - Status antrian download\n"
        "❌ <b>Cancel Downloads</b> - Batalkan download aktif"
    )
    
    await update.callback_query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    return MAIN_MENU


async def show_smart_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Smart features menu"""
    keyboard = [
        [
            InlineKeyboardButton("📋 Queue Manager", callback_data="smart_queue"),
            InlineKeyboardButton("👁️ File Preview", callback_data="smart_preview")
        ],
        [
            InlineKeyboardButton("🔍 Duplicate Check", callback_data="smart_duplicate"),
            InlineKeyboardButton("🤖 Auto-Categorize", callback_data="smart_categorize")
        ],
        [
            InlineKeyboardButton("☁️ Cloud Manager", callback_data="smart_cloud"),
            InlineKeyboardButton("📈 Dashboard", callback_data="smart_dashboard")
        ],
        [InlineKeyboardButton("◀️ Back to Main Menu", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "🎯 <b>Smart Features Menu</b>\n\n"
        "📋 <b>Queue Manager</b> - Kelola antrian download\n"
        "👁️ <b>File Preview</b> - Preview & metadata file\n"
        "🔍 <b>Duplicate Check</b> - Deteksi file duplikat\n"
        "🤖 <b>Auto-Categorize</b> - Kategorisasi otomatis\n"
        "☁️ <b>Cloud Manager</b> - Manage cloud tokens\n"
        "📈 <b>Dashboard</b> - Statistik & analytics"
    )
    
    await update.callback_query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    return MAIN_MENU


async def show_security_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Security features menu"""
    keyboard = [
        [
            InlineKeyboardButton("🛡️ Virus Scan", callback_data="security_scan"),
            InlineKeyboardButton("🔐 Encrypt File", callback_data="security_encrypt")
        ],
        [
            InlineKeyboardButton("🔓 Decrypt File", callback_data="security_decrypt"),
            InlineKeyboardButton("📜 Scan History", callback_data="security_scan_history")
        ],
        [
            InlineKeyboardButton("🔒 Encrypted Files", callback_data="security_encrypted_files"),
            InlineKeyboardButton("🔄 Resume Downloads", callback_data="security_resume")
        ],
        [InlineKeyboardButton("◀️ Back to Main Menu", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "🔒 <b>Security Features Menu</b>\n\n"
        "🛡️ <b>Virus Scan</b> - Scan file dengan ClamAV/VirusTotal\n"
        "🔐 <b>Encrypt File</b> - Enkripsi file dengan AES-256-GCM\n"
        "🔓 <b>Decrypt File</b> - Dekripsi file terenkripsi\n"
        "📜 <b>Scan History</b> - Riwayat virus scan\n"
        "🔒 <b>Encrypted Files</b> - Daftar file terenkripsi\n"
        "🔄 <b>Resume Downloads</b> - Lanjutkan download terputus"
    )
    
    await update.callback_query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    return MAIN_MENU


async def show_files_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """File manager menu"""
    keyboard = [
        [
            InlineKeyboardButton("📂 List All Files", callback_data="files_list_all"),
            InlineKeyboardButton("📁 By Category", callback_data="files_by_category")
        ],
        [
            InlineKeyboardButton("🗑️ Delete Files", callback_data="files_delete"),
            InlineKeyboardButton("📦 Extract Archives", callback_data="files_extract")
        ],
        [
            InlineKeyboardButton("🗂️ Categorize Files", callback_data="files_categorize"),
            InlineKeyboardButton("🧹 Clean All Files", callback_data="files_clean_all")
        ],
        [
            InlineKeyboardButton("💾 Storage Info", callback_data="files_storage")
        ],
        [InlineKeyboardButton("◀️ Back to Main Menu", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "📁 <b>File Manager Menu</b>\n\n"
        "📂 <b>List All Files</b> - Tampilkan semua file\n"
        "📁 <b>By Category</b> - Tampilkan per kategori\n"
        "🗑️ <b>Delete Files</b> - Hapus file individual\n"
        "📦 <b>Extract Archives</b> - Extract file ZIP/RAR/7Z/TAR\n"
        "🗂️ <b>Categorize Files</b> - Pindahkan ke folder kategori\n"
        "🧹 <b>Clean All Files</b> - Hapus semua file (HATI-HATI!)\n"
        "💾 <b>Storage Info</b> - Informasi penyimpanan"
    )
    
    await update.callback_query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    return MAIN_MENU


async def show_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Settings menu"""
    keyboard = [
        [
            InlineKeyboardButton("📂 Download Path", callback_data="settings_path"),
            InlineKeyboardButton("⚡ Bandwidth", callback_data="settings_bandwidth")
        ],
        [
            InlineKeyboardButton("🔔 Notifications", callback_data="settings_notifications"),
            InlineKeyboardButton("🎨 Categories", callback_data="settings_categories")
        ],
        [
            InlineKeyboardButton("🔑 API Keys", callback_data="settings_api_keys"),
            InlineKeyboardButton("🗄️ Database Info", callback_data="settings_database")
        ],
        [InlineKeyboardButton("◀️ Back to Main Menu", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "⚙️ <b>Settings Menu</b>\n\n"
        "📂 <b>Download Path</b> - Atur lokasi download\n"
        "⚡ <b>Bandwidth</b> - Pengaturan bandwidth limiter\n"
        "🔔 <b>Notifications</b> - Pengaturan notifikasi\n"
        "🎨 <b>Categories</b> - Atur kategori file\n"
        "🔑 <b>API Keys</b> - Manage VirusTotal & Cloud APIs\n"
        "🗄️ <b>Database Info</b> - Informasi database"
    )
    
    await update.callback_query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    return MAIN_MENU


async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help information"""
    keyboard = [
        [
            InlineKeyboardButton("📥 Download Help", callback_data="help_download"),
            InlineKeyboardButton("🎯 Smart Features Help", callback_data="help_smart")
        ],
        [
            InlineKeyboardButton("🔒 Security Help", callback_data="help_security"),
            InlineKeyboardButton("📁 File Manager Help", callback_data="help_files")
        ],
        [InlineKeyboardButton("◀️ Back to Main Menu", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "ℹ️ <b>Help & Documentation</b>\n\n"
        "<b>Cara Menggunakan Bot:</b>\n\n"
        "1️⃣ Pilih menu dari tombol yang tersedia\n"
        "2️⃣ Ikuti instruksi di setiap menu\n"
        "3️⃣ Semua operasi menggunakan tombol inline\n"
        "4️⃣ Tidak perlu ketik command manual!\n\n"
        "<b>Fitur Utama:</b>\n"
        "• Download dari URL (batch/schedule/cloud)\n"
        "• Smart features (queue/preview/stats)\n"
        "• Security (scan/encrypt/resume)\n"
        "• File management (delete/extract/categorize)\n\n"
        "Pilih menu help di bawah untuk detail lebih lanjut."
    )
    
    await update.callback_query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    return MAIN_MENU
