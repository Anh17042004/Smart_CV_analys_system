from groq import AsyncGroq
from fastapi import UploadFile
from core.config import settings
from core.logger import logger

class STTService:
    def __init__(self):
        self._client = None

    @property
    def client(self) -> AsyncGroq:
        if self._client is None:
            if not settings.GROQ_API_KEY:
                raise ValueError("Groq API Key is not configured on the server.")
            self._client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        return self._client

    async def transcribe_audio(self, file: UploadFile, language_code: str) -> str:
        """
        Gửi file audio đã tải lên tới Groq Cloud Whisper API qua SDK chính thức.
        """
        if not settings.GROQ_API_KEY:
            logger.error("❌ GROQ_API_KEY chưa được cấu hình trên backend.")
            raise ValueError("Groq API Key is not configured on the server.")
        
        try:
            # Đọc nội dung file audio
            file_content = await file.read()
            filename = file.filename or "speech.webm"
            
            logger.info(f"🎙️ Đang gửi file audio ({len(file_content)} bytes, lang={language_code}) tới Groq Whisper SDK...")
            
            # Sử dụng AsyncGroq client
            transcription = await self.client.audio.transcriptions.create(
                file=(filename, file_content),
                model="whisper-large-v3",
                language=language_code if language_code else None,
                response_format="json"
            )
            
            logger.info("✅ Nhận diện giọng nói thành công từ Groq SDK.")
            return transcription.text
                
        except Exception as e:
            logger.error(f"❌ Gặp lỗi khi xử lý Whisper STT qua SDK: {e}")
            raise e

stt_service = STTService()
