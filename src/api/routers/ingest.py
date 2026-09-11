import os
import shutil
import tempfile
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db_session
from services.storage import MinioStorage
from services.vector_store import VectorStore
from pipelines.chunking import PDFChunker
from pipelines.embedding import EmbeddingGenerator
from schemas.document import DocumentUploadResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/documents", tags=["Document Ingestion"])

# Khởi tạo các services đơn thể
storage_service = MinioStorage()
vector_store_service = VectorStore()
chunker_service = PDFChunker(chunk_size=150, overlap=30)
embedder_service = EmbeddingGenerator(dimension=768)

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Endpoint tiếp nhận file PDF:
    1. Upload lưu trữ nguyên bản trên MinIO Object Storage.
    2. Trích xuất text & Chunker theo Sliding Window.
    3. Phát sinh Vector Embedding 768 chiều.
    4. Lưu thông tin Document & Batch Chunks vào PostgreSQL (pgvector).
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Hệ thống hiện tại chỉ hỗ trợ xử lý định dạng file PDF!")

    # 1. Lưu tạm file lên đĩa cứng local để upload MinIO
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        shutil.copyfileobj(file.file, tmp_file)
        tmp_path = tmp_file.name

    try:
        bucket_name = os.getenv("MINIO_BUCKET_NAME", "documents")
        s3_key = f"documents/{file.filename}"

        # 2. Upload file lên MinIO
        upload_success = storage_service.upload_file(bucket_name, tmp_path, s3_key)
        if not upload_success:
            raise HTTPException(status_code=500, detail="Không thể lưu trữ file lên hệ thống MinIO Storage!")

        # 3. Đọc lại stream và trích xuất text PDF
        pdf_stream = storage_service.get_file_stream(bucket_name, s3_key)
        raw_text = chunker_service.extract_text_from_pdf(pdf_stream)
        chunks = chunker_service.chunk_text(raw_text)

        if not chunks:
            raise HTTPException(status_code=400, detail="File PDF rỗng hoặc không chứa dữ liệu văn bản trích xuất được!")

        # 4. Phát sinh Embeddings
        embeddings = await embedder_service.get_embeddings_batch(chunks)

        # 5. Lưu vào Database PostgreSQL
        doc = await vector_store_service.create_document(db, filename=file.filename, s3_key=s3_key)

        chunks_data = [
            {"chunk_index": idx, "content": text_chunk, "embedding": emb}
            for idx, (text_chunk, emb) in enumerate(zip(chunks, embeddings))
        ]

        inserted_chunks = await vector_store_service.insert_chunks_batch(db, doc.id, chunks_data)

        return DocumentUploadResponse(
            message="Tải lên và nạp dữ liệu tài liệu thành công!",
            document_id=doc.id,
            filename=doc.filename,
            s3_key=doc.s3_key,
            chunks_count=len(inserted_chunks),
            created_at=doc.created_at
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Lỗi khi xử lý upload document: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống nội bộ: {str(e)}")
    finally:
        # Xóa file tạm
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
