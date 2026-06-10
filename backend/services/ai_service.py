import json
import re
from json_repair import loads as json_repair_loads
from ollama import Client
from core.config import settings
from core.logger import logger


class AIService:
    def __init__(self):
        if settings.OLLAMA_API_KEY:
            self.client = Client(host=settings.OLLAMA_HOST, headers={"Authorization": f"Bearer {settings.OLLAMA_API_KEY}"})
            logger.info("ã kết nối tới Ollama thành công.")
        else:
            self.client = None
            logger.warning("Không có API key, kết nối tới Ollama không thành công.")
    
    def generate_text(self, prompt: str, model_name:str = None) ->str:
        if not self.client:
            raise Exception("External AI service is not available. Please try again later.")
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
            response = self.client.chat(
                model=model_name or settings.OLLAMA_MODEL,
                messages=messages
            )
            return response['message']['content'].strip()
        
        except Exception as e:
            logger.error(f"Lỗi gọi API Ollama: {str(e)}")
            raise Exception(f"AI Service Error: {str(e)}")

    def generate_json(self, prompt: str, schema: dict = None, model_name:str = None) ->dict:
        if not self.client:
            raise Exception("External AI service is not available. Please try again later.")
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
            response = self.client.chat(
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
            # (unicode cụt, dấu ngoặc thiếu, dấu phẩy thừa/thiếu, ký tự điều khiển, v.v.)
            result = json_repair_loads(content)
            
            if not isinstance(result, dict):
                raise Exception(f"AI Service trả về kiểu dữ liệu không hợp lệ: {type(result).__name__} (cần dict)")
            
            return result
        
        except Exception as e:
            logger.error(f"❌ Lỗi gọi Ollama (generate_json): {e}")
            raise Exception(f"AI Service Error: {str(e)}")
            
ai_service = AIService()

        