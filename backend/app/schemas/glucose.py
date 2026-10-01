from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict


class GlucoseReadingBase(BaseModel):
    glucose_value: float = Field(..., ge=20.0, le=600.0, description="Glucose level in mg/dL (20-600)")
    week_number: int = Field(..., ge=1, le=52, description="Monitoring week number (typically 1-4)")
    meal_context: Optional[str] = Field("random", description="Meal context: fasting, post_prandial, bedtime, random")


class GlucoseReadingCreate(GlucoseReadingBase):
    timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("glucose_value")
    @classmethod
    def validate_glucose_value(cls, v: float) -> float:
        if v < 20.0 or v > 600.0:
            raise ValueError("Glucose reading must be between 20.0 and 600.0 mg/dL")
        return round(v, 1)


class GlucoseReadingResponse(GlucoseReadingBase):
    id: int
    patient_id: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class GlucoseReadingListResponse(BaseModel):
    patient_id: str
    total_readings: int
    readings: List[GlucoseReadingResponse]
