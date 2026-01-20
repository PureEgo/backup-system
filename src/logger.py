import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Dict

class Logger:
    
    @staticmethod
    def setup_logging(config: Dict) -> logging.Logger:
        log_level = config.get('level', 'INFO')
        log_file = config.get('file', './logs/backup.log')
        max_size_mb = config.get('max_size_mb', 10)
        backup_count = config.get('backup_count', 5)
        console_output = config.get('console_output', True)
        
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        logger = logging.getLogger()
        logger.setLevel(getattr(logging, log_level.upper()))
        
        logger.handlers.clear()
        
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_size_mb * 1024 * 1024,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
        
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(getattr(logging, log_level.upper()))
            console_handler.setFormatter(simple_formatter)
            logger.addHandler(console_handler)
        
        logger.info("=" * 80)
        logger.info(f"Backup System Started - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)
        
        return logger
    
    @staticmethod
    def log_backup_start(logger: logging.Logger, database: str) -> None:
        logger.info("-" * 80)
        logger.info(f"Starting backup for database: {database}")
        logger.info("-" * 80)
    
    @staticmethod
    def log_backup_complete(
        logger: logging.Logger,
        database: str,
        duration: float,
        success: bool
    ) -> None:
        status = "SUCCESS" if success else "FAILED"
        logger.info("-" * 80)
        logger.info(f"Backup {status} for database: {database}")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info("-" * 80)
