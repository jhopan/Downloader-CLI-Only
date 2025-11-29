import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from datetime import datetime, timedelta
import uuid
import asyncio

logger = logging.getLogger(__name__)

# Conversation states
AWAITING_URLS, AWAITING_SCHEDULE_URL, AWAITING_SCHEDULE_TIME = range(3)


async def multi_download_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /batch - multi URL download"""
    await update.message.reply_text(
        "📥 <b>Batch Download</b>\n\n"
        "Kirimkan beberapa URL untuk didownload sekaligus.\n"
        "Format: Satu URL per baris\n\n"
        "<b>Contoh:</b>\n"
        "<code>https://example.com/file1.zip\n"
        "https://example.com/file2.mp4\n"
        "https://example.com/file3.pdf</code>\n\n"
        "Kirim /cancel untuk membatalkan.",
        parse_mode='HTML'
    )
    return AWAITING_URLS


async def receive_urls(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive multiple URLs dan mulai batch download"""
    text = update.message.text.strip()
    urls = [url.strip() for url in text.split('\n') if url.strip()]
    
    # Filter valid URLs
    valid_urls = [url for url in urls if url.startswith(('http://', 'https://'))]
    
    if not valid_urls:
        await update.message.reply_text(
            "❌ Tidak ada URL valid yang ditemukan.\n"
            "Pastikan setiap URL dimulai dengan http:// atau https://",
            parse_mode='HTML'
        )
        return AWAITING_URLS
    
    if len(valid_urls) > 20:
        await update.message.reply_text(
            "⚠️ Maksimal 20 URL per batch.\n"
            f"Anda mengirim {len(valid_urls)} URL.\n"
            "Silakan kirim ulang dengan max 20 URL.",
            parse_mode='HTML'
        )
        return AWAITING_URLS
    
    # Create batch
    batch_id = str(uuid.uuid4())[:8]
    user_id = update.effective_user.id
    
    # Get download manager from context
    download_manager = context.bot_data.get('download_manager')
    db_manager = context.bot_data.get('db_manager')
    download_dir = context.bot_data.get('download_dir', './downloads')
    
    if not download_manager or not db_manager:
        await update.message.reply_text("❌ System error. Please try again later.")
        return ConversationHandler.END
    
    # Get user's download path
    download_path = db_manager.get_download_path(user_id, download_dir)
    
    # Save batch to database
    db_manager.add_batch_download(user_id, batch_id, len(valid_urls))
    
    # Send confirmation
    msg = await update.message.reply_text(
        f"📦 <b>Batch Download Created</b>\n\n"
        f"<b>Batch ID:</b> <code>{batch_id}</code>\n"
        f"<b>Total URLs:</b> {len(valid_urls)}\n\n"
        f"Starting downloads...",
        parse_mode='HTML'
    )
    
    # Start downloads
    download_ids = []
    for i, url in enumerate(valid_urls, 1):
        try:
            # Progress callback untuk update message
            async def progress_callback(dl_id, progress, downloaded, total, speed, completed=False):
                pass  # No individual progress for batch
            
            download_id = await download_manager.start_download(
                url=url,
                download_dir=download_path,
                user_id=user_id,
                progress_callback=progress_callback
            )
            
            # Add to batch
            db_manager.add_batch_item(batch_id, url, download_id)
            download_ids.append(download_id)
            
        except Exception as e:
            logger.error(f"Failed to start download {i}/{len(valid_urls)}: {e}")
            db_manager.add_batch_item(batch_id, url, f"error_{i}")
            db_manager.update_batch_item_status(
                batch_id, f"error_{i}", 'failed', error_message=str(e)
            )
    
    # Start monitoring task
    asyncio.create_task(monitor_batch(
        context, batch_id, user_id, msg.chat_id, msg.message_id,
        download_manager, db_manager
    ))
    
    return ConversationHandler.END


