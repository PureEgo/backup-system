import os
import io
import json
import pickle
import logging
from typing import Optional, List, Dict
from datetime import datetime

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False

class GoogleDriveHandler:
    
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    
    def __init__(self, config: Dict):
        self.config = config
        self.enabled = config.get('enabled', False)
        self.credentials_file = config.get('credentials_file', './config/google_drive_credentials.json')
        self.token_file = config.get('token_file', './config/google_drive_token.pickle')
        self.folder_id = config.get('folder_id', None)
        self.folder_name = config.get('folder_name', 'Database Backups')
        self.service = None
        self.logger = logging.getLogger(__name__)
        
        if not GOOGLE_DRIVE_AVAILABLE:
            self.logger.warning("Google Drive libraries not installed. Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
            self.enabled = False
        
        if self.enabled:
            self._initialize_service()
    
    def _get_credentials(self) -> Optional[Credentials]:
        creds = None
        
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, 'rb') as token:
                    creds = pickle.load(token)
                self.logger.info("✅ Loaded existing OAuth token")
            except Exception as e:
                self.logger.error(f"Error loading token: {e}")
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    self.logger.info("🔄 Refreshing OAuth token...")
                    creds.refresh(Request())
                    self.logger.info("✅ Token refreshed")
                except Exception as e:
                    self.logger.error(f"❌ Token refresh failed: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(self.credentials_file):
                    self.logger.error(f"❌ Credentials file not found: {self.credentials_file}")
                    return None
                
                try:
                    self.logger.info("🔐 Starting OAuth authorization flow...")
                    self.logger.info("=" * 80)
                    self.logger.info("IMPORTANT: You need to authorize access to Google Drive!")
                    self.logger.info("A browser window will open. Please:")
                    self.logger.info("1. Log in with your Google account")
                    self.logger.info("2. Click 'Allow' to grant access")
                    self.logger.info("3. The authorization will complete automatically")
                    self.logger.info("=" * 80)
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, 
                        self.SCOPES
                    )
                    
                    creds = flow.run_local_server(port=8080)
                    
                    self.logger.info("✅ Authorization successful!")
                    
                except Exception as e:
                    self.logger.error(f"❌ OAuth authorization failed: {e}")
                    return None
            
            try:
                with open(self.token_file, 'wb') as token:
                    pickle.dump(creds, token)
                self.logger.info("✅ Token saved")
            except Exception as e:
                self.logger.error(f"Error saving token: {e}")
        
        return creds
    
    def _initialize_service(self) -> bool:
        try:
            credentials = self._get_credentials()
            
            if not credentials:
                self.logger.error("❌ Failed to get credentials")
                self.enabled = False
                return False
            
            self.service = build('drive', 'v3', credentials=credentials)
            
            if not self.folder_id:
                self.folder_id = self._get_or_create_folder(self.folder_name)
                
                if self.folder_id:
                    self._save_folder_id(self.folder_id)
            
            self.logger.info(f"✅ Google Drive initialized - Folder: {self.folder_name} ({self.folder_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Google Drive: {e}")
            self.enabled = False
            return False
    
    def _save_folder_id(self, folder_id: str):
        try:
            config_path = self.credentials_file.replace('google_drive_credentials.json', 'config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    full_config = json.load(f)
                
                if 'google_drive' in full_config:
                    full_config['google_drive']['folder_id'] = folder_id
                    
                    with open(config_path, 'w') as f:
                        json.dump(full_config, f, indent=4)
                    
                    self.logger.info(f"✅ Saved folder_id to config: {folder_id}")
        except Exception as e:
            self.logger.warning(f"Could not save folder_id to config: {e}")
    
    def _get_or_create_folder(self, folder_name: str, parent_id: str = None) -> Optional[str]:
        try:
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            if parent_id:
                query += f" and '{parent_id}' in parents"
            
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                folder_id = files[0]['id']
                self.logger.info(f"📁 Found existing folder: {folder_name} ({folder_id})")
                return folder_id
            
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_id:
                file_metadata['parents'] = [parent_id]
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            folder_id = folder.get('id')
            self.logger.info(f"📁 Created new folder: {folder_name} ({folder_id})")
            return folder_id
            
        except Exception as e:
            self.logger.error(f"❌ Error getting/creating folder: {e}")
            return None
    
    def upload_backup(self, backup_file: str) -> bool:
        if not self.enabled:
            self.logger.warning("Google Drive is disabled")
            return False
        
        try:
            if not os.path.exists(backup_file):
                self.logger.error(f"Backup file not found: {backup_file}")
                return False
            
            filename = os.path.basename(backup_file)
            
            existing_file_id = self._find_file(filename)
            
            file_metadata = {
                'name': filename,
                'parents': [self.folder_id]
            }
            
            media = MediaFileUpload(
                backup_file,
                mimetype='application/gzip',
                resumable=True
            )
            
            if existing_file_id:
                file = self.service.files().update(
                    fileId=existing_file_id,
                    media_body=media
                ).execute()
                self.logger.info(f"📤 Updated file in Google Drive: {filename}")
            else:
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, name, size, createdTime'
                ).execute()
                self.logger.info(f"📤 Uploaded to Google Drive: {filename} ({file.get('id')})")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error uploading to Google Drive: {e}")
            return False
    
    def _find_file(self, filename: str) -> Optional[str]:
        try:
            query = f"name='{filename}' and '{self.folder_id}' in parents and trashed=false"
            
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                return files[0]['id']
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding file: {e}")
            return None
    
    def list_backups(self) -> List[Dict]:
        if not self.enabled:
            return []
        
        try:
            query = f"'{self.folder_id}' in parents and trashed=false"
            
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, size, createdTime, modifiedTime)',
                orderBy='createdTime desc'
            ).execute()
            
            files = results.get('files', [])
            
            backups = []
            for file in files:
                backups.append({
                    'id': file['id'],
                    'name': file['name'],
                    'size': int(file.get('size', 0)),
                    'created': file.get('createdTime'),
                    'modified': file.get('modifiedTime')
                })
            
            return backups
            
        except Exception as e:
            self.logger.error(f"Error listing Google Drive backups: {e}")
            return []
    
    def download_backup(self, file_id: str, destination: str) -> bool:
        if not self.enabled:
            return False
        
        try:
            request = self.service.files().get_media(fileId=file_id)
            
            with io.FileIO(destination, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        self.logger.info(f"Download progress: {progress}%")
            
            self.logger.info(f"✅ Downloaded from Google Drive: {destination}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error downloading from Google Drive: {e}")
            return False
    
    def delete_backup(self, file_id: str) -> bool:
        if not self.enabled:
            return False
        
        try:
            self.service.files().delete(fileId=file_id).execute()
            self.logger.info(f"🗑️ Deleted from Google Drive: {file_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error deleting from Google Drive: {e}")
            return False
    
    def cleanup_old_backups(self, keep_count: int = 10) -> int:
        if not self.enabled:
            return 0
        
        try:
            backups = self.list_backups()
            
            if len(backups) <= keep_count:
                return 0
            
            backups_to_delete = backups[keep_count:]
            deleted_count = 0
            
            for backup in backups_to_delete:
                if self.delete_backup(backup['id']):
                    deleted_count += 1
            
            self.logger.info(f"🗑️ Cleaned up {deleted_count} old backups from Google Drive")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old backups: {e}")
            return 0
    
    def test_connection(self) -> bool:
        if not self.enabled:
            return False
        
        try:
            folder = self.service.files().get(
                fileId=self.folder_id,
                fields='id, name'
            ).execute()
            
            self.logger.info(f"✅ Google Drive connection test successful: {folder['name']}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Google Drive connection test failed: {e}")
            return False
    
    def get_storage_quota(self) -> Dict:
        if not self.enabled:
            return {}
        
        try:
            about = self.service.about().get(fields='storageQuota').execute()
            quota = about.get('storageQuota', {})
            
            limit = int(quota.get('limit', 0))
            usage = int(quota.get('usage', 0))
            
            return {
                'total_gb': limit / (1024 ** 3),
                'used_gb': usage / (1024 ** 3),
                'available_gb': (limit - usage) / (1024 ** 3),
                'usage_percent': (usage / limit * 100) if limit > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting storage quota: {e}")
            return {}