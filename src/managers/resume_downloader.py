"""
Resume Download Manager
Handle interrupted downloads dengan Range requests
"""
import os
import json
import logging
from typing import Dict, Optional
from datetime import datetime
import aiofiles
import aiohttp

logger = logging.getLogger(__name__)


class DownloadState:
    """Track download state untuk resume capability"""
    
    def __init__(self, state_dir: str = "downloads/.state"):
        """
        Initialize download state manager
        
        Args:
            state_dir: Directory untuk simpan state files
        """
        self.state_dir = state_dir
        os.makedirs(state_dir, exist_ok=True)
    
    def get_state_path(self, download_id: str) -> str:
        """Get path ke state file"""
        return os.path.join(self.state_dir, f"{download_id}.json")
    
    def save_state(self, download_id: str, url: str, filepath: str, 
                   downloaded_bytes: int, total_bytes: int):
        """
        Save download state
        
        Args:
            download_id: Download ID
            url: Download URL
            filepath: Target filepath
            downloaded_bytes: Bytes already downloaded
            total_bytes: Total file size
        """
        state = {
            'download_id': download_id,
            'url': url,
            'filepath': filepath,
            'downloaded_bytes': downloaded_bytes,
            'total_bytes': total_bytes,
            'timestamp': datetime.now().isoformat(),
            'resume_supported': True
        }
        
        state_path = self.get_state_path(download_id)
        
        try:
            with open(state_path, 'w') as f:
                json.dump(state, f, indent=2)
            
            logger.info(f"Download state saved: {download_id} ({downloaded_bytes}/{total_bytes} bytes)")
        
        except Exception as e:
            logger.error(f"Error saving download state: {e}")
    
    def load_state(self, download_id: str) -> Optional[Dict]:
        """
        Load download state
        
        Args:
            download_id: Download ID
            
        Returns:
            State dictionary atau None
        """
        state_path = self.get_state_path(download_id)
        
        if not os.path.exists(state_path):
            return None
        
        try:
            with open(state_path, 'r') as f:
                state = json.load(f)
            
            # Verify partial file exists
            filepath = state.get('filepath')
            if filepath and os.path.exists(filepath):
                actual_size = os.path.getsize(filepath)
                state['actual_file_size'] = actual_size
                
                logger.info(f"Download state loaded: {download_id} ({actual_size} bytes on disk)")
                return state
            else:
                logger.warning(f"State file exists but download file missing: {filepath}")
                return None
        
        except Exception as e:
            logger.error(f"Error loading download state: {e}")
            return None
    
    def clear_state(self, download_id: str):
        """Clear download state after completion"""
        state_path = self.get_state_path(download_id)
        
        try:
            if os.path.exists(state_path):
                os.remove(state_path)
                logger.info(f"Download state cleared: {download_id}")
        except Exception as e:
            logger.error(f"Error clearing download state: {e}")
    
    def get_all_incomplete_downloads(self) -> list:
        """Get all incomplete downloads yang bisa di-resume"""
        incomplete = []
        
        try:
            for filename in os.listdir(self.state_dir):
                if filename.endswith('.json'):
                    download_id = filename[:-5]  # Remove .json
                    state = self.load_state(download_id)
                    
                    if state:
                        incomplete.append(state)
        
        except Exception as e:
            logger.error(f"Error getting incomplete downloads: {e}")
        
        return incomplete


