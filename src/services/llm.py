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
        
        # Đọc cấu hình Gemini (Có thể tùy chỉnh GEMINI_MODEL linh hoạt)
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
        Ghép ngữ cảnh và câu hỏi vào Prompt Template chuẩn RAG.
        """
        context_str = ""
        for i, ctx in enumerate(contexts, 1):
            context_str += f"\n[Nguồn {i} - Chunk Index {ctx.get('chunk_index')}]:\n{ctx.get('content')}\n"

        prompt = f"""Bạn là một Chuyên gia Trợ lý Phân tích Tài liệu Doanh nghiệp (DocIntel AI Assistant).
Dưới đây là các thông tin ngữ cảnh được trích xuất trực tiếp từ cơ sở dữ liệu tài liệu:

--- BẮT ĐẦU NGỮ CẢNH ---
{context_str}
--- KẾT THÚC NGỮ CẢNH ---

Nhiệm vụ của bạn:
1. Dựa VÀO ĐÚNG ngữ cảnh được cung cấp ở trên để trả lời câu hỏi của người dùng.
2. Trả lời một cách chính xác, ngắn gọn, súc tích và có cấu trúc rõ ràng.
3. Nếu ngữ cảnh không chứa đủ thông tin để trả lời, hãy lịch sự thông báo rằng tài liệu chưa đề cập đến nội dung này.
4. Cuối câu trả lời, hãy trích dẫn các [Nguồn X] tương ứng mà bạn đã sử dụng.

Câu hỏi của người dùng: {question}
Trả lời:"""
        return prompt

    async def generate_answer(self, question: str, contexts: List[Dict[str, Any]]) -> str:
        """
        Sinh câu trả lời từ LLM (Ưu tiên Groq Cloud -> Gemini -> Mock).
        """
        prompt = self.format_prompt(question, contexts)

        # 1. Thử gọi Groq Cloud API
        if self.groq_client:
            try:
                chat_completion = await self.groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "Bạn là trợ lý AI phân tích tài liệu chuyên nghiệp."},
                        {"role": "user", "content": prompt}
                    ],
                    model=self.groq_model,
                    temperature=0.2,
                    max_tokens=500, # Giảm max_tokens để tránh dính Rate Limit của Groq Free Tier
                )
                answer = chat_completion.choices[0].message.content
                logger.info(f"Sinh câu trả lời thành công từ Groq Cloud API ({self.groq_model}).")
                return answer
            except Exception as e:
                logger.error(f"Lỗi gọi Groq Cloud API: {e}")

        # 2. Thử gọi Gemini qua SDK chính thức (Tự chọn model từ GEMINI_MODEL)
        if self.gemini_api_key and HAS_GENAI_SDK:
            try:
                model = genai.GenerativeModel(self.gemini_model)
                response = model.generate_content(prompt)
                if response.text:
                    logger.info(f"Sinh câu trả lời thành công từ Gemini SDK ({self.gemini_model}).")
                    return response.text
            except Exception as e:
                logger.error(f"Lỗi gọi Gemini SDK ({self.gemini_model}): {e}")

        # 3. Thử gọi Gemini qua REST HTTP động (Nếu chưa cài SDK)
        if self.gemini_api_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.gemini_api_key}"
                async with httpx.AsyncClient(timeout=15.0) as client:
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
                    else:
                        logger.error(f"Lỗi Gemini REST API HTTP {response.status_code}: {response.text}")
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