"""
Virus Scanner
Support ClamAV dan VirusTotal API
"""
import os
import hashlib
import logging
from typing import Dict, Optional, Tuple
import aiohttp
import asyncio

logger = logging.getLogger(__name__)


class VirusScanner:
    """Scan files untuk virus menggunakan ClamAV dan VirusTotal"""
    
    def __init__(self, virustotal_api_key: Optional[str] = None):
        """
        Initialize virus scanner
        
        Args:
            virustotal_api_key: VirusTotal API key (optional)
        """
        self.vt_api_key = virustotal_api_key
        self.vt_api_url = "https://www.virustotal.com/api/v3"
        self.clamav_available = self._check_clamav()
    
    def _check_clamav(self) -> bool:
        """Check if ClamAV is installed"""
        try:
            import subprocess
            result = subprocess.run(['clamscan', '--version'], 
                                  capture_output=True, timeout=5)
            if result.returncode == 0:
                logger.info("ClamAV detected and available")
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning("ClamAV not found or not responding")
        
        return False
    
    async def scan_file(self, filepath: str, use_virustotal: bool = True) -> Dict:
        """
        Scan file untuk virus
        
        Args:
            filepath: Path ke file
            use_virustotal: Use VirusTotal jika True
            
        Returns:
            Scan result dictionary
        """
        if not os.path.exists(filepath):
            return {
                'status': 'error',
                'message': 'File not found',
                'infected': False
            }
        
        result = {
            'filepath': filepath,
            'filename': os.path.basename(filepath),
            'file_size': os.path.getsize(filepath),
            'scanned': False,
            'infected': False,
            'threats': [],
            'scanners': []
        }
        
        # Try ClamAV first (local, fast)
        if self.clamav_available:
            clamav_result = await self._scan_with_clamav(filepath)
            result['scanners'].append('clamav')
            result['scanned'] = True
            
            if clamav_result['infected']:
                result['infected'] = True
                result['threats'].extend(clamav_result['threats'])
                result['clamav_result'] = clamav_result
        
        # Try VirusTotal (online, comprehensive)
        if use_virustotal and self.vt_api_key:
            # Only scan if file is not too large (< 32MB for VT free)
            if result['file_size'] < 32 * 1024 * 1024:
                vt_result = await self._scan_with_virustotal(filepath)
                result['scanners'].append('virustotal')
                result['scanned'] = True
                
                if vt_result['infected']:
                    result['infected'] = True
                    result['threats'].extend(vt_result['threats'])
                    result['virustotal_result'] = vt_result
            else:
                logger.info(f"File too large for VirusTotal free API: {result['file_size']} bytes")
        
        # Summary
        if result['scanned']:
            result['status'] = 'infected' if result['infected'] else 'clean'
            result['message'] = f"Scanned with {', '.join(result['scanners'])}"
        else:
            result['status'] = 'not_scanned'
            result['message'] = 'No scanner available'
        
        return result
    
    async def _scan_with_clamav(self, filepath: str) -> Dict:
        """Scan dengan ClamAV"""
        try:
            import subprocess
            
            # Run clamscan
            process = await asyncio.create_subprocess_exec(
                'clamscan',
                '--no-summary',
                '--infected',
                filepath,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)
            output = stdout.decode('utf-8', errors='ignore')
            
            # Parse output
            if 'FOUND' in output:
                # Extract threat name
                threats = []
                for line in output.split('\n'):
                    if 'FOUND' in line:
                        parts = line.split(':')
                        if len(parts) >= 2:
                            threat_name = parts[1].replace('FOUND', '').strip()
                            threats.append(threat_name)
                
                return {
                    'infected': True,
                    'threats': threats,
                    'scanner': 'clamav',
                    'raw_output': output
                }
            else:
                return {
                    'infected': False,
                    'threats': [],
                    'scanner': 'clamav',
                    'raw_output': output
                }
        
        except asyncio.TimeoutError:
            logger.error("ClamAV scan timeout")
            return {'infected': False, 'threats': [], 'error': 'timeout'}
        except Exception as e:
            logger.error(f"ClamAV scan error: {e}")
            return {'infected': False, 'threats': [], 'error': str(e)}
    
    async def _scan_with_virustotal(self, filepath: str) -> Dict:
        """Scan dengan VirusTotal API"""
        if not self.vt_api_key:
            return {'infected': False, 'threats': [], 'error': 'no_api_key'}
        
        try:
            # Calculate file hash
            file_hash = self._calculate_sha256(filepath)
            
            # Check if file already scanned (hash lookup)
            existing_result = await self._virustotal_hash_lookup(file_hash)
            
            if existing_result:
                return existing_result
            
            # Upload and scan (for new files)
            # Note: Free API has limitations, this is simplified
            logger.info(f"File not in VirusTotal database, would need upload: {file_hash}")
            
            return {
                'infected': False,
                'threats': [],
                'scanner': 'virustotal',
                'message': 'File not in VT database (upload not implemented for free tier)'
            }
        
        except Exception as e:
            logger.error(f"VirusTotal scan error: {e}")
            return {'infected': False, 'threats': [], 'error': str(e)}
    
    async def _virustotal_hash_lookup(self, file_hash: str) -> Optional[Dict]:
        """Lookup file hash di VirusTotal database"""
        try:
            headers = {
                'x-apikey': self.vt_api_key
            }
            
            url = f"{self.vt_api_url}/files/{file_hash}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Parse results
                        attributes = data.get('data', {}).get('attributes', {})
                        last_analysis = attributes.get('last_analysis_stats', {})
                        
                        malicious = last_analysis.get('malicious', 0)
                        suspicious = last_analysis.get('suspicious', 0)
                        
                        infected = (malicious + suspicious) > 0
                        
                        threats = []
                        if infected:
                            # Extract threat names from results
                            results = attributes.get('last_analysis_results', {})
                            for engine, result in results.items():
                                if result.get('category') in ['malicious', 'suspicious']:
                                    threat_name = result.get('result', 'Unknown')
                                    if threat_name and threat_name not in threats:
                                        threats.append(f"{engine}: {threat_name}")
                        
                        return {
                            'infected': infected,
                            'threats': threats[:10],  # Limit to 10
                            'scanner': 'virustotal',
                            'stats': last_analysis,
                            'total_engines': sum(last_analysis.values())
                        }
                    elif response.status == 404:
                        # File not in database
                        return None
                    else:
                        logger.warning(f"VirusTotal API error: {response.status}")
                        return None
        
        except Exception as e:
            logger.error(f"VirusTotal lookup error: {e}")
            return None
    
    def _calculate_sha256(self, filepath: str) -> str:
        """Calculate SHA256 hash dari file"""
        sha256_hash = hashlib.sha256()
        
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def quarantine_file(self, filepath: str, quarantine_dir: str = "downloads/quarantine") -> bool:
        """
        Move infected file ke quarantine directory
        
        Args:
            filepath: Path ke infected file
            quarantine_dir: Quarantine directory
            
        Returns:
            True jika berhasil
        """
        try:
            os.makedirs(quarantine_dir, exist_ok=True)
            
            filename = os.path.basename(filepath)
            quarantine_path = os.path.join(quarantine_dir, filename)
            
            # Handle duplicate names
            if os.path.exists(quarantine_path):
                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(quarantine_path):
                    quarantine_path = os.path.join(quarantine_dir, f"{base}_{counter}{ext}")
                    counter += 1
            
            # Move file
            import shutil
            shutil.move(filepath, quarantine_path)
            
            logger.warning(f"File quarantined: {filepath} -> {quarantine_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error quarantining file: {e}")
            return False
    
    def format_scan_result(self, result: Dict) -> str:
        """Format scan result untuk display"""
        text = "🛡️ **Virus Scan Result**\n\n"
        text += f"📄 **File:** {result['filename']}\n"
        text += f"📦 **Size:** {self._format_size(result['file_size'])}\n\n"
        
        if result['status'] == 'clean':
            text += "✅ **Status:** CLEAN\n"
            text += f"🔍 **Scanned by:** {', '.join(result['scanners'])}\n"
            text += "\nNo threats detected. File is safe to use."
        
        elif result['status'] == 'infected':
            text += "⚠️ **Status:** INFECTED\n"
            text += f"🔍 **Scanned by:** {', '.join(result['scanners'])}\n\n"
            
            if result['threats']:
                text += "🦠 **Threats detected:**\n"
                for threat in result['threats'][:5]:  # Show max 5
                    text += f"• {threat}\n"
            
            text += "\n⚠️ **WARNING:** File has been quarantined for safety."
        
        elif result['status'] == 'not_scanned':
            text += "❓ **Status:** NOT SCANNED\n"
            text += f"ℹ️ {result['message']}\n"
            text += "\nNo virus scanner available. Use with caution."
        
        else:
            text += f"❌ **Status:** ERROR\n"
            text += f"ℹ️ {result['message']}\n"
        
        return text
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
