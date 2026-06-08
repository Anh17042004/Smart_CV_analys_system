from fastapi import APIRouter
from api.v1.endpoints import auth
from api.v1.endpoints import cv_analysis
from api.v1.endpoints import job_search
from api.v1.endpoints import interview
from api.v1.endpoints import tts

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(cv_analysis.router, prefix="/cv", tags=["CV Analysis"])
api_router.include_router(job_search.router, prefix="/jobs", tags=["Jobs"])
api_router.include_router(interview.router, prefix="/interview", tags=["Interview"])
api_router.include_router(tts.router, prefix="/tts", tags=["TTS"])