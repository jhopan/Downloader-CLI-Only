from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.handlers.common import is_admin, show_main_menu, get_download_path, delete_user_message
from app.handlers.states import MAIN_MENU, WAITING_CUSTOM_PATH
from app.keyboards.inline_keyboards import settings_keyboard, back_button_keyboard, back_to_main_keyboard
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show menu pengaturan"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    db_manager = context.bot_data.get('db_manager')
    use_custom = False
    custom_path = None
    
    if db_manager:
        pref = db_manager.get_user_preference(user_id)
        if pref:
            use_custom = pref['use_custom_path']
            custom_path = pref['custom_download_path']
    
    reply_markup = settings_keyboard(use_custom)
    
    status = "Custom Path" if use_custom else "Default Path"
    path_info = custom_path if use_custom and custom_path else get_download_path(context, user_id, db_manager)
    
    await query.edit_message_text(
        "⚙️ <b>Pengaturan Bot</b>\n\n"
        f"📍 <b>Lokasi Unduhan:</b> {status}\n"
        f"📁 <b>Path:</b> <code>{path_info}</code>\n\n"
        "Pilih opsi di bawah:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    return MAIN_MENU


async def toggle_path_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle antara default dan custom path"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    db_manager = context.bot_data.get('db_manager')
    
    if not db_manager:
        await query.answer("❌ Database tidak tersedia", show_alert=True)
        return MAIN_MENU
    
    pref = db_manager.get_user_preference(user_id)
    
    if not pref or not pref.get('custom_download_path'):
        await query.answer("⚠️ Atur lokasi custom terlebih dahulu", show_alert=True)
        return MAIN_MENU
    
    # Toggle
    new_status = not pref['use_custom_path']
    db_manager.toggle_custom_path(user_id, new_status)
    
    await query.answer(f"✅ Beralih ke {'Custom' if new_status else 'Default'} Path")
    
    # Refresh menu
    return await settings_menu(update, context)


async def set_custom_path_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show menu untuk set custom path"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    reply_markup = back_button_keyboard()
    
    await query.edit_message_text(
        "📝 <b>Atur Lokasi Unduhan Custom</b>\n\n"
        "Kirim path direktori untuk menyimpan file unduhan.\n\n"
        "<b>Contoh:</b>\n"
        "• <code>/home/user/downloads</code>\n"
        "• <code>/var/www/files</code>\n"
        "• <code>./my_downloads</code>\n\n"
        "⚠️ Pastikan bot memiliki permission write ke folder tersebut.",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    return WAITING_CUSTOM_PATH


async def handle_custom_path(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle input custom path dari user"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    custom_path = update.message.text.strip()
    
    # Validasi path
    try:
        # Expand path
        custom_path = os.path.expanduser(custom_path)
        custom_path = os.path.abspath(custom_path)
        
        # Coba buat folder jika belum ada
        os.makedirs(custom_path, exist_ok=True)
        
        # Test write permission
        test_file = os.path.join(custom_path, '.test_write')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        
        # Save to database
        db_manager = context.bot_data.get('db_manager')
        if db_manager:
            db_manager.set_user_download_path(user_id, custom_path, use_custom=True)
        
        reply_markup = back_to_main_keyboard()
        
        if 'main_message_id' in context.user_data:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=context.user_data['main_message_id'],
                text=f"✅ <b>Lokasi Custom Tersimpan!</b>\n\n"
                     f"Path: <code>{custom_path}</code>\n\n"
                     f"Semua unduhan akan disimpan di lokasi ini.",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        
        await delete_user_message(update)
        logger.info(f"User {user_id} set custom path: {custom_path}")
        return MAIN_MENU
        
    except PermissionError:
        reply_markup = back_button_keyboard()
        
        if 'main_message_id' in context.user_data:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=context.user_data['main_message_id'],
                text=f"❌ <b>Permission Denied</b>\n\n"
                     f"Bot tidak memiliki akses write ke:\n"
                     f"<code>{custom_path}</code>\n\n"
                     f"Silakan pilih folder lain atau ubah permission.",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        
        await delete_user_message(update)
        return WAITING_CUSTOM_PATH
        
    except Exception as e:
        logger.error(f"Error setting custom path: {e}")
        
        reply_markup = back_button_keyboard()
        
        if 'main_message_id' in context.user_data:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=context.user_data['main_message_id'],
                text=f"❌ <b>Error</b>\n\n"
                     f"Path tidak valid: {str(e)}\n\n"
                     f"Silakan coba lagi dengan path yang valid.",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        
        await delete_user_message(update)
        return WAITING_CUSTOM_PATH


async def download_history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show download history"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    db_manager = context.bot_data.get('db_manager')
    
    if not db_manager:
        await query.edit_message_text(
            "❌ Database tidak tersedia",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Kembali", callback_data="back_to_main")
            ]])
        )
        return MAIN_MENU
    
    # Ambil riwayat unduhan (20 terakhir)
    history = db_manager.get_download_history(user_id, limit=20)
    
    if not history:
        await query.edit_message_text(
            "📋 <b>Riwayat Unduhan</b>\n\n"
            "Belum ada riwayat unduhan.\n"
            "Mulai unduh file untuk melihat riwayatnya di sini!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Kembali", callback_data="back_to_main")
            ]]),
            parse_mode='HTML'
        )
        return MAIN_MENU
    
    # Get storage info
    import shutil
    try:
        download_path = get_download_path(context, user_id, db_manager)
        total, used, free = shutil.disk_usage(download_path)
        storage_info = (
            f"💾 <b>Storage Info</b>\n"
            f"📁 Lokasi: <code>{download_path}</code>\n"
            f"📊 Total: {_format_size(total)} | "
            f"Terpakai: {_format_size(used)} | "
            f"Tersisa: {_format_size(free)}\n\n"
        )
    except Exception as e:
        storage_info = ""
        logger.warning(f"Failed to get storage info: {e}")
    
    # Format riwayat
    text = f"📋 <b>Riwayat Unduhan</b>\n\n{storage_info}"
    
    for i, item in enumerate(history, 1):
        status_emoji = {
            'completed': '✅',
            'failed': '❌',
            'cancelled': '⚠️',
            'downloading': '⏳'
        }.get(item['status'], '❓')
        
        # Format waktu
        try:
            start_time = datetime.fromisoformat(item['start_time'])
            time_str = start_time.strftime("%d/%m/%Y %H:%M")
        except:
            time_str = "N/A"
        
        # Format ukuran file
        file_size = item['file_size']
        if file_size:
            size_str = _format_size(file_size)
        else:
            size_str = "N/A"
        
        # Potong nama file jika terlalu panjang
        filename = item['filename']
        if len(filename) > 40:
            filename = filename[:37] + "..."
        
        text += f"{i}. {status_emoji} <code>{filename}</code>\n"
        text += f"   📅 {time_str} | 📦 {size_str}\n"
        
        # Tambah separator setiap 5 item untuk readability
        if i % 5 == 0 and i < len(history):
            text += "\n"
    
    # Keyboard
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data="download_history")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    return MAIN_MENU


def _format_size(size_bytes: int) -> str:
    """Format ukuran file ke human readable"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"
