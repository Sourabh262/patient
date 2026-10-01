import math
from typing import List, Dict, Optional, Any
from app.core.config import settings
from app.models.glucose_reading import GlucoseReading
from app.schemas.report import WeeklyMetric, FourWeekCalculationResult
from app.core.logging import logger

# Clinical Classification Constants
STAGE_HYPO = "Hypoglycemia"
STAGE_NORMAL = "Normal"
STAGE_PREDIABETES = "Pre-diabetes"
STAGE_DIABETES = "Diabetes"
STAGE_INSUFFICIENT = "Insufficient Data"

TREND_IMPROVING = "improving"
TREND_WORSENING = "worsening"
TREND_STABLE = "stable"
TREND_FLUCTUATING = "fluctuating"
TREND_INSUFFICIENT = "insufficient_data"


def classify_stage(
    value: Optional[float],
    hypo_threshold: float = settings.GLUCOSE_HYPO_THRESHOLD,
    normal_max: float = settings.GLUCOSE_NORMAL_MAX,
    prediabetes_max: float = settings.GLUCOSE_PREDIABETES_MAX,
) -> str:
    """Deterministically classifies glucose average based on configurable clinical cutoffs.
    - Hypoglycemia: < hypo_threshold (e.g. < 70 mg/dL)
    - Normal: hypo_threshold <= value <= normal_max (e.g. 70 - 99 mg/dL)
    - Pre-diabetes: normal_max < value <= prediabetes_max (e.g. 100 - 125 mg/dL)
    - Diabetes: > prediabetes_max (e.g. >= 126 mg/dL)
    """
    if value is None or math.isnan(value):
        return STAGE_INSUFFICIENT

    if value < hypo_threshold:
        return STAGE_HYPO
    elif value <= normal_max:
        return STAGE_NORMAL
    elif value <= prediabetes_max:
        return STAGE_PREDIABETES
    else:
        return STAGE_DIABETES


def calculate_trend(weekly_averages: List[Optional[float]], threshold_delta: float = 5.0) -> str:
    """Calculates overall 4-week trajectory deterministically.
    - Compares earliest available week with latest available week.
    - Evaluates monotonicity and fluctuation across intermediate weeks.
    """
    valid_points = [(idx, val) for idx, val in enumerate(weekly_averages) if val is not None]

    if len(valid_points) < 2:
        return TREND_INSUFFICIENT

    first_val = valid_points[0][1]
    last_val = valid_points[-1][1]
    overall_delta = last_val - first_val

    # Check for zigzag / fluctuating patterns if we have 3 or 4 points
    if len(valid_points) >= 3:
        deltas = [valid_points[i + 1][1] - valid_points[i][1] for i in range(len(valid_points) - 1)]
        has_positive = any(d > threshold_delta for d in deltas)
        has_negative = any(d < -threshold_delta for d in deltas)
        if has_positive and has_negative and abs(overall_delta) < threshold_delta * 1.5:
            return TREND_FLUCTUATING

    if overall_delta <= -threshold_delta:
        return TREND_IMPROVING
    elif overall_delta >= threshold_delta:
        return TREND_WORSENING
    else:
        return TREND_STABLE


def calculate_4_week_report(
    patient_id: str,
    readings: List[GlucoseReading],
    hypo_threshold: float = settings.GLUCOSE_HYPO_THRESHOLD,
    normal_max: float = settings.GLUCOSE_NORMAL_MAX,
    prediabetes_max: float = settings.GLUCOSE_PREDIABETES_MAX,
) -> FourWeekCalculationResult:
    """Groups telemetry into 4 discrete monitoring weeks, computes deterministic means,
    clinical staging, and overall trend trajectory.
    """
    # Group readings by week number (1 to 4)
    week_groups: Dict[int, List[float]] = {1: [], 2: [], 3: [], 4: []}
    total_valid_readings = 0

    for r in readings:
        # Filter valid week ranges and physical glucose boundaries (20 - 600 mg/dL)
        if 1 <= r.week_number <= 4:
            val = r.glucose_value
            if val is not None and not math.isnan(val) and 20.0 <= val <= 600.0:
                week_groups[r.week_number].append(float(val))
                total_valid_readings += 1
            else:
                logger.warning(
                    "Excluded anomalous/invalid glucose reading %s for patient %s",
                    val,
                    patient_id,
                )

    weekly_metrics: List[WeeklyMetric] = []
    weekly_averages_dict: Dict[str, Optional[float]] = {}
    weekly_stages_dict: Dict[str, str] = {}
    averages_list: List[Optional[float]] = []

    for week_num in range(1, 5):
        vals = week_groups[week_num]
        if vals:
            avg = round(sum(vals) / len(vals), 1)
            stage = classify_stage(
                avg,
                hypo_threshold=hypo_threshold,
                normal_max=normal_max,
                prediabetes_max=prediabetes_max,
            )
        else:
            avg = None
            stage = STAGE_INSUFFICIENT

        metric = WeeklyMetric(
            week_number=week_num,
            average_glucose=avg,
            stage=stage,
            reading_count=len(vals),
        )
        weekly_metrics.append(metric)
        weekly_averages_dict[f"week_{week_num}"] = avg
        weekly_stages_dict[f"week_{week_num}"] = stage
        averages_list.append(avg)

    # Determine latest / current stage
    current_stage = STAGE_INSUFFICIENT
    for metric in reversed(weekly_metrics):
        if metric.average_glucose is not None:
            current_stage = metric.stage
            break

    # Determine trend
    trend = calculate_trend(averages_list)

    return FourWeekCalculationResult(
        patient_id=patient_id,
        weeks=weekly_metrics,
        weekly_averages=weekly_averages_dict,
        weekly_stages=weekly_stages_dict,
        current_stage=current_stage,
        trend=trend,
        total_readings_analyzed=total_valid_readings,
        has_sufficient_data=total_valid_readings > 0,
    )
