from typing import List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException, status
from app.models.glucose_reading import GlucoseReading
from app.repositories.glucose_repository import GlucoseReadingRepository
from app.repositories.patient_repository import PatientRepository
from app.schemas.glucose import (
    GlucoseReadingCreate,
    GlucoseReadingResponse,
    GlucoseReadingListResponse,
)
from app.core.logging import logger


class GlucoseService:
    def __init__(
        self,
        glucose_repo: GlucoseReadingRepository,
        patient_repo: PatientRepository,
    ):
        self.glucose_repo = glucose_repo
        self.patient_repo = patient_repo

    async def get_patient_readings(
        self, patient_id: str, limit: Optional[int] = None
    ) -> GlucoseReadingListResponse:
        # Verify patient exists
        patient = await self.patient_repo.get_by_id(patient_id)
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient with ID '{patient_id}' not found.",
            )

        readings = await self.glucose_repo.get_by_patient(patient_id, limit=limit)
        items = [
            GlucoseReadingResponse(
                id=r.id,
                patient_id=r.patient_id,
                glucose_value=r.glucose_value,
                week_number=r.week_number,
                meal_context=r.meal_context,
                timestamp=r.timestamp,
            )
            for r in readings
        ]

        return GlucoseReadingListResponse(
            patient_id=patient_id,
            total_readings=len(items),
            readings=items,
        )

    async def add_reading(
        self, patient_id: str, payload: GlucoseReadingCreate
    ) -> GlucoseReadingResponse:
        patient = await self.patient_repo.get_by_id(patient_id)
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient with ID '{patient_id}' not found.",
            )

        reading = GlucoseReading(
            patient_id=patient_id,
            glucose_value=payload.glucose_value,
            week_number=payload.week_number,
            meal_context=payload.meal_context,
            timestamp=payload.timestamp or datetime.now(timezone.utc),
        )

        saved = await self.glucose_repo.create(reading)
        logger.info(
            "Added glucose reading for patient %s (Week %d: %.1f mg/dL)",
            patient_id,
            saved.week_number,
            saved.glucose_value,
        )

        return GlucoseReadingResponse(
            id=saved.id,
            patient_id=saved.patient_id,
            glucose_value=saved.glucose_value,
            week_number=saved.week_number,
            meal_context=saved.meal_context,
            timestamp=saved.timestamp,
        )

    async def get_latest_4_weeks(self, patient_id: str) -> List[GlucoseReading]:
        patient = await self.patient_repo.get_by_id(patient_id)
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient with ID '{patient_id}' not found.",
            )
        return await self.glucose_repo.get_latest_weeks_readings(patient_id, max_weeks=4)
