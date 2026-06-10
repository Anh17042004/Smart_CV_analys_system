import os
import asyncio
from sentence_transformers import SentenceTransformer

class EmbeddingService:
    def __init__(self):
        self._model = None

    @property
    def model(self):
        if self._model is None:
            # Kiểm tra xem mô hình bkai-foundation-models/vietnamese-bi-encoder có tồn tại cục bộ không
            local_model_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "models",
                "vietnamese-bi-encoder"
            )
            if os.path.exists(local_model_path) and (
                os.path.exists(os.path.join(local_model_path, "pytorch_model.bin")) or 
                os.path.exists(os.path.join(local_model_path, "model.safetensors"))
            ):
                self._model = SentenceTransformer(local_model_path, device='cpu')
            else:
                self._model = SentenceTransformer('bkai-foundation-models/vietnamese-bi-encoder', device='cpu')
        return self._model

    def encode(self, text: str) -> list[float]:
        if not text:
            return []
        return self.model.encode(text).tolist()

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return self.model.encode(texts).tolist()

    # ── Phương thức bất đồng bộ (Async) ──
    # Chạy tính toán embedding trên thread pool riêng để không chặn event loop ASGI
    async def encode_async(self, text: str) -> list[float]:
        """Phiên bản async của encode(), chạy trên thread pool để tránh block event loop."""
        if not text:
            return []
        return await asyncio.to_thread(self.encode, text)

    async def encode_batch_async(self, texts: list[str]) -> list[list[float]]:
        """Phiên bản async của encode_batch(), chạy trên thread pool để tránh block event loop."""
        if not texts:
            return []
        return await asyncio.to_thread(self.encode_batch, texts)

embedding_service = EmbeddingService()

