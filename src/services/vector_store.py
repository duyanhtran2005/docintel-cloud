import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import engine, Base
from db.models import Document, DocumentChunk

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        pass

    async def init_db(self):
        """
        Khởi tạo extension 'vector' và tự động tạo toàn bộ bảng DB + Index HNSW.
        """
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Đã khởi tạo Database schema và HNSW Index thành công!")

    async def create_document(self, session: AsyncSession, filename: str, s3_key: str) -> Document:
        """Tạo bản ghi Document mới trong DB"""
        doc = Document(filename=filename, s3_key=s3_key)
        session.add(doc)
        await session.commit()
        await session.refresh(doc)
        return doc

    async def insert_chunks_batch(
        self, session: AsyncSession, document_id: Any, chunks_data: List[Dict[str, Any]]
    ) -> List[DocumentChunk]:
        """
        Insert hàng loạt (batch) các chunk văn bản cùng vector embedding 768 chiều vào Postgres.
        """
        chunk_objects = [
            DocumentChunk(
                document_id=document_id,
                chunk_index=item["chunk_index"],
                content=item["content"],
                embedding=item["embedding"],
            )
            for item in chunks_data
        ]

        session.add_all(chunk_objects)
        await session.commit()
        logger.info(f"Đã insert thành công {len(chunk_objects)} chunks vào database!")
        return chunk_objects

    async def search_similar_chunks(
        self, session: AsyncSession, query_vector: List[float], top_k: int = 8
    ) -> List[Tuple[DocumentChunk, float, str]]:
        """
        Tìm kiếm Top-K chunk có độ tương đồng Cosine cao nhất với HNSW Index.
        Tự động JOIN với bảng Document để lấy tên file PDF gốc (filename).
        """
        distance_col = DocumentChunk.embedding.cosine_distance(query_vector).label("distance")

        stmt = (
            select(DocumentChunk, distance_col, Document.filename)
            .join(Document, DocumentChunk.document_id == Document.id)
            .order_by(distance_col.asc())
            .limit(top_k)
        )

        result = await session.execute(stmt)
        rows = result.all()
        
        # Trả về danh sách: [(DocumentChunk, distance_score, filename), ...]
        return [(row[0], float(row[1]), str(row[2])) for row in rows]
