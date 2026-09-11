# 🚀 DocIntel-Cloud: Hệ Thống Xử Lý Tài Liệu Thông Minh & Hỏi Đáp RAG (0-Cost Cloud-Native)

> **Dự án thực chiến chuẩn Enterprise dành cho Data Engineer & AI Engineer**  
> **Chi phí vận hành: 100% Miễn Phí (0 VNĐ)** thông qua Docker local và hạ tầng AWS Free Tier.

---

## 🎯 1. Mục Đích Dự Án
DocIntel-Cloud giải quyết bài toán phân tích và khai thác thông tin từ các tài liệu lớn của doanh nghiệp (báo cáo tài chính, hợp đồng pháp lý, tài liệu kỹ thuật dài hàng trăm trang PDF):
- **Tự động hóa Ingestion Pipeline**: Tải file PDF, tự động trích xuất nội dung và làm sạch lỗi font, lọc bỏ các ký tự byte điều khiển UTF-8 lỗi (`\x00`).
- **Phân đoạn thông minh (Chunking)**: Cắt văn bản theo thuật toán cửa sổ trượt (Sliding Window) với tham số `overlap` để bảo tồn trọn vẹn ngữ cảnh của câu.
- **Lưu trữ Vector & HNSW Index**: Tích hợp PostgreSQL 16 với extension `pgvector`, sử dụng chỉ mục **HNSW (Hierarchical Navigable Small World)** cho phép tìm kiếm ngữ nghĩa theo độ tương đồng Cosine cực nhanh (< 5ms).
- **Hỏi đáp thông minh (RAG QA)**: Kết nối với các mô hình ngôn ngữ lớn (Google Gemini / Groq Llama 3) để tổng hợp câu trả lời tự nhiên từ tài liệu nội bộ, kèm tính năng **trích dẫn chính xác nguồn dữ liệu (Citation Tracing)** giúp chống "chém gió" (Anti-Hallucination).

---

## 🏗️ 2. Kiến Trúc Hệ Thống

```text
[Người Dùng / Client]
          │
          ▼ (HTTP REST / API)
┌─────────────────────────────────────────────────────────────┐
│ FastAPI Serving Gateway (Cổng API trung tâm)                │
│  - POST /upload: Tiếp nhận file PDF, băm chunk              │
│  - POST /search: Tìm kiếm vector tương đồng                 │
│  - POST /qa/query: Tổng hợp câu trả lời bằng AI (RAG)       │
└──────┬──────────────────────┬───────────────────────────────┘
       │                      │
       ▼                      ▼
┌──────────────────┐   ┌───────────────────────────────┐
│ MinIO Storage    │   │ PostgreSQL 16 + pgvector      │
│ (Giả lập AWS S3) │   │ (Lưu trữ quan hệ + Vector DB) │
│ - Lưu file PDF gốc│  │ - Bảng documents & chunks     │
│ - Bucket:        │   │ - HNSW Index (Cosine Ops)     │
│   `documents`    │   └───────────────────────────────┘
└──────────────────┘                  ▲
                                      │ (Mã hóa Vector)
                       ┌──────────────┴────────────────┐
                       │ Embedding & LLM Engine        │
                       │ - SentenceTransformers (Local)│
                       │ - Google Gemini API / Groq    │
                       └───────────────────────────────┘
```

---

## 🛠️ 3. Công Nghệ Sử Dụng

| Thành phần | Công nghệ sử dụng | Vai trò & Lý do lựa chọn |
|---|---|---|
| **API Framework** | FastAPI (Python 3.11, AsyncIO, Pydantic v2) | Đảm bảo hiệu năng xử lý bất đồng bộ (I/O-bound) cao nhất. |
| **Object Storage** | MinIO Container | Giả lập chuẩn AWS S3 API (`boto3`), dễ dàng chuyển đổi sang S3 Cloud không cần đổi code. |
| **Database & Vector Store** | PostgreSQL 16 + `pgvector` (HNSW Index) | Loại bỏ chi phí dùng Vector DB độc lập (Pinecone/Weaviate). Tìm kiếm vector sub-5ms. |
| **Embedding Engine** | `sentence-transformers` / Gemini API | Chạy local offline 100% trên CPU hoặc gọi Free API Key. |
| **LLM RAG Engine** | Groq Cloud (Llama-3.1-8b) / Gemini Flash | Tốc độ suy luận siêu nhanh (>500 tokens/sec), 0 USD. |
| **Containerization** | Docker & Multi-Stage Dockerfile | Đóng gói tối ưu dung lượng image (~300MB), chạy Non-root `appuser`. |
| **CI/CD Pipeline** | GitHub Actions & GHCR | Tự động hóa kiểm thử `pytest`, build và push Docker Image lên Registry. |

