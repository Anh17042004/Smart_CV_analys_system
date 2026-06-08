from fastapi import APIRouter, Query
from services.tts_service import tts_service

router = APIRouter()

@router.get("", summary="Chuyển đổi văn bản thành giọng nói qua Microsoft Edge TTS")
async def tts_proxy(
    text: str = Query(..., description="Văn bản cần đọc"),
    lang: str = Query("vi", description="Mã ngôn ngữ mặc định (vi hoặc en)"),
    voice: str = Query(None, description="Tên giọng đọc cụ thể của Microsoft Edge (ví dụ: vi-VN-NamMinhNeural)")
):
    """
    Chuyển văn bản thành giọng đọc và trả về stream âm thanh MPEG trực tiếp.
    Nếu không chọn giọng đọc cụ thể, hệ thống sẽ tự động chọn giọng nữ mặc định tương ứng với ngôn ngữ.
    """
    if not voice:
        if lang.lower() == "en" or lang.lower().startswith("en"):
            voice = "en-US-AriaNeural"  # Giọng nữ tiếng Anh mặc định
        else:
            voice = "vi-VN-HoaiMyNeural"  # Giọng nữ tiếng Việt mặc định
            
    return await tts_service.stream_tts(text, voice)
