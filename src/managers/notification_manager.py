"""
Notification Manager
Mengelola pengaturan dan pengiriman notifikasi kustom untuk berbagai event
"""

import json
import os
import asyncio
from typing import Dict, Optional
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

class NotificationManager:
    def __init__(self, bot: Bot, settings_file: str = "notification_settings.json"):
        self.bot = bot
        self.settings_file = settings_file
        self.settings = self._load_settings()
        
    def _load_settings(self) -> Dict:
        """Load notification settings from file"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading notification settings: {e}")
        
        # Default settings
        return {
            "download_complete": {
                "enabled": True,
                "message": "✅ Download selesai!\n📁 File: {filename}\n📊 Size: {size}\n⏱️ Waktu: {duration}",
                "sound": True
            },
            "download_start": {
                "enabled": True,
                "message": "⬇️ Download dimulai...\n🔗 URL: {url}\n📁 File: {filename}",
                "sound": False
            },
            "download_error": {
                "enabled": True,
                "message": "❌ Download gagal!\n📁 File: {filename}\n⚠️ Error: {error}",
                "sound": True
            },
            "download_retry": {
                "enabled": True,
                "message": "🔄 Retry download (attempt {attempt}/{max_attempts})\n📁 File: {filename}\n⏳ Delay: {delay}s",
                "sound": False
            },
            "schedule_created": {
                "enabled": True,
                "message": "⏰ Jadwal dibuat!\n📅 Waktu: {schedule_time}\n🔗 URL: {url}",
                "sound": False
            },
            "schedule_triggered": {
                "enabled": True,
                "message": "⏰ Jadwal dimulai!\n📅 Waktu: {schedule_time}\n📁 File: {filename}",
                "sound": True
            },
            "extraction_complete": {
                "enabled": True,
                "message": "📦 Ekstraksi selesai!\n📁 File: {filename}\n📂 Folder: {extract_path}",
                "sound": False
            },
            "extraction_error": {
                "enabled": True,
                "message": "❌ Ekstraksi gagal!\n📁 File: {filename}\n⚠️ Error: {error}",
                "sound": True
            }
        }
    
    def _save_settings(self):
        """Save notification settings to file"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, indent=2, fp=f, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving notification settings: {e}")
    
    async def send_notification(self, chat_id: int, event_type: str, **kwargs):
        """Send notification based on event type and settings"""
        if event_type not in self.settings:
            return
        
        event_settings = self.settings[event_type]
        
        if not event_settings.get("enabled", True):
            return
        
        try:
            # Format message dengan data yang diberikan
            message = event_settings["message"].format(**kwargs)
            
            # Tambahkan disable_notification jika sound disabled
            disable_notification = not event_settings.get("sound", False)
            
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                disable_notification=disable_notification,
                parse_mode='HTML'
            )
        except KeyError as e:
            # Jika ada parameter yang hilang, kirim pesan default
            print(f"Missing parameter in notification: {e}")
            await self.bot.send_message(
                chat_id=chat_id,
                text=f"ℹ️ Event: {event_type}",
                disable_notification=True
            )
        except Exception as e:
            print(f"Error sending notification: {e}")
    
    def get_event_setting(self, event_type: str) -> Optional[Dict]:
        """Get settings for specific event type"""
        return self.settings.get(event_type)
    
    def update_event_setting(self, event_type: str, enabled: Optional[bool] = None, 
                           message: Optional[str] = None, sound: Optional[bool] = None):
        """Update settings for specific event type"""
        if event_type not in self.settings:
            return False
        
        if enabled is not None:
            self.settings[event_type]["enabled"] = enabled
        
        if message is not None:
            self.settings[event_type]["message"] = message
        
        if sound is not None:
            self.settings[event_type]["sound"] = sound
        
        self._save_settings()
        return True
    
    def toggle_event(self, event_type: str) -> bool:
        """Toggle event enabled/disabled"""
        if event_type not in self.settings:
            return False
        
        self.settings[event_type]["enabled"] = not self.settings[event_type]["enabled"]
        self._save_settings()
        return self.settings[event_type]["enabled"]
    
    def toggle_sound(self, event_type: str) -> bool:
        """Toggle sound for event"""
        if event_type not in self.settings:
            return False
        
        self.settings[event_type]["sound"] = not self.settings[event_type]["sound"]
        self._save_settings()
        return self.settings[event_type]["sound"]
    
    def reset_to_default(self):
        """Reset all settings to default"""
        self.settings = self._load_settings()
        if os.path.exists(self.settings_file):
            os.remove(self.settings_file)
        self._save_settings()
    
    def get_event_list(self) -> Dict[str, Dict]:
        """Get all event types and their settings"""
        return self.settings.copy()
    
    def get_event_display_name(self, event_type: str) -> str:
        """Get display name for event type"""
        display_names = {
            "download_complete": "Download Selesai",
            "download_start": "Download Dimulai",
            "download_error": "Download Error",
            "download_retry": "Download Retry",
            "schedule_created": "Jadwal Dibuat",
            "schedule_triggered": "Jadwal Dimulai",
            "extraction_complete": "Ekstraksi Selesai",
            "extraction_error": "Ekstraksi Error"
        }
        return display_names.get(event_type, event_type)
