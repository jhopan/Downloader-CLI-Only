import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler

logger = logging.getLogger(__name__)

# Conversation states
AWAITING_SPEED_LIMIT, AWAITING_SCHEDULE_START, AWAITING_SCHEDULE_END, AWAITING_SCHEDULE_SPEED = range(4)


async def bandwidth_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bandwidth settings menu"""
    user_id = update.effective_user.id
    db_manager = context.bot_data.get('db_manager')
    
    if not db_manager:
        await update.message.reply_text("❌ System error")
        return
    
    settings = db_manager.get_bandwidth_settings(user_id)
    
    if settings:
        current_limit = settings['max_speed_kbps']
        schedule_enabled = settings['schedule_enabled']
        schedule_text = ""
        
        if schedule_enabled and settings['schedule_start_time']:
            schedule_text = (
                f"\n<b>📅 Schedule:</b> Enabled\n"
                f"   Time: {settings['schedule_start_time']} - {settings['schedule_end_time']}\n"
                f"   Speed: {settings['schedule_speed_kbps']} KB/s"
            )
    else:
        current_limit = 0
        schedule_text = ""
    
    limit_text = f"{current_limit} KB/s" if current_limit > 0 else "Unlimited"
    
    keyboard = [
        [InlineKeyboardButton("⚡ Set Speed Limit", callback_data="bw_set_limit")],
        [InlineKeyboardButton("📅 Schedule Limit", callback_data="bw_schedule")],
        [InlineKeyboardButton("🔄 Reset to Unlimited", callback_data="bw_reset")],
    ]
    
    await update.message.reply_text(
        f"🌐 <b>Bandwidth Settings</b>\n\n"
        f"<b>Current Limit:</b> {limit_text}{schedule_text}\n\n"
        f"Choose an option:",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def bandwidth_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle bandwidth button callbacks"""
    query = update.callback_query
    await query.answer()
    
    action = query.data.split('_', 2)[2] if '_' in query.data else query.data
    
    if action == 'set_limit' or query.data == 'bw_set_limit':
        await query.edit_message_text(
            "⚡ <b>Set Speed Limit</b>\n\n"
            "Masukkan batas kecepatan download dalam KB/s\n"
            "Contoh:\n"
            "  <code>500</code> = 500 KB/s (~0.5 MB/s)\n"
            "  <code>1024</code> = 1024 KB/s (1 MB/s)\n"
            "  <code>5120</code> = 5120 KB/s (5 MB/s)\n\n"
            "Kirim /cancel untuk membatalkan.",
            parse_mode='HTML'
        )
        return AWAITING_SPEED_LIMIT
    
    elif action == 'schedule' or query.data == 'bw_schedule':
        await query.edit_message_text(
            "📅 <b>Schedule Bandwidth Limit</b>\n\n"
            "Atur batas kecepatan berdasarkan waktu.\n"
            "Berguna untuk menghemat bandwidth di jam tertentu.\n\n"
            "Masukkan waktu MULAI (format 24 jam)\n"
            "Contoh: <code>09:00</code>\n\n"
            "Kirim /cancel untuk membatalkan.",
            parse_mode='HTML'
        )
        return AWAITING_SCHEDULE_START
    
    elif action == 'reset' or query.data == 'bw_reset':
        user_id = query.from_user.id
        db_manager = context.bot_data.get('db_manager')
        
        if db_manager:
            db_manager.set_bandwidth_limit(user_id, 0)
            db_manager.set_bandwidth_schedule(user_id, False, '', '', 0)
        
        await query.edit_message_text(
            "✅ <b>Bandwidth Reset</b>\n\n"
            "Batas kecepatan diatur ke unlimited.",
            parse_mode='HTML'
        )
        return ConversationHandler.END


