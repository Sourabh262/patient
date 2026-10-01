from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.patient import Patient


class GlucoseReading(Base):
    __tablename__ = "glucose_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("patients.patient_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    week_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    glucose_value: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    meal_context: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="random")

    # Relationship
    patient: Mapped["Patient"] = relationship("Patient", back_populates="readings")

    # Composite indexes for rapid weekly and temporal filtering
    __table_args__ = (
        Index("ix_readings_patient_week", "patient_id", "week_number"),
        Index("ix_readings_patient_timestamp", "patient_id", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<GlucoseReading P:{self.patient_id} W:{self.week_number} Val:{self.glucose_value}>"
