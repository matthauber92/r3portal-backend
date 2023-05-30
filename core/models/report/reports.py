from sqlalchemy import Column, Integer, String
from core.models.base import Base

class Reports(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    twitter_report_count = Column(Integer, index=False)
    twitter_users_count = Column(Integer, index=False)
    twitter_submitted_reports_count = Column(Integer, index=False)
    youtube_report_count = Column(Integer, index=False)
    youtube_users_count = Column(Integer, index=False)
    youtube_submitted_reports_count = Column(Integer, index=False)

