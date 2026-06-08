JD_SUMMARY_PROMPT = """
Bạn là một trợ lý AI chuyên nghiệp. Nhiệm vụ của bạn là đọc và tóm tắt Job Description (JD) dưới đây thành một dòng mô tả chuẩn hóa có định dạng nghiêm ngặt để đưa vào mô hình tạo vector embedding.

--- NỘI DUNG JOB DESCRIPTION ---
{job_description}

--- YÊU CẦU ĐẦU RA ---
Tạo ra một dòng tóm tắt duy nhất theo định dạng sau (sử dụng dấu gạch đứng '|' làm phân cách):
[Vị trí tuyển dụng] | [Ngành nghề/Lĩnh vực] | [Danh sách kỹ năng yêu cầu quan trọng nhất, ngăn cách bởi dấu phẩy] | [Yêu cầu số năm kinh nghiệm] | [Yêu cầu học vấn]

Ví dụ mẫu:
Backend Developer | CNTT | Python, FastAPI, PostgreSQL, Docker, Git | 1-3 năm | Đại học

* Lưu ý quan trọng:
- Trả về đúng 1 dòng duy nhất, không thêm giải thích hay chữ dẫn đầu.
- Giữ nguyên tên kỹ năng bằng tiếng Anh.
- Rút gọn tối đa thông tin thừa.
"""

CV_SUMMARY_PROMPT = """
Bạn là một trợ lý AI chuyên nghiệp. Nhiệm vụ của bạn là đọc nội dung CV trích xuất dưới đây và tóm tắt nó thành một dòng mô tả chuẩn hóa có định dạng nghiêm ngặt để đưa vào mô hình tạo vector embedding.

--- NỘI DUNG CV ---
{extracted_text}

--- YÊU CẦU ĐẦU RA ---
Tạo ra một dòng tóm tắt duy nhất theo định dạng sau (sử dụng dấu gạch đứng '|' làm phân cách, tương thích hoàn toàn với cấu trúc của JD):
[Vị trí công việc mục tiêu/hiện tại] | [Ngành nghề/Lĩnh vực] | [Danh sách các kỹ năng chuyên môn chính của ứng viên, ngăn cách bởi dấu phẩy] | [Số năm kinh nghiệm làm việc thực tế] | [Học vấn cao nhất]

Ví dụ mẫu:
Backend Developer | CNTT | Python, Django, SQL, Docker, Redis, RESTful API | 1 năm | Đại học

* Lưu ý quan trọng:
- Trả về đúng 1 dòng duy nhất, không thêm giải thích hay chữ dẫn đầu.
- Giữ nguyên tên kỹ năng bằng tiếng Anh.
- Rút gọn tối đa thông tin thừa.
"""
