from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Tuple


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Keyboard untuk menu utama"""
    keyboard = [
        [InlineKeyboardButton("📥 Unduh Langsung", callback_data="direct_download")],
        [InlineKeyboardButton("⏰ Unduh Berjadwal", callback_data="scheduled_download")],
        [InlineKeyboardButton("📊 Status Unduhan", callback_data="download_status")],
        [InlineKeyboardButton("📜 Riwayat Unduhan", callback_data="download_history")],
        [InlineKeyboardButton("📋 Lihat Jadwal", callback_data="view_schedules")],
        [InlineKeyboardButton("⚙️ Pengaturan", callback_data="settings")],
        [InlineKeyboardButton("❌ Batalkan Unduhan", callback_data="cancel_download")],
    ]
    return InlineKeyboardMarkup(keyboard)


def back_to_main_keyboard() -> InlineKeyboardMarkup:
    """Keyboard kembali ke menu utama"""
    keyboard = [[InlineKeyboardButton("🔙 Kembali ke Menu", callback_data="back_to_main")]]
    return InlineKeyboardMarkup(keyboard)


def back_button_keyboard() -> InlineKeyboardMarkup:
    """Keyboard dengan tombol kembali"""
    keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="back_to_main")]]
    return InlineKeyboardMarkup(keyboard)


def settings_keyboard(use_custom_path: bool = False) -> InlineKeyboardMarkup:
    """Keyboard untuk pengaturan"""
    status_text = "✅ Custom" if use_custom_path else "📁 Default"
    
    keyboard = [
        [InlineKeyboardButton(f"📍 Lokasi Unduhan: {status_text}", callback_data="toggle_path")],
        [InlineKeyboardButton("📝 Atur Lokasi Custom", callback_data="set_custom_path")],
        [InlineKeyboardButton("📜 Riwayat Unduhan", callback_data="download_history")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def confirm_keyboard(action: str) -> InlineKeyboardMarkup:
    """Keyboard konfirmasi"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Ya", callback_data=f"confirm_{action}"),
            InlineKeyboardButton("❌ Tidak", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def cancel_download_keyboard(downloads: dict) -> InlineKeyboardMarkup:
    """Keyboard untuk batalkan unduhan"""
    keyboard = []
    
    for download_id, info in downloads.items():
        filename = info['filename']
        if len(filename) > 30:
            filename = filename[:27] + "..."
        
        keyboard.append([
            InlineKeyboardButton(
                f"❌ {filename}",
                callback_data=f"cancel_{download_id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="back_to_main")])
    return InlineKeyboardMarkup(keyboard)


def cancel_schedule_keyboard(schedules: list) -> InlineKeyboardMarkup:
    """Keyboard untuk batalkan jadwal"""
    keyboard = []
    
    for schedule in schedules:
        schedule_id = schedule['schedule_id']
        url = schedule['url']
        if len(url) > 30:
            url = url[:27] + "..."
        
        keyboard.append([
            InlineKeyboardButton(
                f"❌ {url}",
                callback_data=f"cancel_schedule_{schedule_id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="back_to_main")])
    return InlineKeyboardMarkup(keyboard)


def refresh_and_back_keyboard(refresh_action: str) -> InlineKeyboardMarkup:
    """Keyboard dengan refresh dan kembali"""
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data=refresh_action)],
        [InlineKeyboardButton("🔙 Kembali", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)
