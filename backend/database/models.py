"""
CV MENTOR — Database ORM Models
==================================
8 bảng chính thức của hệ thống (sử dụng PostgreSQL + pgvector)
Dùng SQLAlchemy 2.0 Mapped style (async compatible)
"""

from sqlalchemy import Integer, String, Text, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from datetime import datetime, timezone
from database.connection import Base


# ============================================================
# 1. USERS — Quản lý tài khoản (Mục 2.1 & 2.2)
# ============================================================
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="user", nullable=False)  # "user" | "admin"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    cv_uploads: Mapped[list["CVUpload"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    cv_analyses: Mapped[list["CVAnalysis"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    saved_jobs: Mapped[list["SavedJob"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    interview_sessions: Mapped[list["InterviewSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")


# ============================================================
# 2. CV_UPLOADS — File CV gốc (Mục 3.1)
# ============================================================
class CVUpload(Base):
    __tablename__ = "cv_uploads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "pdf" | "docx"
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)     # bytes
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)        # Nội dung trích xuất
    
    # Vector embedding cache
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)               # AI tóm tắt CV
    embedding = mapped_column(Vector(768), nullable=True)                          # Vector 768D đại diện CV

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="cv_uploads")
    analyses: Mapped[list["CVAnalysis"]] = relationship(back_populates="cv_upload", cascade="all, delete-orphan")


# ============================================================
# 3. CV_ANALYSES — Kết quả phân tích CV (Mục 3.3 & 3.4)
# ============================================================
class CVAnalysis(Base):
    __tablename__ = "cv_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cv_id: Mapped[int] = mapped_column(Integer, ForeignKey("cv_uploads.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Input từ user (Mục 3.2)
    job_description: Mapped[str | None] = mapped_column(Text, nullable=True)       # JD paste vào (optional)

    # Kết quả AI phân tích
    resume_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_field: Mapped[str | None] = mapped_column(String(255), nullable=True)   # Lĩnh vực nghề nghiệp
    target_role: Mapped[str | None] = mapped_column(String(255), nullable=True)    # Vị trí cụ thể
    ats_score: Mapped[int | None] = mapped_column(Integer, nullable=True)          # 0-100
    strengths: Mapped[str | None] = mapped_column(Text, nullable=True)             # JSON: ["point1", "point2"]
    weaknesses: Mapped[str | None] = mapped_column(Text, nullable=True)            # JSON: ["point1", "point2"]
    improvements: Mapped[str | None] = mapped_column(Text, nullable=True)          # JSON: ["point1", "point2"]
    skills_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)       # JSON: {current, missing, match_%}
    job_match: Mapped[str | None] = mapped_column(Text, nullable=True)             # JSON: {match_%, gaps} (optional)
    recommended_courses: Mapped[str | None] = mapped_column(Text, nullable=True)   # JSON: [{name, url}]
    detailed_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)     # Nhận xét tổng thể

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="cv_analyses")
    cv_upload: Mapped["CVUpload"] = relationship(back_populates="analyses")
    recommendations: Mapped[list["AnalysisRecommendation"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan"
    )


# ============================================================
# 4. JOB_DESCRIPTIONS — Metadata JD & Vector Embedding (MỚI)
# ============================================================
class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    salary_range: Mapped[str | None] = mapped_column(String(100), nullable=True)
    experience: Mapped[str | None] = mapped_column(String(100), nullable=True)
    employment_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    skills: Mapped[str | None] = mapped_column(Text, nullable=True)                 # JSON: ["Python", "SQL"]
    description: Mapped[str] = mapped_column(Text, nullable=False)                  # Nội dung JD đầy đủ
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)                # AI tóm tắt JD
    
    # Vector embedding
    embedding = mapped_column(Vector(768), nullable=True)                          # Vector 768D của JD

    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    saved_jobs: Mapped[list["SavedJob"]] = relationship(back_populates="job_description", cascade="all, delete-orphan")
    recommendations: Mapped[list["AnalysisRecommendation"]] = relationship(
        back_populates="job_description", cascade="all, delete-orphan"
    )


# ============================================================
# 5. ANALYSIS_RECOMMENDATIONS — Bảng liên kết gợi ý việc làm (MỚI)
# ============================================================
class AnalysisRecommendation(Base):
    __tablename__ = "analysis_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cv_analysis_id: Mapped[int] = mapped_column(Integer, ForeignKey("cv_analyses.id", ondelete="CASCADE"), nullable=False)
    jd_id: Mapped[int] = mapped_column(Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False)
    match_score: Mapped[float | None] = mapped_column(Float, nullable=True)         # Điểm tương đồng %
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    analysis: Mapped["CVAnalysis"] = relationship(back_populates="recommendations")
    job_description: Mapped["JobDescription"] = relationship(back_populates="recommendations")


# ============================================================
# 6. SAVED_JOBS — Công việc đã lưu (ĐÃ SỬA FK)
# ============================================================
class SavedJob(Base):
    __tablename__ = "saved_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    jd_id: Mapped[int] = mapped_column(Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False)
    match_score: Mapped[float | None] = mapped_column(Float, nullable=True)         # Điểm tương đồng tại lúc lưu
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="saved_jobs")
    job_description: Mapped["JobDescription"] = relationship(back_populates="saved_jobs")


# ============================================================
# 7. INTERVIEW_SESSIONS — Phiên phỏng vấn (Mục 5.1 & 5.5)
# ============================================================
class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    field: Mapped[str | None] = mapped_column(String(255), nullable=True)          # Lĩnh vực
    level: Mapped[str | None] = mapped_column(String(50), nullable=True)           # Intern / Fresher / Junior
    interview_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # HR / Technical / English
    response_mode: Mapped[str | None] = mapped_column(String(50), nullable=True)   # Text / Voice
    language: Mapped[str | None] = mapped_column(String(50), default="Vietnamese", nullable=True) # Ngôn ngữ phỏng vấn: Vietnamese / English
    total_questions: Mapped[int] = mapped_column(Integer, default=5)
    cv_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("cv_uploads.id", ondelete="SET NULL"), nullable=True)
    jd_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("job_descriptions.id", ondelete="SET NULL"), nullable=True)
    custom_jd: Mapped[str | None] = mapped_column(Text, nullable=True)


    # Kết quả tổng kết
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    scores_by_category: Mapped[str | None] = mapped_column(Text, nullable=True)   # JSON
    strengths: Mapped[str | None] = mapped_column(Text, nullable=True)             # JSON
    improvements: Mapped[str | None] = mapped_column(Text, nullable=True)          # JSON
    overall_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="interview_sessions")
    answers: Mapped[list["InterviewAnswer"]] = relationship(back_populates="session", cascade="all, delete-orphan")


# ============================================================
# 8. INTERVIEW_ANSWERS — Chi tiết từng câu Q&A (Mục 5.2-5.4)
# ============================================================
class InterviewAnswer(Base):
    __tablename__ = "interview_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    question_number: Mapped[int] = mapped_column(Integer, nullable=False)          # Thứ tự: 1, 2, 3...
    question_text: Mapped[str] = mapped_column(Text, nullable=False)               # Câu hỏi AI đưa ra
    answer_text: Mapped[str | None] = mapped_column(Text, nullable=True)           # Câu trả lời user

    # Điểm thành phần
    content_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    structure_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    communication_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    ai_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)           # Nhận xét AI
    suggested_answer: Mapped[str | None] = mapped_column(Text, nullable=True)      # Câu trả lời mẫu

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    session: Mapped["InterviewSession"] = relationship(back_populates="answers")
