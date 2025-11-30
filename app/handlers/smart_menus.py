"""
Menu wrapper functions untuk smart features handler
Converts commands to inline keyboard menus
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.handlers.states import MAIN_MENU
import logging

logger = logging.getLogger(__name__)


async def queue_management_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Queue management menu with inline keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("📊 View Queue Status", callback_data="action_view_queue"),
            InlineKeyboardButton("⏸️ Pause Item", callback_data="action_pause_queue")
        ],
        [
            InlineKeyboardButton("▶️ Resume Item", callback_data="action_resume_queue"),
            InlineKeyboardButton("🔼 Change Priority", callback_data="action_priority_queue")
        ],
        [
            InlineKeyboardButton("🗑️ Remove from Queue", callback_data="action_remove_queue")
        ],
        [InlineKeyboardButton("◀️ Back", callback_data="menu_smart")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "📋 <b>Queue Management</b>\n\n"
        "Kelola download queue:\n\n"
        "📊 <b>View Queue Status</b> - Lihat status antrian\n"
        "⏸️ <b>Pause Item</b> - Pause download item\n"
        "▶️ <b>Resume Item</b> - Resume download item\n"
        "🔼 <b>Change Priority</b> - Ubah prioritas item\n"
        "🗑️ <b>Remove from Queue</b> - Hapus dari antrian"
    )
    
    await update.callback_query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    return MAIN_MENU


async def queue_status_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show queue status inline"""
    from app.handlers.smart_features_handler import queue_command
    # Call existing queue command but adapt for callback query
    update.message = update.callback_query.message
    await queue_command(update, context)
    return MAIN_MENU


async def file_preview_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """File preview menu"""
    keyboard = [
        [InlineKeyboardButton("📁 Select File to Preview", callback_data="action_select_preview_file")],
        [InlineKeyboardButton("◀️ Back", callback_data="menu_smart")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "👁️ <b>File Preview</b>\n\n"
        "Preview file dengan metadata:\n\n"
        "• <b>Images</b>: Dimensions, EXIF, format\n"
        "• <b>Videos</b>: Duration, resolution, codec\n"
        "• <b>Audio</b>: Title, artist, bitrate\n"
        "• <b>Documents</b>: Pages, size, format\n\n"
        "Klik tombol di bawah untuk memilih file."
    )
    
    await update.callback_query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    return MAIN_MENU


async def duplicate_check_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Duplicate check menu"""
    keyboard = [
        [InlineKeyboardButton("🔍 Run Duplicate Scan", callback_data="action_run_duplicate_scan")],
        [InlineKeyboardButton("📋 View Duplicates", callback_data="action_view_duplicates")],
        [InlineKeyboardButton("◀️ Back", callback_data="menu_smart")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "🔍 <b>Duplicate Detection</b>\n\n"
        "Deteksi file duplikat berdasarkan:\n\n"
        "• <b>MD5/SHA256 Hash</b> - Hash-based detection\n"
        "• <b>File Size</b> - Size matching\n"
        "• <b>Filename</b> - Filename similarity\n\n"
        "Jalankan scan untuk menemukan file duplikat."
    )
    
    await update.callback_query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    return MAIN_MENU


async def smart_categorize_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Smart categorization menu"""
    keyboard = [
        [
            InlineKeyboardButton("🤖 Auto-Categorize Now", callback_data="action_auto_categorize"),
            InlineKeyboardButton("📝 View Rules", callback_data="action_view_cat_rules")
        ],
        [
            InlineKeyboardButton("➕ Add Rule", callback_data="action_add_cat_rule"),
            InlineKeyboardButton("📊 Categories Stats", callback_data="action_cat_stats")
        ],
        [InlineKeyboardButton("◀️ Back", callback_data="menu_smart")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "🤖 <b>Smart Auto-Categorization</b>\n\n"
        "<b>8 Categories:</b>\n"
        "• Video, Audio, Image, Document\n"
        "• Archive, Code, Ebook, Software\n\n"
        "<b>Features:</b>\n"
        "• Pattern-based learning\n"
        "• Confidence scoring\n"
        "• User action learning\n"
        "• Custom rules support"
    )
    
    await update.callback_query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    return MAIN_MENU


async def cloud_manager_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cloud storage manager menu"""
    keyboard = [
        [
            InlineKeyboardButton("🔗 Google Drive", callback_data="cloud_setup_gdrive"),
            InlineKeyboardButton("📦 Dropbox", callback_data="cloud_setup_dropbox")
        ],
        [
            InlineKeyboardButton("☁️ OneDrive", callback_data="cloud_setup_onedrive"),
            InlineKeyboardButton("📋 View Tokens", callback_data="cloud_view_tokens")
        ],
        [InlineKeyboardButton("◀️ Back", callback_data="menu_smart")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "☁️ <b>Cloud Storage Manager</b>\n\n"
        "Manage OAuth tokens untuk:\n\n"
        "• <b>Google Drive</b> - OAuth 2.0 authentication\n"
        "• <b>Dropbox</b> - App token authentication\n"
        "• <b>OneDrive</b> - Microsoft OAuth 2.0\n\n"
        "Setup atau view existing tokens."
    )
    
    await update.callback_query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    return MAIN_MENU


async def cloud_download_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cloud download menu"""
    keyboard = [
        [InlineKeyboardButton("📤 Send Cloud Link", callback_data="action_send_cloud_link")],
        [
            InlineKeyboardButton("⚙️ Manage Tokens", callback_data="cloud_manager_menu"),
            InlineKeyboardButton("ℹ️ Help", callback_data="help_cloud_download")
        ],
        [InlineKeyboardButton("◀️ Back", callback_data="menu_download")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "☁️ <b>Cloud Storage Download</b>\n\n"
        "<b>Supported Services:</b>\n"
        "• Google Drive (drive.google.com)\n"
        "• Dropbox (dropbox.com)\n"
        "• OneDrive (onedrive.live.com)\n\n"
        "<b>How to use:</b>\n"
        "1. Click 'Send Cloud Link'\n"
        "2. Send link dari cloud storage\n"
        "3. Bot akan auto-detect service\n"
        "4. Download dimulai otomatis\n\n"
        "Klik tombol di bawah untuk mulai."
    )
    
    await update.callback_query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    return MAIN_MENU


async def statistics_dashboard_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Statistics dashboard menu"""
    from app.handlers.smart_features_handler import stats_command
    # Call existing stats command but adapt for callback query
    update.message = update.callback_query.message
    await stats_command(update, context)
    return MAIN_MENU
