import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.logger import setup_logging, logger
from core.exceptions import BaseAppException, app_exception_handler, global_exception_handler, validation_exception_handler
from api.v1.router import api_router
from database.connection import init_database 


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    # Tự động tạo bảng DB khi start server
    await init_database() 
    logger.info(f"🚀 Bật ứng dụng {settings.PROJECT_NAME} v{settings.VERSION}")
    
    # Nạp trước mô hình Embedding tiếng Việt khi khởi động để tránh trễ cho request đầu tiên
    try:
        from services.embedding_service import embedding_service
        logger.info("⏳ Đang nạp trước mô hình Embedding tiếng Việt (vietnamese-bi-encoder)...")
        # Truy cập property .model để kích hoạt SentenceTransformer load
        _ = embedding_service.model
        logger.info("✅ Đã nạp thành công mô hình Embedding tiếng Việt.")
    except Exception as e:
        logger.error(f"⚠️ Không thể nạp trước mô hình Embedding lúc khởi động (có thể do thiếu RAM/Bộ nhớ ảo): {e}")
        
    yield
    logger.info("🛑 Tắt server an toàn.")


app = FastAPI(
    title = settings.PROJECT_NAME,
    version = settings.VERSION,
    lifespan = lifespan
)

# Cấu hình bảo mật kết nối
app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],  # cho phép mọi domain truy cập
    allow_credentials=True, # cho phép gửi credentials,
    allow_methods = ["*"], # cho phép http method
    allow_headers = ["*"]
)

# Đăng ký Router V1 vào FastAPI
app.include_router(api_router, prefix=settings.API_V1_STR)

# đăng ký hàm bắt lỗi
app.add_exception_handler(BaseAppException, app_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)


# api test
@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "ok",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        workers=settings.WORKERS,
        reload=settings.DEBUG
    )