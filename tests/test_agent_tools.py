import json
import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.agent.tools import (
    get_patient,
    get_glucose_readings,
    calculate_glucose_report,
    generate_report,
    send_email,
)
from app.db.seed import seed_database


@pytest.fixture(autouse=True)
async def setup_db():
    await seed_database(force_reseed=False)


@pytest.mark.asyncio
async def test_tool_get_patient():
    # Valid patient
    res_str = await get_patient.ainvoke({"patient_id": "P015"})
    data = json.loads(res_str)
    assert data["patient_id"] == "P015"
    assert "name" in data
    assert "email" in data
    assert "phone" in data

    # Non-existent patient
    res_invalid = await get_patient.ainvoke({"patient_id": "P9999"})
    data_invalid = json.loads(res_invalid)
    assert "error" in data_invalid


@pytest.mark.asyncio
async def test_tool_get_glucose_readings():
    res_str = await get_glucose_readings.ainvoke({"patient_id": "P015"})
    data = json.loads(res_str)
    assert data["patient_id"] == "P015"
    assert data["total_readings"] > 0
    assert len(data["readings"]) > 0
    assert "glucose_value" in data["readings"][0]


@pytest.mark.asyncio
async def test_tool_calculate_glucose_report():
    res_str = await calculate_glucose_report.ainvoke({"patient_id": "P015"})
    data = json.loads(res_str)
    assert data["patient_id"] == "P015"
    assert "weekly_averages" in data
    assert "weekly_stages" in data
    assert "current_stage" in data
    assert "trend" in data
    assert data["has_sufficient_data"] is True


@pytest.mark.asyncio
async def test_tool_generate_report():
    res_str = await generate_report.ainvoke({"patient_id": "P015"})
    data = json.loads(res_str)
    assert "report_id" in data
    assert data["patient_id"] == "P015"
    assert "ai_summary" in data
    assert len(data["ai_summary"]) > 20
    assert data["current_stage"] in ["Normal", "Pre-diabetes", "Diabetes", "Hypoglycemia"]


@pytest.mark.asyncio
async def test_tool_send_email():
    res_str = await send_email.ainvoke({"patient_id": "P015"})
    data = json.loads(res_str)
    assert data["status"] == "success"
    assert data["patient_id"] == "P015"
    assert "@" in data["recipient"]
    assert "report_id" in data


@pytest.mark.asyncio
async def test_chained_tool_execution():
    pid = "P015"
    # Step 1: get_patient
    p_data = json.loads(await get_patient.ainvoke({"patient_id": pid}))
    assert p_data["patient_id"] == pid

    # Step 2: get_glucose_readings
    r_data = json.loads(await get_glucose_readings.ainvoke({"patient_id": pid}))
    assert r_data["total_readings"] > 0

    # Step 3: calculate_glucose_report
    c_data = json.loads(await calculate_glucose_report.ainvoke({"patient_id": pid}))
    assert c_data["current_stage"] is not None

    # Step 4: generate_report
    g_data = json.loads(await generate_report.ainvoke({"patient_id": pid}))
    assert g_data["report_id"] is not None

    # Step 5: send_email
    e_data = json.loads(await send_email.ainvoke({"patient_id": pid}))
    assert e_data["status"] == "success"
