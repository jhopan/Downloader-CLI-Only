from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from app.handlers.common import is_admin, show_main_menu
from app.handlers.states import MAIN_MENU
from app.handlers.download_handler import direct_download_menu
from app.handlers.schedule_handler import scheduled_download_menu
from app.handlers.settings_handler import (
    settings_menu, toggle_path_handler, set_custom_path_menu, download_history_handler
)
from app.handlers.status_handler import (
    download_status_handler, view_schedules_handler, 
    cancel_download_menu, cancel_download_confirm, cancel_schedule_confirm
)
from app.handlers.file_browser_handler import (
    file_browser_menu, show_all_files, show_categorized_files, show_storage_info,
    file_operations_menu, delete_file_menu, extract_archive_menu,
    confirm_delete_file, execute_delete_file, execute_extract_archive
)
from app.handlers.file_operations import (
    categorize_files_operation, confirm_clean_all, execute_clean_all
)
import logging

logger = logging.getLogger(__name__)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk semua inline button"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await query.edit_message_text("⛔ Maaf, Anda tidak memiliki akses ke bot ini.")
        return ConversationHandler.END
    
    data = query.data
    
    # Menu utama
    if data == "back_to_main":
        return await show_main_menu(update, context)
    
    # Download handlers
    elif data == "direct_download":
        return await direct_download_menu(update, context)
    
    elif data == "scheduled_download":
        return await scheduled_download_menu(update, context)
    
    # Status handlers
    elif data == "download_status":
        return await download_status_handler(update, context)
    
    elif data == "view_schedules":
        return await view_schedules_handler(update, context)
    
    elif data == "cancel_download":
        return await cancel_download_menu(update, context)
    
    # Settings handlers
    elif data == "settings":
        return await settings_menu(update, context)
    
    elif data == "toggle_path":
        return await toggle_path_handler(update, context)
    
    elif data == "set_custom_path":
        return await set_custom_path_menu(update, context)
    
    elif data == "download_history":
        return await download_history_handler(update, context)
    
    # File browser handlers
    elif data == "file_browser":
        return await file_browser_menu(update, context)
    
    elif data == "files_all":
        return await show_all_files(update, context)
    
    elif data == "files_categorized":
        return await show_categorized_files(update, context)
    
    elif data == "files_storage":
        return await show_storage_info(update, context)
    
    # File operations handlers
    elif data == "file_operations":
        return await file_operations_menu(update, context)
    
    elif data == "file_op_delete":
        return await delete_file_menu(update, context)
    
    elif data == "file_op_extract":
        return await extract_archive_menu(update, context)
    
    elif data.startswith("delete_file_"):
        filename = data.replace("delete_file_", "")
        return await confirm_delete_file(update, context, filename)
    
    elif data.startswith("confirm_delete_"):
        filename = data.replace("confirm_delete_", "")
        return await execute_delete_file(update, context, filename)
    
    elif data.startswith("extract_"):
        filename = data.replace("extract_", "")
        return await execute_extract_archive(update, context, filename)
    
    elif data == "file_op_categorize":
        return await categorize_files_operation(update, context)
    
    elif data == "file_op_clean_all":
        return await confirm_clean_all(update, context)
    
    elif data == "confirm_clean_all_yes":
        return await execute_clean_all(update, context)
    
    # Cancel actions
    elif data.startswith("cancel_"):
        if data.startswith("cancel_schedule_"):
            schedule_id = data.replace("cancel_schedule_", "")
            return await cancel_schedule_confirm(update, context, schedule_id)
        else:
            download_id = data.replace("cancel_", "")
            return await cancel_download_confirm(update, context, download_id)
    
    return MAIN_MENU
