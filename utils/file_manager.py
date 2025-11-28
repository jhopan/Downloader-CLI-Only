import os
from typing import Dict, List, Tuple
from datetime import datetime


class FileManager:
    """Manager untuk mengelola dan mengkategorikan file downloads"""
    
    # Kategori file berdasarkan ekstensi
    CATEGORIES = {
        'Video': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpeg', '.mpg'],
        'Audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus'],
        'Foto': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico', '.tiff'],
        'Dokumen': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx', '.ppt', '.pptx', '.csv'],
        'Archive': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.iso'],
        'Executable': ['.exe', '.msi', '.apk', '.deb', '.rpm', '.dmg', '.pkg'],
        'Code': ['.py', '.js', '.java', '.cpp', '.c', '.h', '.html', '.css', '.php', '.go', '.rs', '.sh'],
        'Lainnya': []  # Default untuk file yang tidak masuk kategori
    }
    
    def __init__(self, base_path: str):
        self.base_path = os.path.abspath(base_path)
        os.makedirs(self.base_path, exist_ok=True)
    
    def get_file_category(self, filename: str) -> str:
        """Dapatkan kategori file berdasarkan ekstensi"""
        ext = os.path.splitext(filename)[1].lower()
        
        for category, extensions in self.CATEGORIES.items():
            if ext in extensions:
                return category
        
        return 'Lainnya'
    
    def get_all_files(self, categorized: bool = False) -> Dict[str, List[Dict]]:
        """Dapatkan semua file di folder downloads
        
        Args:
            categorized: Jika True, group by kategori. Jika False, return semua file
            
        Returns:
            Dict dengan kategori sebagai key dan list file info sebagai value
        """
        if not os.path.exists(self.base_path):
            return {}
        
        files_by_category = {category: [] for category in self.CATEGORIES.keys()}
        
        try:
            for filename in os.listdir(self.base_path):
                filepath = os.path.join(self.base_path, filename)
                
                # Skip directories
                if os.path.isdir(filepath):
                    continue
                
                # Get file info
                file_info = self.get_file_info(filename)
                
                # Categorize
                category = self.get_file_category(filename)
                files_by_category[category].append(file_info)
        
        except Exception as e:
            print(f"Error reading directory: {e}")
            return {}
        
        # Sort by modified time (newest first)
        for category in files_by_category:
            files_by_category[category].sort(key=lambda x: x['modified_time'], reverse=True)
        
        if categorized:
            # Remove empty categories
            return {k: v for k, v in files_by_category.items() if v}
        else:
            # Return all files in one list
            all_files = []
            for files in files_by_category.values():
                all_files.extend(files)
            all_files.sort(key=lambda x: x['modified_time'], reverse=True)
            return {'Semua File': all_files}
    
    def get_file_info(self, filename: str) -> Dict:
        """Dapatkan informasi detail file"""
        filepath = os.path.join(self.base_path, filename)
        
        try:
            stat = os.stat(filepath)
            
            return {
                'filename': filename,
                'filepath': filepath,
                'size': stat.st_size,
                'modified_time': stat.st_mtime,
                'modified_datetime': datetime.fromtimestamp(stat.st_mtime),
                'category': self.get_file_category(filename)
            }
        except Exception as e:
            return {
                'filename': filename,
                'filepath': filepath,
                'size': 0,
                'modified_time': 0,
                'modified_datetime': datetime.now(),
                'category': 'Lainnya',
                'error': str(e)
            }
    
    def get_storage_stats(self) -> Dict:
        """Dapatkan statistik storage"""
        import shutil
        
        try:
            total, used, free = shutil.disk_usage(self.base_path)
            
            # Calculate total size of files in downloads folder
            downloads_size = 0
            file_count = 0
            
            if os.path.exists(self.base_path):
                for filename in os.listdir(self.base_path):
                    filepath = os.path.join(self.base_path, filename)
                    if os.path.isfile(filepath):
                        downloads_size += os.path.getsize(filepath)
                        file_count += 1
            
            return {
                'total': total,
                'used': used,
                'free': free,
                'downloads_size': downloads_size,
                'file_count': file_count,
                'path': self.base_path
            }
        except Exception as e:
            return {
                'total': 0,
                'used': 0,
                'free': 0,
                'downloads_size': 0,
                'file_count': 0,
                'path': self.base_path,
                'error': str(e)
            }
    
    def delete_file(self, filename: str) -> bool:
        """Hapus file"""
        filepath = os.path.join(self.base_path, filename)
        
        try:
            if os.path.exists(filepath) and os.path.isfile(filepath):
                os.remove(filepath)
                return True
            return False
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False
    
    def move_to_category_folder(self, filename: str) -> Tuple[bool, str]:
        """Pindahkan file ke folder kategorinya
        
        Returns:
            Tuple (success, new_filepath)
        """
        category = self.get_file_category(filename)
        category_dir = os.path.join(self.base_path, category)
        
        os.makedirs(category_dir, exist_ok=True)
        
        old_path = os.path.join(self.base_path, filename)
        new_path = os.path.join(category_dir, filename)
        
        try:
            if os.path.exists(old_path):
                os.rename(old_path, new_path)
                return True, new_path
            return False, ""
        except Exception as e:
            print(f"Error moving file: {e}")
            return False, ""
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Format ukuran file ke human readable"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
