"""
Cloud Storage Downloader
Support untuk Google Drive, Dropbox, OneDrive
"""
import os
import re
import logging
from typing import Optional, Dict, Tuple
import aiohttp
import aiofiles

logger = logging.getLogger(__name__)


class CloudDownloader:
    """Download files dari cloud storage services"""
    
    def __init__(self):
        """Initialize cloud downloader"""
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get atau create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def detect_cloud_service(self, url: str) -> Optional[str]:
        """
        Detect cloud service dari URL
        
        Args:
            url: URL to check
            
        Returns:
            Service name atau None
        """
        url_lower = url.lower()
        
        if 'drive.google.com' in url_lower or 'docs.google.com' in url_lower:
            return 'google_drive'
        elif 'dropbox.com' in url_lower or 'dl.dropboxusercontent.com' in url_lower:
            return 'dropbox'
        elif 'onedrive' in url_lower or '1drv.ms' in url_lower or 'sharepoint.com' in url_lower:
            return 'onedrive'
        
        return None
    
    async def download_from_cloud(self, url: str, download_path: str) -> Tuple[bool, str]:
        """
        Download file dari cloud storage
        
        Args:
            url: Cloud storage URL
            download_path: Path untuk save file
            
        Returns:
            Tuple (success, message)
        """
        service = self.detect_cloud_service(url)
        
        if not service:
            return False, "Unknown cloud service"
        
        try:
            if service == 'google_drive':
                return await self._download_google_drive(url, download_path)
            elif service == 'dropbox':
                return await self._download_dropbox(url, download_path)
            elif service == 'onedrive':
                return await self._download_onedrive(url, download_path)
            else:
                return False, f"Service not supported: {service}"
        
        except Exception as e:
            logger.error(f"Error downloading from {service}: {e}")
            return False, str(e)
    
    async def _download_google_drive(self, url: str, download_path: str) -> Tuple[bool, str]:
        """
        Download dari Google Drive
        Supports:
        - https://drive.google.com/file/d/FILE_ID/view
        - https://drive.google.com/open?id=FILE_ID
        - https://docs.google.com/document/d/FILE_ID/edit
        """
        # Extract file ID
        file_id = self._extract_google_drive_id(url)
        
        if not file_id:
            return False, "Cannot extract Google Drive file ID"
        
        # Convert ke direct download URL
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        
        session = await self.get_session()
        
        try:
            # First request untuk get confirmation token (untuk large files)
            async with session.get(download_url) as response:
                # Check if file requires confirmation
                if 'confirm=' in str(response.url):
                    # Large file, need confirmation token
                    text = await response.text()
                    confirm_token = self._extract_confirm_token(text)
                    
                    if confirm_token:
                        download_url = f"{download_url}&confirm={confirm_token}"
                
                # Download file
                async with session.get(download_url) as dl_response:
                    if dl_response.status == 200:
                        # Check if it's an error page
                        content_type = dl_response.headers.get('Content-Type', '')
                        
                        if 'text/html' in content_type:
                            return False, "File not accessible or requires authentication"
                        
                        # Save file
                        async with aiofiles.open(download_path, 'wb') as f:
                            async for chunk in dl_response.content.iter_chunked(8192):
                                await f.write(chunk)
                        
                        return True, "Downloaded from Google Drive"
                    else:
                        return False, f"HTTP {dl_response.status}"
        
        except Exception as e:
            return False, str(e)
    
    def _extract_google_drive_id(self, url: str) -> Optional[str]:
        """Extract file ID dari Google Drive URL"""
        patterns = [
            r'/file/d/([a-zA-Z0-9_-]+)',
            r'id=([a-zA-Z0-9_-]+)',
            r'/document/d/([a-zA-Z0-9_-]+)',
            r'/presentation/d/([a-zA-Z0-9_-]+)',
            r'/spreadsheets/d/([a-zA-Z0-9_-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_confirm_token(self, html: str) -> Optional[str]:
        """Extract confirmation token dari Google Drive warning page"""
        patterns = [
            r'confirm=([0-9A-Za-z_-]+)',
            r'"confirm":"([0-9A-Za-z_-]+)"',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1)
        
        return None
    
    async def _download_dropbox(self, url: str, download_path: str) -> Tuple[bool, str]:
        """
        Download dari Dropbox
        Supports:
        - https://www.dropbox.com/s/XXXX/filename?dl=0
        - https://www.dropbox.com/sh/XXXX/YYYY?dl=0
        """
        # Convert share link ke direct download
        if '?dl=0' in url:
            download_url = url.replace('?dl=0', '?dl=1')
        elif '?dl=1' not in url:
            download_url = f"{url}?dl=1" if '?' not in url else f"{url}&dl=1"
        else:
            download_url = url
        
        # Replace www.dropbox.com dengan dl.dropboxusercontent.com untuk direct link
        download_url = download_url.replace('www.dropbox.com', 'dl.dropboxusercontent.com')
        
        session = await self.get_session()
        
        try:
            async with session.get(download_url) as response:
                if response.status == 200:
                    # Save file
                    async with aiofiles.open(download_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                    
                    return True, "Downloaded from Dropbox"
                else:
                    return False, f"HTTP {response.status}"
        
        except Exception as e:
            return False, str(e)
    
    async def _download_onedrive(self, url: str, download_path: str) -> Tuple[bool, str]:
        """
        Download dari OneDrive/SharePoint
        Supports:
        - https://onedrive.live.com/...
        - https://1drv.ms/...
        - https://xxx.sharepoint.com/...
        """
        # Convert share link ke direct download
        download_url = url
        
        # For 1drv.ms short links, need to resolve first
        if '1drv.ms' in url:
            session = await self.get_session()
            async with session.get(url, allow_redirects=True) as response:
                download_url = str(response.url)
        
        # Add download parameter
        if '?' in download_url:
            download_url = f"{download_url}&download=1"
        else:
            download_url = f"{download_url}?download=1"
        
        session = await self.get_session()
        
        try:
            async with session.get(download_url) as response:
                if response.status == 200:
                    # Check content type
                    content_type = response.headers.get('Content-Type', '')
                    
                    if 'text/html' in content_type and response.content_length and response.content_length < 100000:
                        # Might be error page
                        return False, "File not accessible or requires authentication"
                    
                    # Save file
                    async with aiofiles.open(download_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                    
                    return True, "Downloaded from OneDrive"
                else:
                    return False, f"HTTP {response.status}"
        
        except Exception as e:
            return False, str(e)
    
    async def get_file_info(self, url: str) -> Optional[Dict]:
        """
        Get file info dari cloud URL (size, name, etc)
        
        Args:
            url: Cloud URL
            
        Returns:
            File info dictionary atau None
        """
        service = self.detect_cloud_service(url)
        
        if not service:
            return None
        
        try:
            session = await self.get_session()
            
            # Send HEAD request
            async with session.head(url, allow_redirects=True) as response:
                if response.status == 200:
                    info = {
                        'service': service,
                        'url': url,
                        'size': response.headers.get('Content-Length', 0),
                        'content_type': response.headers.get('Content-Type', ''),
                    }
                    
                    # Try extract filename
                    content_disposition = response.headers.get('Content-Disposition', '')
                    if 'filename=' in content_disposition:
                        filename = content_disposition.split('filename=')[1].strip('"\'')
                        info['filename'] = filename
                    
                    return info
        
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
        
        return None


class CloudAuthManager:
    """Manage OAuth tokens untuk cloud services"""
    
    def __init__(self, db_manager):
        """
        Initialize auth manager
        
        Args:
            db_manager: Database manager instance
        """
        self.db = db_manager
    
    def save_token(self, user_id: int, service: str, token: str):
        """Save OAuth token"""
        self.db.save_cloud_token(user_id, service, token)
        logger.info(f"Token saved for {service}")
    
    def get_token(self, user_id: int, service: str) -> Optional[str]:
        """Get OAuth token"""
        return self.db.get_cloud_token(user_id, service)
    
    def has_token(self, user_id: int, service: str) -> bool:
        """Check if user has token for service"""
        token = self.get_token(user_id, service)
        return token is not None and len(token) > 0
