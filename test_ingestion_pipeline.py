import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Tải biến môi trường từ .env
load_dotenv()

# Thêm đường dẫn src vào PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from services.storage import MinioStorage
from db.database import AsyncSessionLocal
from services.vector_store import VectorStore
from pipelines.chunking import PDFChunker
from pipelines.embedding import EmbeddingGenerator

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def run_pipeline():
    print("=" * 70)
    print("🚀 ĐANG CHẠY PIPELINE INGESTION TOÀN DIỆN (CHẶNG 2 + 3 + 4)")
    print("=" * 70)

    # 1. Xác định file PDF đầu vào
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_files = [f for f in os.listdir(".") if f.lower().endswith(".pdf")]
        if pdf_files:
            pdf_path = pdf_files[0]
        else:
            print("⚠️ Không tìm thấy file PDF nào!")
            print("💡 Hãy chạy: python test_ingestion_pipeline.py <duong_dan_file.pdf>")
            return

    if not os.path.exists(pdf_path):
        logger.error(f"File PDF '{pdf_path}' không tồn tại!")
        return

    filename = os.path.basename(pdf_path)
    s3_key = f"documents/{filename}"
    bucket_name = os.getenv("MINIO_BUCKET_NAME", "documents")

    # ------------------------------------------------------------------
    # BƯỚC 1: LƯU MÁY CHỦ S3 MINIO (CHẶNG 2)
    # ------------------------------------------------------------------
    logger.info(f"1. Uploading PDF '{filename}' lên MinIO S3...")
    storage = MinioStorage()
    storage.upload_file(bucket_name, pdf_path, s3_key)
    print("   ✅ Upload MinIO thành công!")

    # Lấy lại Stream dữ liệu từ MinIO
    pdf_stream = storage.get_file_stream(bucket_name, s3_key)

    # ------------------------------------------------------------------
    # BƯỚC 2: CHUNKING VĂN BẢN PDF (CHẶNG 4)
    # ------------------------------------------------------------------
    logger.info("2. Trích xuất text & Phân đoạn (Chunking) theo Sliding Window...")
    chunker = PDFChunker(chunk_size=150, overlap=30)
    raw_text = chunker.extract_text_from_pdf(pdf_stream)
    chunks = chunker.chunk_text(raw_text)

    if not chunks:
        print("⚠️ File PDF không có nội dung chữ trích xuất được (có thể là file scan dạng ảnh)!")
        return

    print(f"   ✅ Đã tạo thành công {len(chunks)} chunks từ file PDF.")

    # ------------------------------------------------------------------
    # BƯỚC 3: TẠO VECTOR EMBEDDINGS (CHẶNG 4)
    # ------------------------------------------------------------------
    logger.info("3. Đang phát sinh Vector Embeddings 768 chiều cho từng chunk...")
    embedder = EmbeddingGenerator(dimension=768)
    embeddings = await embedder.get_embeddings_batch(chunks)
    print(f"   ✅ Đã tạo {len(embeddings)} vectors embedding 768 chiều.")

    # ------------------------------------------------------------------
    # BƯỚC 4: LƯU VÀO POSTGRESQL + PGVECTOR (CHẶNG 3)
    # ------------------------------------------------------------------
    logger.info("4. Đang khởi tạo Database & Lưu trữ vào PostgreSQL (pgvector)...")
    vector_store = VectorStore()
    await vector_store.init_db()

    async with AsyncSessionLocal() as session:
        # Tạo Document Record
        doc = await vector_store.create_document(session, filename=filename, s3_key=s3_key)

        # Đóng gói dữ liệu chunks để lưu batch
        chunks_data = [
            {"chunk_index": idx, "content": text_chunk, "embedding": emb}
            for idx, (text_chunk, emb) in enumerate(zip(chunks, embeddings))
        ]

        inserted_chunks = await vector_store.insert_chunks_batch(session, doc.id, chunks_data)
        print(f"   ✅ Đã lưu Document (ID: {doc.id}) cùng {len(inserted_chunks)} Chunks vào Postgres!")

        # ------------------------------------------------------------------
        # BƯỚC 5: TÌM KIẾM THỬ NGHIỆM (COSINE SEARCH VIA HNSW)
        # ------------------------------------------------------------------
        logger.info("5. Chạy thử nghiệm Vector Search kiểm tra kết nối End-to-End...")
        sample_query_emb = embeddings[0]
        search_results = await vector_store.search_similar_chunks(session, sample_query_emb, top_k=2)

    # ------------------------------------------------------------------
    # BÁO CÁO KẾT QUẢ TRỰC QUAN CHO SENIOR
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("📊 MẪU CHUNKS VĂN BẢN TRÍCH XUẤT ĐƯỢC:")
    print("=" * 70)
    for i, c in enumerate(chunks[:3], 1):
        print(f"\n🔹 CHUNK #{i}:")
        print(f"   \"{c[:200]}...\"")
        print("-" * 50)

    print("\n🔎 KẾT QUẢ TÌM KIẾM VECTOR SIMILARITY TRONG DATABASE:")
    print("=" * 70)
    for rank, (chunk_obj, dist) in enumerate(search_results, 1):
        print(f"Top {rank} [Distance: {dist:.4f}]: \"{chunk_obj.content[:100]}...\"")

    print("\n🎉 TOÀN BỘ FLOW CHẶNG 2 + 3 + 4 ĐÃ HOÀN THÀNH XUẤT SẮC!")

if __name__ == "__main__":
    asyncio.run(run_pipeline())
