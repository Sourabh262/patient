from fastapi import APIRouter
from app.api.v1.endpoints import patients, reports, chat

api_router = APIRouter()
api_router.include_router(patients.router, prefix="/patients", tags=["Patients"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(chat.router, prefix="/chat", tags=["AI Chat"])
