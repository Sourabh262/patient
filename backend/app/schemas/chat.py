from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Natural language query for the clinical assistant")


class ChatResponse(BaseModel):
    response: str
    patient_id: Optional[str] = None
    messages: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
