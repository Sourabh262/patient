from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.glucose_reading import GlucoseReading
from app.repositories.base import BaseRepository


class GlucoseReadingRepository(BaseRepository[GlucoseReading]):
    def __init__(self, session: AsyncSession):
        super().__init__(GlucoseReading, session)

    async def get_by_patient(
        self, patient_id: str, limit: Optional[int] = None
    ) -> List[GlucoseReading]:
        stmt = (
            select(GlucoseReading)
            .where(GlucoseReading.patient_id == patient_id)
            .order_by(GlucoseReading.timestamp.asc())
        )
        if limit:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_readings_by_week(
        self, patient_id: str, week_number: int
    ) -> List[GlucoseReading]:
        stmt = (
            select(GlucoseReading)
            .where(
                GlucoseReading.patient_id == patient_id,
                GlucoseReading.week_number == week_number,
            )
            .order_by(GlucoseReading.timestamp.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_weeks_readings(
        self, patient_id: str, max_weeks: int = 4
    ) -> List[GlucoseReading]:
        stmt = (
            select(GlucoseReading)
            .where(
                GlucoseReading.patient_id == patient_id,
                GlucoseReading.week_number <= max_weeks,
                GlucoseReading.week_number >= 1,
            )
            .order_by(GlucoseReading.week_number.asc(), GlucoseReading.timestamp.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def bulk_create(self, readings: List[GlucoseReading]) -> List[GlucoseReading]:
        self.session.add_all(readings)
        await self.session.flush()
        return readings
