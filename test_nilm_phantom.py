"""
Basic tests for nilm_phantom.py (Person 2).
Run with:  pytest tests/test_nilm_phantom.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
from nilm_phantom import (
    NILMClassifier, PhantomDetector, run_pipeline, demo_stream, SIGNATURES
)


def test_classifier_trains_and_predicts():
    clf = NILMClassifier().fit()
    label, conf = clf.predict_sample(p=1800, pf=0.90)   # squarely in AC's range
    assert label == "Air Conditioner"
    assert 0.0 <= conf <= 1.0


def test_phantom_detector_needs_sustained_standby():
    det = PhantomDetector(min_minutes=15)
    is_phantom = False
    # 14 minutes of standby should NOT trigger yet (1 sample = 1 minute)
    for _ in range(14):
        is_phantom, alert = det.update("Smart TV (Standby)", power_w=2.0, dt_s=60)
    assert is_phantom is False

    # the 15th minute should trigger exactly one alert
    is_phantom, alert = det.update("Smart TV (Standby)", power_w=2.0, dt_s=60)
    assert is_phantom is True
    assert alert is not None
    assert "Smart TV (Standby)" in alert

    # it should not re-fire the alert every subsequent minute
    _, alert2 = det.update("Smart TV (Standby)", power_w=2.0, dt_s=60)
    assert alert2 is None


def test_active_device_never_flagged_phantom():
    det = PhantomDetector(min_minutes=15)
    for _ in range(30):
        is_phantom, alert = det.update("Air Conditioner", power_w=1600, dt_s=60)
    assert is_phantom is False
    assert alert is None


def test_pipeline_runs_on_demo_data():
    df = demo_stream()
    result = run_pipeline(df, interval_s=60)
    expected_cols = {
        "timestamp", "active_power", "power_factor", "appliance",
        "confidence", "state", "is_phantom", "alert",
    }
    assert expected_cols.issubset(result.columns)
    assert len(result) == len(df)
    assert result["is_phantom"].sum() > 0   # demo data includes standby stretches


def test_pipeline_accepts_minimal_columns():
    """Person 1 might not send ReactivePower/PowerFactor — pipeline should still run."""
    df = pd.DataFrame({
        "Timestamp": range(20),
        "Voltage": [230] * 20,
        "Current": [0.5] * 20,
        "ActivePower": [100] * 20,
    })
    result = run_pipeline(df, interval_s=60)
    assert len(result) == 20


def test_all_signatures_have_valid_ranges():
    for name, sig in SIGNATURES.items():
        assert sig.p[0] <= sig.p[1], f"{name}: power range reversed"
        assert 0 <= sig.pf[0] <= sig.pf[1] <= 1, f"{name}: power factor out of bounds"
