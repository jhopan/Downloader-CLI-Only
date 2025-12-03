"""
Handler untuk kompresi file dengan format ZIP, TAR.GZ, dan 7Z
User dapat memilih file dan format kompresi secara manual
"""

import os
import zipfile
import tarfile
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.handlers.common import is_admin, get_download_path
from app.handlers.states import MAIN_MENU
from datetime import datetime

logger = logging.getLogger(__name__)


async def compress_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main compress menu"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    keyboard = [
        [InlineKeyboardButton("📦 Pilih File untuk Dikompres", callback_data="compress_select_files")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="file_operations")]
    ]
    
    await query.edit_message_text(
        "📦 <b>File Compressor</b>\n\n"
        "Kompres file ke dalam archive dengan format yang Anda pilih.\n\n"
        "<b>Format yang didukung:</b>\n"
        "• ZIP - Universal, cepat, kompatibel\n"
        "• TAR.GZ - Linux standard, good compression\n"
        "• 7Z - Best compression ratio (requires py7zr)\n\n"
        "Pilih file yang ingin dikompres:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    return MAIN_MENU


async def compress_select_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Select files to compress"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    db_manager = context.bot_data.get('db_manager')
    download_path = get_download_path(context, user_id, db_manager)
    
    # List all files in download directory
    try:
        files = []
        for root, dirs, filenames in os.walk(download_path):
            for filename in filenames:
                # Skip already compressed files and temp files
                if not filename.endswith(('.zip', '.tar.gz', '.7z', '.rar', '.tmp')):
                    rel_path = os.path.relpath(os.path.join(root, filename), download_path)
                    file_size = os.path.getsize(os.path.join(root, filename))
                    files.append((rel_path, file_size))
        
        if not files:
            await query.edit_message_text(
                "❌ <b>Tidak Ada File</b>\n\n"
                "Tidak ada file yang bisa dikompres di folder download.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Kembali", callback_data="compress_menu")
                ]]),
                parse_mode='HTML'
            )
            return MAIN_MENU
        
        # Sort by name
        files.sort(key=lambda x: x[0])
        
        # Initialize selected files in context if not exists
        if 'compress_selected_files' not in context.user_data:
            context.user_data['compress_selected_files'] = []
        
        # Create keyboard with file list
        keyboard = []
        for file_path, file_size in files[:20]:  # Limit to 20 files per page
            # Check if already selected
            selected = "✅ " if file_path in context.user_data['compress_selected_files'] else ""
            size_str = format_size(file_size)
            
            # Truncate long filenames
            display_name = file_path if len(file_path) <= 35 else file_path[:32] + "..."
            
            keyboard.append([
                InlineKeyboardButton(
                    f"{selected}{display_name} ({size_str})",
                    callback_data=f"compress_toggle_{file_path}"
                )
            ])
        
        # Add control buttons
        selected_count = len(context.user_data['compress_selected_files'])
        keyboard.append([
            InlineKeyboardButton(
                f"✅ Pilih Semua" if selected_count == 0 else f"❌ Hapus Semua ({selected_count})",
                callback_data="compress_toggle_all"
            )
        ])
        
        if selected_count > 0:
            keyboard.append([
                InlineKeyboardButton(
                    f"➡️ Lanjut ke Format ({selected_count} files)",
                    callback_data="compress_choose_format"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("🔙 Kembali", callback_data="compress_menu")
        ])
        
        await query.edit_message_text(
            f"📁 <b>Pilih File untuk Dikompres</b>\n\n"
            f"Tap file untuk memilih/batal pilih.\n"
            f"<b>Dipilih:</b> {selected_count} file(s)\n\n"
            f"<i>Total files: {len(files)}</i>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error listing files for compression: {e}")
        await query.edit_message_text(
            f"❌ <b>Error</b>\n\n"
            f"Gagal membaca daftar file: {str(e)}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Kembali", callback_data="compress_menu")
            ]]),
            parse_mode='HTML'
        )
    
    return MAIN_MENU


