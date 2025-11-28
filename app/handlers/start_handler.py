from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from app.handlers.common import is_admin, show_main_menu
from app.handlers.states import MAIN_MENU
import logging

logger = logging.getLogger(__name__)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /start"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("⛔ Maaf, Anda tidak memiliki akses ke bot ini.")
        return ConversationHandler.END
    
    logger.info(f"User {user_id} started the bot")
    return await show_main_menu(update, context, edit_message=False)


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /cancel"""
    await update.message.reply_text("✅ Operasi dibatalkan.")
    return ConversationHandler.END
