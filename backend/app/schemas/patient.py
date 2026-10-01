from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from app.schemas.common import PaginationMeta
from app.schemas.glucose import GlucoseReadingResponse


class PatientBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Patient full name")
    phone: str = Field(..., min_length=7, max_length=30, description="Contact phone number")
    email: EmailStr = Field(..., description="Valid patient email address for report notifications")
    address: str = Field(..., min_length=5, max_length=255, description="Physical residential address")


class PatientCreate(PatientBase):
    patient_id: str = Field(..., min_length=2, max_length=50, pattern=r"^[A-Za-z0-9_-]+$", description="Unique patient identifier, e.g. P001")


class PatientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, min_length=7, max_length=30)
    email: Optional[EmailStr] = None
    address: Optional[str] = Field(None, min_length=5, max_length=255)


class PatientResponse(PatientBase):
    patient_id: str
    created_at: datetime
    updated_at: datetime
    total_readings: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


class PatientDetailResponse(PatientResponse):
    readings: List[GlucoseReadingResponse] = []


class PatientListResponse(BaseModel):
    items: List[PatientResponse]
    meta: PaginationMeta
