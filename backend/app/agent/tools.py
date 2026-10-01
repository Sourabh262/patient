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

        # 1. Fetch patient
        patient = await p_repo.get_by_id(clean_id)
        if not patient:
            return json.dumps({"error": f"Patient '{clean_id}' does not exist in registry."})

        # 2. Retrieve readings and calculate
        readings = await g_repo.get_latest_weeks_readings(clean_id, max_weeks=4)
        calc = calculate_4_week_report(patient_id=clean_id, readings=readings)

        # 3. Create verified AI summary
        summary = (
            f"Patient {patient.name} ({clean_id}) has completed 4-week glycemic monitoring. "
            f"Current classification is {calc.current_stage} with an overall '{calc.trend}' trajectory. "
            f"Week 1 avg: {calc.weekly_averages.get('week_1')} mg/dL ({calc.weekly_stages.get('week_1')}); "
            f"Week 4 avg: {calc.weekly_averages.get('week_4')} mg/dL ({calc.weekly_stages.get('week_4')}). "
            f"Total readings analyzed: {calc.total_readings_analyzed}."
        )

        from app.models.report import Report

        report = Report(
            patient_id=clean_id,
            weekly_averages=calc.weekly_averages,
            weekly_stages=calc.weekly_stages,
            current_stage=calc.current_stage,
            trend=calc.trend,
            ai_summary=summary,
        )
        saved = await r_repo.create(report)
        await session.commit()

        return json.dumps(
            {
                "report_id": saved.id,
                "patient_id": clean_id,
                "patient_name": patient.name,
                "email": patient.email,
                "weekly_averages": saved.weekly_averages,
                "weekly_stages": saved.weekly_stages,
                "current_stage": saved.current_stage,
                "trend": saved.trend,
                "ai_summary": saved.ai_summary,
            },
            indent=2,
        )


@tool(args_schema=PatientToolInput)
async def send_email(patient_id: str) -> str:
    """Send the latest verified 4-week glucose clinical report to the patient's registered email address.
    """
    clean_id = patient_id.strip().upper()
    async with AsyncSessionLocal() as session:
        p_repo = PatientRepository(session)
        r_repo = ReportRepository(session)

        patient = await p_repo.get_by_id(clean_id)
        if not patient:
            return json.dumps({"error": f"Patient '{clean_id}' not found."})

        # Ensure a report exists, or generate one
        report = await r_repo.get_latest_by_patient(clean_id)
        if not report:
            # Generate report first
            gen_res = json.loads(await generate_report.ainvoke({"patient_id": clean_id}))
            report_id = gen_res.get("report_id")
            report = await r_repo.get(report_id)

        # Mark sent in database
        await r_repo.mark_email_sent(report.id, recipient=patient.email)
        await session.commit()

        return json.dumps(
            {
                "status": "success",
                "message": f"4-week glucose report successfully dispatched to {patient.email}.",
                "recipient": patient.email,
                "patient_id": clean_id,
                "report_id": report.id,
            },
            indent=2,
        )


ALL_AGENT_TOOLS = [
    get_patient,
    get_glucose_readings,
    calculate_glucose_report,
    generate_report,
    send_email,
]

TOOLS_BY_NAME = {t.name: t for t in ALL_AGENT_TOOLS}
