from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from database.repositories.user_repo import user_repo
from schemas.user import UserResponse
from schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from core.security import hash_password, verify_password, create_access_token
from database.models import User

class AuthService:
    async def register(self, db: AsyncSession, user_data: RegisterRequest) -> UserResponse:
        existing_user = await user_repo.get_by_email(db, user_data.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already exists")
        hashed_password = hash_password(user_data.password)
        new_user = await user_repo.create(db, user_data=user_data, hashed_password=hashed_password)
        return UserResponse.model_validate(new_user)


    async def login(self, db: AsyncSession, user_data: LoginRequest) -> TokenResponse:
        user = await user_repo.get_by_email(db, user_data.email)
        if not user:
            raise HTTPException(status_code=400, detail="Email not found")
        if not verify_password(user_data.password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect password")
        access_token = create_access_token(data={"sub": str(user.id)})
        await user_repo.update_last_login(db, user.id)
        return TokenResponse(access_token=access_token)


    async def get_me(self, db: AsyncSession, user_id: int) -> UserResponse:
        user = await user_repo.get_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserResponse.model_validate(user)

    async def update_profile(self, db: AsyncSession, user_id: int, full_name: str) -> UserResponse:
        user = await user_repo.get_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        updated_user = await user_repo.update_profile(db, user, full_name)
        return UserResponse.model_validate(updated_user)

    async def change_password(self, db: AsyncSession, user_id: int, current_password: str, new_password: str) -> None:
        user = await user_repo.get_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if not verify_password(current_password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mật khẩu hiện tại không chính xác")
        hashed_password = hash_password(new_password)
        await user_repo.update_password(db, user, hashed_password)
        
auth_service = AuthService()