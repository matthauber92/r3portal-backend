from fastapi import APIRouter
from .reporting import route_twitter
from .reporting import route_youtube


api_router = APIRouter()

api_router.include_router(route_twitter.router, prefix="/twitter", tags=["twitter"])
api_router.include_router(route_youtube.router, prefix="/youtube", tags=["youtube"])
