import os
import logging
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler
)

# Import handlers
from app.handlers.start_handler import start_handler, cancel_handler
from app.handlers.button_handler import button_handler
from app.handlers.download_handler import handle_direct_download_link
from app.handlers.schedule_handler import handle_schedule_link, handle_schedule_time
from app.handlers.settings_handler import handle_custom_path
from app.handlers.states import (
    MAIN_MENU, WAITING_LINK, WAITING_SCHEDULE_LINK, 
    WAITING_SCHEDULE_TIME, WAITING_CUSTOM_PATH
)

# Import managers and database
from src.managers.download_manager import DownloadManager
from src.managers.scheduler_manager import SchedulerManager
from src.database.db_manager import Database

# Import config
import config

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Disable verbose HTTP request logs
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('telegram.ext.Application').setLevel(logging.WARNING)

# Disable verbose HTTP logs
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('telegram.ext').setLevel(logging.WARNING)


def main():
    """Jalankan bot"""
    
    # Initialize database
    logger.info("Initializing database...")
    db_manager = Database(config.DATABASE_PATH)
    
    # Initialize download manager
    logger.info("Initializing download manager...")
    download_manager = DownloadManager(db_manager=db_manager)
    
    # Initialize scheduler manager
    logger.info("Initializing scheduler...")
    scheduler_manager = SchedulerManager(download_manager, db_manager=db_manager)
    
    # Create application with network settings
    logger.info("Creating bot application...")
    application = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .build()
    )
    
    # Store managers in bot_data
    application.bot_data['download_manager'] = download_manager
    application.bot_data['scheduler_manager'] = scheduler_manager
    application.bot_data['db_manager'] = db_manager
    
    # Create conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_handler)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(button_handler)
            ],
            WAITING_LINK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_direct_download_link),
                CallbackQueryHandler(button_handler)
            ],
            WAITING_SCHEDULE_LINK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_schedule_link),
                CallbackQueryHandler(button_handler)
            ],
            WAITING_SCHEDULE_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_schedule_time),
                CallbackQueryHandler(button_handler)
            ],
            WAITING_CUSTOM_PATH: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_path),
                CallbackQueryHandler(button_handler)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel_handler)],
    )
    
    application.add_handler(conv_handler)
    
    # Setup post_init callback untuk start scheduler di event loop
    async def post_init(application):
        """Initialize scheduler setelah event loop berjalan"""
        logger.info("Starting scheduler...")
        scheduler_manager.start()
    
    # Setup post_shutdown callback untuk stop scheduler
    async def post_shutdown(application):
        """Cleanup saat bot dihentikan"""
        logger.info("Stopping scheduler...")
        scheduler_manager.stop()
    
    application.post_init = post_init
    application.post_shutdown = post_shutdown
    
    # Print startup info
    print("=" * 60)
    print("🤖 Bot Telegram Pengunduh Otomatis")
    print("=" * 60)
    print(f"✅ Bot berhasil dijalankan!")
    print(f"📁 Default download folder: {config.DEFAULT_DOWNLOAD_DIR}")
    print(f"💾 Database: {config.DATABASE_PATH}")
    print(f"👥 Admin IDs: {config.ADMIN_IDS}")
    print(f"📊 Max concurrent downloads: {config.MAX_CONCURRENT_DOWNLOADS}")
    print("=" * 60)
    print("Bot siap menerima perintah...")
    print("Tekan Ctrl+C untuk menghentikan bot")
    print("=" * 60)
    
    # Run bot with network error handling and retry
    max_retries = 5
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            # Jalankan bot dengan polling
            application.run_polling(
                allowed_updates=['message', 'callback_query'],
                drop_pending_updates=True
            )
            break  # Jika sukses, keluar dari loop
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            break
        except Exception as e:
            error_msg = str(e).lower()
            
            # Cek apakah error terkait network
            is_network_error = any(keyword in error_msg for keyword in [
                'timeout', 'connection', 'network', 'unreachable', 
                'timed out', 'getaddrinfo', 'temporary failure'
            ])
            
            if is_network_error and attempt < max_retries - 1:
                logger.error(f"Network error (attempt {attempt + 1}/{max_retries}): {e}")
                logger.info(f"🔄 Reconnecting dalam {retry_delay} detik...")
                print(f"\n⚠️  Koneksi terputus! Mencoba reconnect dalam {retry_delay} detik...")
                import time
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)  # Exponential backoff, max 60 detik
            else:
                # Error bukan network atau max retry tercapai
                logger.error(f"Bot error: {e}")
                if attempt >= max_retries - 1:
                    print("\n❌ Koneksi gagal setelah beberapa percobaan. Bot dihentikan.")
                raise


if __name__ == '__main__':
    main()
