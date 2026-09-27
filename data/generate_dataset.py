import math
import random
from datetime import datetime, timedelta

import pandas as pd


# =========================================================
# CONFIGURATION
# =========================================================

START_TIME = datetime(2026, 9, 23, 8, 0, 0)

# One reading every minute
INTERVAL_MINUTES = 1

# Reproducible random values
random.seed(42)


# =========================================================
# ROOM CONFIGURATION
# =========================================================
# Each room has a maximum allowed simulated load.

ROOM_LIMITS = {
    "Living Room": 500,
    "Bedroom": 2000,
    "Kitchen": 500,
}


# =========================================================
# APPLIANCE CONFIGURATION
# =========================================================
# Device limits are simulated limits for the dashboard.
#
# These are NOT physical hardware specifications.
# They are simply thresholds used by PhantomGuard.
# =========================================================

DEVICE_LIMITS = {
    "Fan": 50,
    "TV": 120,
    "Laptop": 80,
    "Refrigerator": 220,
    "AC": 1600,
}


# =========================================================
# SCENARIOS
# =========================================================
#
# The first six fields are compatible with the existing
# PhantomGuard NILM input format.
#
# power_min / power_max:
#     simulated active power range
#
# pf_min / pf_max:
#     simulated power-factor range
#
# nilm_label:
#     reference label for validation
#
# room:
#     simulated location of the appliance
#
# =========================================================

SCENARIOS = [

    # -----------------------------------------------------
    # FAN - LIVING ROOM
    # -----------------------------------------------------

    {
        "duration": 20,
        "room": "Living Room",
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
        "room": "Living Room",
        "appliance": "Fan",
        "status": "OFF",
        "power_min": 0.05,
        "power_max": 0.30,
        "pf_min": 0.10,
        "pf_max": 0.30,
        "nilm_label": "Off / Idle",
    },


    # -----------------------------------------------------
    # TV - LIVING ROOM
    # -----------------------------------------------------

    {
        "duration": 20,
        "room": "Living Room",
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
        "room": "Living Room",
        "appliance": "TV",
        "status": "Standby",
        "power_min": 1,
        "power_max": 3,
        "pf_min": 0.20,
        "pf_max": 0.40,
        "nilm_label": "Smart TV (Standby)",
    },


    # -----------------------------------------------------
    # LAPTOP - BEDROOM
    # -----------------------------------------------------

    {
        "duration": 20,
        "room": "Bedroom",
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
        "room": "Bedroom",
        "appliance": "Laptop",
        "status": "Standby",
        "power_min": 3,
        "power_max": 6,
        "pf_min": 0.20,
        "pf_max": 0.50,
        "nilm_label": "Laptop Charger (Idle)",
    },


    # -----------------------------------------------------
    # REFRIGERATOR - KITCHEN
    # -----------------------------------------------------

    {
        "duration": 20,
        "room": "Kitchen",
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
        "room": "Kitchen",
        "appliance": "Refrigerator",
        "status": "OFF",
        "power_min": 0.05,
        "power_max": 0.30,
        "pf_min": 0.10,
        "pf_max": 0.30,
        "nilm_label": "Off / Idle",
    },


    # -----------------------------------------------------
    # AC - BEDROOM
    # -----------------------------------------------------
    #
    # Device limit is 1600 W.
    #
    # Some generated AC readings can exceed this limit,
    # allowing the control logic to simulate AUTO_OFF.
    #

    {
        "duration": 20,
        "room": "Bedroom",
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
        "room": "Bedroom",
        "appliance": "AC",
        "status": "Standby",
        "power_min": 1,
        "power_max": 3,
        "pf_min": 0.20,
        "pf_max": 0.40,
        "nilm_label": "Air Conditioner (Standby)",
    },
]


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def generate_voltage():
    """
    Simulate normal household voltage with small variation.
    """
    return round(random.uniform(228.0, 232.0), 2)


def generate_power(scenario):
    """
    Generate active power within the scenario range.
    """
    return random.uniform(
        scenario["power_min"],
        scenario["power_max"]
    )


