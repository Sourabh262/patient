import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.agent.workflow import run_agent, clinical_agent
from app.db.seed import seed_database


@pytest.fixture(autouse=True)
async def setup_db():
    await seed_database(force_reseed=False)


@pytest.mark.asyncio
async def test_agent_get_patient_info():
    result = await run_agent("Get patient P015 information.")
    assert result["error"] is None
    response = result["response"]
    assert "P015" in response or "patient" in response.lower()
    # P015 has an address and email in synthetic seed data
    assert "@" in response or "email" in response.lower()


@pytest.mark.asyncio
async def test_agent_glucose_report():
    result = await run_agent("Show P015's last 4 weeks glucose report.")
    assert result["error"] is None
    response = result["response"]
    assert "P015" in response or "report" in response.lower()
    # Check that stage / average information is present
    assert any(term in response.lower() for term in ["diabetes", "normal", "pre-diabetes", "week", "average"])


@pytest.mark.asyncio
async def test_agent_glucose_history():
    result = await run_agent("Show the patient's glucose history for P015.")
    assert result["error"] is None
    response = result["response"]
    assert "P015" in response or "readings" in response.lower() or "glucose" in response.lower()


@pytest.mark.asyncio
async def test_agent_send_email():
    result = await run_agent("Send P015's glucose report to the patient.")
    assert result["error"] is None
    response = result["response"]
    assert any(term in response.lower() for term in ["email", "dispatched", "sent", "success"])


@pytest.mark.asyncio
async def test_agent_missing_patient_id():
    result = await run_agent("Show the glucose report please.")
    assert result["error"] is None
    response = result["response"].lower()
    assert "patient id" in response or "provide" in response


@pytest.mark.asyncio
async def test_agent_invalid_patient_id():
    result = await run_agent("Get patient P999999 information.")
    assert result["error"] is None
    response = result["response"].lower()
    assert "not found" in response or "could not locate" in response or "error" in response
