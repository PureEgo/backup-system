import pytest
import os
import json
import tempfile
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.config_manager import ConfigManager
from src.backup_manager import BackupManager
from src.notification_service import NotificationService

class TestConfigManager:
    
    def test_load_config(self, tmp_path):
        config_file = tmp_path / "test_config.json"
        config_data = {
            "database": {
                "host": "localhost",
                "port": 3306,
                "user": "test",
                "password": "test"
            },
            "backup": {},
            "storage": {},
            "notifications": {},
            "logging": {}
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        config_manager = ConfigManager(str(config_file))
        config = config_manager.load_config()
        
        assert config['database']['host'] == 'localhost'
        assert config['database']['port'] == 3306
    
    def test_get_config_value(self, tmp_path):
        config_file = tmp_path / "test_config.json"
        config_data = {
            "database": {
                "host": "localhost"
            },
            "backup": {},
            "storage": {},
            "notifications": {},
            "logging": {}
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        config_manager = ConfigManager(str(config_file))
        config_manager.load_config()
        
        assert config_manager.get('database.host') == 'localhost'
        assert config_manager.get('database.port', 3306) == 3306
    
    def test_update_config(self, tmp_path):
        config_file = tmp_path / "test_config.json"
        config_data = {
            "database": {"host": "localhost"},
            "backup": {},
            "storage": {},
            "notifications": {},
            "logging": {}
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        config_manager = ConfigManager(str(config_file))
        config_manager.load_config()
        config_manager.update('database.host', 'newhost')
        
        assert config_manager.get('database.host') == 'newhost'

class TestBackupManager:
    
    def test_generate_filename(self):
        config = {
            'local_path': './backups',
            'compression': True,
            'compression_format': 'gzip'
        }
        
        manager = BackupManager(config)
        filename = manager.generate_backup_filename('testdb', 'full')
        
        assert 'testdb' in filename
        assert 'full' in filename
        assert filename.endswith('.sql.gz')
    
    def test_calculate_checksum(self, tmp_path):
        config = {'local_path': str(tmp_path)}
        manager = BackupManager(config)
        
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        checksum = manager.calculate_checksum(str(test_file))
        assert len(checksum) == 32
        assert checksum == manager.calculate_checksum(str(test_file))
    
    def test_list_backups(self, tmp_path):
        config = {'local_path': str(tmp_path)}
        manager = BackupManager(config)
        
        (tmp_path / "db1_full_20240101_120000.sql.gz").touch()
        (tmp_path / "db2_full_20240101_130000.sql.gz").touch()
        
        backups = manager.list_backups()
        assert len(backups) == 2
    
    def test_verify_backup(self, tmp_path):
        config = {'local_path': str(tmp_path)}
        manager = BackupManager(config)
        
        empty_file = tmp_path / "empty.sql.gz"
        empty_file.touch()
        assert not manager.verify_backup(str(empty_file))
        
        assert not manager.verify_backup(str(tmp_path / "nonexistent.sql.gz"))

class TestNotificationService:
    
    def test_format_success_message(self):
        config = {
            'email': {'enabled': False},
            'telegram': {'enabled': False}
        }
        
        service = NotificationService(config)
        message = service._format_success_message('testdb', '/path/to/backup.sql.gz')
        
        assert 'testdb' in message
        assert 'Success' in message or 'success' in message.lower()
    
    def test_format_failure_message(self):
        config = {
            'email': {'enabled': False},
            'telegram': {'enabled': False}
        }
        
        service = NotificationService(config)
        message = service._format_failure_message('testdb', 'Connection timeout')
        
        assert 'testdb' in message
        assert 'Failed' in message or 'failed' in message.lower()
        assert 'Connection timeout' in message

class TestIntegration:
    
    def test_full_workflow(self, tmp_path):
        pass

@pytest.fixture
def temp_config(tmp_path):
    config_file = tmp_path / "config.json"
    config_data = {
        "database": {
            "host": "localhost",
            "port": 3306,
            "user": "test",
            "password": "test",
            "databases": ["testdb"]
        },
        "backup": {
            "local_path": str(tmp_path / "backups"),
            "compression": True,
            "retention_days": 30,
            "max_backups": 10
        },
        "storage": {
            "local": {"enabled": True}
        },
        "notifications": {
            "email": {"enabled": False},
            "telegram": {"enabled": False}
        },
        "logging": {
            "level": "INFO",
            "file": str(tmp_path / "test.log")
        },
        "scheduler": {
            "enabled": False
        }
    }
    
    with open(config_file, 'w') as f:
        json.dump(config_data, f)
    
    return str(config_file)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
