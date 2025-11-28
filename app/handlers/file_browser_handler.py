from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.handlers.common import is_admin
from app.handlers.states import MAIN_MENU
from utils.file_manager import FileManager
import logging

logger = logging.getLogger(__name__)


async def file_browser_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show file browser menu"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    keyboard = [
        [InlineKeyboardButton("📂 Semua File", callback_data="files_all")],
        [InlineKeyboardButton("📁 File Berkategori", callback_data="files_categorized")],
        [InlineKeyboardButton("💾 Storage Info", callback_data="files_storage")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(
        "📂 <b>File Manager</b>\n\n"
        "Pilih mode tampilan:\n\n"
        "📂 <b>Semua File</b> - Lihat semua file dalam satu list\n"
        "📁 <b>File Berkategori</b> - Lihat file dikelompokkan berdasarkan tipe\n"
        "💾 <b>Storage Info</b> - Informasi penyimpanan\n",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    return MAIN_MENU


async def show_all_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all files in downloads folder"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    db_manager = context.bot_data.get('db_manager')
    from app.handlers.common import get_download_path
    import config
    
    download_path = get_download_path(context, user_id, db_manager) if db_manager else config.DEFAULT_DOWNLOAD_DIR
    
    file_manager = FileManager(download_path)
    files_dict = file_manager.get_all_files(categorized=False)
    
    if not files_dict or not files_dict.get('Semua File'):
        await query.edit_message_text(
            "📂 <b>Semua File</b>\n\n"
            "📭 Folder downloads kosong.\n"
            f"📁 Lokasi: <code>{download_path}</code>",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Kembali", callback_data="file_browser")
            ]]),
            parse_mode='HTML'
        )
        return MAIN_MENU
    
    files = files_dict['Semua File']
    
    # Build text
    text = f"📂 <b>Semua File</b>\n\n"
    text += f"📁 Lokasi: <code>{download_path}</code>\n"
    text += f"📊 Total: {len(files)} file\n\n"
    
    # Limit to 15 files per page
    for i, file_info in enumerate(files[:15], 1):
        category_emoji = _get_category_emoji(file_info['category'])
        size_str = FileManager.format_size(file_info['size'])
        time_str = file_info['modified_datetime'].strftime("%d/%m %H:%M")
        
        filename = file_info['filename']
        if len(filename) > 35:
            filename = filename[:32] + "..."
        
        text += f"{i}. {category_emoji} <code>{filename}</code>\n"
        text += f"   📦 {size_str} | 🕐 {time_str}\n"
    
    if len(files) > 15:
        text += f"\n... dan {len(files) - 15} file lainnya"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data="files_all")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="file_browser")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    return MAIN_MENU


async def show_categorized_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show files grouped by category"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    db_manager = context.bot_data.get('db_manager')
    from app.handlers.common import get_download_path
    import config
    
    download_path = get_download_path(context, user_id, db_manager) if db_manager else config.DEFAULT_DOWNLOAD_DIR
    
    file_manager = FileManager(download_path)
    files_by_category = file_manager.get_all_files(categorized=True)
    
    if not files_by_category:
        await query.edit_message_text(
            "📁 <b>File Berkategori</b>\n\n"
            "📭 Folder downloads kosong.\n"
            f"📁 Lokasi: <code>{download_path}</code>",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Kembali", callback_data="file_browser")
            ]]),
            parse_mode='HTML'
        )
        return MAIN_MENU
    
    # Build text
    text = f"📁 <b>File Berkategori</b>\n\n"
    text += f"📂 Lokasi: <code>{download_path}</code>\n\n"
    
    total_files = sum(len(files) for files in files_by_category.values())
    text += f"📊 Total: {total_files} file\n\n"
    
    # Show categories with file count
    for category, files in files_by_category.items():
        if not files:
            continue
        
        emoji = _get_category_emoji(category)
        total_size = sum(f['size'] for f in files)
        size_str = FileManager.format_size(total_size)
        
        text += f"{emoji} <b>{category}</b>: {len(files)} file ({size_str})\n"
        
        # Show first 3 files in category
        for file_info in files[:3]:
            filename = file_info['filename']
            if len(filename) > 30:
                filename = filename[:27] + "..."
            size = FileManager.format_size(file_info['size'])
            text += f"   • <code>{filename}</code> ({size})\n"
        
        if len(files) > 3:
            text += f"   ... dan {len(files) - 3} file lainnya\n"
        
        text += "\n"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data="files_categorized")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="file_browser")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    return MAIN_MENU


async def show_storage_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show storage information"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    db_manager = context.bot_data.get('db_manager')
    from app.handlers.common import get_download_path
    import config
    
    download_path = get_download_path(context, user_id, db_manager) if db_manager else config.DEFAULT_DOWNLOAD_DIR
    
    file_manager = FileManager(download_path)
    stats = file_manager.get_storage_stats()
    
    text = "💾 <b>Storage Info</b>\n\n"
    text += f"📁 Lokasi: <code>{stats['path']}</code>\n\n"
    
    text += "<b>Disk Storage:</b>\n"
    text += f"📊 Total: {FileManager.format_size(stats['total'])}\n"
    text += f"📈 Terpakai: {FileManager.format_size(stats['used'])}\n"
    text += f"📉 Tersisa: {FileManager.format_size(stats['free'])}\n\n"
    
    text += "<b>Downloads Folder:</b>\n"
    text += f"📂 Total File: {stats['file_count']}\n"
    text += f"📦 Total Ukuran: {FileManager.format_size(stats['downloads_size'])}\n"
    
    # Calculate percentage
    if stats['total'] > 0:
        used_pct = (stats['used'] / stats['total']) * 100
        free_pct = (stats['free'] / stats['total']) * 100
        
        text += f"\n💹 Penggunaan: {used_pct:.1f}% | Tersisa: {free_pct:.1f}%"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data="files_storage")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="file_browser")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    return MAIN_MENU


def _get_category_emoji(category: str) -> str:
    """Get emoji for category"""
    emojis = {
        'Video': '🎬',
        'Audio': '🎵',
        'Foto': '🖼️',
        'Dokumen': '📄',
        'Archive': '📦',
        'Executable': '⚙️',
        'Code': '💻',
        'Lainnya': '📁'
    }
    return emojis.get(category, '📁')
