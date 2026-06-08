from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class InterviewStartRequest(BaseModel):
    field: str = Field(..., description="Lĩnh vực phỏng vấn, ví dụ: IT, Marketing, Design...")
    level: str = Field(..., description="Cấp bậc: Intern, Fresher, Junior, Middle, Senior...")
    interview_type: str = Field(..., description="Loại phỏng vấn: HR, Technical, English...")
    response_mode: str = Field("Text", description="Hình thức: Text hoặc Voice")
    language: str = Field("Vietnamese", description="Ngôn ngữ phỏng vấn: Vietnamese hoặc English")
    total_questions: int = Field(5, ge=1, le=10, description="Tổng số câu hỏi")
    cv_id: Optional[int] = Field(None, description="ID của CV để làm ngữ cảnh")
    jd_id: Optional[int] = Field(None, description="ID của JD mẫu để làm ngữ cảnh")
    custom_jd: Optional[str] = Field(None, description="Mô tả công việc tùy chỉnh")

class AnswerDetailResponse(BaseModel):
    id: int
    session_id: int
    question_number: int
    question_text: str
    answer_text: Optional[str] = None
    content_score: Optional[float] = None
    structure_score: Optional[float] = None
    communication_score: Optional[float] = None
    confidence_score: Optional[float] = None
    overall_score: Optional[float] = None
    ai_feedback: Optional[str] = None
    suggested_answer: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class InterviewSessionStartResponse(BaseModel):
    session_id: int
    first_question: AnswerDetailResponse

class InterviewAnswerSubmit(BaseModel):
    session_id: int
    question_number: int
    answer_text: str

class InterviewAnswerSubmitResponse(BaseModel):
    evaluation: AnswerDetailResponse
    next_question: Optional[AnswerDetailResponse] = None
    is_completed: bool

class InterviewSessionResponse(BaseModel):
    id: int
    user_id: int
    field: Optional[str] = None
    level: Optional[str] = None
    interview_type: Optional[str] = None
    response_mode: Optional[str] = None
    language: Optional[str] = None
    total_questions: int
    overall_score: Optional[float] = None
    scores_by_category: Optional[Any] = None # can be JSON string or parsed dict
    strengths: Optional[Any] = None
    improvements: Optional[Any] = None
    overall_feedback: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    answers: List[AnswerDetailResponse] = []

    class Config:
        from_attributes = True
