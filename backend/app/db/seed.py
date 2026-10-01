import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from sqlalchemy import select
from app.db.session import AsyncSessionLocal, init_db
from app.models.patient import Patient
from app.models.glucose_reading import GlucoseReading
from app.core.logging import logger


def find_data_file() -> Path:
    # Check potential relative locations
    candidates = [
        Path("data/synthetic_patients.json"),
        Path("../data/synthetic_patients.json"),
        Path(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "synthetic_patients.json")),
    ]
    for candidate in candidates:
        if candidate.resolve().exists():
            return candidate.resolve()
    raise FileNotFoundError("Could not locate synthetic_patients.json in data directory")


async def seed_database(force_reseed: bool = False) -> int:
    """Seeds the database with 30 synthetic patient records from JSON."""
    await init_db()

    data_file = find_data_file()
    with open(data_file, "r", encoding="utf-8") as f:
        patients_data = json.load(f)

    async with AsyncSessionLocal() as session:
        # Check existing count
        existing = await session.execute(select(Patient.patient_id))
        existing_ids = set(existing.scalars().all())

        if existing_ids and not force_reseed:
            logger.info("Database already seeded with %d patients. Skipping.", len(existing_ids))
            return len(existing_ids)

        seeded_count = 0
        for p_item in patients_data:
            pid = p_item["patient_id"]
            if pid in existing_ids and not force_reseed:
                continue

            patient = Patient(
                patient_id=pid,
                name=p_item["name"],
                phone=p_item["phone"],
                email=p_item["email"],
                address=p_item["address"],
            )
            session.add(patient)
            await session.flush()

            # Add readings
            for r_item in p_item.get("readings", []):
                # Parse timestamp
                ts_str = r_item["timestamp"]
                if ts_str.endswith("Z"):
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                else:
                    ts = datetime.fromisoformat(ts_str)

                reading = GlucoseReading(
                    patient_id=pid,
                    week_number=r_item["week_number"],
                    glucose_value=float(r_item["glucose_value"]),
                    meal_context=r_item.get("meal_context", "random"),
                    timestamp=ts,
                )
                session.add(reading)

            seeded_count += 1

        await session.commit()
        logger.info("Successfully seeded %d patients and their glucose telemetry", seeded_count)
        return seeded_count


if __name__ == "__main__":
    count = asyncio.run(seed_database(force_reseed=True))
    print(f"Seed complete. Inserted {count} patients.")
