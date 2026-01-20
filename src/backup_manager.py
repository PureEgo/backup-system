import os
import gzip
import shutil
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import hashlib

class BackupManager:
    
    def __init__(self, config: Dict):
        self.config = config
        self.local_path = config.get('local_path', './backups')
        self.compression = config.get('compression', True)
        self.compression_format = config.get('compression_format', 'gzip')
        self.encryption = config.get('encryption', False)
        self.retention_days = config.get('retention_days', 30)
        self.max_backups = config.get('max_backups', 10)
        self.logger = logging.getLogger(__name__)
        
        self._ensure_backup_dir()
    
    def _ensure_backup_dir(self) -> None:
        os.makedirs(self.local_path, exist_ok=True)
        self.logger.info(f"Backup directory: {self.local_path}")
    
    def generate_backup_filename(self, database: str, backup_type: str = "full") -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{database}_{backup_type}_{timestamp}.sql"
        
        if self.compression:
            filename += ".gz"
        
        return filename
    
    def compress_file(self, input_file: str, output_file: str = None) -> Optional[str]:
        if output_file is None:
            output_file = input_file + '.gz'
        
        try:
            self.logger.info(f"Compressing file: {input_file}")
            
            with open(input_file, 'rb') as f_in:
                with gzip.open(output_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            os.remove(input_file)
            
            original_size = os.path.getsize(input_file) if os.path.exists(input_file) else 0
            compressed_size = os.path.getsize(output_file)
            compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
            
            self.logger.info(f"File compressed: {output_file} (saved {compression_ratio:.1f}%)")
            return output_file
            
        except Exception as e:
            self.logger.error(f"Error compressing file: {e}")
            return None
    
    def decompress_file(self, input_file: str, output_file: str = None) -> Optional[str]:
        if output_file is None:
            output_file = input_file.replace('.gz', '')
        
        try:
            self.logger.info(f"Decompressing file: {input_file}")
            
            with gzip.open(input_file, 'rb') as f_in:
                with open(output_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            self.logger.info(f"File decompressed: {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"Error decompressing file: {e}")
            return None
    
    def calculate_checksum(self, file_path: str) -> str:
        try:
            md5_hash = hashlib.md5()
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
            
            checksum = md5_hash.hexdigest()
            self.logger.debug(f"Checksum for {file_path}: {checksum}")
            return checksum
            
        except Exception as e:
            self.logger.error(f"Error calculating checksum: {e}")
            return ""
    
    def get_backup_info(self, backup_file: str) -> Dict:
        try:
            stat = os.stat(backup_file)
            
            info = {
                'filename': os.path.basename(backup_file),
                'path': backup_file,
                'size': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created': datetime.fromtimestamp(stat.st_ctime),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'checksum': self.calculate_checksum(backup_file)
            }
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting backup info: {e}")
            return {}
    
    def list_backups(self, database: str = None) -> List[Dict]:
        backups = []
        
        try:
            for filename in os.listdir(self.local_path):
                if filename.endswith(('.sql', '.sql.gz')):
                    if database and not filename.startswith(database):
                        continue
                    
                    file_path = os.path.join(self.local_path, filename)
                    info = self.get_backup_info(file_path)
                    if info:
                        backups.append(info)
            
            backups.sort(key=lambda x: x['created'], reverse=True)
            
            self.logger.info(f"Found {len(backups)} backup(s)")
            
        except Exception as e:
            self.logger.error(f"Error listing backups: {e}")
        
        return backups
    
    def cleanup_old_backups(self, database: str = None) -> int:
        removed_count = 0
        
        try:
            backups = self.list_backups(database)
            
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            for backup in backups:
                if backup['created'] < cutoff_date:
                    os.remove(backup['path'])
                    self.logger.info(f"Removed old backup: {backup['filename']}")
                    removed_count += 1
            
            if len(backups) > self.max_backups:
                excess_backups = backups[self.max_backups:]
                for backup in excess_backups:
                    if os.path.exists(backup['path']):
                        os.remove(backup['path'])
                        self.logger.info(f"Removed excess backup: {backup['filename']}")
                        removed_count += 1
            
            if removed_count > 0:
                self.logger.info(f"Cleanup completed: {removed_count} backup(s) removed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
        
        return removed_count
    
    def get_total_backup_size(self) -> float:
        total_size = 0
        
        try:
            for filename in os.listdir(self.local_path):
                if filename.endswith(('.sql', '.sql.gz')):
                    file_path = os.path.join(self.local_path, filename)
                    total_size += os.path.getsize(file_path)
            
            return round(total_size / (1024 * 1024), 2)
            
        except Exception as e:
            self.logger.error(f"Error calculating total size: {e}")
            return 0.0
    
    def verify_backup(self, backup_file: str) -> bool:
        try:
            if not os.path.exists(backup_file):
                self.logger.error(f"Backup file not found: {backup_file}")
                return False
            
            file_size = os.path.getsize(backup_file)
            if file_size == 0:
                self.logger.error(f"Backup file is empty: {backup_file}")
                return False
            
            if backup_file.endswith('.gz'):
                with gzip.open(backup_file, 'rb') as f:
                    f.read(1)
            
            self.logger.info(f"Backup verification passed: {backup_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Backup verification failed: {e}")
            return False
