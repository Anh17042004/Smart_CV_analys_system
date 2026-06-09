import json
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
    
    def generate_json(self, prompt: str, model_name:str = None) ->dict:
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
                format="json"
            )
            content = response['message']['content'].strip()
            
            # Strip markdown code block wrapper nếu có (```json ... ```)
            if content.startswith("```"):
                import re
                content = re.sub(r"^```(?:json)?\s*", "", content)
                content = re.sub(r"\s*```$", "", content)
                content = content.strip()
            
            if not content:
                raise Exception("AI Service trả về nội dung rỗng.")
            
            return json.loads(content)
        
        except json.JSONDecodeError as jde:
            raw_content = response['message']['content'] if 'response' in dir() else 'No response content'
            logger.error(f"❌ Lỗi parse JSON từ Ollama: {jde}.\nNội dung thô nhận được:\n{raw_content}")
            raise Exception(f"AI Service trả về định dạng JSON không hợp lệ: {jde}")
        except Exception as e:
            logger.error(f"❌ Lỗi gọi Ollama (generate_json): {e}")
            raise Exception(f"AI Service Error: {str(e)}")
            
ai_service = AIService()
        