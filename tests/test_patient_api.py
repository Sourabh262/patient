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
async def test_list_patients_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Default list
        res = await client.get("/api/v1/patients")
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert "meta" in data
        assert data["meta"]["total"] >= 30
        assert len(data["items"]) <= 50

        # Pagination limit
        res_paginated = await client.get("/api/v1/patients?skip=0&limit=5")
        assert res_paginated.status_code == 200
        assert len(res_paginated.json()["items"]) == 5

        # Search by patient ID
        res_search = await client.get("/api/v1/patients?search=P015")
        assert res_search.status_code == 200
        search_items = res_search.json()["items"]
        assert len(search_items) == 1
        assert search_items[0]["patient_id"] == "P015"


@pytest.mark.asyncio
async def test_get_patient_detail_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Existing patient
        res = await client.get("/api/v1/patients/P015")
        assert res.status_code == 200
        data = res.json()
        assert data["patient_id"] == "P015"
        assert "readings" in data
        assert len(data["readings"]) > 0

        # Non-existent patient
        res_404 = await client.get("/api/v1/patients/NONEXISTENT999")
        assert res_404.status_code == 404
        assert "not found" in res_404.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_and_update_patient_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Generate unique id for test run
        import uuid
        uid = uuid.uuid4().hex[:6]
        pid = f"PT{uid}"
        pemail = f"test_{uid}@hospital-care.org"

        new_patient = {
            "patient_id": pid,
            "name": "Sarah Connor",
            "phone": "+1-555-900-1122",
            "email": pemail,
            "address": "404 Skynet Bypass, Los Angeles, CA",
        }
        res_create = await client.post("/api/v1/patients", json=new_patient)
        assert res_create.status_code == 201
        created = res_create.json()
        assert created["patient_id"] == pid
        assert created["name"] == "Sarah Connor"

        # Duplicate ID should return 409 Conflict
        res_dup_id = await client.post("/api/v1/patients", json=new_patient)
        assert res_dup_id.status_code == 409

        # Update patient
        update_payload = {
            "name": "Sarah J. Connor",
            "phone": "+1-555-900-9999",
        }
        res_update = await client.put(f"/api/v1/patients/{pid}", json=update_payload)
        assert res_update.status_code == 200
        updated = res_update.json()
        assert updated["name"] == "Sarah J. Connor"
        assert updated["phone"] == "+1-555-900-9999"


@pytest.mark.asyncio
async def test_glucose_readings_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Get readings for P015
        res_get = await client.get("/api/v1/patients/P015/readings")
        assert res_get.status_code == 200
        data = res_get.json()
        assert data["patient_id"] == "P015"
        assert data["total_readings"] > 0

        # Add new valid reading
        new_reading = {
            "glucose_value": 142.5,
            "week_number": 4,
            "meal_context": "post_prandial",
        }
        res_add = await client.post("/api/v1/patients/P015/readings", json=new_reading)
        assert res_add.status_code == 201
        added = res_add.json()
        assert added["patient_id"] == "P015"
        assert added["glucose_value"] == 142.5
        assert added["week_number"] == 4

        # Add invalid glucose reading (out of bounds)
        res_invalid = await client.post(
            "/api/v1/patients/P015/readings",
            json={"glucose_value": 12.0, "week_number": 2},
        )
        assert res_invalid.status_code == 422

        # Add reading for non-existent patient
        res_no_patient = await client.post(
            "/api/v1/patients/INVALID_ID/readings",
            json={"glucose_value": 110.0, "week_number": 1},
        )
        assert res_no_patient.status_code == 404
