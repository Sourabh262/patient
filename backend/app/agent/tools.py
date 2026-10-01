import json
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from app.db.session import AsyncSessionLocal
from app.repositories.patient_repository import PatientRepository
from app.repositories.glucose_repository import GlucoseReadingRepository
from app.repositories.report_repository import ReportRepository
from app.services.patient_service import PatientService
from app.services.glucose_service import GlucoseService
from app.services.report_service import ReportService
from app.services.email_service import EmailService
from app.services.glucose_calculator import calculate_4_week_report
from app.core.logging import logger


class PatientToolInput(BaseModel):
    patient_id: str = Field(..., description="Unique patient identifier, e.g., 'P015' or 'P001'")


@tool(args_schema=PatientToolInput)
async def get_patient(patient_id: str) -> str:
    """Retrieve demographic information and contact details for a specific registered patient.
    Input must be a valid patient_id (e.g. 'P015').
    """
    clean_id = patient_id.strip().upper()
    async with AsyncSessionLocal() as session:
        repo = PatientRepository(session)
        service = PatientService(repo)
        try:
            patient = await service.get_patient(clean_id)
            return json.dumps(
                {
                    "patient_id": patient.patient_id,
                    "name": patient.name,
                    "phone": patient.phone,
                    "email": patient.email,
                    "address": patient.address,
                },
                indent=2,
            )
        except Exception as e:
            logger.warning("get_patient tool error for %s: %s", clean_id, str(e))
            return json.dumps({"error": f"Patient with ID '{clean_id}' was not found in the registry."})


@tool(args_schema=PatientToolInput)
async def get_glucose_readings(patient_id: str) -> str:
    """Retrieve the raw glucose telemetry history and readings for a patient across all weeks.
    Input must be a valid patient_id.
    """
    clean_id = patient_id.strip().upper()
    async with AsyncSessionLocal() as session:
        p_repo = PatientRepository(session)
        g_repo = GlucoseReadingRepository(session)
        service = GlucoseService(g_repo, p_repo)
        try:
            res = await service.get_patient_readings(clean_id)
            readings_data = [
                {
                    "week": r.week_number,
                    "glucose_value": r.glucose_value,
                    "meal_context": r.meal_context,
                    "timestamp": r.timestamp.isoformat(),
                }
                for r in res.readings
            ]
            return json.dumps(
                {
                    "patient_id": clean_id,
                    "total_readings": len(readings_data),
                    "readings": readings_data,
                },
                indent=2,
            )
        except Exception as e:
            logger.warning("get_glucose_readings error for %s: %s", clean_id, str(e))
            return json.dumps({"error": f"Could not retrieve readings for patient '{clean_id}'. {str(e)}"})


@tool(args_schema=PatientToolInput)
async def calculate_glucose_report(patient_id: str) -> str:
    """Deterministically calculate 4-week glucose averages, clinical stage for each week,
    current stage, and 4-week trend for a patient.
    """
    clean_id = patient_id.strip().upper()
    async with AsyncSessionLocal() as session:
        p_repo = PatientRepository(session)
        g_repo = GlucoseReadingRepository(session)
        service = GlucoseService(g_repo, p_repo)
        try:
            result = await service.calculate_4_week_summary(clean_id)
            return json.dumps(
                {
                    "patient_id": result.patient_id,
                    "weekly_averages": result.weekly_averages,
                    "weekly_stages": result.weekly_stages,
                    "current_stage": result.current_stage,
                    "trend": result.trend,
                    "total_readings_analyzed": result.total_readings_analyzed,
                    "has_sufficient_data": result.has_sufficient_data,
                },
                indent=2,
            )
        except Exception as e:
            logger.warning("calculate_glucose_report error for %s: %s", clean_id, str(e))
            return json.dumps({"error": f"Failed to compute glucose averages for '{clean_id}'. {str(e)}"})


@tool(args_schema=PatientToolInput)
async def generate_report(patient_id: str) -> str:
    """Generate a comprehensive 4-week clinical glucose report including patient demographics,
    weekly averages, weekly stages, current stage, trend, and verified AI clinical summary.
    Saves the report to the database.
    """
    clean_id = patient_id.strip().upper()
    async with AsyncSessionLocal() as session:
        p_repo = PatientRepository(session)
        g_repo = GlucoseReadingRepository(session)
        r_repo = ReportRepository(session)
        service = ReportService(r_repo, p_repo, g_repo)

        try:
            saved = await service.generate_and_save_report(clean_id)
            patient = await p_repo.get_by_id(clean_id)
            return json.dumps(
                {
                    "report_id": saved.id,
                    "patient_id": clean_id,
                    "patient_name": patient.name if patient else "",
                    "email": patient.email if patient else "",
                    "weekly_averages": saved.weekly_averages,
                    "weekly_stages": saved.weekly_stages,
                    "current_stage": saved.current_stage,
                    "trend": saved.trend,
                    "ai_summary": saved.ai_summary,
                },
                indent=2,
            )
        except Exception as e:
            logger.warning("generate_report tool error for %s: %s", clean_id, str(e))
            return json.dumps({"error": f"Failed generating report for '{clean_id}': {str(e)}"})


@tool(args_schema=PatientToolInput)
async def send_email(patient_id: str) -> str:
    """Send the latest verified 4-week glucose clinical report to the patient's registered email address.
    """
    clean_id = patient_id.strip().upper()
    from app.services.email_service import EmailService

    async with AsyncSessionLocal() as session:
        p_repo = PatientRepository(session)
        g_repo = GlucoseReadingRepository(session)
        r_repo = ReportRepository(session)
        rep_service = ReportService(r_repo, p_repo, g_repo)
        email_service = EmailService()

        patient = await p_repo.get_by_id(clean_id)
        if not patient:
            return json.dumps({"error": f"Patient '{clean_id}' not found."})

        # Ensure a report exists or generate one
        report = await rep_service.get_latest_report(clean_id)
        if not report:
            report = await rep_service.generate_and_save_report(clean_id)

        try:
            result = await email_service.send_patient_report_email(patient, report)
            await rep_service.mark_report_emailed(report.id, recipient=patient.email)
            return json.dumps(
                {
                    "status": "success",
                    "message": f"4-week glucose report successfully dispatched to {patient.email}.",
                    "recipient": patient.email,
                    "patient_id": clean_id,
                    "report_id": report.id,
                    "details": result,
                },
                indent=2,
            )
        except Exception as e:
            logger.error("send_email tool error for %s: %s", clean_id, str(e))
            return json.dumps({"error": f"Failed to send email to patient '{clean_id}': {str(e)}"})


ALL_AGENT_TOOLS = [
    get_patient,
    get_glucose_readings,
    calculate_glucose_report,
    generate_report,
    send_email,
]

TOOLS_BY_NAME = {t.name: t for t in ALL_AGENT_TOOLS}
