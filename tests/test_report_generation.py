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
async def test_generate_report_workflow_end_to_end():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Generate report for P015
        res = await client.post("/api/v1/reports/generate", json={"patient_id": "P015"})
        assert res.status_code == 201
        data = res.json()

        # 1. Patient Information
        assert "patient" in data
        patient = data["patient"]
        assert patient["patient_id"] == "P015"
        assert len(patient["name"]) > 0
        assert len(patient["phone"]) > 0
        assert "@" in patient["email"]
        assert len(patient["address"]) > 0

        # 2. Glucose Report
        assert "weekly_averages" in data
        assert "weekly_stages" in data
        for w in range(1, 5):
            key = f"week_{w}"
            assert key in data["weekly_averages"]
            assert key in data["weekly_stages"]
            assert isinstance(data["weekly_averages"][key], (int, float))
            assert data["weekly_stages"][key] in ["Normal", "Pre-diabetes", "Diabetes", "Hypoglycemia"]

        assert data["current_stage"] in ["Normal", "Pre-diabetes", "Diabetes", "Hypoglycemia"]
        assert data["trend"] in ["improving", "worsening", "stable", "fluctuating"]

        # 3. AI Summary
        assert "ai_summary" in data
        assert len(data["ai_summary"]) > 25
        # The AI summary should mention the patient or ID
        assert "P015" in data["ai_summary"] or patient["name"] in data["ai_summary"]

        report_id = data["report_id"]

        # 4. Fetch by ID
        res_by_id = await client.get(f"/api/v1/reports/{report_id}")
        assert res_by_id.status_code == 200
        assert res_by_id.json()["report_id"] == report_id

        # 5. Fetch latest
        res_latest = await client.get("/api/v1/reports/latest/P015")
        assert res_latest.status_code == 200
        assert res_latest.json()["patient"]["patient_id"] == "P015"


@pytest.mark.asyncio
async def test_generate_report_invalid_patient():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/v1/reports/generate", json={"patient_id": "P_INVALID_999"})
        assert res.status_code == 404
        assert "not found" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_recent_reports():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/reports?limit=5")
        assert res.status_code == 200
        assert isinstance(res.json(), list)
