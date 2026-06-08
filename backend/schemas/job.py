from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

# --- Nhập JD ---
class JobDescriptionCreate(BaseModel):
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None
    experience: Optional[str] = None
    employment_type: Optional[str] = None
    skills: Optional[List[str]] = None
    description: str
    source_url: Optional[str] = None


class JobDescriptionResponse(BaseModel):
    id: int
    title: str
    company: Optional[str]
    location: Optional[str]
    salary_range: Optional[str]
    experience: Optional[str]
    employment_type: Optional[str]
    skills: Optional[List[str]] = None
    description: str
    summary: Optional[str]
    source_url: Optional[str]
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True
    )


# --- Job Search (Từ khóa) ---
class JobSearchRequest(BaseModel):
    keyword: str
    location: Optional[str] = None


class JobSearchResponse(BaseModel):
    total: int
    results: List[JobDescriptionResponse]


# --- Job Recommend (Vector search) ---
class JobRecommendItem(BaseModel):
    jd: JobDescriptionResponse
    match_score: float                  # Điểm tương đồng % (0-100)


class JobRecommendResponse(BaseModel):
    cv_id: int
    total: int
    recommendations: List[JobRecommendItem]


# --- Saved Jobs ---
class SavedJobCreate(BaseModel):
    jd_id: int


class SavedJobResponse(BaseModel):
    id: int
    jd: JobDescriptionResponse
    match_score: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
