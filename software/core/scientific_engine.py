"""
LuxSense Pro — Scientific Metrology & Photometric Analysis Engine
Provides rigorous scientific computations:
- Lux / Foot-Candle conversion
- Time-integrated light exposure (Lux-hours & Lux-seconds per CIE 157:2004)
- Spatial illuminance mapping & lighting uniformity (U1, U2, Diversity ratio per EN 12464-1)
- Statistical analysis & combined uncertainty budgeting (GUM / ISO 98-3 standard)
- Threshold excursion analysis
- Experiment session comparative analysis
- Scientific CSV and print-ready report generation
"""

import math
import time
import json
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional, Tuple

# Physical & Photometric Constants
LUX_PER_FOOT_CANDLE = 10.7639104
PHOTOPIC_LUMINOUS_EFFICACY_555NM = 683.008  # lm/W at 555 nm (CIE standard)

# Museum conservation exposure limits (CIE 157:2004) in lx·h / year
EXPOSURE_LIMITS_CIE157 = {
    "highly_sensitive": 50000,    # Silk, historical textiles, watercolors
    "moderately_sensitive": 150000, # Oil paintings, wood, leather
    "insensitive": 450000,          # Stone, metal, ceramics, glass
}

@dataclass
class UncertaintyBudget:
    sample_mean: float
    standard_deviation: float
    standard_error: float
    degrees_of_freedom: int
    sensor_accuracy_spec_percent: float  # e.g., 7.0% calibrated (or 20.0% uncalibrated)
    sensor_uncertainty_lux: float
    repeatability_uncertainty_lux: float
    combined_standard_uncertainty: float
    expanded_uncertainty_95: float       # k = 2.0 (approx 95% confidence)
    relative_expanded_uncertainty_pct: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class SpatialMeasurementPoint:
    point_id: str
    label: str
    x_m: float
    y_m: float
    measured_lux: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class UniformityReport:
    points_count: int
    min_lux: float
    max_lux: float
    average_lux: float
    uniformity_u1: float  # E_min / E_avg (Task area uniformity)
    uniformity_u2: float  # E_min / E_max
    diversity_ratio: float # E_max / E_min
    en12464_compliant: bool # U1 >= 0.60 for typical office task area
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ExposureReport:
    total_duration_seconds: float
    duration_hours: float
    cumulative_lux_seconds: float
    cumulative_lux_hours: float
    average_lux: float
    daily_projected_lux_hours: float
    annual_projected_lux_hours: float
    cie157_conservation_status: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ThresholdReport:
    min_threshold_lux: float
    max_threshold_lux: float
    total_samples: int
    in_range_samples: int
    in_range_percent: float
    under_threshold_samples: int
    over_threshold_samples: int
    compliance_status: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

# -----------------------------------------------------------------------------
# Metric Conversions
# -----------------------------------------------------------------------------
def lux_to_foot_candles(lux: float) -> float:
    """Convert illuminance from Lux to Foot-Candles (lm/ft^2)."""
    return round(lux / LUX_PER_FOOT_CANDLE, 4)

def foot_candles_to_lux(fc: float) -> float:
    """Convert illuminance from Foot-Candles to Lux (lm/m^2)."""
    return round(fc * LUX_PER_FOOT_CANDLE, 2)

def lux_to_estimated_irradiance(lux: float) -> float:
    """
    ESTIMATED: Approximate optical irradiance in W/m^2 based on 555nm photopic peak.
    Explicitly labeled as ESTIMATED because spectral distribution varies with light source.
    """
    return round(lux / PHOTOPIC_LUMINOUS_EFFICACY_555NM, 5)

