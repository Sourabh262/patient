from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from app.api.deps import get_patient_service, get_glucose_service
from app.services.patient_service import PatientService
from app.services.glucose_service import GlucoseService
from app.schemas.patient import (
    PatientCreate,
    PatientUpdate,
    PatientResponse,
    PatientDetailResponse,
    PatientListResponse,
)
from app.schemas.glucose import (
    GlucoseReadingCreate,
    GlucoseReadingResponse,
    GlucoseReadingListResponse,
)

router = APIRouter()


@router.get("", response_model=PatientListResponse, summary="List patients with pagination and search")
async def list_patients(
    skip: int = Query(0, ge=0, description="Offset"),
    limit: int = Query(50, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(None, description="Search by ID, name, or email"),
    service: PatientService = Depends(get_patient_service),
):
    return await service.list_patients(skip=skip, limit=limit, search=search)


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED, summary="Create a new patient")
async def create_patient(
    payload: PatientCreate,
    service: PatientService = Depends(get_patient_service),
):
    return await service.create_patient(payload)


@router.get("/{patient_id}", response_model=PatientDetailResponse, summary="Get patient details and readings")
async def get_patient(
    patient_id: str,
    service: PatientService = Depends(get_patient_service),
):
    return await service.get_patient_detail(patient_id)


@router.put("/{patient_id}", response_model=PatientResponse, summary="Update patient details")
async def update_patient(
    patient_id: str,
    payload: PatientUpdate,
    service: PatientService = Depends(get_patient_service),
):
    return await service.update_patient(patient_id, payload)


@router.get("/{patient_id}/readings", response_model=GlucoseReadingListResponse, summary="Get patient glucose readings")
async def get_glucose_readings(
    patient_id: str,
    limit: Optional[int] = Query(None, ge=1, le=500, description="Limit number of readings"),
    glucose_service: GlucoseService = Depends(get_glucose_service),
):
    return await glucose_service.get_patient_readings(patient_id=patient_id, limit=limit)


@router.post(
    "/{patient_id}/readings",
    response_model=GlucoseReadingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a new glucose reading for patient",
)
async def add_glucose_reading(
    patient_id: str,
    payload: GlucoseReadingCreate,
    glucose_service: GlucoseService = Depends(get_glucose_service),
):
    return await glucose_service.add_reading(patient_id=patient_id, payload=payload)
