from pydantic import BaseModel


class YoutubeReportBase(BaseModel):
    video_id: str
    reason_id: str
    comments: str

