import edge_tts
from fastapi.responses import StreamingResponse
from core.logger import logger

class TTSService:
    async def stream_tts(self, text: str, voice: str = "vi-VN-HoaiMyNeural") -> StreamingResponse:
        """
        Tạo luồng phát âm thanh trực tuyến từ Microsoft Edge TTS và chuyển tiếp về Client.
        """
        try:
            communicate = edge_tts.Communicate(text, voice)
            
            async def stream_generator():
                try:
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            yield chunk["data"]
                except Exception as stream_err:
                    logger.error(f"❌ Lỗi trong generator stream Edge TTS: {stream_err}")
                    yield b""
                    
            return StreamingResponse(stream_generator(), media_type="audio/mpeg")
            
        except Exception as e:
            logger.error(f"❌ Lỗi khi khởi tạo Edge TTS: {e}")
            # Fallback trả về stream rỗng để tránh treo kết nối client
            async def empty_generator():
                yield b""
            return StreamingResponse(empty_generator(), media_type="audio/mpeg")

tts_service = TTSService()
