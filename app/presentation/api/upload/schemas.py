from typing import List, Optional
from pydantic import BaseModel


class UploadResponse(BaseModel):
    id: str
    filename: str
    status: str
    uploaded_at: str
    uploaded_by_user_id: Optional[str]


class UploadListResponse(BaseModel):
    items: List[UploadResponse]
    total: int
    limit: int
    offset: int
