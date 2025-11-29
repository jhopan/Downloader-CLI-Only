from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.handlers.common import is_admin, show_main_menu, get_download_path, delete_user_message
from app.handlers.states import MAIN_MENU, WAITING_LINK
from app.keyboards.inline_keyboards import back_button_keyboard, back_to_main_keyboard
from utils.validators import validate_url
from utils.link_validator import LinkValidator
import logging

logger = logging.getLogger(__name__)


def format_size(bytes_size):
    """Format bytes ke human readable"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.2f} TB"


def progress_bar(percent):
    """Generate progress bar"""
    filled = int(percent / 10)
    empty = 10 - filled
    return '█' * filled + '░' * empty


async def direct_download_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show menu untuk unduh langsung"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    reply_markup = back_button_keyboard()
    
    await query.edit_message_text(
        "📥 <b>Unduh Langsung</b>\n\n"
        "Silakan kirim link file yang ingin diunduh.\n"
        "Bot akan memvalidasi link terlebih dahulu.\n\n"
        "Contoh:\n"
        "• https://example.com/file.zip\n"
        "• https://drive.google.com/...\n"
        "• https://mega.nz/...",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    return WAITING_LINK


async def handle_direct_download_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle link untuk unduh langsung"""
    user = update.effective_user
    user_id = user.id
    user_name = user.first_name or user.username or f"User-{user_id}"
    
    if not is_admin(user_id):
        return ConversationHandler.END
    
    url = update.message.text.strip()
    logger.info(f"📥 Request download dari {user_name}: {url[:50]}...")
    
    # Validasi URL format
    is_valid, message = validate_url(url)
    
    if not is_valid:
        reply_markup = back_button_keyboard()
        
        if 'main_message_id' in context.user_data:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=context.user_data['main_message_id'],
                text=f"❌ <b>Link Tidak Valid</b>\n\n{message}\n\n"
                     f"Silakan kirim link yang valid atau klik tombol di bawah:",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        
        await delete_user_message(update)
        return WAITING_LINK
    
    # Validasi apakah link bisa didownload
    await update.message.reply_text("🔍 Memvalidasi link... Mohon tunggu.")
    
    validator = LinkValidator()
    is_downloadable, error_msg, file_info = await validator.validate_link(url)
    
    if not is_downloadable:
        # Link tidak bisa didownload
        keyboard = [
            [InlineKeyboardButton("🔄 Ganti Link", callback_data="direct_download")],
            [InlineKeyboardButton("❌ Batal", callback_data="back_to_main")]
        ]
        
        if 'main_message_id' in context.user_data:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=context.user_data['main_message_id'],
                text=f"⚠️ <b>Link Tidak Dapat Diunduh</b>\n\n"
                     f"URL: <code>{url[:60]}...</code>\n"
                     f"Error: <code>{error_msg}</code>\n\n"
                     f"Link ini tidak dapat diakses atau diunduh.\n"
                     f"Apakah Anda ingin mengganti link atau membatalkan?",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
        
        await delete_user_message(update)
        return MAIN_MENU
    
    # Link valid dan bisa didownload
    file_size_str = validator.format_size(file_info['size']) if file_info['size'] > 0 else 'Unknown'
    
    await update.message.reply_text(
        f"✅ <b>Link Valid!</b>\n\n"
        f"📄 File: <code>{file_info['filename']}</code>\n"
        f"📦 Ukuran: <code>{file_size_str}</code>\n"
        f"📋 Type: <code>{file_info['type']}</code>\n\n"
        f"Memulai download...",
        parse_mode='HTML'
    )
    
    # Dapatkan download path untuk user
    download_manager = context.bot_data['download_manager']
    db_manager = context.bot_data.get('db_manager')
    download_path = get_download_path(context, user_id, db_manager)
    
    # Progress callback untuk update Telegram
    last_update_progress = [0]  # Mutable untuk track last update
    progress_message_id = [None]
    
    async def progress_callback(download_id, progress, downloaded, total, speed, completed=False):
        """Callback untuk update progress di Telegram"""
        nonlocal last_update_progress, progress_message_id
        
        # Update setiap 20% atau completed
        if completed or int(progress) - last_update_progress[0] >= 20:
            last_update_progress[0] = int(progress)
            
            if completed:
                # Download selesai
                text = (
                    f"✅ <b>Download Selesai!</b>\n\n"
                    f"File: <code>{url.split('/')[-1]}</code>\n"
                    f"Ukuran: <code>{format_size(downloaded)}</code>\n"
                    f"Lokasi: <code>{download_path}</code>\n"
                    f"ID: <code>{download_id}</code>"
                )
                logger.info(f"🎉 {user_name} selesai download: {download_id}")
            else:
                # Progress update
                bar = progress_bar(progress)
                text = (
                    f"📥 <b>Sedang Mengunduh...</b>\n\n"
                    f"{bar} {progress:.1f}%\n\n"
                    f"Downloaded: <code>{format_size(downloaded)}</code> / <code>{format_size(total)}</code>\n"
                    f"Speed: <code>{format_size(speed)}/s</code>\n"
                    f"ID: <code>{download_id}</code>"
                )
            
            try:
                if progress_message_id[0]:
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=progress_message_id[0],
                        text=text,
                        parse_mode='HTML'
                    )
                else:
                    msg = await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=text,
                        parse_mode='HTML'
                    )
                    progress_message_id[0] = msg.message_id
            except Exception as e:
                logger.error(f"Progress update error: {e}")
    
    # URL valid, mulai download dengan progress callback
    try:
        download_id = await download_manager.start_download(
            url, download_path, user_id, progress_callback=progress_callback
        )
        
        reply_markup = back_to_main_keyboard()
        
        if 'main_message_id' in context.user_data:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=context.user_data['main_message_id'],
                text=f"✅ <b>Unduhan Dimulai!</b>\n\n"
                     f"Link: {url[:60]}...\n"
                     f"ID: <code>{download_id}</code>\n\n"
                     f"Progress akan ditampilkan di bawah.",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        
        await delete_user_message(update)
        logger.info(f"✅ {user_name} memulai download (ID: {download_id})")
        return MAIN_MENU
        
    except Exception as e:
        logger.error(f"❌ Error download untuk {user_name}: {e}")
        
        reply_markup = back_button_keyboard()
        
        if 'main_message_id' in context.user_data:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=context.user_data['main_message_id'],
                text=f"❌ <b>Error</b>\n\n"
                     f"Gagal memulai unduhan: {str(e)}",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        
        await delete_user_message(update)
        return MAIN_MENU
