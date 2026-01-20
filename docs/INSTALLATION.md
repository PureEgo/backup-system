# Installation Guide

## Requirements

- Python 3.8+
- MySQL 5.7+ or 8.0+
- mysqldump (MySQL client tools)

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/username/backup_system.git
cd backup_system
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your settings.

### 5. Create MySQL User

```sql
CREATE USER 'backup_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT SELECT, LOCK TABLES, SHOW VIEW, EVENT, TRIGGER ON *.* TO 'backup_user'@'localhost';
FLUSH PRIVILEGES;
```

### 6. Create Directories

```bash
mkdir -p backups logs config
```

### 7. Copy Configuration

```bash
cp config/config.example.json config/config.json
```

### 8. Run

```bash
python main.py --backup
python main.py --web
```

## Docker Installation

```bash
docker-compose up -d
```

## Troubleshooting

### mysqldump not found

Linux:
```bash
sudo apt-get install mysql-client
```

Windows: Add MySQL bin folder to PATH.

### Permission denied

Check MySQL user privileges:
```sql
SHOW GRANTS FOR 'backup_user'@'localhost';
```
