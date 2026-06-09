import json
import asyncio
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import InterviewSession, InterviewAnswer
from database.repositories.interview_repo import interview_repo
from database.repositories.cv_repo import cv_repo
from database.repositories.job_repo import job_repo
from services.ai_service import ai_service
from schemas.interview import InterviewStartRequest, AnswerDetailResponse, QuestionEvaluationResult, InterviewSummaryResult
from prompts.interview import (
    GENERATOR_PROMPT_TEMPLATE,
    EVALUATION_PROMPT_TEMPLATE,
    SUMMARY_PROMPT_TEMPLATE
)

class InterviewService:
    async def start_session(
        self,
        db: AsyncSession,
        user_id: int,
        req: InterviewStartRequest
    ) -> Dict[str, Any]:
        # 1. Khởi tạo session trong DB
        session = await interview_repo.create_session(
            db=db,
            user_id=user_id,
            field=req.field,
            level=req.level,
            interview_type=req.interview_type,
            response_mode=req.response_mode,
            total_questions=req.total_questions,
            language=req.language,
            cv_id=req.cv_id,
            jd_id=req.jd_id,
            custom_jd=req.custom_jd
        )

        # 2. Thu thập ngữ cảnh CV
        context_cv = ""
        if req.cv_id:
            cv_upload = await cv_repo.get_upload_by_id(db, req.cv_id, user_id)
            if cv_upload and cv_upload.extracted_text:
                context_cv = f"Nội dung CV của ứng viên:\n---\n{cv_upload.extracted_text}\n---\n"

        # 3. Thu thập ngữ cảnh JD
        context_jd = ""
        if req.jd_id:
            jd_desc = await job_repo.get_jd_by_id(db, req.jd_id)
            if jd_desc:
                context_jd = f"Yêu cầu công việc (JD):\n---\nTiêu đề: {jd_desc.title}\nCông ty: {jd_desc.company}\nMô tả: {jd_desc.description}\n---\n"
        elif req.custom_jd:
            context_jd = f"Yêu cầu công việc (JD) tự nhập:\n---\n{req.custom_jd}\n---\n"

        # 4. Tạo câu hỏi đầu tiên
        chat_history = "(Bắt đầu cuộc phỏng vấn. Ứng viên vừa vào phòng phỏng vấn)"
        lang_str = "Tiếng Anh" if session.language == "English" else "Tiếng Việt"
        prompt = GENERATOR_PROMPT_TEMPLATE.format(
            field=req.field,
            level=req.level,
            interview_type=req.interview_type,
            context_cv=context_cv,
            context_jd=context_jd,
            chat_history=chat_history,
            next_question_number=1,
            total_questions=req.total_questions,
            language=lang_str
        )

        first_question_text = await asyncio.to_thread(ai_service.generate_text, prompt)
        if not first_question_text:
            first_question_text = "Xin chào bạn, chúng ta bắt đầu phỏng vấn nhé. Hãy giới thiệu một chút về bản thân bạn?"

        # 5. Lưu câu hỏi đầu tiên vào DB
        first_answer_obj = await interview_repo.create_answer(
            db=db,
            session_id=session.id,
            question_number=1,
            question_text=first_question_text
        )

        return {
            "session_id": session.id,
            "first_question": AnswerDetailResponse.from_orm(first_answer_obj)
        }

    async def evaluate_single_answer(
        self,
        ans: InterviewAnswer,
        session: InterviewSession,
        lang_str: str
    ) -> None:
        try:
            eval_prompt = EVALUATION_PROMPT_TEMPLATE.format(
                field=session.field or "Chung",
                level=session.level or "Fresher/Junior",
                interview_type=session.interview_type or "General",
                question_text=ans.question_text,
                answer_text=ans.answer_text,
                language=lang_str
            )
            evaluation_result = await asyncio.to_thread(ai_service.generate_json, eval_prompt, QuestionEvaluationResult.model_json_schema())
        except Exception as e:
            from core.logger import logger
            logger.error(f"❌ Lỗi đánh giá câu hỏi {ans.question_number} của AI: {str(e)}")
            evaluation_result = {
                "content_score": 5.0,
                "structure_score": 5.0,
                "communication_score": 5.0,
                "confidence_score": 5.0,
                "overall_score": 5.0,
                "ai_feedback": "Không thể phân tích tự động bằng AI tại thời điểm này do lỗi hệ thống.",
                "suggested_answer": "Vui lòng xem lại kiến thức chuyên môn cho câu hỏi này."
            }
            
        ans.content_score = evaluation_result.get("content_score", 5.0)
        ans.structure_score = evaluation_result.get("structure_score", 5.0)
        ans.communication_score = evaluation_result.get("communication_score", 5.0)
        ans.confidence_score = evaluation_result.get("confidence_score", 5.0)
        ans.overall_score = evaluation_result.get("overall_score", 5.0)
        ans.ai_feedback = evaluation_result.get("ai_feedback", "")
        ans.suggested_answer = evaluation_result.get("suggested_answer", "")

    async def submit_answer(
        self,
        db: AsyncSession,
        user_id: int,
        session_id: int,
        question_number: int,
        answer_text: str
    ) -> Dict[str, Any]:
        # 1. Lấy thông tin session
        session = await interview_repo.get_session_by_id(db, session_id, user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy phiên phỏng vấn."
            )

        if session.completed_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phiên phỏng vấn này đã hoàn thành trước đó."
            )

        # 2. Lấy câu hỏi hiện tại
        current_answer_obj = await interview_repo.get_answer_by_number(db, session_id, question_number)
        if not current_answer_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không tìm thấy câu hỏi số {question_number}."
            )

        if current_answer_obj.answer_text is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Câu hỏi này đã được trả lời."
            )

        # 3. Lưu câu trả lời trực tiếp vào DB mà chưa chấm điểm ngay
        current_answer_obj.answer_text = answer_text
        await db.commit()
        await db.refresh(current_answer_obj)

        is_completed = (question_number >= session.total_questions)
        next_question_resp = None
        lang_str = "Tiếng Anh" if session.language == "English" else "Tiếng Việt"

        if is_completed:
            # 4. Đánh giá tất cả câu trả lời cùng lúc ở cuối buổi
            refreshed_session = await interview_repo.get_session_by_id(db, session_id, user_id)
            
            # Chạy song song toàn bộ đánh giá bằng asyncio.gather + asyncio.to_thread
            evaluation_tasks = [
                self.evaluate_single_answer(ans, refreshed_session, lang_str) 
                for ans in refreshed_session.answers
            ]
            await asyncio.gather(*evaluation_tasks)
            
            # Commit điểm số và feedbacks sau khi đánh giá xong
            await db.commit()
            
            # Xây dựng báo cáo tổng kết
            interview_details = ""
            total_score_sum = 0.0
            cat_scores = {"content": 0.0, "structure": 0.0, "communication": 0.0, "confidence": 0.0}
            
            for ans in refreshed_session.answers:
                interview_details += f"Q{ans.question_number}: {ans.question_text}\n"
                interview_details += f"A{ans.question_number}: {ans.answer_text}\n"
                interview_details += f"Feedback: {ans.ai_feedback}\n"
                interview_details += f"Score: {ans.overall_score}\n\n"
                total_score_sum += ans.overall_score or 0.0
                cat_scores["content"] += ans.content_score or 0.0
                cat_scores["structure"] += ans.structure_score or 0.0
                cat_scores["communication"] += ans.communication_score or 0.0
                cat_scores["confidence"] += ans.confidence_score or 0.0
                
            n = len(refreshed_session.answers)
            if n > 0:
                for key in cat_scores:
                    cat_scores[key] = round(cat_scores[key] / n, 2)
            
            summary_prompt = SUMMARY_PROMPT_TEMPLATE.format(
                field=session.field or "Chung",
                level=session.level or "Fresher/Junior",
                interview_type=session.interview_type or "General",
                interview_details=interview_details,
                language=lang_str
            )
            
            summary_result = await asyncio.to_thread(ai_service.generate_json, summary_prompt, InterviewSummaryResult.model_json_schema())
            
            # Cập nhật thông tin tổng hợp vào session
            await interview_repo.complete_session(
                db=db,
                session_id=session.id,
                overall_score=summary_result.get("overall_score", round(total_score_sum / n, 2) if n > 0 else 0.0),
                scores_by_category=summary_result.get("scores_by_category", cat_scores),
                strengths=summary_result.get("strengths", []),
                improvements=summary_result.get("improvements", []),
                overall_feedback=summary_result.get("overall_feedback", "Hoàn thành phỏng vấn.")
            )
            
            # Đảm bảo refresh lại thực thể câu hỏi cuối để trả về đầy đủ điểm số
            await db.refresh(current_answer_obj)
        else:
            # 5. Tạo câu hỏi tiếp theo
            refreshed_session = await interview_repo.get_session_by_id(db, session_id, user_id)
            
            chat_history = ""
            for ans in refreshed_session.answers:
                if ans.answer_text:
                    chat_history += f"Người phỏng vấn: {ans.question_text}\nỨng viên: {ans.answer_text}\n"
            
            # Xây dựng ngữ cảnh CV/JD
            context_cv = ""
            if session.cv_id:
                cv_upload = await cv_repo.get_upload_by_id(db, session.cv_id, user_id)
                if cv_upload and cv_upload.extracted_text:
                    context_cv = f"Nội dung CV của ứng viên:\n---\n{cv_upload.extracted_text}\n---\n"

            context_jd = ""
            if session.jd_id:
                jd_desc = await job_repo.get_jd_by_id(db, session.jd_id)
                if jd_desc:
                    context_jd = f"Yêu cầu công việc (JD):\n---\nTiêu đề: {jd_desc.title}\nCông ty: {jd_desc.company}\nMô tả: {jd_desc.description}\n---\n"
            elif session.custom_jd:
                context_jd = f"Yêu cầu công việc (JD) tự nhập:\n---\n{session.custom_jd}\n---\n"
            
            # Tạo prompt cho câu hỏi tiếp theo
            next_num = question_number + 1
            gen_prompt = GENERATOR_PROMPT_TEMPLATE.format(
                field=session.field or "Chung",
                level=session.level or "Junior",
                interview_type=session.interview_type or "HR",
                context_cv=context_cv,
                context_jd=context_jd,
                chat_history=chat_history,
                next_question_number=next_num,
                total_questions=session.total_questions,
                language=lang_str
            )
            
            next_question_text = await asyncio.to_thread(ai_service.generate_text, gen_prompt)
            if not next_question_text:
                next_question_text = f"Câu hỏi tiếp theo dành cho bạn: Hãy chia sẻ về một thử thách kỹ thuật lớn nhất bạn từng gặp và cách bạn giải quyết nó?"
                
            # Lưu câu hỏi tiếp theo vào DB
            next_answer_obj = await interview_repo.create_answer(
                db=db,
                session_id=session.id,
                question_number=next_num,
                question_text=next_question_text
            )
            next_question_resp = AnswerDetailResponse.from_orm(next_answer_obj)

        return {
            "evaluation": AnswerDetailResponse.from_orm(current_answer_obj),
            "next_question": next_question_resp,
            "is_completed": is_completed
        }


    async def get_session(self, db: AsyncSession, session_id: int, user_id: int) -> Optional[InterviewSession]:
        return await interview_repo.get_session_by_id(db, session_id, user_id)

    async def get_history(self, db: AsyncSession, user_id: int) -> List[InterviewSession]:
        return await interview_repo.get_user_sessions(db, user_id)

    async def delete_session(self, db: AsyncSession, session_id: int, user_id: int) -> bool:
        return await interview_repo.delete_session(db, session_id, user_id)

    def format_session_response(self, session: InterviewSession) -> Any:
        if not session:
            return None
        
        scores_by_category = None
        if session.scores_by_category:
            try:
                scores_by_category = json.loads(session.scores_by_category)
            except Exception:
                scores_by_category = {}

        strengths = []
        if session.strengths:
            try:
                strengths = json.loads(session.strengths)
            except Exception:
                strengths = []

        improvements = []
        if session.improvements:
            try:
                improvements = json.loads(session.improvements)
            except Exception:
                improvements = []

        answers_sorted = sorted(session.answers, key=lambda x: x.question_number)
        answers_list = [AnswerDetailResponse.from_orm(ans) for ans in answers_sorted]

        from schemas.interview import InterviewSessionResponse
        return InterviewSessionResponse(
            id=session.id,
            user_id=session.user_id,
            field=session.field,
            level=session.level,
            interview_type=session.interview_type,
            response_mode=session.response_mode,
            language=session.language,
            total_questions=session.total_questions,
            overall_score=session.overall_score,
            scores_by_category=scores_by_category,
            strengths=strengths,
            improvements=improvements,
            overall_feedback=session.overall_feedback,
            started_at=session.started_at,
            completed_at=session.completed_at,
            answers=answers_list
        )

interview_service = InterviewService()

