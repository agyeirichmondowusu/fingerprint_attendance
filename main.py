from fastapi import FastAPI, Request
import pandas as pd
import datetime
import gspread
from google.oauth2.service_account import Credentials
import uvicorn
import os
from fastapi import FastAPI, Request
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import requests
import json

app = FastAPI()

# # Step 1: Download service account key from Dropbox
# dropbox_url = 'https://www.dropbox.com/scl/fi/m0rzm0gchg3hlbqnd2wjt/credentials.json?rlkey=p18jdyr8ldqw3ir4cr02zbavt&st=hd57u8oq&dl=1'
# response = requests.get(dropbox_url)
# response.raise_for_status()
# service_account_info = response.json()

# # Step 2: Authenticate using service account
# SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
# credentials = service_account.Credentials.from_service_account_info(
#     service_account_info, scopes=SCOPES)

# # Step 3: Download file from Google Drive
# def download_json_file():
#     file_id = '1zNhAOzCnq4I9CccyFz9tnPdgtz_MH4VP'
#     service = build('drive', 'v3', credentials=credentials)
#     request = service.files().get_media(fileId=file_id)
#     fh = io.FileIO(SERVICE_ACCOUNT_FILE, 'wb')
#     downloader = MediaIoBaseDownload(fh, request)

#     done = False
#     while not done:
#         status, done = downloader.next_chunk()
#         print(f"Download progress: {int(status.progress() * 100)}%")

#     print(f"Downloaded file saved to {SERVICE_ACCOUNT_FILE}")

# download_json_file()


# Define Google Sheets scopes
SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]

# Path to your service account credentials
SERVICE_ACCOUNT_FILE = "credentials.json"

# Your Google Sheet ID (get this from the URL of the sheet)
SPREADSHEET_ID = "1uoRqz984lwGvmIE4lV7-8AMk2KFFCbqf-buzN9tz9vU"


@app.post("/att_id")
async def mark_attendance(request: Request):
    # Authenticate
    # creds = Credentials.from_service_account_file(
    #     SERVICE_ACCOUNT_FILE, scopes=SCOPES)
     # ✅ Authenticate from environment variable or fallback to file
    if "GOOGLE_CREDENTIALS" in os.environ:
        creds_info = json.loads(os.environ["GOOGLE_CREDENTIALS"])
        creds = service_account.Credentials.from_service_account_info(
            creds_info, scopes=SCOPES
        )
    else:
        # Fallback if you're testing locally and have credentials.json
        creds = service_account.Credentials.from_service_account_file(
            "credentials.json", scopes=SCOPES
        )
    gc = gspread.authorize(creds)
    data = await request.json()
    student_id = str(data.get("id"))
    # student_id = "15"
    # Open the Google Sheet
    sh = gc.open_by_key(SPREADSHEET_ID)
    worksheet = sh.get_worksheet(0)  # First sheet

    # Get values as DataFrame
    records = worksheet.get_all_records()
    df = pd.DataFrame(records)

    # Convert ID to int if needed
    df['ID'] = df['ID'].astype(str)

    # Generate today's date as column name
    today = datetime.datetime.now().strftime("%d/%m/%Y")
    now_time = datetime.datetime.now().strftime("%H:%M:%S")

    if today not in df.columns:
        df[today] = ""

    if student_id in df['ID'].values:
        df.loc[df['ID'] == student_id, today] = now_time
    else:
        print("❌ ID not found in sheet.")

    # Clear existing sheet
    worksheet.clear()

    # Re-upload with updated data
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())

    return {"status": f"✅ Attendance marked for ID {student_id}", "time": now_time}



# if __name__=='__main__':
#     if os.path.exists(SERVICE_ACCOUNT_FILE):
#         print("Exists")
#     else:
#         download_json_file()

#     uvicorn.run(app, host="0.0.0.0", port=8580)
