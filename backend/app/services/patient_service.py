from typing import Optional, List, Tuple
from fastapi import HTTPException, status
from app.models.patient import Patient
from app.repositories.patient_repository import PatientRepository
from app.schemas.patient import (
    PatientCreate,
    PatientUpdate,
    PatientResponse,
    PatientListResponse,
    PaginationMeta,
    PatientDetailResponse,
)
from app.core.logging import logger


class PatientService:
    def __init__(self, patient_repo: PatientRepository):
        self.patient_repo = patient_repo

    async def list_patients(
        self, skip: int = 0, limit: int = 50, search: Optional[str] = None
    ) -> PatientListResponse:
        total = await self.patient_repo.count(search=search)
        patients = await self.patient_repo.list_patients(skip=skip, limit=limit, search=search)

        items = []
        for p in patients:
            item = PatientResponse(
                patient_id=p.patient_id,
                name=p.name,
                phone=p.phone,
                email=p.email,
                address=p.address,
                created_at=p.created_at,
                updated_at=p.updated_at,
                total_readings=len(p.readings) if hasattr(p, "readings") and p.readings else 0,
            )
            items.append(item)

        return PatientListResponse(
            items=items,
            meta=PaginationMeta(
                total=total,
                skip=skip,
                limit=limit,
                has_more=(skip + limit) < total,
            ),
        )

    async def get_patient(self, patient_id: str) -> Patient:
        patient = await self.patient_repo.get_by_id(patient_id)
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient with ID '{patient_id}' not found.",
            )
        return patient

    async def get_patient_detail(self, patient_id: str) -> PatientDetailResponse:
        patient = await self.get_patient(patient_id)
        return PatientDetailResponse(
            patient_id=patient.patient_id,
            name=patient.name,
            phone=patient.phone,
            email=patient.email,
            address=patient.address,
            created_at=patient.created_at,
            updated_at=patient.updated_at,
            total_readings=len(patient.readings) if patient.readings else 0,
            readings=[
                {
                    "id": r.id,
                    "patient_id": r.patient_id,
                    "glucose_value": r.glucose_value,
                    "week_number": r.week_number,
                    "meal_context": r.meal_context,
                    "timestamp": r.timestamp,
                }
                for r in (patient.readings or [])
            ],
        )

    async def create_patient(self, payload: PatientCreate) -> PatientResponse:
        # Check if patient_id already exists
        existing_id = await self.patient_repo.get_by_id(payload.patient_id)
        if existing_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Patient ID '{payload.patient_id}' already registered.",
            )

        # Check if email is already used
        existing_email = await self.patient_repo.get_by_email(payload.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{payload.email}' already registered to another patient.",
            )

        patient = Patient(
            patient_id=payload.patient_id,
            name=payload.name,
            phone=payload.phone,
            email=payload.email,
            address=payload.address,
        )
        saved = await self.patient_repo.create(patient)
        logger.info("Created new patient record with ID %s", saved.patient_id)

        return PatientResponse(
            patient_id=saved.patient_id,
            name=saved.name,
            phone=saved.phone,
            email=saved.email,
            address=saved.address,
            created_at=saved.created_at,
            updated_at=saved.updated_at,
            total_readings=0,
        )

    async def update_patient(self, patient_id: str, payload: PatientUpdate) -> PatientResponse:
        patient = await self.get_patient(patient_id)

        if payload.name is not None:
            patient.name = payload.name
        if payload.phone is not None:
            patient.phone = payload.phone
        if payload.email is not None and payload.email != patient.email:
            existing_email = await self.patient_repo.get_by_email(payload.email)
            if existing_email and existing_email.patient_id != patient_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Email '{payload.email}' already registered to another patient.",
                )
            patient.email = payload.email
        if payload.address is not None:
            patient.address = payload.address

        updated = await self.patient_repo.update(patient)
        logger.info("Updated patient record %s", updated.patient_id)

        return PatientResponse(
            patient_id=updated.patient_id,
            name=updated.name,
            phone=updated.phone,
            email=updated.email,
            address=updated.address,
            created_at=updated.created_at,
            updated_at=updated.updated_at,
            total_readings=len(updated.readings) if updated.readings else 0,
        )
