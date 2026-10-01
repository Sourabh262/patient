from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.api.deps import get_report_service
from app.services.report_service import ReportService
from app.schemas.report import (
    ReportCreate,
    ReportResponse,
    FullPatientReportResponse,
)

router = APIRouter()


@router.post(
    "/generate",
    response_model=FullPatientReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate and persist complete 4-week clinical glucose report with AI summary",
)
async def generate_patient_report(
    payload: ReportCreate,
    service: ReportService = Depends(get_report_service),
):
    saved_report = await service.generate_and_save_report(payload.patient_id)
    return await service.get_full_report(saved_report.id)


@router.get(
    "/latest/{patient_id}",
    response_model=FullPatientReportResponse,
    summary="Get the most recent 4-week glucose report for a patient",
)
async def get_latest_patient_report(
    patient_id: str,
    service: ReportService = Depends(get_report_service),
):
    return await service.get_latest_full_report(patient_id)


@router.get(
    "/{report_id}",
    response_model=FullPatientReportResponse,
    summary="Get full report details by report ID",
)
async def get_report_by_id(
    report_id: int,
    service: ReportService = Depends(get_report_service),
):
    return await service.get_full_report(report_id)


@router.get(
    "",
    response_model=List[ReportResponse],
    summary="List recent reports across all patients for clinician overview",
)
async def list_recent_reports(
    limit: int = Query(10, ge=1, le=50),
    service: ReportService = Depends(get_report_service),
):
    reports = await service.list_recent_reports(limit=limit)
    return reports
