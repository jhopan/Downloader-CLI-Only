import asyncio
import logging
from datetime import datetime
from typing import Optional
import uuid

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service untuk menjalankan scheduled downloads"""
    
    def __init__(self, db_manager, download_manager, bot_application):
        self.db_manager = db_manager
        self.download_manager = download_manager
        self.bot = bot_application.bot
        self.running = False
        self.check_interval = 60  # Check every 60 seconds
        
    async def start(self):
        """Start scheduler service"""
        if self.running:
            logger.warning("Scheduler already running")
            return
        
        self.running = True
        logger.info("📅 Scheduler service started")
        
        # Run scheduler loop
        asyncio.create_task(self._scheduler_loop())
    
    async def stop(self):
        """Stop scheduler service"""
        self.running = False
        logger.info("Scheduler service stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                await self._check_and_execute_schedules()
            except Exception as e:
                logger.error(f"Scheduler error: {e}", exc_info=True)
            
            # Wait before next check
            await asyncio.sleep(self.check_interval)
    
    async def _check_and_execute_schedules(self):
        """Check and execute pending schedules"""
        pending_schedules = self.db_manager.get_pending_schedules()
        
        if not pending_schedules:
            return
        
        now = datetime.now()
        
        for schedule in pending_schedules:
            try:
                # Parse scheduled time
                scheduled_time = datetime.fromisoformat(schedule['scheduled_time'])
                
                # Check if it's time to execute
                if now >= scheduled_time:
                    await self._execute_schedule(schedule)
            except Exception as e:
                logger.error(f"Error executing schedule {schedule['schedule_id']}: {e}")
                self.db_manager.update_schedule_status(
                    schedule['schedule_id'], 
                    'failed'
                )
    
    async def _execute_schedule(self, schedule: dict):
        """Execute a scheduled download"""
        logger.info(f"🎯 Executing scheduled download: {schedule['schedule_id']}")
        
        # Update status to executing
        self.db_manager.update_schedule_status(schedule['schedule_id'], 'executing')
        
        try:
            # Start download
            download_id = await self.download_manager.start_download(
                url=schedule['url'],
                download_dir=schedule['download_path'],
                user_id=schedule['user_id'],
                progress_callback=None  # No progress callback for scheduled downloads
            )
            
            # Update schedule with download_id
            self.db_manager.update_schedule_status(
                schedule['schedule_id'], 
                'completed',
                download_id
            )
            
            # Send notification to user
            try:
                await self.bot.send_message(
                    chat_id=schedule['user_id'],
                    text=(
                        f"✅ <b>Scheduled Download Started!</b>\n\n"
                        f"<b>URL:</b> {schedule['url'][:50]}...\n"
                        f"<b>Download ID:</b> <code>{download_id}</code>\n\n"
                        f"Download is now in progress."
                    ),
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")
            
        except Exception as e:
            logger.error(f"Failed to execute schedule: {e}")
            self.db_manager.update_schedule_status(schedule['schedule_id'], 'failed')
            
            # Send error notification
            try:
                await self.bot.send_message(
                    chat_id=schedule['user_id'],
                    text=(
                        f"❌ <b>Scheduled Download Failed</b>\n\n"
                        f"<b>URL:</b> {schedule['url'][:50]}...\n"
                        f"<b>Error:</b> {str(e)}\n\n"
                        f"Please try downloading manually."
                    ),
                    parse_mode='HTML'
                )
            except:
                pass
