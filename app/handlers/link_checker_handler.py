"""
Handler untuk Link Checker/Validator di Telegram
Validate links sebelum download
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.handlers.common import is_admin
from app.handlers.states import MAIN_MENU, WAITING_LINK
from src.utils.link_validator import LinkValidator

logger = logging.getLogger(__name__)


async def link_checker_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main link checker menu"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    keyboard = [
        [InlineKeyboardButton("🔗 Check Single Link", callback_data="linkcheck_single")],
        [InlineKeyboardButton("📋 Check Multiple Links", callback_data="linkcheck_multiple")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="download_menu")]
    ]
    
    await query.edit_message_text(
        "🔍 <b>Link Checker/Validator</b>\n\n"
        "Validasi link sebelum download untuk memastikan:\n"
        "• Link masih aktif\n"
        "• File size\n"
        "• Content type\n"
        "• Response time\n\n"
        "<b>Pilih mode:</b>\n"
        "• <b>Single Link</b> - Check 1 URL\n"
        "• <b>Multiple Links</b> - Check hingga 10 URLs sekaligus",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    return MAIN_MENU


async def link_checker_single(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt for single link"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['link_check_mode'] = 'single'
    
    # Store message ID for editing later
    context.user_data['main_message_id'] = query.message.message_id
    
    keyboard = [[InlineKeyboardButton("🔙 Batal", callback_data="link_checker_menu")]]
    
    await query.edit_message_text(
        "🔗 <b>Check Single Link</b>\n\n"
        "Kirim URL yang ingin divalidasi:\n\n"
        "<i>Contoh:</i>\n"
        "<code>https://example.com/file.mp4</code>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    return WAITING_LINK


async def link_checker_multiple(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt for multiple links"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['link_check_mode'] = 'multiple'
    context.user_data['main_message_id'] = query.message.message_id
    
    keyboard = [[InlineKeyboardButton("🔙 Batal", callback_data="link_checker_menu")]]
    
    await query.edit_message_text(
        "📋 <b>Check Multiple Links</b>\n\n"
        "Kirim URLs yang ingin divalidasi (satu per baris).\n"
        "Max: 10 URLs\n\n"
        "<i>Contoh:</i>\n"
        "<code>https://example.com/file1.mp4\n"
        "https://example.com/file2.zip\n"
        "https://example.com/file3.pdf</code>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    return WAITING_LINK


async def link_checker_validate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Validate the submitted links"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    mode = context.user_data.get('link_check_mode', 'single')
    user_input = update.message.text.strip()
    
    # Parse URLs
    if mode == 'single':
        urls = [user_input]
    else:
        urls = [url.strip() for url in user_input.split('\n') if url.strip()]
        urls = urls[:10]  # Limit to 10
    
    if not urls:
        await update.message.reply_text(
            "❌ Tidak ada URL yang valid.\n\n"
            "Kirim URL yang benar.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Kembali", callback_data="link_checker_menu")
            ]]),
            parse_mode='HTML'
        )
        return MAIN_MENU
    
    # Show progress message
    progress_msg = await update.message.reply_text(
        f"🔍 <b>Validating {len(urls)} link(s)...</b>\n\n"
        f"<i>Mohon tunggu...</i>",
        parse_mode='HTML'
    )
    
    # Validate links
    validator = LinkValidator(timeout=10)
    results = await validator.validate_links(urls)
    
    # Build result message
    valid_count = sum(1 for r in results if r['valid'])
    invalid_count = len(results) - valid_count
    
    message = f"🔍 <b>Link Validation Results</b>\n\n"
    message += f"📊 <b>Summary:</b>\n"
    message += f"✅ Valid: {valid_count}\n"
    message += f"❌ Invalid: {invalid_count}\n\n"
    
    for i, result in enumerate(results, 1):
        status_emoji = "✅" if result['valid'] else "❌"
        message += f"{status_emoji} <b>Link {i}:</b>\n"
        
        # Truncate URL if too long
        url_display = result['url'][:50] + "..." if len(result['url']) > 50 else result['url']
        message += f"🔗 <code>{url_display}</code>\n"
        
        if result['valid']:
            message += f"📊 Size: {validator.format_size(result['file_size'])}\n"
            message += f"📁 Type: {validator.get_content_category(result['content_type'])}\n"
            if result['filename']:
                filename_display = result['filename'][:40] + "..." if len(result['filename']) > 40 else result['filename']
                message += f"📄 File: <code>{filename_display}</code>\n"
            message += f"⏱️ Response: {result['response_time']:.2f}s\n"
        else:
            message += f"⚠️ Error: {result['error']}\n"
        
        message += "\n"
        
        # Telegram message limit is 4096 chars
        if len(message) > 3500:
            message += f"<i>...dan {len(results) - i} link lainnya</i>\n"
            break
    
    keyboard = []
    
    # If all links valid, offer to download
    if valid_count > 0:
        if mode == 'single':
            keyboard.append([InlineKeyboardButton("📥 Download Link Ini", callback_data="direct_download")])
        else:
            keyboard.append([InlineKeyboardButton("📥 Batch Download", callback_data="batch_download_menu")])
    
    keyboard.append([InlineKeyboardButton("🔍 Check Lagi", callback_data="link_checker_menu")])
    keyboard.append([InlineKeyboardButton("🔙 Menu", callback_data="back_to_main")])
    
    # Delete user message
    try:
        await update.message.delete()
    except:
        pass
    
    # Edit progress message with results
    await progress_msg.edit_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    # Clear context
    if 'link_check_mode' in context.user_data:
        del context.user_data['link_check_mode']
    
    logger.info(f"User {user_id} validated {len(urls)} links: {valid_count} valid, {invalid_count} invalid")
    
    return MAIN_MENU
