from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from app.handlers.common import is_admin
from app.handlers.menu_handler import show_main_menu
from app.handlers.states import MAIN_MENU
from app.keyboards.reply_keyboards import main_menu_keyboard
import logging

logger = logging.getLogger(__name__)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /start"""
    user = update.effective_user
    user_id = user.id
    user_name = user.first_name or user.username or f"User-{user_id}"
    
    logger.info(f"📱 /start - {user_name} (ID: {user_id})")
    
    if not is_admin(user_id):
        logger.warning(f"🚫 Akses ditolak - {user_name} (ID: {user_id})")
        await update.message.reply_text("⛔ Maaf, Anda tidak memiliki akses ke bot ini.")
        return ConversationHandler.END
    
    logger.info(f"✅ Menu utama ditampilkan untuk {user_name}")
    # Use inline keyboard menu instead
    return await show_main_menu(update, context, edit_message=False)


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /cancel"""
    await update.message.reply_text("✅ Operasi dibatalkan.")
    return ConversationHandler.END
