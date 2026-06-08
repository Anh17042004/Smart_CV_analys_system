import asyncio
import sys
import io
from sqlalchemy import select

# Set stdout/stderr encoding to UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add backend folder to sys.path
sys.path.append(r"D:\analzyz_cv_ai\Smart-AI-Resume-Analyzer\CV_AI\backend")

from database.connection import AsyncSessionLocal
from database.models import User
from schemas.interview import InterviewStartRequest
from services.interview_service import interview_service

async def test_interview_flow():
    print("🚀 Bắt đầu kiểm thử luồng Phỏng Vấn Giả Lập...")
    async with AsyncSessionLocal() as db:
        # 1. Tìm hoặc tạo User test
        user_result = await db.execute(select(User).limit(1))
        user = user_result.scalar_one_or_none()
        if not user:
            print("Không tìm thấy user. Đang tạo dummy user...")
            user = User(email="interview_tester@example.com", hashed_password="pwd", full_name="Interview Tester")
            db.add(user)
            await db.commit()
            await db.refresh(user)
        
        print(f"👤 Sử dụng User ID: {user.id}")

        # 2. Khởi tạo phiên phỏng vấn mới (General Interview)
        start_req = InterviewStartRequest(
            field="AI Engineer",
            level="Intern",
            interview_type="Technical",
            response_mode="Text",
            total_questions=3, # test với 3 câu hỏi cho nhanh
            cv_id=None,
            jd_id=None,
            custom_jd="Yêu cầu ứng viên thành thạo Python, FastAPI và tối ưu cơ sở dữ liệu PostgreSQL."
        )

        print("\n⏳ Đang khởi tạo phòng phỏng vấn và sinh câu hỏi 1...")
        start_result = await interview_service.start_session(db, user.id, start_req)
        session_id = start_result["session_id"]
        first_q = start_result["first_question"]
        print(f"✅ Đã tạo Session ID: {session_id}")
        print(f"🤖 AI [Q1]: {first_q.question_text}")

        # 3. Trả lời câu hỏi 1
        print("\n💬 Đang gửi câu trả lời cho Q1...")
        ans_1_text = "Tôi là lập trình viên Junior Python. Tôi có kinh nghiệm làm việc với FastAPI, SQLAlchemy để thiết kế hệ thống backend RESTful API tối ưu và bảo mật tốt."
        result_1 = await interview_service.submit_answer(db, user.id, session_id, 1, ans_1_text)
        print(f"📊 Kết quả đánh giá Q1:")
        print(f"   - Điểm tổng quan: {result_1['evaluation'].overall_score}")
        print(f"   - Nhận xét: {result_1['evaluation'].ai_feedback}")
        print(f"   - Câu trả lời mẫu gợi ý: {result_1['evaluation'].suggested_answer}")
        
        # Lấy câu hỏi 2
        next_q = result_1["next_question"]
        print(f"🤖 AI [Q2]: {next_q.question_text}")

        # 4. Trả lời câu hỏi 2
        print("\n💬 Đang gửi câu trả lời cho Q2...")
        ans_2_text = "Tôi thường viết code dễ hiểu, chia nhỏ hàm và viết unit test bằng pytest để đảm bảo tính đúng đắn trước khi bàn giao."
        result_2 = await interview_service.submit_answer(db, user.id, session_id, 2, ans_2_text)
        print(f"📊 Kết quả đánh giá Q2:")
        print(f"   - Điểm tổng quan: {result_2['evaluation'].overall_score}")
        
        # Lấy câu hỏi 3
        next_q3 = result_2["next_question"]
        print(f"🤖 AI [Q3]: {next_q3.question_text}")

        # 5. Trả lời câu hỏi 3 (câu hỏi cuối cùng)
        print("\n💬 Đang gửi câu trả lời cho Q3 (Câu hỏi cuối cùng)...")
        ans_3_text = "Tôi chưa có nhiều cơ hội tự thiết kế hệ thống lớn, nhưng tôi đã tham gia triển khai các cấu trúc cơ sở dữ liệu quan hệ tối ưu hóa index."
        result_3 = await interview_service.submit_answer(db, user.id, session_id, 3, ans_3_text)
        print(f"📊 Kết quả đánh giá Q3:")
        print(f"   - Điểm tổng quan: {result_3['evaluation'].overall_score}")
        print(f"🎉 Trạng thái hoàn thành: {result_3['is_completed']}")

        # 6. Đọc thông tin kết quả phỏng vấn tổng hợp
        print("\n⏳ Đang tải báo cáo kết quả phỏng vấn tổng hợp...")
        session_obj = await interview_service.get_session(db, session_id, user.id)
        session_formatted = interview_service.format_session_response(session_obj)
        print(f"🏆 Điểm phỏng vấn tổng kết: {session_formatted.overall_score}")
        print(f"✨ Điểm các tiêu chí: {session_formatted.scores_by_category}")
        print(f"🔥 Điểm mạnh: {session_formatted.strengths}")
        print(f"💡 Cần cải thiện: {session_formatted.improvements}")
        print(f"📝 Nhận xét chung: {session_formatted.overall_feedback}")

        # 7. Dọn dẹp
        print("\n🧹 Đang xóa session test...")
        await interview_service.delete_session(db, session_id, user.id)
        print("🎉 Kiểm thử hoàn thành thành công!")

if __name__ == "__main__":
    asyncio.run(test_interview_flow())
