import os
import random
import logging
from typing import List
import httpx
from dotenv import load_dotenv

# Load biến môi trường từ file .env
load_dotenv()

logger = logging.getLogger(__name__)

# Thử import sentence_transformers nếu có (Local CPU Embeddings - Không cần API Key)
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

# Thử import SDK google.generativeai nếu có
try:
    import google.generativeai as genai
    HAS_GENAI_SDK = True
except ImportError:
    HAS_GENAI_SDK = False

class EmbeddingGenerator:
    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/embeddings")
        self.ollama_model = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self._ollama_available = None
        self._st_model = None

        # 1. Khởi tạo SentenceTransformers local nếu có thư viện
        if HAS_SENTENCE_TRANSFORMERS:
            try:
                # Dùng model bge-small-en-v1.5 hoặc all-MiniLM-L6-v2 chạy nhẹ trên CPU
                logger.info("📦 Đang tải/khởi tạo mô hình SentenceTransformers chạy local trên CPU...")
                self._st_model = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception as e:
                logger.warning(f"Không thể load SentenceTransformers: {e}")

        # 2. Khởi tạo Gemini SDK nếu có key
        if self.gemini_api_key and HAS_GENAI_SDK:
            try:
                genai.configure(api_key=self.gemini_api_key)
            except Exception as e:
                logger.warning(f"Không thể cấu hình Google GenAI SDK: {e}")

    async def _check_ollama(self) -> bool:
        """Kiểm tra nhanh trong 0.3 giây xem Ollama local có đang chạy không"""
        if self._ollama_available is not None:
            return self._ollama_available
        try:
            async with httpx.AsyncClient(timeout=0.3) as client:
                resp = await client.get("http://localhost:11434/api/version")
                self._ollama_available = (resp.status_code == 200)
        except Exception:
            self._ollama_available = False
        return self._ollama_available

    async def get_embedding(self, text: str) -> List[float]:
        """
        Tạo vector embedding 768 chiều.
        Ưu tiên: SentenceTransformers Local -> Ollama -> Gemini -> Mock
        """
        # 1. Thử dùng SentenceTransformers Local trên CPU (Chạy nhanh, 0-Cost, Không cần Key)
        if self._st_model:
            try:
                vec = self._st_model.encode(text, convert_to_numpy=True).tolist()
                # Nếu vector có kích thước khác (vd 384), bù/cắt cho chuẩn 768 chiều DB
                if len(vec) < self.dimension:
                    vec = vec + [0.0] * (self.dimension - len(vec))
                return vec[:self.dimension]
            except Exception as e:
                logger.warning(f"Lỗi SentenceTransformers: {e}")

        # 2. Thử gọi Ollama Local nếu đang chạy
        if await self._check_ollama():
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.post(
                        self.ollama_url,
                        json={"model": self.ollama_model, "prompt": text}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        embedding = data.get("embedding", [])
                        if len(embedding) == self.dimension:
                            return embedding
            except Exception:
                pass

        # 3. Thử gọi qua SDK google.generativeai chính thức
        if self.gemini_api_key and HAS_GENAI_SDK:
            for model_name in ["models/text-embedding-004", "models/embedding-001"]:
                try:
                    result = genai.embed_content(
                        model=model_name,
                        content=text[:2000],
                        task_type="retrieval_document",
                    )
                    values = result.get("embedding", [])
                    if len(values) > 0:
                        if len(values) < self.dimension:
                            values = values + [0.0] * (self.dimension - len(values))
                        return values[:self.dimension]
                except Exception:
                    pass

        # 4. Fallback: Mock Generator
        random.seed(hash(text))
        return [random.uniform(-1.0, 1.0) for _ in range(self.dimension)]

    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Tạo vector embedding cho danh sách văn bản.
        """
        if self._st_model:
            logger.info("🚀 Đang dùng SentenceTransformers chạy trực tiếp trên CPU (Offline, 0-Cost, Không cần Key)...")
        elif await self._check_ollama():
            logger.info("⚡ Đang dùng Ollama Local (nomic-embed-text) phát sinh embeddings...")
        elif self.gemini_api_key:
            logger.info("✨ Đang dùng Google Gemini API phát sinh embeddings...")
        else:
            logger.warning("⚠️ Đang dùng Mock Vector Generator giả lập...")

        embeddings = []
        for text in texts:
            emb = await self.get_embedding(text)
            embeddings.append(emb)
        return embeddings
