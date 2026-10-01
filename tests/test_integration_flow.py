import pytest
import os
import sys
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.main import app
from app.db.seed import seed_database


@pytest.fixture(autouse=True)
async def setup_db():
    await seed_database(force_reseed=False)


@pytest.mark.asyncio
async def test_end_to_end_chat_request_flow():
    """Validates: React -> FastAPI -> LangGraph -> Tools -> Services -> Database end-to-end."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Chat asking for patient information
        res_info = await client.post("/api/chat", json={"message": "Get patient P015 information."})
        assert res_info.status_code == 200
        data_info = res_info.json()
        assert "response" in data_info
        assert "P015" in data_info["response"] or "patient" in data_info["response"].lower()

        # 2. Chat asking for glucose report
        res_report = await client.post("/api/chat", json={"message": "Show P015's last 4 weeks glucose report."})
        assert res_report.status_code == 200
        data_report = res_report.json()
        assert "response" in data_report
        assert len(data_report["response"]) > 20

        # 3. Chat asking to dispatch report via email: React -> FastAPI -> LangGraph -> Tools -> Services -> Database
        res_email = await client.post("/api/chat", json={"message": "Send P015's 4-week glucose report to the patient."})
        assert res_email.status_code == 200
        data_email = res_email.json()
        assert "response" in data_email
        assert any(k in data_email["response"].lower() for k in ["email", "dispatched", "sent", "success"])


@pytest.mark.asyncio
async def test_end_to_end_patient_to_report_to_email_api_flow():
    """Validates complete patient lifecycle from retrieval to report generation and email dispatch."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Get patient
        res_p = await client.get("/api/v1/patients/P015")
        assert res_p.status_code == 200
        p_data = res_p.json()
        assert p_data["patient_id"] == "P015"

        # 2. Calculate glucose metrics
        res_calc = await client.get("/api/v1/patients/P015/calculate-report")
        assert res_calc.status_code == 200
        calc_data = res_calc.json()
        assert calc_data["patient_id"] == "P015"
        assert calc_data["current_stage"] is not None

        # 3. Generate formal report
        res_gen = await client.post("/api/v1/reports/generate", json={"patient_id": "P015"})
        assert res_gen.status_code == 201
        rep_data = res_gen.json()
        report_id = rep_data["report_id"]
        assert report_id is not None
        assert "ai_summary" in rep_data

        # 4. Email the report
        res_mail = await client.post(f"/api/v1/reports/{report_id}/send-email")
        assert res_mail.status_code == 200
        mail_data = res_mail.json()
        assert mail_data["status"] == "success"
