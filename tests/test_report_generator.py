"""
Tests for Scientific Report Generator
Verifies generation of scientific CSV and HTML certificate reports.
"""

from pathlib import Path
from software.core.report_generator import generate_scientific_csv, generate_scientific_html_report

def test_generate_scientific_csv():
    csv_file = generate_scientific_csv("default")
    assert Path(csv_file).exists()
    content = Path(csv_file).read_text(encoding="utf-8")
    assert "LUXSENSE PRO SCIENTIFIC METROLOGY REPORT" in content
    assert "UNCERTAINTY & METROLOGICAL BUDGET" in content
    assert "[MEASURED]" in content
    assert "[CALIBRATED]" in content
    assert "[CALCULATED]" in content
    assert "[ESTIMATED]" in content

def test_generate_scientific_html_report():
    html_file = generate_scientific_html_report("default")
    assert Path(html_file).exists()
    content = Path(html_file).read_text(encoding="utf-8")
    assert "LuxSense Pro" in content
    assert "Metrological Uncertainty Budget" in content
    assert "Spatial Lighting Uniformity" in content
    assert "Time-Integrated Exposure" in content
    assert "Scientific Integrity &amp; Instrument Scope Disclosure" in content
