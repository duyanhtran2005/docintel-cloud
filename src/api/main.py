import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from db.database import engine
from services.vector_store import VectorStore
from api.routers import ingest, query, qa

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan Event: Tự động khởi tạo Database Schema & HNSW Index khi FastAPI khởi động.
    """
    logger.info("🚀 Đang khởi động FastAPI Application Gateway...")
    try:
        vector_store = VectorStore()
        await vector_store.init_db()
        logger.info("✅ Database & HNSW Vector Index đã sẵn sàng!")
    except Exception as e:
        logger.error(f"❌ Lỗi kết nối Database khi khởi động app: {e}")
    yield
    logger.info("🛑 Đang đóng các kết nối FastAPI Application...")

app = FastAPI(
    title="Enterprise Document Intelligence & QA API",
    description="Hệ thống xử lý tài liệu thông minh, Hybrid Vector Search & RAG QA Engine (0-Cost Cloud-Native)",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount toàn bộ 3 APIRouters
app.include_router(ingest.router)
app.include_router(query.router)
app.include_router(qa.router)

# Đường dẫn tới thư mục static chứa giao diện Web
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")

@app.get("/", tags=["Frontend"])
async def serve_frontend(request: Request):
    """
    Hàm điều hướng thông minh:
    - Nếu mở từ Trình duyệt web (Accept text/html) -> Phục vụ giao diện Chatbot & Upload PDF
    - Nếu gọi từ Pytest hoặc API Client -> Trả về JSON trạng thái hệ thống
    """
    index_file = os.path.join(static_dir, "index.html")
    accept_header = request.headers.get("accept", "")
    
    if "text/html" in accept_header and os.path.exists(index_file):
        return FileResponse(index_file)
        
    return {
        "system": "DocIntel Cloud API Gateway",
        "status": "online",
        "docs_url": "/docs"
    }

@app.get("/health", tags=["Health Check"])
async def health_check():
    return {"status": "healthy"}
