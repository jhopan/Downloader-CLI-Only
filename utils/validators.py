import re
from urllib.parse import urlparse
from typing import Tuple


def validate_url(url: str) -> Tuple[bool, str]:
    """
    Validasi URL
    Returns: (is_valid, message)
    """
    if not url:
        return False, "URL tidak boleh kosong."
    
    # Cek format URL dasar
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if not url_pattern.match(url):
        return False, "Format URL tidak valid. Pastikan URL dimulai dengan http:// atau https://"
    
    # Parse URL
    try:
        parsed = urlparse(url)
        
        if not parsed.scheme in ['http', 'https']:
            return False, "URL harus menggunakan protokol HTTP atau HTTPS."
        
        if not parsed.netloc:
            return False, "URL tidak memiliki domain yang valid."
        
        # Cek panjang URL
        if len(url) > 2048:
            return False, "URL terlalu panjang (maksimal 2048 karakter)."
        
        return True, "URL valid."
        
    except Exception as e:
        return False, f"Error saat memvalidasi URL: {str(e)}"


def is_direct_download_url(url: str) -> bool:
    """
    Cek apakah URL adalah direct download link
    """
    # Ekstensi file umum
    file_extensions = [
        '.zip', '.rar', '.7z', '.tar', '.gz',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx',
        '.mp3', '.mp4', '.avi', '.mkv', '.flv',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp',
        '.exe', '.apk', '.deb', '.rpm',
        '.iso', '.dmg', '.pkg'
    ]
    
    url_lower = url.lower()
    
    # Cek ekstensi file
    for ext in file_extensions:
        if url_lower.endswith(ext):
            return True
    
    # Cek parameter download
    if 'download' in url_lower or 'file' in url_lower:
        return True
    
    return False
