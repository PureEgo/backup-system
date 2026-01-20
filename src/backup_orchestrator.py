import os
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional

from .config_manager import ConfigManager
from .database_connector import DatabaseConnector
from .backup_manager import BackupManager
from .storage_handler import StorageHandler
from .notification_service import NotificationService
from .scheduler import BackupScheduler
from .logger import Logger

try:
    from .google_drive_handler import GoogleDriveHandler
    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False
    GoogleDriveHandler = None

class BackupOrchestrator:
    
    def __init__(self, config_path: str = "./config/config.json"):
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.load_config()
        
        self.logger = Logger.setup_logging(self.config.get('logging', {}))
        
        self.db_connector = DatabaseConnector(self.config.get('database', {}))
        self.backup_manager = BackupManager(self.config.get('backup', {}))
        self.storage_handler = StorageHandler(self.config.get('storage', {}))
        self.notification_service = NotificationService(
            self.config.get('notifications', {}),
            config_path=config_path
        )
        
        if GOOGLE_DRIVE_AVAILABLE:
            self.google_drive = GoogleDriveHandler(self.config.get('google_drive', {}))
            if self.google_drive.enabled:
                self.logger.info("✅ Google Drive integration enabled")
        else:
            self.google_drive = None
            if self.config.get('google_drive', {}).get('enabled'):
                self.logger.warning("⚠️ Google Drive enabled in config but libraries not installed")
        
        scheduler_config = self.config.get('scheduler', {})
        self.scheduler = BackupScheduler(
            config=scheduler_config,
            backup_function=self._scheduled_backup
        )
        
        if scheduler_config.get('enabled', False):
            self.scheduler.start()
            self.logger.info("✅ Scheduler started automatically")
        
        self.logger.info("Backup Orchestrator initialized")
    
    def run_backup(self, databases: List[str] = None) -> Dict[str, Dict]:
        if databases is None:
            databases = self.config.get('database', {}).get('databases', [])
        
        if not databases:
            self.logger.warning("No databases specified for backup")
            return {}
        
        results = {}
        
        for database in databases:
            success = self._backup_single_database(database)
            results[database] = {
                'status': 'success' if success else 'error',
                'success': success,
                'database': database
            }
        
        return results
    
    def _backup_single_database(self, database: str) -> bool:
        start_time = time.time()
        Logger.log_backup_start(self.logger, database)
        
        try:
            if not self.db_connector.test_connection():
                raise Exception("Database connection failed")
            
            backup_filename = self.backup_manager.generate_backup_filename(database)
            backup_path = os.path.join(self.backup_manager.local_path, backup_filename)
            
            temp_sql_file = backup_path.replace('.gz', '') if backup_path.endswith('.gz') else backup_path
            
            if not self.db_connector.create_backup(database, temp_sql_file):
                raise Exception("Failed to create database dump")
            
            if self.backup_manager.compression:
                compressed_file = self.backup_manager.compress_file(temp_sql_file)
                if compressed_file:
                    backup_path = compressed_file
                else:
                    raise Exception("Compression failed")
            
            if not self.backup_manager.verify_backup(backup_path):
                raise Exception("Backup verification failed")
            
            storage_results = self.storage_handler.upload_backup(backup_path)
            
            if self.google_drive and self.google_drive.enabled:
                try:
                    gdrive_success = self.google_drive.upload_backup(backup_path)
                    storage_results['google_drive'] = gdrive_success
                except Exception as e:
                    self.logger.error(f"Google Drive upload failed: {e}")
                    storage_results['google_drive'] = False
            
            removed_count = self.backup_manager.cleanup_old_backups(database)
            
            duration = time.time() - start_time
            
            backup_info = self.backup_manager.get_backup_info(backup_path)
            
            details = {
                'duration': duration,
                'storage': storage_results,
                'size_mb': backup_info.get('size_mb', 0),
                'removed_old': removed_count
            }
            
            self.notification_service.send_backup_notification(
                success=True,
                database=database,
                backup_file=backup_path,
                details=details
            )
            
            Logger.log_backup_complete(self.logger, database, duration, True)
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            error_message = str(e)
            
            self.logger.error(f"Backup failed for {database}: {error_message}")
            
            self.notification_service.send_backup_notification(
                success=False,
                database=database,
                error_message=error_message,
                details={'duration': duration}
            )
            
            Logger.log_backup_complete(self.logger, database, duration, False)
            return False
    
    def restore_database(self, database: str, backup_file: str) -> bool:
        try:
            self.logger.info(f"Starting restore for database: {database}")
            
            if not os.path.exists(backup_file):
                raise Exception(f"Backup file not found: {backup_file}")
            
            if backup_file.endswith('.gz'):
                decompressed_file = self.backup_manager.decompress_file(backup_file)
                if not decompressed_file:
                    raise Exception("Failed to decompress backup file")
                restore_file = decompressed_file
            else:
                restore_file = backup_file
            
            if not self.db_connector.restore_backup(database, restore_file):
                raise Exception("Database restore failed")
            
            if restore_file != backup_file and os.path.exists(restore_file):
                os.remove(restore_file)
            
            self.logger.info(f"Database restored successfully: {database}")
            return True
            
        except Exception as e:
            self.logger.error(f"Restore failed: {e}")
            return False
    
    def get_system_status(self) -> Dict:
        try:
            db_connected = self.db_connector.test_connection()
            databases = self.db_connector.get_database_list() if db_connected else []
            
            all_backups = self.backup_manager.list_backups()
            total_size = self.backup_manager.get_total_backup_size()
            
            storage_status = {}
            if self.config.get('storage', {}).get('ftp', {}).get('enabled'):
                storage_status['ftp'] = self.storage_handler.test_ftp_connection()
            if self.config.get('storage', {}).get('sftp', {}).get('enabled'):
                storage_status['sftp'] = self.storage_handler.test_sftp_connection()
            if self.google_drive and self.google_drive.enabled:
                storage_status['google_drive'] = self.google_drive.test_connection()
            
            notification_status = {}
            if self.config.get('notifications', {}).get('email', {}).get('enabled'):
                notification_status['email'] = self.notification_service.test_email_connection()
            if self.config.get('notifications', {}).get('telegram', {}).get('enabled'):
                notification_status['telegram'] = self.notification_service.test_telegram_connection()
            
            status = {
                'timestamp': datetime.now().isoformat(),
                'database': {
                    'connected': db_connected,
                    'databases': databases,
                    'count': len(databases)
                },
                'backups': {
                    'total_count': len(all_backups),
                    'total_size_mb': total_size,
                    'oldest': all_backups[-1]['created'].isoformat() if all_backups else None,
                    'newest': all_backups[0]['created'].isoformat() if all_backups else None
                },
                'storage': storage_status,
                'notifications': notification_status
            }
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {'error': str(e)}
    
    def list_all_backups(self) -> List[Dict]:
        return self.backup_manager.list_backups()
    
    def get_database_info(self, database: str) -> Dict:
        try:
            if not self.db_connector.test_connection():
                return {'error': 'Database connection failed'}
            
            size = self.db_connector.get_database_size(database)
            tables_count = self.db_connector.get_tables_count(database)
            backups = self.backup_manager.list_backups(database)
            
            info = {
                'name': database,
                'size_mb': size,
                'tables_count': tables_count,
                'backups_count': len(backups),
                'latest_backup': backups[0]['created'].isoformat() if backups else None
            }
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting database info: {e}")
            return {'error': str(e)}
    
    def _scheduled_backup(self):
        try:
            self.logger.info("🕒 Scheduled backup triggered")
            databases = self.config.get('database', {}).get('databases', [])
            results = self.run_backup(databases)
            
            success_count = sum(1 for r in results.values() if r.get('success'))
            total = len(results)
            
            self.logger.info(f"✅ Scheduled backup completed: {success_count}/{total} successful")
        except Exception as e:
            self.logger.error(f"❌ Scheduled backup failed: {e}")
    
    def get_scheduler_status(self) -> Dict:
        try:
            return {
                'enabled': self.scheduler.enabled,
                'running': self.scheduler.running,
                'interval': self.scheduler.interval,
                'backup_time': self.scheduler.backup_time,
                'next_run': self.scheduler.get_next_run() if self.scheduler.running else 'Not scheduled',
                'timezone': self.scheduler.timezone
            }
        except Exception as e:
            self.logger.error(f"Error getting scheduler status: {e}")
            return {'error': str(e)}
    
    def start_scheduler(self) -> bool:
        try:
            self.scheduler.start()
            self.logger.info("✅ Scheduler started")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error starting scheduler: {e}")
            return False
    
    def stop_scheduler(self) -> bool:
        try:
            self.scheduler.stop()
            self.logger.info("⏹️ Scheduler stopped")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error stopping scheduler: {e}")
            return False
    
    def run_scheduler_now(self) -> Dict:
        try:
            self.logger.info("▶️ Running scheduler backup now")
            self.scheduler.run_now()
            return {'success': True, 'message': 'Backup started'}
        except Exception as e:
            self.logger.error(f"❌ Error running scheduler backup: {e}")
            return {'success': False, 'error': str(e)}
    
    def configure_scheduler(self, config: Dict) -> bool:
        try:
            self.config['scheduler'].update(config)
            
            if self.scheduler.running:
                self.scheduler.stop()
            
            self.scheduler = BackupScheduler(
                config=self.config['scheduler'],
                backup_function=self._scheduled_backup
            )
            
            if config.get('enabled', False):
                self.scheduler.start()
            
            self.config_manager.save_config(self.config)
            
            self.logger.info("✅ Scheduler configured")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error configuring scheduler: {e}")
            return False