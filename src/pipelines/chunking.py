import io
import re
import logging
from typing import List, Union
from pypdf import PdfReader

logger = logging.getLogger(__name__)

class PDFChunker:
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        """
        Khởi tạo Chunker với kích thước cửa sổ trượt (sliding window).
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    def clean_text(self, text: str) -> str:
        """
        Làm sạch văn bản: Loại bỏ ký tự NUL (\x00) và các ký tự điều khiển lỗi UTF-8.
        PostgreSQL không chấp nhận ký tự \x00 trong cột văn bản TEXT/VARCHAR.
        """
        if not text:
            return ""
        # Loại bỏ ký tự NUL \x00
        text = text.replace("\x00", "")
        # Loại bỏ các ký tự điều khiển ASCII ngoại trừ newline (\n), tab (\t), carriage return (\r)
        text = re.sub(r'[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        return text

    def extract_text_from_pdf(self, pdf_input: Union[str, io.BytesIO]) -> str:
        """
        Trích xuất toàn bộ văn bản (raw text) từ file PDF và làm sạch UTF-8.
        """
        try:
            reader = PdfReader(pdf_input)
            text_content = []
            for page_idx, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    cleaned_page = self.clean_text(page_text)
                    text_content.append(cleaned_page)
            
            full_text = "\n".join(text_content)
            logger.info(f"Trích xuất thành công {len(reader.pages)} trang PDF với {len(full_text)} ký tự.")
            return full_text
        except Exception as e:
            logger.error(f"Lỗi khi đọc file PDF bằng pypdf: {e}")
            raise e

    def chunk_text(self, text: str) -> List[str]:
        """
        Cắt đoạn văn bản thành danh sách các chunks theo kỹ thuật Sliding Window.
        """
        text = self.clean_text(text)
        if not text or not text.strip():
            return []

        words = text.split()
        total_words = len(words)

        if total_words <= self.chunk_size:
            return [" ".join(words)]

        chunks = []
        step = self.chunk_size - self.overlap
        if step <= 0:
            step = self.chunk_size

        for i in range(0, total_words, step):
            chunk_words = words[i : i + self.chunk_size]
            chunk_str = " ".join(chunk_words)
            cleaned_chunk = self.clean_text(chunk_str)
            if cleaned_chunk.strip():
                chunks.append(cleaned_chunk)

        logger.info(f"Đã chia văn bản thành {len(chunks)} chunks (Size: {self.chunk_size}, Overlap: {self.overlap}).")
        return chunks
