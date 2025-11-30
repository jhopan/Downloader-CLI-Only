"""
Statistics Dashboard
Generate visual statistics untuk download activity
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class StatisticsManager:
    """Manage download statistics dan dashboard"""
    
    def __init__(self, db_manager):
        """
        Initialize statistics manager
        
        Args:
            db_manager: Database manager instance
        """
        self.db = db_manager
    
    def get_dashboard_data(self, user_id: int, days: int = 30) -> Dict:
        """
        Get comprehensive dashboard data
        
        Args:
            user_id: User ID
            days: Number of days untuk statistics
            
        Returns:
            Dashboard data dictionary
        """
        # Get statistics dari database
        stats = self.db.get_statistics(user_id, days)
        
        # Calculate totals
        total_downloads = sum(s['total_downloads'] for s in stats)
        total_bytes = sum(s['total_bytes'] for s in stats)
        successful_downloads = sum(s['successful_downloads'] for s in stats)
        failed_downloads = sum(s['failed_downloads'] for s in stats)
        
        # Calculate success rate
        success_rate = (successful_downloads / total_downloads * 100) if total_downloads > 0 else 0
        
        # Calculate average speed
        avg_speed = sum(s['avg_speed_kbps'] * s['total_downloads'] for s in stats) / total_downloads if total_downloads > 0 else 0
        
        # Get download history untuk top files
        history = self.db.get_download_history(user_id, limit=100)
        
        # Find largest downloads
        largest_files = sorted(
            [h for h in history if h.get('file_size', 0) > 0],
            key=lambda x: x.get('file_size', 0),
            reverse=True
        )[:10]
        
        # Calculate daily averages
        daily_avg_downloads = total_downloads / days if days > 0 else 0
        daily_avg_bytes = total_bytes / days if days > 0 else 0
        
        return {
            'period_days': days,
            'total_downloads': total_downloads,
            'total_bytes': total_bytes,
            'total_size_formatted': self._format_bytes(total_bytes),
            'successful_downloads': successful_downloads,
            'failed_downloads': failed_downloads,
            'success_rate': round(success_rate, 1),
            'avg_speed_kbps': round(avg_speed, 1),
            'avg_speed_formatted': self._format_speed(avg_speed),
            'daily_avg_downloads': round(daily_avg_downloads, 1),
            'daily_avg_bytes': round(daily_avg_bytes, 1),
            'daily_avg_formatted': self._format_bytes(daily_avg_bytes),
            'largest_files': [
                {
                    'filename': f['filename'],
                    'size': f['file_size'],
                    'size_formatted': self._format_bytes(f['file_size']),
                    'date': f.get('start_time', '')
                }
                for f in largest_files
            ],
            'daily_stats': stats
        }
    
    def format_dashboard_text(self, dashboard_data: Dict) -> str:
        """
        Format dashboard data ke text untuk Telegram
        
        Args:
            dashboard_data: Dashboard data dictionary
            
        Returns:
            Formatted text
        """
        text = "📊 **Download Statistics Dashboard**\n\n"
        text += f"📅 **Period:** Last {dashboard_data['period_days']} days\n\n"
        
        text += "**📥 Overall Statistics**\n"
        text += f"• Total Downloads: {dashboard_data['total_downloads']}\n"
        text += f"• Total Size: {dashboard_data['total_size_formatted']}\n"
        text += f"• Success Rate: {dashboard_data['success_rate']}%\n"
        text += f"• Average Speed: {dashboard_data['avg_speed_formatted']}\n\n"
        
        text += "**✅ Success vs ❌ Failed**\n"
        text += f"• Successful: {dashboard_data['successful_downloads']}\n"
        text += f"• Failed: {dashboard_data['failed_downloads']}\n\n"
        
        text += "**📊 Daily Averages**\n"
        text += f"• Downloads/day: {dashboard_data['daily_avg_downloads']}\n"
        text += f"• Data/day: {dashboard_data['daily_avg_formatted']}\n\n"
        
        if dashboard_data['largest_files']:
            text += "**🏆 Top 5 Largest Files**\n"
            for i, file in enumerate(dashboard_data['largest_files'][:5], 1):
                filename = file['filename']
                if len(filename) > 30:
                    filename = filename[:27] + "..."
                text += f"{i}. {filename} - {file['size_formatted']}\n"
        
        return text
    
    def generate_chart_data(self, user_id: int, days: int = 7) -> Dict:
        """
        Generate data untuk chart visualization
        
        Args:
            user_id: User ID
            days: Number of days
            
        Returns:
            Chart data dictionary
        """
        stats = self.db.get_statistics(user_id, days)
        
        # Reverse untuk chronological order
        stats.reverse()
        
        # Extract data untuk charts
        dates = [s['date'] for s in stats]
        downloads = [s['total_downloads'] for s in stats]
        bytes_data = [s['total_bytes'] for s in stats]
        success_rates = [
            (s['successful_downloads'] / s['total_downloads'] * 100) 
            if s['total_downloads'] > 0 else 0
            for s in stats
        ]
        
        return {
            'labels': dates,
            'downloads': downloads,
            'bytes': bytes_data,
            'success_rates': success_rates,
            'formatted_bytes': [self._format_bytes(b) for b in bytes_data]
        }
    
    def get_trending_files(self, user_id: int, limit: int = 10) -> List[Dict]:
        """
        Get trending file types
        
        Args:
            user_id: User ID
            limit: Max results
            
        Returns:
            List of trending file types
        """
        history = self.db.get_download_history(user_id, limit=200)
        
        # Count by extension
        extension_counts = {}
        extension_bytes = {}
        
        for item in history:
            filename = item.get('filename', '')
            file_size = item.get('file_size', 0)
            
            # Get extension
            if '.' in filename:
                ext = filename.rsplit('.', 1)[1].lower()
            else:
                ext = 'unknown'
            
            extension_counts[ext] = extension_counts.get(ext, 0) + 1
            extension_bytes[ext] = extension_bytes.get(ext, 0) + file_size
        
        # Sort by count
        trending = [
            {
                'extension': ext,
                'count': count,
                'total_bytes': extension_bytes[ext],
                'total_size': self._format_bytes(extension_bytes[ext]),
                'avg_size': self._format_bytes(extension_bytes[ext] // count)
            }
            for ext, count in sorted(extension_counts.items(), key=lambda x: x[1], reverse=True)
        ]
        
        return trending[:limit]
    
    def _format_bytes(self, size_bytes: int) -> str:
        """Format bytes ke human readable"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    def _format_speed(self, kbps: float) -> str:
        """Format speed ke human readable"""
        if kbps < 1024:
            return f"{kbps:.1f} KB/s"
        else:
            mbps = kbps / 1024
            return f"{mbps:.2f} MB/s"
    
    def get_time_distribution(self, user_id: int, days: int = 30) -> Dict:
        """
        Get download time distribution (hourly)
        
        Args:
            user_id: User ID
            days: Number of days
            
        Returns:
            Time distribution data
        """
        history = self.db.get_download_history(user_id, limit=500)
        
        # Count by hour
        hour_counts = {i: 0 for i in range(24)}
        
        for item in history:
            start_time = item.get('start_time')
            if start_time:
                try:
                    dt = datetime.fromisoformat(start_time)
                    hour = dt.hour
                    hour_counts[hour] += 1
                except:
                    pass
        
        # Find peak hours
        peak_hour = max(hour_counts.items(), key=lambda x: x[1])
        
        return {
            'hourly_distribution': hour_counts,
            'peak_hour': peak_hour[0],
            'peak_count': peak_hour[1],
            'peak_time_formatted': f"{peak_hour[0]:02d}:00 - {peak_hour[0]+1:02d}:00"
        }
