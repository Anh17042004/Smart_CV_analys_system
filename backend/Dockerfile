FROM python:3.11-slim

# Tạo thư mục cache cho HuggingFace Transformers (SentenceTransformers)
ENV HF_HOME=/tmp/huggingface
RUN mkdir -p /tmp/huggingface && chmod 777 /tmp/huggingface

WORKDIR /app

# Cài đặt các gói hệ thống cần thiết cho việc biên dịch nếu cần
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Copy file requirements.txt từ thư mục gốc của backend
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn của backend vào container
COPY . .

# Chạy backend trên cổng 8000 (cổng tiêu chuẩn của FastAPI/Backend trên VPS)
# Sử dụng gunicorn với 2 workers (đảm bảo cân bằng giữa hiệu năng và tài nguyên RAM của VPS)
CMD ["gunicorn", "main:app", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
