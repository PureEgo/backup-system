# Architecture

## System Overview

The Backup System is a modular Python application for automated MySQL database backups.

## Components

### Core Modules

```
src/
├── backup_manager.py      - Backup file operations
├── backup_orchestrator.py - Main coordinator
├── config_manager.py      - Configuration handling
├── database_connector.py  - MySQL connection
├── google_drive_handler.py - Google Drive upload
├── logger.py              - Logging setup
├── notification_service.py - Email/Telegram alerts
├── scheduler.py           - Automatic backup scheduler
├── storage_handler.py     - FTP/SFTP storage
└── web_interface.py       - Flask REST API
```

### Data Flow

```
User/Scheduler
     │
     ▼
BackupOrchestrator
     │
     ├── DatabaseConnector (mysqldump)
     │         │
     │         ▼
     ├── BackupManager (compress, verify)
     │         │
     │         ▼
     ├── StorageHandler (FTP/SFTP)
     ├── GoogleDriveHandler (cloud)
     │         │
     │         ▼
     └── NotificationService (alerts)
```

## Configuration

All settings stored in `config/config.json` or environment variables (`.env`).

## API

REST API available at port 5000 (configurable).

Main endpoints:
- GET /api/status
- GET /api/backups  
- POST /api/backup/run
- POST /api/backup/restore

## Security

- Credentials stored in `.env` (not in repo)
- `.gitignore` excludes sensitive files
- SSL/TLS support for remote storage