---

## ⚡ 4. Hướng Dẫn Cài Đặt & Khởi Chạy (Local)

### Bước 1: Khởi động các container hạ tầng
Mở Terminal tại thư mục dự án và chạy:
```bash
docker compose up -d
```
Lệnh này sẽ khởi chạy 3 dịch vụ ngầm:
* **MinIO Console**: `http://localhost:9001` (Tài khoản: `minioadmin` / `minioadmin`)
* **PostgreSQL (pgvector)**: Cổng `5432` (DB: `docintel`, User: `postgres`, Pass: `postgrespassword`)
* **Redis**: Cổng `6379`

### Bước 2: Cài đặt thư viện Python
```bash
pip install -r requirements.txt
```

### Bước 3: Cấu hình biến môi trường
Tạo file `.env` từ file mẫu `.env.example`:
```bash
# Trên Windows CMD/PowerShell:
copy .env.example .env

# Trên Linux/macOS:
cp .env.example .env
```
Sau đó mở file `.env` và điền `GEMINI_API_KEY` hoặc `GROQ_API_KEY` của bạn.

### Bước 4: Chạy ứng dụng FastAPI
* **Trên PowerShell**:
  ```powershell
  $env:PYTHONPATH="src"
  python -m uvicorn src.api.main:app --reload --port 8000
  ```
* **Trên Linux / Mac**:
  ```bash
  PYTHONPATH=src python -m uvicorn src.api.main:app --reload --port 8000
  ```

---

## 📡 5. Hướng Dẫn Sử Dụng API

Sau khi server khởi động, bạn có thể truy cập Swagger UI tương tác tại: **`http://localhost:8000/docs`** hoặc gọi API qua `curl`:

### 1. Tải lên tài liệu PDF (`POST /api/v1/documents/upload`)
Tải file PDF lên hệ thống. Server sẽ tự động lưu vào MinIO, cắt thành các đoạn văn bản nhỏ và lưu vector vào Postgres:
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@duong_dan_den_file.pdf"
```

### 2. Tìm kiếm đoạn văn bản tương đồng (`POST /api/v1/documents/search`)
Tìm Top K đoạn trích liên quan nhất bằng phép đo Cosine Similarity:
```bash
curl -X POST "http://localhost:8000/api/v1/documents/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "string", "top_k": 3}'
```

### 3. Hỏi đáp ngữ cảnh thông minh RAG (`POST /api/v1/qa/query`)
Đặt câu hỏi, hệ thống tự động tìm kiếm ngữ cảnh và gọi AI để trả lời kèm trích dẫn nguồn:
```bash
curl -X POST "http://localhost:8000/api/v1/qa/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "string", "top_k": 3}'
```

---

## 🧪 6. Kiểm Thử Tự Động (Automated Testing)

Dự án tích hợp đầy đủ kiểm thử tự động với Pytest:
```bash
pytest -v
```
Kết quả kiểm thử bao gồm:
* Kiểm thử thuật toán băm chunk Sliding Window.
* Kiểm thử tính năng làm sạch dữ liệu UTF-8 NUL byte (`\x00`).
* Kiểm thử các API Health Check và Root Endpoint.

---

## ⚖️ 7. Giấy Phép Bản Quyền (License)
Dự án được phân phối dưới giấy phép **MIT License**. Bạn có thể tự do tham khảo, học tập và phát triển tiếp.

---

## ⭐ Ủng Hộ Dự Án (Show Your Support)

Nếu bạn thấy dự án **DocIntel-Cloud** hữu ích hoặc giúp ích cho quá trình học tập / công việc của bạn, hãy dành tặng cho mình **1 Star (⭐)** ở góc trên bên phải GitHub để tiếp thêm động lực phát triển nhé! 

Cảm ơn bạn rất nhiều! Chúc bạn học tập và làm việc hiệu quả! 🚀
