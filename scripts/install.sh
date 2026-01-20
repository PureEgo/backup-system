#!/bin/bash

# Installation script for Backup System (Linux)

echo "================================"
echo "Backup System Installation"
echo "================================"
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

if [ $? -ne 0 ]; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Check MySQL client
echo ""
echo "Checking MySQL client..."
mysqldump --version

if [ $? -ne 0 ]; then
    echo "Warning: mysqldump not found"
    echo "Installing MySQL client..."
    
    # Detect OS
    if [ -f /etc/debian_version ]; then
        sudo apt-get update
        sudo apt-get install -y mysql-client
    elif [ -f /etc/redhat-release ]; then
        sudo yum install -y mysql
    else
        echo "Please install mysql-client manually"
    fi
fi

# Create virtual environment (optional but recommended)
echo ""
read -p "Create Python virtual environment? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p backups
mkdir -p logs
mkdir -p config

# Setup configuration
echo ""
if [ ! -f config/config.json ]; then
    echo "Configuration file not found."
    read -p "Create default configuration? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Config is already created in config/config.json
        echo "Configuration file created: config/config.json"
        echo "Please edit this file with your settings"
    fi
else
    echo "Configuration file already exists"
fi

# Test installation
echo ""
echo "Testing installation..."
python3 main.py --status

if [ $? -eq 0 ]; then
    echo ""
    echo "================================"
    echo "Installation completed successfully!"
    echo "================================"
    echo ""
    echo "Next steps:"
    echo "1. Edit config/config.json with your settings"
    echo "2. Test backup: python3 main.py --backup"
    echo "3. Start web interface: python3 main.py --web"
    echo ""
    echo "For automatic backups, setup cron:"
    echo "  crontab -e"
    echo "  Add: 0 2 * * * cd $(pwd) && python3 main.py --backup"
else
    echo ""
    echo "Installation completed with warnings"
    echo "Please check the configuration file"
fi

# Setup cron (optional)
echo ""
read -p "Setup automatic backup with cron? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Backup time (HH:MM, default 02:00): " backup_time
    backup_time=${backup_time:-"02:00"}
    
    # Parse time
    hour=$(echo $backup_time | cut -d: -f1)
    minute=$(echo $backup_time | cut -d: -f2)
    
    # Add to crontab
    current_dir=$(pwd)
    cron_cmd="$minute $hour * * * cd $current_dir && python3 main.py --backup >> $current_dir/logs/cron.log 2>&1"
    
    # Check if entry already exists
    (crontab -l 2>/dev/null | grep -v "main.py --backup"; echo "$cron_cmd") | crontab -
    
    echo "Cron job added: Daily backup at $backup_time"
    echo "View cron jobs: crontab -l"
fi

echo ""
echo "Installation script completed!"
