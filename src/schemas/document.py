from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class DocumentUploadResponse(BaseModel):
    message: str
    document_id: UUID
    filename: str
    s3_key: str
    chunks_count: int
    created_at: datetime
