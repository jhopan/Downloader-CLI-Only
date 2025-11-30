import sqlite3
import logging
from typing import Optional, Dict, List
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class Database:
    """Database manager untuk menyimpan user preferences dan download history"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_database()
    
    def _get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def _init_database(self):
        """Initialize database tables"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Table untuk user preferences
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id INTEGER PRIMARY KEY,
                custom_download_path TEXT,
                use_custom_path INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # Table untuk download history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS download_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                download_id TEXT UNIQUE,
                url TEXT,
                filename TEXT,
                filepath TEXT,
                status TEXT,
                file_size INTEGER,
                start_time TEXT,
                end_time TEXT,
                error_message TEXT
            )
        ''')
        
        # Table untuk scheduled downloads
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                schedule_id TEXT UNIQUE,
                url TEXT,
                scheduled_time TEXT,
                created_time TEXT,
                status TEXT,
                download_id TEXT,
                executed_time TEXT,
                download_path TEXT
            )
        ''')
        
        # Table untuk batch downloads
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS batch_downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                batch_id TEXT UNIQUE,
                total_urls INTEGER,
                completed_urls INTEGER DEFAULT 0,
                failed_urls INTEGER DEFAULT 0,
                status TEXT,
                created_time TEXT,
                completed_time TEXT
            )
        ''')
        
        # Table untuk batch download items
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS batch_download_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT,
                url TEXT,
                download_id TEXT,
                status TEXT,
                filename TEXT,
                error_message TEXT,
                FOREIGN KEY (batch_id) REFERENCES batch_downloads(batch_id)
            )
        ''')
        
        # Table untuk bandwidth settings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bandwidth_settings (
                user_id INTEGER PRIMARY KEY,
                max_speed_kbps INTEGER DEFAULT 0,
                schedule_enabled INTEGER DEFAULT 0,
                schedule_start_time TEXT,
                schedule_end_time TEXT,
                schedule_speed_kbps INTEGER,
                updated_at TEXT
            )
        ''')
        
        # Table untuk file hashes (duplicate detection)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_hashes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                filename TEXT,
                filepath TEXT,
                file_size INTEGER,
                md5_hash TEXT,
                sha256_hash TEXT,
                created_time TEXT,
                UNIQUE(filepath)
            )
        ''')
        
        # Table untuk download queue
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS download_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                queue_id TEXT UNIQUE,
                user_id INTEGER,
                url TEXT,
                filename TEXT,
                priority INTEGER DEFAULT 2,
                status TEXT,
                download_id TEXT,
                added_time TEXT,
                started_time TEXT,
                completed_time TEXT,
                error_message TEXT,
                file_size INTEGER DEFAULT 0,
                downloaded_size INTEGER DEFAULT 0,
                progress REAL DEFAULT 0.0
            )
        ''')
        
        # Table untuk file metadata (preview info)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filepath TEXT UNIQUE,
                file_type TEXT,
                mime_type TEXT,
                duration INTEGER,
                width INTEGER,
                height INTEGER,
                thumbnail_path TEXT,
                metadata_json TEXT,
                extracted_time TEXT
            )
        ''')
        
        # Table untuk download statistics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS download_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date TEXT,
                total_downloads INTEGER DEFAULT 0,
                total_bytes INTEGER DEFAULT 0,
                successful_downloads INTEGER DEFAULT 0,
                failed_downloads INTEGER DEFAULT 0,
                avg_speed_kbps REAL DEFAULT 0.0,
                UNIQUE(user_id, date)
            )
        ''')
        
        # Table untuk cloud service tokens
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cloud_tokens (
                user_id INTEGER PRIMARY KEY,
                google_drive_token TEXT,
                dropbox_token TEXT,
                onedrive_token TEXT,
                updated_at TEXT
            )
        ''')
        
        # Table untuk smart categorization rules
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categorization_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                pattern TEXT,
                category TEXT,
                confidence REAL DEFAULT 1.0,
                created_time TEXT,
                last_used TEXT,
                use_count INTEGER DEFAULT 0
            )
        ''')
        
        # Table untuk virus scan results
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS virus_scan_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                filepath TEXT,
                filename TEXT,
                scan_time TEXT,
                status TEXT,
                infected INTEGER DEFAULT 0,
                threats TEXT,
                scanners TEXT,
                quarantined INTEGER DEFAULT 0
            )
        ''')
        
        # Table untuk encryption passwords (obfuscated)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS encryption_passwords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                filename TEXT,
                encrypted_filename TEXT,
                password_hint TEXT,
                created_time TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    # ===== USER PREFERENCES =====
    
    def get_user_preference(self, user_id: int) -> Optional[Dict]:
        """Get user preference"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, custom_download_path, use_custom_path, created_at, updated_at
            FROM user_preferences
            WHERE user_id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'user_id': row[0],
                'custom_download_path': row[1],
                'use_custom_path': bool(row[2]),
                'created_at': row[3],
                'updated_at': row[4]
            }
        return None
    
    def set_user_download_path(self, user_id: int, path: str, use_custom: bool = True):
        """Set custom download path for user"""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        # Check if exists
        existing = self.get_user_preference(user_id)
        
        if existing:
            cursor.execute('''
                UPDATE user_preferences
                SET custom_download_path = ?, use_custom_path = ?, updated_at = ?
                WHERE user_id = ?
            ''', (path, int(use_custom), now, user_id))
        else:
            cursor.execute('''
                INSERT INTO user_preferences (user_id, custom_download_path, use_custom_path, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, path, int(use_custom), now, now))
        
        conn.commit()
        conn.close()
        logger.info(f"User {user_id} download path updated: {path}")
    
    def toggle_custom_path(self, user_id: int, use_custom: bool):
        """Toggle penggunaan custom path"""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            UPDATE user_preferences
            SET use_custom_path = ?, updated_at = ?
            WHERE user_id = ?
        ''', (int(use_custom), now, user_id))
        
        conn.commit()
        conn.close()
    
    def get_download_path(self, user_id: int, default_path: str) -> str:
        """Get download path untuk user (custom atau default)"""
        pref = self.get_user_preference(user_id)
        
        if pref and pref['use_custom_path'] and pref['custom_download_path']:
            # Pastikan folder exist
            os.makedirs(pref['custom_download_path'], exist_ok=True)
            return pref['custom_download_path']
        
        return default_path
    
    # ===== DOWNLOAD HISTORY =====
    
    def add_download_history(self, user_id: int, download_id: str, url: str, 
                            filename: str, filepath: str, status: str):
        """Add download history"""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO download_history 
            (user_id, download_id, url, filename, filepath, status, start_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, download_id, url, filename, filepath, status, now))
        
        conn.commit()
        conn.close()
    
    def update_download_history(self, download_id: str, status: str, 
                               file_size: Optional[int] = None,
                               error_message: Optional[str] = None):
        """Update download history"""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        if file_size is not None:
            cursor.execute('''
                UPDATE download_history
                SET status = ?, file_size = ?, end_time = ?, error_message = ?
                WHERE download_id = ?
            ''', (status, file_size, now, error_message, download_id))
        else:
            cursor.execute('''
                UPDATE download_history
                SET status = ?, end_time = ?, error_message = ?
                WHERE download_id = ?
            ''', (status, now, error_message, download_id))
        
        conn.commit()
        conn.close()
    
    def get_download_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get download history for user"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT download_id, url, filename, status, file_size, start_time, end_time
            FROM download_history
            WHERE user_id = ?
            ORDER BY start_time DESC
            LIMIT ?
        ''', (user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'download_id': row[0],
                'url': row[1],
                'filename': row[2],
                'status': row[3],
                'file_size': row[4],
                'start_time': row[5],
                'end_time': row[6]
            }
            for row in rows
        ]
    
    # ===== SCHEDULED DOWNLOADS =====
    
    def add_scheduled_download(self, user_id: int, schedule_id: str, url: str,
                              scheduled_time: str, download_path: str):
        """Add scheduled download"""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO scheduled_downloads
            (user_id, schedule_id, url, scheduled_time, created_time, status, download_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, schedule_id, url, scheduled_time, now, 'pending', download_path))
        
        conn.commit()
        conn.close()
    
    def get_pending_schedules(self) -> List[Dict]:
        """Get all pending scheduled downloads"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT schedule_id, user_id, url, scheduled_time, download_path
            FROM scheduled_downloads
            WHERE status = 'pending'
            ORDER BY scheduled_time ASC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'schedule_id': row[0],
                'user_id': row[1],
                'url': row[2],
                'scheduled_time': row[3],
                'download_path': row[4]
            }
            for row in rows
        ]
    
    def update_schedule_status(self, schedule_id: str, status: str, 
                              download_id: Optional[str] = None):
        """Update schedule status"""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        if download_id:
            cursor.execute('''
                UPDATE scheduled_downloads
                SET status = ?, download_id = ?, executed_time = ?
                WHERE schedule_id = ?
            ''', (status, download_id, now, schedule_id))
        else:
            cursor.execute('''
                UPDATE scheduled_downloads
                SET status = ?, executed_time = ?
                WHERE schedule_id = ?
            ''', (status, now, schedule_id))
        
        conn.commit()
        conn.close()
    
    def get_user_schedules(self, user_id: int) -> List[Dict]:
        """Get user's scheduled downloads"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT schedule_id, url, scheduled_time, status, download_id
            FROM scheduled_downloads
            WHERE user_id = ? AND status IN ('pending', 'executing')
            ORDER BY scheduled_time ASC
        ''', (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'schedule_id': row[0],
                'url': row[1],
                'scheduled_time': row[2],
                'status': row[3],
                'download_id': row[4]
            }
            for row in rows
        ]

def add_batch_download(self, user_id: int, batch_id: str, total_urls: int):
    """Create new batch download"""
    conn = self._get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO batch_downloads
        (user_id, batch_id, total_urls, status, created_time)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, batch_id, total_urls, 'processing', now))
    
    conn.commit()
    conn.close()

def add_batch_item(self, batch_id: str, url: str, download_id: str):
    """Add item to batch"""
    conn = self._get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO batch_download_items
        (batch_id, url, download_id, status)
        VALUES (?, ?, ?, ?)
    ''', (batch_id, url, download_id, 'pending'))
    
    conn.commit()
    conn.close()

def update_batch_item_status(self, batch_id: str, download_id: str, 
                             status: str, filename: Optional[str] = None,
                             error_message: Optional[str] = None):
    """Update batch item status"""
    conn = self._get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE batch_download_items
        SET status = ?, filename = ?, error_message = ?
        WHERE batch_id = ? AND download_id = ?
    ''', (status, filename, error_message, batch_id, download_id))
    
    conn.commit()
    conn.close()
    
    # Update batch progress
    self._update_batch_progress(batch_id)

def _update_batch_progress(self, batch_id: str):
    """Update batch download progress"""
    conn = self._get_connection()
    cursor = conn.cursor()
    
    # Count completed and failed
    cursor.execute('''
        SELECT 
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
            COUNT(*) as total
        FROM batch_download_items
        WHERE batch_id = ?
    ''', (batch_id,))
    
    row = cursor.fetchone()
    completed = row[0] or 0
    failed = row[1] or 0
    total = row[2]
    
    # Update batch
    status = 'completed' if (completed + failed) == total else 'processing'
    completed_time = datetime.now().isoformat() if status == 'completed' else None
    
    cursor.execute('''
        UPDATE batch_downloads
        SET completed_urls = ?, failed_urls = ?, status = ?, completed_time = ?
        WHERE batch_id = ?
    ''', (completed, failed, status, completed_time, batch_id))
    
    conn.commit()
    conn.close()

def get_batch_info(self, batch_id: str) -> Optional[Dict]:
    """Get batch download info"""
    conn = self._get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT batch_id, total_urls, completed_urls, failed_urls, status,
               created_time, completed_time
        FROM batch_downloads
        WHERE batch_id = ?
    ''', (batch_id,))
    
    row = cursor.fetchone()
    
    if row:
        # Get items
        cursor.execute('''
            SELECT url, status, filename, error_message
            FROM batch_download_items
            WHERE batch_id = ?
            ORDER BY id ASC
        ''', (batch_id,))
        
        items = cursor.fetchall()
        conn.close()
        
        return {
            'batch_id': row[0],
            'total_urls': row[1],
            'completed_urls': row[2],
            'failed_urls': row[3],
            'status': row[4],
            'created_time': row[5],
            'completed_time': row[6],
            'items': [
                {
                    'url': item[0],
                    'status': item[1],
                    'filename': item[2],
                    'error_message': item[3]
                }
                for item in items
            ]
        }
    
    conn.close()
    return None

def get_user_batches(self, user_id: int, limit: int = 10) -> List[Dict]:
    """Get user's batch downloads"""
    conn = self._get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT batch_id, total_urls, completed_urls, failed_urls, status, created_time
        FROM batch_downloads
        WHERE user_id = ?
        ORDER BY created_time DESC
        LIMIT ?
    ''', (user_id, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            'batch_id': row[0],
            'total_urls': row[1],
            'completed_urls': row[2],
            'failed_urls': row[3],
            'status': row[4],
            'created_time': row[5]
        }
        for row in rows
    ]

# ===== BANDWIDTH SETTINGS =====

def get_bandwidth_settings(self, user_id: int) -> Optional[Dict]:
    """Get bandwidth settings for user"""
    conn = self._get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT max_speed_kbps, schedule_enabled, schedule_start_time,
               schedule_end_time, schedule_speed_kbps
        FROM bandwidth_settings
        WHERE user_id = ?
    ''', (user_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'max_speed_kbps': row[0],
            'schedule_enabled': bool(row[1]),
            'schedule_start_time': row[2],
            'schedule_end_time': row[3],
            'schedule_speed_kbps': row[4]
        }
    return None

