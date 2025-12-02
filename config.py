import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]

# Download Configuration
DEFAULT_DOWNLOAD_DIR = os.getenv('DEFAULT_DOWNLOAD_DIR', './downloads')
MAX_CONCURRENT_DOWNLOADS = int(os.getenv('MAX_CONCURRENT_DOWNLOADS', '5'))
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '8192'))  # 8KB

# Auto-Retry Configuration
MAX_DOWNLOAD_RETRIES = int(os.getenv('MAX_DOWNLOAD_RETRIES', '3'))
RETRY_DELAY_BASE = int(os.getenv('RETRY_DELAY_BASE', '5'))  # Base delay in seconds (exponential backoff)

# Database Configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', './data/bot.db')

# Smart Features Configuration
AUTO_CATEGORIZE_DOWNLOADS = os.getenv('AUTO_CATEGORIZE', 'false').lower() == 'true'
FILE_CATEGORIES = [cat.strip() for cat in os.getenv('FILE_CATEGORIES', 'Video,Audio,Image,Document,Archive,Code,Ebook,Software').split(',')]

# Validation
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN tidak ditemukan! Silakan atur di file .env")

if not ADMIN_IDS:
    raise ValueError("ADMIN_IDS tidak ditemukan! Silakan atur di file .env")

# Ensure directories exist
os.makedirs(DEFAULT_DOWNLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

print(f"✅ Konfigurasi dimuat:")
print(f"   - Admin IDs: {ADMIN_IDS}")
print(f"   - Default Download Dir: {DEFAULT_DOWNLOAD_DIR}")
print(f"   - Max Concurrent: {MAX_CONCURRENT_DOWNLOADS}")
print(f"   - Database: {DATABASE_PATH}")
