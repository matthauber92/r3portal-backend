import os
import requests
from dotenv import load_dotenv, find_dotenv
from core.models import Reports
from core.schemas.report_payload import ReportBase
from db import get_db
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
# from google.oauth2.credentials import Credentials
# from googleapiclient.discovery import build


load_dotenv(find_dotenv())

router = APIRouter()

# Create a YouTube API client
api_key = os.getenv("YOUTUBE_API_KEY")
# Create OAuth 2.0 credentials using your client ID and secret
# creds = Credentials.from_authorized_user_info(info={"client_id": os.getenv("YOUTUBE_CLIENT_ID"), "client_secret": os.getenv("YOUTUBE_CLIENT_SECRET")})
# print(creds)
# youtube = build("youtube", "v3", credentials=creds)

@router.get('/get_youtube_report')
def get_report(_db: Session = Depends(get_db)):
    report = _db.query(Reports).filter(Reports.id == 1).first()
    if report is None:
        return {"youtube_report_count": 0, "youtube_users_count": 0, "youtube_submitted_reports_count": 0}

    returned_report = Reports()
    returned_report.youtube_report_count = report.youtube_report_count
    returned_report.youtube_users_count = report.youtube_users_count
    returned_report.youtube_submitted_reports_count = report.youtube_submitted_reports_count

    return returned_report


# @router.get("/get_report_reason")
# def get_report_reason():
#     try:
#         # Call the video abuse report reasons endpoint
#         response = youtube.videoAbuseReportReasons().list(part="snippet").execute()
#
#         # Print the list of video abuse report reasons
#         reasons = response["items"]
#         for reason in reasons:
#             print(reason["snippet"]["label"])
#
#     except HTTPException as e:
#         print(f"Failed to retrieve report reasons: {e}")


@router.post("/create_youtube_report")
def create_youtube_report(report: ReportBase, _db: Session = Depends(get_db)):
    # authorize the API with your credentials
    try:
       data = search_videos(report.usernames)
       return data

    except HTTPException as e:
        print(f"Failed to authenticate: {e}")

# function to search for videos by a specific username
def search_videos(username):
    # API endpoint
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={username}&type=video&key={os.getenv('YOUTUBE_API_KEY')}"

    # make GET request to the API
    response = requests.get(url)

    # parse response as JSON
    data = response.json()

    return data["items"]
    # print the title and link of each video
    # for item in data["items"]:
    #     print(item["snippet"]["title"])
    #     print("https://www.youtube.com/watch?v=" + item["id"]["videoId"])