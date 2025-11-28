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
    
    # Create application
    logger.info("Creating bot application...")
    application = Application.builder().token(config.BOT_TOKEN).build()
    
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
    
    # Start scheduler
    logger.info("Starting scheduler...")
    scheduler_manager.start()
    
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
    
    # Run bot
    try:
        application.run_polling(allowed_updates=['message', 'callback_query'])
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        scheduler_manager.stop()
    except Exception as e:
        logger.error(f"Bot error: {e}")
        scheduler_manager.stop()
        raise


if __name__ == '__main__':
    main()
