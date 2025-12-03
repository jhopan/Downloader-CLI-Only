"""
Link Checker/Validator
Validate links before download dengan HEAD request
Check file size, content type, dan availability
"""

import aiohttp
import asyncio
import logging
from typing import List, Dict, Optional
from urllib.parse import urlparse
from datetime import datetime

logger = logging.getLogger(__name__)


class LinkValidator:
    """Validate download links before downloading"""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*'
        }
    
    async def validate_link(self, url: str) -> Dict:
        """
        Validate single link
        
        Returns:
            Dict with keys: valid, status_code, file_size, content_type, error
        """
        result = {
            'url': url,
            'valid': False,
            'status_code': None,
            'file_size': None,
            'content_type': None,
            'filename': None,
            'error': None,
            'response_time': None
        }
        
        try:
            start_time = datetime.now()
            
            async with aiohttp.ClientSession() as session:
                # Try HEAD request first
                try:
                    async with session.head(
                        url, 
                        headers=self.headers, 
                        timeout=aiohttp.ClientTimeout(total=self.timeout),
                        allow_redirects=True
                    ) as response:
                        result['status_code'] = response.status
                        result['response_time'] = (datetime.now() - start_time).total_seconds()
                        
                        if response.status == 200:
                            result['valid'] = True
                            result['file_size'] = int(response.headers.get('content-length', 0))
                            result['content_type'] = response.headers.get('content-type', 'unknown')
                            
                            # Try to get filename from Content-Disposition
                            content_disp = response.headers.get('Content-Disposition', '')
                            if 'filename=' in content_disp:
                                import re
                                match = re.search(r'filename[*]?=["\']?([^"\';\r\n]+)', content_disp)
                                if match:
                                    result['filename'] = match.group(1)
                            
                            # Fallback to URL path
                            if not result['filename']:
                                parsed = urlparse(url)
                                result['filename'] = parsed.path.split('/')[-1] or 'download'
                        
                        elif response.status == 405:  # Method Not Allowed
                            # Some servers don't support HEAD, try GET
                            raise aiohttp.ClientError("HEAD not allowed")
                        
                        else:
                            result['error'] = f"HTTP {response.status}"
                
                except (aiohttp.ClientError, asyncio.TimeoutError):
                    # Fallback to GET request with range header
                    async with session.get(
                        url,
                        headers={**self.headers, 'Range': 'bytes=0-0'},
                        timeout=aiohttp.ClientTimeout(total=self.timeout),
                        allow_redirects=True
                    ) as response:
                        result['status_code'] = response.status
                        result['response_time'] = (datetime.now() - start_time).total_seconds()
                        
                        if response.status in [200, 206]:  # OK or Partial Content
                            result['valid'] = True
                            
                            # Get file size from Content-Range or Content-Length
                            content_range = response.headers.get('Content-Range', '')
                            if content_range:
                                # Format: bytes 0-0/12345
                                import re
                                match = re.search(r'/(\d+)', content_range)
                                if match:
                                    result['file_size'] = int(match.group(1))
                            else:
                                result['file_size'] = int(response.headers.get('content-length', 0))
                            
                            result['content_type'] = response.headers.get('content-type', 'unknown')
                            
                            # Get filename
                            content_disp = response.headers.get('Content-Disposition', '')
                            if 'filename=' in content_disp:
                                import re
                                match = re.search(r'filename[*]?=["\']?([^"\';\r\n]+)', content_disp)
                                if match:
                                    result['filename'] = match.group(1)
                            
                            if not result['filename']:
                                parsed = urlparse(url)
                                result['filename'] = parsed.path.split('/')[-1] or 'download'
                        else:
                            result['error'] = f"HTTP {response.status}"
        
        except asyncio.TimeoutError:
            result['error'] = "Timeout - Server tidak merespon"
        except aiohttp.ClientError as e:
            result['error'] = f"Connection error: {str(e)}"
        except Exception as e:
            result['error'] = f"Error: {str(e)}"
        
        return result
    
    async def validate_links(self, urls: List[str]) -> List[Dict]:
        """
        Validate multiple links concurrently
        
        Args:
            urls: List of URLs to validate
            
        Returns:
            List of validation results
        """
        tasks = [self.validate_link(url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Format file size to human readable"""
        if size_bytes == 0:
            return "Unknown"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    @staticmethod
    def get_content_category(content_type: str) -> str:
        """Get file category from content type"""
        content_type = content_type.lower()
        
        if 'video' in content_type:
            return "🎬 Video"
        elif 'audio' in content_type:
            return "🎵 Audio"
        elif 'image' in content_type:
            return "🖼️ Image"
        elif 'pdf' in content_type:
            return "📄 PDF"
        elif 'zip' in content_type or 'rar' in content_type or '7z' in content_type:
            return "📦 Archive"
        elif 'text' in content_type:
            return "📝 Text"
        elif 'application' in content_type:
            return "📎 Application"
        else:
            return "📎 File"
