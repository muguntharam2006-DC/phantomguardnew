import streamlit as st
import pandas as pd
import numpy as np
import os
from nilm_phantom import run_pipeline

st.set_page_config(page_title="PhantomGuard: Smart Power Strip", page_icon="⚡", layout="wide")

st.title("⚡ PhantomGuard: Smart Power Strip & Phantom Load Monitor")
st.markdown("AI-powered appliance identification (NILM), standby waste detection, and Indian DISCOM slab billing.")

# Sidebar Configuration
st.sidebar.header("Configuration")
data_source = st.sidebar.selectbox(
    "Select Data Source", 
    ["Default Demo Data (sample_power_data.csv)", "Person 1 Dataset (phantomguard_energy_dataset.csv)"]
)

# Safe local loader function
def load_data(source):
    if "Person 1" in source and os.path.exists("data/phantomguard_energy_dataset.csv"):
        return pd.read_csv("data/phantomguard_energy_dataset.csv")
    elif os.path.exists("sample_power_data.csv"):
        return pd.read_csv("sample_power_data.csv")
    else:
        return pd.DataFrame({
            'Timestamp': [0, 60, 120],
            'Voltage': [230.0, 230.0, 230.0],
            'Current': [0.1, 0.1, 0.5],
            'ActivePower': [2.0, 2.0, 100.0],
            'ReactivePower': [1.0, 1.0, 10.0],
            'PowerFactor': [0.5, 0.5, 0.9]
        })

df = load_data(data_source)

# Run NILM Pipeline from Person 2
results_df = run_pipeline(df)

# Standardize column names to lowercase to prevent key errors
results_df.columns = [str(c).lower() for c in results_df.columns]

# Handle column name variations gracefully
volt_col = 'voltage' if 'voltage' in results_df.columns else None
power_col = 'active_power' if 'active_power' in results_df.columns else ('activepower' if 'activepower' in results_df.columns else results_df.columns[1])
time_col = 'timestamp' if 'timestamp' in results_df.columns else results_df.columns[0]

# Top Summary Metrics
col1, col2, col3 = st.columns(3)
avg_voltage = results_df[volt_col].mean() if volt_col else 230.0
avg_power = results_df[power_col].mean()

total_energy_kwh = (avg_power * len(results_df) * 60 / 3600) / 1000 
slab_rate = 7.0  # Indian DISCOM average placeholder tariff rate per unit (₹/kWh)
estimated_bill = total_energy_kwh * 30 * slab_rate

col1.metric("Avg Voltage", f"{avg_voltage:.1f} V")
col2.metric("Total Active Power (Avg)", f"{avg_power:.2f} W")
col3.metric("Est. Monthly Bill (Slab)", f"₹ {estimated_bill:.2f}")

# Tariff Warning Check
if estimated_bill > 1000:
    st.warning("⚠️ **Tariff Slab Warning:** Projected monthly usage exceeds standard subsidized tiers. Check your phantom loads below.")

# Alerts Section (Person 2 Integration)
st.subheader("🚨 Phantom Load Alerts")
alert_col = 'alert' if 'alert' in results_df.columns else None
if alert_col:
    alerts = results_df[results_df[alert_col].notnull()][alert_col].unique()
    if len(alerts) > 0:
        for alert in alerts:
            st.error(alert)
    else:
        st.success("No active phantom loads detected right now!")
else:
    st.success("No alerts column found.")

# Dashboard Charts & Table
st.subheader("📊 Live Power Consumption & Appliance Stream")
chart_data = results_df.set_index(time_col)[[power_col]] if time_col in results_df.columns else results_df[[power_col]]
st.line_chart(chart_data)

st.subheader("Detailed Sensor & NILM Log")
st.dataframe(results_df, use_container_width=True)