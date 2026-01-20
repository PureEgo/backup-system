import os
import logging
from ftplib import FTP, FTP_TLS
import paramiko
from typing import Dict, Optional, List

class StorageHandler:
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def upload_backup(self, local_file: str) -> Dict[str, bool]:
        results = {}
        
        if not os.path.exists(local_file):
            self.logger.error(f"Local file not found: {local_file}")
            return {'error': False}
        
        if self.config.get('local', {}).get('enabled'):
            results['local'] = self._handle_local_storage(local_file)
        
        if self.config.get('ftp', {}).get('enabled'):
            results['ftp'] = self._upload_ftp(local_file)
        
        if self.config.get('sftp', {}).get('enabled'):
            results['sftp'] = self._upload_sftp(local_file)
        
        return results
    
    def _handle_local_storage(self, local_file: str) -> bool:
        try:
            self.logger.info(f"Local storage: {local_file}")
            return True
        except Exception as e:
            self.logger.error(f"Local storage error: {e}")
            return False
    
    def _upload_ftp(self, local_file: str) -> bool:
        ftp_config = self.config.get('ftp', {})
        
        try:
            host = ftp_config.get('host')
            port = ftp_config.get('port', 21)
            user = ftp_config.get('user')
            password = ftp_config.get('password')
            remote_path = ftp_config.get('remote_path', '/')
            use_ssl = ftp_config.get('use_ssl', False)
            
            self.logger.info(f"Connecting to FTP server: {host}:{port}")
            
            if use_ssl:
                ftp = FTP_TLS()
            else:
                ftp = FTP()
            
            ftp.connect(host, port)
            ftp.login(user, password)
            
            if use_ssl:
                ftp.prot_p()
            
            try:
                ftp.cwd(remote_path)
            except:
                self._create_ftp_directory(ftp, remote_path)
                ftp.cwd(remote_path)
            
            filename = os.path.basename(local_file)
            
            with open(local_file, 'rb') as f:
                ftp.storbinary(f'STOR {filename}', f)
            
            self.logger.info(f"FTP upload successful: {filename}")
            ftp.quit()
            return True
            
        except Exception as e:
            self.logger.error(f"FTP upload error: {e}")
            return False
    
    def _create_ftp_directory(self, ftp: FTP, path: str) -> None:
        dirs = path.strip('/').split('/')
        current_path = ''
        
        for directory in dirs:
            current_path += '/' + directory
            try:
                ftp.mkd(current_path)
                self.logger.info(f"Created FTP directory: {current_path}")
            except:
                pass
    
    def _upload_sftp(self, local_file: str) -> bool:
        sftp_config = self.config.get('sftp', {})
        
        try:
            host = sftp_config.get('host')
            port = sftp_config.get('port', 22)
            user = sftp_config.get('user')
            password = sftp_config.get('password')
            private_key = sftp_config.get('private_key')
            remote_path = sftp_config.get('remote_path', '/')
            
            self.logger.info(f"Connecting to SFTP server: {host}:{port}")
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if private_key and os.path.exists(private_key):
                ssh.connect(host, port=port, username=user, key_filename=private_key)
            else:
                ssh.connect(host, port=port, username=user, password=password)
            
            sftp = ssh.open_sftp()
            
            self._create_sftp_directory(sftp, remote_path)
            
            filename = os.path.basename(local_file)
            remote_file = os.path.join(remote_path, filename).replace('\\', '/')
            
            sftp.put(local_file, remote_file)
            
            self.logger.info(f"SFTP upload successful: {filename}")
            
            sftp.close()
            ssh.close()
            return True
            
        except Exception as e:
            self.logger.error(f"SFTP upload error: {e}")
            return False
    
    def _create_sftp_directory(self, sftp: paramiko.SFTPClient, path: str) -> None:
        dirs = path.strip('/').split('/')
        current_path = ''
        
        for directory in dirs:
            current_path += '/' + directory
            try:
                sftp.stat(current_path)
            except:
                try:
                    sftp.mkdir(current_path)
                    self.logger.info(f"Created SFTP directory: {current_path}")
                except:
                    pass
    
    def test_ftp_connection(self) -> bool:
        ftp_config = self.config.get('ftp', {})
        
        try:
            host = ftp_config.get('host')
            port = ftp_config.get('port', 21)
            user = ftp_config.get('user')
            password = ftp_config.get('password')
            use_ssl = ftp_config.get('use_ssl', False)
            
            if use_ssl:
                ftp = FTP_TLS()
            else:
                ftp = FTP()
            
            ftp.connect(host, port)
            ftp.login(user, password)
            ftp.quit()
            
            self.logger.info("FTP connection test successful")
            return True
            
        except Exception as e:
            self.logger.error(f"FTP connection test failed: {e}")
            return False
    
    def test_sftp_connection(self) -> bool:
        sftp_config = self.config.get('sftp', {})
        
        try:
            host = sftp_config.get('host')
            port = sftp_config.get('port', 22)
            user = sftp_config.get('user')
            password = sftp_config.get('password')
            private_key = sftp_config.get('private_key')
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if private_key and os.path.exists(private_key):
                ssh.connect(host, port=port, username=user, key_filename=private_key)
            else:
                ssh.connect(host, port=port, username=user, password=password)
            
            ssh.close()
            
            self.logger.info("SFTP connection test successful")
            return True
            
        except Exception as e:
            self.logger.error(f"SFTP connection test failed: {e}")
            return False
    
    def list_remote_backups_ftp(self) -> List[str]:
        ftp_config = self.config.get('ftp', {})
        backups = []
        
        try:
            host = ftp_config.get('host')
            port = ftp_config.get('port', 21)
            user = ftp_config.get('user')
            password = ftp_config.get('password')
            remote_path = ftp_config.get('remote_path', '/')
            use_ssl = ftp_config.get('use_ssl', False)
            
            if use_ssl:
                ftp = FTP_TLS()
            else:
                ftp = FTP()
            
            ftp.connect(host, port)
            ftp.login(user, password)
            ftp.cwd(remote_path)
            
            files = ftp.nlst()
            backups = [f for f in files if f.endswith(('.sql', '.sql.gz'))]
            
            ftp.quit()
            
        except Exception as e:
            self.logger.error(f"Error listing FTP backups: {e}")
        
        return backups
    
    def download_backup_ftp(self, remote_filename: str, local_path: str) -> bool:
        ftp_config = self.config.get('ftp', {})
        
        try:
            host = ftp_config.get('host')
            port = ftp_config.get('port', 21)
            user = ftp_config.get('user')
            password = ftp_config.get('password')
            remote_path = ftp_config.get('remote_path', '/')
            use_ssl = ftp_config.get('use_ssl', False)
            
            if use_ssl:
                ftp = FTP_TLS()
            else:
                ftp = FTP()
            
            ftp.connect(host, port)
            ftp.login(user, password)
            ftp.cwd(remote_path)
            
            with open(local_path, 'wb') as f:
                ftp.retrbinary(f'RETR {remote_filename}', f.write)
            
            ftp.quit()
            
            self.logger.info(f"Downloaded backup from FTP: {remote_filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error downloading from FTP: {e}")
            return False
