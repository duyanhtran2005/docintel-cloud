import os
import sys
import random
import asyncio
import logging

# Thêm đường dẫn src vào PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from db.database import AsyncSessionLocal
from services.vector_store import VectorStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def generate_dummy_embedding(dim: int = 768) -> list[float]:
    """Tạo ngẫu nhiên một vector giả lập 768 chiều để test"""
    return [random.uniform(-1.0, 1.0) for _ in range(dim)]

async def main():
    print("=" * 60)
    print("🚀 BẮT ĐẦU TEST POSTGRESQL PGVECTOR & HNSW INDEXING")
    print("=" * 60)

    vector_store = VectorStore()

    # 1. Khởi tạo Table & HNSW Index
    logger.info("Đang khởi tạo database table và HNSW index...")
    await vector_store.init_db()

    async with AsyncSessionLocal() as session:
        # 2. Tạo bản ghi Document mẫu
        doc = await vector_store.create_document(
            session, filename="bao_cao_tai_chinh_2026.pdf", s3_key="pdfs/bao_cao_tai_chinh_2026.pdf"
        )
        print(f"📄 Đã tạo Document với ID: {doc.id}")

        # 3. Chuẩn bị 3 Chunks mẫu kèm vector giả lập 768 chiều
        sample_embeddings = [generate_dummy_embedding() for _ in range(3)]
        
        chunks_data = [
            {
                "chunk_index": 0,
                "content": "Doanh thu năm 2026 của công ty đạt 500 tỷ đồng, tăng trưởng 25% so với cùng kỳ.",
                "embedding": sample_embeddings[0],
            },
            {
                "chunk_index": 1,
                "content": "Hệ thống AI Document Intelligence giúp giảm 80% thời gian xử lý hồ sơ thủ công.",
                "embedding": sample_embeddings[1],
            },
            {
                "chunk_index": 2,
                "content": "Dự án DocIntel-Cloud triển khai thành công trên AWS với chi phí hạ tầng tối ưu 0 USD.",
                "embedding": sample_embeddings[2],
            },
        ]

        # 4. Test Insert Batch
        logger.info("Đang insert batch 3 chunks vào database...")
        inserted_chunks = await vector_store.insert_chunks_batch(session, doc.id, chunks_data)
        print(f"✅ Đã lưu {len(inserted_chunks)} chunks vào PostgreSQL thành công!")

        # 5. Test Vector Similarity Search (HNSW Index)
        # Sử dụng vector trùng với chunk_1 để kiểm tra độ chính xác (kết quả Cosine Distance phải gần 0)
        query_vector = sample_embeddings[1]
        logger.info("Đang tìm kiếm Top 2 chunks tương đồng nhất bằng HNSW Cosine Search...")
        
        results = await vector_store.search_similar_chunks(session, query_vector=query_vector, top_k=2)

        print("\n🔎 KẾT QUẢ TÌM KIẾM VECTOR (TOP K SIMILARITY):")
        print("-" * 60)
        for rank, (chunk, distance) in enumerate(results, 1):
            print(f"Top {rank} [Distance: {distance:.4f}] (Khoảng cách càng nhỏ càng tương đồng):")
            print(f"  📝 Content: \"{chunk.content}\"")
            print(f"  📌 Chunk Index: {chunk.chunk_index}")
            print("-" * 60)

    print("🎉 TEST DATABASE & VECTOR INDEXING HOÀN TẢO!")

if __name__ == "__main__":
    asyncio.run(main())
