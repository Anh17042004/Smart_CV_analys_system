import json
from typing import List, Tuple
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy import or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import JobDescription, SavedJob, AnalysisRecommendation, CVUpload

class JobRepository:
    # ============================================================
    # 1. Job Descriptions (JD)
    # ============================================================
    @staticmethod
    async def create_jd(db: AsyncSession, data: dict, skills_list: List[str] = None, embedding: List[float] = None) -> JobDescription:
        skills_json = json.dumps(skills_list) if skills_list else None
        db_jd = JobDescription(
            title=data["title"],
            company=data.get("company"),
            location=data.get("location"),
            salary_range=data.get("salary_range"),
            experience=data.get("experience"),
            employment_type=data.get("employment_type"),
            skills=skills_json,
            description=data["description"],
            summary=data.get("summary"),
            embedding=embedding,
            source_url=data.get("source_url"),
            is_active=data.get("is_active", True)
        )
        db.add(db_jd)
        await db.commit()
        await db.refresh(db_jd)
        return db_jd

    @staticmethod
    async def batch_create_jds(db: AsyncSession, jd_list: List[dict]) -> List[JobDescription]:
        db_jds = []
        for item in jd_list:
            skills = item.get("skills")
            skills_json = json.dumps(skills) if skills else None
            db_jd = JobDescription(
                title=item["title"],
                company=item.get("company"),
                location=item.get("location"),
                salary_range=item.get("salary_range"),
                experience=item.get("experience"),
                employment_type=item.get("employment_type"),
                skills=skills_json,
                description=item["description"],
                summary=item.get("summary"),
                embedding=item.get("embedding"),
                source_url=item.get("source_url"),
                is_active=item.get("is_active", True)
            )
            db_jds.append(db_jd)
        db.add_all(db_jds)
        await db.commit()
        # Refresh all items
        for jd in db_jds:
            await db.refresh(jd)
        return db_jds

    @staticmethod
    async def get_jd_by_id(db: AsyncSession, jd_id: int) -> JobDescription | None:
        result = await db.execute(select(JobDescription).where(JobDescription.id == jd_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def search_by_keyword(db: AsyncSession, keyword: str, location: str = None, limit: int = 20) -> List[JobDescription]:
        conditions = [
            or_(
                JobDescription.title.ilike(f"%{keyword}%"),
                JobDescription.company.ilike(f"%{keyword}%")
            ),
            JobDescription.is_active == True
        ]
        if location:
            conditions.append(JobDescription.location.ilike(f"%{location}%"))
        
        stmt = select(JobDescription).where(and_(*conditions)).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def search_by_vector(db: AsyncSession, query_embedding: List[float], limit: int = 10) -> List[Tuple[JobDescription, float]]:
        # cosine_distance: <=> 
        # Similarity = 1 - Cosine Distance
        distance_expr = JobDescription.embedding.cosine_distance(query_embedding)
        stmt = (
            select(JobDescription, (1 - distance_expr).label("similarity"))
            .where(JobDescription.is_active == True)
            .order_by(distance_expr)
            .limit(limit)
        )
        result = await db.execute(stmt)
        # return list of tuples (JobDescription, score)
        return [(row[0], float(row[1])) for row in result.all()]

    # ============================================================
    # 2. Saved Jobs
    # ============================================================
    @staticmethod
    async def save_job(db: AsyncSession, user_id: int, jd_id: int, match_score: float = None) -> SavedJob:
        db_saved = SavedJob(
            user_id=user_id,
            jd_id=jd_id,
            match_score=match_score
        )
        db.add(db_saved)
        await db.commit()
        
        # Eager load the relationship before returning to prevent MissingGreenlet error
        result = await db.execute(
            select(SavedJob)
            .options(joinedload(SavedJob.job_description))
            .where(SavedJob.id == db_saved.id)
        )
        return result.scalar_one()

    @staticmethod
    async def get_saved_job_by_jd_id(db: AsyncSession, user_id: int, jd_id: int) -> SavedJob | None:
        result = await db.execute(
            select(SavedJob)
            .options(joinedload(SavedJob.job_description))
            .where(SavedJob.user_id == user_id, SavedJob.jd_id == jd_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_saved_jobs(db: AsyncSession, user_id: int) -> List[SavedJob]:
        result = await db.execute(
            select(SavedJob)
            .options(joinedload(SavedJob.job_description))
            .where(SavedJob.user_id == user_id)
            .order_by(SavedJob.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def delete_saved_job(db: AsyncSession, saved_id: int, user_id: int) -> bool:
        result = await db.execute(
            select(SavedJob).where(SavedJob.id == saved_id, SavedJob.user_id == user_id)
        )
        db_saved = result.scalar_one_or_none()
        if db_saved:
            await db.delete(db_saved)
            await db.commit()
            return True
        return False

    # ============================================================
    # 3. Analysis Recommendations
    # ============================================================
    @staticmethod
    async def save_recommendations(db: AsyncSession, cv_analysis_id: int, recommendations: List[dict]):
        # recommendations: [{"jd_id": 1, "match_score": 85.5}, ...]
        db_recs = [
            AnalysisRecommendation(
                cv_analysis_id=cv_analysis_id,
                jd_id=item["jd_id"],
                match_score=item["match_score"]
            )
            for item in recommendations
        ]
        db.add_all(db_recs)
        await db.commit()

    @staticmethod
    async def get_recommendations_by_analysis_id(db: AsyncSession, cv_analysis_id: int) -> List[AnalysisRecommendation]:
        result = await db.execute(
            select(AnalysisRecommendation)
            .options(joinedload(AnalysisRecommendation.job_description))
            .where(AnalysisRecommendation.cv_analysis_id == cv_analysis_id)
            .order_by(AnalysisRecommendation.match_score.desc())
        )
        return result.scalars().all()

    # ============================================================
    # 4. CV Upload Embedding & Summary Caching
    # ============================================================
    @staticmethod
    async def update_cv_summary_and_embedding(db: AsyncSession, cv_id: int, summary: str, embedding: List[float]) -> CVUpload | None:
        result = await db.execute(select(CVUpload).where(CVUpload.id == cv_id))
        cv = result.scalar_one_or_none()
        if cv:
            cv.summary = summary
            cv.embedding = embedding
            await db.commit()
            await db.refresh(cv)
        return cv

job_repo = JobRepository()
