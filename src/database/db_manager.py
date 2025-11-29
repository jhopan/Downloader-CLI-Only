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