# -----------------------------------------------------------------------------
# Scientific Uncertainty & Statistics (GUM / ISO 98-3)
# -----------------------------------------------------------------------------
def calculate_uncertainty_budget(
    values: List[float], 
    sensor_accuracy_percent: float = 7.0
) -> UncertaintyBudget:
    """
    Computes rigorous metrological uncertainty budget conforming to GUM (Guide to the
    Expression of Uncertainty in Measurement).
    """
    n = len(values)
    if n == 0:
        return UncertaintyBudget(
            sample_mean=0.0,
            standard_deviation=0.0,
            standard_error=0.0,
            degrees_of_freedom=0,
            sensor_accuracy_spec_percent=sensor_accuracy_percent,
            sensor_uncertainty_lux=0.0,
            repeatability_uncertainty_lux=0.0,
            combined_standard_uncertainty=0.0,
            expanded_uncertainty_95=0.0,
            relative_expanded_uncertainty_pct=0.0
        )

    mean_val = sum(values) / n
    if n > 1:
        variance = sum((x - mean_val) ** 2 for x in values) / (n - 1)
        s = math.sqrt(variance)
    else:
        s = 0.0

    standard_error = s / math.sqrt(n) if n > 0 else 0.0

    # Type B uncertainty: rectangular distribution assumption for manufacturer accuracy
    u_sensor = (mean_val * (sensor_accuracy_percent / 100.0)) / math.sqrt(3.0)

    # Type A uncertainty: repeatability of readings
    u_repeatability = standard_error

    # Combined standard uncertainty
    u_combined = math.sqrt(u_sensor ** 2 + u_repeatability ** 2)

    # Expanded uncertainty with coverage factor k = 2.0 (approx 95.45% confidence)
    u_expanded = 2.0 * u_combined
    rel_expanded_pct = (u_expanded / mean_val * 100.0) if mean_val > 0 else 0.0

    return UncertaintyBudget(
        sample_mean=round(mean_val, 2),
        standard_deviation=round(s, 2),
        standard_error=round(standard_error, 3),
        degrees_of_freedom=max(0, n - 1),
        sensor_accuracy_spec_percent=round(sensor_accuracy_percent, 1),
        sensor_uncertainty_lux=round(u_sensor, 2),
        repeatability_uncertainty_lux=round(u_repeatability, 3),
        combined_standard_uncertainty=round(u_combined, 2),
        expanded_uncertainty_95=round(u_expanded, 2),
        relative_expanded_uncertainty_pct=round(rel_expanded_pct, 2)
    )

# -----------------------------------------------------------------------------
# Light Exposure Integration (Lux-Hours)
# -----------------------------------------------------------------------------
def calculate_light_exposure(
    time_lux_series: List[Tuple[float, float]]
) -> ExposureReport:
    """
    Computes time-integrated illuminance exposure H_v using trapezoidal integration:
    H_v = integral(E_v dt) in lux-seconds and lux-hours.
    """
    if len(time_lux_series) < 2:
        return ExposureReport(
            total_duration_seconds=0.0,
            duration_hours=0.0,
            cumulative_lux_seconds=0.0,
            cumulative_lux_hours=0.0,
            average_lux=0.0,
            daily_projected_lux_hours=0.0,
            annual_projected_lux_hours=0.0,
            cie157_conservation_status="INSUFFICIENT_DATA"
        )

    # Sort by timestamp
    sorted_pts = sorted(time_lux_series, key=lambda x: x[0])
    total_lux_seconds = 0.0

    for i in range(1, len(sorted_pts)):
        t_prev, lux_prev = sorted_pts[i - 1]
        t_curr, lux_curr = sorted_pts[i]
        dt = max(0.0, t_curr - t_prev)
        # Trapezoidal slice
        total_lux_seconds += 0.5 * (lux_prev + lux_curr) * dt

    total_duration_sec = sorted_pts[-1][0] - sorted_pts[0][0]
    total_hours = total_duration_sec / 3600.0 if total_duration_sec > 0 else 0.0
    total_lux_hours = total_lux_seconds / 3600.0
    avg_lux = (total_lux_seconds / total_duration_sec) if total_duration_sec > 0 else 0.0

    # Annual projection assuming 10 hours exposure per day for 365 days
    daily_lux_hours = avg_lux * 10.0
    annual_lux_hours = daily_lux_hours * 365.0

    # Conservation status classification
    if annual_lux_hours <= EXPOSURE_LIMITS_CIE157["highly_sensitive"]:
        status = "COMPLIANT: Safe for Highly Sensitive Archival Materials (Silk/Watercolors)"
    elif annual_lux_hours <= EXPOSURE_LIMITS_CIE157["moderately_sensitive"]:
        status = "COMPLIANT: Suitable for Moderately Sensitive Art (Oil Paintings/Wood)"
    elif annual_lux_hours <= EXPOSURE_LIMITS_CIE157["insensitive"]:
        status = "COMPLIANT: Standard Museum Exhibits (Ceramics/Metals)"
    else:
        status = "EXCEEDED: High Exposure Hazard — UV/Photolytic Degradation Risk"

    return ExposureReport(
        total_duration_seconds=round(total_duration_sec, 1),
        duration_hours=round(total_hours, 3),
        cumulative_lux_seconds=round(total_lux_seconds, 1),
        cumulative_lux_hours=round(total_lux_hours, 2),
        average_lux=round(avg_lux, 2),
        daily_projected_lux_hours=round(daily_lux_hours, 1),
        annual_projected_lux_hours=round(annual_lux_hours, 0),
        cie157_conservation_status=status
    )