class ResumableDownloader:
    """Downloader dengan resume capability menggunakan Range requests"""
    
    def __init__(self, state_manager: DownloadState):
        """
        Initialize resumable downloader
        
        Args:
            state_manager: DownloadState instance
        """
        self.state = state_manager
    
    async def download_with_resume(self, download_id: str, url: str, filepath: str,
                                   progress_callback=None) -> bool:
        """
        Download file dengan resume capability
        
        Args:
            download_id: Download ID
            url: Download URL
            filepath: Target filepath
            progress_callback: Progress callback function
            
        Returns:
            True jika berhasil
        """
        # Check if ada state untuk resume
        existing_state = self.state.load_state(download_id)
        
        if existing_state:
            logger.info(f"🔄 Resuming download: {download_id}")
            return await self._resume_download(download_id, existing_state, progress_callback)
        else:
            logger.info(f"🆕 Starting new download: {download_id}")
            return await self._start_download(download_id, url, filepath, progress_callback)
    
    async def _start_download(self, download_id: str, url: str, filepath: str,
                             progress_callback=None) -> bool:
        """Start new download dengan resume support"""
        try:
            headers = self._get_headers(url)
            
            async with aiohttp.ClientSession() as session:
                async with session.head(url, headers=headers) as response:
                    # Check if server supports range requests
                    accept_ranges = response.headers.get('Accept-Ranges', '')
                    supports_resume = accept_ranges.lower() == 'bytes'
                    
                    total_size = int(response.headers.get('Content-Length', 0))
                    
                    if not supports_resume:
                        logger.warning("Server doesn't support Range requests, resume not available")
                
                # Start download
                return await self._download_chunks(
                    download_id, url, filepath, 0, total_size, 
                    supports_resume, progress_callback
                )
        
        except Exception as e:
            logger.error(f"Error starting download: {e}")
            return False
    
    async def _resume_download(self, download_id: str, state: Dict,
                              progress_callback=None) -> bool:
        """Resume interrupted download"""
        url = state['url']
        filepath = state['filepath']
        start_byte = state['actual_file_size']  # Use actual file size on disk
        total_size = state['total_bytes']
        
        logger.info(f"📥 Resuming from byte {start_byte}/{total_size}")
        
        try:
            return await self._download_chunks(
                download_id, url, filepath, start_byte, total_size,
                True, progress_callback
            )
        
        except Exception as e:
            logger.error(f"Error resuming download: {e}")
            return False
    
    async def _download_chunks(self, download_id: str, url: str, filepath: str,
                              start_byte: int, total_size: int, 
                              supports_resume: bool, progress_callback=None) -> bool:
        """Download file in chunks dengan periodic state saving"""
        try:
            headers = self._get_headers(url)
            
            # Add Range header jika resume dari middle
            if start_byte > 0:
                headers['Range'] = f'bytes={start_byte}-'
                logger.info(f"📍 Range request: bytes={start_byte}-")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, 
                                      timeout=aiohttp.ClientTimeout(total=None)) as response:
                    # Check response status
                    if start_byte > 0:
                        if response.status != 206:  # Partial Content
                            logger.warning(f"Server returned {response.status} instead of 206, starting fresh")
                            start_byte = 0
                            # Start fresh download
                            return await self._start_download(download_id, url, filepath, progress_callback)
                    elif response.status != 200:
                        raise Exception(f"HTTP {response.status}")
                    
                    # Open file untuk append jika resume, write jika new
                    mode = 'ab' if start_byte > 0 else 'wb'
                    
                    downloaded_bytes = start_byte
                    chunk_size = 65536  # 64KB
                    save_state_interval = 1048576  # Save state every 1MB
                    last_state_save = downloaded_bytes
                    
                    async with aiofiles.open(filepath, mode) as f:
                        async for chunk in response.content.iter_chunked(chunk_size):
                            # Write chunk
                            await f.write(chunk)
                            downloaded_bytes += len(chunk)
                            
                            # Call progress callback
                            if progress_callback:
                                progress = (downloaded_bytes / total_size * 100) if total_size > 0 else 0
                                await progress_callback(downloaded_bytes, total_size, progress)
                            
                            # Save state periodically jika resume supported
                            if supports_resume and (downloaded_bytes - last_state_save) >= save_state_interval:
                                self.state.save_state(download_id, url, filepath, 
                                                     downloaded_bytes, total_size)
                                last_state_save = downloaded_bytes
                    
                    # Download complete
                    logger.info(f"✅ Download completed: {filepath} ({downloaded_bytes} bytes)")
                    
                    # Clear state
                    self.state.clear_state(download_id)
                    
                    return True
        
        except asyncio.TimeoutError:
            logger.error("Download timeout")
            # Save state untuk resume
            if supports_resume:
                current_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
                self.state.save_state(download_id, url, filepath, current_size, total_size)
            return False
        
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {e}")
            # Save state untuk resume
            if supports_resume:
                current_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
                self.state.save_state(download_id, url, filepath, current_size, total_size)
            return False
        
        except Exception as e:
            logger.error(f"Download error: {e}")
            # Save state jika error
            if supports_resume:
                try:
                    current_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
                    self.state.save_state(download_id, url, filepath, current_size, total_size)
                except:
                    pass
            return False
    
    def _get_headers(self, url: str) -> Dict[str, str]:
        """Get HTTP headers untuk request"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
        }
        
        # Add Referer
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            if parsed.netloc:
                headers['Referer'] = f"{parsed.scheme}://{parsed.netloc}/"
        except:
            pass
        
        return headers
