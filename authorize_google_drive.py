import pickle
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def authorize():
    print("=" * 80)
    print("GOOGLE DRIVE OAUTH AUTHORIZATION")
    print("=" * 80)
    print()
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            './config/google_drive_credentials.json',
            SCOPES
        )
        
        flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
        
        auth_url, _ = flow.authorization_url(prompt='consent')
        
        print("STEP 1: Open this URL in your browser:")
        print()
        print(auth_url)
        print()
        print("STEP 2: Log in with your Google account and click 'Allow'")
        print()
        print("STEP 3: Copy the authorization code and paste it below")
        print()
        
        code = input("Enter authorization code: ").strip()
        
        if not code:
            print("❌ No code entered!")
            return False
        
        print()
        print("🔄 Exchanging code for token...")
        flow.fetch_token(code=code)
        
        with open('./config/google_drive_token.pickle', 'wb') as token:
            pickle.dump(flow.credentials, token)
        
        print("✅ Authorization successful!")
        print("✅ Token saved to: ./config/google_drive_token.pickle")
        print()
        print("You can now use Google Drive backups!")
        print("Restart the backup system: docker-compose restart backup_system_app")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"❌ Authorization failed: {e}")
        return False

if __name__ == "__main__":
    authorize()