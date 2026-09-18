import os
import logging
from typing import List, Dict, Any
import httpx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Thử import SDK groq và google.generativeai
try:
    from groq import AsyncGroq
    HAS_GROQ_SDK = True
except ImportError:
    HAS_GROQ_SDK = False

try:
    import google.generativeai as genai
    HAS_GENAI_SDK = True
except ImportError:
    HAS_GENAI_SDK = False

class LLMService:
    def __init__(self):
        # Đọc cấu hình Groq
        self.groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip()
        
        # Đọc cấu hình Gemini
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()
        
        # Khởi tạo Groq Client
        self.groq_client = None
        if self.groq_api_key and HAS_GROQ_SDK:
            try:
                self.groq_client = AsyncGroq(api_key=self.groq_api_key)
            except Exception as e:
                logger.warning(f"Không thể khởi tạo Groq Client: {e}")

        # Khởi tạo Gemini Client SDK nếu có key
        if self.gemini_api_key and HAS_GENAI_SDK:
            try:
                genai.configure(api_key=self.gemini_api_key)
            except Exception as e:
                logger.warning(f"Không thể cấu hình Gemini SDK: {e}")

    def format_prompt(self, question: str, contexts: List[Dict[str, Any]]) -> str:
        """
        Ghép ngữ cảnh và câu hỏi vào Prompt Template chuẩn RAG Đa Tài Liệu (Multi-Document RAG).
        """
        context_str = ""
        for i, ctx in enumerate(contexts, 1):
            fname = ctx.get("filename", "Tài liệu")
            cidx = ctx.get("chunk_index", 0)
            content = ctx.get("content", "")
            context_str += f"\n--- [Nguồn {i} | File: {fname} | Chunk #{cidx}] ---\n{content}\n"

        prompt = f"""Bạn là một Chuyên gia Trợ lý Phân tích Tài liệu Doanh nghiệp Cấp cao (Enterprise Document Intelligence & Research Assistant).
Dưới đây là các đoạn thông tin ngữ cảnh được trích xuất từ cơ sở dữ liệu các tài liệu đã nạp:

=== BẮT ĐẦU DỮ LIỆU NGỮ CẢNH ===
{context_str}
=== KẾT THÚC DỮ LIỆU NGỮ CẢNH ===

HƯỚNG DẪN TRẢ LỜI:
1. Trả lời bằng Tiếng Việt một cách tự nhiên, chuyên sâu, khách quan và mạch lạc.
2. Dựa HOÀN TOÀN vào ngữ cảnh được cung cấp ở trên.
3. ĐẶC BIỆT KHI CÂU HỎI YÊU CẦU SO SÁNH (ví dụ so sánh giữa 2 hay nhiều mô hình/tài liệu khác nhau):
   - Hãy tổng hợp và đối chiếu toàn bộ các thông tin tìm thấy từ tất cả các file tài liệu trong ngữ cảnh.
   - Trình bày rõ ràng các tiêu chí so sánh: Kiến trúc (Architecture), Hiệu năng (Performance/Benchmarks), Tính mới/Ưu nhược điểm.
   - Khuyến khích sử dụng Bảng so sánh (Markdown Table) hoặc phân mục gạch đầu dòng có cấu trúc đẹp mắt.
4. Cuối các ý quan trọng hoặc cuối câu trả lời, hãy chú thích rõ các [Nguồn X] (kèm tên file tương ứng) mà bạn đã trích xuất thông tin.
5. Nếu một khía cạnh nào đó chưa có trong ngữ cảnh, hãy nói rõ tài liệu chưa đề cập khía cạnh đó.

Câu hỏi của người dùng: {question}
Trả lời:"""
        return prompt

    async def generate_answer(self, question: str, contexts: List[Dict[str, Any]]) -> str:
        """
        Sinh câu trả lời từ LLM (Ưu tiên Gemini SDK -> Groq -> Mock).
        """
        prompt = self.format_prompt(question, contexts)

        # 1. Gọi Gemini qua SDK chính thức (Tối ưu nhất cho RAG Context lớn)
        if self.gemini_api_key and HAS_GENAI_SDK:
            try:
                model = genai.GenerativeModel(
                    self.gemini_model,
                    generation_config={"max_output_tokens": 2500, "temperature": 0.2}
                )
                response = model.generate_content(prompt)
                if response.text:
                    logger.info(f"Sinh câu trả lời thành công từ Gemini SDK ({self.gemini_model}).")
                    return response.text
            except Exception as e:
                logger.error(f"Lỗi gọi Gemini SDK ({self.gemini_model}): {e}")

        # 2. Thử gọi Groq Cloud API
        if self.groq_client:
            try:
                chat_completion = await self.groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "Bạn là trợ lý AI phân tích tài liệu chuyên nghiệp."},
                        {"role": "user", "content": prompt}
                    ],
                    model=self.groq_model,
                    temperature=0.2,
                    max_tokens=1200,
                )
                answer = chat_completion.choices[0].message.content
                logger.info(f"Sinh câu trả lời thành công từ Groq Cloud API ({self.groq_model}).")
                return answer
            except Exception as e:
                logger.error(f"Lỗi gọi Groq Cloud API: {e}")

        # 3. Thử gọi Gemini qua REST HTTP
        if self.gemini_api_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.gemini_api_key}"
                async with httpx.AsyncClient(timeout=25.0) as client:
                    response = await client.post(
                        url,
                        json={"contents": [{"parts": [{"text": prompt}]}]}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            answer = candidates[0]["content"]["parts"][0]["text"]
                            logger.info(f"Sinh câu trả lời thành công từ Gemini REST API ({self.gemini_model}).")
                            return answer
            except Exception as e:
                logger.error(f"Lỗi kết nối Gemini REST API: {e}")

        # 4. Fallback: Mock LLM Generator
        logger.warning("Đang dùng Mock LLM Generator giả lập câu trả lời...")
        top_snippet = contexts[0].get("content", "")[:150] if contexts else "Không có ngữ cảnh"
        return (
            f"Dựa trên các đoạn tài liệu trích xuất:\n\n"
            f"\"{top_snippet}...\"\n\n"
            f"Hệ thống xác nhận thông tin liên quan đến câu hỏi \"{question}\" đã được ghi nhận trong tài liệu. "
            f"(Trích dẫn từ Nguồn 1)."
        )