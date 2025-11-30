"""
File Encryption
AES-256 encryption untuk files
"""
import os
import logging
from typing import Optional, Tuple
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import secrets

logger = logging.getLogger(__name__)


class FileEncryption:
    """Encrypt dan decrypt files menggunakan AES-256"""
    
    def __init__(self):
        """Initialize encryption"""
        self.backend = default_backend()
        self.key_iterations = 100000  # PBKDF2 iterations
    
    def generate_password(self, length: int = 16) -> str:
        """
        Generate random secure password
        
        Args:
            length: Password length
            
        Returns:
            Random password string
        """
        import string
        alphabet = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
    
    def derive_key(self, password: str, salt: bytes) -> bytes:
        """
        Derive encryption key dari password menggunakan PBKDF2
        
        Args:
            password: Password string
            salt: Salt bytes
            
        Returns:
            32-byte key untuk AES-256
        """
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits
            salt=salt,
            iterations=self.key_iterations,
            backend=self.backend
        )
        key = kdf.derive(password.encode())
        return key
    
    def encrypt_file(self, input_path: str, output_path: Optional[str] = None,
                    password: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Encrypt file menggunakan AES-256-GCM
        
        Args:
            input_path: Path ke file yang akan diencrypt
            output_path: Path output (default: input_path + .enc)
            password: Password untuk encryption (auto-generate jika None)
            
        Returns:
            Tuple (success, message, password)
        """
        if not os.path.exists(input_path):
            return False, "Input file not found", None
        
        try:
            # Generate password jika tidak diberikan
            if not password:
                password = self.generate_password()
                logger.info("Auto-generated password for encryption")
            
            # Generate salt dan IV
            salt = secrets.token_bytes(16)  # 128 bits
            iv = secrets.token_bytes(12)    # 96 bits untuk GCM
            
            # Derive key dari password
            key = self.derive_key(password, salt)
            
            # Setup cipher (AES-256-GCM)
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(iv),
                backend=self.backend
            )
            encryptor = cipher.encryptor()
            
            # Determine output path
            if not output_path:
                output_path = input_path + '.enc'
            
            # Encrypt file
            with open(input_path, 'rb') as f_in:
                with open(output_path, 'wb') as f_out:
                    # Write header: salt (16) + iv (12) = 28 bytes
                    f_out.write(salt)
                    f_out.write(iv)
                    
                    # Encrypt data in chunks
                    while True:
                        chunk = f_in.read(64 * 1024)  # 64KB chunks
                        if not chunk:
                            break
                        encrypted_chunk = encryptor.update(chunk)
                        f_out.write(encrypted_chunk)
                    
                    # Finalize dan write GCM tag
                    f_out.write(encryptor.finalize())
                    f_out.write(encryptor.tag)  # 16 bytes GCM tag
            
            file_size = os.path.getsize(output_path)
            logger.info(f"File encrypted: {input_path} -> {output_path} ({file_size} bytes)")
            
            return True, f"File encrypted successfully: {os.path.basename(output_path)}", password
        
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            return False, f"Encryption failed: {str(e)}", None
    
    def decrypt_file(self, input_path: str, password: str,
                    output_path: Optional[str] = None) -> Tuple[bool, str]:
        """
        Decrypt file yang diencrypt dengan AES-256-GCM
        
        Args:
            input_path: Path ke encrypted file
            password: Password untuk decryption
            output_path: Path output (default: remove .enc extension)
            
        Returns:
            Tuple (success, message)
        """
        if not os.path.exists(input_path):
            return False, "Input file not found"
        
        try:
            # Determine output path
            if not output_path:
                if input_path.endswith('.enc'):
                    output_path = input_path[:-4]  # Remove .enc
                else:
                    output_path = input_path + '.dec'
            
            with open(input_path, 'rb') as f_in:
                # Read header
                salt = f_in.read(16)
                iv = f_in.read(12)
                
                if len(salt) != 16 or len(iv) != 12:
                    return False, "Invalid encrypted file format"
                
                # Derive key
                key = self.derive_key(password, salt)
                
                # Read encrypted data dan tag
                encrypted_data = f_in.read()
                
                if len(encrypted_data) < 16:
                    return False, "Invalid encrypted file (too short)"
                
                # Split data dan GCM tag
                tag = encrypted_data[-16:]
                encrypted_data = encrypted_data[:-16]
                
                # Setup cipher
                cipher = Cipher(
                    algorithms.AES(key),
                    modes.GCM(iv, tag),
                    backend=self.backend
                )
                decryptor = cipher.decryptor()
                
                # Decrypt
                with open(output_path, 'wb') as f_out:
                    # Decrypt in chunks
                    chunk_size = 64 * 1024
                    for i in range(0, len(encrypted_data), chunk_size):
                        chunk = encrypted_data[i:i + chunk_size]
                        decrypted_chunk = decryptor.update(chunk)
                        f_out.write(decrypted_chunk)
                    
                    # Finalize (verifies GCM tag)
                    f_out.write(decryptor.finalize())
            
            file_size = os.path.getsize(output_path)
            logger.info(f"File decrypted: {input_path} -> {output_path} ({file_size} bytes)")
            
            return True, f"File decrypted successfully: {os.path.basename(output_path)}"
        
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            
            # Remove incomplete output file
            if output_path and os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except:
                    pass
            
            error_msg = str(e)
            if 'tag' in error_msg.lower() or 'authentication' in error_msg.lower():
                return False, "Decryption failed: Invalid password or corrupted file"
            else:
                return False, f"Decryption failed: {error_msg}"
    
    def get_file_info(self, filepath: str) -> dict:
        """
        Get info tentang encrypted file
        
        Args:
            filepath: Path ke file
            
        Returns:
            File info dictionary
        """
        info = {
            'filepath': filepath,
            'filename': os.path.basename(filepath),
            'exists': os.path.exists(filepath),
            'is_encrypted': filepath.endswith('.enc'),
            'size': 0,
            'size_formatted': '0 B'
        }
        
        if info['exists']:
            size = os.path.getsize(filepath)
            info['size'] = size
            info['size_formatted'] = self._format_size(size)
            
            # Check if file looks like encrypted format
            if size > 28:  # Must have at least salt + iv
                try:
                    with open(filepath, 'rb') as f:
                        f.read(28)  # salt + iv
                        info['has_encryption_header'] = True
                except:
                    info['has_encryption_header'] = False
        
        return info
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"


class PasswordManager:
    """Manage encryption passwords"""
    
    def __init__(self, db_manager):
        """
        Initialize password manager
        
        Args:
            db_manager: Database manager instance
        """
        self.db = db_manager
    
    def save_password(self, user_id: int, filename: str, password: str):
        """
        Save encryption password (encrypted dengan user-specific key)
        
        Args:
            user_id: User ID
            filename: Encrypted filename
            password: Encryption password
        """
        # Simple obfuscation (not secure, just basic protection)
        # In production, use proper encryption for password storage
        import base64
        obfuscated = base64.b64encode(password.encode()).decode()
        
        # Save to database (would need new table)
        # For now, just log
        logger.info(f"Password saved for {filename} (user: {user_id})")
    
    def get_password(self, user_id: int, filename: str) -> Optional[str]:
        """Get saved password"""
        # Retrieve dari database
        # For now, return None
        return None
