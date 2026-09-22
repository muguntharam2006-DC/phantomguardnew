"""
UrjaGuard - Person 2: NILM + Phantom Load Detection
====================================================
Pipeline:  generated power data  ->  appliance identification  ->
           phantom/standby detection  ->  simple alert

INPUT  (from Person 1's generator)  -- a pandas DataFrame / CSV with columns:
    Timestamp, Voltage, Current, ActivePower, ReactivePower, PowerFactor
    (ReactivePower / PowerFactor are optional; they are derived if missing)

OUTPUT (for Person 3 / dashboard) -- one dict per sample:
    {timestamp, active_power, power_factor, appliance, state,
     is_phantom, alert}          # alert is None unless phantom is confirmed

Run the demo:   python nilm_phantom.py --demo
Run on a CSV:   python nilm_phantom.py --csv power_data.csv --interval 60
"""
from __future__ import annotations

import argparse
import math
from collections import deque
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

# ----------------------------------------------------------------------------
# 1. APPLIANCE SIGNATURE LIBRARY
#    Ranges taken from the UrjaGuard pitch (Indian household fingerprint table)
#    p = real power (W), pf = power factor, phantom = standby waste,
#    essential = should be scheduled (e.g. night) rather than cut permanently
# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class Signature:
    p: tuple
    pf: tuple
    phantom: bool = False
    essential: bool = False


SIGNATURES: dict[str, Signature] = {
    "Off / Idle":               Signature((0.0, 0.5),      (0.10, 0.30)),
    "Set-Top Box (Active)":     Signature((18, 22),        (0.60, 0.70)),
    "Set-Top Box (Standby)":    Signature((15, 19),        (0.55, 0.65), phantom=True),
    "Smart TV (Active)":        Signature((60, 120),       (0.90, 0.98)),
    "Smart TV (Standby)":       Signature((1, 3),          (0.30, 0.45), phantom=True),
    "Wi-Fi Router":             Signature((8, 12),         (0.50, 0.60), phantom=True, essential=True),
    "Laptop Charger (Active)":  Signature((45, 70),        (0.90, 0.97)),
    "Laptop Charger (Idle)":    Signature((3, 6),          (0.35, 0.50), phantom=True),
    "BLDC Ceiling Fan":         Signature((28, 42),        (0.60, 0.78)),
    "Desktop PC + Monitor":     Signature((110, 250),      (0.90, 0.98)),
    "Refrigerator":             Signature((130, 200),      (0.55, 0.75), essential=True),
    "Microwave":                Signature((1000, 1300),    (0.95, 0.99)),
    "Air Conditioner":          Signature((1300, 1800),    (0.85, 0.95)),
    "Geyser":                   Signature((1900, 2100),    (0.99, 1.00)),
}

FEATURES = ["p_mean", "p_std", "pf_mean", "q_mean"]


# ----------------------------------------------------------------------------
# 2. FEATURE EXTRACTION
# ----------------------------------------------------------------------------
def reactive_from_pf(p: float, pf: float) -> float:
    """Q = P * tan(acos(PF))  (fallback when Person 1 doesn't send Q)."""
    pf = min(max(pf, 0.01), 1.0)
    return p * math.tan(math.acos(pf))


def window_features(p: np.ndarray, pf: np.ndarray, q: np.ndarray) -> list:
    """Collapse a short window of samples into one feature vector."""
    return [float(np.mean(p)), float(np.std(p)), float(np.mean(pf)), float(np.mean(q))]


# ----------------------------------------------------------------------------
# 3. SYNTHETIC TRAINING DATA (built from the signature library)
# ----------------------------------------------------------------------------
def make_training_data(samples_per_class: int = 400, window: int = 5, seed: int = 42):
    rng = np.random.default_rng(seed)
    X, y = [], []
    for name, sig in SIGNATURES.items():
        for _ in range(samples_per_class):
            p0 = rng.uniform(*sig.p)
            pf0 = rng.uniform(*sig.pf)
            noise = max(0.02 * p0, 0.05)                 # ~2% measurement noise
            p = p0 + rng.normal(0, noise, window)
            pf = np.clip(pf0 + rng.normal(0, 0.01, window), 0.05, 1.0)
            q = np.array([reactive_from_pf(abs(a), b) for a, b in zip(p, pf)])
            X.append(window_features(np.abs(p), pf, q))
            y.append(name)
    return pd.DataFrame(X, columns=FEATURES), np.array(y)


