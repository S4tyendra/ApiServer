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


def create_folder_and_get_id(folder_name, parent_folder_id):
    drive_service = authenticate()
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_folder_id]
    }
    folder = drive_service.files().create(body=file_metadata,
                                          fields='id').execute()
    folder_id = folder.get('id')

    return folder_id
