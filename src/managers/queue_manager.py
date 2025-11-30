"""
Download Queue Manager
Priority-based queue dengan pause/resume capability
"""
import asyncio
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class QueuePriority(Enum):
    """Priority levels untuk download queue"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class QueueStatus(Enum):
    """Status untuk queue items"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class QueueItem:
    """Item dalam download queue"""
    queue_id: str
    user_id: int
    url: str
    filename: str
    priority: QueuePriority
    status: QueueStatus
    download_id: Optional[str] = None
    added_time: datetime = field(default_factory=datetime.now)
    started_time: Optional[datetime] = None
    completed_time: Optional[datetime] = None
    error_message: Optional[str] = None
    file_size: int = 0
    downloaded_size: int = 0
    progress: float = 0.0
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'queue_id': self.queue_id,
            'user_id': self.user_id,
            'url': self.url,
            'filename': self.filename,
            'priority': self.priority.name,
            'status': self.status.value,
            'download_id': self.download_id,
            'added_time': self.added_time.isoformat(),
            'started_time': self.started_time.isoformat() if self.started_time else None,
            'completed_time': self.completed_time.isoformat() if self.completed_time else None,
            'error_message': self.error_message,
            'file_size': self.file_size,
            'downloaded_size': self.downloaded_size,
            'progress': self.progress
        }


