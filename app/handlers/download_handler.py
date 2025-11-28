from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from app.handlers.common import is_admin, show_main_menu, get_download_path, delete_user_message
from app.handlers.states import MAIN_MENU, WAITING_LINK
from app.keyboards.inline_keyboards import back_button_keyboard, back_to_main_keyboard
from utils.validators import validate_url
import logging

logger = logging.getLogger(__name__)


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
    
    # Validasi URL
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
    
    # Dapatkan download path untuk user
    download_manager = context.bot_data['download_manager']
    db_manager = context.bot_data.get('db_manager')
    download_path = get_download_path(context, user_id, db_manager)
    
    # URL valid, mulai download
    try:
        download_id = await download_manager.start_download(url, download_path, user_id)
        
        reply_markup = back_to_main_keyboard()
        
        if 'main_message_id' in context.user_data:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=context.user_data['main_message_id'],
                text=f"✅ <b>Unduhan Dimulai!</b>\n\n"
                     f"Link: {url[:60]}...\n"
                     f"ID: <code>{download_id}</code>\n"
                     f"Lokasi: <code>{download_path}</code>\n\n"
                     f"File akan diunduh secara otomatis.\n"
                     f"Gunakan menu Status Unduhan untuk melihat progress.",
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
