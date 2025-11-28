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