# ----------------------------------------------------------------------------
# 4. NILM CLASSIFIER  (Random Forest, as planned on Day 3)
# ----------------------------------------------------------------------------
class NILMClassifier:
    def __init__(self, window: int = 5):
        self.window = window
        self.model = RandomForestClassifier(n_estimators=150, random_state=42, n_jobs=-1)
        self.trained = False
        self._buf_p, self._buf_pf, self._buf_q = (deque(maxlen=window) for _ in range(3))

    def fit(self, X=None, y=None):
        if X is None:
            X, y = make_training_data(window=self.window)
        self.model.fit(X, y)
        self.trained = True
        return self

    def predict_sample(self, p: float, pf: float, q: float | None = None) -> tuple[str, float]:
        """Streaming prediction: feed one sample at a time, uses a rolling window."""
        q = reactive_from_pf(p, pf) if q is None else q
        self._buf_p.append(p); self._buf_pf.append(pf); self._buf_q.append(q)
        feats = pd.DataFrame(
            [window_features(np.array(self._buf_p), np.array(self._buf_pf), np.array(self._buf_q))],
            columns=FEATURES,
        )
        proba = self.model.predict_proba(feats)[0]
        i = int(np.argmax(proba))
        return str(self.model.classes_[i]), float(proba[i])

    def reset_window(self):
        for b in (self._buf_p, self._buf_pf, self._buf_q):
            b.clear()


# ----------------------------------------------------------------------------
# 5. PHANTOM LOAD DETECTOR
#    A device counts as phantom only after it has stayed in standby for
#    `min_minutes` continuously (PDF plan: sustained standby for 15+ mins).
# ----------------------------------------------------------------------------
class PhantomDetector:
    def __init__(self, min_minutes: float = 15, tariff_per_kwh: float = 7.0, grace: int = 3):
        self.grace = grace                 # tolerate this many stray samples inside a streak
        self._misses = 0
        self.min_seconds = min_minutes * 60
        self.tariff = tariff_per_kwh
        self._label = None
        self._elapsed = 0.0
        self._energy_wh = 0.0
        self._alerted = False

    def update(self, label: str, power_w: float, dt_s: float):
        """Returns (is_phantom_now, alert_or_None)."""
        sig = SIGNATURES[label]
        if not sig.phantom:
            self._misses += 1
            if self._misses > self.grace or self._label is None:
                self._label, self._elapsed, self._energy_wh, self._alerted = None, 0.0, 0.0, False
                return False, None
            self._elapsed += dt_s                      # brief glitch: keep the streak alive
            return self._elapsed >= self.min_seconds, None
        self._misses = 0

        if self._label is None or (label != self._label and self._alerted):
            # new standby streak (or a different device after we already alerted)
            self._label, self._elapsed, self._energy_wh, self._alerted = label, 0.0, 0.0, False
        else:
            self._label = label                        # flicker between similar standby labels
        self._elapsed += dt_s
        self._energy_wh += power_w * dt_s / 3600.0

        if self._elapsed >= self.min_seconds:
            alert = None
            if not self._alerted:                      # fire once per streak
                self._alerted = True
                alert = self._build_alert(label, sig, power_w)
            return True, alert
        return False, None

    def _build_alert(self, label: str, sig: Signature, power_w: float) -> str:
        mins = self._elapsed / 60
        kwh_month = power_w * 24 * 30 / 1000
        cost_month = kwh_month * self.tariff
        action = ("Schedule an automatic night cut-off (e.g. 1 AM - 6 AM)."
                  if sig.essential else "Enable auto cut-off for this socket.")
        return (f"PHANTOM LOAD: {label} has been in standby for {mins:.0f} min "
                f"drawing {power_w:.1f} W (~{kwh_month:.1f} units / Rs {cost_month:.0f} per month). "
                f"{action}")


