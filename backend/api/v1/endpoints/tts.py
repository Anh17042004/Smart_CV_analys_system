from fastapi import APIRouter, Query
from services.tts_service import tts_service

router = APIRouter()

@router.get("", summary="Proxy cho Google Translate TTS")
async def tts_proxy(text: str = Query(...), lang: str = Query("vi")):
    """Proxy âm thanh Google Translate TTS để tránh CORS/Referer block trên trình duyệt."""
    return tts_service.stream_tts(text, lang)
