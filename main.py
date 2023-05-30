import os
import logging
import boto3
from services import api_router, run_twitter_reporting, clean_bucket
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every


app = FastAPI()
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

# connect to s3 bucket
s3 = boto3.client("s3", aws_access_key_id=os.getenv("AWS_ACCESS_KEY"), aws_secret_access_key=os.getenv("AWS_ACCESS_SECRET_KEY"))
bucket = "twitter-users-to-report"
path = "twitter_users_to_report"

origins = [
    'http://localhost:3000',
    'https://localhost:3000',
    'https://reportal-frontend-react.herokuapp.com',
    'http://reportal-frontend-react.herokuapp.com',
    'http://www.r3portal.org',
    'https://www.r3portal.org'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def include_router(api):
    api.include_router(api_router)


include_router(app)


@app.on_event("startup")
@repeat_every(seconds=60 * 60)  # 1 hour
def run_report() -> None:
    # clean_bucket()
    # Retrieve the existing content of the file
    result = s3.get_object(Bucket=bucket, Key=path)
    existing_content = result['Body'].read().decode("utf-8")
    user_list = existing_content.splitlines()

    if len(user_list) > 0:
        logging.info(f'Running Twitter Report for {len(user_list)} user(s)')
        run_twitter_reporting()
        return
    logging.info(f'No report to run')

