from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db
from api.dependencies import get_current_user
from database.models import User
from schemas.auth import LoginRequest, RegisterRequest, TokenResponse, ProfileUpdateRequest, ChangePasswordRequest
from schemas.user import UserResponse
from services.auth_service import auth_service
router = APIRouter()

@router.post("/register", response_model=UserResponse, summary="Đăng ký tài khoản mới")
async def register(user_data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.register(db, user_data)

@router.post("/login", response_model=TokenResponse, summary="Đăng nhập vào tài khoản")
async def login(user_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.login(db, user_data)

@router.get("/me", response_model=UserResponse, summary="Lấy thông tin tài khoản hiện tại")
async def me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/profile", response_model=UserResponse, summary="Cập nhật thông tin tài khoản")
async def update_profile(
    req_data: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await auth_service.update_profile(db, current_user.id, req_data.full_name)

@router.put("/change-password", summary="Thay đổi mật khẩu")
async def change_password(
    req_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await auth_service.change_password(db, current_user.id, req_data.current_password, req_data.new_password)
    return {"message": "Đổi mật khẩu thành công"}