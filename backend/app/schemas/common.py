from typing import Optional
from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None


class PaginationMeta(BaseModel):
    total: int
    skip: int
    limit: int
    has_more: bool
