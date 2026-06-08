FROM python:3.11-slim

# Tạo thư mục cache cho HuggingFace Transformers (SentenceTransformers)
ENV HF_HOME=/tmp/huggingface
RUN mkdir -p /tmp/huggingface && chmod 777 /tmp/huggingface

WORKDIR /app

# Cài đặt các gói hệ thống cần thiết cho việc biên dịch nếu cần
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy file requirements.txt từ thư mục gốc của backend
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn của backend vào container
COPY . .

# Chạy backend trên cổng 7860 (cổng mặc định của Hugging Face Spaces)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
