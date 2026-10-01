import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from fastapi import HTTPException, status
from app.models.report import Report
from app.repositories.report_repository import ReportRepository
from app.repositories.patient_repository import PatientRepository
from app.repositories.glucose_repository import GlucoseReadingRepository
from app.services.glucose_calculator import calculate_4_week_report
from app.schemas.report import ReportResponse
from app.core.logging import logger


class ReportService:
    def __init__(
        self,
        report_repo: ReportRepository,
        patient_repo: PatientRepository,
        glucose_repo: GlucoseReadingRepository,
    ):
        self.report_repo = report_repo
        self.patient_repo = patient_repo
        self.glucose_repo = glucose_repo

    async def generate_and_save_report(self, patient_id: str, ai_summary: Optional[str] = None) -> Report:
        """Generates a complete 4-week clinical report, calculates averages/stages/trend,
        attaches AI clinical summary, and persists to database.
        """
        clean_id = patient_id.strip().upper()

        # 1. Verify patient exists
        patient = await self.patient_repo.get_by_id(clean_id)
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient with ID '{clean_id}' not found.",
            )

        # 2. Get latest 4 weeks readings
        readings = await self.glucose_repo.get_latest_weeks_readings(clean_id, max_weeks=4)

        # 3. Deterministically calculate metrics
        calc = calculate_4_week_report(patient_id=clean_id, readings=readings)

        # 4. Synthesize AI summary if not provided
        if not ai_summary:
            ai_summary = (
                f"Patient {patient.name} ({clean_id}) has completed 4-week glycemic monitoring. "
                f"Current stage is classified as {calc.current_stage} with an overall '{calc.trend}' trajectory. "
                f"Weekly averages: W1: {calc.weekly_averages.get('week_1')} mg/dL ({calc.weekly_stages.get('week_1')}), "
                f"W2: {calc.weekly_averages.get('week_2')} mg/dL ({calc.weekly_stages.get('week_2')}), "
                f"W3: {calc.weekly_averages.get('week_3')} mg/dL ({calc.weekly_stages.get('week_3')}), "
                f"W4: {calc.weekly_averages.get('week_4')} mg/dL ({calc.weekly_stages.get('week_4')}). "
                f"Total valid readings analyzed: {calc.total_readings_analyzed}."
            )

        report = Report(
            patient_id=clean_id,
            weekly_averages=calc.weekly_averages,
            weekly_stages=calc.weekly_stages,
            current_stage=calc.current_stage,
            trend=calc.trend,
            ai_summary=ai_summary,
            generated_at=datetime.now(timezone.utc),
            email_sent=False,
        )

        saved = await self.report_repo.create(report)
        logger.info("Saved clinical report ID %d for patient %s", saved.id, clean_id)
        return saved

    async def get_latest_report(self, patient_id: str) -> Optional[Report]:
        clean_id = patient_id.strip().upper()
        return await self.report_repo.get_latest_by_patient(clean_id)

    async def list_patient_reports(self, patient_id: str) -> List[Report]:
        clean_id = patient_id.strip().upper()
        return await self.report_repo.list_by_patient(clean_id)

    async def list_recent_reports(self, limit: int = 10) -> List[Report]:
        return await self.report_repo.list_recent(limit=limit)

    async def mark_report_emailed(self, report_id: int, recipient: str) -> Optional[Report]:
        return await self.report_repo.mark_email_sent(report_id, recipient=recipient)
