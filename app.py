import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
from simulation import generate_demo_data
from calculations import packet_metrics, battery_status, classify_movement
from config import SETTINGS

st.set_page_config(page_title="WiTrac | Wildlife Telemetry", page_icon="🛰️", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
.stApp {background:#0b1220;color:#e8eef7}
[data-testid="stSidebar"] {background:#101b2d}
.block-container {padding-top:1.2rem;max-width:1600px}
.metric-card {background:linear-gradient(145deg,#15243a,#101b2d);border:1px solid #263b56;border-radius:14px;padding:16px 18px;min-height:112px}
.metric-label {font-size:12px;color:#9fb2c9;text-transform:uppercase;letter-spacing:.08em}
.metric-value {font-size:27px;font-weight:700;color:#f3f7fc;margin-top:7px}
.metric-note {font-size:11px;color:#8fa4bd;margin-top:3px}
.section-title {font-size:19px;font-weight:700;color:#e8eef7;margin:12px 0}
.small-muted {color:#9fb2c9;font-size:12px}
div[data-testid="stMetric"] {background:#15243a;border:1px solid #263b56;padding:12px;border-radius:12px}
</style>
""", unsafe_allow_html=True)

def card(label, value, note=""):
    st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>', unsafe_allow_html=True)

def explain(title, source, method, formula="Not applicable"):
    with st.expander(f"How is {title} obtained?"):
        st.write(f"**Source:** {source}")
        st.write(f"**Method:** {method}")
        st.code(formula)

with st.sidebar:
    st.markdown("## 🛰️ WiTrac")
    st.caption("WILDLIFE TELEMETRY PLATFORM")
    page = st.radio("NAVIGATION", ["Overview", "GPS Tracking", "Environment", "Movement", "Energy Management", "LoRa Analytics", "Historical Data"])
    st.divider()
    mode = st.selectbox("Operating mode", ["Simulation", "Hardware (serial JSON)"])
    scenario = st.selectbox("Simulation scenario", ["Daylight", "Cloudy", "Night", "Poor LoRa"])
    activity = st.selectbox("Movement scenario", ["Intermittent movement", "Resting", "Movement"])
    seed = st.number_input("Simulation seed", min_value=0, max_value=999999, value=42, step=1)
    st.caption("Demo coordinates are fictional test waypoints near Chennai. They do not represent a real tortoise.")

st.markdown("# WiTrac")
st.markdown("**Wildlife Telemetry & Energy Intelligence**  ·  Indian Star Tortoise demonstration tag")
st.warning("SIMULATION MODE — all readings, route points and packet events are generated demonstration data, not live animal telemetry.", icon="⚠️")

# Hardware mode deliberately requires a user-supplied gateway schema/port and never silently falls back.
if mode == "Hardware (serial JSON)":
    st.info("Hardware adapter is provided in hardware.py. Connect a Raspberry Pi gateway that emits the documented JSON-lines schema.")
    port = st.text_input("Serial port", value="COM3" if st.session_state.get("is_windows", True) else "/dev/ttyUSB0")
    baud = st.number_input("Baud rate", min_value=1200, max_value=921600, value=115200, step=1200)
    if st.button("Read gateway data"):
        try:
            from hardware import read_serial_records
            records = read_serial_records(port, int(baud))
            if records:
                st.session_state["hardware_records"] = records
                st.success(f"Received {len(records)} gateway records.")
            else:
                st.error("No valid JSON telemetry records received.")
        except Exception as e:
            st.error(f"Hardware connection failed: {e}")
    records = st.session_state.get("hardware_records", [])
    if not records:
        st.stop()
    df = pd.DataFrame(records)
    required = ["timestamp","latitude","longitude","temperature_c","humidity_pct","battery_v","rssi_dbm","snr_db"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        st.error("Missing required fields in gateway records: " + ", ".join(missing))
        st.stop()
    for c in ["timestamp"]:
        if c in df.columns: df[c] = pd.to_datetime(df[c], errors="coerce")
    latest = df.iloc[-1]
    stats = {"tx": int(latest.get("tx_total",0)), "rx": int(latest.get("rx_total",0))}
    stats["pdr"], stats["loss"] = packet_metrics(stats["tx"], stats["rx"])
    stats["latency_ms"] = latest.get("latency_ms", None)
    data_label = "HARDWARE DATA"
else:
    df, stats = generate_demo_data(scenario=scenario, activity=activity, seed=int(seed))
    latest = df.iloc[-1]
    data_label = "SIMULATED DATA"

st.caption(f"Tag: **{SETTINGS.tag_id}**  ·  Species: **{SETTINGS.species}**  ·  Source: **{data_label}**  ·  Updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")

if page == "Overview":
    st.markdown('<div class="section-title">System overview</div>', unsafe_allow_html=True)
    cols = st.columns(4)
    vals = [
        ("GPS FIX", "SIMULATED FIX" if mode=="Simulation" else str(latest.get("gps_fix","FIX STATUS UNKNOWN")), f"{int(latest.get('satellites',0))} satellites"),
        ("TEMPERATURE", f"{latest.get('temperature_c',float('nan')):.1f} °C", "DHT22"),
        ("HUMIDITY", f"{latest.get('humidity_pct',float('nan')):.1f} %", "DHT22"),
        ("BATTERY VOLTAGE", f"{latest.get('battery_v',float('nan')):.3f} V", "Li-ion terminal voltage"),
        ("SOLAR INPUT", f"{latest.get('solar_input_v',float('nan')):.3f} V" if pd.notna(latest.get('solar_input_v',np.nan)) else "N/A", "BQ25570 input node; voltage only"),
        ("ACCELERATION", f"{latest.get('accel_magnitude_g',np.nan):.3f} g" if "accel_magnitude_g" in latest else "3-axis data", "ADXL345 magnitude"),
        ("LORA RSSI", f"{latest.get('rssi_dbm',np.nan):.1f} dBm", "SX1278 receiver metadata"),
        ("PACKET DELIVERY", f"{stats['pdr']:.1f} %" if stats.get("pdr") is not None else "N/A", f"{stats['rx']} received / {stats['tx']} transmitted"),
    ]
    for c,(label,value,note) in zip(cols*2, vals): 
        with c: card(label,value,note)
    st.markdown('<div class="section-title">Demonstration tracking route</div>', unsafe_allow_html=True)
    m = folium.Map(location=[float(latest["latitude"]),float(latest["longitude"])], zoom_start=15, tiles="OpenStreetMap")
    coords = df[["latitude","longitude"]].dropna().values.tolist()
    if coords:
        folium.PolyLine(coords, color="#16c7a0", weight=4, opacity=.85, tooltip="Simulated route").add_to(m)
        folium.Marker(coords[-1], tooltip="Latest simulated position", popup=SETTINGS.species, icon=folium.Icon(color="green")).add_to(m)
    st_folium(m, height=390, use_container_width=True)
    st.caption("The map uses fictional demonstration waypoints. Do not interpret it as a real animal location.")

elif page == "GPS Tracking":
    st.subheader("GPS tracking · NEO-6M")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Latitude", f"{latest['latitude']:.6f}°")
    c2.metric("Longitude", f"{latest['longitude']:.6f}°")
    c3.metric("Speed", f"{latest.get('gps_speed_kmh',0):.2f} km/h")
    c4.metric("Satellites", str(latest.get("satellites","N/A")))
    st.metric("HDOP", f"{latest.get('hdop',float('nan')):.2f}" if pd.notna(latest.get("hdop",np.nan)) else "N/A")
    m = folium.Map(location=[float(latest["latitude"]),float(latest["longitude"])], zoom_start=15)
    coords = df[["latitude","longitude"]].dropna().values.tolist()
    folium.PolyLine(coords,color="#16c7a0",weight=4).add_to(m)
    folium.Marker(coords[-1],tooltip="Latest position").add_to(m)
    st_folium(m,height=480,use_container_width=True)
    explain("GPS speed","NEO-6M GPS speed field, or successive valid positions","Distance between consecutive positions divided by elapsed time","Speed (km/h) = Haversine distance (m) / Δt (s) × 3.6")
    explain("HDOP","NEO-6M navigation output","Horizontal dilution of precision; dimensionless quality indicator","Direct GPS-reported HDOP; lower generally indicates better geometry")

elif page == "Environment":
    st.subheader("Environmental monitoring · DHT22")
    a,b = st.columns(2)
    a.metric("Temperature", f"{latest['temperature_c']:.1f} °C")
    b.metric("Relative humidity", f"{latest['humidity_pct']:.1f} %")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.timestamp,y=df.temperature_c,name="Temperature (°C)",line=dict(width=2)))
    fig.add_trace(go.Scatter(x=df.timestamp,y=df.humidity_pct,name="Humidity (%)",yaxis="y2",line=dict(width=2)))
    fig.update_layout(template="plotly_dark",height=420,yaxis=dict(title="Temperature (°C)"),yaxis2=dict(title="Humidity (%)",overlaying="y",side="right"),legend=dict(orientation="h"))
    st.plotly_chart(fig,use_container_width=True)
    explain("Temperature","DHT22","Direct sensor measurement; simulated profile in demo mode","No derived formula")
    explain("Relative humidity","DHT22","Direct sensor measurement","No derived formula")

elif page == "Movement":
    st.subheader("Movement monitoring · ADXL345")
    st.caption("Acceleration axes are shown in g. The magnitude includes gravity; movement classification uses variation around the window mean.")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("X acceleration",f"{latest['ax_g']:.3f} g")
    c2.metric("Y acceleration",f"{latest['ay_g']:.3f} g")
    c3.metric("Z acceleration",f"{latest['az_g']:.3f} g")
    c4.metric("Magnitude",f"{latest['accel_magnitude_g']:.3f} g")
    window = df[["ax_g","ay_g","az_g"]].tail(SETTINGS.movement_window_samples).to_numpy()
    centered = window - window.mean(axis=0) if len(window) > 1 else window
    dynamic_rms = float(np.sqrt(np.mean(np.sum(centered**2, axis=1)))) if len(window) else 0.0
    movement_state = "MOVEMENT DETECTED" if dynamic_rms >= SETTINGS.movement_delta_threshold_g else "LOW MOVEMENT"
    st.metric("Windowed movement indicator", movement_state, f"Dynamic RMS: {dynamic_rms:.3f} g · threshold: {SETTINGS.movement_delta_threshold_g:.2f} g")
    axes = go.Figure()
    for col in ["ax_g","ay_g","az_g"]:
        axes.add_trace(go.Scatter(x=df.timestamp,y=df[col],name=col))
    axes.update_layout(template="plotly_dark",height=350,title="Three-axis acceleration")
    st.plotly_chart(axes,use_container_width=True)
    mag = go.Figure(go.Scatter(x=df.timestamp,y=df.accel_magnitude_g,name="Magnitude"))
    mag.update_layout(template="plotly_dark",height=280,title="Acceleration magnitude")
    st.plotly_chart(mag,use_container_width=True)
    st.info("Movement classification should be calibrated using stationary and controlled-movement recordings from the actual tag. The demo scenario is illustrative.")
    explain("Acceleration magnitude","ADXL345 X/Y/Z axes","Euclidean magnitude of the three acceleration components","a = √(ax² + ay² + az²)")
    explain("Movement state","ADXL345 time-window samples","RMS variation around each axis' window mean compared with a calibrated threshold","RMSdynamic = √mean(Σ(axis − window_mean)²)")

elif page == "Energy Management":
    st.subheader("Solar and battery management · BQ25570 + Li-ion")
    a,b,c = st.columns(3)
    a.metric("Solar input voltage",f"{latest.get('solar_input_v',np.nan):.3f} V" if pd.notna(latest.get("solar_input_v",np.nan)) else "N/A")
    b.metric("Battery voltage",f"{latest['battery_v']:.3f} V")
    v_ok = latest.get("vbat_ok",None)
    c.metric("Battery-good signal",str(v_ok).upper() if v_ok is not None else "NOT PROVIDED")
    st.warning("Battery voltage is not a state-of-charge percentage. Battery thresholds below are example configuration values and must be replaced with the selected cell's datasheet limits and the BQ25570 VBAT_OK configuration.")
    status = battery_status(float(latest["battery_v"]), SETTINGS.battery_low_v, SETTINGS.battery_good_v, SETTINGS.battery_high_v)
    st.metric("Configured voltage status",status)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.timestamp,y=df.solar_input_v,name="Solar input voltage (V)"))
    fig.add_trace(go.Scatter(x=df.timestamp,y=df.battery_v,name="Li-ion battery voltage (V)"))
    fig.update_layout(template="plotly_dark",height=390,title="Energy voltage history",yaxis_title="Voltage (V)")
    st.plotly_chart(fig,use_container_width=True)
    explain("Solar input voltage","Voltage measured at the configured BQ25570 input node","Direct voltage measurement; node must be explicitly identified in hardware","Vnode = calibrated ADC voltage × divider ratio")
    explain("Battery voltage","Li-ion battery terminal measurement","ADC measurement corrected for divider ratio and ADC calibration","Vbattery = Vadc × (R1 + R2) / R2")
    explain("Battery-good status","BQ25570 VBAT_OK pin","Digital status according to the IC configuration and external threshold resistors","Read the configured logic level; do not infer an arbitrary percentage")

elif page == "LoRa Analytics":
    st.subheader("LoRa communication · SX1278")
    a,b,c,d = st.columns(4)
    a.metric("RSSI",f"{latest['rssi_dbm']:.1f} dBm")
    b.metric("SNR",f"{latest['snr_db']:.1f} dB")
    c.metric("Transmitted",str(stats["tx"]))
    d.metric("Received",str(stats["rx"]))
    e,f,g = st.columns(3)
    e.metric("Packet delivery ratio",f"{stats['pdr']:.1f} %" if stats["pdr"] is not None else "N/A")
    f.metric("Packet loss",f"{stats['loss']:.1f} %" if stats["loss"] is not None else "N/A")
    g.metric("Mean latency",f"{stats['latency_ms']:.1f} ms" if stats["latency_ms"] is not None else "N/A")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.timestamp,y=df.rssi_dbm,name="RSSI (dBm)"))
    fig.add_trace(go.Scatter(x=df.timestamp,y=df.snr_db,name="SNR (dB)",yaxis="y2"))
    fig.update_layout(template="plotly_dark",height=400,yaxis=dict(title="RSSI (dBm)"),yaxis2=dict(title="SNR (dB)",overlaying="y",side="right"))
    st.plotly_chart(fig,use_container_width=True)
    explain("Packet delivery ratio","Gateway packet sequence accounting","Received unique sequence numbers divided by transmitted sequence numbers in the same window","PDR (%) = received / transmitted × 100")
    explain("Packet loss","Gateway packet sequence accounting","Transmitted packets minus received packets, divided by transmitted packets","Loss (%) = (transmitted − received) / transmitted × 100")
    explain("Latency","Synchronized transmit and receive timestamps","Receive timestamp minus transmit timestamp for each successfully received packet","Latency (ms) = (t_receive − t_transmit) × 1000")

elif page == "Historical Data":
    st.subheader("Historical telemetry and export")
    start = st.date_input("Start date", value=df.timestamp.min().date())
    end = st.date_input("End date", value=df.timestamp.max().date())
    filtered = df[(df.timestamp.dt.date >= start) & (df.timestamp.dt.date <= end)]
    if filtered.empty:
        st.info("No records in selected date range.")
    else:
        options = ["temperature_c","humidity_pct","ax_g","ay_g","az_g","solar_input_v","battery_v","rssi_dbm","snr_db"]
        selected = st.multiselect("Select parameters",options,default=["temperature_c","battery_v","rssi_dbm"])
        if selected:
            long = filtered.melt(id_vars="timestamp",value_vars=selected,var_name="parameter",value_name="value")
            fig = px.line(long,x="timestamp",y="value",color="parameter",template="plotly_dark",height=420)
            st.plotly_chart(fig,use_container_width=True)
        st.dataframe(filtered, use_container_width=True, hide_index=True)
        st.download_button("Download filtered CSV",filtered.to_csv(index=False).encode("utf-8"),"witrac_telemetry.csv","text/csv")

st.divider()
st.caption("WiTrac prototype dashboard · Sensor readings and calculations must be validated against the actual assembled hardware before field deployment.")
