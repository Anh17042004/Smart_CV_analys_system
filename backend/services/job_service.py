import math
import re
import asyncio
from typing import List, Tuple
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from database.models import JobDescription, SavedJob, CVUpload, CVAnalysis
from database.repositories.job_repo import job_repo
from services.embedding_service import embedding_service
from services.ai_service import ai_service
from prompts.job_search import JD_SUMMARY_PROMPT, CV_SUMMARY_PROMPT
from schemas.job import JobDescriptionCreate, JobDescriptionResponse, JobRecommendItem, JobRecommendResponse, SavedJobResponse

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    dot_product = sum(x * y for x, y in zip(v1, v2))
    magnitude1 = math.sqrt(sum(x * x for x in v1))
    magnitude2 = math.sqrt(sum(x * x for x in v2))
    if not magnitude1 or not magnitude2:
        return 0.0
    return dot_product / (magnitude1 * magnitude2)

def parse_years_of_experience(exp_str: str) -> float:
    if not exp_str:
        return 0.0
    
    exp_str_lower = exp_str.lower()
    
    no_exp_keywords = ["chưa có", "không có", "no experience", "fresher", "intern", "chưa", "dưới 1 năm"]
    if any(kw in exp_str_lower for kw in no_exp_keywords):
        if "dưới 1" in exp_str_lower:
            return 0.5
        return 0.0
        
    numbers = re.findall(r"\d+(?:\.\d+)?", exp_str_lower)
    if not numbers:
        return 0.0
        
    float_nums = [float(n) for n in numbers]
    return sum(float_nums) / len(float_nums)

def parse_jd_experience(jd_exp_str: str) -> tuple[float | None, float | None]:
    if not jd_exp_str:
        return None, None
        
    exp_str_lower = jd_exp_str.lower()
    
    no_exp_keywords = ["không yêu cầu", "không y/c", "chưa có kinh nghiệm", "no requirement", "any", "không quan trọng"]
    if any(kw in exp_str_lower for kw in no_exp_keywords):
        return 0.0, None
        
    if "dưới 1 năm" in exp_str_lower or "dưới 1" in exp_str_lower:
        return 0.0, 1.0
        
    if "trên" in exp_str_lower or "tối thiểu" in exp_str_lower or "+" in exp_str_lower:
        numbers = re.findall(r"\d+(?:\.\d+)?", exp_str_lower)
        if numbers:
            val = float(numbers[0])
            return val, None
            
    normalized = re.sub(r"\s*(?:-|đến|to)\s*", "-", exp_str_lower)
    range_match = re.search(r"(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)", normalized)
    if range_match:
        min_val = float(range_match.group(1))
        max_val = float(range_match.group(2))
        return min_val, max_val
        
    numbers = re.findall(r"\d+(?:\.\d+)?", exp_str_lower)
    if numbers:
        val = float(numbers[0])
        return val, None
        
    return None, None

def extract_experience_from_cv_summary(summary: str) -> float:
    if not summary:
        return 0.0
    parts = [p.strip() for p in summary.split('|')]
    if len(parts) >= 4:
        return parse_years_of_experience(parts[3])
    return parse_years_of_experience(summary)

def extract_experience_from_jd(jd) -> tuple[float | None, float | None]:
    if jd.experience:
        min_exp, max_exp = parse_jd_experience(jd.experience)
        if min_exp is not None:
            return min_exp, max_exp
            
    if jd.summary:
        parts = [p.strip() for p in jd.summary.split('|')]
        if len(parts) >= 4:
            return parse_jd_experience(parts[3])
            
    return None, None

def calculate_match_score(similarity: float, cv_summary: str, jd) -> float:
    raw_score = similarity * 100.0
    raw_score = max(0.0, min(100.0, raw_score))
    
    cv_exp = extract_experience_from_cv_summary(cv_summary)
    min_exp, max_exp = extract_experience_from_jd(jd)
    
    if min_exp is not None and cv_exp < min_exp:
        deficit = min_exp - cv_exp
        penalty = deficit * 12.0
        return max(0.0, round(raw_score - penalty, 2))
        
    return round(raw_score, 2)

