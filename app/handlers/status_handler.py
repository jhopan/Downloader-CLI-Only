from telegram import Update
from telegram.ext import ContextTypes
from app.handlers.common import is_admin, show_main_menu
from app.handlers.states import MAIN_MENU
from app.keyboards.inline_keyboards import (
    cancel_download_keyboard, cancel_schedule_keyboard,
    refresh_and_back_keyboard
)
import logging

logger = logging.getLogger(__name__)


async def download_status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show status unduhan"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    download_manager = context.bot_data['download_manager']
    status_text = download_manager.get_status_text()
    
    reply_markup = refresh_and_back_keyboard("download_status")
    
    await query.edit_message_text(
        status_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    return MAIN_MENU


async def view_schedules_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show jadwal unduhan"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    scheduler_manager = context.bot_data['scheduler_manager']
    schedules_text = scheduler_manager.get_schedules_text(user_id)
    
    reply_markup = refresh_and_back_keyboard("view_schedules")
    
    await query.edit_message_text(
        schedules_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    return MAIN_MENU


async def cancel_download_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show menu untuk cancel download"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    download_manager = context.bot_data['download_manager']
    active_downloads = download_manager.get_active_downloads()
    
    if not active_downloads:
        await query.answer("ℹ️ Tidak ada unduhan aktif", show_alert=True)
        return await show_main_menu(update, context)
    
    reply_markup = cancel_download_keyboard(active_downloads)
    
    await query.edit_message_text(
        "❌ <b>Batalkan Unduhan</b>\n\n"
        "Pilih unduhan yang ingin dibatalkan:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    return MAIN_MENU


async def cancel_download_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE, download_id: str):
    """Confirm cancel download"""
    query = update.callback_query
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    download_manager = context.bot_data['download_manager']
    success = download_manager.cancel_download(download_id)
    
    if success:
        await query.answer("✅ Unduhan berhasil dibatalkan!", show_alert=True)
        logger.info(f"User {user_id} cancelled download {download_id}")
    else:
        await query.answer("❌ Gagal membatalkan unduhan", show_alert=True)
    
    return await show_main_menu(update, context)


async def cancel_schedule_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE, schedule_id: str):
    """Confirm cancel schedule"""
    query = update.callback_query
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    scheduler_manager = context.bot_data['scheduler_manager']
    success = scheduler_manager.cancel_schedule(schedule_id)
    
    if success:
        await query.answer("✅ Jadwal berhasil dibatalkan!", show_alert=True)
        logger.info(f"User {user_id} cancelled schedule {schedule_id}")
    else:
        await query.answer("❌ Gagal membatalkan jadwal", show_alert=True)
    
    return await show_main_menu(update, context)
