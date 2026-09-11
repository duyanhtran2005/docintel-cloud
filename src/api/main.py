import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

@app.get("/", tags=["Health Check"])
async def root():
    return {
        "system": "DocIntel Cloud API Gateway",
        "status": "online",
        "docs_url": "/docs"
    }

@app.get("/health", tags=["Health Check"])
async def health_check():
    return {"status": "healthy"}
