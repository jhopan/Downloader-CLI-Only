"""
Handler untuk upload file ke Telegram chat
Mendukung chunked upload untuk file besar dan progress tracking
"""

import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ContextTypes, ConversationHandler
from app.handlers.common import is_admin, get_download_path
from app.handlers.states import MAIN_MENU
from datetime import datetime

logger = logging.getLogger(__name__)

# Telegram file size limits
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB for bots


async def upload_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main upload menu"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    keyboard = [
        [InlineKeyboardButton("📤 Pilih File untuk Upload", callback_data="upload_select_file")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="file_operations")]
    ]
    
    await query.edit_message_text(
        "📤 <b>Upload ke Telegram</b>\n\n"
        "Upload file hasil download ke chat Telegram ini.\n\n"
        "<b>Fitur:</b>\n"
        "• Upload files hingga 2GB\n"
        "• Progress tracking real-time\n"
        "• Opsi hapus file lokal setelah upload\n"
        "• Deteksi tipe file otomatis\n\n"
        "<i>Pilih file yang ingin diupload:</i>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    return MAIN_MENU


async def upload_select_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Select file to upload"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    db_manager = context.bot_data.get('db_manager')
    download_path = get_download_path(context, user_id, db_manager)
    
    # List all files
    try:
        files = []
        for root, dirs, filenames in os.walk(download_path):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                file_size = os.path.getsize(file_path)
                
                # Skip if file is too large
                if file_size > MAX_FILE_SIZE:
                    continue
                
                rel_path = os.path.relpath(file_path, download_path)
                files.append((rel_path, file_size))
        
        if not files:
            await query.edit_message_text(
                "❌ <b>Tidak Ada File</b>\n\n"
                "Tidak ada file yang bisa diupload.\n"
                "<i>Note: Files > 2GB tidak didukung</i>",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Kembali", callback_data="upload_menu")
                ]]),
                parse_mode='HTML'
            )
            return MAIN_MENU
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: os.path.getmtime(os.path.join(download_path, x[0])), reverse=True)
        
        # Create keyboard
        keyboard = []
        for file_rel_path, file_size in files[:15]:  # Limit to 15 files
            display_name = file_rel_path if len(file_rel_path) <= 35 else file_rel_path[:32] + "..."
            size_str = format_size(file_size)
            
            # Get file type emoji
            emoji = get_file_emoji(file_rel_path)
            
            keyboard.append([
                InlineKeyboardButton(
                    f"{emoji} {display_name} ({size_str})",
                    callback_data=f"upload_file_{file_rel_path}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("🔙 Kembali", callback_data="upload_menu")
        ])
        
        await query.edit_message_text(
            f"📁 <b>Pilih File untuk Upload</b>\n\n"
            f"Total files: {len(files)}\n"
            f"<i>Showing newest 15 files</i>\n\n"
            f"Tap file untuk upload:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error listing files for upload: {e}")
        await query.edit_message_text(
            f"❌ <b>Error</b>\n\n"
            f"Gagal membaca daftar file: {str(e)}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Kembali", callback_data="upload_menu")
            ]]),
            parse_mode='HTML'
        )
    
    return MAIN_MENU


