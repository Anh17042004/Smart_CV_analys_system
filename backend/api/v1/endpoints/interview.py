from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from api.dependencies import get_current_user
from database.models import User
from schemas.interview import (
    InterviewStartRequest,
    InterviewSessionStartResponse,
    InterviewAnswerSubmit,
    InterviewAnswerSubmitResponse,
    InterviewSessionResponse
)
from services.interview_service import interview_service

router = APIRouter()

@router.post("/start", response_model=InterviewSessionStartResponse, status_code=status.HTTP_201_CREATED, summary="Khởi tạo phiên phỏng vấn mới")
async def start_interview(
    request_data: InterviewStartRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        result = await interview_service.start_session(db, current_user.id, request_data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khởi tạo phiên phỏng vấn: {str(e)}"
        )

@router.post("/answer", response_model=InterviewAnswerSubmitResponse, summary="Gửi câu trả lời của ứng viên cho câu hỏi hiện tại")
async def submit_answer(
    answer_data: InterviewAnswerSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # submit_answer raises HTTPException for validation errors (e.g. out of order, already answered, session not found)
    return await interview_service.submit_answer(
        db=db,
        user_id=current_user.id,
        session_id=answer_data.session_id,
        question_number=answer_data.question_number,
        answer_text=answer_data.answer_text
    )

@router.get("/session/{session_id}", response_model=InterviewSessionResponse, summary="Lấy chi tiết kết quả của một phiên phỏng vấn")
async def get_session_details(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = await interview_service.get_session(db, session_id, current_user.id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy phiên phỏng vấn."
        )
    return interview_service.format_session_response(session)

@router.get("/history", response_model=List[InterviewSessionResponse], summary="Lấy lịch sử các phiên phỏng vấn của user")
async def get_interview_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sessions = await interview_service.get_history(db, current_user.id)
    return [interview_service.format_session_response(s) for s in sessions]

@router.delete("/{session_id}", summary="Xóa một phiên phỏng vấn")
async def delete_interview_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    success = await interview_service.delete_session(db, session_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy phiên phỏng vấn để xóa."
        )
    return {"success": True, "message": "Đã xóa phiên phỏng vấn thành công."}
