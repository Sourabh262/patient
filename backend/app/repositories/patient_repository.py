from typing import Optional, List
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.patient import Patient
from app.repositories.base import BaseRepository


class PatientRepository(BaseRepository[Patient]):
    def __init__(self, session: AsyncSession):
        super().__init__(Patient, session)

    async def get_by_id(self, patient_id: str) -> Optional[Patient]:
        stmt = (
            select(Patient)
            .where(Patient.patient_id == patient_id)
            .options(
                selectinload(Patient.readings),
                selectinload(Patient.reports),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[Patient]:
        stmt = select(Patient).where(Patient.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_patients(
        self, skip: int = 0, limit: int = 100, search: Optional[str] = None
    ) -> List[Patient]:
        stmt = select(Patient).order_by(Patient.patient_id.asc())
        if search:
            search_pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Patient.patient_id.ilike(search_pattern),
                    Patient.name.ilike(search_pattern),
                    Patient.email.ilike(search_pattern),
                )
            )
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, search: Optional[str] = None) -> int:
        stmt = select(func.count()).select_from(Patient)
        if search:
            search_pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Patient.patient_id.ilike(search_pattern),
                    Patient.name.ilike(search_pattern),
                    Patient.email.ilike(search_pattern),
                )
            )
        result = await self.session.execute(stmt)
        return result.scalar() or 0
