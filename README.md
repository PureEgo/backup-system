# Automated Database Backup System

System automatycznego tworzenia kopii zapasowych baz danych MySQL z obsługą wielu lokalizacji przechowywania, powiadomień i harmonogramu.

## Funkcje

- Automatyczne kopie zapasowe MySQL
- Kompresja gzip
- Przechowywanie: lokalne, Google Drive, FTP, SFTP
- Powiadomienia: Email (SMTP), Telegram
- Harmonogram automatycznych backupów
- Web interfejs do zarządzania
- Rotacja starych kopii zapasowych
- Przywracanie baz danych

## Wymagania

- Python 3.8+
- MySQL Server 5.7+ lub 8.0+
- mysqldump

## Instalacja

### 1. Klonowanie repozytorium

```bash
git clone https://github.com/yourusername/backup_system.git
cd backup_system
```

### 2. Tworzenie środowiska wirtualnego

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. Instalacja zależności

```bash
pip install -r requirements.txt
```

### 4. Konfiguracja zmiennych środowiskowych

```bash
cp .env.example .env
```

Edytuj plik `.env` i ustaw swoje wartości:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=backup_user
DB_PASSWORD=your_password
DB_DATABASES=database1,database2

EMAIL_ENABLED=true
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SENDER=your@email.com
EMAIL_PASSWORD=your_app_password

TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_IDS=your_chat_id
```

### 5. Utworzenie użytkownika MySQL

```sql
CREATE USER 'backup_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT SELECT, LOCK TABLES, SHOW VIEW, EVENT, TRIGGER ON *.* TO 'backup_user'@'localhost';
FLUSH PRIVILEGES;
```

### 6. Utworzenie katalogów

```bash
mkdir -p backups logs config
```

## Użycie

### Ręczny backup

```bash
python main.py --backup
```

### Backup wybranych baz

```bash
python main.py --backup --databases db1 db2
```

### Web interfejs

```bash
python main.py --web
```

Dostępny pod: `http://localhost:5000`

### Status systemu

```bash
python main.py --status
```

### Lista kopii

```bash
python main.py --list
```

### Przywracanie

```bash
python main.py --restore database_name backup_file.sql.gz
```

## Harmonogram

### Linux (cron)

```bash
crontab -e
```

Dodaj:
```
0 2 * * * cd /path/to/backup_system && /path/to/venv/bin/python main.py --backup
```

### Windows

Użyj Task Scheduler lub:

```bash
python -c "from src.scheduler import WindowsScheduler; WindowsScheduler.create_scheduled_task('DatabaseBackup', 'main.py', '02:00')"
```

## Powiadomienia

### Email (Gmail)

1. Włącz 2FA na koncie Google
2. Wygeneruj App Password
3. Ustaw w `.env`:

```env
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SENDER=your@gmail.com
EMAIL_PASSWORD=your_app_password
```

### Telegram

1. Utwórz bota: [@BotFather](https://t.me/botfather)
2. Pobierz token
3. Napisz do bota
4. Pobierz chat_id:
```bash
curl https://api.telegram.org/bot<TOKEN>/getUpdates
```

## Google Drive

1. Utwórz projekt w [Google Cloud Console](https://console.cloud.google.com)
2. Włącz Google Drive API
3. Utwórz credentials (OAuth 2.0)
4. Pobierz plik JSON jako `config/google_drive_credentials.json`
5. Uruchom autoryzację:

```bash
python authorize_google_drive.py
```

## API Endpoints

| Endpoint | Method | Opis |
|----------|--------|------|
| `/api/status` | GET | Status systemu |
| `/api/backups` | GET | Lista backupów |
| `/api/databases` | GET | Lista baz danych |
| `/api/backup/run` | POST | Uruchom backup |
| `/api/backup/restore` | POST | Przywróć bazę |
| `/api/backup/download/<file>` | GET | Pobierz backup |
| `/api/scheduler/start` | POST | Start harmonogramu |
| `/api/scheduler/stop` | POST | Stop harmonogramu |
| `/api/test/notifications` | POST | Test powiadomień |

## Struktura projektu

```
backup_system/
├── config/
│   └── config.example.json
├── src/
│   ├── backup_manager.py
│   ├── backup_orchestrator.py
│   ├── config_manager.py
│   ├── database_connector.py
│   ├── google_drive_handler.py
│   ├── logger.py
│   ├── notification_service.py
│   ├── scheduler.py
│   ├── storage_handler.py
│   └── web_interface.py
├── tests/
│   └── test_backup.py
├── main.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Rozwiązywanie problemów

### mysqldump nie znaleziony

Linux:
```bash
sudo apt-get install mysql-client
```

Windows: Dodaj MySQL bin do PATH

### Błąd połączenia MySQL

1. Sprawdź czy MySQL działa
2. Zweryfikuj dane logowania
3. Sprawdź uprawnienia użytkownika

### Powiadomienia nie działają

Email: Sprawdź App Password dla Gmail
Telegram: Zweryfikuj token i chat_id

## Bezpieczeństwo

- Nie commituj `.env` do repozytorium
- Używaj silnych haseł
- Ogranicz uprawnienia użytkownika MySQL
- Preferuj SFTP zamiast FTP

## Testy

```bash
pytest tests/ -v
```

## Licencja

MIT License

## Autor

Projekt inżynierski - 2025/2026
