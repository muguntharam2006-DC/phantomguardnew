import math
import random
from datetime import datetime, timedelta

import pandas as pd


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

START_TIME = datetime(2026, 9, 23, 8, 0, 0)

# One reading every minute
INTERVAL_MINUTES = 1

# Reproducible randomness
random.seed(42)


# ---------------------------------------------------------
# Appliance scenarios
# ---------------------------------------------------------
# Power ranges are chosen to work with the current
# PhantomGuard NILM signature ranges.
#
# Each scenario:
#   duration = number of minutes
#   appliance = user-friendly appliance name
#   status = ON / Standby / OFF
#   power_min / power_max = active power range
#   pf_min / pf_max = power factor range
#   nilm_label = label corresponding to the current NILM
# ---------------------------------------------------------

SCENARIOS = [
    # Fan
    {
        "duration": 20,
        "appliance": "Fan",
        "status": "ON",
        "power_min": 28,
        "power_max": 42,
        "pf_min": 0.90,
        "pf_max": 0.98,
        "nilm_label": "BLDC Ceiling Fan",
    },
    {
        "duration": 10,
        "appliance": "Fan",
        "status": "OFF",
        "power_min": 0.05,
        "power_max": 0.30,
        "pf_min": 0.10,
        "pf_max": 0.30,
        "nilm_label": "Off / Idle",
    },

    # TV
    {
        "duration": 20,
        "appliance": "TV",
        "status": "ON",
        "power_min": 60,
        "power_max": 120,
        "pf_min": 0.90,
        "pf_max": 0.99,
        "nilm_label": "Smart TV (Active)",
    },
    {
        "duration": 20,
        "appliance": "TV",
        "status": "Standby",
        "power_min": 1,
        "power_max": 3,
        "pf_min": 0.20,
        "pf_max": 0.40,
        "nilm_label": "Smart TV (Standby)",
    },

    # Laptop
    {
        "duration": 20,
        "appliance": "Laptop",
        "status": "ON",
        "power_min": 45,
        "power_max": 70,
        "pf_min": 0.90,
        "pf_max": 0.99,
        "nilm_label": "Laptop Charger (Active)",
    },
    {
        "duration": 20,
        "appliance": "Laptop",
        "status": "Standby",
        "power_min": 3,
        "power_max": 6,
        "pf_min": 0.20,
        "pf_max": 0.50,
        "nilm_label": "Laptop Charger (Idle)",
    },

    # Refrigerator
    {
        "duration": 20,
        "appliance": "Refrigerator",
        "status": "ON",
        "power_min": 130,
        "power_max": 200,
        "pf_min": 0.80,
        "pf_max": 0.95,
        "nilm_label": "Refrigerator",
    },
    {
        "duration": 15,
        "appliance": "Refrigerator",
        "status": "OFF",
        "power_min": 0.05,
        "power_max": 0.30,
        "pf_min": 0.10,
        "pf_max": 0.30,
        "nilm_label": "Off / Idle",
    },

    # AC
    {
        "duration": 20,
        "appliance": "AC",
        "status": "ON",
        "power_min": 1300,
        "power_max": 1800,
        "pf_min": 0.85,
        "pf_max": 0.98,
        "nilm_label": "Air Conditioner",
    },
    {
        "duration": 20,
        "appliance": "AC",
        "status": "Standby",
        "power_min": 1,
        "power_max": 3,
        "pf_min": 0.20,
        "pf_max": 0.40,
        "nilm_label": "Smart TV (Standby)",
    },
]


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def generate_voltage():
    """
    Simulate normal household voltage with small variation.
    """
    return round(random.uniform(228.0, 232.0), 2)


def generate_power(scenario):
    """
    Generate active power within the scenario's range.
    """
    return random.uniform(
        scenario["power_min"],
        scenario["power_max"]
    )


def generate_power_factor(scenario):
    """
    Generate a power factor appropriate for the scenario.
    """
    return random.uniform(
        scenario["pf_min"],
        scenario["pf_max"]
    )


def calculate_current(power, voltage, power_factor):
    """
    I = P / (V × PF)
    """
    if voltage <= 0 or power_factor <= 0:
        return 0.0

    return power / (voltage * power_factor)


def calculate_reactive_power(power, power_factor):
    """
    Q = P × tan(acos(PF))
    """
    power_factor = max(0.01, min(power_factor, 1.0))

    angle = math.acos(power_factor)

    return power * math.tan(angle)


def calculate_energy_kwh(power, interval_minutes):
    """
    Energy (kWh) = Power (W) × time (hours) / 1000
    """
    hours = interval_minutes / 60

    return (power * hours) / 1000


# ---------------------------------------------------------
# Dataset generation
# ---------------------------------------------------------

def generate_dataset():
    rows = []

    timestamp = START_TIME
    cumulative_energy = 0.0

    for scenario in SCENARIOS:

        for _ in range(scenario["duration"]):

            voltage = generate_voltage()
            power = generate_power(scenario)
            power_factor = generate_power_factor(scenario)

            current = calculate_current(
                power,
                voltage,
                power_factor
            )

            reactive_power = calculate_reactive_power(
                power,
                power_factor
            )

            energy_kwh = calculate_energy_kwh(
                power,
                INTERVAL_MINUTES
            )

            cumulative_energy += energy_kwh

            rows.append({
                "Timestamp": timestamp.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),

                "Voltage": round(voltage, 2),

                "Current": round(current, 3),

                "ActivePower": round(power, 2),

                "ReactivePower": round(
                    reactive_power,
                    2
                ),

                "PowerFactor": round(
                    power_factor,
                    3
                ),

                "Appliance": scenario["appliance"],

                "Status": scenario["status"],

                "NILMLabel": scenario["nilm_label"],

                "Energy_kWh": round(
                    energy_kwh,
                    6
                ),

                "CumulativeEnergy_kWh": round(
                    cumulative_energy,
                    6
                ),
            })

            timestamp += timedelta(
                minutes=INTERVAL_MINUTES
            )

    return pd.DataFrame(rows)


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

if __name__ == "__main__":

    df = generate_dataset()

    output_file = "data/phantomguard_energy_dataset.csv"

    df.to_csv(
        output_file,
        index=False
    )

    print()
    print("==========================================")
    print(" PhantomGuard Dataset Generator")
    print("==========================================")
    print()
    print(f"Generated rows : {len(df)}")
    print(f"Output file    : {output_file}")
    print()
    print("Columns:")
    for column in df.columns:
        print(f"  - {column}")

    print()
    print("Appliance distribution:")
    print(df["Appliance"].value_counts())

    print()
    print("Status distribution:")
    print(df["Status"].value_counts())

    print()
    print("Total energy:")
    print(
        f"{df['CumulativeEnergy_kWh'].iloc[-1]:.3f} kWh"
    )

    print()
    print("Dataset generated successfully!")