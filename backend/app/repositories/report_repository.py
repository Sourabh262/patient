from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.report import Report
from app.repositories.base import BaseRepository


class ReportRepository(BaseRepository[Report]):
    def __init__(self, session: AsyncSession):
        super().__init__(Report, session)

    async def get_latest_by_patient(self, patient_id: str) -> Optional[Report]:
        stmt = (
            select(Report)
            .where(Report.patient_id == patient_id)
            .order_by(Report.generated_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_patient(self, patient_id: str) -> List[Report]:
        stmt = (
            select(Report)
            .where(Report.patient_id == patient_id)
            .order_by(Report.generated_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_recent(self, limit: int = 10) -> List[Report]:
        stmt = select(Report).order_by(Report.generated_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def mark_email_sent(self, report_id: int, recipient: str) -> Optional[Report]:
        report = await self.get(report_id)
        if report:
            report.email_sent = True
            report.email_sent_at = datetime.now(timezone.utc)
            report.email_recipient = recipient
            await self.session.flush()
            await self.session.refresh(report)
        return report
