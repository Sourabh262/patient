import pytest
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.models.glucose_reading import GlucoseReading
from app.services.glucose_calculator import (
    classify_stage,
    calculate_trend,
    calculate_4_week_report,
    STAGE_HYPO,
    STAGE_NORMAL,
    STAGE_PREDIABETES,
    STAGE_DIABETES,
    STAGE_INSUFFICIENT,
    TREND_IMPROVING,
    TREND_WORSENING,
    TREND_STABLE,
    TREND_FLUCTUATING,
    TREND_INSUFFICIENT,
)


def test_stage_classification_cutoffs_and_boundaries():
    # Hypoglycemia: < 70
    assert classify_stage(69.9) == STAGE_HYPO
    assert classify_stage(55.0) == STAGE_HYPO

    # Normal: 70 - 99
    assert classify_stage(70.0) == STAGE_NORMAL
    assert classify_stage(85.5) == STAGE_NORMAL
    assert classify_stage(99.0) == STAGE_NORMAL

    # Pre-diabetes: 99.1 - 125
    assert classify_stage(99.1) == STAGE_PREDIABETES
    assert classify_stage(110.0) == STAGE_PREDIABETES
    assert classify_stage(125.0) == STAGE_PREDIABETES

    # Diabetes: > 125
    assert classify_stage(125.1) == STAGE_DIABETES
    assert classify_stage(140.0) == STAGE_DIABETES
    assert classify_stage(220.0) == STAGE_DIABETES

    # Missing / None
    assert classify_stage(None) == STAGE_INSUFFICIENT


def test_trend_calculation():
    # Improving: w1 -> w4 drops by > 5
    assert calculate_trend([160.0, 140.0, 120.0, 100.0]) == TREND_IMPROVING
    assert calculate_trend([120.0, None, 110.0, 95.0]) == TREND_IMPROVING

    # Worsening: w1 -> w4 rises by > 5
    assert calculate_trend([90.0, 110.0, 130.0, 150.0]) == TREND_WORSENING

    # Stable: within +/- 5
    assert calculate_trend([92.0, 94.0, 91.0, 93.0]) == TREND_STABLE

    # Fluctuating: zig-zag
    assert calculate_trend([110.0, 150.0, 90.0, 112.0]) == TREND_FLUCTUATING

    # Insufficient: fewer than 2 valid points
    assert calculate_trend([None, None, None, 110.0]) == TREND_INSUFFICIENT
    assert calculate_trend([None, None, None, None]) == TREND_INSUFFICIENT


def test_calculate_4_week_report_normal_flow():
    readings = [
        # Week 1: avg (90 + 94)/2 = 92.0 -> Normal
        GlucoseReading(patient_id="P_TEST", week_number=1, glucose_value=90.0),
        GlucoseReading(patient_id="P_TEST", week_number=1, glucose_value=94.0),
        # Week 2: avg 110.0 -> Pre-diabetes
        GlucoseReading(patient_id="P_TEST", week_number=2, glucose_value=110.0),
        # Week 3: avg 130.0 -> Diabetes
        GlucoseReading(patient_id="P_TEST", week_number=3, glucose_value=130.0),
        # Week 4: avg 140.0 -> Diabetes
        GlucoseReading(patient_id="P_TEST", week_number=4, glucose_value=140.0),
    ]

    result = calculate_4_week_report(patient_id="P_TEST", readings=readings)

    assert result.patient_id == "P_TEST"
    assert result.weekly_averages["week_1"] == 92.0
    assert result.weekly_stages["week_1"] == STAGE_NORMAL

    assert result.weekly_averages["week_2"] == 110.0
    assert result.weekly_stages["week_2"] == STAGE_PREDIABETES

    assert result.weekly_averages["week_3"] == 130.0
    assert result.weekly_stages["week_3"] == STAGE_DIABETES

    assert result.weekly_averages["week_4"] == 140.0
    assert result.weekly_stages["week_4"] == STAGE_DIABETES

    assert result.current_stage == STAGE_DIABETES
    assert result.trend == TREND_WORSENING
    assert result.total_readings_analyzed == 5
    assert result.has_sufficient_data is True


def test_calculate_4_week_report_with_incomplete_and_missing_weeks():
    # Only Week 1 and Week 4 have readings
    readings = [
        GlucoseReading(patient_id="P_SPARSE", week_number=1, glucose_value=160.0),
        GlucoseReading(patient_id="P_SPARSE", week_number=4, glucose_value=120.0),
    ]

    result = calculate_4_week_report(patient_id="P_SPARSE", readings=readings)

    assert result.weekly_averages["week_1"] == 160.0
    assert result.weekly_stages["week_1"] == STAGE_DIABETES

    assert result.weekly_averages["week_2"] is None
    assert result.weekly_stages["week_2"] == STAGE_INSUFFICIENT

    assert result.weekly_averages["week_3"] is None
    assert result.weekly_stages["week_3"] == STAGE_INSUFFICIENT

    assert result.weekly_averages["week_4"] == 120.0
    assert result.weekly_stages["week_4"] == STAGE_PREDIABETES

    assert result.current_stage == STAGE_PREDIABETES
    assert result.trend == TREND_IMPROVING


def test_calculate_4_week_report_empty_data():
    result = calculate_4_week_report(patient_id="P_EMPTY", readings=[])

    assert result.patient_id == "P_EMPTY"
    assert all(avg is None for avg in result.weekly_averages.values())
    assert all(stage == STAGE_INSUFFICIENT for stage in result.weekly_stages.values())
    assert result.current_stage == STAGE_INSUFFICIENT
    assert result.trend == TREND_INSUFFICIENT
    assert result.total_readings_analyzed == 0
    assert result.has_sufficient_data is False


def test_calculate_4_week_report_filters_invalid_and_out_of_range_values():
    readings = [
        GlucoseReading(patient_id="P_ANOMALY", week_number=1, glucose_value=90.0),
        GlucoseReading(patient_id="P_ANOMALY", week_number=1, glucose_value=-50.0),  # invalid negative
        GlucoseReading(patient_id="P_ANOMALY", week_number=1, glucose_value=1200.0),  # invalid high
        GlucoseReading(patient_id="P_ANOMALY", week_number=5, glucose_value=100.0),  # week outside 1-4
    ]

    result = calculate_4_week_report(patient_id="P_ANOMALY", readings=readings)
    # Only the 90.0 reading in week 1 should be counted
    assert result.total_readings_analyzed == 1
    assert result.weekly_averages["week_1"] == 90.0
