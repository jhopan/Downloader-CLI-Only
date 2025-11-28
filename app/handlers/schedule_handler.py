from telegram import Update
from telegram.ext import ContextTypes
from app.handlers.common import is_admin, show_main_menu, get_download_path, delete_user_message
from app.handlers.states import MAIN_MENU, WAITING_SCHEDULE_LINK, WAITING_SCHEDULE_TIME
from app.keyboards.inline_keyboards import back_button_keyboard, back_to_main_keyboard
from utils.validators import validate_url
import logging

logger = logging.getLogger(__name__)


async def scheduled_download_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show menu untuk unduh berjadwal"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    reply_markup = back_button_keyboard()
    
    await query.edit_message_text(
        "⏰ <b>Unduh Berjadwal</b>\n\n"
        "Silakan kirim link file yang ingin dijadwalkan.",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    return WAITING_SCHEDULE_LINK


async def handle_schedule_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle link untuk unduh berjadwal"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    url = update.message.text.strip()
    
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
        return WAITING_SCHEDULE_LINK
    
    # Simpan URL dan minta waktu
    context.user_data['schedule_url'] = url
    
    reply_markup = back_button_keyboard()
    
    if 'main_message_id' in context.user_data:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=context.user_data['main_message_id'],
            text="⏰ <b>Jadwalkan Unduhan</b>\n\n"
                 "Link valid! ✅\n\n"
                 "Silakan masukkan waktu untuk memulai unduhan.\n\n"
                 "<b>Format:</b>\n"
                 "• <code>DD/MM/YYYY HH:MM</code>\n"
                 "  Contoh: <code>28/11/2025 14:30</code>\n\n"
                 "• <code>1h</code> = 1 jam dari sekarang\n"
                 "• <code>30m</code> = 30 menit dari sekarang\n"
                 "• <code>2d</code> = 2 hari dari sekarang",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    await delete_user_message(update)
    return WAITING_SCHEDULE_TIME


async def handle_schedule_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle waktu untuk jadwal unduhan"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    time_input = update.message.text.strip()
    url = context.user_data.get('schedule_url')
    
    if not url:
        return await show_main_menu(update, context)
    
    # Parse waktu
    scheduler_manager = context.bot_data['scheduler_manager']
    scheduled_time = scheduler_manager.parse_time_input(time_input)
    
    if not scheduled_time:
        reply_markup = back_button_keyboard()
        
        if 'main_message_id' in context.user_data:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=context.user_data['main_message_id'],
                text="❌ <b>Format Waktu Tidak Valid</b>\n\n"
                     "Silakan coba lagi dengan format yang benar:\n\n"
                     "• <code>DD/MM/YYYY HH:MM</code>\n"
                     "• <code>1h</code>, <code>30m</code>, <code>2d</code>",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        
        await delete_user_message(update)
        return WAITING_SCHEDULE_TIME
    
    # Dapatkan download path untuk user
    db_manager = context.bot_data.get('db_manager')
    download_path = get_download_path(context, user_id, db_manager)
    
    # Tambahkan ke scheduler
    try:
        schedule_id = scheduler_manager.add_schedule(url, scheduled_time, download_path, user_id)
        
        reply_markup = back_to_main_keyboard()
        
        if 'main_message_id' in context.user_data:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=context.user_data['main_message_id'],
                text=f"✅ <b>Unduhan Dijadwalkan!</b>\n\n"
                     f"Link: {url[:60]}...\n"
                     f"Waktu: <code>{scheduled_time.strftime('%d/%m/%Y %H:%M')}</code>\n"
                     f"ID Jadwal: <code>{schedule_id}</code>\n"
                     f"Lokasi: <code>{download_path}</code>\n\n"
                     f"Unduhan akan dimulai secara otomatis pada waktu yang ditentukan.",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        
        await delete_user_message(update)
        del context.user_data['schedule_url']
        logger.info(f"User {user_id} scheduled download: {url} at {scheduled_time}")
        return MAIN_MENU
        
    except Exception as e:
        logger.error(f"Error scheduling download: {e}")
        
        reply_markup = back_button_keyboard()
        
        if 'main_message_id' in context.user_data:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=context.user_data['main_message_id'],
                text=f"❌ <b>Error</b>\n\n"
                     f"Gagal menjadwalkan unduhan: {str(e)}",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        
        await delete_user_message(update)
        return MAIN_MENU
