from google.oauth2 import service_account
from googleapiclient.discovery import build





SERVICE_ACCOUNT_EMAIL = "drive-devh@devh-421310.iam.gserviceaccount.com"
SERVICE_ACCOUNT_FILE = 'storage/service.json'
FOLDER_ID = '1p90vuxE8jp7mBwW63qj7rIwpiCuaYMEP'
SCOPES = ['https://www.googleapis.com/auth/drive']

def authenticate():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, subject=SERVICE_ACCOUNT_EMAIL, scopes=SCOPES)
    drive_service = build('drive', 'v3', credentials=credentials)
    return drive_service    