async def monitor_batch(context, batch_id, user_id, chat_id, message_id,
                       download_manager, db_manager):
    """Monitor batch download progress"""
    while True:
        await asyncio.sleep(5)  # Check every 5 seconds
        
        batch_info = db_manager.get_batch_info(batch_id)
        if not batch_info:
            break
        
        # Check if all completed
        if batch_info['status'] == 'completed':
            # Send final update
            completed = batch_info['completed_urls']
            failed = batch_info['failed_urls']
            total = batch_info['total_urls']
            
            text = (
                f"✅ <b>Batch Download Completed!</b>\n\n"
                f"<b>Batch ID:</b> <code>{batch_id}</code>\n"
                f"<b>Total:</b> {total}\n"
                f"<b>✅ Success:</b> {completed}\n"
                f"<b>❌ Failed:</b> {failed}\n\n"
            )
            
            if failed > 0:
                text += "<b>Failed URLs:</b>\n"
                for item in batch_info['items']:
                    if item['status'] == 'failed':
                        text += f"• {item['url'][:50]}...\n"
            
            keyboard = [[
                InlineKeyboardButton("📋 View Details", callback_data=f"batch_detail:{batch_id}")
            ]]
            
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=text,
                    parse_mode='HTML',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except:
                pass
            
            break
        else:
            # Update progress
            completed = batch_info['completed_urls']
            failed = batch_info['failed_urls']
            total = batch_info['total_urls']
            in_progress = total - completed - failed
            
            text = (
                f"📦 <b>Batch Download Progress</b>\n\n"
                f"<b>Batch ID:</b> <code>{batch_id}</code>\n"
                f"<b>Progress:</b> {completed + failed}/{total}\n"
                f"<b>✅ Completed:</b> {completed}\n"
                f"<b>⏳ In Progress:</b> {in_progress}\n"
                f"<b>❌ Failed:</b> {failed}"
            )
            
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=text,
                    parse_mode='HTML'
                )
            except:
                pass