class QueueManager:
    """Manage download queue dengan priority dan concurrency control"""
    
    def __init__(self, max_concurrent: int = 3):
        """
        Initialize queue manager
        
        Args:
            max_concurrent: Maximum concurrent downloads
        """
        self.max_concurrent = max_concurrent
        self.queue: List[QueueItem] = []
        self.active_downloads: Dict[str, QueueItem] = {}
        self.queue_lock = asyncio.Lock()
        self.processing = False
        self.processor_task: Optional[asyncio.Task] = None
    
    async def add_to_queue(self, user_id: int, url: str, filename: str, 
                          priority: QueuePriority = QueuePriority.NORMAL) -> str:
        """
        Tambah item ke queue
        
        Args:
            user_id: User ID
            url: URL to download
            filename: Filename
            priority: Queue priority
            
        Returns:
            Queue ID
        """
        async with self.queue_lock:
            # Generate queue ID
            import uuid
            queue_id = str(uuid.uuid4())[:8]
            
            # Create queue item
            item = QueueItem(
                queue_id=queue_id,
                user_id=user_id,
                url=url,
                filename=filename,
                priority=priority,
                status=QueueStatus.PENDING
            )
            
            # Add to queue
            self.queue.append(item)
            
            # Sort by priority (highest first)
            self.queue.sort(key=lambda x: x.priority.value, reverse=True)
            
            logger.info(f"➕ Added to queue: {filename} (priority: {priority.name})")
            
            return queue_id
    
    async def remove_from_queue(self, queue_id: str) -> bool:
        """
        Remove item dari queue
        
        Args:
            queue_id: Queue ID to remove
            
        Returns:
            True jika berhasil
        """
        async with self.queue_lock:
            for i, item in enumerate(self.queue):
                if item.queue_id == queue_id:
                    if item.status == QueueStatus.DOWNLOADING:
                        logger.warning(f"Cannot remove active download: {queue_id}")
                        return False
                    
                    self.queue.pop(i)
                    logger.info(f"🗑️ Removed from queue: {item.filename}")
                    return True
            
            return False
    
    async def pause_item(self, queue_id: str) -> bool:
        """
        Pause download item
        
        Args:
            queue_id: Queue ID to pause
            
        Returns:
            True jika berhasil
        """
        async with self.queue_lock:
            for item in self.queue:
                if item.queue_id == queue_id:
                    if item.status == QueueStatus.DOWNLOADING:
                        item.status = QueueStatus.PAUSED
                        logger.info(f"⏸️ Paused: {item.filename}")
                        return True
                    elif item.status == QueueStatus.PENDING:
                        item.status = QueueStatus.PAUSED
                        return True
            
            return False
    
    async def resume_item(self, queue_id: str) -> bool:
        """
        Resume paused download
        
        Args:
            queue_id: Queue ID to resume
            
        Returns:
            True jika berhasil
        """
        async with self.queue_lock:
            for item in self.queue:
                if item.queue_id == queue_id and item.status == QueueStatus.PAUSED:
                    item.status = QueueStatus.PENDING
                    logger.info(f"▶️ Resumed: {item.filename}")
                    return True
            
            return False
    
    async def change_priority(self, queue_id: str, new_priority: QueuePriority) -> bool:
        """
        Ubah priority item dalam queue
        
        Args:
            queue_id: Queue ID
            new_priority: New priority level
            
        Returns:
            True jika berhasil
        """
        async with self.queue_lock:
            for item in self.queue:
                if item.queue_id == queue_id:
                    old_priority = item.priority
                    item.priority = new_priority
                    
                    # Re-sort queue
                    self.queue.sort(key=lambda x: x.priority.value, reverse=True)
                    
                    logger.info(f"🔄 Priority changed: {item.filename} ({old_priority.name} → {new_priority.name})")
                    return True
            
            return False
    
    async def get_queue_status(self, user_id: Optional[int] = None) -> Dict:
        """
        Get queue status
        
        Args:
            user_id: Filter by user ID (optional)
            
        Returns:
            Queue status dictionary
        """
        async with self.queue_lock:
            queue_items = self.queue
            if user_id:
                queue_items = [item for item in queue_items if item.user_id == user_id]
            
            return {
                'total': len(queue_items),
                'pending': sum(1 for item in queue_items if item.status == QueueStatus.PENDING),
                'downloading': sum(1 for item in queue_items if item.status == QueueStatus.DOWNLOADING),
                'paused': sum(1 for item in queue_items if item.status == QueueStatus.PAUSED),
                'completed': sum(1 for item in queue_items if item.status == QueueStatus.COMPLETED),
                'failed': sum(1 for item in queue_items if item.status == QueueStatus.FAILED),
                'active_slots': len(self.active_downloads),
                'max_concurrent': self.max_concurrent,
                'items': [item.to_dict() for item in queue_items]
            }
    
    async def get_next_item(self) -> Optional[QueueItem]:
        """
        Get next item untuk diproses (berdasarkan priority)
        
        Returns:
            Next queue item atau None
        """
        async with self.queue_lock:
            for item in self.queue:
                if item.status == QueueStatus.PENDING:
                    return item
            
            return None
    
    async def update_progress(self, queue_id: str, downloaded_size: int, 
                             total_size: int, progress: float):
        """
        Update download progress
        
        Args:
            queue_id: Queue ID
            downloaded_size: Downloaded bytes
            total_size: Total file size
            progress: Progress percentage
        """
        async with self.queue_lock:
            for item in self.queue:
                if item.queue_id == queue_id:
                    item.downloaded_size = downloaded_size
                    item.file_size = total_size
                    item.progress = progress
                    break
    
    async def mark_completed(self, queue_id: str, download_id: str):
        """Mark item as completed"""
        async with self.queue_lock:
            for item in self.queue:
                if item.queue_id == queue_id:
                    item.status = QueueStatus.COMPLETED
                    item.download_id = download_id
                    item.completed_time = datetime.now()
                    
                    # Remove from active
                    if queue_id in self.active_downloads:
                        del self.active_downloads[queue_id]
                    
                    logger.info(f"✅ Completed: {item.filename}")
                    break
    
    async def mark_failed(self, queue_id: str, error_message: str):
        """Mark item as failed"""
        async with self.queue_lock:
            for item in self.queue:
                if item.queue_id == queue_id:
                    item.status = QueueStatus.FAILED
                    item.error_message = error_message
                    item.completed_time = datetime.now()
                    
                    # Remove from active
                    if queue_id in self.active_downloads:
                        del self.active_downloads[queue_id]
                    
                    logger.error(f"❌ Failed: {item.filename} - {error_message}")
                    break
    
    def start_processing(self):
        """Start queue processor"""
        if not self.processing:
            self.processing = True
            self.processor_task = asyncio.create_task(self._process_queue())
            logger.info("🚀 Queue processor started")
    
    def stop_processing(self):
        """Stop queue processor"""
        self.processing = False
        if self.processor_task:
            self.processor_task.cancel()
            logger.info("🛑 Queue processor stopped")
    
    async def _process_queue(self):
        """Background queue processor"""
        while self.processing:
            try:
                # Check if ada slot available
                if len(self.active_downloads) < self.max_concurrent:
                    # Get next item
                    next_item = await self.get_next_item()
                    
                    if next_item:
                        # Mark as downloading
                        async with self.queue_lock:
                            next_item.status = QueueStatus.DOWNLOADING
                            next_item.started_time = datetime.now()
                            self.active_downloads[next_item.queue_id] = next_item
                        
                        logger.info(f"🔄 Processing: {next_item.filename}")
                
                # Wait sebelum check lagi
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in queue processor: {e}")
                await asyncio.sleep(5)
