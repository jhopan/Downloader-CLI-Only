from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.handlers.common import is_admin
from app.handlers.states import MAIN_MENU
from utils.file_manager import FileManager
import os
import logging
import zipfile
import tarfile

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
        [InlineKeyboardButton("🛠️ Operasi File", callback_data="file_operations")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(
        "📂 <b>File Manager</b>\n\n"
        "Pilih mode tampilan:\n\n"
        "📂 <b>Semua File</b> - Lihat semua file dalam satu list\n"
        "📁 <b>File Berkategori</b> - Lihat file dikelompokkan berdasarkan tipe\n"
        "💾 <b>Storage Info</b> - Informasi penyimpanan\n"
        "🛠️ <b>Operasi File</b> - Hapus, ekstrak, organize file\n",
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


async def file_operations_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show file operations menu"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    keyboard = [
        [InlineKeyboardButton("🗑️ Hapus File", callback_data="file_op_delete")],
        [InlineKeyboardButton("📦 Ekstrak Archive", callback_data="file_op_extract")],
        [InlineKeyboardButton("📁 Pindah ke Kategori", callback_data="file_op_categorize")],
        [InlineKeyboardButton("🧹 Bersihkan Semua", callback_data="file_op_clean_all")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="file_browser")]
    ]
    
    await query.edit_message_text(
        "🛠️ <b>Operasi File</b>\n\n"
        "Pilih operasi yang ingin dilakukan:\n\n"
        "🗑️ <b>Hapus File</b> - Hapus file tertentu\n"
        "📦 <b>Ekstrak Archive</b> - Ekstrak file ZIP/RAR\n"
        "📁 <b>Pindah ke Kategori</b> - Organisir file otomatis\n"
        "🧹 <b>Bersihkan Semua</b> - Hapus semua file",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    return MAIN_MENU


async def delete_file_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show delete file menu"""
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
            "📭 <b>Tidak Ada File</b>\n\n"
            "Folder downloads kosong.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Kembali", callback_data="file_operations")
            ]]),
            parse_mode='HTML'
        )
        return MAIN_MENU
    
    files = files_dict['Semua File'][:10]  # Limit 10 files
    
    keyboard = []
    for file_info in files:
        filename = file_info['filename']
        if len(filename) > 30:
            filename = filename[:27] + "..."
        
        keyboard.append([InlineKeyboardButton(
            f"🗑️ {filename}",
            callback_data=f"delete_file_{file_info['filename']}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="file_operations")])
    
    await query.edit_message_text(
        "🗑️ <b>Hapus File</b>\n\n"
        "Pilih file yang ingin dihapus:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    return MAIN_MENU


async def extract_archive_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show extract archive menu"""
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
    files_dict = file_manager.get_all_files(categorized=True)
    
    archives = files_dict.get('Archive', [])
    
    if not archives:
        await query.edit_message_text(
            "📦 <b>Tidak Ada Archive</b>\n\n"
            "Tidak ada file ZIP/RAR yang dapat diekstrak.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Kembali", callback_data="file_operations")
            ]]),
            parse_mode='HTML'
        )
        return MAIN_MENU
    
    keyboard = []
    for file_info in archives[:10]:
        filename = file_info['filename']
        if len(filename) > 30:
            filename = filename[:27] + "..."
        
        keyboard.append([InlineKeyboardButton(
            f"📦 {filename}",
            callback_data=f"extract_{file_info['filename']}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="file_operations")])
    
    await query.edit_message_text(
        "📦 <b>Ekstrak Archive</b>\n\n"
        "Pilih file yang ingin diekstrak:",
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
        'Lainnya': '📎'
    }
    return emojis.get(category, '📎')


async def confirm_delete_file(update: Update, context: ContextTypes.DEFAULT_TYPE, filename: str):
    """Confirm delete file"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    db_manager = context.bot_data.get('db_manager')
    from app.handlers.common import get_download_path
    import config
    
    download_path = get_download_path(context, user_id, db_manager) if db_manager else config.DEFAULT_DOWNLOAD_DIR
    file_path = os.path.join(download_path, filename)
    
    if not os.path.exists(file_path):
        await query.edit_message_text(
            f"❌ <b>File Tidak Ditemukan</b>\n\n"
            f"File <code>{filename}</code> tidak ditemukan.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Kembali", callback_data="file_op_delete")
            ]]),
            parse_mode='HTML'
        )
        return MAIN_MENU
    
    file_size = FileManager.format_size(os.path.getsize(file_path))
    
    keyboard = [
        [InlineKeyboardButton("✅ Ya, Hapus", callback_data=f"confirm_delete_{filename}")],
        [InlineKeyboardButton("❌ Batal", callback_data="file_op_delete")]
    ]
    
    await query.edit_message_text(
        f"🗑️ <b>Konfirmasi Hapus</b>\n\n"
        f"Apakah Anda yakin ingin menghapus file ini?\n\n"
        f"📄 Nama: <code>{filename}</code>\n"
        f"📦 Ukuran: {file_size}\n\n"
        f"⚠️ File yang dihapus tidak dapat dikembalikan!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    return MAIN_MENU


async def execute_delete_file(update: Update, context: ContextTypes.DEFAULT_TYPE, filename: str):
    """Execute delete file"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    db_manager = context.bot_data.get('db_manager')
    from app.handlers.common import get_download_path
    import config
    
    download_path = get_download_path(context, user_id, db_manager) if db_manager else config.DEFAULT_DOWNLOAD_DIR
    file_path = os.path.join(download_path, filename)
    
    try:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            os.remove(file_path)
            
            await query.edit_message_text(
                f"✅ <b>File Berhasil Dihapus</b>\n\n"
                f"📄 Nama: <code>{filename}</code>\n"
                f"📦 Ukuran: {FileManager.format_size(file_size)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Kembali", callback_data="file_operations")
                ]]),
                parse_mode='HTML'
            )
            logger.info(f"File deleted: {filename} by user {user_id}")
        else:
            await query.edit_message_text(
                f"❌ <b>File Tidak Ditemukan</b>\n\n"
                f"File <code>{filename}</code> tidak ditemukan.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Kembali", callback_data="file_operations")
                ]]),
                parse_mode='HTML'
            )
    except Exception as e:
        logger.error(f"Error deleting file {filename}: {e}")
        await query.edit_message_text(
            f"❌ <b>Error</b>\n\n"
            f"Gagal menghapus file: {str(e)}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Kembali", callback_data="file_operations")
            ]]),
            parse_mode='HTML'
        )
    
    return MAIN_MENU