async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /schedule - scheduled download"""
    await update.message.reply_text(
        "⏰ <b>Schedule Download</b>\n\n"
        "Kirimkan URL yang ingin dijadwalkan.\n\n"
        "Kirim /cancel untuk membatalkan.",
        parse_mode='HTML'
    )
    return AWAITING_SCHEDULE_URL


async def receive_schedule_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive URL untuk scheduled download"""
    url = update.message.text.strip()
    
    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text(
            "❌ URL tidak valid. Harus dimulai dengan http:// atau https://",
            parse_mode='HTML'
        )
        return AWAITING_SCHEDULE_URL
    
    # Save URL in context
    context.user_data['schedule_url'] = url
    
    # Show time options
    now = datetime.now()
    keyboard = [
        [InlineKeyboardButton("⏰ 1 jam lagi", callback_data="schedule_time:1h")],
        [InlineKeyboardButton("⏰ 3 jam lagi", callback_data="schedule_time:3h")],
        [InlineKeyboardButton("⏰ 6 jam lagi", callback_data="schedule_time:6h")],
        [InlineKeyboardButton("⏰ 12 jam lagi", callback_data="schedule_time:12h")],
        [InlineKeyboardButton("📅 Besok pagi (08:00)", callback_data="schedule_time:tomorrow")],
        [InlineKeyboardButton("✏️ Custom Time", callback_data="schedule_time:custom")]
    ]
    
    await update.message.reply_text(
        "⏰ <b>Pilih Waktu Download</b>\n\n"
        f"<b>URL:</b> {url[:50]}...\n\n"
        "Pilih waktu atau ketik format: <code>HH:MM</code> (24 jam)\n"
        "Contoh: <code>14:30</code> untuk jam 2:30 siang",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return AWAITING_SCHEDULE_TIME


async def receive_schedule_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive custom time untuk schedule"""
    time_str = update.message.text.strip()
    
    try:
        # Parse time (HH:MM)
        time_parts = time_str.split(':')
        if len(time_parts) != 2:
            raise ValueError("Invalid format")
        
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("Invalid time range")
        
        # Create scheduled time
        now = datetime.now()
        scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If time already passed today, schedule for tomorrow
        if scheduled_time <= now:
            scheduled_time += timedelta(days=1)
        
        # Create schedule
        await create_schedule(update, context, scheduled_time)
        
        return ConversationHandler.END
        
    except Exception as e:
        await update.message.reply_text(
            "❌ Format waktu tidak valid.\n"
            "Gunakan format: <code>HH:MM</code>\n"
            "Contoh: <code>14:30</code>",
            parse_mode='HTML'
        )
        return AWAITING_SCHEDULE_TIME


async def schedule_time_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle schedule time button callback"""
    query = update.callback_query
    await query.answer()
    
    time_option = query.data.split(':')[1]
    now = datetime.now()
    
    if time_option == 'custom':
        await query.edit_message_text(
            "✏️ <b>Custom Time</b>\n\n"
            "Ketik waktu dalam format: <code>HH:MM</code>\n"
            "Contoh: <code>14:30</code> untuk jam 2:30 siang",
            parse_mode='HTML'
        )
        return AWAITING_SCHEDULE_TIME
    
    # Calculate scheduled time
    if time_option.endswith('h'):
        hours = int(time_option[:-1])
        scheduled_time = now + timedelta(hours=hours)
    elif time_option == 'tomorrow':
        scheduled_time = (now + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
    else:
        await query.edit_message_text("❌ Invalid option")
        return ConversationHandler.END
    
    # Create schedule
    await create_schedule_from_query(query, context, scheduled_time)
    
    return ConversationHandler.END


async def create_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE, scheduled_time: datetime):
    """Create scheduled download"""
    url = context.user_data.get('schedule_url')
    user_id = update.effective_user.id
    
    db_manager = context.bot_data.get('db_manager')
    download_dir = context.bot_data.get('download_dir', './downloads')
    
    if not db_manager:
        await update.message.reply_text("❌ System error")
        return
    
    # Get user's download path
    download_path = db_manager.get_download_path(user_id, download_dir)
    
    # Create schedule
    schedule_id = str(uuid.uuid4())[:8]
    db_manager.add_scheduled_download(
        user_id, schedule_id, url,
        scheduled_time.isoformat(),
        download_path
    )
    
    await update.message.reply_text(
        f"✅ <b>Download Scheduled!</b>\n\n"
        f"<b>Schedule ID:</b> <code>{schedule_id}</code>\n"
        f"<b>URL:</b> {url[:50]}...\n"
        f"<b>Waktu:</b> {scheduled_time.strftime('%Y-%m-%d %H:%M')}\n\n"
        f"Download akan dimulai otomatis pada waktu yang ditentukan.",
        parse_mode='HTML'
    )


async def create_schedule_from_query(query, context, scheduled_time):
    """Create schedule from callback query"""
    url = context.user_data.get('schedule_url')
    user_id = query.from_user.id
    
    db_manager = context.bot_data.get('db_manager')
    download_dir = context.bot_data.get('download_dir', './downloads')
    
    download_path = db_manager.get_download_path(user_id, download_dir)
    
    schedule_id = str(uuid.uuid4())[:8]
    db_manager.add_scheduled_download(
        user_id, schedule_id, url,
        scheduled_time.isoformat(),
        download_path
    )
    
    await query.edit_message_text(
        f"✅ <b>Download Scheduled!</b>\n\n"
        f"<b>Schedule ID:</b> <code>{schedule_id}</code>\n"
        f"<b>URL:</b> {url[:50]}...\n"
        f"<b>Waktu:</b> {scheduled_time.strftime('%Y-%m-%d %H:%M')}\n\n"
        f"Download akan dimulai otomatis pada waktu yang ditentukan.",
        parse_mode='HTML'
    )


async def my_schedules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's scheduled downloads"""
    user_id = update.effective_user.id
    db_manager = context.bot_data.get('db_manager')
    
    if not db_manager:
        await update.message.reply_text("❌ System error")
        return
    
    schedules = db_manager.get_user_schedules(user_id)
    
    if not schedules:
        await update.message.reply_text(
            "📅 Tidak ada jadwal download aktif.",
            parse_mode='HTML'
        )
        return
    
    text = "📅 <b>Jadwal Download Anda</b>\n\n"
    
    for sched in schedules:
        scheduled_time = datetime.fromisoformat(sched['scheduled_time'])
        status_emoji = "⏳" if sched['status'] == 'pending' else "🔄"
        
        text += (
            f"{status_emoji} <b>{sched['schedule_id']}</b>\n"
            f"   URL: {sched['url'][:40]}...\n"
            f"   Waktu: {scheduled_time.strftime('%Y-%m-%d %H:%M')}\n"
            f"   Status: {sched['status']}\n\n"
        )
    
    await update.message.reply_text(text, parse_mode='HTML')


async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel conversation"""
    await update.message.reply_text(
        "❌ Dibatalkan.",
        parse_mode='HTML'
    )
    return ConversationHandler.END


# Create conversation handler for batch download
batch_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('batch', multi_download_command)],
    states={
        AWAITING_URLS: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_urls)
        ],
    },
    fallbacks=[CommandHandler('cancel', cancel_conversation)],
)

# Create conversation handler for scheduled download
schedule_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('schedule', schedule_command)],
    states={
        AWAITING_SCHEDULE_URL: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_schedule_url)
        ],
        AWAITING_SCHEDULE_TIME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_schedule_time),
            CallbackQueryHandler(schedule_time_button, pattern='^schedule_time:')
        ],
    },
    fallbacks=[CommandHandler('cancel', cancel_conversation)],
)
