import os
import json
import smtplib
import logging
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Optional

class NotificationService:
    
    def __init__(self, config: Dict, config_path: str = "./config/config.json"):
        self.config = config
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
        
        self._load_saved_config()
    
    def _load_saved_config(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    full_config = json.load(f)
                
                if 'notifications' in full_config:
                    saved = full_config['notifications']
                    
                    if 'email' in saved:
                        if 'email' not in self.config:
                            self.config['email'] = {}
                        self.config['email'].update(saved['email'])
                    
                    if 'telegram' in saved:
                        if 'telegram' not in self.config:
                            self.config['telegram'] = {}
                        self.config['telegram'].update(saved['telegram'])
                    
                    self.logger.info("✅ Notifications config loaded from file")
        except Exception as e:
            self.logger.error(f"❌ Error loading notifications config: {e}")
    
    def save_config(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    full_config = json.load(f)
            else:
                full_config = {}
            
            full_config['notifications'] = self.config
            
            with open(self.config_path, 'w') as f:
                json.dump(full_config, f, indent=4)
            
            self.logger.info("✅ Notifications config saved to file")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error saving notifications config: {e}")
            return False
    
    def update_config(self, new_config: Dict) -> bool:
        try:
            if 'email' in new_config:
                if 'email' not in self.config:
                    self.config['email'] = {}
                self.config['email'].update(new_config['email'])
            
            if 'telegram' in new_config:
                if 'telegram' not in self.config:
                    self.config['telegram'] = {}
                self.config['telegram'].update(new_config['telegram'])
            
            return self.save_config()
        except Exception as e:
            self.logger.error(f"Error updating config: {e}")
            return False
    
    def send_backup_notification(
        self,
        success: bool,
        database: str,
        backup_file: str = None,
        error_message: str = None,
        details: Dict = None
    ) -> None:
        if success:
            subject = f"✅ Backup Successful: {database}"
            message = self._format_success_message(database, backup_file, details)
        else:
            subject = f"❌ Backup Failed: {database}"
            message = self._format_failure_message(database, error_message, details)
        
        if self.config.get('email', {}).get('enabled'):
            notify_condition = (
                success and self.config['email'].get('notify_on_success', True)
            ) or (
                not success and self.config['email'].get('notify_on_failure', True)
            )
            
            if notify_condition:
                self.send_email(subject, message)
        
        if self.config.get('telegram', {}).get('enabled'):
            notify_condition = (
                success and self.config['telegram'].get('notify_on_success', True)
            ) or (
                not success and self.config['telegram'].get('notify_on_failure', True)
            )
            
            if notify_condition:
                self.send_telegram(message)
    
    def _format_success_message(
        self,
        database: str,
        backup_file: str,
        details: Dict = None
    ) -> str:
        import os
        
        message = f"✅ Backup Completed Successfully\n\n"
        message += f"📊 Database: {database}\n"
        message += f"🕒 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        if backup_file:
            filename = os.path.basename(backup_file)
            message += f"📦 File: {filename}\n"
            
            if os.path.exists(backup_file):
                size_mb = os.path.getsize(backup_file) / (1024 * 1024)
                message += f"💾 Size: {size_mb:.2f} MB\n"
        
        if details:
            if 'duration' in details:
                message += f"⏱️ Duration: {details['duration']:.2f} seconds\n"
            if 'storage' in details:
                message += f"\n📍 Storage Locations:\n"
                for location, status in details['storage'].items():
                    status_icon = "✅" if status else "❌"
                    message += f"  {status_icon} {location.upper()}\n"
        
        message += f"\n🚀 Backup system is running smoothly!"
        
        return message
    
    def _format_failure_message(
        self,
        database: str,
        error_message: str,
        details: Dict = None
    ) -> str:
        message = f"❌ Backup Failed\n\n"
        message += f"📊 Database: {database}\n"
        message += f"🕒 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        if error_message:
            message += f"\n⚠️ Error:\n{error_message}\n"
        
        if details:
            message += f"\n📋 Additional Details:\n"
            for key, value in details.items():
                message += f"  • {key}: {value}\n"
        
        message += f"\n🔍 Please check the logs for more information."
        
        return message
    
    def send_email(self, subject: str, body: str, html: bool = False) -> bool:
        email_config = self.config.get('email', {})
        
        try:
            smtp_server = email_config.get('smtp_server')
            smtp_port = email_config.get('smtp_port', 587)
            sender = email_config.get('sender')
            password = email_config.get('password')
            recipients = email_config.get('recipients', [])
            use_tls = email_config.get('use_tls', True)
            
            if not all([smtp_server, sender, password, recipients]):
                self.logger.error("Email configuration incomplete")
                return False
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = sender
            msg['To'] = ', '.join(recipients)
            
            if html:
                msg.attach(MIMEText(body, 'html'))
            else:
                plain_body = body.replace('**', '').replace('*', '')
                msg.attach(MIMEText(plain_body, 'plain'))
            
            self.logger.info(f"Sending email to {len(recipients)} recipient(s)")
            
            if use_tls:
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            
            server.login(sender, password)
            server.send_message(msg)
            server.quit()
            
            self.logger.info("📧 Email sent successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending email: {e}")
            return False
    
    def send_telegram(self, message: str) -> bool:
        telegram_config = self.config.get('telegram', {})
        
        try:
            bot_token = telegram_config.get('bot_token')
            chat_ids = telegram_config.get('chat_ids', [])
            
            if not bot_token or not chat_ids:
                self.logger.error("Telegram configuration incomplete")
                return False
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            
            success_count = 0
            
            for chat_id in chat_ids:
                payload = {
                    'chat_id': chat_id,
                    'text': message
                }
                
                response = requests.post(url, json=payload, timeout=10)
                
                if response.status_code == 200:
                    success_count += 1
                else:
                    self.logger.error(f"Telegram API error for chat {chat_id}: {response.text}")
            
            if success_count > 0:
                self.logger.info(f"💬 Telegram message sent to {success_count} chat(s)")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending Telegram message: {e}")
            return False
    
    def test_email_connection(self) -> bool:
        email_config = self.config.get('email', {})
        
        try:
            smtp_server = email_config.get('smtp_server')
            smtp_port = email_config.get('smtp_port', 587)
            sender = email_config.get('sender')
            password = email_config.get('password')
            use_tls = email_config.get('use_tls', True)
            
            if use_tls:
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            
            server.login(sender, password)
            server.quit()
            
            self.logger.info("Email connection test successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Email connection test failed: {e}")
            return False
    
    def test_telegram_connection(self) -> bool:
        telegram_config = self.config.get('telegram', {})
        
        try:
            bot_token = telegram_config.get('bot_token')
            
            if not bot_token:
                return False
            
            url = f"https://api.telegram.org/bot{bot_token}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    bot_name = data.get('result', {}).get('username')
                    self.logger.info(f"Telegram connection test successful: @{bot_name}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Telegram connection test failed: {e}")
            return False
    
    def send_test_notification(self) -> Dict[str, bool]:
        results = {}
        
        test_message = f"🧪 Test Notification\n\n"
        test_message += f"This is a test message from the backup system.\n"
        test_message += f"🕒 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        test_message += f"\n✅ If you receive this message, notifications are working correctly!"
        
        if self.config.get('email', {}).get('enabled'):
            results['email'] = self.send_email("🧪 Test Notification - Backup System", test_message)
        
        if self.config.get('telegram', {}).get('enabled'):
            results['telegram'] = self.send_telegram(test_message)
        
        return results