"""
Smart Categorization Engine
Pattern-based auto categorization dengan learning capability
"""
import os
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SmartCategorizer:
    """Smart file categorization dengan pattern learning"""
    
    # Default categories dan patterns
    DEFAULT_PATTERNS = {
        'video': [
            r'.*\.(mp4|mkv|avi|mov|flv|wmv|webm|m4v|mpeg|mpg|3gp)$',
            r'.*\b(movie|film|video|episode|season|s\d+e\d+)\b.*',
        ],
        'audio': [
            r'.*\.(mp3|wav|flac|aac|ogg|m4a|wma|opus)$',
            r'.*\b(song|music|audio|album|track)\b.*',
        ],
        'image': [
            r'.*\.(jpg|jpeg|png|gif|bmp|svg|webp|ico|tiff)$',
            r'.*\b(photo|picture|image|pic|screenshot)\b.*',
        ],
        'document': [
            r'.*\.(pdf|doc|docx|txt|rtf|odt|xls|xlsx|ppt|pptx|csv)$',
            r'.*\b(document|report|paper|sheet|presentation|resume|cv)\b.*',
        ],
        'archive': [
            r'.*\.(zip|rar|7z|tar|gz|bz2|xz|iso)$',
            r'.*\b(archive|backup|compressed)\b.*',
        ],
        'code': [
            r'.*\.(py|js|java|cpp|c|h|cs|php|rb|go|rs|swift)$',
            r'.*\b(source|code|script|program)\b.*',
        ],
        'ebook': [
            r'.*\.(epub|mobi|azw|azw3)$',
            r'.*\b(ebook|book)\b.*',
        ],
        'software': [
            r'.*\.(exe|msi|dmg|pkg|deb|rpm|apk)$',
            r'.*\b(installer|setup|install)\b.*',
        ],
    }
    
    def __init__(self, db_manager, download_dir: str):
        """
        Initialize smart categorizer
        
        Args:
            db_manager: Database manager instance
            download_dir: Base download directory
        """
        self.db = db_manager
        self.download_dir = download_dir
        self.user_patterns: Dict[int, List[Dict]] = {}  # Cache user patterns
    
    def categorize_file(self, filename: str, user_id: Optional[int] = None) -> Tuple[str, float]:
        """
        Categorize file berdasarkan patterns
        
        Args:
            filename: Filename to categorize
            user_id: User ID untuk user-specific patterns
            
        Returns:
            Tuple (category, confidence)
        """
        filename_lower = filename.lower()
        
        # Check user-specific patterns first (jika ada)
        if user_id:
            user_category, user_confidence = self._check_user_patterns(filename_lower, user_id)
            if user_category:
                return user_category, user_confidence
        
        # Check default patterns
        for category, patterns in self.DEFAULT_PATTERNS.items():
            for pattern in patterns:
                if re.match(pattern, filename_lower, re.IGNORECASE):
                    return category, 0.9  # High confidence untuk default patterns
        
        # Default category
        return 'other', 0.5
    
    def _check_user_patterns(self, filename: str, user_id: int) -> Tuple[Optional[str], float]:
        """Check user-specific learned patterns"""
        # Load user patterns jika belum loaded
        if user_id not in self.user_patterns:
            self.user_patterns[user_id] = self.db.get_categorization_rules(user_id)
        
        patterns = self.user_patterns[user_id]
        
        # Check each pattern
        for rule in patterns:
            pattern = rule['pattern']
            category = rule['category']
            confidence = rule['confidence']
            
            try:
                if re.search(pattern, filename, re.IGNORECASE):
                    # Update usage
                    self.db.update_rule_usage(user_id, pattern)
                    return category, confidence
            except re.error:
                logger.warning(f"Invalid regex pattern: {pattern}")
                continue
        
        return None, 0.0
    
    def learn_from_user_action(self, user_id: int, filename: str, category: str):
        """
        Learn dari user action (user manually categorize file)
        
        Args:
            user_id: User ID
            filename: Filename yang dikategorisasi
            category: Category yang dipilih user
        """
        # Extract patterns dari filename
        patterns = self._extract_patterns(filename)
        
        # Add patterns to database
        for pattern in patterns:
            try:
                self.db.add_categorization_rule(
                    user_id=user_id,
                    pattern=pattern,
                    category=category,
                    confidence=0.7  # Initial confidence untuk learned patterns
                )
                logger.info(f"Learned pattern: {pattern} → {category}")
            except Exception as e:
                logger.error(f"Error saving pattern: {e}")
        
        # Clear cache untuk user
        if user_id in self.user_patterns:
            del self.user_patterns[user_id]
    
    def _extract_patterns(self, filename: str) -> List[str]:
        """Extract useful patterns dari filename"""
        patterns = []
        
        # Extension pattern
        if '.' in filename:
            ext = filename.rsplit('.', 1)[1].lower()
            patterns.append(f'.*\\.{re.escape(ext)}$')
        
        # Word patterns (keywords)
        # Remove extension
        name_without_ext = filename.rsplit('.', 1)[0] if '.' in filename else filename
        
        # Extract words (3+ characters)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', name_without_ext.lower())
        
        # Add significant words as patterns
        for word in words:
            if len(word) >= 4:  # Only significant words
                patterns.append(f'.*\\b{re.escape(word)}\\b.*')
        
        return patterns[:3]  # Max 3 patterns
    
    def auto_categorize_downloads(self, user_id: int) -> Dict[str, int]:
        """
        Auto categorize semua files di download folder
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary dengan count per category
        """
        if not os.path.exists(self.download_dir):
            return {}
        
        categorized = {}
        
        # List all files
        files = [f for f in os.listdir(self.download_dir) if os.path.isfile(os.path.join(self.download_dir, f))]
        
        for filename in files:
            category, confidence = self.categorize_file(filename, user_id)
            
            # Only move if confidence > 0.6
            if confidence > 0.6:
                # Create category folder
                category_dir = os.path.join(self.download_dir, category.capitalize())
                os.makedirs(category_dir, exist_ok=True)
                
                # Move file
                old_path = os.path.join(self.download_dir, filename)
                new_path = os.path.join(category_dir, filename)
                
                try:
                    # Handle duplicate names
                    if os.path.exists(new_path):
                        base, ext = os.path.splitext(filename)
                        counter = 1
                        while os.path.exists(new_path):
                            new_filename = f"{base} ({counter}){ext}"
                            new_path = os.path.join(category_dir, new_filename)
                            counter += 1
                    
                    os.rename(old_path, new_path)
                    
                    categorized[category] = categorized.get(category, 0) + 1
                    logger.info(f"Categorized: {filename} → {category} (confidence: {confidence:.2f})")
                
                except Exception as e:
                    logger.error(f"Error moving file {filename}: {e}")
        
        return categorized
    
    def get_suggested_category(self, filename: str, user_id: Optional[int] = None) -> Dict:
        """
        Get suggested category dengan explanation
        
        Args:
            filename: Filename
            user_id: User ID
            
        Returns:
            Suggestion dictionary
        """
        category, confidence = self.categorize_file(filename, user_id)
        
        # Get matching pattern
        matching_pattern = self._get_matching_pattern(filename, category, user_id)
        
        confidence_level = "High" if confidence >= 0.8 else "Medium" if confidence >= 0.6 else "Low"
        
        return {
            'filename': filename,
            'category': category,
            'confidence': confidence,
            'confidence_level': confidence_level,
            'matching_pattern': matching_pattern,
            'is_learned': self._is_learned_pattern(filename, user_id)
        }
    
    def _get_matching_pattern(self, filename: str, category: str, user_id: Optional[int]) -> str:
        """Get pattern yang match dengan filename"""
        filename_lower = filename.lower()
        
        # Check user patterns first
        if user_id and user_id in self.user_patterns:
            for rule in self.user_patterns[user_id]:
                if rule['category'] == category:
                    try:
                        if re.search(rule['pattern'], filename_lower, re.IGNORECASE):
                            return rule['pattern']
                    except:
                        pass
        
        # Check default patterns
        if category in self.DEFAULT_PATTERNS:
            for pattern in self.DEFAULT_PATTERNS[category]:
                if re.match(pattern, filename_lower, re.IGNORECASE):
                    return pattern
        
        return "unknown"
    
    def _is_learned_pattern(self, filename: str, user_id: Optional[int]) -> bool:
        """Check if categorization uses learned pattern"""
        if not user_id or user_id not in self.user_patterns:
            return False
        
        filename_lower = filename.lower()
        
        for rule in self.user_patterns[user_id]:
            try:
                if re.search(rule['pattern'], filename_lower, re.IGNORECASE):
                    return True
            except:
                pass
        
        return False
    
    def get_category_stats(self, user_id: int) -> Dict:
        """
        Get statistics tentang categorization
        
        Args:
            user_id: User ID
            
        Returns:
            Statistics dictionary
        """
        # Load user patterns
        if user_id not in self.user_patterns:
            self.user_patterns[user_id] = self.db.get_categorization_rules(user_id)
        
        patterns = self.user_patterns[user_id]
        
        # Count patterns per category
        category_counts = {}
        for rule in patterns:
            category = rule['category']
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Find most used patterns
        top_patterns = sorted(patterns, key=lambda x: x['use_count'], reverse=True)[:5]
        
        return {
            'total_learned_patterns': len(patterns),
            'categories': category_counts,
            'top_patterns': [
                {
                    'pattern': p['pattern'],
                    'category': p['category'],
                    'use_count': p['use_count']
                }
                for p in top_patterns
            ]
        }
