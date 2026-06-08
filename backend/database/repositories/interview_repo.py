import json
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from database.models import InterviewSession, InterviewAnswer

class InterviewRepository:
    @staticmethod
    async def create_session(
        db: AsyncSession,
        user_id: int,
        field: str,
        level: str,
        interview_type: str,
        response_mode: str,
        total_questions: int,
        language: str = "Vietnamese",
        cv_id: Optional[int] = None,
        jd_id: Optional[int] = None,
        custom_jd: Optional[str] = None
    ) -> InterviewSession:
        db_session = InterviewSession(
            user_id=user_id,
            field=field,
            level=level,
            interview_type=interview_type,
            response_mode=response_mode,
            language=language,
            total_questions=total_questions,
            cv_id=cv_id,
            jd_id=jd_id,
            custom_jd=custom_jd
        )
        db.add(db_session)
        await db.commit()
        await db.refresh(db_session)
        return db_session

    @staticmethod
    async def get_session_by_id(
        db: AsyncSession,
        session_id: int,
        user_id: int
    ) -> Optional[InterviewSession]:
        """Lấy chi tiết một phiên phỏng vấn kèm danh sách các câu hỏi/trả lời."""
        result = await db.execute(
            select(InterviewSession)
            .options(joinedload(InterviewSession.answers))
            .where(InterviewSession.id == session_id, InterviewSession.user_id == user_id)
        )
        session = result.unique().scalar_one_or_none()
        if session:
            # Sắp xếp các câu trả lời/câu hỏi theo question_number
            session.answers.sort(key=lambda x: x.question_number)
        return session

    @staticmethod
    async def get_user_sessions(
        db: AsyncSession,
        user_id: int
    ) -> List[InterviewSession]:
        """Lấy danh sách lịch sử các phiên phỏng vấn của một user."""
        result = await db.execute(
            select(InterviewSession)
            .where(InterviewSession.user_id == user_id)
            .order_by(InterviewSession.started_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def delete_session(
        db: AsyncSession,
        session_id: int,
        user_id: int
    ) -> bool:
        """Xóa một phiên phỏng vấn."""
        result = await db.execute(
            select(InterviewSession)
            .where(InterviewSession.id == session_id, InterviewSession.user_id == user_id)
        )
        session = result.scalar_one_or_none()
        if session:
            await db.delete(session)
            await db.commit()
            return True
        return False

    @staticmethod
    async def create_answer(
        db: AsyncSession,
        session_id: int,
        question_number: int,
        question_text: str
    ) -> InterviewAnswer:
        """Tạo mới một câu hỏi cho phiên phỏng vấn."""
        db_answer = InterviewAnswer(
            session_id=session_id,
            question_number=question_number,
            question_text=question_text
        )
        db.add(db_answer)
        await db.commit()
        await db.refresh(db_answer)
        return db_answer

    @staticmethod
    async def get_answer_by_number(
        db: AsyncSession,
        session_id: int,
        question_number: int
    ) -> Optional[InterviewAnswer]:
        """Lấy câu hỏi theo số thứ tự trong phiên."""
        result = await db.execute(
            select(InterviewAnswer)
            .where(InterviewAnswer.session_id == session_id, InterviewAnswer.question_number == question_number)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_answer_evaluation(
        db: AsyncSession,
        answer_id: int,
        answer_text: str,
        evaluation_result: dict
    ) -> InterviewAnswer:
        """Cập nhật câu trả lời và đánh giá từ AI cho câu hỏi cụ thể."""
        result = await db.execute(
            select(InterviewAnswer).where(InterviewAnswer.id == answer_id)
        )
        db_answer = result.scalar_one()
        
        db_answer.answer_text = answer_text
        db_answer.content_score = evaluation_result.get("content_score", 0.0)
        db_answer.structure_score = evaluation_result.get("structure_score", 0.0)
        db_answer.communication_score = evaluation_result.get("communication_score", 0.0)
        db_answer.confidence_score = evaluation_result.get("confidence_score", 0.0)
        db_answer.overall_score = evaluation_result.get("overall_score", 0.0)
        db_answer.ai_feedback = evaluation_result.get("ai_feedback", "")
        db_answer.suggested_answer = evaluation_result.get("suggested_answer", "")
        
        await db.commit()
        await db.refresh(db_answer)
        return db_answer

    @staticmethod
    async def complete_session(
        db: AsyncSession,
        session_id: int,
        overall_score: float,
        scores_by_category: dict,
        strengths: List[str],
        improvements: List[str],
        overall_feedback: str
    ) -> InterviewSession:
        """Hoàn thành phiên phỏng vấn và lưu kết quả tổng kết."""
        result = await db.execute(
            select(InterviewSession).where(InterviewSession.id == session_id)
        )
        session = result.scalar_one()
        
        session.overall_score = overall_score
        session.scores_by_category = json.dumps(scores_by_category)
        session.strengths = json.dumps(strengths)
        session.improvements = json.dumps(improvements)
        session.overall_feedback = overall_feedback
        session.completed_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(session)
        return session

interview_repo = InterviewRepository()
