import schedule
import time
import logging
from datetime import datetime
from typing import Callable, Dict
import threading

class BackupScheduler:
    
    def __init__(self, config: Dict, backup_function: Callable):
        self.config = config
        self.backup_function = backup_function
        self.enabled = config.get('enabled', True)
        self.backup_time = config.get('backup_time', '02:00')
        self.interval = config.get('backup_interval', 'daily')
        self.timezone = config.get('timezone', 'UTC')
        self.running = False
        self.thread = None
        self.logger = logging.getLogger(__name__)
    
    def schedule_backups(self) -> None:
        schedule.clear()
        
        if not self.enabled:
            self.logger.info("Scheduler is disabled")
            return
        
        if self.interval == 'daily':
            schedule.every().day.at(self.backup_time).do(self._run_backup)
            self.logger.info(f"Scheduled daily backup at {self.backup_time}")
            
        elif self.interval == 'hourly':
            schedule.every().hour.do(self._run_backup)
            self.logger.info("Scheduled hourly backups")
            
        elif self.interval.endswith('hours'):
            try:
                hours = int(self.interval.replace('hours', ''))
                schedule.every(hours).hours.do(self._run_backup)
                self.logger.info(f"Scheduled backup every {hours} hours")
            except ValueError:
                self.logger.error(f"Invalid interval format: {self.interval}")
                
        elif self.interval == 'weekly':
            schedule.every().sunday.at(self.backup_time).do(self._run_backup)
            self.logger.info(f"Scheduled weekly backup on Sunday at {self.backup_time}")
            
        else:
            self.logger.error(f"Unknown interval: {self.interval}")
    
    def _run_backup(self) -> None:
        try:
            self.logger.info("Scheduled backup started")
            self.backup_function()
            self.logger.info("Scheduled backup completed")
        except Exception as e:
            self.logger.error(f"Error during scheduled backup: {e}")
    
    def start(self) -> None:
        if self.running:
            self.logger.warning("Scheduler is already running")
            return
        
        self.schedule_backups()
        self.running = True
        
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        
        self.logger.info("Scheduler started")
    
    def _run_scheduler(self) -> None:
        while self.running:
            schedule.run_pending()
            time.sleep(60)
    
    def stop(self) -> None:
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        
        schedule.clear()
        self.logger.info("Scheduler stopped")
    
    def get_next_run(self) -> str:
        jobs = schedule.get_jobs()
        if not jobs:
            return "No jobs scheduled"
        
        next_run = min(job.next_run for job in jobs)
        return next_run.strftime('%Y-%m-%d %H:%M:%S')
    
    def run_now(self) -> None:
        self.logger.info("Manual backup triggered")
        self._run_backup()

class CronScheduler:
    
    @staticmethod
    def create_cron_job(
        script_path: str,
        schedule_time: str = "0 2 * * *",
        description: str = "Automated Database Backup"
    ) -> bool:
        try:
            from crontab import CronTab
            
            cron = CronTab(user=True)
            
            cron.remove_all(command=script_path)
            
            job = cron.new(command=f'python3 {script_path}', comment=description)
            job.setall(schedule_time)
            
            cron.write()
            
            logging.info(f"Cron job created: {schedule_time} - {script_path}")
            return True
            
        except ImportError:
            logging.error("python-crontab not installed. Run: pip install python-crontab")
            return False
        except Exception as e:
            logging.error(f"Error creating cron job: {e}")
            return False
    
    @staticmethod
    def remove_cron_job(script_path: str) -> bool:
        try:
            from crontab import CronTab
            
            cron = CronTab(user=True)
            removed = cron.remove_all(command=script_path)
            cron.write()
            
            logging.info(f"Removed {removed} cron job(s)")
            return True
            
        except Exception as e:
            logging.error(f"Error removing cron job: {e}")
            return False

class WindowsScheduler:
    
    @staticmethod
    def create_scheduled_task(
        task_name: str,
        script_path: str,
        schedule_time: str = "02:00",
        python_path: str = "python"
    ) -> bool:
        try:
            import subprocess
            
            subprocess.run(
                ['schtasks', '/Delete', '/TN', task_name, '/F'],
                capture_output=True
            )
            
            command = [
                'schtasks', '/Create',
                '/TN', task_name,
                '/TR', f'{python_path} {script_path}',
                '/SC', 'DAILY',
                '/ST', schedule_time,
                '/F'
            ]
            
            result = subprocess.run(command, capture_output=True, text=True)
            
            if result.returncode == 0:
                logging.info(f"Scheduled task created: {task_name}")
                return True
            else:
                logging.error(f"Error creating scheduled task: {result.stderr}")
                return False
                
        except Exception as e:
            logging.error(f"Error creating Windows scheduled task: {e}")
            return False
    
    @staticmethod
    def remove_scheduled_task(task_name: str) -> bool:
        try:
            import subprocess
            
            result = subprocess.run(
                ['schtasks', '/Delete', '/TN', task_name, '/F'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logging.info(f"Scheduled task removed: {task_name}")
                return True
            else:
                logging.error(f"Error removing scheduled task: {result.stderr}")
                return False
                
        except Exception as e:
            logging.error(f"Error removing Windows scheduled task: {e}")
            return False
