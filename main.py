from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
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

SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]
# Your Google Sheet ID (get this from the URL of the sheet)
SPREADSHEET_ID = "1uoRqz984lwGvmIE4lV7-8AMk2KFFCbqf-buzN9tz9vU"

# download_json_file()
def init():
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
    return creds

# Define Google Sheets scopes

@app.get("/all_rows")
async def get_all_rows():
    # Authenticate with Google Sheets
    creds = init()
    gc = gspread.authorize(creds)

    # Open the spreadsheet
    spreadsheet = gc.open("attendance_sheet")  # Replace with your sheet name
    worksheet = spreadsheet.sheet1  # or .worksheet("Sheet1")

    # Get all rows as a list of lists
    rows = worksheet.get_all_values()  # [[row1], [row2], [row3], ...]

    return JSONResponse(content={"rows": rows})


@app.post("/add_scholar")
async def add_scholar(request: Request):
    creds = init()
    gc = gspread.authorize(creds)
          
    data = await request.json()
    first_name = str(data.get("first_name"))
    middle_name = str(data.get("middle_name"))
    last_name = str(data.get("last_name"))
    gender = str(data.get("gender"))
    residence = str(data.get("residence"))
    baptism_status = str(data.get("baptism_status"))
    parent_name = str(data.get("parent_name"))
    parent_contact = str(data.get("parent_contact"))
    date_of_birth = str(data.get("dob"))

    sh = gc.open_by_key(SPREADSHEET_ID)
    worksheet = sh.get_worksheet(0)  # First sheet

    columns = worksheet.row_values(1)  # Get header row
    id_column = worksheet.col_values(1)
    if len(id_column) > 1:
        last_id = id_column[-1]
        new_id = int(last_id)+1

    record_dict = [
        int(new_id),
        f'{first_name} {middle_name} {last_name}',
        gender,
        date_of_birth,
        baptism_status,
        parent_name,
        parent_contact,
        residence
    ]

    response = worksheet.append_row(record_dict)

    return response


@app.post("/att_id")
async def mark_attendance(request: Request):
    # Authenticate
    # creds = Credentials.from_service_account_file(
    #     SERVICE_ACCOUNT_FILE, scopes=SCOPES)
     # ✅ Authenticate from environment variable or fallback to file

    creds = init()
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

