from pydantic import BaseModel, Field
from typing import List
from uuid import UUID

class CitationItem(BaseModel):
    chunk_id: UUID
    document_id: UUID
    filename: str
    chunk_index: int
    content_snippet: str
    full_content: str
    relevance_score: float

class QARequest(BaseModel):
    question: str = Field(..., description="Câu hỏi của người dùng")
    top_k: int = Field(default=8, ge=1, le=30, description="Số lượng đoạn ngữ cảnh tìm kiếm (tối đa 30 chunks)")
    stream: bool = Field(default=False, description="Tùy chọn trả về kết quả dạng streaming")

class QAResponse(BaseModel):
    question: str
    answer: str
    citations: List[CitationItem]
    execution_time_ms: float
