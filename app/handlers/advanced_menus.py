"""
Menu wrapper functions untuk advanced handler
Converts commands to inline keyboard menus
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.handlers.states import MAIN_MENU
import logging

logger = logging.getLogger(__name__)


async def batch_download_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Batch download menu"""
    keyboard = [
        [InlineKeyboardButton("📤 Send URLs (one per line)", callback_data="action_send_batch_urls")],
        [
            InlineKeyboardButton("📋 Example Format", callback_data="help_batch_format"),
            InlineKeyboardButton("ℹ️ Help", callback_data="help_batch_download")
        ],
        [InlineKeyboardButton("◀️ Back", callback_data="menu_download")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "📦 <b>Batch Download</b>\n\n"
        "<b>Download Multiple URLs:</b>\n"
        "• Max 20 URLs per batch\n"
        "• Real-time progress monitoring\n"
        "• Individual file tracking\n"
        "• Auto-retry failed downloads\n\n"
        "<b>How to use:</b>\n"
        "1. Click 'Send URLs'\n"
        "2. Send URLs (one per line)\n"
        "3. Type 'done' when finished\n"
        "4. Monitor batch progress\n\n"
        "<b>Example:</b>\n"
        "<code>https://example.com/file1.mp4\n"
        "https://example.com/file2.zip\n"
        "https://example.com/file3.pdf\n"
        "done</code>"
    )
    
    await update.callback_query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    return MAIN_MENU


async def bandwidth_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bandwidth limiter menu"""
    from app.handlers.bandwidth_handler import bandwidth_command
    # Call existing bandwidth command but adapt for callback query
    update.message = update.callback_query.message
    await bandwidth_command(update, context)
    return MAIN_MENU
