import pytest
import os
import sys
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

import pytest_asyncio
from app.db.base import Base
from app.models.patient import Patient
from app.models.glucose_reading import GlucoseReading
from app.models.report import Report
from app.repositories.patient_repository import PatientRepository
from app.repositories.glucose_repository import GlucoseReadingRepository
from app.repositories.report_repository import ReportRepository


@pytest_asyncio.fixture
async def test_session():
    # Use in-memory SQLite for isolated test execution
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_patient_crud(test_session: AsyncSession):
    repo = PatientRepository(test_session)

    # Create
    patient = Patient(
        patient_id="P999",
        name="Test Patient",
        phone="+1-555-0199",
        email="test.patient@example.com",
        address="123 Lab Test Ave",
    )
    created = await repo.create(patient)
    assert created.patient_id == "P999"

    # Read
    fetched = await repo.get_by_id("P999")
    assert fetched is not None
    assert fetched.name == "Test Patient"
    assert fetched.email == "test.patient@example.com"

    # Search & Count
    count = await repo.count("Test")
    assert count == 1

    # Update
    fetched.name = "Updated Test Patient"
    updated = await repo.update(fetched)
    assert updated.name == "Updated Test Patient"

    # Delete
    await repo.delete(updated)
    deleted = await repo.get_by_id("P999")
    assert deleted is None


@pytest.mark.asyncio
async def test_glucose_readings_and_relations(test_session: AsyncSession):
    p_repo = PatientRepository(test_session)
    g_repo = GlucoseReadingRepository(test_session)

    # Create patient
    patient = Patient(
        patient_id="P888",
        name="Glucose Patient",
        phone="+1-555-0888",
        email="glucose@example.com",
        address="456 Pancreas Way",
    )
    await p_repo.create(patient)

    # Insert readings across 4 weeks
    readings = [
        GlucoseReading(
            patient_id="P888",
            week_number=1,
            glucose_value=95.0,
            timestamp=datetime.now(timezone.utc),
            meal_context="fasting",
        ),
        GlucoseReading(
            patient_id="P888",
            week_number=2,
            glucose_value=105.5,
            timestamp=datetime.now(timezone.utc),
            meal_context="post_prandial",
        ),
        GlucoseReading(
            patient_id="P888",
            week_number=3,
            glucose_value=115.0,
            timestamp=datetime.now(timezone.utc),
            meal_context="fasting",
        ),
        GlucoseReading(
            patient_id="P888",
            week_number=4,
            glucose_value=128.0,
            timestamp=datetime.now(timezone.utc),
            meal_context="post_prandial",
        ),
    ]
    await g_repo.bulk_create(readings)

    # Query latest 4 weeks readings
    queried_readings = await g_repo.get_latest_weeks_readings("P888", max_weeks=4)
    assert len(queried_readings) == 4
    assert [r.week_number for r in queried_readings] == [1, 2, 3, 4]

    # Verify Patient relationship loads readings
    patient_with_history = await p_repo.get_by_id("P888")
    assert patient_with_history is not None
    assert len(patient_with_history.readings) == 4


@pytest.mark.asyncio
async def test_report_crud_and_status(test_session: AsyncSession):
    p_repo = PatientRepository(test_session)
    r_repo = ReportRepository(test_session)

    patient = Patient(
        patient_id="P777",
        name="Report Patient",
        phone="+1-555-0777",
        email="report.patient@example.com",
        address="789 Clinical Blvd",
    )
    await p_repo.create(patient)

    report = Report(
        patient_id="P777",
        weekly_averages={"week_1": 92.0, "week_2": 94.5, "week_3": 96.0, "week_4": 95.0},
        weekly_stages={"week_1": "Normal", "week_2": "Normal", "week_3": "Normal", "week_4": "Normal"},
        current_stage="Normal",
        trend="stable",
        ai_summary="Patient maintains healthy glycemic control over the past 4 weeks.",
    )
    created_report = await r_repo.create(report)
    assert created_report.id is not None
    assert created_report.email_sent is False

    # Mark email sent
    updated_report = await r_repo.mark_email_sent(created_report.id, "report.patient@example.com")
    assert updated_report is not None
    assert updated_report.email_sent is True
    assert updated_report.email_recipient == "report.patient@example.com"
    assert updated_report.email_sent_at is not None

    # Fetch latest report for patient
    latest = await r_repo.get_latest_by_patient("P777")
    assert latest is not None
    assert latest.id == created_report.id


@pytest.mark.asyncio
async def test_seed_database_import():
    from app.db.seed import seed_database
    from app.db.session import AsyncSessionLocal
    from app.models.patient import Patient
    from sqlalchemy import select, func

    # Running seed
    count = await seed_database(force_reseed=False)
    assert count == 30

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(func.count()).select_from(Patient))
        patient_count = result.scalar()
        assert patient_count == 30
