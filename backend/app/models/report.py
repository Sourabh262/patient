from datetime import datetime, timezone
from typing import Dict, Any, Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.patient import Patient


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("patients.patient_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    weekly_averages: Mapped[Dict[str, Optional[float]]] = mapped_column(JSON, nullable=False)
    weekly_stages: Mapped[Dict[str, str]] = mapped_column(JSON, nullable=False)
    current_stage: Mapped[str] = mapped_column(String(50), nullable=False)
    trend: Mapped[str] = mapped_column(String(50), nullable=False)  # improving, worsening, stable, insufficient_data
    ai_summary: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    email_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    email_recipient: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationship
    patient: Mapped["Patient"] = relationship("Patient", back_populates="reports")

    def __repr__(self) -> str:
        return f"<Report {self.id} for {self.patient_id} - Stage: {self.current_stage}>"
