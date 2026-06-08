from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, status, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from api.dependencies import get_current_user
from database.models import User
from schemas.cv import CVUploadResponse, AnalysisRequest, CVAnalysisResponse, BatchDeleteRequest, JDExtractResponse
from schemas.job import JobRecommendResponse
from services.cv_service import cv_service

router = APIRouter()

@router.post("/upload", response_model=CVUploadResponse, status_code=status.HTTP_201_CREATED, summary="Tải lên file CV (PDF/DOCX)")
async def upload_cv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await cv_service.upload_cv(db, file, current_user.id)


@router.post("/analyze", response_model=CVAnalysisResponse, summary="Phân tích CV bằng AI Ollama")
async def analyze_cv(
    request_data: AnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await cv_service.analyze_cv(db, request_data.cv_id, current_user.id, request_data.job_description)


@router.get("/history", response_model=List[CVAnalysisResponse], summary="Lấy lịch sử phân tích CV của User")
async def get_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await cv_service.get_history(db, current_user.id)


@router.get("/result/{analysis_id}", response_model=CVAnalysisResponse, summary="Xem chi tiết kết quả phân tích theo ID")
async def get_result(
    analysis_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await cv_service.get_analysis_detail(db, analysis_id, current_user.id)


@router.get("/report/{analysis_id}", summary="Tải file báo cáo PDF kết quả phân tích CV")
async def download_report(
    analysis_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pdf_buffer = await cv_service.generate_pdf_report(db, analysis_id, current_user.id)
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=cv_report_{analysis_id}.pdf"}
    )


@router.get("/recommend/{cv_id}", response_model=JobRecommendResponse, summary="Gợi ý việc làm phù hợp cho CV (Vector Search)")
async def recommend_jobs(
    cv_id: int,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from services.job_service import job_service
    recs = await job_service.recommend_jobs_for_cv(db, cv_id, current_user.id, limit=limit)
    return JobRecommendResponse(
        cv_id=cv_id,
        total=len(recs),
        recommendations=recs
    )


@router.delete("/analysis/{analysis_id}", summary="Xóa một bản ghi phân tích CV")
async def delete_analysis(
    analysis_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    success = await cv_service.delete_analysis(db, analysis_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy lịch sử phân tích CV hoặc bạn không có quyền xóa."
        )
    return {"message": "Xóa lịch sử phân tích CV thành công."}


@router.post("/analysis/batch-delete", summary="Xóa hàng loạt bản ghi phân tích CV")
async def batch_delete_analyses(
    request: BatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deleted_count = await cv_service.batch_delete_analyses(db, request.analysis_ids, current_user.id)
    return {
        "message": f"Đã xóa thành công {deleted_count} bản ghi phân tích CV.",
        "deleted_count": deleted_count
    }


@router.post("/extract-text", response_model=JDExtractResponse, summary="Trích xuất văn bản từ file JD (PDF/DOCX)")
async def extract_text(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    filename = file.filename
    file_ext = filename.split(".")[-1].lower() if "." in filename else ""
    if file_ext not in ["pdf", "docx"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chỉ chấp nhận file định dạng .pdf hoặc .docx"
        )

    file_bytes = await file.read()
    extracted_text = cv_service.extract_text(file_bytes, file_ext)
    return JDExtractResponse(text=extracted_text, filename=filename)

