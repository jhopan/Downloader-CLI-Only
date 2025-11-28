from telegram import Update
from telegram.ext import ContextTypes
from app.keyboards.inline_keyboards import main_menu_keyboard
import config


def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in config.ADMIN_IDS


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                        edit_message: bool = True) -> int:
    """Tampilkan menu utama"""
    from app.handlers.states import MAIN_MENU
    
    reply_markup = main_menu_keyboard()
    
    welcome_text = (
        "🤖 <b>Bot Pengunduh Otomatis</b>\n\n"
        "Selamat datang! Pilih menu di bawah ini:\n\n"
        "📥 <b>Unduh Langsung</b> - Unduh file sekarang juga\n"
        "⏰ <b>Unduh Berjadwal</b> - Jadwalkan unduhan untuk nanti\n"
        "📊 <b>Status Unduhan</b> - Lihat status unduhan aktif\n"
        "📋 <b>Lihat Jadwal</b> - Lihat daftar jadwal unduhan\n"
        "⚙️ <b>Pengaturan</b> - Atur lokasi download & lainnya\n"
        "❌ <b>Batalkan Unduhan</b> - Batalkan unduhan yang sedang berjalan"
    )
    
    if edit_message and update.callback_query:
        await update.callback_query.edit_message_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    elif update.message:
        msg = await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        context.user_data['main_message_id'] = msg.message_id
    
    return MAIN_MENU


def get_download_path(context: ContextTypes.DEFAULT_TYPE, user_id: int, db_manager) -> str:
    """Get download path untuk user"""
    if db_manager:
        return db_manager.get_download_path(user_id, config.DEFAULT_DOWNLOAD_DIR)
    return config.DEFAULT_DOWNLOAD_DIR


async def delete_user_message(update: Update):
    """Hapus pesan user untuk keep chat clean"""
    try:
        if update.message:
            await update.message.delete()
    except:
        pass