def generate_power_factor(scenario):
    """
    Generate power factor within the scenario range.
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
    power_factor = max(
        0.01,
        min(power_factor, 1.0)
    )

    angle = math.acos(power_factor)

    return power * math.tan(angle)


def calculate_energy_kwh(power, interval_minutes):
    """
    Energy (kWh) =
    Power (W) × time (hours) / 1000
    """
    hours = interval_minutes / 60

    return (power * hours) / 1000


# =========================================================
# DATASET GENERATION
# =========================================================

def generate_dataset():

    rows = []

    timestamp = START_TIME

    cumulative_energy = 0.0

    # Tracks how long an appliance has remained in standby.
    standby_duration = 0

    for scenario in SCENARIOS:

        # Reset standby counter whenever scenario changes.
        if scenario["status"] != "Standby":
            standby_duration = 0

        for _ in range(scenario["duration"]):

            # ---------------------------------------------
            # Electrical values
            # ---------------------------------------------

            voltage = generate_voltage()

            power = generate_power(scenario)

            power_factor = generate_power_factor(
                scenario
            )

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


            # ---------------------------------------------
            # Room and device limits
            # ---------------------------------------------

            room = scenario["room"]

            appliance = scenario["appliance"]

            device_limit = DEVICE_LIMITS[appliance]

            room_limit = ROOM_LIMITS[room]


            # ---------------------------------------------
            # Phantom load
            # ---------------------------------------------

            if scenario["status"] == "Standby":

                standby_duration += INTERVAL_MINUTES

                phantom_load = power

            else:

                standby_duration = 0

                phantom_load = 0.0


            # ---------------------------------------------
            # Control simulation
            # ---------------------------------------------

            control_mode = "NONE"

            control_action = "NONE"


            # Automatic cut-off when device exceeds
            # its configured power limit.
            #
            # We record the event on the reading where
            # the limit was exceeded.

            if (
                scenario["status"] == "ON"
                and power > device_limit
            ):

                control_mode = "AUTO"

                control_action = "AUTO_OFF"


            # ---------------------------------------------
            # Example manual turn-off event
            # ---------------------------------------------
            #
            # The final minute of the TV ON scenario is
            # treated as a simulated manual turn-off command.
            #

            if (
                appliance == "TV"
                and scenario["status"] == "ON"
                and _ == scenario["duration"] - 1
            ):

                control_mode = "MANUAL"

                control_action = "MANUAL_OFF"


            # ---------------------------------------------
            # Save row
            # ---------------------------------------------

            rows.append({

                "Timestamp": timestamp.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),

                "Room": room,

                "Voltage": round(
                    voltage,
                    2
                ),

                "Current": round(
                    current,
                    3
                ),

                "ActivePower": round(
                    power,
                    2
                ),

                "ReactivePower": round(
                    reactive_power,
                    2
                ),

                "PowerFactor": round(
                    power_factor,
                    3
                ),

                "Appliance": appliance,

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

                "DevicePowerLimit_W": device_limit,

                "RoomPowerLimit_W": room_limit,

                "PhantomLoad_W": round(
                    phantom_load,
                    2
                ),

                "PhantomDuration_Min": standby_duration,

                "ControlMode": control_mode,

                "ControlAction": control_action,
            })


            timestamp += timedelta(
                minutes=INTERVAL_MINUTES
            )

    return pd.DataFrame(rows)


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    df = generate_dataset()

    output_file = (
        "data/phantomguard_energy_dataset.csv"
    )

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

    print(
        df["Appliance"].value_counts()
    )

    print()

    print("Room distribution:")

    print(
        df["Room"].value_counts()
    )

    print()

    print("Status distribution:")

    print(
        df["Status"].value_counts()
    )

    print()

    print("Control actions:")

    print(
        df["ControlAction"].value_counts()
    )

    print()

    print("Phantom-load rows:")

    print(
        (df["PhantomLoad_W"] > 0).sum()
    )

    print()

    print("Total energy:")

    print(
        f"{df['CumulativeEnergy_kWh'].iloc[-1]:.3f} kWh"
    )

    print()

    print("Dataset generated successfully!")