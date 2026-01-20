import json
import os
from typing import Dict, Any
import logging

class ConfigManager:
    
    def __init__(self, config_path: str = "./config/config.json"):
        self.config_path = config_path
        self.config = None
        self.logger = logging.getLogger(__name__)
        
    def load_config(self) -> Dict[str, Any]:
        try:
            if not os.path.exists(self.config_path):
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            self.logger.info(f"Configuration loaded from {self.config_path}")
            self._validate_config()
            return self.config
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in config file: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            raise
    
    def _validate_config(self) -> None:
        required_sections = ['database', 'backup', 'storage', 'notifications', 'logging']
        
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required configuration section: {section}")
        
        db_required = ['host', 'port', 'user', 'password']
        for field in db_required:
            if field not in self.config['database']:
                raise ValueError(f"Missing required database field: {field}")
        
        self.logger.info("Configuration validation passed")
    
    def get(self, key: str, default: Any = None) -> Any:
        if self.config is None:
            self.load_config()
        
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def save_config(self, config: Dict[str, Any] = None) -> None:
        if config is not None:
            self.config = config
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            
            self.logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            raise
    
    def update(self, key: str, value: Any) -> None:
        if self.config is None:
            self.load_config()
        
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.logger.info(f"Configuration updated: {key} = {value}")
