from datetime import datetime, timezone
from typing import List, TYPE_CHECKING
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.glucose_reading import GlucoseReading
    from app.models.report import Report


class Patient(Base):
    __tablename__ = "patients"

    patient_id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    readings: Mapped[List["GlucoseReading"]] = relationship(
        "GlucoseReading",
        back_populates="patient",
        cascade="all, delete-orphan",
        order_by="GlucoseReading.timestamp.asc()",
    )
    reports: Mapped[List["Report"]] = relationship(
        "Report",
        back_populates="patient",
        cascade="all, delete-orphan",
        order_by="Report.generated_at.desc()",
    )

    def __repr__(self) -> str:
        return f"<Patient {self.patient_id} - {self.name}>"
