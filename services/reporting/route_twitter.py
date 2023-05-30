import os
import tweepy
import logging
import boto3
from datetime import date
from dotenv import load_dotenv, find_dotenv
from core.models import Reports
from core.schemas.report_payload import ReportBase
from db import get_db
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

load_dotenv(find_dotenv())
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

router = APIRouter()

# connect to s3 bucket
s3 = boto3.client("s3", aws_access_key_id=os.getenv("AWS_ACCESS_KEY"), aws_secret_access_key=os.getenv("AWS_ACCESS_SECRET_KEY"))
bucket = "twitter-users-to-report"
path = "twitter_users_to_report"

app_key = os.getenv("API_KEY")
app_secret = os.getenv("API_SECRET")
access_token = os.getenv("ACCESS_TOKEN")
access_secret = os.getenv("ACCESS_TOKEN_SECRET")

auth = tweepy.OAuthHandler(app_key, app_secret)
auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth)

@router.get('/get_s3_bucket')
def get_s3_bucket():
    # Retrieve the existing content of the file
    result = s3.get_object(Bucket=bucket, Key=path)
    existing_content = result['Body'].read().decode("utf-8")
    user_list = list(reversed(existing_content.splitlines()))
    return user_list

def clean_bucket():
    # Retrieve the existing content of the file
    result = s3.get_object(Bucket=bucket, Key=path)
    existing_content = result['Body'].read().decode("utf-8")
    user_list = existing_content.splitlines()

    for username in user_list:
        if username == '@janiecountry@Sammy_rockchick':
            # create array of update user list for s3
            filter_content = [s for s in user_list if s != '@janiecountry@Sammy_rockchick']
            content = "\n".join(filter_content)

            # Write the contents to the file
            s3.put_object(Bucket=bucket, Key=path, Body=content)
            return

@router.get('/get_user_by_name')
def get_user_by_name(username: str):
    try:
        user = api.get_user(screen_name=username)
        return user
    except tweepy.TweepyException as e:
        logging.error(str(e))

@router.get('/get_twitter_report')
def get_twitter_report(_db: Session = Depends(get_db)):
    report = _db.query(Reports).filter(Reports.id == 1).first()
    if report is None:
        return {"twitter_report_count": 0, "twitter_users_count": 0, "twitter_submitted_reports": 0}

    returned_report = Reports()
    returned_report.twitter_report_count = report.twitter_report_count
    returned_report.twitter_users_count = report.twitter_users_count
    returned_report.twitter_submitted_reports_count = report.twitter_submitted_reports_count

    return returned_report


@router.post("/create_twitter_report")
def create_twitter_report(report: ReportBase, _db: Session = Depends(get_db)):
    # authorize the API with your credentials
    try:
        result = s3.get_object(Bucket=bucket, Key=path)
        existing_content = result['Body'].read().decode("utf-8")
        user_list = list(reversed(existing_content.splitlines()))

        app_report = _db.query(Reports).filter(Reports.id == 1).first()

        tweet_count = 0
        users_reported_count = 0

        with open('keywords') as f:
            keywords = [line.rstrip('\n') for line in f]
            logging.info(f"REPORT USERS {report.usernames}")
            for username in report.usernames:
                if username in user_list:
                    continue

                query = ' OR '.join(keywords)
                query = f"from:{username}"

                try:
                    tweets = tweepy.Cursor(api.search_tweets, q=query, tweet_mode='extended').items(50)
                    logging.info(f"TWEETS {tweets}")

                    been_reported = False
                    for tweet in tweets:
                        if any(keyword in tweet.full_text for keyword in keywords):
                            try:
                                tweet_count += 1

                                if been_reported is False:
                                    been_reported = True
                                    users_reported_count += 1
                                    # write user to text file that needs to be reported to s3 bucket
                                    # Retrieve the existing content of the file
                                    result = s3.get_object(Bucket=bucket, Key=path)
                                    existing_content = result['Body'].read().decode("utf-8")
                                    new_content = f'{username}\n'
                                    updated_content = existing_content + new_content

                                    s3.put_object(Bucket=bucket, Key=path, Body=updated_content)

                            except tweepy.TweepyException:
                                raise HTTPException(status_code=429, detail=f"You are over the limit for reports. {users_reported_count} user(s) and {tweet_count} tweet(s) were reported. Please try again later.")
                except tweepy.TweepyException:
                   raise HTTPException(status_code=429, detail=f"You are over the limit for reports. {users_reported_count} user(s) and {tweet_count} tweet(s) were reported. Please try again later.")

        app_report.twitter_report_count += tweet_count
        app_report.twitter_users_count += users_reported_count
        app_report.twitter_submitted_reports_count += 1
        _db.add(app_report)
        _db.commit()
        _db.refresh(app_report)
        return {f"Successfully reported {users_reported_count} user(s) and {tweet_count} tweet(s) due to targeted insults"}
    except tweepy.TweepyException as e:
        logging.info(f"Failed to authenticate: {e}")


def run_twitter_reporting():
    # authorize the API with your credentials
    try:
        logging.info("Begin running report")
        # Retrieve the existing content of the file
        result = s3.get_object(Bucket=bucket, Key=path)
        existing_content = result['Body'].read().decode("utf-8")
        user_list = existing_content.splitlines()
        logging.info("Get users from s3 bucket")

        tweet_count = 0
        with open('keywords') as f:
            keywords = [line.rstrip('\n') for line in f]
            for username in user_list:
                query = ' OR '.join(keywords)
                query = f"from:{username}"
                logging.info(f"Looking for {username}")

                try:
                    tweets = tweepy.Cursor(api.search_tweets, q=query, tweet_mode='extended').items(50)
                    logging.info(f"ALL TWEETS {tweets}")
                    been_reported = False
                    logging.info("Searched users tweets")

                    for tweet in tweets:
                        if any(keyword in tweet.full_text.lower() for keyword in keywords):
                            try:
                                logging.info(f"LETS REPORT {username}")

                                api.report_spam(user_id=tweet.user.id)
                                tweet_count +=  1

                                if been_reported is False:
                                    been_reported = True
                                    # recycle user if already reports
                                    recycle_user(username)

                            except tweepy.TweepyException:
                                logging.info(f"{date.today()} You are over the limit for reports.")
                                raise HTTPException(status_code=429, detail=f"You are over the limit for reports.")
                except tweepy.TweepyException:
                    logging.info(f"{date.today()} You are over the limit for reports. {tweet_count} tweet(s) were reported.")
                    raise HTTPException(status_code=429, detail=f"You are over the limit for reports. {tweet_count} tweet(s) were reported.")

        logging.info(f'Finished running report at {date.today()}')
        return {f"Successfully reported {tweet_count} tweet(s) due to targeted insults"}
    except tweepy.TweepyException as e:
        logging.info(f"Failed to authenticate: {e}")


def recycle_user(user):
    # Retrieve the existing content of the file
    result = s3.get_object(Bucket=bucket, Key=path)
    existing_content = result['Body'].read().decode("utf-8")
    user_list = existing_content.splitlines()

    for username in user_list:
        if username == user:
            # create array of update user list for s3
            filter_content = [s for s in user_list if s != user]
            content = "\n".join(filter_content)
            new_content =  content + f"\n{user}"

            # Write the contents to the file
            s3.put_object(Bucket=bucket, Key=path, Body=new_content)
            logging.info(f"Recycled USER{user}")
            return

