import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from fastapi import HTTPException, status
from langchain_core.messages import SystemMessage, HumanMessage
from app.models.report import Report
from app.models.patient import Patient
from app.repositories.report_repository import ReportRepository
from app.repositories.patient_repository import PatientRepository
from app.repositories.glucose_repository import GlucoseReadingRepository
from app.services.glucose_calculator import calculate_4_week_report
from app.schemas.report import (
    FullPatientReportResponse,
    PatientInfoSummary,
    ReportResponse,
)
from app.agent.llm import get_llm
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

    async def generate_ai_summary(self, patient: Patient, calc: Any) -> str:
        """Sends verified calculated metrics to the LLM to generate a concise, patient-friendly summary.
        Strictly prohibits hallucination of outside values.
        """
        w1_avg = calc.weekly_averages.get("week_1")
        w2_avg = calc.weekly_averages.get("week_2")
        w3_avg = calc.weekly_averages.get("week_3")
        w4_avg = calc.weekly_averages.get("week_4")

        w1_str = f"{w1_avg:.1f} mg/dL" if w1_avg is not None else "No readings"
        w2_str = f"{w2_avg:.1f} mg/dL" if w2_avg is not None else "No readings"
        w3_str = f"{w3_avg:.1f} mg/dL" if w3_avg is not None else "No readings"
        w4_str = f"{w4_avg:.1f} mg/dL" if w4_avg is not None else "No readings"

        system_instruction = (
            "You are a clinical endocrinology reporting assistant. "
            "Write a concise, patient-friendly 2-3 sentence clinical summary based STRICTLY "
            "on the verified metrics provided. You must NEVER fabricate or modify numbers, stages, or patient details."
        )

        user_prompt = (
            f"Patient Information:\n"
            f"- Name: {patient.name}\n"
            f"- ID: {patient.patient_id}\n\n"
            f"Verified 4-Week Glucose Telemetry:\n"
            f"- Week 1 Average: {w1_str} ({calc.weekly_stages.get('week_1')})\n"
            f"- Week 2 Average: {w2_str} ({calc.weekly_stages.get('week_2')})\n"
            f"- Week 3 Average: {w3_str} ({calc.weekly_stages.get('week_3')})\n"
            f"- Week 4 Average: {w4_str} ({calc.weekly_stages.get('week_4')})\n"
            f"- Current Classification: {calc.current_stage}\n"
            f"- Overall 4-Week Trend: {calc.trend}\n"
            f"- Valid Readings Analyzed: {calc.total_readings_analyzed}\n\n"
            f"Please generate the verified clinical summary."
        )

        try:
            llm = get_llm(temperature=0.0)
            res = await llm.ainvoke([SystemMessage(content=system_instruction), HumanMessage(content=user_prompt)])
            summary = res.content.strip() if hasattr(res, "content") and res.content else ""
            if summary and len(summary) > 15:
                return summary
        except Exception as e:
            logger.warning("LLM summary generation failed (%s). Using verified deterministic summary template.", e)

        # Verified deterministic clinical fallback (no hallucinations)
        return (
            f"Patient {patient.name} ({patient.patient_id}) has completed 4 weeks of continuous glucose monitoring. "
            f"Their latest glucose status is classified as {calc.current_stage} with an overall '{calc.trend}' trajectory. "
            f"Weekly averages recorded: Week 1: {w1_str} ({calc.weekly_stages.get('week_1')}), "
            f"Week 2: {w2_str} ({calc.weekly_stages.get('week_2')}), "
            f"Week 3: {w3_str} ({calc.weekly_stages.get('week_3')}), "
            f"Week 4: {w4_str} ({calc.weekly_stages.get('week_4')}). "
            f"Total readings analyzed: {calc.total_readings_analyzed}."
        )

    async def generate_and_save_report(
        self, patient_id: str, custom_summary: Optional[str] = None
    ) -> Report:
        """Generates a complete 4-week clinical report, calculates averages/stages/trend,
        attaches AI clinical summary, and persists to database.
        """
        clean_id = patient_id.strip().upper()

        patient = await self.patient_repo.get_by_id(clean_id)
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient with ID '{clean_id}' not found.",
            )

        readings = await self.glucose_repo.get_latest_weeks_readings(clean_id, max_weeks=4)
        calc = calculate_4_week_report(patient_id=clean_id, readings=readings)

        ai_summary = custom_summary or await self.generate_ai_summary(patient, calc)

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

    async def get_full_report(self, report_id: int) -> FullPatientReportResponse:
        report = await self.report_repo.get(report_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report with ID '{report_id}' not found.",
            )
        patient = await self.patient_repo.get_by_id(report.patient_id)
        return self._format_full_report(patient, report)

    async def get_latest_report(self, patient_id: str) -> Optional[Report]:
        clean_id = patient_id.strip().upper()
        return await self.report_repo.get_latest_by_patient(clean_id)

    async def get_latest_full_report(self, patient_id: str) -> FullPatientReportResponse:
        clean_id = patient_id.strip().upper()
        patient = await self.patient_repo.get_by_id(clean_id)
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient with ID '{clean_id}' not found.",
            )

        report = await self.report_repo.get_latest_by_patient(clean_id)
        if not report:
            # Generate automatically if none exists
            report = await self.generate_and_save_report(clean_id)

        return self._format_full_report(patient, report)

    async def list_patient_reports(self, patient_id: str) -> List[Report]:
        clean_id = patient_id.strip().upper()
        return await self.report_repo.list_by_patient(clean_id)

    async def list_recent_reports(self, limit: int = 10) -> List[Report]:
        return await self.report_repo.list_recent(limit=limit)

    async def mark_report_emailed(self, report_id: int, recipient: str) -> Optional[Report]:
        return await self.report_repo.mark_email_sent(report_id, recipient=recipient)

    def _format_full_report(self, patient: Optional[Patient], report: Report) -> FullPatientReportResponse:
        return FullPatientReportResponse(
            report_id=report.id,
            generated_at=report.generated_at,
            patient=PatientInfoSummary(
                patient_id=patient.patient_id if patient else report.patient_id,
                name=patient.name if patient else "Unknown",
                phone=patient.phone if patient else "Unknown",
                email=patient.email if patient else "Unknown",
                address=patient.address if patient else "Unknown",
            ),
            weekly_averages=report.weekly_averages,
            weekly_stages=report.weekly_stages,
            current_stage=report.current_stage,
            trend=report.trend,
            ai_summary=report.ai_summary,
            email_sent=report.email_sent,
            email_sent_at=report.email_sent_at,
            email_recipient=report.email_recipient,
        )
