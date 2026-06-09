import json
import re
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
    
    def _sanitize_json(self, content: str) -> str:
        """Sanitizes JSON string by escaping invalid backslash and unicode escapes."""
        result = []
        i = 0
        n = len(content)
        while i < n:
            char = content[i]
            if char == '\\':
                if i + 1 < n:
                    next_char = content[i+1]
                    if next_char in ['"', '\\', '/', 'b', 'f', 'n', 'r', 't']:
                        result.append('\\' + next_char)
                        i += 2
                        continue
                    elif next_char == 'u':
                        if i + 5 < n and all(c in '0123456789abcdefABCDEF' for c in content[i+2:i+6]):
                            result.append(content[i:i+6])
                            i += 6
                            continue
                        else:
                            result.append('\\\\u')
                            i += 2
                            continue
                    else:
                        result.append('\\\\' + next_char)
                        i += 2
                        continue
                else:
                    result.append('\\\\')
                    i += 1
            else:
                result.append(char)
                i += 1
                
        return "".join(result)

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
            
            # Sanitize JSON string before loading
            content = self._sanitize_json(content)
            
            return json.loads(content)
        
        except json.JSONDecodeError as jde:
            raw_content = response['message']['content'] if 'response' in dir() else 'No response content'
            logger.error(f"❌ Lỗi parse JSON từ Ollama: {jde}.\nNội dung thô nhận được:\n{raw_content}")
            raise Exception(f"AI Service trả về định dạng JSON không hợp lệ: {jde}")
        except Exception as e:
            logger.error(f"❌ Lỗi gọi Ollama (generate_json): {e}")
            raise Exception(f"AI Service Error: {str(e)}")
            
ai_service = AIService()
        