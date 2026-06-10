from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db
from api.dependencies import get_current_user
from database.models import User
from schemas.job import (
    JobDescriptionCreate,
    JobDescriptionResponse,
    JobSearchRequest,
    JobSearchResponse,
    SavedJobCreate,
    SavedJobResponse
)
from services.job_service import job_service

router = APIRouter()

def format_jd_response(jd) -> JobDescriptionResponse:
    import json
    skills_list = []
    if jd.skills:
        try:
            skills_list = json.loads(jd.skills) if isinstance(jd.skills, str) else jd.skills
        except Exception:
            skills_list = []
    return JobDescriptionResponse(
        id=jd.id,
        title=jd.title,
        company=jd.company,
        location=jd.location,
        salary_range=jd.salary_range,
        experience=jd.experience,
        employment_type=jd.employment_type,
        skills=skills_list,
        description=jd.description,
        summary=jd.summary,
        source_url=jd.source_url,
        is_active=jd.is_active,
        created_at=jd.created_at
    )

# ============================================================
# 1. Job Description Ingestion (Admin)
# ============================================================
@router.post("/jd", response_model=JobDescriptionResponse, status_code=status.HTTP_201_CREATED, summary="[Admin] Thêm mới một Job Description")
async def create_job(
    request: JobDescriptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Ràng buộc phân quyền Admin nếu cần, ở đây cho phép mọi tài khoản demo
    if current_user.role != "admin":
         # Cho phép cả user và admin để dễ dàng demo thử nghiệm trong giai đoạn phát triển
         pass
    jd = await job_service.ingest_jd(db, request)
    return format_jd_response(jd)


@router.post("/jd/batch", response_model=List[JobDescriptionResponse], status_code=status.HTTP_201_CREATED, summary="[Admin] Import hàng loạt Job Description")
async def batch_create_jobs(
    request: List[JobDescriptionCreate],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    inserted_jds = await job_service.batch_ingest_jds(db, request)
    return [format_jd_response(jd) for jd in inserted_jds]


@router.get("/jd/{jd_id}", response_model=JobDescriptionResponse, summary="Xem thông tin chi tiết một Job Description")
async def get_job_detail(
    jd_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from database.repositories.job_repo import job_repo
    jd = await job_repo.get_jd_by_id(db, jd_id)
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy thông tin công việc yêu cầu."
        )
    return format_jd_response(jd)


# ============================================================
# 2. Job Search (Keyword)
# ============================================================
@router.post("/search", response_model=JobSearchResponse, summary="Tìm kiếm việc làm theo từ khóa và vị trí (SQL LIKE)")
async def search_jobs(
    request: JobSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    jds, total = await job_service.search_jobs(db, request.keyword, request.location)
    results = [format_jd_response(jd) for jd in jds]
    return JobSearchResponse(total=total, results=results)


# ============================================================
# 3. Saved Jobs
# ============================================================
@router.post("/saved", response_model=SavedJobResponse, status_code=status.HTTP_201_CREATED, summary="Lưu công việc yêu thích")
async def save_job(
    request: SavedJobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_saved = await job_service.save_job(db, current_user.id, request.jd_id)
    return SavedJobResponse(
        id=db_saved.id,
        jd=format_jd_response(db_saved.job_description),
        match_score=db_saved.match_score,
        created_at=db_saved.created_at
    )


@router.get("/saved", response_model=List[SavedJobResponse], summary="Lấy danh sách các công việc đã lưu")
async def get_saved_jobs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await job_service.get_saved_jobs(db, current_user.id)


@router.delete("/saved/{saved_id}", summary="Xóa công việc khỏi danh sách lưu")
async def delete_saved_job(
    saved_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    success = await job_service.delete_saved_job(db, saved_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy bản ghi lưu việc làm để xóa."
        )
    return {"message": "Đã xóa công việc khỏi danh sách lưu thành công."}
