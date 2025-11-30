"""
Smart Features Handler
Handler untuk duplicate detection, queue management, preview, statistics, cloud, dan smart categorization
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Conversation states
AWAITING_CLOUD_AUTH = 1
AWAITING_MANUAL_CATEGORY = 2


async def queue_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show download queue status"""
    user_id = update.effective_user.id
    
    try:
        # Get queue manager dari context
        queue_manager = context.bot_data.get('queue_manager')
        
        if not queue_manager:
            await update.message.reply_text("❌ Queue manager tidak tersedia")
            return
        
        # Get queue status
        status = await queue_manager.get_queue_status(user_id)
        
        text = "📋 **Download Queue Status**\n\n"
        text += f"• Total Items: {status['total']}\n"
        text += f"• Pending: {status['pending']}\n"
        text += f"• Downloading: {status['downloading']} / {status['max_concurrent']}\n"
        text += f"• Paused: {status['paused']}\n"
        text += f"• Completed: {status['completed']}\n"
        text += f"• Failed: {status['failed']}\n\n"
        
        # Show queue items
        if status['items']:
            text += "**Queue Items:**\n"
            for item in status['items'][:10]:  # Show max 10
                status_emoji = {
                    'pending': '⏳',
                    'downloading': '⬇️',
                    'paused': '⏸️',
                    'completed': '✅',
                    'failed': '❌'
                }.get(item['status'], '❓')
                
                filename = item['filename']
                if len(filename) > 30:
                    filename = filename[:27] + "..."
                
                priority_emoji = ['🔴', '🟡', '🟢', '🔵'][min(item['priority'], 3)]
                
                text += f"{status_emoji} {priority_emoji} {filename}\n"
                
                # Show progress jika downloading
                if item['status'] == 'downloading' and item['progress'] > 0:
                    text += f"   Progress: {item['progress']:.1f}%\n"
        
        # Create buttons untuk queue management
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="queue_refresh")],
            [InlineKeyboardButton("📊 Queue Stats", callback_data="queue_stats")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    except Exception as e:
        logger.error(f"Error in queue_command: {e}")
        await update.message.reply_text(f"❌ Error: {e}")


async def preview_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show file preview dengan metadata"""
    user_id = update.effective_user.id
    
    try:
        db_manager = context.bot_data.get('db_manager')
        file_preview = context.bot_data.get('file_preview')
        
        if not db_manager or not file_preview:
            await update.message.reply_text("❌ Preview service tidak tersedia")
            return
        
        # Get recent downloads
        history = db_manager.get_download_history(user_id, limit=10)
        
        if not history:
            await update.message.reply_text("📁 Belum ada file untuk preview")
            return
        
        # Create buttons untuk select file
        keyboard = []
        for item in history[:5]:  # Show max 5
            filename = item['filename']
            if len(filename) > 40:
                filename = filename[:37] + "..."
            
            keyboard.append([
                InlineKeyboardButton(
                    f"👁️ {filename}", 
                    callback_data=f"preview_{item['download_id']}"
                )
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📁 **Select File to Preview:**",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    except Exception as e:
        logger.error(f"Error in preview_command: {e}")
        await update.message.reply_text(f"❌ Error: {e}")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show download statistics dashboard"""
    user_id = update.effective_user.id
    
    try:
        stats_manager = context.bot_data.get('stats_manager')
        
        if not stats_manager:
            await update.message.reply_text("❌ Statistics service tidak tersedia")
            return
        
        # Get dashboard data
        dashboard = stats_manager.get_dashboard_data(user_id, days=30)
        
        # Format text
        text = stats_manager.format_dashboard_text(dashboard)
        
        # Create buttons untuk more options
        keyboard = [
            [
                InlineKeyboardButton("📊 7 Days", callback_data="stats_7"),
                InlineKeyboardButton("📊 30 Days", callback_data="stats_30"),
            ],
            [
                InlineKeyboardButton("📈 Trending Files", callback_data="stats_trending"),
                InlineKeyboardButton("⏰ Time Distribution", callback_data="stats_time"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    except Exception as e:
        logger.error(f"Error in stats_command: {e}")
        await update.message.reply_text(f"❌ Error: {e}")


async def cloud_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manage cloud storage downloads"""
    keyboard = [
        [
            InlineKeyboardButton("☁️ Google Drive", callback_data="cloud_gdrive"),
            InlineKeyboardButton("☁️ Dropbox", callback_data="cloud_dropbox"),
        ],
        [
            InlineKeyboardButton("☁️ OneDrive", callback_data="cloud_onedrive"),
        ],
        [
            InlineKeyboardButton("ℹ️ Help", callback_data="cloud_help"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "☁️ **Cloud Storage Download**\n\n"
        "Download files dari cloud storage services.\n"
        "Pilih service atau kirim link langsung:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def smart_category_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Smart auto categorization"""
    user_id = update.effective_user.id
    
    try:
        smart_categorizer = context.bot_data.get('smart_categorizer')
        
        if not smart_categorizer:
            await update.message.reply_text("❌ Smart categorization tidak tersedia")
            return
        
        # Get category stats
        stats = smart_categorizer.get_category_stats(user_id)
        
        text = "🤖 **Smart Auto-Categorization**\n\n"
        text += f"📚 Learned Patterns: {stats['total_learned_patterns']}\n\n"
        
        if stats['categories']:
            text += "**Categories:**\n"
            for category, count in stats['categories'].items():
                text += f"• {category.capitalize()}: {count} patterns\n"
            text += "\n"
        
        if stats['top_patterns']:
            text += "**🏆 Most Used Patterns:**\n"
            for i, pattern in enumerate(stats['top_patterns'], 1):
                text += f"{i}. {pattern['category']} - {pattern['use_count']} uses\n"
        
        # Create buttons
        keyboard = [
            [
                InlineKeyboardButton("🚀 Auto-Categorize Now", callback_data="smart_auto"),
            ],
            [
                InlineKeyboardButton("📝 Teach Pattern", callback_data="smart_teach"),
                InlineKeyboardButton("📊 View Stats", callback_data="smart_stats"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    except Exception as e:
        logger.error(f"Error in smart_category_command: {e}")
        await update.message.reply_text(f"❌ Error: {e}")


async def duplicate_check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check untuk duplicate files"""
    user_id = update.effective_user.id
    
    try:
        db_manager = context.bot_data.get('db_manager')
        
        if not db_manager:
            await update.message.reply_text("❌ Database tidak tersedia")
            return
        
        # Get file hashes
        hashes = db_manager.get_file_hashes(user_id)
        
        if not hashes:
            await update.message.reply_text("📁 Belum ada file untuk check duplicates")
            return
        
        # Find duplicates
        hash_map = {}
        duplicates = []
        
        for file_info in hashes:
            hash_val = file_info['md5_hash']
            if hash_val in hash_map:
                duplicates.append({
                    'original': hash_map[hash_val],
                    'duplicate': file_info
                })
            else:
                hash_map[hash_val] = file_info
        
        text = "🔍 **Duplicate Detection Results**\n\n"
        text += f"📊 Total Files: {len(hashes)}\n"
        text += f"🔄 Duplicates Found: {len(duplicates)}\n\n"
        
        if duplicates:
            text += "**Duplicate Files:**\n"
            for i, dup in enumerate(duplicates[:10], 1):  # Show max 10
                orig = dup['original']
                dupl = dup['duplicate']
                
                text += f"\n{i}. **{orig['filename']}**\n"
                text += f"   Duplicate: {dupl['filename']}\n"
                text += f"   Size: {orig['file_size']} bytes\n"
        else:
            text += "✨ No duplicates found! All files are unique."
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    except Exception as e:
        logger.error(f"Error in duplicate_check_command: {e}")
        await update.message.reply_text(f"❌ Error: {e}")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks untuk smart features"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    try:
        # Queue callbacks
        if data == "queue_refresh":
            await queue_command(update, context)
        
        elif data == "queue_stats":
            queue_manager = context.bot_data.get('queue_manager')
            status = await queue_manager.get_queue_status(user_id)
            
            text = "📊 **Detailed Queue Statistics**\n\n"
            text += f"• Max Concurrent: {status['max_concurrent']}\n"
            text += f"• Active Slots: {status['active_slots']}\n"
            text += f"• Available Slots: {status['max_concurrent'] - status['active_slots']}\n\n"
            text += f"• Total Items: {status['total']}\n"
            text += f"• Pending: {status['pending']}\n"
            text += f"• Downloading: {status['downloading']}\n"
            text += f"• Paused: {status['paused']}\n"
            text += f"• Completed: {status['completed']}\n"
            text += f"• Failed: {status['failed']}\n"
            
            await query.edit_message_text(text, parse_mode='Markdown')
        
        # Preview callback
        elif data.startswith("preview_"):
            download_id = data.split("_")[1]
            db_manager = context.bot_data.get('db_manager')
            file_preview = context.bot_data.get('file_preview')
            
            # Get file info
            history = db_manager.get_download_history(user_id, limit=100)
            file_info = next((h for h in history if h['download_id'] == download_id), None)
            
            if not file_info:
                await query.edit_message_text("❌ File tidak ditemukan")
                return
            
            filepath = file_info['filepath']
            
            # Extract metadata
            metadata = file_preview.extract_metadata(filepath)
            
            text = f"👁️ **File Preview**\n\n"
            text += f"📄 **Name:** {metadata.get('filename', 'Unknown')}\n"
            text += f"📦 **Size:** {file_preview.format_size(metadata.get('size', 0))}\n"
            text += f"📋 **Type:** {metadata.get('file_type', 'Unknown')}\n"
            
            if metadata.get('width') and metadata.get('height'):
                text += f"📐 **Dimensions:** {metadata['width']}x{metadata['height']}\n"
            
            if metadata.get('duration'):
                text += f"⏱️ **Duration:** {file_preview.format_duration(metadata['duration'])}\n"
            
            if metadata.get('format'):
                text += f"🎨 **Format:** {metadata['format']}\n"
            
            await query.edit_message_text(text, parse_mode='Markdown')
        
        # Stats callbacks
        elif data.startswith("stats_"):
            stats_manager = context.bot_data.get('stats_manager')
            
            if data == "stats_7":
                dashboard = stats_manager.get_dashboard_data(user_id, days=7)
                text = stats_manager.format_dashboard_text(dashboard)
                await query.edit_message_text(text, parse_mode='Markdown')
            
            elif data == "stats_30":
                dashboard = stats_manager.get_dashboard_data(user_id, days=30)
                text = stats_manager.format_dashboard_text(dashboard)
                await query.edit_message_text(text, parse_mode='Markdown')
            
            elif data == "stats_trending":
                trending = stats_manager.get_trending_files(user_id, limit=10)
                
                text = "📈 **Trending File Types**\n\n"
                for i, trend in enumerate(trending, 1):
                    text += f"{i}. **.{trend['extension']}** - {trend['count']} files\n"
                    text += f"   Total: {trend['total_size']}, Avg: {trend['avg_size']}\n"
                
                await query.edit_message_text(text, parse_mode='Markdown')
            
            elif data == "stats_time":
                time_dist = stats_manager.get_time_distribution(user_id, days=30)
                
                text = "⏰ **Download Time Distribution**\n\n"
                text += f"🔥 **Peak Hour:** {time_dist['peak_time_formatted']}\n"
                text += f"📊 **Peak Downloads:** {time_dist['peak_count']}\n\n"
                
                # Show hourly bar chart (simplified)
                text += "**Hourly Activity:**\n"
                max_count = max(time_dist['hourly_distribution'].values())
                for hour in range(0, 24, 3):  # Show every 3 hours
                    count = time_dist['hourly_distribution'][hour]
                    bar_length = int((count / max_count * 10)) if max_count > 0 else 0
                    bar = "█" * bar_length
                    text += f"{hour:02d}:00 {bar} {count}\n"
                
                await query.edit_message_text(text, parse_mode='Markdown')
        
        # Smart categorization callbacks
        elif data == "smart_auto":
            smart_categorizer = context.bot_data.get('smart_categorizer')
            
            await query.edit_message_text("🚀 Auto-categorizing files...")
            
            result = smart_categorizer.auto_categorize_downloads(user_id)
            
            text = "✅ **Auto-Categorization Complete!**\n\n"
            if result:
                text += "**Files Moved:**\n"
                for category, count in result.items():
                    text += f"• {category.capitalize()}: {count} files\n"
            else:
                text += "No files to categorize or all files already categorized."
            
            await query.edit_message_text(text, parse_mode='Markdown')
        
        # Cloud callbacks
        elif data.startswith("cloud_"):
            service = data.split("_")[1]
            
            if service == "help":
                text = "☁️ **Cloud Storage Download Help**\n\n"
                text += "**Supported Services:**\n"
                text += "• Google Drive - drive.google.com\n"
                text += "• Dropbox - dropbox.com\n"
                text += "• OneDrive - onedrive.live.com\n\n"
                text += "**How to use:**\n"
                text += "1. Copy share link dari cloud storage\n"
                text += "2. Kirim link ke bot\n"
                text += "3. Bot akan detect service dan download\n\n"
                text += "**Note:** Public links work best. Private files may require authentication."
                
                await query.edit_message_text(text, parse_mode='Markdown')
            else:
                text = f"☁️ **{service.upper()} Download**\n\n"
                text += f"Kirim {service} share link untuk download.\n\n"
                text += "**Example:**\n"
                
                if service == "gdrive":
                    text += "`https://drive.google.com/file/d/FILE_ID/view`"
                elif service == "dropbox":
                    text += "`https://www.dropbox.com/s/XXXXX/file.zip?dl=0`"
                elif service == "onedrive":
                    text += "`https://onedrive.live.com/...`"
                
                await query.edit_message_text(text, parse_mode='Markdown')
    
    except Exception as e:
        logger.error(f"Error in button_callback: {e}")
        await query.edit_message_text(f"❌ Error: {e}")


# Create handler
def get_smart_features_handlers():
    """Get all handlers untuk smart features"""
    return [
        CommandHandler('queue', queue_command),
        CommandHandler('preview', preview_command),
        CommandHandler('stats', stats_command),
        CommandHandler('cloud', cloud_command),
        CommandHandler('smartcat', smart_category_command),
        CommandHandler('duplicates', duplicate_check_command),
        CallbackQueryHandler(button_callback, pattern="^(queue_|preview_|stats_|smart_|cloud_)")
    ]
