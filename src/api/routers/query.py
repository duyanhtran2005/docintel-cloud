import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db_session
from services.vector_store import VectorStore
from pipelines.embedding import EmbeddingGenerator
from schemas.query import SearchRequest, SearchResponse, SearchResultItem

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/documents", tags=["Vector Search"])

vector_store_service = VectorStore()
embedder_service = EmbeddingGenerator(dimension=768)

@router.post("/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Endpoint tìm kiếm vector ngữ nghĩa (Semantic Vector Search):
    1. Mã hóa câu hỏi (query string) thành Vector Embedding 768 chiều.
    2. Thực hiện Cosine Similarity Search bằng HNSW Index trong PostgreSQL.
    3. Trả về Top K đoạn văn bản có khoảng cách gần nhất.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Câu truy vấn tìm kiếm không được để rỗng!")

    try:
        # 1. Mã hóa query
        query_vector = await embedder_service.get_embedding(request.query)

        # 2. Tìm kiếm Vector Similarity
        raw_results = await vector_store_service.search_similar_chunks(
            db, query_vector=query_vector, top_k=request.top_k
        )

        # 3. Đóng gói Response
        formatted_results = [
            SearchResultItem(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                distance=distance
            )
            for chunk, distance in raw_results
        ]

        return SearchResponse(
            query=request.query,
            total_results=len(formatted_results),
            results=formatted_results
        )

    except Exception as e:
        logger.error(f"Lỗi tìm kiếm vector search: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống nội bộ: {str(e)}")
