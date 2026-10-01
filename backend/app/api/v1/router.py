from fastapi import APIRouter
from app.api.v1.endpoints import patients, reports

api_router = APIRouter()
api_router.include_router(patients.router, prefix="/patients", tags=["Patients"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