class JobService:
    # ============================================================
    # 1. Job Description Ingestion (Admin)
    # ============================================================
    @staticmethod
    async def ingest_jd(db: AsyncSession, jd_data: JobDescriptionCreate) -> JobDescription:
        # ① Gọi LLM để tóm tắt JD theo định dạng chuẩn hóa
        prompt = JD_SUMMARY_PROMPT.format(job_description=jd_data.description)
        try:
            summary = await asyncio.to_thread(ai_service.generate_text, prompt)
        except Exception as e:
            summary = jd_data.title  # Fallback nếu AI lỗi

        # ② Gọi Embedding Service để sinh vector 384D từ summary (async, không chặn event loop)
        embedding = None
        if summary:
            embedding = await embedding_service.encode_async(summary)

        # ③ Lưu thông tin vào SQLite/Postgres
        data_dict = jd_data.model_dump()
        data_dict["summary"] = summary
        
        return await job_repo.create_jd(
            db=db,
            data=data_dict,
            skills_list=jd_data.skills,
            embedding=embedding
        )

    @staticmethod
    async def batch_ingest_jds(db: AsyncSession, jds: List[JobDescriptionCreate]) -> List[JobDescription]:
        inserted_jds = []
        for jd in jds:
            inserted = await JobService.ingest_jd(db, jd)
            inserted_jds.append(inserted)
        return inserted_jds

    # ============================================================
    # 2. Job Search (Từ khóa SQL)
    # ============================================================
    @staticmethod
    async def search_jobs(db: AsyncSession, keyword: str, location: str = None) -> tuple[List[JobDescription], int]:
        return await job_repo.search_by_keyword(db, keyword, location)

    # ============================================================
    # 3. Job Recommendation (Vector Search)
    # ============================================================
    @staticmethod
    async def recommend_jobs_for_cv(db: AsyncSession, cv_id: int, user_id: int, cv_analysis_id: int = None, limit: int = 10) -> List[JobRecommendItem]:
        # ① Lấy CV upload gốc
        result = await db.execute(
            select(CVUpload).where(CVUpload.id == cv_id, CVUpload.user_id == user_id)
        )
        cv = result.scalar_one_or_none()
        if not cv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy CV upload được chỉ định."
            )

        # ② Kiểm tra cache summary & embedding
        summary = cv.summary
        embedding = cv.embedding

        if not summary or embedding is None:
            # Tạo tóm tắt CV từ LLM (async, không chặn event loop)
            prompt = CV_SUMMARY_PROMPT.format(extracted_text=cv.extracted_text or "")
            try:
                summary = await asyncio.to_thread(ai_service.generate_text, prompt)
            except Exception:
                summary = cv.filename

            # Tạo embedding từ tóm tắt (async, không chặn event loop)
            embedding = await embedding_service.encode_async(summary)
            
            # Cập nhật cache vào DB
            await job_repo.update_cv_summary_and_embedding(db, cv_id, summary, embedding)

        # ③ Thực hiện truy vấn Vector Search trên pgvector với giới hạn lớn hơn để phục vụ re-ranking
        retrieval_limit = max(limit * 5, 50)
        matched_jobs = await job_repo.search_by_vector(db, embedding, limit=retrieval_limit)

        # ④ Định dạng dữ liệu và tính toán điểm tương thích có phạt (Re-ranking)
        recommend_items = []

        for jd, similarity in matched_jobs:
            # Tính điểm tương thích sau khi phạt độ lệch kinh nghiệm
            match_score = calculate_match_score(similarity, summary, jd)
            
            # Đọc kỹ năng dạng JSON string từ DB chuyển thành list
            import json
            skills_list = []
            if jd.skills:
                try:
                    skills_list = json.loads(jd.skills)
                except Exception:
                    skills_list = []

            jd_response = JobDescriptionResponse(
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
            
            recommend_items.append(
                JobRecommendItem(
                    jd=jd_response,
                    match_score=match_score
                )
            )

        # Sắp xếp danh sách gợi ý giảm dần theo match_score
        recommend_items.sort(key=lambda x: x.match_score, reverse=True)

        # Trích xuất top 'limit' kết quả phù hợp nhất
        final_recommend_items = recommend_items[:limit]

        # ⑤ Nếu có cv_analysis_id, lưu kết quả gợi ý vào bảng liên kết
        if cv_analysis_id and final_recommend_items:
            recommendations_to_save = [
                {
                    "jd_id": item.jd.id,
                    "match_score": item.match_score
                }
                for item in final_recommend_items
            ]
            # Xóa các gợi ý cũ (nếu có) trước khi tạo mới để tránh trùng lặp
            from database.models import AnalysisRecommendation
            await db.execute(
                select(AnalysisRecommendation).where(AnalysisRecommendation.cv_analysis_id == cv_analysis_id)
            )
            await job_repo.save_recommendations(db, cv_analysis_id, recommendations_to_save)

        return final_recommend_items

    # ============================================================
    # 4. Saved Jobs
    # ============================================================
    @staticmethod
    async def save_job(db: AsyncSession, user_id: int, jd_id: int) -> SavedJob:
        # Kiểm tra Job có tồn tại không
        jd = await job_repo.get_jd_by_id(db, jd_id)
        if not jd:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy thông tin công việc."
            )

        # Kiểm tra xem đã lưu chưa
        existing = await job_repo.get_saved_job_by_jd_id(db, user_id, jd_id)
        if existing:
            return existing

        # Tính toán match score bằng Cosine Similarity
        # Lấy CV mới nhất của User
        result = await db.execute(
            select(CVUpload).where(CVUpload.user_id == user_id).order_by(CVUpload.created_at.desc()).limit(1)
        )
        latest_cv = result.scalar_one_or_none()
        
        match_score = None
        if latest_cv and latest_cv.embedding is not None and jd.embedding is not None:
            similarity = cosine_similarity(latest_cv.embedding, jd.embedding)
            cv_summary = latest_cv.summary
            if not cv_summary:
                prompt = CV_SUMMARY_PROMPT.format(extracted_text=latest_cv.extracted_text or "")
                try:
                    cv_summary = await asyncio.to_thread(ai_service.generate_text, prompt)
                except Exception:
                    cv_summary = latest_cv.filename
                await job_repo.update_cv_summary_and_embedding(db, latest_cv.id, cv_summary, latest_cv.embedding)
            match_score = calculate_match_score(similarity, cv_summary, jd)

        return await job_repo.save_job(db, user_id, jd_id, match_score)

    @staticmethod
    async def get_saved_jobs(db: AsyncSession, user_id: int) -> List[SavedJobResponse]:
        saved_list = await job_repo.get_saved_jobs(db, user_id)
        
        responses = []
        for item in saved_list:
            jd = item.job_description
            import json
            skills_list = []
            if jd.skills:
                try:
                    skills_list = json.loads(jd.skills)
                except Exception:
                    skills_list = []

            jd_res = JobDescriptionResponse(
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
            
            responses.append(
                SavedJobResponse(
                    id=item.id,
                    jd=jd_res,
                    match_score=item.match_score,
                    created_at=item.created_at
                )
            )
        return responses

    @staticmethod
    async def delete_saved_job(db: AsyncSession, saved_id: int, user_id: int) -> bool:
        return await job_repo.delete_saved_job(db, saved_id, user_id)

job_service = JobService()
