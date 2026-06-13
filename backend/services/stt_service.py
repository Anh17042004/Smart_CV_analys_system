from groq import AsyncGroq
from fastapi import UploadFile
from core.config import settings
from core.logger import logger
from core.key_rotator import KeyRotator, AllKeysRateLimitedError, is_rate_limit_error, extract_retry_after

class STTService:
    def __init__(self):
        key_list = settings.groq_key_list
        if not key_list:
            logger.warning("⚠️ Không có Groq API key nào được cấu hình. STT sẽ không hoạt động.")
            self.rotator = None
            self._clients = {}
            return
        
        # ✅ Cache tất cả AsyncGroq clients lúc startup
        self.rotator = KeyRotator("groq", key_list)
        self._clients: dict[str, AsyncGroq] = {}
        for key in key_list:
            self._clients[key] = AsyncGroq(api_key=key)
        logger.info(f"✅ Đã khởi tạo Groq STT với {len(key_list)} API key(s).")

    async def transcribe_audio(self, file: UploadFile, language_code: str) -> str:
        """
        Gửi file audio đã tải lên tới Groq Cloud Whisper API.
        Tự động xoay vòng key và retry khi bị rate limit.
        """
        if not self.rotator:
            logger.error("❌ Groq API Key chưa được cấu hình trên backend.")
            raise ValueError("Groq API Key is not configured on the server.")
        
        # Đọc nội dung file audio 1 lần duy nhất
        file_content = await file.read()
        filename = file.filename or "speech.webm"
        
        total_keys = len(self._clients)
        
        for attempt in range(total_keys):
            key = await self.rotator.get_available_key()
            client = self._clients[key]
            try:
                logger.info(
                    f"🎙️ Đang gửi file audio ({len(file_content)} bytes, lang={language_code}) "
                    f"tới Groq Whisper SDK (key ...{key[-6:]})..."
                )
                
                transcription = await client.audio.transcriptions.create(
                    file=(filename, file_content),
                    model="whisper-large-v3",
                    language=language_code if language_code else None,
                    response_format="json"
                )
                
                logger.info("✅ Nhận diện giọng nói thành công từ Groq SDK.")
                return transcription.text
                
            except Exception as e:
                if is_rate_limit_error(e):
                    retry_after = extract_retry_after(e)
                    self.rotator.mark_rate_limited(key, retry_after)
                    continue    # Thử key tiếp theo
                else:
                    self.rotator.mark_error(key)
                    logger.error(f"❌ Gặp lỗi khi xử lý Whisper STT (key ...{key[-6:]}): {e}")
                    raise e
        
        raise AllKeysRateLimitedError(
            f"Tất cả {total_keys} Groq API key(s) đều đang bị rate limit. "
            f"Vui lòng thử lại sau."
        )

stt_service = STTService()
