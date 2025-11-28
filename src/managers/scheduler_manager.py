import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import uuid
import re
import logging

logger = logging.getLogger(__name__)


class SchedulerManager:
    """Mengelola penjadwalan download"""
    
    def __init__(self, download_manager, db_manager=None):
        self.download_manager = download_manager
        self.db_manager = db_manager
        self.schedules: Dict[str, dict] = {}
        self.running = False
        self.scheduler_task = None
        
        # Load pending schedules from database
        if self.db_manager:
            self._load_pending_schedules()
    
    def _load_pending_schedules(self):
        """Load pending schedules from database"""
        try:
            pending = self.db_manager.get_pending_schedules()
            for schedule in pending:
                self.schedules[schedule['schedule_id']] = {
                    'url': schedule['url'],
                    'user_id': schedule['user_id'],
                    'scheduled_time': datetime.fromisoformat(schedule['scheduled_time']),
                    'download_path': schedule['download_path'],
                    'status': 'pending'
                }
            logger.info(f"Loaded {len(pending)} pending schedules from database")
        except Exception as e:
            logger.error(f"Error loading pending schedules: {e}")
    
    def start(self):
        """Mulai scheduler"""
        if not self.running:
            self.running = True
            self.scheduler_task = asyncio.create_task(self._run_scheduler())
            logger.info("Scheduler started")
    
    def stop(self):
        """Stop scheduler"""
        self.running = False
        if self.scheduler_task:
            self.scheduler_task.cancel()
            logger.info("Scheduler stopped")
    
    async def _run_scheduler(self):
        """Loop utama scheduler"""
        while self.running:
            try:
                current_time = datetime.now()
                
                # Cek semua jadwal
                schedules_to_execute = []
                for schedule_id, schedule in list(self.schedules.items()):
                    if schedule['scheduled_time'] <= current_time and schedule['status'] == 'pending':
                        schedules_to_execute.append((schedule_id, schedule))
                
                # Eksekusi jadwal yang sudah waktunya
                for schedule_id, schedule in schedules_to_execute:
                    logger.info(f"Executing scheduled download: {schedule['url']}")
                    
                    # Update status
                    self.schedules[schedule_id]['status'] = 'executing'
                    
                    # Mulai download
                    try:
                        download_id = await self.download_manager.start_download(
                            schedule['url'],
                            schedule['download_path'],
                            schedule.get('user_id')
                        )
                        
                        self.schedules[schedule_id]['download_id'] = download_id
                        self.schedules[schedule_id]['status'] = 'completed'
                        
                        # Update database
                        if self.db_manager:
                            self.db_manager.update_schedule_status(
                                schedule_id, 'completed', download_id
                            )
                        
                    except Exception as e:
                        logger.error(f"Failed to start scheduled download: {e}")
                        self.schedules[schedule_id]['status'] = 'failed'
                        self.schedules[schedule_id]['error'] = str(e)
                        
                        # Update database
                        if self.db_manager:
                            self.db_manager.update_schedule_status(schedule_id, 'failed')
                
                # Tunggu 5 detik sebelum cek lagi
                await asyncio.sleep(5)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler: {e}")
                await asyncio.sleep(5)
    
    def add_schedule(self, url: str, scheduled_time: datetime, download_path: str, 
                    user_id: Optional[int] = None) -> str:
        """Tambahkan jadwal download baru"""
        schedule_id = str(uuid.uuid4())[:8]
        
        self.schedules[schedule_id] = {
            'url': url,
            'user_id': user_id,
            'scheduled_time': scheduled_time,
            'download_path': download_path,
            'created_time': datetime.now(),
            'status': 'pending',
            'download_id': None,
            'executed_time': None
        }
        
        # Simpan ke database
        if self.db_manager and user_id:
            self.db_manager.add_scheduled_download(
                user_id, schedule_id, url, 
                scheduled_time.isoformat(), download_path
            )
        
        logger.info(f"Schedule added: {schedule_id} for {scheduled_time}")
        return schedule_id
    
    def cancel_schedule(self, schedule_id: str) -> bool:
        """Batalkan jadwal"""
        if schedule_id in self.schedules:
            schedule = self.schedules[schedule_id]
            if schedule['status'] == 'pending':
                self.schedules[schedule_id]['status'] = 'cancelled'
                
                # Update database
                if self.db_manager:
                    self.db_manager.update_schedule_status(schedule_id, 'cancelled')
                
                logger.info(f"Schedule cancelled: {schedule_id}")
                return True
        return False
    
    def get_schedules_text(self, user_id: Optional[int] = None) -> str:
        """Dapatkan teks daftar jadwal"""
        # Filter by user if specified
        if user_id:
            pending_schedules = {
                k: v for k, v in self.schedules.items() 
                if v['status'] == 'pending' and v.get('user_id') == user_id
            }
        else:
            pending_schedules = {k: v for k, v in self.schedules.items() if v['status'] == 'pending'}
        
        if not pending_schedules:
            return "ℹ️ Tidak ada jadwal unduhan yang aktif."
        
        text = "📋 <b>Daftar Jadwal Unduhan</b>\n\n"
        
        for schedule_id, schedule in sorted(
            pending_schedules.items(),
            key=lambda x: x[1]['scheduled_time']
        ):
            url = schedule['url']
            if len(url) > 50:
                url = url[:47] + "..."
            
            scheduled_time = schedule['scheduled_time'].strftime('%d/%m/%Y %H:%M')
            
            # Hitung waktu tersisa
            time_remaining = schedule['scheduled_time'] - datetime.now()
            if time_remaining.total_seconds() > 0:
                hours = int(time_remaining.total_seconds() // 3600)
                minutes = int((time_remaining.total_seconds() % 3600) // 60)
                time_str = f"{hours}j {minutes}m" if hours > 0 else f"{minutes}m"
            else:
                time_str = "segera"
            
            text += f"🔔 <b>ID:</b> <code>{schedule_id}</code>\n"
            text += f"   Link: {url}\n"
            text += f"   Waktu: <code>{scheduled_time}</code>\n"
            text += f"   Tersisa: {time_str}\n"
            text += f"   Lokasi: <code>{schedule['download_path']}</code>\n\n"
        
        return text
    
    def parse_time_input(self, time_input: str) -> Optional[datetime]:
        """
        Parse input waktu dari user
        Format yang didukung:
        - DD/MM/YYYY HH:MM
        - 1h, 2h, 30m, 2d (relative time)
        """
        time_input = time_input.strip()
        
        # Coba parse format DD/MM/YYYY HH:MM
        try:
            return datetime.strptime(time_input, '%d/%m/%Y %H:%M')
        except ValueError:
            pass
        
        # Coba parse relative time (1h, 30m, 2d)
        relative_pattern = re.compile(r'^(\d+)(h|m|d)$', re.IGNORECASE)
        match = relative_pattern.match(time_input)
        
        if match:
            value = int(match.group(1))
            unit = match.group(2).lower()
            
            now = datetime.now()
            
            if unit == 'h':  # hours
                return now + timedelta(hours=value)
            elif unit == 'm':  # minutes
                return now + timedelta(minutes=value)
            elif unit == 'd':  # days
                return now + timedelta(days=value)
        
        return None
