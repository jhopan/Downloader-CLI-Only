"""
File Preview Generator
Extract metadata dan generate thumbnails untuk berbagai file types
"""
import os
import mimetypes
from typing import Dict, Optional, Tuple
from PIL import Image
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class FilePreview:
    """Generate preview dan extract metadata dari files"""
    
    def __init__(self, thumbnail_dir: str = "downloads/thumbnails"):
        """
        Initialize preview generator
        
        Args:
            thumbnail_dir: Directory untuk simpan thumbnails
        """
        self.thumbnail_dir = thumbnail_dir
        os.makedirs(thumbnail_dir, exist_ok=True)
    
    def get_file_info(self, filepath: str) -> Dict:
        """
        Get basic file information
        
        Args:
            filepath: Path ke file
            
        Returns:
            Dictionary berisi file info
        """
        if not os.path.exists(filepath):
            return {}
        
        stat = os.stat(filepath)
        mime_type, _ = mimetypes.guess_type(filepath)
        
        return {
            'filename': os.path.basename(filepath),
            'filepath': filepath,
            'size': stat.st_size,
            'mime_type': mime_type or 'application/octet-stream',
            'file_type': self._get_file_category(mime_type),
            'modified_time': stat.st_mtime,
            'created_time': stat.st_ctime
        }
    
    def _get_file_category(self, mime_type: Optional[str]) -> str:
        """Categorize file based on MIME type"""
        if not mime_type:
            return 'other'
        
        if mime_type.startswith('video/'):
            return 'video'
        elif mime_type.startswith('audio/'):
            return 'audio'
        elif mime_type.startswith('image/'):
            return 'image'
        elif mime_type.startswith('text/') or 'document' in mime_type:
            return 'document'
        elif 'pdf' in mime_type:
            return 'document'
        elif any(x in mime_type for x in ['zip', 'rar', 'tar', '7z', 'gz']):
            return 'archive'
        else:
            return 'other'
    
    def extract_metadata(self, filepath: str) -> Dict:
        """
        Extract metadata dari file
        
        Args:
            filepath: Path ke file
            
        Returns:
            Metadata dictionary
        """
        info = self.get_file_info(filepath)
        file_type = info.get('file_type')
        
        try:
            if file_type == 'image':
                return self._extract_image_metadata(filepath, info)
            elif file_type == 'video':
                return self._extract_video_metadata(filepath, info)
            elif file_type == 'audio':
                return self._extract_audio_metadata(filepath, info)
            elif file_type == 'document':
                return self._extract_document_metadata(filepath, info)
            else:
                return info
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return info
    
    def _extract_image_metadata(self, filepath: str, info: Dict) -> Dict:
        """Extract metadata dari image file"""
        try:
            with Image.open(filepath) as img:
                info['width'] = img.width
                info['height'] = img.height
                info['format'] = img.format
                info['mode'] = img.mode
                
                # Extract EXIF jika ada
                if hasattr(img, '_getexif') and img._getexif():
                    exif = img._getexif()
                    info['has_exif'] = True
                    # Add relevant EXIF data
                else:
                    info['has_exif'] = False
                
                # Generate thumbnail
                thumbnail_path = self._generate_image_thumbnail(filepath, img)
                if thumbnail_path:
                    info['thumbnail_path'] = thumbnail_path
        
        except Exception as e:
            logger.error(f"Error extracting image metadata: {e}")
        
        return info
    
    def _extract_video_metadata(self, filepath: str, info: Dict) -> Dict:
        """Extract metadata dari video file (requires ffprobe)"""
        try:
            import subprocess
            import json
            
            # Use ffprobe untuk extract metadata
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                filepath
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                # Extract format info
                if 'format' in data:
                    fmt = data['format']
                    info['duration'] = float(fmt.get('duration', 0))
                    info['bitrate'] = int(fmt.get('bit_rate', 0))
                    info['format_name'] = fmt.get('format_name', '')
                
                # Extract video stream info
                for stream in data.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        info['width'] = stream.get('width', 0)
                        info['height'] = stream.get('height', 0)
                        info['codec'] = stream.get('codec_name', '')
                        info['fps'] = eval(stream.get('r_frame_rate', '0/1'))
                        break
                
                # Generate thumbnail
                thumbnail_path = self._generate_video_thumbnail(filepath)
                if thumbnail_path:
                    info['thumbnail_path'] = thumbnail_path
        
        except FileNotFoundError:
            logger.warning("ffprobe not found, video metadata extraction skipped")
        except Exception as e:
            logger.error(f"Error extracting video metadata: {e}")
        
        return info
    
    def _extract_audio_metadata(self, filepath: str, info: Dict) -> Dict:
        """Extract metadata dari audio file"""
        try:
            # Try using mutagen library
            from mutagen import File as MutagenFile
            
            audio = MutagenFile(filepath)
            
            if audio:
                info['duration'] = audio.info.length if hasattr(audio.info, 'length') else 0
                info['bitrate'] = audio.info.bitrate if hasattr(audio.info, 'bitrate') else 0
                info['sample_rate'] = audio.info.sample_rate if hasattr(audio.info, 'sample_rate') else 0
                
                # Extract tags
                if audio.tags:
                    info['title'] = str(audio.tags.get('title', [''])[0]) if 'title' in audio.tags else ''
                    info['artist'] = str(audio.tags.get('artist', [''])[0]) if 'artist' in audio.tags else ''
                    info['album'] = str(audio.tags.get('album', [''])[0]) if 'album' in audio.tags else ''
        
        except ImportError:
            logger.warning("mutagen not installed, audio metadata extraction skipped")
        except Exception as e:
            logger.error(f"Error extracting audio metadata: {e}")
        
        return info
    
    def _extract_document_metadata(self, filepath: str, info: Dict) -> Dict:
        """Extract metadata dari document"""
        try:
            ext = os.path.splitext(filepath)[1].lower()
            
            if ext == '.pdf':
                # Try PyPDF2
                try:
                    import PyPDF2
                    
                    with open(filepath, 'rb') as f:
                        pdf = PyPDF2.PdfReader(f)
                        info['pages'] = len(pdf.pages)
                        
                        # Extract metadata
                        if pdf.metadata:
                            info['title'] = pdf.metadata.get('/Title', '')
                            info['author'] = pdf.metadata.get('/Author', '')
                            info['subject'] = pdf.metadata.get('/Subject', '')
                except ImportError:
                    logger.warning("PyPDF2 not installed")
        
        except Exception as e:
            logger.error(f"Error extracting document metadata: {e}")
        
        return info
    
    def _generate_image_thumbnail(self, filepath: str, img: Image.Image = None) -> Optional[str]:
        """Generate thumbnail untuk image"""
        try:
            if img is None:
                img = Image.open(filepath)
            
            # Create thumbnail (max 200x200)
            img_copy = img.copy()
            img_copy.thumbnail((200, 200), Image.Resampling.LANCZOS)
            
            # Save thumbnail
            filename = os.path.basename(filepath)
            thumb_name = f"thumb_{filename}"
            thumb_path = os.path.join(self.thumbnail_dir, thumb_name)
            
            # Convert RGBA to RGB jika perlu
            if img_copy.mode == 'RGBA':
                img_copy = img_copy.convert('RGB')
            
            img_copy.save(thumb_path, 'JPEG', quality=85)
            
            return thumb_path
        
        except Exception as e:
            logger.error(f"Error generating image thumbnail: {e}")
            return None
    
    def _generate_video_thumbnail(self, filepath: str) -> Optional[str]:
        """Generate thumbnail untuk video (requires ffmpeg)"""
        try:
            import subprocess
            
            filename = os.path.basename(filepath)
            thumb_name = f"thumb_{os.path.splitext(filename)[0]}.jpg"
            thumb_path = os.path.join(self.thumbnail_dir, thumb_name)
            
            # Use ffmpeg untuk extract frame di 10% duration
            cmd = [
                'ffmpeg',
                '-i', filepath,
                '-ss', '00:00:01',  # 1 second in
                '-vframes', '1',
                '-vf', 'scale=200:-1',
                '-y',  # Overwrite
                thumb_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            
            if result.returncode == 0 and os.path.exists(thumb_path):
                return thumb_path
        
        except FileNotFoundError:
            logger.warning("ffmpeg not found, video thumbnail generation skipped")
        except Exception as e:
            logger.error(f"Error generating video thumbnail: {e}")
        
        return None
    
    def format_size(self, size_bytes: int) -> str:
        """Format file size untuk display"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    def format_duration(self, seconds: float) -> str:
        """Format duration untuk display"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