def set_bandwidth_limit(self, user_id: int, max_speed_kbps: int):
    """Set bandwidth limit for user"""
    conn = self._get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    # Check if exists
    existing = self.get_bandwidth_settings(user_id)
    
    if existing:
        cursor.execute('''
            UPDATE bandwidth_settings
            SET max_speed_kbps = ?, updated_at = ?
            WHERE user_id = ?
        ''', (max_speed_kbps, now, user_id))
    else:
        cursor.execute('''
            INSERT INTO bandwidth_settings (user_id, max_speed_kbps, updated_at)
            VALUES (?, ?, ?)
        ''', (user_id, max_speed_kbps, now))
    
    conn.commit()
    conn.close()

def set_bandwidth_schedule(self, user_id: int, enabled: bool, 
                          start_time: str, end_time: str, speed_kbps: int):
    """Set bandwidth schedule for user"""
    conn = self._get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    # Check if exists
    existing = self.get_bandwidth_settings(user_id)
    
    if existing:
        cursor.execute('''
            UPDATE bandwidth_settings
            SET schedule_enabled = ?, schedule_start_time = ?, 
                schedule_end_time = ?, schedule_speed_kbps = ?, updated_at = ?
            WHERE user_id = ?
        ''', (int(enabled), start_time, end_time, speed_kbps, now, user_id))
    else:
        cursor.execute('''
            INSERT INTO bandwidth_settings 
            (user_id, schedule_enabled, schedule_start_time, schedule_end_time,
             schedule_speed_kbps, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, int(enabled), start_time, end_time, speed_kbps, now))
    
    conn.commit()
    conn.close()

def get_current_bandwidth_limit(self, user_id: int) -> int:
    """Get current bandwidth limit based on time and settings"""
    from datetime import datetime
    
    settings = self.get_bandwidth_settings(user_id)
    
    if not settings:
        return 0  # No limit
    
    # Check if schedule is enabled
    if settings['schedule_enabled'] and settings['schedule_start_time'] and settings['schedule_end_time']:
        now = datetime.now().time()
        start = datetime.strptime(settings['schedule_start_time'], '%H:%M').time()
        end = datetime.strptime(settings['schedule_end_time'], '%H:%M').time()
        
        # Check if current time is in scheduled range
        if start <= end:
            # Normal range (e.g., 09:00 - 17:00)
            if start <= now <= end:
                return settings['schedule_speed_kbps'] or 0
        else:
            # Overnight range (e.g., 22:00 - 06:00)
            if now >= start or now <= end:
                return settings['schedule_speed_kbps'] or 0
    
    # Return default max speed
    return settings['max_speed_kbps'] or 0

    # ===== FILE HASHES (DUPLICATE DETECTION) =====
    
    def add_file_hash(self, user_id: int, filename: str, filepath: str, 
                     file_size: int, md5_hash: str, sha256_hash: Optional[str] = None):
        """Add file hash to database"""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT OR REPLACE INTO file_hashes
            (user_id, filename, filepath, file_size, md5_hash, sha256_hash, created_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, filename, filepath, file_size, md5_hash, sha256_hash, now))
        
        conn.commit()
        conn.close()
    
    def find_duplicate_by_hash(self, md5_hash: str, user_id: Optional[int] = None) -> Optional[Dict]:
        """Find duplicate file by MD5 hash"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute('''
                SELECT filename, filepath, file_size, created_time
                FROM file_hashes
                WHERE md5_hash = ? AND user_id = ?
                ORDER BY created_time DESC
                LIMIT 1
            ''', (md5_hash, user_id))
        else:
            cursor.execute('''
                SELECT filename, filepath, file_size, created_time
                FROM file_hashes
                WHERE md5_hash = ?
                ORDER BY created_time DESC
                LIMIT 1
            ''', (md5_hash,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'filename': row[0],
                'filepath': row[1],
                'file_size': row[2],
                'created_time': row[3]
            }
        return None
    
    def get_file_hashes(self, user_id: int) -> List[Dict]:
        """Get all file hashes for user"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT filename, filepath, file_size, md5_hash, created_time
            FROM file_hashes
            WHERE user_id = ?
            ORDER BY created_time DESC
        ''', (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'filename': row[0],
                'filepath': row[1],
                'file_size': row[2],
                'md5_hash': row[3],
                'created_time': row[4]
            }
            for row in rows
        ]
    
    # ===== DOWNLOAD QUEUE =====
    
    def add_to_queue(self, user_id: int, queue_id: str, url: str, filename: str, 
                    priority: int = 2) -> bool:
        """Add item to download queue"""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        try:
            cursor.execute('''
                INSERT INTO download_queue
                (queue_id, user_id, url, filename, priority, status, added_time)
                VALUES (?, ?, ?, ?, ?, 'pending', ?)
            ''', (queue_id, user_id, url, filename, priority, now))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error adding to queue: {e}")
            conn.close()
            return False
    
    def update_queue_status(self, queue_id: str, status: str, download_id: Optional[str] = None,
                           error_message: Optional[str] = None):
        """Update queue item status"""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        if status == 'downloading':
            cursor.execute('''
                UPDATE download_queue
                SET status = ?, download_id = ?, started_time = ?
                WHERE queue_id = ?
            ''', (status, download_id, now, queue_id))
        elif status in ['completed', 'failed', 'cancelled']:
            cursor.execute('''
                UPDATE download_queue
                SET status = ?, completed_time = ?, error_message = ?
                WHERE queue_id = ?
            ''', (status, now, error_message, queue_id))
        else:
            cursor.execute('''
                UPDATE download_queue
                SET status = ?
                WHERE queue_id = ?
            ''', (status, queue_id))
        
        conn.commit()
        conn.close()
    
    def update_queue_progress(self, queue_id: str, downloaded_size: int, 
                             file_size: int, progress: float):
        """Update queue item progress"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE download_queue
            SET downloaded_size = ?, file_size = ?, progress = ?
            WHERE queue_id = ?
        ''', (downloaded_size, file_size, progress, queue_id))
        
        conn.commit()
        conn.close()
    
    def get_queue_items(self, user_id: Optional[int] = None, status: Optional[str] = None) -> List[Dict]:
        """Get queue items"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT queue_id, user_id, url, filename, priority, status, download_id, ' \
                'added_time, started_time, completed_time, error_message, file_size, ' \
                'downloaded_size, progress FROM download_queue WHERE 1=1'
        params = []
        
        if user_id:
            query += ' AND user_id = ?'
            params.append(user_id)
        
        if status:
            query += ' AND status = ?'
            params.append(status)
        
        query += ' ORDER BY priority DESC, added_time ASC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'queue_id': row[0],
                'user_id': row[1],
                'url': row[2],
                'filename': row[3],
                'priority': row[4],
                'status': row[5],
                'download_id': row[6],
                'added_time': row[7],
                'started_time': row[8],
                'completed_time': row[9],
                'error_message': row[10],
                'file_size': row[11],
                'downloaded_size': row[12],
                'progress': row[13]
            }
            for row in rows
        ]
    
    def change_queue_priority(self, queue_id: str, new_priority: int) -> bool:
        """Change queue item priority"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE download_queue
            SET priority = ?
            WHERE queue_id = ?
        ''', (new_priority, queue_id))
        
        conn.commit()
        changed = cursor.rowcount > 0
        conn.close()
        return changed
    
    def remove_from_queue(self, queue_id: str) -> bool:
        """Remove item from queue"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM download_queue WHERE queue_id = ?', (queue_id,))
        
        conn.commit()
        removed = cursor.rowcount > 0
        conn.close()
        return removed
    
    # ===== FILE METADATA (PREVIEW) =====
    
    def add_file_metadata(self, filepath: str, file_type: str, mime_type: str,
                         metadata: Dict):
        """Add file metadata for preview"""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        import json
        metadata_json = json.dumps(metadata)
        
        cursor.execute('''
            INSERT OR REPLACE INTO file_metadata
            (filepath, file_type, mime_type, duration, width, height, 
             thumbnail_path, metadata_json, extracted_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (filepath, file_type, mime_type, 
              metadata.get('duration'), metadata.get('width'), metadata.get('height'),
              metadata.get('thumbnail_path'), metadata_json, now))
        
        conn.commit()
        conn.close()
    
    def get_file_metadata(self, filepath: str) -> Optional[Dict]:
        """Get file metadata"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT file_type, mime_type, duration, width, height, 
                   thumbnail_path, metadata_json
            FROM file_metadata
            WHERE filepath = ?
        ''', (filepath,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            import json
            return {
                'file_type': row[0],
                'mime_type': row[1],
                'duration': row[2],
                'width': row[3],
                'height': row[4],
                'thumbnail_path': row[5],
                'metadata': json.loads(row[6]) if row[6] else {}
            }
        return None
    
    # ===== DOWNLOAD STATISTICS =====
    
    def update_statistics(self, user_id: int, bytes_downloaded: int, 
                         success: bool, speed_kbps: float):
        """Update download statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()
        today = datetime.now().date().isoformat()
        
        # Get existing stats
        cursor.execute('''
            SELECT total_downloads, total_bytes, successful_downloads, 
                   failed_downloads, avg_speed_kbps
            FROM download_statistics
            WHERE user_id = ? AND date = ?
        ''', (user_id, today))
        
        row = cursor.fetchone()
        
        if row:
            # Update existing
            total_downloads = row[0] + 1
            total_bytes = row[1] + bytes_downloaded
            successful = row[2] + (1 if success else 0)
            failed = row[3] + (0 if success else 1)
            # Calculate new average speed
            avg_speed = (row[4] * row[0] + speed_kbps) / total_downloads
            
            cursor.execute('''
                UPDATE download_statistics
                SET total_downloads = ?, total_bytes = ?, successful_downloads = ?,
                    failed_downloads = ?, avg_speed_kbps = ?
                WHERE user_id = ? AND date = ?
            ''', (total_downloads, total_bytes, successful, failed, avg_speed, user_id, today))
        else:
            # Insert new
            cursor.execute('''
                INSERT INTO download_statistics
                (user_id, date, total_downloads, total_bytes, successful_downloads,
                 failed_downloads, avg_speed_kbps)
                VALUES (?, ?, 1, ?, ?, ?, ?)
            ''', (user_id, today, bytes_downloaded, 1 if success else 0, 
                  0 if success else 1, speed_kbps))
        
        conn.commit()
        conn.close()
    
    def get_statistics(self, user_id: int, days: int = 30) -> List[Dict]:
        """Get download statistics for last N days"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT date, total_downloads, total_bytes, successful_downloads,
                   failed_downloads, avg_speed_kbps
            FROM download_statistics
            WHERE user_id = ?
            ORDER BY date DESC
            LIMIT ?
        ''', (user_id, days))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'date': row[0],
                'total_downloads': row[1],
                'total_bytes': row[2],
                'successful_downloads': row[3],
                'failed_downloads': row[4],
                'avg_speed_kbps': row[5]
            }
            for row in rows
        ]
    
    # ===== CLOUD TOKENS =====
    
    def save_cloud_token(self, user_id: int, service: str, token: str):
        """Save cloud service token"""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        # Get existing tokens
        cursor.execute('SELECT google_drive_token, dropbox_token, onedrive_token FROM cloud_tokens WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        
        if row:
            # Update specific service token
            if service == 'google_drive':
                cursor.execute('UPDATE cloud_tokens SET google_drive_token = ?, updated_at = ? WHERE user_id = ?',
                             (token, now, user_id))
            elif service == 'dropbox':
                cursor.execute('UPDATE cloud_tokens SET dropbox_token = ?, updated_at = ? WHERE user_id = ?',
                             (token, now, user_id))
            elif service == 'onedrive':
                cursor.execute('UPDATE cloud_tokens SET onedrive_token = ?, updated_at = ? WHERE user_id = ?',
                             (token, now, user_id))
        else:
            # Insert new row
            if service == 'google_drive':
                cursor.execute('INSERT INTO cloud_tokens (user_id, google_drive_token, updated_at) VALUES (?, ?, ?)',
                             (user_id, token, now))
            elif service == 'dropbox':
                cursor.execute('INSERT INTO cloud_tokens (user_id, dropbox_token, updated_at) VALUES (?, ?, ?)',
                             (user_id, token, now))
            elif service == 'onedrive':
                cursor.execute('INSERT INTO cloud_tokens (user_id, onedrive_token, updated_at) VALUES (?, ?, ?)',
                             (user_id, token, now))
        
        conn.commit()
        conn.close()
    
    def get_cloud_token(self, user_id: int, service: str) -> Optional[str]:
        """Get cloud service token"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT google_drive_token, dropbox_token, onedrive_token FROM cloud_tokens WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            if service == 'google_drive':
                return row[0]
            elif service == 'dropbox':
                return row[1]
            elif service == 'onedrive':
                return row[2]
        
        return None
    
    # ===== SMART CATEGORIZATION =====
    
    def add_categorization_rule(self, user_id: int, pattern: str, category: str, 
                               confidence: float = 1.0):
        """Add categorization rule"""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO categorization_rules
            (user_id, pattern, category, confidence, created_time, last_used, use_count)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        ''', (user_id, pattern, category, confidence, now, now))
        
        conn.commit()
        conn.close()
    
    def get_categorization_rules(self, user_id: int) -> List[Dict]:
        """Get categorization rules"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT pattern, category, confidence, use_count
            FROM categorization_rules
            WHERE user_id = ?
            ORDER BY confidence DESC, use_count DESC
        ''', (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'pattern': row[0],
                'category': row[1],
                'confidence': row[2],
                'use_count': row[3]
            }
            for row in rows
        ]
    
    def update_rule_usage(self, user_id: int, pattern: str):
        """Update rule usage count"""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            UPDATE categorization_rules
            SET use_count = use_count + 1, last_used = ?
            WHERE user_id = ? AND pattern = ?
        ''', (now, user_id, pattern))
        
        conn.commit()
        conn.close()
    
    # ===== VIRUS SCAN RESULTS =====
    
    def add_scan_result(self, user_id: int, filepath: str, filename: str,
                       status: str, infected: bool, threats: list, 
                       scanners: list, quarantined: bool = False):
        """Add virus scan result"""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        import json
        threats_json = json.dumps(threats)
        scanners_json = json.dumps(scanners)
        
        cursor.execute('''
            INSERT INTO virus_scan_results
            (user_id, filepath, filename, scan_time, status, infected, 
             threats, scanners, quarantined)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, filepath, filename, now, status, int(infected),
              threats_json, scanners_json, int(quarantined)))
        
        conn.commit()
        conn.close()
    
    def get_scan_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get virus scan history"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT filename, scan_time, status, infected, threats, scanners, quarantined
            FROM virus_scan_results
            WHERE user_id = ?
            ORDER BY scan_time DESC
            LIMIT ?
        ''', (user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        import json
        return [
            {
                'filename': row[0],
                'scan_time': row[1],
                'status': row[2],
                'infected': bool(row[3]),
                'threats': json.loads(row[4]) if row[4] else [],
                'scanners': json.loads(row[5]) if row[5] else [],
                'quarantined': bool(row[6])
            }
            for row in rows
        ]
    
    # ===== ENCRYPTION PASSWORDS =====
    
    def save_encryption_info(self, user_id: int, filename: str, 
                            encrypted_filename: str, password_hint: str = ""):
        """Save encryption info (not the actual password!)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO encryption_passwords
            (user_id, filename, encrypted_filename, password_hint, created_time)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, filename, encrypted_filename, password_hint, now))
        
        conn.commit()
        conn.close()
    
    def get_encrypted_files(self, user_id: int) -> List[Dict]:
        """Get list of encrypted files"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT filename, encrypted_filename, password_hint, created_time
            FROM encryption_passwords
            WHERE user_id = ?
            ORDER BY created_time DESC
        ''', (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'filename': row[0],
                'encrypted_filename': row[1],
                'password_hint': row[2],
                'created_time': row[3]
            }
            for row in rows
        ]
