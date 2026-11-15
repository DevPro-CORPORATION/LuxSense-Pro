"""
Tests for LuxSense Pro Scientific Metrology Engine
Verifies photometric conversions, uncertainty budgets, exposure integration, and uniformity.
"""

import pytest
from software.core.scientific_engine import (
    lux_to_foot_candles,
    foot_candles_to_lux,
    lux_to_estimated_irradiance,
    calculate_uncertainty_budget,
    calculate_light_exposure,
    calculate_spatial_uniformity,
    analyze_threshold_compliance,
    SpatialMeasurementPoint
)

def test_lux_fc_conversion_roundtrip():
    original_lux = 500.0
    fc = lux_to_foot_candles(original_lux)
    assert 46.4 <= fc <= 46.5
    back_lux = foot_candles_to_lux(fc)
    assert abs(back_lux - original_lux) < 0.1

def test_estimated_irradiance():
    lux = 683.008
    irr = lux_to_estimated_irradiance(lux)
    assert abs(irr - 1.0) < 0.01

def test_uncertainty_budget_calculation():
    # 10 readings centered around 500 lux with slight noise
    readings = [502.1, 498.4, 501.0, 499.5, 500.2, 503.4, 497.8, 500.9, 501.5, 499.0]
    budget = calculate_uncertainty_budget(readings, sensor_accuracy_percent=7.0)

    assert 499.0 < budget.sample_mean < 502.0
    assert budget.standard_deviation > 0.0
    assert budget.standard_error > 0.0
    assert budget.degrees_of_freedom == 9
    assert budget.sensor_uncertainty_lux > 0.0
    assert budget.combined_standard_uncertainty > 0.0
    assert budget.expanded_uncertainty_95 > budget.combined_standard_uncertainty
    assert 0.0 < budget.relative_expanded_uncertainty_pct < 15.0

def test_light_exposure_integration():
    # 1 hour (3600 seconds) at museum archive level 10 lux
    series = [
        (0.0, 10.0),
        (1800.0, 10.0),
        (3600.0, 10.0)
    ]
    report = calculate_light_exposure(series)
    assert report.total_duration_seconds == 3600.0
    assert abs(report.duration_hours - 1.0) < 0.001
    assert abs(report.cumulative_lux_hours - 10.0) < 1.0
    assert report.average_lux == 10.0
    assert "COMPLIANT" in report.cie157_conservation_status

def test_spatial_uniformity_en12464():
    pts = [
        SpatialMeasurementPoint("P1", "Desk Left", 0.0, 0.0, 480.0, "10:00:00"),
        SpatialMeasurementPoint("P2", "Desk Center", 0.5, 0.0, 520.0, "10:00:05"),
        SpatialMeasurementPoint("P3", "Desk Right", 1.0, 0.0, 500.0, "10:00:10"),
    ]
    report = calculate_spatial_uniformity(pts)
    assert report.points_count == 3
    assert report.min_lux == 480.0
    assert report.max_lux == 520.0
    assert report.average_lux == 500.0
    # U1 = 480 / 500 = 0.96 >= 0.60
    assert report.uniformity_u1 == 0.96
    assert report.en12464_compliant is True

def test_threshold_compliance():
    readings = [450.0, 500.0, 520.0, 480.0, 750.0, 200.0]
    report = analyze_threshold_compliance(readings, min_threshold=400.0, max_threshold=600.0)
    assert report.total_samples == 6
    assert report.in_range_samples == 4 # 450, 500, 520, 480
    assert report.under_threshold_samples == 1 # 200
    assert report.over_threshold_samples == 1 # 750
    assert abs(report.in_range_percent - (4/6 * 100)) < 0.1