async def execute_extract_archive(update: Update, context: ContextTypes.DEFAULT_TYPE, filename: str):
    """Execute extract archive"""
    query = update.callback_query
    await query.answer("🔄 Mengekstrak file...")
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    db_manager = context.bot_data.get('db_manager')
    from app.handlers.common import get_download_path
    import config
    
    download_path = get_download_path(context, user_id, db_manager) if db_manager else config.DEFAULT_DOWNLOAD_DIR
    file_path = os.path.join(download_path, filename)
    
    if not os.path.exists(file_path):
        await query.edit_message_text(
            f"❌ <b>File Tidak Ditemukan</b>\n\n"
            f"File <code>{filename}</code> tidak ditemukan.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Kembali", callback_data="file_operations")
            ]]),
            parse_mode='HTML'
        )
        return MAIN_MENU
    
    # Create extract folder
    base_name = os.path.splitext(filename)[0]
    extract_path = os.path.join(download_path, base_name)
    
    # If folder exists, add number
    counter = 1
    original_extract_path = extract_path
    while os.path.exists(extract_path):
        extract_path = f"{original_extract_path}_{counter}"
        counter += 1
    
    try:
        os.makedirs(extract_path, exist_ok=True)
        
        # Extract based on file type
        if filename.lower().endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
                file_count = len(zip_ref.namelist())
        elif filename.lower().endswith('.rar'):
            # RAR support with rarfile library
            try:
                import rarfile
                with rarfile.RarFile(file_path, 'r') as rar_ref:
                    rar_ref.extractall(extract_path)
                    file_count = len(rar_ref.namelist())
            except ImportError:
                await query.edit_message_text(
                    f"❌ <b>Library Tidak Tersedia</b>\n\n"
                    f"Library 'rarfile' belum terinstall.\n"
                    f"Install dengan: <code>pip install rarfile</code>\n\n"
                    f"<b>Note:</b> Juga butuh unrar/unar di system:\n"
                    f"• Linux: <code>sudo apt install unrar</code>\n"
                    f"• Windows: Download dari rarlab.com",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Kembali", callback_data="file_operations")
                    ]]),
                    parse_mode='HTML'
                )
                return MAIN_MENU
            except rarfile.RarCannotExec:
                await query.edit_message_text(
                    f"❌ <b>UnRAR Tidak Ditemukan</b>\n\n"
                    f"UnRAR tool tidak tersedia di system.\n\n"
                    f"<b>Install UnRAR:</b>\n"
                    f"• Linux: <code>sudo apt install unrar</code>\n"
                    f"• CasaOS: Install via terminal atau app store\n"
                    f"• Windows: Download dari rarlab.com",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Kembali", callback_data="file_operations")
                    ]]),
                    parse_mode='HTML'
                )
                return MAIN_MENU
        elif filename.lower().endswith(('.tar', '.tar.gz', '.tgz', '.tar.bz2')):
            with tarfile.open(file_path, 'r:*') as tar_ref:
                tar_ref.extractall(extract_path)
                file_count = len(tar_ref.getmembers())
        elif filename.lower().endswith('.7z'):
            # 7z support with py7zr library
            try:
                import py7zr
                with py7zr.SevenZipFile(file_path, 'r') as sz_ref:
                    sz_ref.extractall(extract_path)
                    file_count = len(sz_ref.getnames())
            except ImportError:
                await query.edit_message_text(
                    f"❌ <b>Library Tidak Tersedia</b>\n\n"
                    f"Library 'py7zr' belum terinstall.\n"
                    f"Install dengan: <code>pip install py7zr</code>",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Kembali", callback_data="file_operations")
                    ]]),
                    parse_mode='HTML'
                )
                return MAIN_MENU
        else:
            await query.edit_message_text(
                f"❌ <b>Format Tidak Didukung</b>\n\n"
                f"Format file <code>{filename}</code> tidak didukung.\n"
                f"Format yang didukung: ZIP, RAR, 7Z, TAR, TAR.GZ",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Kembali", callback_data="file_operations")
                ]]),
                parse_mode='HTML'
            )
            return MAIN_MENU
        
        await query.edit_message_text(
            f"✅ <b>Ekstraksi Berhasil</b>\n\n"
            f"📦 Archive: <code>{filename}</code>\n"
            f"📂 Diekstrak ke: <code>{os.path.basename(extract_path)}</code>\n"
            f"📊 Total file: {file_count}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Kembali", callback_data="file_operations")
            ]]),
            parse_mode='HTML'
        )
        logger.info(f"Archive extracted: {filename} -> {extract_path} by user {user_id}")
        
        # Send notification: extraction complete
        notification_manager = context.bot_data.get('notification_manager')
        if notification_manager:
            import asyncio
            asyncio.create_task(notification_manager.send_notification(
                chat_id=user_id,
                event_type='extraction_complete',
                filename=filename,
                extract_path=os.path.basename(extract_path)
            ))
        
    except Exception as e:
        logger.error(f"Error extracting archive {filename}: {e}")
        # Clean up extract folder if error
        if os.path.exists(extract_path):
            try:
                import shutil
                shutil.rmtree(extract_path)
            except:
                pass
        
        # Send notification: extraction error
        notification_manager = context.bot_data.get('notification_manager')
        if notification_manager:
            import asyncio
            asyncio.create_task(notification_manager.send_notification(
                chat_id=user_id,
                event_type='extraction_error',
                filename=filename,
                error=str(e)
            ))
        
        await query.edit_message_text(
            f"❌ <b>Error Ekstraksi</b>\n\n"
            f"Gagal mengekstrak file: {str(e)}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Kembali", callback_data="file_operations")
            ]]),
            parse_mode='HTML'
        )
    
    return MAIN_MENU

