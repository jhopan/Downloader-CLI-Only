import os
import asyncio
import aiohttp
import aiofiles
from typing import Dict, Optional, Callable
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


class DownloadManager:
    """Mengelola multiple download secara bersamaan"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.active_downloads: Dict[str, dict] = {}
        self.completed_downloads: Dict[str, dict] = {}
        self.failed_downloads: Dict[str, dict] = {}
        self.download_tasks: Dict[str, asyncio.Task] = {}
        
    async def start_download(self, url: str, download_dir: str, user_id: Optional[int] = None) -> str:
        """Mulai download file dari URL"""
        download_id = str(uuid.uuid4())[:8]
        
        # Pastikan folder download exist
        os.makedirs(download_dir, exist_ok=True)
        
        # Dapatkan nama file dari URL
        filename = self._get_filename_from_url(url)
        filepath = os.path.join(download_dir, filename)
        
        # Tambahkan ke active downloads
        self.active_downloads[download_id] = {
            'url': url,
            'filename': filename,
            'filepath': filepath,
            'download_dir': download_dir,
            'status': 'starting',
            'progress': 0,
            'total_size': 0,
            'downloaded_size': 0,
            'start_time': datetime.now(),
            'speed': 0,
            'user_id': user_id
        }
        
        # Simpan ke database jika tersedia
        if self.db_manager and user_id:
            self.db_manager.add_download_history(
                user_id, download_id, url, filename, filepath, 'starting'
            )
        
        # Mulai download di background
        task = asyncio.create_task(self._download_file(download_id, url, filepath, user_id))
        self.download_tasks[download_id] = task
        
        return download_id
    
    async def _download_file(self, download_id: str, url: str, filepath: str, user_id: Optional[int] = None):
        """Download file secara asynchronous"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=None)) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}")
                    
                    total_size = int(response.headers.get('content-length', 0))
                    self.active_downloads[download_id]['total_size'] = total_size
                    self.active_downloads[download_id]['status'] = 'downloading'
                    
                    downloaded_size = 0
                    start_time = datetime.now()
                    
                    # Buat file dan mulai download
                    async with aiofiles.open(filepath, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            if download_id not in self.active_downloads:
                                # Download dibatalkan
                                await f.close()
                                if os.path.exists(filepath):
                                    os.remove(filepath)
                                return
                            
                            await f.write(chunk)
                            downloaded_size += len(chunk)
                            
                            # Update progress
                            elapsed = (datetime.now() - start_time).total_seconds()
                            speed = downloaded_size / elapsed if elapsed > 0 else 0
                            
                            self.active_downloads[download_id].update({
                                'downloaded_size': downloaded_size,
                                'progress': (downloaded_size / total_size * 100) if total_size > 0 else 0,
                                'speed': speed
                            })
            
            # Download selesai
            download_info = self.active_downloads.pop(download_id)
            download_info['status'] = 'completed'
            download_info['end_time'] = datetime.now()
            self.completed_downloads[download_id] = download_info
            
            # Update database
            if self.db_manager and user_id:
                self.db_manager.update_download_history(
                    download_id, 'completed', file_size=downloaded_size
                )
            
            # Remove task
            if download_id in self.download_tasks:
                del self.download_tasks[download_id]
            
            logger.info(f"Download completed: {download_info['filename']}")
            
        except asyncio.CancelledError:
            # Download dibatalkan
            if download_id in self.active_downloads:
                download_info = self.active_downloads.pop(download_id)
                if os.path.exists(filepath):
                    os.remove(filepath)
                
                # Update database
                if self.db_manager and user_id:
                    self.db_manager.update_download_history(
                        download_id, 'cancelled', error_message='Cancelled by user'
                    )
                
                logger.info(f"Download cancelled: {download_info['filename']}")
            
            if download_id in self.download_tasks:
                del self.download_tasks[download_id]
            
        except Exception as e:
            # Download gagal
            if download_id in self.active_downloads:
                download_info = self.active_downloads.pop(download_id)
                download_info['status'] = 'failed'
                download_info['error'] = str(e)
                download_info['end_time'] = datetime.now()
                self.failed_downloads[download_id] = download_info
                
                if os.path.exists(filepath):
                    os.remove(filepath)
                
                # Update database
                if self.db_manager and user_id:
                    self.db_manager.update_download_history(
                        download_id, 'failed', error_message=str(e)
                    )
                
                logger.error(f"Download failed: {download_info['filename']} - {e}")
            
            if download_id in self.download_tasks:
                del self.download_tasks[download_id]
    
    def cancel_download(self, download_id: str) -> bool:
        """Batalkan download yang sedang berjalan"""
        if download_id in self.active_downloads:
            download_info = self.active_downloads[download_id]
            
            # Cancel task
            if download_id in self.download_tasks:
                self.download_tasks[download_id].cancel()
            
            # Hapus dari active downloads
            self.active_downloads.pop(download_id)
            
            # Hapus file jika ada
            if os.path.exists(download_info['filepath']):
                try:
                    os.remove(download_info['filepath'])
                except:
                    pass
            
            return True
        return False
    
    def get_active_downloads(self) -> Dict[str, dict]:
        """Dapatkan daftar download aktif"""
        return self.active_downloads.copy()
    
    def get_status_text(self) -> str:
        """Dapatkan teks status untuk ditampilkan"""
        if not self.active_downloads:
            return "ℹ️ Tidak ada unduhan yang sedang berjalan."
        
        text = "📊 <b>Status Unduhan</b>\n\n"
        
        for download_id, info in self.active_downloads.items():
            progress = info.get('progress', 0)
            speed = info.get('speed', 0)
            speed_mb = speed / 1024 / 1024  # Convert to MB/s
            
            filename = info['filename']
            if len(filename) > 40:
                filename = filename[:37] + "..."
            
            text += f"📄 <b>{filename}</b>\n"
            text += f"   ID: <code>{download_id}</code>\n"
            text += f"   Progress: {progress:.1f}%\n"
            text += f"   Speed: {speed_mb:.2f} MB/s\n"
            text += f"   Lokasi: <code>{info['download_dir']}</code>\n\n"
        
        # Tambahkan info completed dan failed
        if self.completed_downloads:
            text += f"\n✅ Selesai: {len(self.completed_downloads)}\n"
        
        if self.failed_downloads:
            text += f"❌ Gagal: {len(self.failed_downloads)}\n"
        
        return text
    
    def _get_filename_from_url(self, url: str) -> str:
        """Ekstrak nama file dari URL"""
        from urllib.parse import urlparse, unquote
        
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)
        filename = unquote(filename)
        
        if not filename or filename == '/':
            # Generate nama file dari timestamp
            filename = f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return filename
    
    def make_filename_unique(self, filepath: str) -> str:
        """Buat filename unik jika sudah ada"""
        if not os.path.exists(filepath):
            return filepath
        
        directory = os.path.dirname(filepath)
        filename = os.path.basename(filepath)
        base, ext = os.path.splitext(filename)
        counter = 1
        
        while os.path.exists(os.path.join(directory, f"{base}_{counter}{ext}")):
            counter += 1
        
        return os.path.join(directory, f"{base}_{counter}{ext}")
