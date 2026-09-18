# 🚀 DocIntel-Cloud: Enterprise Document Intelligence & Semantic Search Pipeline (RAG)

> **A production-grade, end-to-end cloud-native pipeline architected for Data Engineers & AI Engineers**  
---

## 🎯 1. Project Overview & Objectives
DocIntel-Cloud is engineered to automate the ingestion, indexing, and semantic exploration of large-scale enterprise documents (financial statements, legal contracts, complex technical manuals):
- **Automated Ingestion Pipeline**: Ingests raw PDFs, extracts text streams, and performs rigorous data sanitization (eliminating corrupted UTF-8 control bytes like `\x00`).
- **Context-Preserving Chunking**: Implements a sliding window token-chunking strategy with configurable overlap to preserve sentence boundaries and semantic context.
- **Vector Storage & HNSW Indexing**: Integrates PostgreSQL 16 with `pgvector`, utilizing **HNSW (Hierarchical Navigable Small World)** indexing for sub-5ms cosine similarity vector search.
<<<<<<< HEAD
- **Context-Augmented QA (RAG)**: Synthesizes ground-truth answers using state-of-the-art LLMs with **precise citation tracing** to mitigate hallucinations.
=======
- **Context-Augmented QA (RAG)**: Synthesizes ground-truth answers using LLMs with **precise citation tracing** to mitigate hallucinations.
>>>>>>> cccbf642653a5485256cbc1ac06d8f3123cebd95

---

## 🏗️ 2. System Architecture

```text
[Client / User Application]
          │
          ▼ (HTTP REST / API)
┌─────────────────────────────────────────────────────────────┐
│ FastAPI Serving Gateway (Central API Hub)                   │
│  - POST /upload: Document upload, async parsing & chunking  │
│  - POST /search: Cosine similarity vector search            │
│  - POST /qa/query: Context synthesis & citation tracing     │
└──────┬──────────────────────┬───────────────────────────────┘
       │                      │
       ▼                      ▼
┌──────────────────┐   ┌───────────────────────────────┐
│ MinIO Storage    │   │ PostgreSQL 16 + pgvector      │
│ (S3 Simulation)  │   │ (Relational + Vector DB)      │
│ - Raw PDF store  │   │ - Tables: documents & chunks  │
│ - Bucket:        │   │ - HNSW Index (Cosine Ops)     │
│   `documents`    │   └───────────────────────────────┘
└──────────────────┘                  ▲
                                      │ (Dense Embeddings)
                       ┌──────────────┴────────────────┐
                       │ Embedding & LLM Engine        │
                       │ - SentenceTransformers (Local)│
                       │ - Google Gemini API / Groq    │
                       └───────────────────────────────┘
```

---

## 🛠️ 3. Tech Stack Specification

| Component | Technology | Rationale & Architectural Decisions |
|---|---|---|
| **API Framework** | FastAPI (Python 3.11, AsyncIO, Pydantic v2) | High-throughput asynchronous runtime optimized for I/O-bound operations. |
| **Object Storage** | MinIO Container | S3-compatible API (`boto3` ready) ensuring zero-code migration to AWS S3. |
| **Database & Vector Store** | PostgreSQL 16 + `pgvector` (HNSW Index) | Unified relational and vector database with sub-5ms cosine retrieval. |
<<<<<<< HEAD
| **Embedding Engine** | `sentence-transformers` | 100% offline, zero-cost CPU inference without external API rate limits. |
=======
| **Embedding Engine** | `sentence-transformers` | 100% offlines. |
>>>>>>> cccbf642653a5485256cbc1ac06d8f3123cebd95
| **LLM RAG Engine** | Groq Cloud (Llama 3.1) / Gemini Flash | Ultra-fast context synthesis (>500 tokens/sec) with citation tracing. |
| **Containerization** | Docker & Multi-Stage Dockerfile | Minimal production footprint (~300MB) executing as non-root `appuser`. |
| **CI/CD Pipeline** | GitHub Actions & GHCR | Automated linting, pytest suites, and automated container image publishing. |

---

## ⚡ 4. Quick Start Guide (Local Setup)

