# API Reference

Base URL: `http://localhost:5000`

## Endpoints

### System Status

```http
GET /api/status
```

Response:
```json
{
  "timestamp": "2025-01-20T12:00:00",
  "database": {
    "connected": true,
    "count": 2
  },
  "backups": {
    "total_count": 10,
    "total_size_mb": 50.5
  }
}
```

### List Backups

```http
GET /api/backups
```

### List Databases

```http
GET /api/databases
```

### Run Backup

```http
POST /api/backup/run
Content-Type: application/json

{
  "databases": ["db1", "db2"]
}
```

### Restore Database

```http
POST /api/backup/restore
Content-Type: application/json

{
  "database": "db_name",
  "backup_file": "backup_20250120.sql.gz"
}
```

### Download Backup

```http
GET /api/backup/download/<filename>
```

### Scheduler Status

```http
GET /api/scheduler
```

### Start Scheduler

```http
POST /api/scheduler/start
```

### Stop Scheduler

```http
POST /api/scheduler/stop
```

### Test Notifications

```http
POST /api/test/notifications
```

## Examples

### cURL

```bash
curl http://localhost:5000/api/status

curl -X POST http://localhost:5000/api/backup/run \
  -H "Content-Type: application/json" \
  -d '{"databases": ["mydb"]}'
```

### Python

```python
import requests

response = requests.get('http://localhost:5000/api/status')
print(response.json())

response = requests.post(
    'http://localhost:5000/api/backup/run',
    json={'databases': ['mydb']}
)
```
