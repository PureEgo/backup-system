#!/usr/bin/env python3

import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src import BackupOrchestrator, WebInterface


def main():
    parser = argparse.ArgumentParser(
        description='Automated Database Backup System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --backup
  python main.py --backup --databases db1 db2
  python main.py --web
  python main.py --web --port 8080
  python main.py --status
  python main.py --list
  python main.py --restore db_name backup_file.sql.gz
        """
    )
    
    parser.add_argument(
        '--config',
        default='./config/config.json',
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--backup',
        action='store_true',
        help='Run backup immediately'
    )
    
    parser.add_argument(
        '--databases',
        nargs='+',
        help='Specific databases to backup'
    )
    
    parser.add_argument(
        '--web',
        action='store_true',
        help='Start web interface'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        help='Web interface port'
    )
    
    parser.add_argument(
        '--host',
        help='Web interface host'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show system status'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all backups'
    )
    
    parser.add_argument(
        '--restore',
        nargs=2,
        metavar=('DATABASE', 'BACKUP_FILE'),
        help='Restore database from backup'
    )
    
    args = parser.parse_args()
    
    try:
        orchestrator = BackupOrchestrator(args.config)
        
        if args.backup:
            print("Starting backup...")
            results = orchestrator.run_backup(args.databases)
            
            print("\nBackup Results:")
            for db, success in results.items():
                status = "SUCCESS" if success else "FAILED"
                print(f"  {db}: {status}")
            
            return 0 if all(results.values()) else 1
        
        elif args.web:
            web = WebInterface(args.config)
            web.run(host=args.host, port=args.port, debug=False, use_reloader=False)
            return 0
        
        elif args.status:
            status = orchestrator.get_system_status()
            
            print("\n=== System Status ===")
            print(f"\nTimestamp: {status.get('timestamp', 'N/A')}")
            
            print("\nDatabase:")
            db_status = status.get('database', {})
            print(f"  Connected: {db_status.get('connected', False)}")
            print(f"  Databases: {db_status.get('count', 0)}")
            
            print("\nBackups:")
            backup_status = status.get('backups', {})
            print(f"  Total: {backup_status.get('total_count', 0)}")
            print(f"  Total Size: {backup_status.get('total_size_mb', 0)} MB")
            print(f"  Newest: {backup_status.get('newest', 'N/A')}")
            print(f"  Oldest: {backup_status.get('oldest', 'N/A')}")
            
            print("\nStorage:")
            for storage, connected in status.get('storage', {}).items():
                status_icon = "+" if connected else "-"
                print(f"  {status_icon} {storage.upper()}")
            
            print("\nNotifications:")
            for service, connected in status.get('notifications', {}).items():
                status_icon = "+" if connected else "-"
                print(f"  {status_icon} {service.upper()}")
            
            return 0
        
        elif args.list:
            backups = orchestrator.list_all_backups()
            
            print(f"\n=== Backups ({len(backups)}) ===\n")
            
            if not backups:
                print("No backups found.")
                return 0
            
            for backup in backups:
                print(f"File: {backup['filename']}")
                print(f"  Size: {backup['size_mb']} MB")
                print(f"  Created: {backup['created']}")
                print(f"  Checksum: {backup['checksum']}")
                print()
            
            return 0
        
        elif args.restore:
            database, backup_file = args.restore
            
            print(f"\nRestoring database '{database}' from '{backup_file}'...")
            
            success = orchestrator.restore_database(database, backup_file)
            
            if success:
                print("Restore completed successfully!")
                return 0
            else:
                print("Restore failed. Check logs for details.")
                return 1
        
        else:
            parser.print_help()
            return 1
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 130
    
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
