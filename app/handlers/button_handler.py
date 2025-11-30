from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from app.handlers.common import is_admin
from app.handlers.states import MAIN_MENU
from app.handlers.menu_handler import (
    show_main_menu, show_download_menu, show_status_menu, show_smart_menu,
    show_security_menu, show_files_menu, show_settings_menu, show_help
)
# Smart features menus
from app.handlers.smart_menus import (
    queue_management_menu, queue_status_menu, file_preview_menu,
    duplicate_check_menu, smart_categorize_menu, cloud_manager_menu,
    cloud_download_menu, statistics_dashboard_menu
)
# Security menus
from app.handlers.security_menus import (
    virus_scan_menu, encrypt_file_menu, decrypt_file_menu,
    scan_history_menu, encrypted_files_menu, resume_download_menu
)
# Advanced menus
from app.handlers.advanced_menus import batch_download_menu, bandwidth_menu

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
    
    # ========== MAIN MENU NAVIGATION ==========
    if data == "back_to_main":
        return await show_main_menu(update, context)
    
    # Main menu categories
    elif data == "menu_download":
        return await show_download_menu(update, context)
    
    elif data == "menu_status":
        return await show_status_menu(update, context)
    
    elif data == "menu_smart":
        return await show_smart_menu(update, context)
    
    elif data == "menu_security":
        return await show_security_menu(update, context)
    
    elif data == "menu_files":
        return await show_files_menu(update, context)
    
    elif data == "menu_settings":
        return await show_settings_menu(update, context)
    
    elif data == "show_help":
        return await show_help(update, context)
    
    # ========== DOWNLOAD MENU ==========
    elif data == "download_direct":
        return await direct_download_menu(update, context)
    
    elif data == "download_batch":
        return await batch_download_menu(update, context)
    
    elif data == "download_schedule":
        return await scheduled_download_menu(update, context)
    
    elif data == "download_cloud":
        return await cloud_download_menu(update, context)
    
    elif data == "download_resume":
        return await resume_download_menu(update, context)
    
    elif data == "download_bandwidth":
        return await bandwidth_menu(update, context)
    
    # ========== STATUS MENU ==========
    elif data == "status_active":
        return await download_status_handler(update, context)
    
    elif data == "status_history":
        return await download_history_handler(update, context)
    
    elif data == "status_schedules":
        return await view_schedules_handler(update, context)
    
    elif data == "status_queue":
        from app.handlers.smart_features_handler import queue_status_menu
        return await queue_status_menu(update, context)
    
    elif data == "status_cancel":
        return await cancel_download_menu(update, context)
    
    # ========== SMART FEATURES MENU ==========
    elif data == "smart_queue":
        return await queue_management_menu(update, context)
    
    elif data == "smart_preview":
        return await file_preview_menu(update, context)
    
    elif data == "smart_duplicate":
        return await duplicate_check_menu(update, context)
    
    elif data == "smart_categorize":
        return await smart_categorize_menu(update, context)
    
    elif data == "smart_cloud":
        return await cloud_manager_menu(update, context)
    
    elif data == "smart_dashboard":
        return await statistics_dashboard_menu(update, context)
    
    elif data == "show_stats":
        return await statistics_dashboard_menu(update, context)
    
    # ========== SECURITY MENU ==========
    elif data == "security_scan":
        return await virus_scan_menu(update, context)
    
    elif data == "security_encrypt":
        return await encrypt_file_menu(update, context)
    
    elif data == "security_decrypt":
        return await decrypt_file_menu(update, context)
    
    elif data == "security_scan_history":
        return await scan_history_menu(update, context)
    
    elif data == "security_encrypted_files":
        return await encrypted_files_menu(update, context)
    
    elif data == "security_resume":
        return await resume_download_menu(update, context)
    
    # ========== FILE MANAGER MENU ==========
    elif data == "files_list_all":
        return await show_all_files(update, context)
    
    elif data == "files_by_category":
        return await show_categorized_files(update, context)
    
    elif data == "files_delete":
        return await delete_file_menu(update, context)
    
    elif data == "files_extract":
        return await extract_archive_menu(update, context)
    
    elif data == "files_categorize":
        return await categorize_files_operation(update, context)
    
    elif data == "files_clean_all":
        return await confirm_clean_all(update, context)
    
    elif data == "files_storage":
        return await show_storage_info(update, context)
    
    # ========== OLD HANDLERS (backward compatibility) ==========
    elif data == "direct_download":
        return await direct_download_menu(update, context)
    
    elif data == "scheduled_download":
        return await scheduled_download_menu(update, context)
    
    elif data == "download_status":
        return await download_status_handler(update, context)
    
    elif data == "view_schedules":
        return await view_schedules_handler(update, context)
    
    elif data == "cancel_download":
        return await cancel_download_menu(update, context)
    
    elif data == "settings":
        return await settings_menu(update, context)
    
    elif data == "toggle_path":
        return await toggle_path_handler(update, context)
    
    elif data == "set_custom_path":
        return await set_custom_path_menu(update, context)
    
    elif data == "download_history":
        return await download_history_handler(update, context)
    
    elif data == "file_browser":
        return await file_browser_menu(update, context)
    
    elif data == "files_all":
        return await show_all_files(update, context)
    
    elif data == "files_categorized":
        return await show_categorized_files(update, context)
    
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