async def receive_speed_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive speed limit input"""
    try:
        speed = int(update.message.text.strip())
        
        if speed < 0:
            raise ValueError("Speed must be positive")
        
        user_id = update.effective_user.id
        db_manager = context.bot_data.get('db_manager')
        
        if db_manager:
            db_manager.set_bandwidth_limit(user_id, speed)
        
        await update.message.reply_text(
            f"✅ <b>Speed Limit Set</b>\n\n"
            f"Kecepatan download dibatasi: <b>{speed} KB/s</b>\n"
            f"({speed / 1024:.2f} MB/s)",
            parse_mode='HTML'
        )
        
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text(
            "❌ Input tidak valid. Masukkan angka (dalam KB/s)\n"
            "Contoh: <code>1024</code> untuk 1 MB/s",
            parse_mode='HTML'
        )
        return AWAITING_SPEED_LIMIT


async def receive_schedule_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive schedule start time"""
    try:
        time_str = update.message.text.strip()
        time_parts = time_str.split(':')
        
        if len(time_parts) != 2:
            raise ValueError("Invalid format")
        
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("Invalid time range")
        
        # Save start time
        context.user_data['schedule_start'] = f"{hour:02d}:{minute:02d}"
        
        await update.message.reply_text(
            "📅 <b>Schedule Bandwidth Limit</b>\n\n"
            f"Waktu MULAI: <code>{context.user_data['schedule_start']}</code>\n\n"
            "Masukkan waktu SELESAI (format 24 jam)\n"
            "Contoh: <code>17:00</code>",
            parse_mode='HTML'
        )
        
        return AWAITING_SCHEDULE_END
        
    except Exception:
        await update.message.reply_text(
            "❌ Format waktu tidak valid.\n"
            "Gunakan format: <code>HH:MM</code>\n"
            "Contoh: <code>09:00</code>",
            parse_mode='HTML'
        )
        return AWAITING_SCHEDULE_START


async def receive_schedule_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive schedule end time"""
    try:
        time_str = update.message.text.strip()
        time_parts = time_str.split(':')
        
        if len(time_parts) != 2:
            raise ValueError("Invalid format")
        
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("Invalid time range")
        
        # Save end time
        context.user_data['schedule_end'] = f"{hour:02d}:{minute:02d}"
        
        await update.message.reply_text(
            "📅 <b>Schedule Bandwidth Limit</b>\n\n"
            f"Waktu MULAI: <code>{context.user_data['schedule_start']}</code>\n"
            f"Waktu SELESAI: <code>{context.user_data['schedule_end']}</code>\n\n"
            "Masukkan batas kecepatan (KB/s) untuk periode ini\n"
            "Contoh: <code>500</code> untuk 500 KB/s",
            parse_mode='HTML'
        )
        
        return AWAITING_SCHEDULE_SPEED
        
    except Exception:
        await update.message.reply_text(
            "❌ Format waktu tidak valid.\n"
            "Gunakan format: <code>HH:MM</code>\n"
            "Contoh: <code>17:00</code>",
            parse_mode='HTML'
        )
        return AWAITING_SCHEDULE_END


async def receive_schedule_speed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive schedule speed limit"""
    try:
        speed = int(update.message.text.strip())
        
        if speed < 0:
            raise ValueError("Speed must be positive")
        
        user_id = update.effective_user.id
        db_manager = context.bot_data.get('db_manager')
        
        start_time = context.user_data['schedule_start']
        end_time = context.user_data['schedule_end']
        
        if db_manager:
            db_manager.set_bandwidth_schedule(
                user_id, True, start_time, end_time, speed
            )
        
        await update.message.reply_text(
            f"✅ <b>Bandwidth Schedule Set</b>\n\n"
            f"<b>Periode:</b> {start_time} - {end_time}\n"
            f"<b>Speed Limit:</b> {speed} KB/s ({speed / 1024:.2f} MB/s)\n\n"
            f"Download akan otomatis dibatasi pada periode tersebut.",
            parse_mode='HTML'
        )
        
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text(
            "❌ Input tidak valid. Masukkan angka (dalam KB/s)\n"
            "Contoh: <code>500</code> untuk 500 KB/s",
            parse_mode='HTML'
        )
        return AWAITING_SCHEDULE_SPEED


async def cancel_bandwidth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel bandwidth configuration"""
    await update.message.reply_text("❌ Dibatalkan.", parse_mode='HTML')
    return ConversationHandler.END


# Create conversation handler for bandwidth settings
bandwidth_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler('bandwidth', bandwidth_command),
        CallbackQueryHandler(bandwidth_callback, pattern='^bw_')
    ],
    states={
        AWAITING_SPEED_LIMIT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_speed_limit)
        ],
        AWAITING_SCHEDULE_START: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_schedule_start)
        ],
        AWAITING_SCHEDULE_END: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_schedule_end)
        ],
        AWAITING_SCHEDULE_SPEED: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_schedule_speed)
        ],
    },
    fallbacks=[CommandHandler('cancel', cancel_bandwidth)],
)
