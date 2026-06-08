from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from database.models import User
from schemas.user import UserCreate

class UserRepository:
    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
        """Lấy User từ DB bằng ID."""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> User | None:
        """Lấy User từ DB bằng Email."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create(db: AsyncSession, user_data: UserCreate, hashed_password: str) -> User:
        """Tạo mới User trong DB."""
        db_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    @staticmethod
    async def update_last_login(db: AsyncSession, user_id: int) -> None:
        """Cập nhật thời gian đăng nhập cuối cùng của User."""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.last_login = datetime.now(timezone.utc)
            await db.commit()

    @staticmethod
    async def update_profile(db: AsyncSession, user: User, full_name: str) -> User:
        """Cập nhật thông tin profile của User."""
        user.full_name = full_name
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def update_password(db: AsyncSession, user: User, hashed_password: str) -> User:
        """Cập nhật mật khẩu mới của User."""
        user.hashed_password = hashed_password
        await db.commit()
        await db.refresh(user)
        return user

user_repo = UserRepository()
