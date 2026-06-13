from fastapi import APIRouter, File, UploadFile, Query, HTTPException, status
from core.config import settings
from services.stt_service import stt_service
from core.logger import logger

router = APIRouter()

@router.post("/transcribe", summary="Chuyển đổi âm thanh thành văn bản qua Groq Whisper API")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Query("Vietnamese", description="Ngôn ngữ dùng để nhận diện (Vietnamese hoặc English)")
):
    """
    Tải file ghi âm lên, gọi qua dịch vụ Groq Whisper để dịch thành văn bản.
    """
    if not settings.groq_key_list:
         raise HTTPException(
             status_code=status.HTTP_501_NOT_IMPLEMENTED,
             detail="Dịch vụ Whisper chưa được cấu hình. GROQ_API_KEY bị thiếu trên backend."
         )
         
    # Ánh xạ ngôn ngữ sang code tương ứng cho API Whisper
    lang_code = "vi"
    if language.lower() == "english":
        lang_code = "en"
        
    try:
        text = await stt_service.transcribe_audio(file, lang_code)
        return {"text": text}
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi nhận diện giọng nói: {str(exc)}"
        )

@router.get("/config", summary="Kiểm tra cấu hình Whisper STT")
async def get_stt_config():
    """
    Trả về thông tin xem dịch vụ Whisper STT có sẵn sàng hoạt động (đã cấu hình API key) hay không.
    """
    is_available = bool(settings.groq_key_list)
    return {"whisper_available": is_available}
