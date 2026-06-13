"""
Key Rotator — Bộ xoay vòng API Key tự động
=============================================
Quản lý danh sách API key cho các nhà cung cấp (Ollama, Groq, ...),
tự động xoay vòng Round-Robin và bỏ qua key đang bị rate limit.

Tính năng:
  ✅ Async-safe (asyncio.Lock)
  ✅ Round-Robin xoay vòng
  ✅ Auto-retry khi bị 429
  ✅ Cooldown đọc từ Retry-After header
  ✅ Thống kê usage lưu vào database
  ✅ Backward-compatible với 1 key duy nhất
"""

import asyncio
import hashlib
import time
from typing import Optional
from core.logger import logger

# Thời gian cooldown mặc định (giây) khi không có Retry-After header
DEFAULT_COOLDOWN = 60


class AllKeysRateLimitedError(Exception):
    """Tất cả API keys đều đang bị rate limit."""
    pass


class KeyRotator:
    """
    Bộ xoay vòng Round-Robin cho danh sách API keys.
    
    Sử dụng:
        rotator = KeyRotator("ollama", ["key1", "key2", "key3"])
        key = await rotator.get_available_key()
        # ... gọi API với key ...
        # Nếu bị 429:
        rotator.mark_rate_limited(key, retry_after=30)
    """

    def __init__(self, provider: str, keys: list[str]):
        if not keys:
            raise ValueError(f"[{provider}] Danh sách API keys không được rỗng.")
        
        self.provider = provider
        self._keys = keys
        self._index = 0
        self._lock = asyncio.Lock()
        self._cooldowns: dict[str, float] = {}    # {key: thời điểm hết cooldown}
        
        # Thống kê in-memory (sẽ được flush vào database định kỳ)
        self._stats: dict[str, dict] = {}
        for key in keys:
            h = self._hash_key(key)
            self._stats[h] = {
                "provider": provider,
                "request_count": 0,
                "error_count": 0,
                "rate_limit_count": 0,
                "last_used_at": None,
            }
        
        logger.info(f"🔑 [{provider}] KeyRotator khởi tạo với {len(keys)} key(s).")

    @staticmethod
    def _hash_key(key: str) -> str:
        """Tạo mã hash SHA-256 rút gọn 16 ký tự từ key (không lưu plaintext)."""
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    async def get_available_key(self) -> str:
        """
        Lấy key khả dụng tiếp theo theo Round-Robin.
        Bỏ qua các key đang trong thời gian cooldown.
        
        Raises:
            AllKeysRateLimitedError: Khi tất cả keys đều đang bị rate limit.
        """
        async with self._lock:
            now = time.time()
            total = len(self._keys)
            
            for _ in range(total):
                key = self._keys[self._index % total]
                self._index += 1
                
                # Bỏ qua key đang trong cooldown
                expiry = self._cooldowns.get(key, 0)
                if now < expiry:
                    remaining = int(expiry - now)
                    logger.debug(f"⏳ [{self.provider}] Key ...{key[-6:]} đang cooldown, còn {remaining}s. Bỏ qua.")
                    continue
                
                # Cập nhật thống kê
                h = self._hash_key(key)
                self._stats[h]["request_count"] += 1
                self._stats[h]["last_used_at"] = now
                return key
            
            raise AllKeysRateLimitedError(
                f"[{self.provider}] Tất cả {total} API key(s) đều đang bị rate limit. "
                f"Vui lòng thử lại sau."
            )

    def mark_rate_limited(self, key: str, retry_after: Optional[int] = None):
        """
        Đánh dấu key bị rate limit (429) và đưa vào cooldown.
        
        Args:
            key: API key bị rate limit.
            retry_after: Số giây cooldown (từ Retry-After header). 
                         Nếu None, dùng DEFAULT_COOLDOWN.
        """
        cooldown = retry_after or DEFAULT_COOLDOWN
        self._cooldowns[key] = time.time() + cooldown
        
        h = self._hash_key(key)
        self._stats[h]["rate_limit_count"] += 1
        self._stats[h]["error_count"] += 1
        
        logger.warning(
            f"⚠️ [{self.provider}] Key ...{key[-6:]} bị rate limit! "
            f"Cooldown {cooldown}s. "
            f"(Tổng bị limit: {self._stats[h]['rate_limit_count']} lần)"
        )

    def mark_error(self, key: str):
        """Đánh dấu key gặp lỗi (không phải rate limit)."""
        h = self._hash_key(key)
        self._stats[h]["error_count"] += 1

    def get_status(self) -> dict:
        """Trả về trạng thái tổng quan cho Admin monitoring."""
        now = time.time()
        active = sum(1 for k in self._keys if now >= self._cooldowns.get(k, 0))
        cooldown_count = len(self._keys) - active
        return {
            "total": len(self._keys),
            "active": active,
            "cooldown": cooldown_count,
            "keys": {
                self._hash_key(k): {
                    **self._stats[self._hash_key(k)],
                    "is_active": now >= self._cooldowns.get(k, 0),
                }
                for k in self._keys
            }
        }

    async def flush_stats_to_db(self, db):
        """
        Đẩy thống kê in-memory vào bảng api_key_usages trong database.
        Gọi khi Admin request hoặc khi có sự kiện rate limit.
        """
        from database.models import ApiKeyUsage
        from sqlalchemy.future import select
        from datetime import datetime, timezone
        
        for key in self._keys:
            h = self._hash_key(key)
            stats = self._stats[h]
            
            # Tìm record hiện có trong DB
            result = await db.execute(
                select(ApiKeyUsage).where(
                    ApiKeyUsage.provider == self.provider,
                    ApiKeyUsage.key_hash == h
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # Cộng dồn vào record hiện có
                existing.request_count = (existing.request_count or 0) + stats["request_count"]
                existing.error_count = (existing.error_count or 0) + stats["error_count"]
                existing.rate_limit_count = (existing.rate_limit_count or 0) + stats["rate_limit_count"]
                if stats["last_used_at"]:
                    existing.last_used_at = datetime.fromtimestamp(stats["last_used_at"], tz=timezone.utc)
                existing.updated_at = datetime.now(timezone.utc)
            else:
                # Tạo record mới
                new_record = ApiKeyUsage(
                    provider=self.provider,
                    key_hash=h,
                    request_count=stats["request_count"],
                    error_count=stats["error_count"],
                    rate_limit_count=stats["rate_limit_count"],
                    last_used_at=datetime.fromtimestamp(stats["last_used_at"], tz=timezone.utc) if stats["last_used_at"] else None,
                )
                db.add(new_record)
            
            # Reset bộ đếm in-memory sau khi flush
            stats["request_count"] = 0
            stats["error_count"] = 0
            stats["rate_limit_count"] = 0
        
        await db.commit()
        logger.info(f"💾 [{self.provider}] Đã flush thống kê {len(self._keys)} key(s) vào database.")


# ── Helper functions ──

def is_rate_limit_error(error: Exception) -> bool:
    """
    Phát hiện lỗi rate limit bằng status_code hoặc exception type.
    KHÔNG dùng string matching.
    """
    # Check status_code trực tiếp trên exception
    if hasattr(error, "status_code"):
        return error.status_code == 429
    
    # Check status_code qua response object
    if hasattr(error, "response") and hasattr(error.response, "status_code"):
        return error.response.status_code == 429
    
    # Groq SDK: groq.RateLimitError
    error_class_name = type(error).__name__
    if error_class_name == "RateLimitError":
        return True
    
    return False


def extract_retry_after(error: Exception) -> Optional[int]:
    """
    Đọc giá trị Retry-After từ response header (nếu có).
    Trả về số giây, hoặc None nếu không tìm thấy.
    """
    # Thử đọc từ response.headers
    if hasattr(error, "response") and hasattr(error.response, "headers"):
        val = error.response.headers.get("Retry-After") or error.response.headers.get("retry-after")
        if val and str(val).isdigit():
            return int(val)
    
    # Thử đọc từ thuộc tính retry_after (Groq SDK)
    if hasattr(error, "retry_after"):
        return int(error.retry_after)
    
    return None
