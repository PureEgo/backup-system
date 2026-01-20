import mysql.connector
from mysql.connector import Error
import subprocess
import os
import logging
from datetime import datetime
from typing import List, Optional, Dict


class DatabaseConnector:
    
    def __init__(self, config: Dict):
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 3306)
        self.user = config.get('user')
        self.password = config.get('password')
        self.databases = config.get('databases', [])
        self.connection = None
        self.logger = logging.getLogger(__name__)
    
    def connect(self) -> bool:
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password
            )
            
            if self.connection.is_connected():
                db_info = self.connection.get_server_info()
                self.logger.info(f"Connected to MySQL Server version {db_info}")
                return True
            
        except Error as e:
            self.logger.error(f"Error connecting to MySQL: {e}")
            return False
    
    def disconnect(self) -> None:
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.logger.info("MySQL connection closed")
    
    def test_connection(self) -> bool:
        result = self.connect()
        self.disconnect()
        return result
    
    def get_database_list(self) -> List[str]:
        databases = []
        
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            cursor = self.connection.cursor()
            cursor.execute("SHOW DATABASES")
            
            exclude_dbs = ['information_schema', 'mysql', 'performance_schema', 'sys']
            
            for (db,) in cursor:
                if db not in exclude_dbs:
                    databases.append(db)
            
            cursor.close()
            self.logger.info(f"Found {len(databases)} databases")
            
        except Error as e:
            self.logger.error(f"Error getting database list: {e}")
        
        return databases
    
    def get_database_size(self, database: str) -> float:
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            cursor = self.connection.cursor()
            query = """
                SELECT 
                    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) as size_mb
                FROM information_schema.TABLES
                WHERE table_schema = %s
            """
            
            cursor.execute(query, (database,))
            result = cursor.fetchone()
            cursor.close()
            
            return result[0] if result[0] else 0.0
            
        except Error as e:
            self.logger.error(f"Error getting database size: {e}")
            return 0.0
    
    def create_backup(self, database: str, output_file: str) -> bool:
        try:
            dump_cmd = [
                'mysqldump',
                f'--host={self.host}',
                f'--port={self.port}',
                f'--user={self.user}',
                f'--password={self.password}',
                '--skip-ssl',
                '--single-transaction',
                '--quick',
                '--lock-tables=false',
                '--routines',
                '--triggers',
                '--events',
                database
            ]
            
            self.logger.info(f"Starting backup of database: {database}")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                result = subprocess.run(
                    dump_cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    text=True
                )
            
            if result.returncode == 0:
                file_size = os.path.getsize(output_file) / (1024 * 1024)
                self.logger.info(f"Backup created successfully: {output_file} ({file_size:.2f} MB)")
                return True
            else:
                self.logger.error(f"mysqldump error: {result.stderr}")
                return False
                
        except FileNotFoundError:
            self.logger.error("mysqldump not found. Please install MySQL client tools.")
            return False
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            return False
    
    def restore_backup(self, database: str, input_file: str) -> bool:
        try:
            if not os.path.exists(input_file):
                self.logger.error(f"Backup file not found: {input_file}")
                return False
            
            self.connect()
            cursor = self.connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database}`")
            cursor.close()
            self.disconnect()
            
            restore_cmd = [
                'mysql',
                f'--host={self.host}',
                f'--port={self.port}',
                f'--user={self.user}',
                f'--password={self.password}',
                '--skip-ssl',
                database
            ]
            
            self.logger.info(f"Starting restore of database: {database}")
            
            with open(input_file, 'r', encoding='utf-8') as f:
                result = subprocess.run(
                    restore_cmd,
                    stdin=f,
                    stderr=subprocess.PIPE,
                    text=True
                )
            
            if result.returncode == 0:
                self.logger.info(f"Database restored successfully: {database}")
                return True
            else:
                self.logger.error(f"mysql restore error: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error restoring backup: {e}")
            return False
    
    def get_tables_count(self, database: str) -> int:
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            cursor = self.connection.cursor()
            cursor.execute(f"USE `{database}`")
            cursor.execute("SHOW TABLES")
            
            count = len(cursor.fetchall())
            cursor.close()
            
            return count
            
        except Error as e:
            self.logger.error(f"Error getting tables count: {e}")
            return 0