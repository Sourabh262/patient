import pytest
import os
import sys
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.services.email_service import EmailService, EmailValidationError, EmailDeliveryError
from app.models.patient import Patient
from app.models.report import Report
from app.main import app
from app.db.seed import seed_database


@pytest.fixture(autouse=True)
async def setup_db():
    await seed_database(force_reseed=False)


def test_email_validation():
    svc = EmailService()
    # Valid emails
    assert svc.validate_email_address("doctor@hospital.org") == "doctor@hospital.org"
    assert svc.validate_email_address("patient.123@domain.com") == "patient.123@domain.com"

    # Invalid emails
    with pytest.raises(EmailValidationError):
        svc.validate_email_address("invalid-email-no-at")

    with pytest.raises(EmailValidationError):
        svc.validate_email_address("@nodomain.com")

    with pytest.raises(EmailValidationError):
        svc.validate_email_address("spaces in@email.com")


def test_email_masking_for_safe_logging():
    svc = EmailService()
    masked = svc.mask_email("johndoe@hospital.org")
    assert masked == "j***e@hospital.org"
    assert "johndoe" not in masked


def test_report_formatting_html_and_text():
    svc = EmailService()

    patient = Patient(
        patient_id="P_MAIL_TEST",
        name="Eleanor Vance",
        phone="+1-555-0199",
        email="eleanor.vance@example.org",
        address="100 Hill House Rd",
    )
    report = Report(
        id=99,
        patient_id="P_MAIL_TEST",
        weekly_averages={"week_1": 95.0, "week_2": 115.0, "week_3": 135.0, "week_4": 150.0},
        weekly_stages={"week_1": "Normal", "week_2": "Pre-diabetes", "week_3": "Diabetes", "week_4": "Diabetes"},
        current_stage="Diabetes",
        trend="worsening",
        ai_summary="Patient exhibits increasing glucose averages progressing to diabetes.",
    )

    text = svc.format_report_plain_text(patient, report)
    assert "Eleanor Vance" in text
    assert "P_MAIL_TEST" in text
    assert "Diabetes" in text
    assert "Week 1: 95.0 mg/dL" in text
    assert "increasing glucose averages" in text

    html = svc.format_report_html(patient, report)
    assert "Eleanor Vance" in html
    assert "P_MAIL_TEST" in html
    assert "95.0 mg/dL" in html
    assert "Pre-diabetes" in html
    assert "increasing glucose averages" in html


@pytest.mark.asyncio
async def test_email_simulation_dispatch():
    svc = EmailService()
    patient = Patient(
        patient_id="P_SIM",
        name="Simulation Patient",
        phone="+1-555-0200",
        email="sim.patient@hospital-care.org",
        address="42 Virtual Lane",
    )
    report = Report(
        id=101,
        patient_id="P_SIM",
        weekly_averages={"week_1": 90.0},
        weekly_stages={"week_1": "Normal"},
        current_stage="Normal",
        trend="stable",
        ai_summary="Glycemic metrics are stable and well within standard normal limits.",
    )

    result = await svc.send_patient_report_email(patient, report)
    assert result["status"] == "simulated"
    assert result["recipient"] == "sim.patient@hospital-care.org"
    assert "dispatched_at" in result


@pytest.mark.asyncio
async def test_send_report_email_api_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First generate a report for P015
        gen_res = await client.post("/api/v1/reports/generate", json={"patient_id": "P015"})
        assert gen_res.status_code == 201
        report_id = gen_res.json()["report_id"]

        # Call send-email endpoint
        res = await client.post(f"/api/v1/reports/{report_id}/send-email")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert "@" in data["message"]

        # Check report shows emailed in database
        report_res = await client.get(f"/api/v1/reports/{report_id}")
        assert report_res.status_code == 200
        assert report_res.json()["email_sent"] is True
        assert "@" in report_res.json()["email_recipient"]
