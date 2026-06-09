JD_SUMMARY_PROMPT = """
Bạn là một trợ lý AI chuyên nghiệp. Nhiệm vụ của bạn là đọc và tóm tắt Job Description (JD) dưới đây thành một dòng mô tả chuẩn hóa có định dạng nghiêm ngặt để đưa vào mô hình tạo vector embedding.

--- NỘI DUNG JOB DESCRIPTION ---
{job_description}

--- YÊU CẦU ĐẦU RA ---
Tạo ra một dòng tóm tắt duy nhất theo định dạng sau (sử dụng dấu gạch đứng '|' làm phân cách):
[Vị trí tuyển dụng kèm cấp bậc: Intern/Fresher/Junior/Mid/Senior/Lead] | [Ngành nghề/Lĩnh vực] | [Danh sách kỹ năng yêu cầu quan trọng nhất, ngăn cách bởi dấu phẩy] | [Yêu cầu số năm kinh nghiệm] | [Yêu cầu học vấn]

Ví dụ mẫu:
Senior Backend Developer | CNTT | Python, FastAPI, PostgreSQL, Docker, Git | 3-5 năm | Đại học

* Lưu ý quan trọng:
- Trả về đúng 1 dòng duy nhất, không thêm giải thích hay chữ dẫn đầu.
- Phải xác định và ghi rõ cấp bậc tuyển dụng ở cột 1 (ví dụ: Intern, Fresher, Junior, Mid, Senior, Lead). Nếu không đề cập trực tiếp, hãy tự suy luận từ mô tả công việc, trách nhiệm và mức lương.
- Cột số 4 (yêu cầu số năm kinh nghiệm) phải được trích xuất chính xác và chuẩn hóa về dạng: 'X năm', 'X-Y năm', 'Trên X năm', 'Dưới 1 năm' hoặc 'Không yêu cầu'. Ví dụ: '3 năm', '2-4 năm', 'Trên 5 năm'.
- Giữ nguyên tên kỹ năng bằng tiếng Anh.
- Rút gọn tối đa thông tin thừa.
"""

CV_SUMMARY_PROMPT = """
Bạn là một trợ lý AI chuyên nghiệp. Nhiệm vụ của bạn là đọc nội dung CV trích xuất dưới đây và tóm tắt nó thành một dòng mô tả chuẩn hóa có định dạng nghiêm ngặt để đưa vào mô hình tạo vector embedding.

--- NỘI DUNG CV ---
{extracted_text}

--- YÊU CẦU ĐẦU RA ---
Tạo ra một dòng tóm tắt duy nhất theo định dạng sau (sử dụng dấu gạch đứng '|' làm phân cách, tương thích hoàn toàn với cấu trúc của JD):
[Vị trí công việc mục tiêu/hiện tại kèm cấp bậc: Intern/Fresher/Junior/Mid/Senior/Lead] | [Ngành nghề/Lĩnh vực] | [Danh sách các kỹ năng chuyên môn chính của ứng viên, ngăn cách bởi dấu phẩy] | [Số năm kinh nghiệm làm việc thực tế] | [Học vấn cao nhất]

Ví dụ mẫu:
Junior Backend Developer | CNTT | Python, Django, SQL, Docker, Redis, RESTful API | 1 năm | Đại học

* Lưu ý quan trọng:
- Trả về đúng 1 dòng duy nhất, không thêm giải thích hay chữ dẫn đầu.
- Phải xác định và ghi rõ cấp bậc hiện tại hoặc mục tiêu của ứng viên ở cột 1 (ví dụ: Intern, Fresher, Junior, Mid, Senior, Lead). Nếu không có, hãy tự suy luận dựa trên tổng số năm kinh nghiệm và các dự án đã làm.
- Cột số 4 (số năm kinh nghiệm làm việc thực tế) phải được chuẩn hóa về dạng: 'X năm', 'Dưới 1 năm' hoặc 'Chưa có kinh nghiệm'. Ví dụ: '1 năm', '5 năm', 'Dưới 1 năm'.
- Giữ nguyên tên kỹ năng bằng tiếng Anh.
- Rút gọn tối đa thông tin thừa.
"""