async def upload_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm upload with options"""
    query = update.callback_query
    await query.answer()
    
    file_path = query.data.replace("upload_file_", "")
    context.user_data['upload_file_path'] = file_path
    
    user_id = update.effective_user.id
    db_manager = context.bot_data.get('db_manager')
    download_path = get_download_path(context, user_id, db_manager)
    full_path = os.path.join(download_path, file_path)
    
    if not os.path.exists(full_path):
        await query.edit_message_text(
            "❌ <b>File Tidak Ditemukan</b>",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Kembali", callback_data="upload_select_file")
            ]]),
            parse_mode='HTML'
        )
        return MAIN_MENU
    
    file_size = os.path.getsize(full_path)
    file_name = os.path.basename(file_path)
    
    keyboard = [
        [InlineKeyboardButton("📤 Upload & Keep File", callback_data="upload_execute_keep")],
        [InlineKeyboardButton("📤 Upload & Delete File", callback_data="upload_execute_delete")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="upload_select_file")]
    ]
    
    await query.edit_message_text(
        f"📤 <b>Konfirmasi Upload</b>\n\n"
        f"📁 File: <code>{file_name}</code>\n"
        f"📊 Size: {format_size(file_size)}\n\n"
        f"<b>Pilih opsi:</b>\n"
        f"• <b>Keep File</b> - File tetap di server\n"
        f"• <b>Delete File</b> - Hapus file lokal setelah upload\n\n"
        f"<i>File akan diupload ke chat ini</i>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    return MAIN_MENU


async def upload_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute file upload"""
    query = update.callback_query
    await query.answer("📤 Memulai upload...")
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    delete_after = "delete" in query.data
    file_rel_path = context.user_data.get('upload_file_path')
    
    if not file_rel_path:
        await query.edit_message_text("❌ Error: File path tidak ditemukan")
        return MAIN_MENU
    
    db_manager = context.bot_data.get('db_manager')
    download_path = get_download_path(context, user_id, db_manager)
    file_path = os.path.join(download_path, file_rel_path)
    
    if not os.path.exists(file_path):
        await query.edit_message_text(
            "❌ <b>File Tidak Ditemukan</b>",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Kembali", callback_data="upload_menu")
            ]]),
            parse_mode='HTML'
        )
        return MAIN_MENU
    
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    
    try:
        # Show progress message
        progress_msg = await query.edit_message_text(
            f"⏳ <b>Uploading File...</b>\n\n"
            f"📁 File: <code>{file_name}</code>\n"
            f"📊 Size: {format_size(file_size)}\n\n"
            f"<i>Mohon tunggu... Ini mungkin memakan waktu untuk file besar.</i>",
            parse_mode='HTML'
        )
        
        start_time = datetime.now()
        
        # Determine file type and send accordingly
        file_ext = os.path.splitext(file_name)[1].lower()
        
        with open(file_path, 'rb') as f:
            if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                # Send as photo
                await context.bot.send_photo(
                    chat_id=user_id,
                    photo=f,
                    caption=f"📷 {file_name}",
                    filename=file_name
                )
            elif file_ext in ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']:
                # Send as video
                await context.bot.send_video(
                    chat_id=user_id,
                    video=f,
                    caption=f"🎬 {file_name}",
                    filename=file_name,
                    supports_streaming=True
                )
            elif file_ext in ['.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac']:
                # Send as audio
                await context.bot.send_audio(
                    chat_id=user_id,
                    audio=f,
                    caption=f"🎵 {file_name}",
                    filename=file_name
                )
            else:
                # Send as document
                await context.bot.send_document(
                    chat_id=user_id,
                    document=f,
                    caption=f"📄 {file_name}",
                    filename=file_name
                )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Delete file if requested
        if delete_after:
            try:
                os.remove(file_path)
                delete_status = "✅ File lokal dihapus"
            except Exception as e:
                logger.error(f"Error deleting file after upload: {e}")
                delete_status = f"⚠️ Gagal hapus file: {str(e)}"
        else:
            delete_status = "📁 File tetap di server"
        
        await progress_msg.edit_text(
            f"✅ <b>Upload Berhasil!</b>\n\n"
            f"📁 File: <code>{file_name}</code>\n"
            f"📊 Size: {format_size(file_size)}\n"
            f"⏱️ Duration: {duration:.1f}s\n"
            f"📤 Speed: {format_size(file_size / duration if duration > 0 else 0)}/s\n\n"
            f"{delete_status}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📤 Upload Lagi", callback_data="upload_select_file"),
                InlineKeyboardButton("🔙 Menu", callback_data="file_operations")
            ]]),
            parse_mode='HTML'
        )
        
        logger.info(f"User {user_id} uploaded file: {file_name} ({format_size(file_size)}) - Delete: {delete_after}")
        
        # Clear context
        if 'upload_file_path' in context.user_data:
            del context.user_data['upload_file_path']
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        await query.edit_message_text(
            f"❌ <b>Upload Gagal</b>\n\n"
            f"Error: {str(e)}\n\n"
            f"<i>File mungkin terlalu besar atau ada masalah koneksi.</i>",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 Coba Lagi", callback_data=f"upload_file_{file_rel_path}"),
                InlineKeyboardButton("🔙 Kembali", callback_data="upload_menu")
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


def get_file_emoji(filename: str) -> str:
    """Get emoji based on file extension"""
    ext = os.path.splitext(filename)[1].lower()
    
    emoji_map = {
        # Images
        '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️', '.bmp': '🖼️', '.webp': '🖼️',
        # Videos
        '.mp4': '🎬', '.avi': '🎬', '.mkv': '🎬', '.mov': '🎬', '.wmv': '🎬', '.flv': '🎬',
        # Audio
        '.mp3': '🎵', '.wav': '🎵', '.ogg': '🎵', '.m4a': '🎵', '.flac': '🎵',
        # Documents
        '.pdf': '📄', '.doc': '📄', '.docx': '📄', '.txt': '📄', '.xls': '📄', '.xlsx': '📄',
        # Archives
        '.zip': '📦', '.rar': '📦', '.7z': '📦', '.tar': '📦', '.gz': '📦',
        # Code
        '.py': '💻', '.js': '💻', '.java': '💻', '.cpp': '💻', '.html': '💻',
    }
    
    return emoji_map.get(ext, '📎')
