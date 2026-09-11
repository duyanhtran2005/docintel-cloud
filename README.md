# 🚀 Enterprise Document Intelligence & QA Pipeline (DocIntel-Cloud)

> **Architected for Data & AI Engineers | 100% Zero-Cost Cloud-Native Architecture (0 USD)**

DocIntel-Cloud là hệ thống xử lý tài liệu tự động, băm nhỏ văn bản (Text Chunking), tạo Vector Embeddings, lưu trữ hỗn hợp Hợp nhất (Relational + HNSW Vector Search trong PostgreSQL), và hỗ trợ hỏi đáp tổng hợp ngữ cảnh bằng LLM (Retrieval-Augmented Generation - RAG).

---

## 🏗️ System Architecture

```text
               +-------------------------------------------------------------+
               |                       Client / Frontend                     |
               +------------------------------+------------------------------+
                                              |
                                              | HTTP REST / Streaming SSE
                                              v
+-----------------------------------------------------------------------------------------+
| Docker Network (`docintel-net`)                                                         |
|                                                                                         |
|  +-----------------------------------------------------------------------------------+  |
|  |                             FastAPI Serving Gateway                               |  |
|  |  - Ingestion Controller (Upload PDF, sliding window chunker)                       |  |
|  |  - Vector Search Controller (HNSW Cosine Similarity Search)                       |  |
|  |  - LLM RAG Synthesis Engine (Context formatting + Citation tracing)               |  |
|  +---------------------+-------------------------------+-----------------------------+  |
|                        |                               |                                |
|                        | boto3 S3 API                  | Async SQLAlchemy               |
|                        v                               v                                |
|  +------------------------------+     +-------------------------------+                 |
|  |    MinIO (Object Storage)    |     |      PostgreSQL + pgvector    |                 |
|  |  - Raw PDFs, DOCX, TXT       |     |  - Document Metadata          |                 |
|  |  - S3 Bucket: `documents`    |     |  - Chunks & 768D Embeddings   |                 |
|  +------------------------------+     |  - HNSW Index (Cosine Ops)    |                 |
|                                       +-------------------------------+                 |
|                        |                                                                |
|                        | Cache / Rate Limit                                             |
|                        v                                                                |
|  +------------------------------+     +-------------------------------+                 |
|  |     Redis (Cache & Queue)    |     |    SentenceTransformers /     |                 |
|  |  - Query response cache      |     |  Groq Cloud / Gemini API      |                 |
|  +------------------------------+     +-------------------------------+                 |
+-----------------------------------------------------------------------------------------+
```

---

## 🛠️ Tech Stack Specification

| Thành phần | Công nghệ sử dụng | Vai trò & Lý do lựa chọn |
|---|---|---|
| **Framework API** | FastAPI (Python 3.11, AsyncIO, Pydantic v2) | Đảm bảo hiệu năng xử lý bất đồng bộ (I/O-bound) cao nhất. |
| **Object Storage** | MinIO Container | Giả lập chuẩn AWS S3 API (`boto3`), dễ dàng chuyển đổi sang S3 Cloud không đổi code. |
| **Database & Vector Store** | PostgreSQL 16 + `pgvector` (HNSW Index) | Xóa bỏ chi phí dùng Vector DB độc lập (Pinecone/Weaviate). Tìm kiếm vector sub-300ms. |
| **Embedding Engine** | `sentence-transformers` / Gemini API | Chạy local offline 100% trên CPU hoặc gọi Free API Key. |
| **LLM RAG Engine** | Groq Cloud (Llama-3.1-8b) / Gemini Flash | Tốc độ suy luận siêu nhanh (>500 tokens/sec), 0 USD. |
| **Containerization** | Docker & Multi-Stage Dockerfile | Đóng gói tối ưu dung lượng image (~300MB), chạy Non-root `appuser`. |
| **CI/CD Pipeline** | GitHub Actions & GHCR | Tự động hóa kiểm thử `ruff`, `pytest`, build và push Docker Image. |

---

## ⚡ Quick Start Guide (Local Development)

### 1. Khởi chạy toàn bộ hạ tầng bằng Docker Compose
```bash
cd docintel-cloud
docker compose up -d --build
```

### 2. Kiểm tra các cổng dịch vụ
* **FastAPI Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **MinIO Console**: [http://localhost:9001](http://localhost:9001) (User: `minioadmin` / Pass: `minioadmin`)
* **PostgreSQL (pgvector)**: `localhost:5432` (DB: `docintel`, User: `postgres`, Pass: `postgrespassword`)

---

## 📡 REST API Specifications

### 1. Upload & Processing PDF Document
* **Endpoint**: `POST /api/v1/documents/upload`
* **Content-Type**: `multipart/form-data`
* **Payload**: File PDF bất kỳ.

### 2. Semantic Vector Similarity Search
* **Endpoint**: `POST /api/v1/documents/search`
* **Payload JSON**:
```json
{
  "query": "DeepSeek-V3.2 architecture performance",
  "top_k": 3
}
```

### 3. RAG Context QA Engine
* **Endpoint**: `POST /api/v1/qa/query`
* **Payload JSON**:
```json
{
  "question": "Mô hình DeepSeek-V3.2 đạt hiệu năng như thế nào?",
  "top_k": 3
}
```

---

## 📌 CV Resume Bullet Points

* **Enterprise Document Intelligence & QA Platform (Cloud-Native Architecture)**
  * Architected a zero-cost, cloud-native RAG pipeline using **FastAPI**, **PostgreSQL (pgvector)**, and **MinIO (S3-compatible Storage)**, supporting async document ingestion and hybrid semantic search.
  * Implemented an HNSW-indexed vector search combined with sliding-window chunking, achieving sub-300ms retrieval latency over structured text chunks.
  * Containerized microservices suite with multi-stage **Docker** builds and orchestrated local-to-cloud workflows via **Docker Compose** and **GitHub Actions CI/CD**.
