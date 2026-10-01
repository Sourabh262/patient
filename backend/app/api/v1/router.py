from fastapi import APIRouter
from app.api.v1.endpoints import patients

api_router = APIRouter()
api_router.include_router(patients.router, prefix="/patients", tags=["Patients"])
