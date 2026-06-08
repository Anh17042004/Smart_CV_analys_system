from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from schemas.job import JobRecommendItem

class CVUploadResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    created_at: datetime
    model_config = ConfigDict(
        from_attributes=True
    )


class AnalysisRequest(BaseModel):
    cv_id: int
    job_description: Optional[str] = None  # Mô tả công việc (Tùy chọn)


class SkillsAnalysis(BaseModel):
    matched_skills: List[str]
    missing_skills: List[str]
    match_percentage: float


class JobMatch(BaseModel):
    match_percentage: float
    gaps: List[str]


class RecommendedCourse(BaseModel):
    name: str
    provider: str
    skills: List[str]


class AnalysisResult(BaseModel):
    target_field: str  # Lĩnh vực do AI tự nhận diện
    target_role: str   # Vị trí công việc do AI tự nhận diện
    resume_score: int
    ats_score: int
    strengths: List[str]
    weaknesses: List[str]
    improvements: List[str]
    skills_analysis: SkillsAnalysis
    job_match: Optional[JobMatch] = None
    recommended_courses: List[RecommendedCourse]
    detailed_feedback: str


class CVAnalysisResponse(BaseModel):
    id: int
    cv_id: int
    user_id: int
    target_field: Optional[str] = None
    target_role: Optional[str] = None
    job_description: Optional[str] = None
    resume_score: Optional[int] = None
    ats_score: Optional[int] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    improvements: Optional[List[str]] = None
    skills_analysis: Optional[SkillsAnalysis] = None
    job_match: Optional[JobMatch] = None
    recommended_courses: Optional[List[RecommendedCourse]] = None
    detailed_feedback: Optional[str] = None
    recommendations: Optional[List[JobRecommendItem]] = None   # ✨ Gợi ý việc làm
    created_at: datetime
    model_config = ConfigDict(
        from_attributes=True
    )


class BatchDeleteRequest(BaseModel):
    analysis_ids: List[int]


class JDExtractResponse(BaseModel):
    text: str
    filename: str