import os.path
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.file']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'
DB_FILE = 'medicines.json'
MIME_TYPE = 'application/json'

class DriveSync:
    def __init__(self):
        self.creds = None
        self.service = None
        self.authenticate()

    def authenticate(self):
        if os.path.exists(TOKEN_FILE):
            self.creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not os.path.exists(CREDENTIALS_FILE):
                    print(f"Warning: {CREDENTIALS_FILE} not found. Drive sync disabled.")
                    return
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            with open(TOKEN_FILE, 'w') as token:
                token.write(self.creds.to_json())

        self.service = build('drive', 'v3', credentials=self.creds)

    def _find_file(self, name):
        if not self.service: return None
        results = self.service.files().list(
            q=f"name='{name}' and trashed=false",
            pageSize=1, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])
        if not items:
            return None
        return items[0]['id']

    def upload_file(self):
        if not self.service: return
        file_id = self._find_file(DB_FILE)
        file_metadata = {'name': DB_FILE}
        media = MediaFileUpload(DB_FILE, mimetype=MIME_TYPE)

        if file_id:
            # Update existing file
            self.service.files().update(
                fileId=file_id,
                media_body=media).execute()
            print(f"Updated {DB_FILE} on Drive.")
        else:
            # Create new file
            self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id').execute()
            print(f"Created {DB_FILE} on Drive.")

    def download_file(self):
        if not self.service: return
        file_id = self._find_file(DB_FILE)
        if not file_id:
            print(f"{DB_FILE} not found on Drive. Using local version.")
            return

        request = self.service.files().get_media(fileId=file_id)
        fh = io.FileIO(DB_FILE, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        print(f"Downloaded {DB_FILE} from Drive.")

drive_sync = DriveSync()
