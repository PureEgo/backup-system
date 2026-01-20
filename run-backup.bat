@echo off
REM Script to run backup from Docker container

echo Running backup from Docker container...
docker exec backup_system_app python main.py --backup