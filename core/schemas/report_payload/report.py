from pydantic import BaseModel


class ReportBase(BaseModel):
    usernames: list[str]

