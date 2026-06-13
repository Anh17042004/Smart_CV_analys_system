import json
import re
import asyncio
from json_repair import loads as json_repair_loads
from ollama import Client
from core.config import settings
from core.logger import logger
from core.key_rotator import KeyRotator, AllKeysRateLimitedError, is_rate_limit_error, extract_retry_after


class AIService:
    def __init__(self):
        key_list = settings.ollama_key_list
        if not key_list:
            logger.warning("⚠️ Không có Ollama API key nào được cấu hình.")
            self.rotator = None
            self._clients = {}
            return
        
        # ✅ Cache tất cả clients lúc startup (không tạo mới mỗi request)
        self.rotator = KeyRotator("ollama", key_list)
        self._clients: dict[str, Client] = {}
        for key in key_list:
            self._clients[key] = Client(
                host=settings.OLLAMA_HOST,
                headers={"Authorization": f"Bearer {key}"}
            )
        logger.info(f"✅ Đã kết nối tới Ollama với {len(key_list)} API key(s).")
    
    async def generate_text(self, prompt: str, model_name: str = None) -> str:
        if not self.rotator:
            raise Exception("External AI service is not available. Please try again later.")
        
        last_error = None
        total_keys = len(self._clients)
        
        for attempt in range(total_keys):
            key = await self.rotator.get_available_key()
            client = self._clients[key]
            try:
                messages = [
                    {
                        "role": "system",
                        "content": "Bạn là chuyên gia tuyển dụng với 10 năm kinh nghiệm, có nhiệm vụ phân tích và chấm điểm CV."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
                # Chạy client.chat() sync trên thread pool để không chặn event loop
                response = await asyncio.to_thread(
                    client.chat,
                    model=model_name or settings.OLLAMA_MODEL,
                    messages=messages
                )
                return response['message']['content'].strip()
            
            except Exception as e:
                if is_rate_limit_error(e):
                    retry_after = extract_retry_after(e)
                    self.rotator.mark_rate_limited(key, retry_after)
                    last_error = e
                    continue    # Thử key tiếp theo
                else:
                    self.rotator.mark_error(key)
                    logger.error(f"Lỗi gọi API Ollama (key ...{key[-6:]}): {str(e)}")
                    raise Exception(f"AI Service Error: {str(e)}")
        
        # Tất cả key đều bị rate limit
        raise AllKeysRateLimitedError(
            f"Tất cả {total_keys} Ollama API key(s) đều đang bị rate limit. "
            f"Vui lòng thử lại sau."
        )

    async def generate_json(self, prompt: str, schema: dict = None, model_name: str = None) -> dict:
        if not self.rotator:
            raise Exception("External AI service is not available. Please try again later.")
        
        last_error = None
        total_keys = len(self._clients)
        
        for attempt in range(total_keys):
            key = await self.rotator.get_available_key()
            client = self._clients[key]
            try:
                messages = [
                    {
                        "role": "system",
                        "content": "Bạn là chuyên gia tuyển dụng với 10 năm kinh nghiệm, có nhiệm vụ phân tích và chấm điểm CV."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
                response = await asyncio.to_thread(
                    client.chat,
                    model=model_name or settings.OLLAMA_MODEL,
                    messages=messages,
                    format=schema or "json"
                )
                content = response['message']['content'].strip()
                
                # Strip markdown code block wrapper nếu có (```json ... ```)
                if content.startswith("```"):
                    content = re.sub(r"^```(?:json)?\s*", "", content)
                    content = re.sub(r"\s*```$", "", content)
                    content = content.strip()
                
                if not content:
                    raise Exception("AI Service trả về nội dung rỗng.")
                
                # Sử dụng json_repair để tự động sửa chữa mọi lỗi JSON từ LLM
                result = json_repair_loads(content)
                
                if not isinstance(result, dict):
                    raise Exception(f"AI Service trả về kiểu dữ liệu không hợp lệ: {type(result).__name__} (cần dict)")
                
                return result
            
            except AllKeysRateLimitedError:
                raise
            except Exception as e:
                if is_rate_limit_error(e):
                    retry_after = extract_retry_after(e)
                    self.rotator.mark_rate_limited(key, retry_after)
                    last_error = e
                    continue
                else:
                    self.rotator.mark_error(key)
                    logger.error(f"❌ Lỗi gọi Ollama generate_json (key ...{key[-6:]}): {e}")
                    raise Exception(f"AI Service Error: {str(e)}")
        
        raise AllKeysRateLimitedError(
            f"Tất cả {total_keys} Ollama API key(s) đều đang bị rate limit. "
            f"Vui lòng thử lại sau."
        )
            
ai_service = AIService()

        