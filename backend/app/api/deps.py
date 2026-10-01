from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.repositories.patient_repository import PatientRepository
from app.repositories.glucose_repository import GlucoseReadingRepository
from app.repositories.report_repository import ReportRepository
from app.services.patient_service import PatientService
from app.services.glucose_service import GlucoseService


def get_patient_repo(db: AsyncSession = Depends(get_db)) -> PatientRepository:
    return PatientRepository(db)


def get_glucose_repo(db: AsyncSession = Depends(get_db)) -> GlucoseReadingRepository:
    return GlucoseReadingRepository(db)


def get_report_repo(db: AsyncSession = Depends(get_db)) -> ReportRepository:
    return ReportRepository(db)


def get_patient_service(
    patient_repo: PatientRepository = Depends(get_patient_repo),
) -> PatientService:
    return PatientService(patient_repo)


def get_glucose_service(
    glucose_repo: GlucoseReadingRepository = Depends(get_glucose_repo),
    patient_repo: PatientRepository = Depends(get_patient_repo),
) -> GlucoseService:
    return GlucoseService(glucose_repo, patient_repo)
