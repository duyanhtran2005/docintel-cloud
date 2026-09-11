from pydantic import BaseModel, Field
from typing import List
from uuid import UUID

class SearchRequest(BaseModel):
    query: str = Field(..., description="Câu truy vấn tìm kiếm văn bản")
    top_k: int = Field(default=5, ge=1, le=20, description="Số lượng kết quả trả về")

class SearchResultItem(BaseModel):
    chunk_id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    distance: float

class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[SearchResultItem]
