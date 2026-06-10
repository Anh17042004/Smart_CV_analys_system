import io
import os
import json
import asyncio
from typing import List
import pdfplumber
from docx import Document
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# ReportLab imports
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from core.logger import logger
from database.models import CVUpload, CVAnalysis
from database.repositories.cv_repo import cv_repo
from services.ai_service import ai_service
from schemas.cv import CVUploadResponse, CVAnalysisResponse, AnalysisResult
from prompts.cv_analysis import CV_ANALYSIS_PROMPT  # Import prompt từ file riêng biệt

# Thư mục lưu trữ file CV upload vật lý
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

class CVService:
    def extract_text(self, file_bytes: bytes, file_type: str) -> str:
        """Trích xuất chữ từ file PDF hoặc DOCX."""
        try:
            if file_type == "pdf":
                text = ""
                with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                return text.strip()
            elif file_type == "docx":
                doc = Document(io.BytesIO(file_bytes))
                text = ""
                for para in doc.paragraphs:
                    text += para.text + "\n"
                return text.strip()
            else:
                raise ValueError("Định dạng file không được hỗ trợ.")
        except Exception as e:
            logger.error(f"❌ Lỗi trích xuất chữ: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không thể đọc nội dung file: {str(e)}"
            )

    async def upload_cv(self, db: AsyncSession, file: UploadFile, user_id: int) -> CVUploadResponse:
        """Upload file, lưu ổ đĩa, trích xuất text và lưu metadata DB."""
        filename = file.filename
        file_ext = filename.split(".")[-1].lower() if "." in filename else ""
        if file_ext not in ["pdf", "docx"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chỉ chấp nhận file định dạng .pdf hoặc .docx"
            )

        file_bytes = await file.read()
        file_size = len(file_bytes)
        
        # Giới hạn 10MB
        if file_size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dung lượng file không được vượt quá 10MB"
            )

        # Lưu file
        import uuid
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        with open(file_path, "wb") as f:
            f.write(file_bytes)

        # Tiến hành trích xuất chữ thô
        extracted_text = self.extract_text(file_bytes, file_ext)

        db_upload = await cv_repo.save_upload(
            db=db,
            user_id=user_id,
            filename=filename,
            file_path=file_path,
            file_type=file_ext,
            file_size=file_size,
            extracted_text=extracted_text,
        )

        return CVUploadResponse(
            id=db_upload.id,
            filename=db_upload.filename,
            file_type=db_upload.file_type,
            file_size=db_upload.file_size,
            created_at=db_upload.created_at
        )

    async def analyze_cv(self, db: AsyncSession, cv_id: int, user_id: int, job_description: str | None = None) -> CVAnalysisResponse:
        """Gửi nội dung CV và JD tới AI Ollama để thực hiện phân tích."""
        cv_upload = await cv_repo.get_upload_by_id(db, cv_id, user_id)
        if not cv_upload:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy file CV đã upload trong hệ thống."
            )

        extracted_text = cv_upload.extracted_text
        if not extracted_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nội dung file CV trống, không thể phân tích."
            )

        # Định dạng prompt từ file template bên ngoài
        prompt = CV_ANALYSIS_PROMPT.format(
            job_description=job_description or "Không cung cấp",
            extracted_text=extracted_text
        )

        logger.info(f"⏳ Đang gửi yêu cầu phân tích CV lên Ollama Cloud...")
        # Chạy trên thread pool để không chặn event loop ASGI khi có nhiều người dùng đồng thời
        ai_response = await asyncio.to_thread(
            ai_service.generate_json, prompt, AnalysisResult.model_json_schema()
        )
        logger.info(f"✅ Đã nhận được kết quả phân tích JSON sạch từ Ollama.")

        # Chuẩn hóa dữ liệu LLM trả về để tránh lỗi kiểu dữ liệu (vd: chuỗi thay vì danh sách)
        def ensure_list_of_strings(val) -> list[str]:
            if val is None:
                return []
            if isinstance(val, list):
                return [str(item).strip() for item in val if item is not None]
            if isinstance(val, str):
                if ',' in val:
                    return [item.strip() for item in val.split(',') if item.strip()]
                return [val.strip()]
            return [str(val).strip()]

        if isinstance(ai_response, dict):
            for field in ["strengths", "weaknesses", "improvements"]:
                if field in ai_response:
                    ai_response[field] = ensure_list_of_strings(ai_response[field])
            
            skills_analysis = ai_response.get("skills_analysis")
            if isinstance(skills_analysis, dict):
                skills_analysis["matched_skills"] = ensure_list_of_strings(skills_analysis.get("matched_skills", []))
                skills_analysis["missing_skills"] = ensure_list_of_strings(skills_analysis.get("missing_skills", []))
                if "match_percentage" in skills_analysis:
                    try:
                        skills_analysis["match_percentage"] = float(skills_analysis["match_percentage"])
                    except (ValueError, TypeError):
                        skills_analysis["match_percentage"] = 0.0
                ai_response["skills_analysis"] = skills_analysis

            job_match = ai_response.get("job_match")
            if isinstance(job_match, dict):
                job_match["gaps"] = ensure_list_of_strings(job_match.get("gaps", []))
                if "match_percentage" in job_match:
                    try:
                        job_match["match_percentage"] = float(job_match["match_percentage"])
                    except (ValueError, TypeError):
                        job_match["match_percentage"] = 0.0
                ai_response["job_match"] = job_match

            courses = ai_response.get("recommended_courses")
            if isinstance(courses, list):
                cleaned_courses = []
                for course in courses:
                    if isinstance(course, dict):
                        course["name"] = str(course.get("name", "")).strip()
                        course["provider"] = str(course.get("provider", "")).strip()
                        course["skills"] = ensure_list_of_strings(course.get("skills", []))
                        cleaned_courses.append(course)
                ai_response["recommended_courses"] = cleaned_courses

        # Ghi DB kết quả phân tích
        db_analysis = await cv_repo.save_analysis(
            db=db,
            cv_id=cv_id,
            user_id=user_id,
            job_description=job_description,
            analysis_result=ai_response
        )

        # Tự động tìm kiếm và gợi ý việc làm dựa trên CV
        from services.job_service import job_service
        recs = []
        try:
            recs = await job_service.recommend_jobs_for_cv(
                db=db,
                cv_id=cv_id,
                user_id=user_id,
                cv_analysis_id=db_analysis.id
            )
        except Exception as e:
            logger.error(f"❌ Lỗi tự động gợi ý việc làm khi phân tích CV: {e}")

        response_data = self._format_analysis(db_analysis)
        response_data.recommendations = recs
        return response_data

    async def get_history(self, db: AsyncSession, user_id: int) -> List[CVAnalysisResponse]:
        """Lấy toàn bộ lịch sử phân tích của user."""
        analyses = await cv_repo.get_user_analyses(db, user_id)
        return [self._format_analysis(a) for a in analyses]

    async def get_analysis_detail(self, db: AsyncSession, analysis_id: int, user_id: int) -> CVAnalysisResponse:
        """Lấy chi tiết một bản ghi phân tích cũ."""
        analysis = await cv_repo.get_analysis_by_id(db, analysis_id, user_id)
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy kết quả phân tích yêu cầu."
            )
        return self._format_analysis(analysis)

    async def delete_analysis(self, db: AsyncSession, analysis_id: int, user_id: int) -> bool:
        """Xóa một bản ghi phân tích CV theo ID và User ID."""
        return await cv_repo.delete_analysis(db, analysis_id, user_id)

    async def batch_delete_analyses(self, db: AsyncSession, analysis_ids: List[int], user_id: int) -> int:
        """Xóa hàng loạt các bản ghi phân tích CV theo danh sách ID và User ID."""
        return await cv_repo.batch_delete_analyses(db, analysis_ids, user_id)

    def _format_analysis(self, analysis: CVAnalysis) -> CVAnalysisResponse:
        """Helper giải nén các cột lưu dạng JSON String từ DB thành Python dict/list."""
        try:
            from schemas.job import JobDescriptionResponse, JobRecommendItem
            from sqlalchemy.inspection import inspect as sqla_inspect
            recommendations_list = []
            
            insp = sqla_inspect(analysis)
            if "recommendations" not in insp.unloaded:
                for rec in analysis.recommendations:
                    rec_insp = sqla_inspect(rec)
                    if "job_description" not in rec_insp.unloaded:
                        jd = rec.job_description
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
                        recommendations_list.append(
                            JobRecommendItem(
                                jd=jd_res,
                                match_score=rec.match_score
                            )
                        )

            def ensure_list_of_strings(val) -> list[str]:
                if val is None:
                    return []
                if isinstance(val, list):
                    return [str(item).strip() for item in val if item is not None]
                if isinstance(val, str):
                    if ',' in val:
                        return [item.strip() for item in val.split(',') if item.strip()]
                    return [val.strip()]
                return [str(val).strip()]

            # Giải nén và chuẩn hóa dữ liệu lưu trữ
            strengths_raw = json.loads(analysis.strengths) if analysis.strengths else []
            weaknesses_raw = json.loads(analysis.weaknesses) if analysis.weaknesses else []
            improvements_raw = json.loads(analysis.improvements) if analysis.improvements else []
            
            skills_analysis_raw = json.loads(analysis.skills_analysis) if analysis.skills_analysis else None
            if skills_analysis_raw and isinstance(skills_analysis_raw, dict):
                skills_analysis_raw["matched_skills"] = ensure_list_of_strings(skills_analysis_raw.get("matched_skills", []))
                skills_analysis_raw["missing_skills"] = ensure_list_of_strings(skills_analysis_raw.get("missing_skills", []))
                if "match_percentage" in skills_analysis_raw:
                    try:
                        skills_analysis_raw["match_percentage"] = float(skills_analysis_raw["match_percentage"])
                    except (ValueError, TypeError):
                        skills_analysis_raw["match_percentage"] = 0.0

            job_match_raw = json.loads(analysis.job_match) if analysis.job_match else None
            if job_match_raw and isinstance(job_match_raw, dict):
                job_match_raw["gaps"] = ensure_list_of_strings(job_match_raw.get("gaps", []))
                if "match_percentage" in job_match_raw:
                    try:
                        job_match_raw["match_percentage"] = float(job_match_raw["match_percentage"])
                    except (ValueError, TypeError):
                        job_match_raw["match_percentage"] = 0.0

            courses_raw = json.loads(analysis.recommended_courses) if analysis.recommended_courses else []
            courses_cleaned = []
            if isinstance(courses_raw, list):
                for course in courses_raw:
                    if isinstance(course, dict):
                        course["name"] = str(course.get("name", "")).strip()
                        course["provider"] = str(course.get("provider", "")).strip()
                        course["skills"] = ensure_list_of_strings(course.get("skills", []))
                        courses_cleaned.append(course)

            return CVAnalysisResponse(
                id=analysis.id,
                cv_id=analysis.cv_id,
                user_id=analysis.user_id,
                target_field=analysis.target_field,
                target_role=analysis.target_role,
                job_description=analysis.job_description,
                resume_score=analysis.resume_score,
                ats_score=analysis.ats_score,
                strengths=ensure_list_of_strings(strengths_raw),
                weaknesses=ensure_list_of_strings(weaknesses_raw),
                improvements=ensure_list_of_strings(improvements_raw),
                skills_analysis=skills_analysis_raw,
                job_match=job_match_raw,
                recommended_courses=courses_cleaned,
                detailed_feedback=analysis.detailed_feedback,
                recommendations=recommendations_list if recommendations_list else None,
                created_at=analysis.created_at
            )
        except Exception as e:
            logger.error(f"❌ Lỗi giải nén dữ liệu CVAnalysis: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Dữ liệu phân tích lưu trữ trong DB bị lỗi định dạng."
            )

    async def generate_pdf_report(self, db: AsyncSession, analysis_id: int, user_id: int) -> io.BytesIO:
        """Sinh file báo cáo PDF chi tiết bằng ReportLab."""
        analysis = await self.get_analysis_detail(db, analysis_id, user_id)
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=0.5 * inch,
            rightMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch
        )
        
        # Đăng ký font hỗ trợ Tiếng Việt
        import sys
        FONT_NAME = 'Helvetica'
        FONT_BOLD_NAME = 'Helvetica-Bold'
        
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            
            # Danh sách font candidates theo thứ tự ưu tiên
            font_candidates = []
            
            # 1. DejaVuSans (Linux/Docker - cài qua fonts-dejavu-core)
            font_candidates.append((
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            ))
            
            # 2. DejaVuSans đường dẫn khác (một số distro)
            font_candidates.append((
                "/usr/share/fonts/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"
            ))
            
            # 3. Arial trên Windows
            if sys.platform.startswith('win'):
                windir = os.environ.get('WINDIR', 'C:\\Windows')
                font_candidates.insert(0, (
                    os.path.join(windir, 'Fonts', 'arial.ttf'),
                    os.path.join(windir, 'Fonts', 'arialbd.ttf')
                ))
            
            # 4. Font bundled trong thư mục backend (nếu có)
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            font_candidates.append((
                os.path.join(backend_dir, 'fonts', 'DejaVuSans.ttf'),
                os.path.join(backend_dir, 'fonts', 'DejaVuSans-Bold.ttf')
            ))
            
            # Tìm font khả dụng đầu tiên
            font_path = None
            font_bold_path = None
            for p, p_bold in font_candidates:
                if os.path.exists(p) and os.path.exists(p_bold):
                    font_path = p
                    font_bold_path = p_bold
                    break
            
            if font_path and font_bold_path:
                pdfmetrics.registerFont(TTFont('ViFont', font_path))
                pdfmetrics.registerFont(TTFont('ViFont-Bold', font_bold_path))
                pdfmetrics.registerFontFamily('ViFont', normal='ViFont', bold='ViFont-Bold')
                FONT_NAME = 'ViFont'
                FONT_BOLD_NAME = 'ViFont-Bold'
                logger.info(f"✅ Đã đăng ký font tiếng Việt: {font_path}")
            else:
                logger.warning("⚠️ Không tìm thấy font Unicode. PDF sẽ dùng Helvetica (không hỗ trợ tiếng Việt).")
        except Exception as e:
            logger.error(f"❌ Lỗi đăng ký font Unicode: {e}. PDF sẽ dùng Helvetica.")

        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontName=FONT_BOLD_NAME,
            fontSize=20,
            textColor=colors.HexColor('#1E3A8A'),
            spaceAfter=12,
            alignment=1
        )
        
        section_heading = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontName=FONT_BOLD_NAME,
            fontSize=12,
            textColor=colors.white,
            backColor=colors.HexColor('#1E3A8A'),
            borderPadding=5,
            spaceBefore=10,
            spaceAfter=6,
            borderRadius=3
        )
        
        normal_style = ParagraphStyle(
            'NormalStyle',
            parent=styles['Normal'],
            fontName=FONT_NAME,
            fontSize=10,
            leading=14,
            spaceAfter=5
        )
        
        list_style = ParagraphStyle(
            'ListStyle',
            parent=normal_style,
            fontName=FONT_NAME,
            leftIndent=15,
            firstLineIndent=-10,
            spaceAfter=3
        )


        elements = []
        
        # 1. Tiêu đề
        elements.append(Paragraph("BÁO CÁO PHÂN TÍCH CV CHI TIẾT", title_style))
        elements.append(Paragraph(f"Thời gian phân tích: {analysis.created_at.strftime('%d/%m/%Y %H:%M')}", normal_style))
        elements.append(Spacer(1, 10))
        
        # 2. Thông tin chung
        elements.append(Paragraph("Thông Tin Chung", section_heading))
        info_data = [
            [Paragraph("<b>Ngành nghề (AI nhận diện):</b>", normal_style), Paragraph(analysis.target_field or "Không rõ", normal_style)],
            [Paragraph("<b>Vị trí ứng tuyển (AI nhận diện):</b>", normal_style), Paragraph(analysis.target_role or "Không rõ", normal_style)],
            [Paragraph("<b>Điểm CV (Resume Score):</b>", normal_style), Paragraph(f"{analysis.resume_score}/100", normal_style)],
            [Paragraph("<b>Điểm tương thích ATS:</b>", normal_style), Paragraph(f"{analysis.ats_score}/100", normal_style)]
        ]
        info_table = Table(info_data, colWidths=[2.2*inch, 4.8*inch])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 10))
        
        # 3. Điểm mạnh
        elements.append(Paragraph("Điểm Mạnh (Strengths)", section_heading))
        for strength in analysis.strengths:
            elements.append(Paragraph(f"• {strength}", list_style))
        elements.append(Spacer(1, 10))
        
        # 4. Điểm yếu
        elements.append(Paragraph("Điểm Cần Khắc Phục (Weaknesses)", section_heading))
        for weakness in analysis.weaknesses:
            elements.append(Paragraph(f"• {weakness}", list_style))
        elements.append(Spacer(1, 10))
        
        # 5. Đề xuất cải thiện
        elements.append(Paragraph("Đề Xuất Cải Thiện (Improvements)", section_heading))
        for improvement in analysis.improvements:
            elements.append(Paragraph(f"• {improvement}", list_style))
        elements.append(Spacer(1, 10))
        
        # 6. Kỹ năng
        elements.append(Paragraph("Phân Tích Kỹ Năng", section_heading))
        skills_info = analysis.skills_analysis
        if skills_info:
            matched_skills_str = ", ".join(skills_info.matched_skills) or "Không"
            missing_skills_str = ", ".join(skills_info.missing_skills) or "Không"
            
            skills_data = [
                [Paragraph("<b>Độ khớp kỹ năng:</b>", normal_style), Paragraph(f"{skills_info.match_percentage}%", normal_style)],
                [Paragraph("<b>Kỹ năng khớp:</b>", normal_style), Paragraph(matched_skills_str, normal_style)],
                [Paragraph("<b>Kỹ năng thiếu:</b>", normal_style), Paragraph(missing_skills_str, normal_style)]
            ]
            skills_table = Table(skills_data, colWidths=[2.2*inch, 4.8*inch])
            skills_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(skills_table)
        else:
            elements.append(Paragraph("Không có dữ liệu kỹ năng.", normal_style))
        elements.append(Spacer(1, 10))
        
        # 7. Nhận xét tổng quan
        elements.append(Paragraph("Nhận Xét Tổng Thể Từ AI Mentor", section_heading))
        elements.append(Paragraph(analysis.detailed_feedback or "Không có nhận xét chi tiết.", normal_style))
        
        # Dựng file
        doc.build(elements)
        buffer.seek(0)
        return buffer

# Khởi tạo instance Singleton
cv_service = CVService()
