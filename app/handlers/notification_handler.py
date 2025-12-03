"""
Handler untuk menu pengaturan notifikasi kustom
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.handlers.states import WAITING_NOTIFICATION_MESSAGE, MAIN_MENU

async def notification_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main notification settings menu"""
    query = update.callback_query
    await query.answer()
    
    # Get notification manager from context
    notif_manager = context.bot_data.get('notification_manager')
    if not notif_manager:
        await query.edit_message_text("❌ Notification manager tidak tersedia")
        return ConversationHandler.END
    
    events = notif_manager.get_event_list()
    
    keyboard = []
    for event_type, settings in events.items():
        status = "✅" if settings["enabled"] else "❌"
        sound = "🔔" if settings.get("sound", False) else "🔕"
        display_name = notif_manager.get_event_display_name(event_type)
        
        keyboard.append([
            InlineKeyboardButton(
                f"{status} {sound} {display_name}",
                callback_data=f"notif_detail_{event_type}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton("🔄 Reset ke Default", callback_data="notif_reset")
    ])
    keyboard.append([
        InlineKeyboardButton("⬅️ Kembali", callback_data="settings_menu")
    ])
    
    text = (
        "🔔 <b>Pengaturan Notifikasi</b>\n\n"
        "Atur notifikasi untuk berbagai event:\n"
        "✅ = Aktif | ❌ = Nonaktif\n"
        "🔔 = Suara ON | 🔕 = Suara OFF\n\n"
        "Tap event untuk mengatur detailnya:"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    return MAIN_MENU

async def notification_event_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detail settings for specific event"""
    query = update.callback_query
    await query.answer()
    
    event_type = query.data.replace("notif_detail_", "")
    context.user_data['current_event'] = event_type
    
    notif_manager = context.bot_data.get('notification_manager')
    event_settings = notif_manager.get_event_setting(event_type)
    
    if not event_settings:
        await query.edit_message_text("❌ Event tidak ditemukan")
        return NOTIF_MENU
    
    display_name = notif_manager.get_event_display_name(event_type)
    enabled_status = "✅ Aktif" if event_settings["enabled"] else "❌ Nonaktif"
    sound_status = "🔔 ON" if event_settings.get("sound", False) else "🔕 OFF"
    
    keyboard = [
        [
            InlineKeyboardButton(
                f"{'❌ Nonaktifkan' if event_settings['enabled'] else '✅ Aktifkan'}",
                callback_data=f"notif_toggle_{event_type}"
            )
        ],
        [
            InlineKeyboardButton(
                f"{'🔕 Matikan Suara' if event_settings.get('sound', False) else '🔔 Nyalakan Suara'}",
                callback_data=f"notif_sound_{event_type}"
            )
        ],
        [
            InlineKeyboardButton(
                "✏️ Edit Pesan",
                callback_data=f"notif_edit_{event_type}"
            )
        ],
        [
            InlineKeyboardButton("⬅️ Kembali", callback_data="notification_settings")
        ]
    ]
    
    text = (
        f"🔔 <b>{display_name}</b>\n\n"
        f"Status: {enabled_status}\n"
        f"Suara: {sound_status}\n\n"
        f"<b>Pesan saat ini:</b>\n"
        f"<code>{event_settings['message']}</code>\n\n"
        f"<i>Variables yang tersedia:</i>\n"
        f"{_get_available_variables(event_type)}"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    return MAIN_MENU

async def notification_toggle_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle event enabled/disabled"""
    query = update.callback_query
    await query.answer()
    
    event_type = query.data.replace("notif_toggle_", "")
    notif_manager = context.bot_data.get('notification_manager')
    
    new_status = notif_manager.toggle_event(event_type)
    status_text = "diaktifkan" if new_status else "dinonaktifkan"
    
    await query.answer(f"Notifikasi {status_text}!", show_alert=True)
    
    # Refresh detail view
    context.user_data['current_event'] = event_type
    return await notification_event_detail(update, context)

async def notification_toggle_sound(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle sound for event"""
    query = update.callback_query
    await query.answer()
    
    event_type = query.data.replace("notif_sound_", "")
    notif_manager = context.bot_data.get('notification_manager')
    
    new_status = notif_manager.toggle_sound(event_type)
    status_text = "dinyalakan" if new_status else "dimatikan"
    
    await query.answer(f"Suara notifikasi {status_text}!", show_alert=True)
    
    # Refresh detail view
    context.user_data['current_event'] = event_type
    return await notification_event_detail(update, context)

async def notification_edit_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start editing notification message"""
    query = update.callback_query
    await query.answer()
    
    event_type = query.data.replace("notif_edit_", "")
    context.user_data['editing_event'] = event_type
    
    notif_manager = context.bot_data.get('notification_manager')
    event_settings = notif_manager.get_event_setting(event_type)
    display_name = notif_manager.get_event_display_name(event_type)
    
    keyboard = [[
        InlineKeyboardButton("❌ Batal", callback_data=f"notif_detail_{event_type}")
    ]]
    
    text = (
        f"✏️ <b>Edit Pesan: {display_name}</b>\n\n"
        f"<b>Pesan saat ini:</b>\n"
        f"<code>{event_settings['message']}</code>\n\n"
        f"<b>Variables yang tersedia:</b>\n"
        f"{_get_available_variables(event_type)}\n\n"
        f"Kirim pesan baru Anda sekarang:"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    return WAITING_NOTIFICATION_MESSAGE

async def notification_save_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save edited notification message"""
    new_message = update.message.text
    event_type = context.user_data.get('editing_event')
    
    if not event_type:
        await update.message.reply_text("❌ Error: Event tidak ditemukan")
        return NOTIF_MENU
    
    notif_manager = context.bot_data.get('notification_manager')
    notif_manager.update_event_setting(event_type, message=new_message)
    
    display_name = notif_manager.get_event_display_name(event_type)
    
    keyboard = [[
        InlineKeyboardButton("✅ OK", callback_data=f"notif_detail_{event_type}")
    ]]
    
    await update.message.reply_text(
        f"✅ Pesan untuk <b>{display_name}</b> berhasil diperbarui!\n\n"
        f"<b>Pesan baru:</b>\n"
        f"<code>{new_message}</code>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    return MAIN_MENU

async def notification_reset_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm reset to default"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Ya, Reset", callback_data="notif_reset_confirm"),
            InlineKeyboardButton("❌ Batal", callback_data="notification_settings")
        ]
    ]
    
    text = (
        "⚠️ <b>Reset ke Default?</b>\n\n"
        "Semua pengaturan notifikasi akan dikembalikan ke default.\n"
        "Yakin ingin melanjutkan?"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    return MAIN_MENU

async def notification_reset_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute reset to default"""
    query = update.callback_query
    await query.answer()
    
    notif_manager = context.bot_data.get('notification_manager')
    notif_manager.reset_to_default()
    
    await query.answer("✅ Reset berhasil!", show_alert=True)
    
    return await notification_settings_menu(update, context)

def _get_available_variables(event_type: str) -> str:
    """Get available variables for event type"""
    variables = {
        "download_complete": "{filename}, {size}, {duration}",
        "download_start": "{url}, {filename}",
        "download_error": "{filename}, {error}",
        "download_retry": "{attempt}, {max_attempts}, {filename}, {delay}",
        "schedule_created": "{schedule_time}, {url}",
        "schedule_triggered": "{schedule_time}, {filename}",
        "extraction_complete": "{filename}, {extract_path}",
        "extraction_error": "{filename}, {error}"
    }
    return f"<code>{variables.get(event_type, 'Tidak ada')}</code>"