# -----------------------------------------------------------------------------
# Spatial Illuminance Mapping & Uniformity
# -----------------------------------------------------------------------------
def calculate_spatial_uniformity(points: List[SpatialMeasurementPoint]) -> UniformityReport:
    """
    Computes lighting uniformity ratios according to EN 12464-1 & IESNA standards:
    - Uniformity U1 = E_min / E_avg (Task area uniformity)
    - Uniformity U2 = E_min / E_max
    - Diversity ratio D = E_max / E_min
    """
    if not points:
        return UniformityReport(
            points_count=0,
            min_lux=0.0,
            max_lux=0.0,
            average_lux=0.0,
            uniformity_u1=0.0,
            uniformity_u2=0.0,
            diversity_ratio=1.0,
            en12464_compliant=False,
            summary="No spatial points recorded."
        )

    lux_vals = [
        p.measured_lux if hasattr(p, "measured_lux") else float(p.get("measured_lux", 0.0))
        for p in points
    ]
    min_val = min(lux_vals)
    max_val = max(lux_vals)
    avg_val = sum(lux_vals) / len(lux_vals)

    u1 = (min_val / avg_val) if avg_val > 0 else 0.0
    u2 = (min_val / max_val) if max_val > 0 else 0.0
    diversity = (max_val / min_val) if min_val > 0 else (999.0 if max_val > 0 else 1.0)

    # Standard EN 12464-1 task area requirement: U1 >= 0.60
    compliant = u1 >= 0.60
    if compliant:
        summary = f"Compliant with EN 12464-1 (U1 = {u1:.2f} >= 0.60). Uniform illumination."
    elif u1 >= 0.40:
        summary = f"Marginal (U1 = {u1:.2f} >= 0.40). Suitable for surrounding area, but sub-optimal for fine task."
    else:
        summary = f"Non-compliant (U1 = {u1:.2f} < 0.40). Significant glare or shadow disparities detected."

    return UniformityReport(
        points_count=len(points),
        min_lux=round(min_val, 2),
        max_lux=round(max_val, 2),
        average_lux=round(avg_val, 2),
        uniformity_u1=round(u1, 3),
        uniformity_u2=round(u2, 3),
        diversity_ratio=round(diversity, 2),
        en12464_compliant=compliant,
        summary=summary
    )

# -----------------------------------------------------------------------------
# Threshold Compliance Analysis
# -----------------------------------------------------------------------------
def analyze_threshold_compliance(
    values: List[float], 
    min_threshold: float, 
    max_threshold: float
) -> ThresholdReport:
    """Analyze percentage of samples within designated upper and lower bounds."""
    if not values:
        return ThresholdReport(
            min_threshold_lux=min_threshold,
            max_threshold_lux=max_threshold,
            total_samples=0,
            in_range_samples=0,
            in_range_percent=0.0,
            under_threshold_samples=0,
            over_threshold_samples=0,
            compliance_status="NO_DATA"
        )

    total = len(values)
    under = sum(1 for v in values if v < min_threshold)
    over = sum(1 for v in values if v > max_threshold)
    in_range = total - (under + over)
    in_range_pct = (in_range / total) * 100.0

    if in_range_pct >= 95.0:
        status = "EXCELLENT (>=95% within tolerances)"
    elif in_range_pct >= 80.0:
        status = "ACCEPTABLE (80% - 94% within tolerances)"
    else:
        status = "NON-COMPLIANT (<80% within tolerances)"

    return ThresholdReport(
        min_threshold_lux=min_threshold,
        max_threshold_lux=max_threshold,
        total_samples=total,
        in_range_samples=in_range,
        in_range_percent=round(in_range_pct, 1),
        under_threshold_samples=under,
        over_threshold_samples=over,
        compliance_status=status
    )
