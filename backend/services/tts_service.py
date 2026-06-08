import urllib.request
import urllib.parse
from fastapi.responses import StreamingResponse
from core.logger import logger

class TTSService:
    def stream_tts(self, text: str, lang: str = "vi") -> StreamingResponse:
        """Tải luồng âm thanh từ Google Translate TTS và chuyển tiếp về Client."""
        if len(text) > 200:
            text = text[:200]
        
        encoded_text = urllib.parse.quote(text)
        url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl={lang}&client=tw-ob&q={encoded_text}"
        
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        
        def stream_audio():
            try:
                with urllib.request.urlopen(req) as response:
                    while True:
                        chunk = response.read(4096)
                        if not chunk:
                            break
                        yield chunk
            except Exception as e:
                logger.error(f"❌ Lỗi proxy TTS: {e}")
                yield b""

        return StreamingResponse(stream_audio(), media_type="audio/mpeg")

tts_service = TTSService()
