"""File operations handlers - Categorize and Clean All"""
import os
import shutil
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.handlers.common import is_admin
from app.handlers.states import MAIN_MENU
from utils.file_manager import FileManager

logger = logging.getLogger(__name__)


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
        'Lainnya': '📎'
    }
    return emojis.get(category, '📎')


async def categorize_files_operation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Categorize all files into folders"""
    query = update.callback_query
    await query.answer("🔄 Mengkategorikan file...")
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    db_manager = context.bot_data.get('db_manager')
    from app.handlers.common import get_download_path
    import config
    
    download_path = get_download_path(context, user_id, db_manager) if db_manager else config.DEFAULT_DOWNLOAD_DIR
    file_manager = FileManager(download_path)
    files_dict = file_manager.get_all_files(categorized=True)
    
    if not files_dict:
        await query.edit_message_text(
            "📭 <b>Tidak Ada File</b>\n\n"
            "Folder downloads kosong.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Kembali", callback_data="file_operations")
            ]]),
            parse_mode='HTML'
        )
        return MAIN_MENU
    
    try:
        moved_count = 0
        categories_created = []
        
        for category, files in files_dict.items():
            if not files or category == 'Lainnya':
                continue
            
            # Create category folder
            category_path = os.path.join(download_path, category)
            if not os.path.exists(category_path):
                os.makedirs(category_path)
                categories_created.append(category)
            
            # Move files to category folder
            for file_info in files:
                src = os.path.join(download_path, file_info['filename'])
                dst = os.path.join(category_path, file_info['filename'])
                
                if os.path.exists(src) and os.path.isfile(src) and src != dst:
                    try:
                        shutil.move(src, dst)
                        moved_count += 1
                    except Exception as move_err:
                        logger.warning(f"Failed to move {file_info['filename']}: {move_err}")
        
        result_text = f"✅ <b>Kategorisasi Selesai</b>\n\n"
        result_text += f"📂 Folder dibuat: {len(categories_created)}\n"
        result_text += f"📄 File dipindahkan: {moved_count}\n\n"
        
        if categories_created:
            result_text += f"<b>Kategori:</b>\n"
            for cat in categories_created:
                emoji = _get_category_emoji(cat)
                result_text += f"{emoji} {cat}\n"
        
        await query.edit_message_text(
            result_text,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Kembali", callback_data="file_operations")
            ]]),
            parse_mode='HTML'
        )
        logger.info(f"Files categorized: {moved_count} files by user {user_id}")
        
    except Exception as e:
        logger.error(f"Error categorizing files: {e}")
        await query.edit_message_text(
            f"❌ <b>Error</b>\n\n"
            f"Gagal mengkategorikan file: {str(e)}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Kembali", callback_data="file_operations")
            ]]),
            parse_mode='HTML'
        )
    
    return MAIN_MENU


async def confirm_clean_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm clean all files"""
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
    
    if stats['file_count'] == 0:
        await query.edit_message_text(
            "📭 <b>Tidak Ada File</b>\n\n"
            "Folder downloads sudah kosong.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Kembali", callback_data="file_operations")
            ]]),
            parse_mode='HTML'
        )
        return MAIN_MENU
    
    keyboard = [
        [InlineKeyboardButton("⚠️ YA, HAPUS SEMUA", callback_data="confirm_clean_all_yes")],
        [InlineKeyboardButton("❌ Batal", callback_data="file_operations")]
    ]
    
    await query.edit_message_text(
        f"🧹 <b>Konfirmasi Bersihkan Semua</b>\n\n"
        f"⚠️ <b>PERINGATAN!</b>\n"
        f"Operasi ini akan menghapus SEMUA file dan folder dalam downloads.\n\n"
        f"📂 Total file: {stats['file_count']}\n"
        f"📦 Total ukuran: {FileManager.format_size(stats['downloads_size'])}\n\n"
        f"❗ File yang dihapus TIDAK DAPAT dikembalikan!\n"
        f"Apakah Anda yakin?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    return MAIN_MENU


async def execute_clean_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute clean all files"""
    query = update.callback_query
    await query.answer("🔄 Menghapus semua file...")
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    db_manager = context.bot_data.get('db_manager')
    from app.handlers.common import get_download_path
    import config
    
    download_path = get_download_path(context, user_id, db_manager) if db_manager else config.DEFAULT_DOWNLOAD_DIR
    
    try:
        # Count files before deletion
        file_count = 0
        total_size = 0
        
        for item in os.listdir(download_path):
            item_path = os.path.join(download_path, item)
            if os.path.isfile(item_path):
                total_size += os.path.getsize(item_path)
                file_count += 1
                os.remove(item_path)
            elif os.path.isdir(item_path):
                # Get folder size
                for root, dirs, files in os.walk(item_path):
                    for f in files:
                        fp = os.path.join(root, f)
                        if os.path.exists(fp):
                            total_size += os.path.getsize(fp)
                            file_count += 1
                # Remove folder
                shutil.rmtree(item_path)
        
        await query.edit_message_text(
            f"✅ <b>Bersihkan Selesai</b>\n\n"
            f"🗑️ File dihapus: {file_count}\n"
            f"💾 Ruang dikosongkan: {FileManager.format_size(total_size)}\n\n"
            f"📂 Folder downloads sudah bersih!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Kembali", callback_data="file_operations")
            ]]),
            parse_mode='HTML'
        )
        logger.info(f"Clean all executed: {file_count} files deleted by user {user_id}")
        
    except Exception as e:
        logger.error(f"Error cleaning all files: {e}")
        await query.edit_message_text(
            f"❌ <b>Error</b>\n\n"
            f"Gagal menghapus file: {str(e)}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Kembali", callback_data="file_operations")
            ]]),
            parse_mode='HTML'
        )
    
    return MAIN_MENU
