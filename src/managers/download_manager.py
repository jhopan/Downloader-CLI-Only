import os
import asyncio
import aiohttp
import aiofiles
from typing import Dict, Optional, Callable
from datetime import datetime
import uuid
import logging
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)


class DownloadManager:
    """Mengelola multiple download secara bersamaan"""
    
    def __init__(self, db_manager=None, notification_manager=None):
        self.db_manager = db_manager
        self.notification_manager = notification_manager
        self.active_downloads: Dict[str, dict] = {}
        self.completed_downloads: Dict[str, dict] = {}
        self.failed_downloads: Dict[str, dict] = {}
        self.download_tasks: Dict[str, asyncio.Task] = {}
        self.progress_callbacks: Dict[str, Callable] = {}  # Callback untuk progress update
        
        # Auto-retry configuration
        import config
        self.max_retries = getattr(config, 'MAX_DOWNLOAD_RETRIES', 3)
        self.retry_delay_base = getattr(config, 'RETRY_DELAY_BASE', 5)  # seconds
        
    async def start_download(self, url: str, download_dir: str, user_id: Optional[int] = None, 
                             progress_callback: Optional[Callable] = None) -> str:
        """Mulai download file dari URL"""
        download_id = str(uuid.uuid4())[:8]
        
        # Pastikan folder download exist
        os.makedirs(download_dir, exist_ok=True)
        
        # Dapatkan nama file dari URL
        filename = self._get_filename_from_url(url)
        filepath = os.path.join(download_dir, filename)
        filepath = os.path.abspath(filepath)  # Convert to absolute path
        
        # Tambahkan ke active downloads
        self.active_downloads[download_id] = {
            'url': url,
            'filename': filename,
            'filepath': filepath,
            'download_dir': os.path.abspath(download_dir),
            'status': 'starting',
            'progress': 0,
            'total_size': 0,
            'downloaded_size': 0,
            'start_time': datetime.now(),
            'speed': 0,
            'user_id': user_id,
            'retry_count': 0,  # Track retry attempts
            'last_error': None
        }
        
        # Simpan ke database jika tersedia
        if self.db_manager and user_id:
            self.db_manager.add_download_history(
                user_id, download_id, url, filename, filepath, 'starting'
            )
        
        # Simpan progress callback
        if progress_callback:
            self.progress_callbacks[download_id] = progress_callback
        
        # Send notification: download start
        if self.notification_manager and user_id:
            asyncio.create_task(self.notification_manager.send_notification(
                chat_id=user_id,
                event_type='download_start',
                url=url,
                filename=filename
            ))
        
        # Mulai download di background
        task = asyncio.create_task(self._download_file(download_id, url, filepath, user_id))
        self.download_tasks[download_id] = task
        
        return download_id
    
    async def _download_file(self, download_id: str, url: str, filepath: str, user_id: Optional[int] = None):
        """Download file dengan auto-retry mechanism"""
        logger.info(f"📥 Memulai download: {os.path.basename(filepath)}")
        logger.info(f"💾 Lokasi: {os.path.abspath(filepath)}")
        
        for attempt in range(self.max_retries):
            try:
                # Call actual download method
                await self._download_file_with_fallback(download_id, url, filepath, user_id)
                return  # Success, exit retry loop
                
            except Exception as e:
                if download_id in self.active_downloads:
                    self.active_downloads[download_id]['retry_count'] = attempt + 1
                    self.active_downloads[download_id]['last_error'] = str(e)
                
                if attempt < self.max_retries - 1:
                    # Calculate exponential backoff delay
                    delay = self.retry_delay_base * (2 ** attempt)
                    logger.warning(f"⚠️ Download gagal (attempt {attempt + 1}/{self.max_retries}): {e}")
                    logger.info(f"🔄 Retry dalam {delay} detik...")
                    
                    # Send notification: download retry
                    if self.notification_manager and user_id:
                        asyncio.create_task(self.notification_manager.send_notification(
                            chat_id=user_id,
                            event_type='download_retry',
                            attempt=attempt + 2,
                            max_attempts=self.max_retries,
                            filename=os.path.basename(filepath),
                            delay=delay
                        ))
                    
                    await asyncio.sleep(delay)
                else:
                    # Max retries reached
                    logger.error(f"❌ Download gagal setelah {self.max_retries} attempts!")
                    
                    # Mark as failed
                    if download_id in self.active_downloads:
                        download_info = self.active_downloads.pop(download_id)
                        download_info['status'] = 'failed'
                        download_info['error'] = f"Max retries ({self.max_retries}) reached. Last error: {e}"
                        download_info['end_time'] = datetime.now()
                        self.failed_downloads[download_id] = download_info
                        
                        if os.path.exists(filepath) and download_info.get('downloaded_size', 0) == 0:
                            os.remove(filepath)
                        
                        # Send notification: download error
                        if self.notification_manager and user_id:
                            asyncio.create_task(self.notification_manager.send_notification(
                                chat_id=user_id,
                                event_type='download_error',
                                filename=os.path.basename(filepath),
                                error=str(e)
                            ))
                        
                        if self.db_manager and user_id:
                            self.db_manager.update_download_history(
                                download_id, 'failed', error_message=str(e)
                            )
                    
                    # Call completion callback with error
                    if download_id in self.progress_callbacks:
                        try:
                            await self.progress_callbacks[download_id](download_id, 0, 0, 0, 0, failed=True, error=str(e))
                        except Exception:
                            pass
                        del self.progress_callbacks[download_id]
                    
                    if download_id in self.download_tasks:
                        del self.download_tasks[download_id]
                    
                    raise
    
    async def _download_file_with_fallback(self, download_id: str, url: str, filepath: str, user_id: Optional[int] = None):
        """Download file secara asynchronous dengan fallback"""
        # Try aiohttp first
        try:
            await self._download_with_aiohttp(download_id, url, filepath, user_id)
            return
        except Exception as e:
            logger.warning(f"⚠️ aiohttp gagal: {e}")
            logger.info(f"🔄 Mencoba dengan urllib...")
            
            # Fallback to urllib
            try:
                await self._download_with_urllib(download_id, url, filepath, user_id)
                return
            except Exception as e2:
                logger.warning(f"⚠️ urllib juga gagal: {e2}")
                logger.info(f"🔄 Mencoba dengan requests (fallback terakhir)...")
                
                # Final fallback: requests library
                try:
                    await self._download_with_requests(download_id, url, filepath, user_id)
                    return
                except Exception as e3:
                    logger.error(f"❌ Semua metode gagal!")
                    logger.error(f"   - aiohttp: {e}")
                    logger.error(f"   - urllib: {e2}")
                    logger.error(f"   - requests: {e3}")
                    raise Exception(f"All download methods failed: {e3}")
    
    async def _download_file_old(self, download_id: str, url: str, filepath: str, user_id: Optional[int] = None):
        """OLD METHOD - Download file secara asynchronous dengan fallback"""
        logger.info(f"📥 Memulai download: {os.path.basename(filepath)}")
        logger.info(f"💾 Lokasi: {os.path.abspath(filepath)}")
        
        # Try aiohttp first
        try:
            await self._download_with_aiohttp(download_id, url, filepath, user_id)
            return
        except Exception as e:
            logger.warning(f"⚠️ aiohttp gagal: {e}")
            logger.info(f"🔄 Mencoba dengan urllib...")
            
            # Fallback to urllib
            try:
                await self._download_with_urllib(download_id, url, filepath, user_id)
                return
            except Exception as e2:
                logger.warning(f"⚠️ urllib juga gagal: {e2}")
                logger.info(f"🔄 Mencoba dengan requests (fallback terakhir)...")
                
                # Final fallback: requests library
                try:
                    await self._download_with_requests(download_id, url, filepath, user_id)
                    return
                except Exception as e3:
                    logger.error(f"❌ Semua metode gagal!")
                    logger.error(f"   - aiohttp: {e}")
                    logger.error(f"   - urllib: {e2}")
                    logger.error(f"   - requests: {e3}")
                    
                    # Mark as failed
                    if download_id in self.active_downloads:
                        download_info = self.active_downloads.pop(download_id)
                        download_info['status'] = 'failed'
                        download_info['error'] = f"Semua metode gagal. aiohttp: {e}, urllib: {e2}, requests: {e3}"
                        download_info['end_time'] = datetime.now()
                        self.failed_downloads[download_id] = download_info
                        
                        if os.path.exists(filepath):
                            os.remove(filepath)
                        
                        if self.db_manager and user_id:
                            self.db_manager.update_download_history(
                                download_id, 'failed', error_message=f"All methods failed: {e3}"
                            )
                    raise Exception(f"Semua metode download gagal. aiohttp: {e}, urllib: {e2}, requests: {e3}")
    
    async def _download_with_aiohttp(self, download_id: str, url: str, filepath: str, user_id: Optional[int] = None):
        """Download menggunakan aiohttp"""
        try:
            # Headers untuk bypass 403
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Referer': url
            }
            
            async with aiohttp.ClientSession(headers=headers) as session:
                # Setup headers yang lebih lengkap untuk bypass 403
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'identity',  # Disable compression untuk progress tracking
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Cache-Control': 'max-age=0',
                }
                
                # Add Referer if URL has domain
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(url)
                    if parsed.netloc:
                        headers['Referer'] = f"{parsed.scheme}://{parsed.netloc}/"
                except:
                    pass
                
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=None)) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}")
                    
                    # Cek Content-Disposition untuk nama file sebenarnya
                    content_disp = response.headers.get('Content-Disposition', '')
                    if content_disp and 'filename=' in content_disp:
                        import re
                        match = re.search(r'filename[*]?=["\']?([^"\';\r\n]+)', content_disp)
                        if match:
                            suggested_filename = match.group(1)
                            # Update filepath dengan nama yang benar
                            new_filepath = os.path.join(os.path.dirname(filepath), suggested_filename)
                            if filepath != new_filepath:
                                filepath = new_filepath
                                self.active_downloads[download_id]['filepath'] = filepath
                                self.active_downloads[download_id]['filename'] = suggested_filename
                                logger.info(f"📝 Nama file terdeteksi: {suggested_filename}")
                    
                    # Jika tidak ada ekstensi, coba deteksi dari Content-Type
                    if '.' not in os.path.basename(filepath):
                        content_type = response.headers.get('Content-Type', '')
                        ext = self._get_extension_from_content_type(content_type)
                        if ext:
                            new_filepath = filepath + ext
                            filepath = new_filepath
                            self.active_downloads[download_id]['filepath'] = filepath
                            self.active_downloads[download_id]['filename'] = os.path.basename(filepath)
                            logger.info(f"📝 Ekstensi ditambahkan: {ext}")
                    
                    total_size = int(response.headers.get('content-length', 0))
                    self.active_downloads[download_id]['total_size'] = total_size
                    self.active_downloads[download_id]['status'] = 'downloading'
                    
                    logger.info(f"📦 Ukuran file: {self.format_size(total_size)}")
                    
                    downloaded_size = 0
                    start_time = datetime.now()
                    last_progress_log = 0
                    
                    # Buat file dan mulai download
                    async with aiofiles.open(filepath, 'wb') as f:
                        async for chunk in response.content.iter_chunked(65536):  # 64KB chunks
                            if download_id not in self.active_downloads:
                                # Download dibatalkan
                                await f.close()
                                if os.path.exists(filepath):
                                    os.remove(filepath)
                                logger.warning(f"⚠️ Download dibatalkan: {os.path.basename(filepath)}")
                                return
                            
                            await f.write(chunk)
                            await f.flush()  # Ensure data is written to disk
                            downloaded_size += len(chunk)
                            
                            # Update progress
                            elapsed = (datetime.now() - start_time).total_seconds()
                            speed = downloaded_size / elapsed if elapsed > 0 else 0
                            progress_pct = (downloaded_size / total_size * 100) if total_size > 0 else 0
                            
                            self.active_downloads[download_id].update({
                                'downloaded_size': downloaded_size,
                                'progress': progress_pct,
                                'speed': speed
                            })
                            
                            # Log progress ke terminal setiap 10%
                            if int(progress_pct) >= last_progress_log + 10:
                                last_progress_log = int(progress_pct)
                                logger.info(
                                    f"⏳ Progress: {progress_pct:.1f}% | "
                                    f"{self.format_size(downloaded_size)} / {self.format_size(total_size)} | "
                                    f"Speed: {self.format_size(speed)}/s"
                                )
                            
                            # Call progress callback setiap 10%
                            if download_id in self.progress_callbacks and progress_pct > 0:
                                if int(progress_pct) % 10 == 0 and int(progress_pct) > 0:
                                    try:
                                        await self.progress_callbacks[download_id](download_id, progress_pct, downloaded_size, total_size, speed)
                                    except Exception as e:
                                        logger.error(f"Progress callback error: {e}")
                    
                    # Ensure all data is written
                    logger.info(f"💾 Finalizing file... {self.format_size(downloaded_size)} written")
            
            # Verify file size matches
            if os.path.exists(filepath):
                actual_size = os.path.getsize(filepath)
                if actual_size != downloaded_size:
                    logger.warning(f"⚠️ File size mismatch: expected {downloaded_size}, got {actual_size}")
                else:
                    logger.info(f"✅ File size verified: {self.format_size(actual_size)}")
            
            # Download selesai
            download_info = self.active_downloads.pop(download_id)
            download_info['status'] = 'completed'
            download_info['end_time'] = datetime.now()
            self.completed_downloads[download_id] = download_info
            
            # Calculate download duration
            duration = (download_info['end_time'] - download_info['start_time']).total_seconds()
            duration_str = self.format_duration(duration)
            
            # Update database
            if self.db_manager and user_id:
                self.db_manager.update_download_history(
                    download_id, 'completed', file_size=downloaded_size
                )
            
            # Send notification: download complete
            if self.notification_manager and user_id:
                asyncio.create_task(self.notification_manager.send_notification(
                    chat_id=user_id,
                    event_type='download_complete',
                    filename=download_info['filename'],
                    size=self.format_size(downloaded_size),
                    duration=duration_str
                ))
            
            # Call completion callback
            if download_id in self.progress_callbacks:
                try:
                    await self.progress_callbacks[download_id](download_id, 100, downloaded_size, total_size, 0, completed=True)
                except Exception as e:
                    logger.error(f"Completion callback error: {e}")
                del self.progress_callbacks[download_id]
            
            # Remove task
            if download_id in self.download_tasks:
                del self.download_tasks[download_id]
            
            logger.info(f"✅ Download selesai: {download_info['filename']} ({self.format_size(downloaded_size)})")
            logger.info(f"📁 File tersimpan di: {os.path.abspath(filepath)}")
            
            # Auto-categorize file if enabled
            download_dir_path = download_info.get('download_dir', os.path.dirname(filepath))
            await self._auto_categorize_file(filepath, user_id, download_dir_path)
            
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            # Network error - coba ulang tidak perlu, user bisa download ulang
            logger.error(f"❌ Network error: {e}")
            if download_id in self.active_downloads:
                download_info = self.active_downloads.pop(download_id)
                download_info['status'] = 'failed'
                download_info['error'] = f"Network error: {str(e)}"
                download_info['end_time'] = datetime.now()
                self.failed_downloads[download_id] = download_info
                
                if os.path.exists(filepath):
                    os.remove(filepath)
                
                # Update database
                if self.db_manager and user_id:
                    self.db_manager.update_download_history(
                        download_id, 'failed', error_message=str(e)
                    )
                
                logger.error(f"❌ Download gagal: {download_info['filename']} - {str(e)}")
            
            if download_id in self.download_tasks:
                del self.download_tasks[download_id]
            
            raise  # Re-raise exception for caller
            
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
                
                logger.info(f"❌ Download cancelled: {download_info['filename']}")
            
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
                
                logger.error(f"❌ Download error: {download_info['filename']} - {e}")
            
            if download_id in self.download_tasks:
                del self.download_tasks[download_id]
            
            raise  # Re-raise exception for caller
    
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
        """Ekstrak nama file dari URL dengan deteksi ekstensi pintar"""
        from urllib.parse import urlparse, unquote
        import re
        
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)
        filename = unquote(filename)
        
        # Bersihkan query string jika ada
        if '?' in filename:
            filename = filename.split('?')[0]
        
        # Cek apakah filename valid dan punya ekstensi
        if filename and filename != '/' and '.' in filename:
            return filename
        
        # Jika tidak ada ekstensi, coba deteksi dari URL pattern
        # Contoh: /100MB.bin, /file.zip, dll
        url_parts = parsed.path.split('/')
        for part in reversed(url_parts):
            if part and '.' in part:
                clean_part = unquote(part)
                if '?' in clean_part:
                    clean_part = clean_part.split('?')[0]
                return clean_part
        
        # Jika masih tidak ada, gunakan domain + path sebagai nama
        domain = parsed.netloc.replace('www.', '').replace('.', '_')
        path_clean = parsed.path.strip('/').replace('/', '_')
        
        if path_clean:
            filename = f"{domain}_{path_clean}"
        else:
            filename = domain
        
        # Tambahkan ekstensi default jika tidak ada
        if '.' not in filename:
            filename = f"{filename}.bin"  # Default ke .bin untuk file binary
        
        # Batasi panjang filename
        if len(filename) > 200:
            name_part = filename[:180]
            ext_part = os.path.splitext(filename)[1]
            filename = name_part + ext_part
        
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
    
    async def _download_with_urllib(self, download_id: str, url: str, filepath: str, user_id: Optional[int] = None):
        """Download menggunakan urllib sebagai fallback"""
        logger.info(f"🔧 Menggunakan urllib untuk download")
        
        def download_sync():
            """Synchronous download function"""
            try:
                # Set headers untuk mencegah 403 - sama dengan aiohttp
                req = urllib.request.Request(url)
                req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
                req.add_header('Accept', '*/*')
                req.add_header('Accept-Language', 'en-US,en;q=0.9')
                req.add_header('Accept-Encoding', 'gzip, deflate, br')
                req.add_header('Connection', 'keep-alive')
                req.add_header('Referer', url)
                
                with urllib.request.urlopen(req, timeout=30) as response:
                    # Cek Content-Disposition untuk nama file
                    content_disp = response.headers.get('Content-Disposition', '')
                    if content_disp and 'filename=' in content_disp:
                        import re
                        match = re.search(r'filename[*]?=["\']?([^"\';\r\n]+)', content_disp)
                        if match:
                            suggested_filename = match.group(1)
                            new_filepath = os.path.join(os.path.dirname(filepath), suggested_filename)
                            if filepath != new_filepath:
                                filepath = new_filepath
                                if download_id in self.active_downloads:
                                    self.active_downloads[download_id]['filepath'] = filepath
                                    self.active_downloads[download_id]['filename'] = suggested_filename
                                logger.info(f"📝 Nama file terdeteksi: {suggested_filename}")
                    
                    # Jika tidak ada ekstensi, coba deteksi dari Content-Type
                    if '.' not in os.path.basename(filepath):
                        content_type = response.headers.get('Content-Type', '')
                        ext = self._get_extension_from_content_type(content_type)
                        if ext:
                            new_filepath = filepath + ext
                            filepath = new_filepath
                            if download_id in self.active_downloads:
                                self.active_downloads[download_id]['filepath'] = filepath
                                self.active_downloads[download_id]['filename'] = os.path.basename(filepath)
                            logger.info(f"📝 Ekstensi ditambahkan: {ext}")
                    
                    total_size = int(response.headers.get('content-length', 0))
                    
                    if download_id in self.active_downloads:
                        self.active_downloads[download_id]['total_size'] = total_size
                        self.active_downloads[download_id]['status'] = 'downloading'
                    
                    logger.info(f"📦 Ukuran file: {self.format_size(total_size)}")
                    
                    downloaded_size = 0
                    start_time = datetime.now()
                    last_progress_log = 0
                    
                    with open(filepath, 'wb') as f:
                        while True:
                            # Cek jika download dibatalkan
                            if download_id not in self.active_downloads:
                                if os.path.exists(filepath):
                                    os.remove(filepath)
                                logger.warning(f"⚠️ Download dibatalkan: {os.path.basename(filepath)}")
                                return
                            
                            chunk = response.read(8192)
                            if not chunk:
                                break
                            
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            
                            # Update progress
                            elapsed = (datetime.now() - start_time).total_seconds()
                            speed = downloaded_size / elapsed if elapsed > 0 else 0
                            progress_pct = (downloaded_size / total_size * 100) if total_size > 0 else 0
                            
                            if download_id in self.active_downloads:
                                self.active_downloads[download_id].update({
                                    'downloaded_size': downloaded_size,
                                    'progress': progress_pct,
                                    'speed': speed
                                })
                            
                            # Log progress ke terminal setiap 10%
                            if int(progress_pct) >= last_progress_log + 10:
                                last_progress_log = int(progress_pct)
                                logger.info(
                                    f"⏳ Progress: {progress_pct:.1f}% | "
                                    f"{self.format_size(downloaded_size)} / {self.format_size(total_size)} | "
                                    f"Speed: {self.format_size(speed)}/s"
                                )
                
                return downloaded_size, total_size
                
            except urllib.error.HTTPError as e:
                raise Exception(f"HTTP {e.code}: {e.reason}")
            except urllib.error.URLError as e:
                raise Exception(f"URL Error: {e.reason}")
            except Exception as e:
                raise Exception(f"urllib error: {str(e)}")
        
        # Run sync download in executor
        loop = asyncio.get_event_loop()
        try:
            downloaded_size, total_size = await loop.run_in_executor(None, download_sync)
            
            # Download selesai
            if download_id in self.active_downloads:
                download_info = self.active_downloads.pop(download_id)
                download_info['status'] = 'completed'
                download_info['end_time'] = datetime.now()
                self.completed_downloads[download_id] = download_info
                
                # Update database
                if self.db_manager and user_id:
                    self.db_manager.update_download_history(
                        download_id, 'completed', file_size=downloaded_size
                    )
                
                # Call completion callback
                if download_id in self.progress_callbacks:
                    try:
                        await self.progress_callbacks[download_id](download_id, 100, downloaded_size, total_size, 0, completed=True)
                    except Exception as e:
                        logger.error(f"Completion callback error: {e}")
                    del self.progress_callbacks[download_id]
                
                if download_id in self.download_tasks:
                    del self.download_tasks[download_id]
                
                logger.info(f"✅ Download selesai: {download_info['filename']} ({self.format_size(downloaded_size)})")
                logger.info(f"📁 File tersimpan di: {os.path.abspath(filepath)}")
        
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
                
                if self.db_manager and user_id:
                    self.db_manager.update_download_history(
                        download_id, 'failed', error_message=str(e)
                    )
                
                logger.error(f"❌ Download error: {download_info['filename']} - {e}")
            
            if download_id in self.download_tasks:
                del self.download_tasks[download_id]
            
            raise
    
    async def _download_with_requests(self, download_id: str, url: str, filepath: str, user_id: Optional[int] = None):
        """Download menggunakan requests library sebagai fallback terakhir"""
        logger.info(f"🔧 Menggunakan requests library untuk download")
        
        def download_sync():
            """Synchronous download function using requests"""
            try:
                import requests
                
                # Set headers untuk mencegah 403 - konsisten dengan metode lain
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Cache-Control': 'max-age=0',
                }
                
                # Add Referer
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(url)
                    if parsed.netloc:
                        headers['Referer'] = f"{parsed.scheme}://{parsed.netloc}/"
                except:
                    pass
                
                # Stream download untuk file besar
                with requests.get(url, headers=headers, stream=True, timeout=30) as response:
                    response.raise_for_status()
                    
                    # Cek Content-Disposition untuk nama file
                    content_disp = response.headers.get('Content-Disposition', '')
                    if content_disp and 'filename=' in content_disp:
                        import re
                        match = re.search(r'filename[*]?=["\']?([^"\';\r\n]+)', content_disp)
                        if match:
                            suggested_filename = match.group(1)
                            new_filepath = os.path.join(os.path.dirname(filepath), suggested_filename)
                            if filepath != new_filepath:
                                filepath = new_filepath
                                if download_id in self.active_downloads:
                                    self.active_downloads[download_id]['filepath'] = filepath
                                    self.active_downloads[download_id]['filename'] = suggested_filename
                                logger.info(f"📝 Nama file terdeteksi: {suggested_filename}")
                    
                    # Jika tidak ada ekstensi, coba deteksi dari Content-Type
                    if '.' not in os.path.basename(filepath):
                        content_type = response.headers.get('Content-Type', '')
                        ext = self._get_extension_from_content_type(content_type)
                        if ext:
                            new_filepath = filepath + ext
                            filepath = new_filepath
                            if download_id in self.active_downloads:
                                self.active_downloads[download_id]['filepath'] = filepath
                                self.active_downloads[download_id]['filename'] = os.path.basename(filepath)
                            logger.info(f"📝 Ekstensi ditambahkan: {ext}")
                    
                    total_size = int(response.headers.get('content-length', 0))
                    
                    if download_id in self.active_downloads:
                        self.active_downloads[download_id]['total_size'] = total_size
                        self.active_downloads[download_id]['status'] = 'downloading'
                    
                    logger.info(f"📦 Ukuran file: {self.format_size(total_size)}")
                    
                    downloaded_size = 0
                    start_time = datetime.now()
                    last_progress_log = 0
                    
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            # Cek jika download dibatalkan
                            if download_id not in self.active_downloads:
                                if os.path.exists(filepath):
                                    os.remove(filepath)
                                logger.warning(f"⚠️ Download dibatalkan: {os.path.basename(filepath)}")
                                return
                            
                            if chunk:  # filter out keep-alive new chunks
                                f.write(chunk)
                                downloaded_size += len(chunk)
                                
                                # Update progress
                                elapsed = (datetime.now() - start_time).total_seconds()
                                speed = downloaded_size / elapsed if elapsed > 0 else 0
                                progress_pct = (downloaded_size / total_size * 100) if total_size > 0 else 0
                                
                                if download_id in self.active_downloads:
                                    self.active_downloads[download_id].update({
                                        'downloaded_size': downloaded_size,
                                        'progress': progress_pct,
                                        'speed': speed
                                    })
                                
                                # Log progress ke terminal setiap 10%
                                if int(progress_pct) >= last_progress_log + 10:
                                    last_progress_log = int(progress_pct)
                                    logger.info(
                                        f"⏳ Progress: {progress_pct:.1f}% | "
                                        f"{self.format_size(downloaded_size)} / {self.format_size(total_size)} | "
                                        f"Speed: {self.format_size(speed)}/s"
                                    )
                
                return downloaded_size, total_size
                
            except ImportError:
                raise Exception("Library requests tidak terinstall. Install dengan: pip install requests")
            except requests.exceptions.HTTPError as e:
                raise Exception(f"HTTP {e.response.status_code}: {e.response.reason}")
            except requests.exceptions.ConnectionError as e:
                raise Exception(f"Connection error: {str(e)}")
            except requests.exceptions.Timeout as e:
                raise Exception(f"Timeout error: {str(e)}")
            except requests.exceptions.RequestException as e:
                raise Exception(f"requests error: {str(e)}")
            except Exception as e:
                raise Exception(f"requests unexpected error: {str(e)}")
        
        # Run sync download in executor
        loop = asyncio.get_event_loop()
        try:
            downloaded_size, total_size = await loop.run_in_executor(None, download_sync)
            
            # Download selesai
            if download_id in self.active_downloads:
                download_info = self.active_downloads.pop(download_id)
                download_info['status'] = 'completed'
                download_info['end_time'] = datetime.now()
                self.completed_downloads[download_id] = download_info
                
                # Update database
                if self.db_manager and user_id:
                    self.db_manager.update_download_history(
                        download_id, 'completed', file_size=downloaded_size
                    )
                
                # Call completion callback
                if download_id in self.progress_callbacks:
                    try:
                        await self.progress_callbacks[download_id](download_id, 100, downloaded_size, total_size, 0, completed=True)
                    except Exception as e:
                        logger.error(f"Completion callback error: {e}")
                    del self.progress_callbacks[download_id]
                
                if download_id in self.download_tasks:
                    del self.download_tasks[download_id]
                
                logger.info(f"✅ Download selesai: {download_info['filename']} ({self.format_size(downloaded_size)})")
                logger.info(f"📁 File tersimpan di: {os.path.abspath(filepath)}")
        
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
                
                if self.db_manager and user_id:
                    self.db_manager.update_download_history(
                        download_id, 'failed', error_message=str(e)
                    )
                
                logger.error(f"❌ Download error: {download_info['filename']} - {e}")
            
            if download_id in self.download_tasks:
                del self.download_tasks[download_id]
            
            raise
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Format ukuran file ke human readable"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format durasi ke human readable"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"
    
    def _get_extension_from_content_type(self, content_type: str) -> str:
        """Dapatkan ekstensi file dari Content-Type header"""
        content_type = content_type.lower().split(';')[0].strip()
        
        # Mapping Content-Type ke ekstensi
        mime_to_ext = {
            # Video
            'video/mp4': '.mp4',
            'video/mpeg': '.mpeg',
            'video/quicktime': '.mov',
            'video/x-msvideo': '.avi',
            'video/x-matroska': '.mkv',
            'video/webm': '.webm',
            
            # Audio
            'audio/mpeg': '.mp3',
            'audio/mp4': '.m4a',
            'audio/wav': '.wav',
            'audio/ogg': '.ogg',
            'audio/webm': '.weba',
            
            # Image
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
            'image/svg+xml': '.svg',
            
            # Document
            'application/pdf': '.pdf',
            'application/msword': '.doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/vnd.ms-excel': '.xls',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
            'application/vnd.ms-powerpoint': '.ppt',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
            'text/plain': '.txt',
            'text/html': '.html',
            'text/csv': '.csv',
            
            # Archive
            'application/zip': '.zip',
            'application/x-rar-compressed': '.rar',
            'application/x-7z-compressed': '.7z',
            'application/x-tar': '.tar',
            'application/gzip': '.gz',
            
            # Executable
            'application/x-msdownload': '.exe',
            'application/vnd.android.package-archive': '.apk',
            'application/x-deb': '.deb',
            
            # Binary/Other
            'application/octet-stream': '.bin',
            'application/json': '.json',
            'application/xml': '.xml',
        }
        
        return mime_to_ext.get(content_type, '')
    
    async def _auto_categorize_file(self, filepath: str, user_id: int, download_dir: str):
        """
        Auto-categorize downloaded file ke folder yang sesuai
        
        Args:
            filepath: Path ke file yang baru didownload
            user_id: User ID
            download_dir: Download directory
        """
        try:
            from src.utils.smart_categorizer import SmartCategorizer
            import config
            
            # Check if auto-categorization is enabled
            auto_categorize = getattr(config, 'AUTO_CATEGORIZE_DOWNLOADS', True)
            if not auto_categorize:
                return
            
            # Get filename
            filename = os.path.basename(filepath)
            
            # Create categorizer
            categorizer = SmartCategorizer(self.db_manager, download_dir)
            
            # Categorize file
            category, confidence = categorizer.categorize_file(filename, user_id)
            
            # Only move if confidence is high enough
            if confidence > 0.6 and category != 'other':
                # Create category folder
                category_dir = os.path.join(download_dir, category.capitalize())
                os.makedirs(category_dir, exist_ok=True)
                
                # New path
                new_filepath = os.path.join(category_dir, filename)
                
                # Handle duplicate filenames
                if os.path.exists(new_filepath):
                    base, ext = os.path.splitext(filename)
                    counter = 1
                    while os.path.exists(new_filepath):
                        new_filename = f"{base} ({counter}){ext}"
                        new_filepath = os.path.join(category_dir, new_filename)
                        counter += 1
                
                # Move file
                os.rename(filepath, new_filepath)
                logger.info(f"📂 Auto-categorized: {filename} → {category}/ (confidence: {confidence:.2f})")
                
                return new_filepath
            else:
                logger.debug(f"📁 Kept in root: {filename} (category: {category}, confidence: {confidence:.2f})")
                
        except Exception as e:
            logger.error(f"Error auto-categorizing file: {e}")
            # Don't fail download if categorization fails
            pass
        
        return filepath
