import aiohttp
import asyncio
import urllib.request
import urllib.error
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class LinkValidator:
    """Validator untuk mengecek apakah link bisa didownload"""
    
    @staticmethod
    async def validate_link(url: str) -> Tuple[bool, Optional[str], Optional[dict]]:
        """Validasi apakah link bisa didownload
        
        Returns:
            Tuple (is_valid, error_message, file_info)
            - is_valid: True jika link valid dan bisa didownload
            - error_message: Pesan error jika ada
            - file_info: Dict dengan info file (size, type, filename)
        """
        # Try aiohttp first
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
            }
            
            async with aiohttp.ClientSession(headers=headers) as session:
                # Try HEAD request first
                try:
                    async with session.head(url, timeout=aiohttp.ClientTimeout(total=10), allow_redirects=True) as response:
                        if response.status == 200:
                            file_info = {
                                'size': int(response.headers.get('content-length', 0)),
                                'type': response.headers.get('content-type', 'unknown'),
                                'filename': LinkValidator._extract_filename_from_headers(response.headers, url)
                            }
                            return True, None, file_info
                        else:
                            logger.warning(f"HEAD returned {response.status}")
                except (aiohttp.ClientError, asyncio.TimeoutError) as head_err:
                    logger.warning(f"HEAD request failed: {head_err}")
                
                # Fallback: Try GET with Range header
                try:
                    range_headers = headers.copy()
                    range_headers['Range'] = 'bytes=0-1023'
                    async with session.get(url, headers=range_headers, timeout=aiohttp.ClientTimeout(total=10), allow_redirects=True) as get_response:
                        if get_response.status in [200, 206]:
                            file_info = {
                                'size': int(get_response.headers.get('content-length', 0)),
                                'type': get_response.headers.get('content-type', 'unknown'),
                                'filename': LinkValidator._extract_filename_from_headers(get_response.headers, url)
                            }
                            return True, None, file_info
                        else:
                            logger.warning(f"GET returned {get_response.status}")
                except (aiohttp.ClientError, asyncio.TimeoutError) as get_err:
                    logger.warning(f"GET request failed: {get_err}")
                    # Return False to trigger download attempt anyway
                    return False, f"Validation failed: {str(get_err)}", None
        
        except aiohttp.ClientError as e:
            error_msg = str(e)
            logger.warning(f"aiohttp validation failed: {error_msg}")
            # Return False but download manager will still try
            return False, error_msg, None
            
            # Fallback to urllib
            try:
                req = urllib.request.Request(url, method='HEAD')
                req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    file_info = {
                        'size': int(response.headers.get('content-length', 0)),
                        'type': response.headers.get('content-type', 'unknown'),
                        'filename': LinkValidator._extract_filename_from_headers(response.headers, url)
                    }
                    return True, None, file_info
            
            except urllib.error.HTTPError as ue:
                return False, f"HTTP {ue.code}: {ue.reason}", None
            except urllib.error.URLError as ue:
                return False, f"URL Error: {ue.reason}", None
            except Exception as ue:
                return False, str(ue), None
        
        except asyncio.TimeoutError:
            return False, "Timeout: Server tidak merespon", None
        except Exception as e:
            return False, str(e), None
    
    @staticmethod
    def _extract_filename_from_headers(headers, url: str) -> str:
        """Extract filename dari headers"""
        import re
        from urllib.parse import urlparse, unquote
        
        # Try Content-Disposition
        content_disp = headers.get('Content-Disposition', '')
        if content_disp and 'filename=' in content_disp:
            match = re.search(r'filename[*]?=["\']?([^"\';\r\n]+)', content_disp)
            if match:
                return match.group(1)
        
        # Fallback to URL
        parsed = urlparse(url)
        filename = parsed.path.split('/')[-1]
        return unquote(filename) if filename else 'unknown'
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Format ukuran file"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