async def compress_toggle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle file selection"""
    query = update.callback_query
    await query.answer()
    
    file_path = query.data.replace("compress_toggle_", "")
    
    if 'compress_selected_files' not in context.user_data:
        context.user_data['compress_selected_files'] = []
    
    if file_path in context.user_data['compress_selected_files']:
        context.user_data['compress_selected_files'].remove(file_path)
        await query.answer("❌ File dibatalkan", show_alert=False)
    else:
        context.user_data['compress_selected_files'].append(file_path)
        await query.answer("✅ File dipilih", show_alert=False)
    
    # Refresh file list
    return await compress_select_files(update, context)


async def compress_toggle_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle all files selection"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    db_manager = context.bot_data.get('db_manager')
    download_path = get_download_path(context, user_id, db_manager)
    
    # Get all files
    files = []
    for root, dirs, filenames in os.walk(download_path):
        for filename in filenames:
            if not filename.endswith(('.zip', '.tar.gz', '.7z', '.rar', '.tmp')):
                rel_path = os.path.relpath(os.path.join(root, filename), download_path)
                files.append(rel_path)
    
    if 'compress_selected_files' not in context.user_data:
        context.user_data['compress_selected_files'] = []
    
    if len(context.user_data['compress_selected_files']) == 0:
        # Select all
        context.user_data['compress_selected_files'] = files[:20]  # Limit to 20
        await query.answer("✅ Semua file dipilih", show_alert=False)
    else:
        # Deselect all
        context.user_data['compress_selected_files'] = []
        await query.answer("❌ Semua pilihan dibatalkan", show_alert=False)
    
    # Refresh file list
    return await compress_select_files(update, context)


async def compress_choose_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Choose compression format"""
    query = update.callback_query
    await query.answer()
    
    selected_count = len(context.user_data.get('compress_selected_files', []))
    
    if selected_count == 0:
        await query.answer("⚠️ Pilih file terlebih dahulu!", show_alert=True)
        return await compress_select_files(update, context)
    
    keyboard = [
        [InlineKeyboardButton("📦 ZIP - Fast & Universal", callback_data="compress_format_zip")],
        [InlineKeyboardButton("📦 TAR.GZ - Good Compression", callback_data="compress_format_targz")],
        [InlineKeyboardButton("📦 7Z - Best Compression", callback_data="compress_format_7z")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="compress_select_files")]
    ]
    
    await query.edit_message_text(
        f"📦 <b>Pilih Format Kompresi</b>\n\n"
        f"<b>File dipilih:</b> {selected_count} file(s)\n\n"
        f"<b>Pilih format:</b>\n"
        f"• <b>ZIP</b> - Cepat, universal, bagus untuk Windows\n"
        f"• <b>TAR.GZ</b> - Kompresi bagus, standard Linux\n"
        f"• <b>7Z</b> - Kompresi terbaik, ukuran paling kecil\n\n"
        f"<i>Klik format yang diinginkan:</i>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    return MAIN_MENU


async def compress_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute compression"""
    query = update.callback_query
    await query.answer("🔄 Memproses kompresi...")
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    # Get format
    format_type = query.data.replace("compress_format_", "")
    selected_files = context.user_data.get('compress_selected_files', [])
    
    if not selected_files:
        await query.answer("⚠️ Tidak ada file dipilih!", show_alert=True)
        return MAIN_MENU
    
    db_manager = context.bot_data.get('db_manager')
    download_path = get_download_path(context, user_id, db_manager)
    
    # Generate archive name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"archive_{timestamp}"
    
    if format_type == "zip":
        archive_path = os.path.join(download_path, f"{archive_name}.zip")
    elif format_type == "targz":
        archive_path = os.path.join(download_path, f"{archive_name}.tar.gz")
    elif format_type == "7z":
        archive_path = os.path.join(download_path, f"{archive_name}.7z")
    else:
        await query.edit_message_text("❌ Format tidak valid")
        return MAIN_MENU
    
    try:
        # Show progress message
        progress_msg = await query.edit_message_text(
            f"⏳ <b>Mengompres File...</b>\n\n"
            f"Format: <code>{format_type.upper()}</code>\n"
            f"Files: {len(selected_files)} file(s)\n"
            f"Output: <code>{os.path.basename(archive_path)}</code>\n\n"
            f"<i>Mohon tunggu...</i>",
            parse_mode='HTML'
        )
        
        total_size = 0
        compressed_count = 0
        
        if format_type == "zip":
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_rel_path in selected_files:
                    file_full_path = os.path.join(download_path, file_rel_path)
                    if os.path.exists(file_full_path):
                        zipf.write(file_full_path, file_rel_path)
                        total_size += os.path.getsize(file_full_path)
                        compressed_count += 1
        
        elif format_type == "targz":
            with tarfile.open(archive_path, 'w:gz') as tarf:
                for file_rel_path in selected_files:
                    file_full_path = os.path.join(download_path, file_rel_path)
                    if os.path.exists(file_full_path):
                        tarf.add(file_full_path, arcname=file_rel_path)
                        total_size += os.path.getsize(file_full_path)
                        compressed_count += 1
        
        elif format_type == "7z":
            try:
                import py7zr
                with py7zr.SevenZipFile(archive_path, 'w') as szf:
                    for file_rel_path in selected_files:
                        file_full_path = os.path.join(download_path, file_rel_path)
                        if os.path.exists(file_full_path):
                            szf.write(file_full_path, file_rel_path)
                            total_size += os.path.getsize(file_full_path)
                            compressed_count += 1
            except ImportError:
                await query.edit_message_text(
                    "❌ <b>Library Tidak Tersedia</b>\n\n"
                    "Library 'py7zr' belum terinstall.\n"
                    "Install dengan: <code>pip install py7zr</code>",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Kembali", callback_data="compress_menu")
                    ]]),
                    parse_mode='HTML'
                )
                return MAIN_MENU
        
        # Get archive size
        archive_size = os.path.getsize(archive_path)
        compression_ratio = (1 - archive_size / total_size) * 100 if total_size > 0 else 0
        
        # Clear selected files
        context.user_data['compress_selected_files'] = []
        
        await query.edit_message_text(
            f"✅ <b>Kompresi Berhasil!</b>\n\n"
            f"📦 Archive: <code>{os.path.basename(archive_path)}</code>\n"
            f"📁 Files: {compressed_count} file(s)\n"
            f"📊 Size Asli: {format_size(total_size)}\n"
            f"📦 Size Archive: {format_size(archive_size)}\n"
            f"🎯 Compression: {compression_ratio:.1f}%\n\n"
            f"📂 Lokasi: <code>{download_path}</code>",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Kembali", callback_data="file_operations")
            ]]),
            parse_mode='HTML'
        )
        
        logger.info(f"User {user_id} compressed {compressed_count} files to {archive_path}")
        
    except Exception as e:
        logger.error(f"Error compressing files: {e}")
        await query.edit_message_text(
            f"❌ <b>Error Kompresi</b>\n\n"
            f"Gagal mengompres file: {str(e)}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Kembali", callback_data="compress_menu")
            ]]),
            parse_mode='HTML'
        )
    
    return MAIN_MENU


def format_size(size_bytes: int) -> str:
    """Format size to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