### Step 1: Spin Up Infrastructure Containers
Run Docker Compose in the root project directory:
```bash
docker compose up -d
```
This initializes the underlying services in the background:
* **MinIO Console**: `http://localhost:9001` (Credentials: `minioadmin` / `minioadmin`)
* **PostgreSQL (pgvector)**: Port `5432` (DB: `docintel`, User: `postgres`, Password: `postgrespassword`)
* **Redis Cache**: Port `6379`

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy the template configuration into your active `.env`:
```bash
# Windows (CMD / PowerShell):
copy .env.example .env

# Linux / macOS:
cp .env.example .env
```
<<<<<<< HEAD
Open `.env` and fill in your LLM API Key (`GEMINI_API_KEY` or `GROQ_API_KEY`).
=======
Open `.env` and fill in your LLM API Key.
>>>>>>> cccbf642653a5485256cbc1ac06d8f3123cebd95

### Step 4: Launch FastAPI Application Gateway
* **PowerShell**:
  ```powershell
  $env:PYTHONPATH="src"
  python -m uvicorn src.api.main:app --reload --port 8000
  ```
* **Linux / macOS**:
  ```bash
  PYTHONPATH=src python -m uvicorn src.api.main:app --reload --port 8000
  ```

---

## 📡 5. API Reference & Usage

Interactive OpenAPI documentation is live at **`http://localhost:8000/docs`**. You can also interact via `curl`:

### 1. Ingest Document (`POST /api/v1/documents/upload`)
Upload a PDF document. The pipeline automatically persists the binary to MinIO, chunks the text, and stores vector embeddings in PostgreSQL:
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@path/to/your/document.pdf"
```

### 2. Semantic Search (`POST /api/v1/documents/search`)
Query top-K semantically relevant chunks based on cosine distance:
```bash
curl -X POST "http://localhost:8000/api/v1/documents/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "model architecture and benchmark results", "top_k": 3}'
```

### 3. Contextual RAG QA (`POST /api/v1/qa/query`)
Submit natural language questions. The engine retrieves relevant context and prompts the LLM to synthesize a cited answer:
```bash
curl -X POST "http://localhost:8000/api/v1/qa/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the primary advantages of this architecture?", "top_k": 3}'
```

---

## 🧪 6. Automated Testing

The repository maintains an automated test suite executed via `pytest`:
```bash
pytest -v
```
Test coverage verifies:
* Sliding window token chunking with overlap boundaries.
* Data sanitization against corrupted UTF-8 NUL bytes (`\x00`).
* Health check and root gateway endpoint integration.

---

## 🚀 7. Release Notes & Changelog

### 🌟 [v2.0.0] - Multi-Document RAG Pro Edition
- **Multi-Document Comparative RAG**:
  - Enhanced context window retrieval supporting comparative analysis across multiple heterogeneous PDF sources (e.g., DeepSeek-V3.2 vs. Mixtral 8x7B benchmark).
  - Configurable dynamic Top-K chunk retrieval slider (3 to 25 chunks) directly in the UI and API.
  - Fine-tuned system prompts for comprehensive comparative tabular analysis and synthesis.
- **Modern Full-Featured Web UI**:
  - Interactive Dark Mode web dashboard with drag-and-drop PDF ingestion.
  - In-browser markdown table rendering powered by Marked.js.
  - Interactive Source Citations modal: inspect full-text chunks, cosine relevance scores, and document origin with a single click.
- **Storage & Ingestion Optimization**:
  - UTF-8 NUL byte (`\x00`) stripping & data sanitization for robust PDF mathematical equation indexing.
  - MinIO S3-compatible persistent object storage integration.
  - Smart HTTP Accept header content negotiation: serves Web UI for browsers while preserving JSON response for automated test suites.
- **Enterprise CI/CD**:
  - Automated GitHub Actions matrix testing with PostgreSQL 16 `pgvector` & MinIO services.
  - Multi-stage Docker container build with non-root security compliance (`appuser`).

---

### 📦 [v1.0.0] - Initial Enterprise Pipeline Release
- Core end-to-end RAG architecture with FastAPI, PostgreSQL `pgvector` HNSW cosine indexing, and MinIO storage.
- Sliding window chunking algorithm preserving semantic sentence boundaries.
- Contextual QA endpoint with citation referencing.

---

## ⚖️ 8. License
Distributed under the **MIT License**. See `LICENSE` for details.

---

## ⭐ Show Your Support

If you find **DocIntel-Cloud** useful for your research, learning, or production initiatives, please consider starring **(⭐)** this repository on GitHub!

Thank you for your support! 🚀
