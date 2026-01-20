@echo off
REM Installation script for Backup System (Windows)

echo ================================
echo Backup System Installation
echo ================================
echo.

REM Check Python version
echo Checking Python version...
python --version
if errorlevel 1 (
    echo Error: Python is not installed
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

REM Check MySQL client
echo.
echo Checking MySQL client...
mysqldump --version
if errorlevel 1 (
    echo Warning: mysqldump not found
    echo Please install MySQL client or add MySQL bin directory to PATH
    echo Download from: https://dev.mysql.com/downloads/mysql/
    pause
)

REM Create virtual environment (optional)
echo.
set /p VENV="Create Python virtual environment? (y/n): "
if /i "%VENV%"=="y" (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
)

REM Install Python dependencies
echo.
echo Installing Python dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

REM Create necessary directories
echo.
echo Creating directories...
if not exist "backups" mkdir backups
if not exist "logs" mkdir logs
if not exist "config" mkdir config

REM Setup configuration
echo.
if not exist "config\config.json" (
    echo Configuration file not found.
    set /p CONFIG="Create default configuration? (y/n): "
    if /i "%CONFIG%"=="y" (
        echo Configuration file created: config\config.json
        echo Please edit this file with your settings
    )
) else (
    echo Configuration file already exists
)

REM Test installation
echo.
echo Testing installation...
python main.py --status

if errorlevel 0 (
    echo.
    echo ================================
    echo Installation completed successfully!
    echo ================================
    echo.
    echo Next steps:
    echo 1. Edit config\config.json with your settings
    echo 2. Test backup: python main.py --backup
    echo 3. Start web interface: python main.py --web
    echo.
) else (
    echo.
    echo Installation completed with warnings
    echo Please check the configuration file
)

REM Setup Windows Task Scheduler (optional)
echo.
set /p TASK="Setup automatic backup with Task Scheduler? (y/n): "
if /i "%TASK%"=="y" (
    set /p TASKTIME="Backup time (HH:MM, default 02:00): "
    if "%TASKTIME%"=="" set TASKTIME=02:00
    
    set SCRIPT_PATH=%CD%\main.py
    set PYTHON_PATH=python
    
    schtasks /create /tn "DatabaseBackup" /tr "%PYTHON_PATH% %SCRIPT_PATH% --backup" /sc daily /st %TASKTIME% /f
    
    echo Task Scheduler job created: Daily backup at %TASKTIME%
    echo View tasks: schtasks /query /tn "DatabaseBackup"
)

echo.
echo Installation script completed!
pause
