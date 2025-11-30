"""
Menu wrapper functions untuk security handler
Converts commands to inline keyboard menus
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.handlers.states import MAIN_MENU
import logging

logger = logging.getLogger(__name__)


async def virus_scan_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Virus scan menu"""
    keyboard = [
        [InlineKeyboardButton("📁 Select File to Scan", callback_data="action_select_scan_file")],
        [
            InlineKeyboardButton("🔧 ClamAV Scan", callback_data="action_scan_clamav"),
            InlineKeyboardButton("🌐 VirusTotal Scan", callback_data="action_scan_virustotal")
        ],
        [InlineKeyboardButton("◀️ Back", callback_data="menu_security")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "🛡️ <b>Virus Scanning</b>\n\n"
        "<b>Available Scanners:</b>\n\n"
        "🔧 <b>ClamAV</b> - Local scanner (fast)\n"
        "   • Open-source antivirus\n"
        "   • No API key needed\n"
        "   • Offline scanning\n\n"
        "🌐 <b>VirusTotal</b> - Online scan (70+ engines)\n"
        "   • Multiple antivirus engines\n"
        "   • Cloud-based detection\n"
        "   • Requires API key\n\n"
        "Pilih file untuk scan."
    )
    
    await update.callback_query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    return MAIN_MENU


async def encrypt_file_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Encrypt file menu"""
    keyboard = [
        [InlineKeyboardButton("📁 Select File to Encrypt", callback_data="action_select_encrypt_file")],
        [
            InlineKeyboardButton("🔐 Auto Password", callback_data="action_encrypt_auto"),
            InlineKeyboardButton("🔑 Custom Password", callback_data="action_encrypt_custom")
        ],
        [InlineKeyboardButton("◀️ Back", callback_data="menu_security")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "🔐 <b>File Encryption</b>\n\n"
        "<b>Encryption Details:</b>\n"
        "• Algorithm: AES-256-GCM\n"
        "• Key Derivation: PBKDF2 (100,000 iterations)\n"
        "• Authenticated encryption (tamper-proof)\n"
        "• Military-grade security\n\n"
        "<b>Options:</b>\n"
        "• <b>Auto Password</b> - Generate secure password\n"
        "• <b>Custom Password</b> - Use your own password\n\n"
        "Pilih file dan metode enkripsi."
    )
    
    await update.callback_query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    return MAIN_MENU


async def decrypt_file_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Decrypt file menu"""
    keyboard = [
        [InlineKeyboardButton("🔓 Select .enc File", callback_data="action_select_decrypt_file")],
        [InlineKeyboardButton("📋 List Encrypted Files", callback_data="security_encrypted_files")],
        [InlineKeyboardButton("◀️ Back", callback_data="menu_security")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "🔓 <b>File Decryption</b>\n\n"
        "Decrypt file yang telah dienkripsi.\n\n"
        "<b>Requirements:</b>\n"
        "• File dengan extension .enc\n"
        "• Password yang benar\n\n"
        "<b>Note:</b>\n"
        "Password tidak disimpan di database.\n"
        "Pastikan Anda ingat password yang digunakan!\n\n"
        "Pilih file .enc untuk decrypt."
    )
    
    await update.callback_query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    return MAIN_MENU


async def scan_history_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Scan history menu"""
    try:
        db_manager = context.bot_data.get('db_manager')
        user_id = update.effective_user.id
        
        # Get scan history
        history = db_manager.get_scan_history(user_id, limit=10)
        
        if not history:
            text = "📜 <b>Scan History</b>\n\n❌ Tidak ada riwayat scan."
        else:
            text = "📜 <b>Scan History</b>\n\n"
            for scan in history:
                status_emoji = "✅" if scan['status'] == 'clean' else "⚠️" if scan['status'] == 'suspicious' else "🦠"
                text += f"{status_emoji} <b>{scan['filename']}</b>\n"
                text += f"   Scanner: {scan['scanner']}\n"
                text += f"   Status: {scan['status']}\n"
                text += f"   Date: {scan['scan_date']}\n\n"
        
        keyboard = [[InlineKeyboardButton("◀️ Back", callback_data="menu_security")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error in scan_history_menu: {e}")
        keyboard = [[InlineKeyboardButton("◀️ Back", callback_data="menu_security")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(
            text="❌ Error loading scan history",
            reply_markup=reply_markup
        )
    
    return MAIN_MENU


async def encrypted_files_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Encrypted files list menu"""
    try:
        db_manager = context.bot_data.get('db_manager')
        user_id = update.effective_user.id
        
        # Get encrypted files
        encrypted_files = db_manager.get_encrypted_files(user_id)
        
        if not encrypted_files:
            text = "🔒 <b>Encrypted Files</b>\n\n❌ Tidak ada file terenkripsi."
        else:
            text = "🔒 <b>Encrypted Files</b>\n\n"
            for file in encrypted_files:
                text += f"🔐 <b>{file['filename']}</b>\n"
                text += f"   Original: {file['original_filename']}\n"
                text += f"   Size: {file['file_size']} bytes\n"
                text += f"   Date: {file['encrypted_date']}\n\n"
        
        keyboard = [[InlineKeyboardButton("◀️ Back", callback_data="menu_security")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error in encrypted_files_menu: {e}")
        keyboard = [[InlineKeyboardButton("◀️ Back", callback_data="menu_security")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(
            text="❌ Error loading encrypted files",
            reply_markup=reply_markup
        )
    
    return MAIN_MENU


async def resume_download_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Resume download menu"""
    try:
        # Get incomplete downloads from download state
        from src.managers.resume_downloader import DownloadState
        download_state = DownloadState()
        
        incomplete = download_state.get_all_incomplete_downloads()
        
        if not incomplete:
            text = "🔄 <b>Resume Downloads</b>\n\n✅ Tidak ada download yang terputus."
            keyboard = [[InlineKeyboardButton("◀️ Back", callback_data="menu_security")]]
        else:
            text = "🔄 <b>Resume Downloads</b>\n\n"
            text += f"Found {len(incomplete)} incomplete download(s):\n\n"
            
            keyboard = []
            for i, (state_file, state_data) in enumerate(incomplete[:10], 1):  # Max 10
                url = state_data.get('url', 'Unknown')[:40]
                downloaded = state_data.get('downloaded', 0)
                total = state_data.get('total_size', 0)
                percent = (downloaded / total * 100) if total > 0 else 0
                
                text += f"{i}. <b>{state_data.get('filename', 'Unknown')}</b>\n"
                text += f"   Progress: {percent:.1f}% ({downloaded:,} / {total:,} bytes)\n"
                text += f"   URL: {url}...\n\n"
                
                keyboard.append([
                    InlineKeyboardButton(
                        f"▶️ Resume #{i}",
                        callback_data=f"action_resume_{i}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("◀️ Back", callback_data="menu_security")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error in resume_download_menu: {e}")
        keyboard = [[InlineKeyboardButton("◀️ Back", callback_data="menu_security")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(
            text=f"❌ Error loading incomplete downloads: {str(e)}",
            reply_markup=reply_markup
        )
    
    return MAIN_MENU
