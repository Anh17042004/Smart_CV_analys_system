import json
from typing import List
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import CVUpload, CVAnalysis, AnalysisRecommendation

class CVRepository:
    @staticmethod
    async def save_upload(db: AsyncSession, user_id: int, filename: str, file_path: str, file_type: str, file_size: int, extracted_text: str = None) -> CVUpload:
        db_upload = CVUpload(
            user_id=user_id,
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            extracted_text=extracted_text,
        )
        db.add(db_upload)
        await db.commit()
        await db.refresh(db_upload)
        return db_upload
    
    @staticmethod
    async def get_upload_by_id(db: AsyncSession, cv_id: int, user_id: int) -> CVUpload | None:
        """Lấy thông tin file upload theo ID và User ID."""
        result = await db.execute(
            select(CVUpload).where(CVUpload.id == cv_id, CVUpload.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def save_analysis(db: AsyncSession, cv_id: int, user_id: int, job_description: str | None, analysis_result: dict) -> CVAnalysis:
        target_field = analysis_result.get("target_field")
        target_role = analysis_result.get("target_role")
        resume_score = analysis_result.get("resume_score")
        ats_score = analysis_result.get("ats_score")
        detailed_feedback = analysis_result.get("detailed_feedback")
        #chuẩn bị dữ liệu json
        strengths_json = json.dumps(analysis_result.get("strengths", []))
        weaknesses_json = json.dumps(analysis_result.get("weaknesses", []))
        improvements_json = json.dumps(analysis_result.get("improvements", []))
        skills_analysis_json = json.dumps(analysis_result.get("skills_analysis", {}))
        
        job_match = analysis_result.get("job_match")
        job_match_json = json.dumps(job_match) if job_match else None
        
        recommended_courses_json = json.dumps(analysis_result.get("recommended_courses", []))
        db_analysis = CVAnalysis(
            cv_id=cv_id,
            user_id=user_id,
            job_description=job_description,
            target_field=target_field,
            target_role=target_role,
            resume_score=resume_score,
            ats_score=ats_score,
            strengths=strengths_json,
            weaknesses=weaknesses_json,
            improvements=improvements_json,
            skills_analysis=skills_analysis_json,
            job_match=job_match_json,
            recommended_courses=recommended_courses_json,
            detailed_feedback=detailed_feedback
        )
        
        db.add(db_analysis)
        await db.commit()
        await db.refresh(db_analysis)
        return db_analysis


    @staticmethod
    async def get_user_analyses(db: AsyncSession, user_id: int) -> List[CVAnalysis]:
        """Lấy toàn bộ lịch sử phân tích của một User, kèm theo các gợi ý công việc."""
        from sqlalchemy.orm import joinedload
        result = await db.execute(
            select(CVAnalysis)
            .options(joinedload(CVAnalysis.recommendations).joinedload(AnalysisRecommendation.job_description))
            .where(CVAnalysis.user_id == user_id)
            .order_by(CVAnalysis.created_at.desc())
        )
        return result.unique().scalars().all()

        
    @staticmethod
    async def get_analysis_by_id(db: AsyncSession, analysis_id: int, user_id: int) -> CVAnalysis | None:
        """Lấy chi tiết kết quả phân tích theo ID, kèm theo các gợi ý công việc."""
        from sqlalchemy.orm import joinedload
        result = await db.execute(
            select(CVAnalysis)
            .options(joinedload(CVAnalysis.recommendations).joinedload(AnalysisRecommendation.job_description))
            .where(CVAnalysis.id == analysis_id, CVAnalysis.user_id == user_id)
        )
        return result.unique().scalar_one_or_none()

    @staticmethod
    async def delete_analysis(db: AsyncSession, analysis_id: int, user_id: int) -> bool:
        """Xóa một bản ghi phân tích CV theo ID và User ID."""
        result = await db.execute(
            select(CVAnalysis).where(CVAnalysis.id == analysis_id, CVAnalysis.user_id == user_id)
        )
        analysis = result.scalar_one_or_none()
        if analysis:
            await db.delete(analysis)
            await db.commit()
            return True
        return False

    @staticmethod
    async def batch_delete_analyses(db: AsyncSession, analysis_ids: List[int], user_id: int) -> int:
        """Xóa hàng loạt các bản ghi phân tích CV theo danh sách ID và User ID."""
        from sqlalchemy import delete
        stmt = (
            delete(CVAnalysis)
            .where(CVAnalysis.id.in_(analysis_ids), CVAnalysis.user_id == user_id)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount

cv_repo = CVRepository()