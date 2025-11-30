"""
Security & Resume Features Handler
Handler untuk virus scanning, encryption, dan resume downloads
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import os
import logging

logger = logging.getLogger(__name__)

# Conversation states
AWAITING_ENCRYPT_FILE = 1
AWAITING_DECRYPT_FILE = 2
AWAITING_DECRYPT_PASSWORD = 3
AWAITING_SCAN_FILE = 4


async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Scan file untuk virus"""
    user_id = update.effective_user.id
    
    try:
        db_manager = context.bot_data.get('db_manager')
        
        if not db_manager:
            await update.message.reply_text("❌ Service tidak tersedia")
            return
        
        # Get recent downloads
        history = db_manager.get_download_history(user_id, limit=10)
        
        if not history:
            await update.message.reply_text("📁 Belum ada file untuk scan")
            return
        
        # Create buttons untuk select file
        keyboard = []
        for item in history[:5]:
            filename = item['filename']
            if len(filename) > 40:
                filename = filename[:37] + "..."
            
            keyboard.append([
                InlineKeyboardButton(
                    f"🛡️ {filename}", 
                    callback_data=f"scan_{item['download_id']}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("ℹ️ Scan Info", callback_data="scan_info")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🛡️ **Virus Scanning**\n\n"
            "Select file to scan for viruses:\n\n"
            "**Scanners:**\n"
            "• ClamAV (local, fast)\n"
            "• VirusTotal (online, comprehensive)",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    except Exception as e:
        logger.error(f"Error in scan_command: {e}")
        await update.message.reply_text(f"❌ Error: {e}")


async def encrypt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Encrypt file"""
    user_id = update.effective_user.id
    
    try:
        db_manager = context.bot_data.get('db_manager')
        
        if not db_manager:
            await update.message.reply_text("❌ Service tidak tersedia")
            return
        
        # Get recent downloads
        history = db_manager.get_download_history(user_id, limit=10)
        
        if not history:
            await update.message.reply_text("📁 Belum ada file untuk encrypt")
            return
        
        # Create buttons
        keyboard = []
        for item in history[:5]:
            filename = item['filename']
            if len(filename) > 40:
                filename = filename[:37] + "..."
            
            keyboard.append([
                InlineKeyboardButton(
                    f"🔒 {filename}", 
                    callback_data=f"encrypt_{item['download_id']}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("ℹ️ Encryption Info", callback_data="encrypt_info")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🔒 **File Encryption**\n\n"
            "Select file to encrypt with AES-256:\n\n"
            "• Auto-generated secure password\n"
            "• Password will be sent to you\n"
            "• Original file will be kept",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    except Exception as e:
        logger.error(f"Error in encrypt_command: {e}")
        await update.message.reply_text(f"❌ Error: {e}")


async def decrypt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Decrypt file"""
    await update.message.reply_text(
        "🔓 **File Decryption**\n\n"
        "Send me:\n"
        "1. Encrypted file (.enc)\n"
        "2. Password\n\n"
        "I'll decrypt it for you.",
        parse_mode='Markdown'
    )


async def resume_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show resumable downloads"""
    try:
        download_state = context.bot_data.get('download_state')
        
        if not download_state:
            await update.message.reply_text("❌ Resume service tidak tersedia")
            return
        
        # Get incomplete downloads
        incomplete = download_state.get_all_incomplete_downloads()
        
        if not incomplete:
            await update.message.reply_text(
                "✅ **No Incomplete Downloads**\n\n"
                "All downloads completed successfully!",
                parse_mode='Markdown'
            )
            return
        
        text = "🔄 **Resumable Downloads**\n\n"
        text += f"Found {len(incomplete)} incomplete download(s):\n\n"
        
        keyboard = []
        
        for i, state in enumerate(incomplete[:10], 1):
            filename = os.path.basename(state['filepath'])
            if len(filename) > 30:
                filename = filename[:27] + "..."
            
            progress = (state['downloaded_bytes'] / state['total_bytes'] * 100) if state['total_bytes'] > 0 else 0
            
            text += f"{i}. **{filename}**\n"
            text += f"   Progress: {progress:.1f}% ({state['downloaded_bytes']}/{state['total_bytes']} bytes)\n\n"
            
            keyboard.append([
                InlineKeyboardButton(
                    f"▶️ Resume {filename}", 
                    callback_data=f"resume_{state['download_id']}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🗑️ Clear All", callback_data="resume_clear_all")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    except Exception as e:
        logger.error(f"Error in resume_command: {e}")
        await update.message.reply_text(f"❌ Error: {e}")


async def security_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks untuk security features"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    try:
        # Scan callbacks
        if data.startswith("scan_"):
            if data == "scan_info":
                text = "🛡️ **Virus Scanning Info**\n\n"
                text += "**ClamAV:**\n"
                text += "• Local scanner\n"
                text += "• Fast scanning\n"
                text += "• Requires ClamAV installation\n\n"
                text += "**VirusTotal:**\n"
                text += "• Online scanner\n"
                text += "• 70+ antivirus engines\n"
                text += "• Requires API key\n"
                text += "• Max 32MB files (free tier)\n\n"
                text += "**Infected files will be quarantined automatically.**"
                
                await query.edit_message_text(text, parse_mode='Markdown')
            else:
                download_id = data.split("_")[1]
                db_manager = context.bot_data.get('db_manager')
                virus_scanner = context.bot_data.get('virus_scanner')
                
                if not virus_scanner:
                    await query.edit_message_text("❌ Virus scanner tidak tersedia")
                    return
                
                # Get file info
                history = db_manager.get_download_history(user_id, limit=100)
                file_info = next((h for h in history if h['download_id'] == download_id), None)
                
                if not file_info or not os.path.exists(file_info['filepath']):
                    await query.edit_message_text("❌ File tidak ditemukan")
                    return
                
                filepath = file_info['filepath']
                
                await query.edit_message_text(f"🔍 Scanning {file_info['filename']}...\n\nThis may take a few moments...")
                
                # Scan file
                scan_result = await virus_scanner.scan_file(filepath, use_virustotal=True)
                
                # Format result
                result_text = virus_scanner.format_scan_result(scan_result)
                
                # Quarantine if infected
                if scan_result['infected']:
                    quarantine_success = virus_scanner.quarantine_file(filepath)
                    if quarantine_success:
                        result_text += "\n\n🔒 File moved to quarantine folder."
                
                await query.edit_message_text(result_text, parse_mode='Markdown')
        
        # Encrypt callbacks
        elif data.startswith("encrypt_"):
            if data == "encrypt_info":
                text = "🔒 **Encryption Info**\n\n"
                text += "**Algorithm:** AES-256-GCM\n"
                text += "**Key Derivation:** PBKDF2-SHA256 (100,000 iterations)\n"
                text += "**Password:** Auto-generated (16 characters)\n"
                text += "**Output:** filename.ext.enc\n\n"
                text += "**Features:**\n"
                text += "• Authenticated encryption (prevents tampering)\n"
                text += "• Random salt per file\n"
                text += "• Secure password generation\n\n"
                text += "**Keep your password safe!**"
                
                await query.edit_message_text(text, parse_mode='Markdown')
            else:
                download_id = data.split("_")[1]
                db_manager = context.bot_data.get('db_manager')
                file_encryption = context.bot_data.get('file_encryption')
                
                if not file_encryption:
                    await query.edit_message_text("❌ Encryption service tidak tersedia")
                    return
                
                # Get file info
                history = db_manager.get_download_history(user_id, limit=100)
                file_info = next((h for h in history if h['download_id'] == download_id), None)
                
                if not file_info or not os.path.exists(file_info['filepath']):
                    await query.edit_message_text("❌ File tidak ditemukan")
                    return
                
                filepath = file_info['filepath']
                
                await query.edit_message_text(f"🔒 Encrypting {file_info['filename']}...\n\nPlease wait...")
                
                # Encrypt file
                success, message, password = file_encryption.encrypt_file(filepath)
                
                if success:
                    text = "✅ **File Encrypted Successfully!**\n\n"
                    text += f"📄 **File:** {os.path.basename(filepath)}.enc\n"
                    text += f"🔑 **Password:** `{password}`\n\n"
                    text += "⚠️ **IMPORTANT:**\n"
                    text += "• Save this password securely!\n"
                    text += "• Without it, file cannot be decrypted!\n"
                    text += "• Password is shown only once!\n\n"
                    text += f"ℹ️ Original file kept: {os.path.basename(filepath)}"
                    
                    await query.edit_message_text(text, parse_mode='Markdown')
                else:
                    await query.edit_message_text(f"❌ Encryption failed: {message}")
        
        # Resume callbacks
        elif data.startswith("resume_"):
            if data == "resume_clear_all":
                download_state = context.bot_data.get('download_state')
                
                # Confirm first
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Yes, Clear All", callback_data="resume_clear_confirmed"),
                        InlineKeyboardButton("❌ Cancel", callback_data="resume_cancel"),
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    "⚠️ **Clear All Incomplete Downloads?**\n\n"
                    "This will remove all download states.\n"
                    "Partial files will remain on disk.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            
            elif data == "resume_clear_confirmed":
                download_state = context.bot_data.get('download_state')
                
                incomplete = download_state.get_all_incomplete_downloads()
                for state in incomplete:
                    download_state.clear_state(state['download_id'])
                
                await query.edit_message_text(
                    f"✅ Cleared {len(incomplete)} incomplete download(s)."
                )
            
            elif data == "resume_cancel":
                await query.edit_message_text("❌ Cancelled")
            
            else:
                download_id = data.split("_")[1]
                download_state = context.bot_data.get('download_state')
                resume_downloader = context.bot_data.get('resume_downloader')
                
                if not resume_downloader:
                    await query.edit_message_text("❌ Resume service tidak tersedia")
                    return
                
                # Load state
                state = download_state.load_state(download_id)
                
                if not state:
                    await query.edit_message_text("❌ Download state tidak ditemukan")
                    return
                
                filename = os.path.basename(state['filepath'])
                await query.edit_message_text(
                    f"▶️ **Resuming Download**\n\n"
                    f"📄 {filename}\n"
                    f"📊 From: {state['downloaded_bytes']} bytes\n\n"
                    f"Please wait...",
                    parse_mode='Markdown'
                )
                
                # Resume download
                success = await resume_downloader.download_with_resume(
                    download_id, state['url'], state['filepath']
                )
                
                if success:
                    await query.edit_message_text(
                        f"✅ **Download Resumed & Completed!**\n\n"
                        f"📄 {filename}\n"
                        f"📦 Size: {state['total_bytes']} bytes",
                        parse_mode='Markdown'
                    )
                else:
                    await query.edit_message_text(
                        f"❌ **Resume Failed**\n\n"
                        f"Download interrupted again. You can try resuming later.",
                        parse_mode='Markdown'
                    )
    
    except Exception as e:
        logger.error(f"Error in security_button_callback: {e}")
        await query.edit_message_text(f"❌ Error: {e}")


# Handler functions
def get_security_handlers():
    """Get all handlers untuk security features"""
    return [
        CommandHandler('scan', scan_command),
        CommandHandler('encrypt', encrypt_command),
        CommandHandler('decrypt', decrypt_command),
        CommandHandler('resume', resume_command),
        CallbackQueryHandler(security_button_callback, pattern="^(scan_|encrypt_|resume_)")
    ]
