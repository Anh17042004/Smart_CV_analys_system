from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from core.config import settings
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    # ── Connection Pool tối ưu cho gói Supabase Free (giới hạn 15 kết nối) ──
    pool_size=3,           # Số kết nối giữ sẵn trong pool (luôn mở)
    max_overflow=5,        # Số kết nối bổ sung tối đa khi pool đầy (tổng = 3+5 = 8 kết nối mỗi instance)
    pool_recycle=1800,     # Tái tạo kết nối mỗi 30 phút để tránh kết nối cũ bị đóng bởi server
    pool_pre_ping=True,    # Kiểm tra kết nối còn sống trước khi sử dụng (tránh lỗi "connection closed")
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()

#tạo base cho mọi object database
class Base(DeclarativeBase):
    pass

async def init_database():
    async with engine.begin() as conn:
        # Tạo extension pgvector trước khi tạo các bảng
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        # Tạo tất cả các bảng khai báo từ Base
        await conn.run_sync(Base.metadata.create_all)