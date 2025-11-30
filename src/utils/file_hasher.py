"""
File hashing utility untuk duplicate detection
Mendukung MD5 dan SHA256 hashing dengan chunk processing
"""
import hashlib
import os
from typing import Optional, Literal
import logging

logger = logging.getLogger(__name__)

HashAlgorithm = Literal['md5', 'sha256']


class FileHasher:
    """Calculate file hash untuk duplicate detection"""
    
    def __init__(self, algorithm: HashAlgorithm = 'md5', chunk_size: int = 8192):
        """
        Initialize hasher
        
        Args:
            algorithm: 'md5' atau 'sha256'
            chunk_size: Size untuk chunk reading (default 8KB)
        """
        self.algorithm = algorithm
        self.chunk_size = chunk_size
    
    def calculate_hash(self, filepath: str) -> Optional[str]:
        """
        Calculate hash dari file
        
        Args:
            filepath: Path ke file
            
        Returns:
            Hash string atau None jika error
        """
        if not os.path.exists(filepath):
            logger.error(f"File tidak ditemukan: {filepath}")
            return None
        
        try:
            # Pilih hash algorithm
            if self.algorithm == 'md5':
                hasher = hashlib.md5()
            else:
                hasher = hashlib.sha256()
            
            # Read file in chunks untuk efficiency
            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(self.chunk_size)
                    if not chunk:
                        break
                    hasher.update(chunk)
            
            hash_value = hasher.hexdigest()
            logger.debug(f"{self.algorithm.upper()} hash untuk {os.path.basename(filepath)}: {hash_value}")
            return hash_value
            
        except Exception as e:
            logger.error(f"Error menghitung hash untuk {filepath}: {e}")
            return None
    
    def quick_hash(self, filepath: str, sample_size: int = 1048576) -> Optional[str]:
        """
        Calculate hash dari sample awal file (quick check untuk large files)
        
        Args:
            filepath: Path ke file
            sample_size: Size sample dalam bytes (default 1MB)
            
        Returns:
            Hash string dari sample atau None jika error
        """
        if not os.path.exists(filepath):
            return None
        
        try:
            if self.algorithm == 'md5':
                hasher = hashlib.md5()
            else:
                hasher = hashlib.sha256()
            
            with open(filepath, 'rb') as f:
                sample = f.read(sample_size)
                hasher.update(sample)
            
            return hasher.hexdigest()
            
        except Exception as e:
            logger.error(f"Error menghitung quick hash: {e}")
            return None


class DuplicateDetector:
    """Deteksi file duplicate dengan multiple methods"""
    
    def __init__(self, download_dir: str):
        """
        Initialize detector
        
        Args:
            download_dir: Directory untuk check duplicates
        """
        self.download_dir = download_dir
        self.hasher = FileHasher('md5')
    
    def find_duplicate(self, filename: str, file_size: int, file_hash: Optional[str] = None) -> Optional[str]:
        """
        Cari duplicate file di download directory
        
        Args:
            filename: Nama file yang dicari
            file_size: Size file dalam bytes
            file_hash: Hash file (optional, akan dihitung jika None)
            
        Returns:
            Path ke duplicate file atau None jika tidak ada
        """
        if not os.path.exists(self.download_dir):
            return None
        
        try:
            # Check 1: Filename dan size sama
            for existing_file in os.listdir(self.download_dir):
                existing_path = os.path.join(self.download_dir, existing_file)
                
                # Skip jika bukan file
                if not os.path.isfile(existing_path):
                    continue
                
                # Check filename dan size
                if existing_file == filename and os.path.getsize(existing_path) == file_size:
                    # Check 2: Verify dengan hash jika tersedia
                    if file_hash:
                        existing_hash = self.hasher.calculate_hash(existing_path)
                        if existing_hash == file_hash:
                            logger.info(f"🔍 Duplicate ditemukan (exact match): {filename}")
                            return existing_path
                    else:
                        logger.info(f"🔍 Duplicate ditemukan (name+size match): {filename}")
                        return existing_path
            
            # Check 3: Hash-based detection untuk files dengan nama berbeda
            if file_hash:
                for existing_file in os.listdir(self.download_dir):
                    existing_path = os.path.join(self.download_dir, existing_file)
                    
                    if not os.path.isfile(existing_path):
                        continue
                    
                    # Skip jika size berbeda (optimization)
                    if os.path.getsize(existing_path) != file_size:
                        continue
                    
                    existing_hash = self.hasher.calculate_hash(existing_path)
                    if existing_hash == file_hash:
                        logger.info(f"🔍 Duplicate ditemukan (hash match): {existing_file} = {filename}")
                        return existing_path
            
            return None
            
        except Exception as e:
            logger.error(f"Error saat mencari duplicate: {e}")
            return None
    
    def get_unique_filename(self, filename: str) -> str:
        """
        Generate unique filename jika ada duplicate
        
        Args:
            filename: Original filename
            
        Returns:
            Unique filename dengan counter
        """
        if not os.path.exists(self.download_dir):
            return filename
        
        base, ext = os.path.splitext(filename)
        counter = 1
        new_filename = filename
        
        while os.path.exists(os.path.join(self.download_dir, new_filename)):
            new_filename = f"{base} ({counter}){ext}"
            counter += 1
        
        return new_filename
