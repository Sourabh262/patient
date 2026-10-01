from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class WeeklyMetric(BaseModel):
    week_number: int = Field(..., ge=1, le=52)
    average_glucose: Optional[float] = Field(None, description="Average glucose in mg/dL rounded to 1 decimal place")
    stage: str = Field(..., description="Stage classification: Normal, Pre-diabetes, Diabetes, Hypoglycemia, Insufficient Data")
    reading_count: int = Field(0, description="Total valid readings recorded in this week")


class FourWeekCalculationResult(BaseModel):
    patient_id: str
    weeks: List[WeeklyMetric]
    weekly_averages: Dict[str, Optional[float]]
    weekly_stages: Dict[str, str]
    current_stage: str
    trend: str  # improving, worsening, stable, fluctuating, insufficient_data
    total_readings_analyzed: int
    has_sufficient_data: bool

    model_config = ConfigDict(from_attributes=True)


class ReportCreate(BaseModel):
    patient_id: str


class PatientInfoSummary(BaseModel):
    patient_id: str
    name: str
    phone: str
    email: str
    address: str

    model_config = ConfigDict(from_attributes=True)


class FullPatientReportResponse(BaseModel):
    report_id: int
    generated_at: datetime
    patient: PatientInfoSummary
    weekly_averages: Dict[str, Optional[float]]
    weekly_stages: Dict[str, str]
    current_stage: str
    trend: str
    ai_summary: str
    email_sent: bool = False
    email_sent_at: Optional[datetime] = None
    email_recipient: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ReportResponse(BaseModel):
    id: int
    patient_id: str
    weekly_averages: Dict[str, Optional[float]]
    weekly_stages: Dict[str, str]
    current_stage: str
    trend: str
    ai_summary: str
    generated_at: datetime
    email_sent: bool = False
    email_sent_at: Optional[datetime] = None
    email_recipient: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