# ----------------------------------------------------------------------------
# 6. END-TO-END PIPELINE
# ----------------------------------------------------------------------------
def run_pipeline(df: pd.DataFrame, interval_s: float = 1.0, min_minutes: float = 15,
                 tariff_per_kwh: float = 7.0, clf: NILMClassifier | None = None) -> pd.DataFrame:
    """Take Person 1's DataFrame and return it with appliance/state/phantom/alert columns."""
    clf = clf or NILMClassifier().fit()
    det = PhantomDetector(min_minutes, tariff_per_kwh)

    p_col = "ActivePower"
    pf_col = "PowerFactor" if "PowerFactor" in df else None
    q_col = "ReactivePower" if "ReactivePower" in df else None

    rows = []
    for _, r in df.iterrows():
        p = float(r[p_col])
        pf = float(r[pf_col]) if pf_col else 0.9
        q = float(r[q_col]) if q_col else None
        label, conf = clf.predict_sample(p, pf, q)
        is_ph, alert = det.update(label, p, interval_s)
        rows.append({
            "timestamp": r.get("Timestamp", None),
            "active_power": p,
            "power_factor": pf,
            "appliance": label,
            "confidence": round(conf, 2),
            "state": "Standby" if SIGNATURES[label].phantom else "Active/Off",
            "is_phantom": is_ph,
            "alert": alert,
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# 7. STANDALONE TEST DATA (so Person 2 can work without waiting on Person 1)
# ----------------------------------------------------------------------------
def demo_stream(seed: int = 7) -> pd.DataFrame:
    """1 sample/min: evening TV -> TV left on standby -> night STB standby -> fan."""
    rng = np.random.default_rng(seed)
    plan = [("Smart TV (Active)", 20), ("Smart TV (Standby)", 20),
            ("Set-Top Box (Standby)", 25), ("BLDC Ceiling Fan", 10),
            ("Off / Idle", 5), ("Laptop Charger (Idle)", 18)]
    rows = []
    for name, n in plan:
        sig = SIGNATURES[name]
        for _ in range(n):
            p = rng.uniform(*sig.p) + rng.normal(0, 0.02 * sum(sig.p) / 2)
            pf = float(np.clip(rng.uniform(*sig.pf), 0.05, 1.0))
            v = 230 + rng.normal(0, 3)
            p = abs(p)
            s = p / pf
            rows.append({"Timestamp": len(rows), "Voltage": round(v, 1),
                         "Current": round(s / v, 3), "ActivePower": round(p, 2),
                         "ReactivePower": round(reactive_from_pf(p, pf), 2),
                         "PowerFactor": round(pf, 2), "_truth": name})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(description="UrjaGuard NILM + phantom load detection")
    ap.add_argument("--demo", action="store_true", help="run on built-in synthetic data")
    ap.add_argument("--csv", help="CSV from Person 1's generator")
    ap.add_argument("--interval", type=float, default=60, help="seconds between samples")
    ap.add_argument("--min-minutes", type=float, default=15, help="standby minutes before alert")
    ap.add_argument("--out", default="nilm_results.csv")
    a = ap.parse_args()

    if a.csv:
        df = pd.read_csv(a.csv)
    elif a.demo:
        df = demo_stream()
    else:
        ap.error("use --demo or --csv <file>")

    res = run_pipeline(df, a.interval, a.min_minutes)
    if "_truth" in df:
        acc = (res["appliance"].values == df["_truth"].values).mean()
        print(f"Appliance identification accuracy on demo data: {acc:.1%}")
    print(f"Phantom samples: {int(res.is_phantom.sum())} / {len(res)}\n")
    for _, r in res[res.alert.notna()].iterrows():
        print(f"[t={r.timestamp}] {r.alert}")
    res.to_csv(a.out, index=False)
    print(f"\nSaved results -> {a.out}")


if __name__ == "__main__":
    main()
