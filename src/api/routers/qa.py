import time
import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db_session
from services.vector_store import VectorStore
from services.llm import LLMService
from pipelines.embedding import EmbeddingGenerator
from schemas.qa import QARequest, QAResponse, CitationItem

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/qa", tags=["RAG QA Engine"])

vector_store_service = VectorStore()
embedder_service = EmbeddingGenerator(dimension=768)
llm_service = LLMService()

@router.post("/query", response_model=QAResponse)
async def answer_question(
    request: QARequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Endpoint RAG QA hoàn chỉnh (Retrieval-Augmented Generation):
    1. Mã hóa câu hỏi (User Question) thành Vector Embedding 768D.
    2. Retrieve Top K Chunks liên quan nhất từ PostgreSQL HNSW Index.
    3. Đóng gói Context & Prompt Template.
    4. Gọi LLM (Groq / Gemini) để tổng hợp câu trả lời kèm trích dẫn nguồn.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Câu hỏi không được để rỗng!")

    start_time = time.time()
    try:
        # 1. Vector Search ngữ cảnh liên quan
        query_vector = await embedder_service.get_embedding(request.question)
        search_results = await vector_store_service.search_similar_chunks(
            db, query_vector=query_vector, top_k=request.top_k
        )

        if not search_results:
            return QAResponse(
                question=request.question,
                answer="Không tìm thấy thông tin ngữ cảnh nào trong cơ sở dữ liệu để trả lời câu hỏi này.",
                citations=[],
                execution_time_ms=round((time.time() - start_time) * 1000, 2)
            )

        # 2. Đóng gói contexts cho LLM
        contexts_data = []
        citations = []
        for chunk, distance in search_results:
            contexts_data.append({
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content
            })
            citations.append(CitationItem(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                chunk_index=chunk.chunk_index,
                content_snippet=chunk.content[:150] + "...",
                relevance_score=round(1.0 - distance, 4)  # Đổi distance sang similarity score
            ))

        # 3. Sinh câu trả lời bằng LLM
        llm_answer = await llm_service.generate_answer(request.question, contexts_data)
        execution_time = round((time.time() - start_time) * 1000, 2)

        return QAResponse(
            question=request.question,
            answer=llm_answer,
            citations=citations,
            execution_time_ms=execution_time
        )

    except Exception as e:
        logger.error(f"Lỗi khi thực thi RAG QA: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống nội bộ: {str(e)}")
