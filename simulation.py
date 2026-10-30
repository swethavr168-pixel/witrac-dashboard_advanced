"""Deterministic, scenario-driven demonstration data. All records are labelled simulated."""
import math, time
import numpy as np
import pandas as pd
from calculations import haversine_m, speed_kmh, acceleration_magnitude_g, packet_metrics, mean_latency_ms
from config import SETTINGS

def _route_point(i, route):
    # Smooth interpolation between adjacent predefined waypoints.
    if len(route) < 2:
        return route[0]
    progress = (i * 0.035) % (len(route)-1)
    segment = min(int(progress), len(route)-2)
    frac = progress - segment
    a, b = route[segment], route[segment+1]
    return (a[0] + (b[0]-a[0])*frac, a[1] + (b[1]-a[1])*frac)

def generate_demo_data(n=180, scenario="Daylight", activity="Intermittent movement", seed=42):
    rng = np.random.default_rng(seed)
    now = pd.Timestamp.now().floor("s")
    rows, tx_times, rx_times = [], {}, {}
    route = SETTINGS.route
    prev = None
    tx_total = rx_total = 0
    for i in range(n):
        ts = now - pd.Timedelta(seconds=(n-1-i)*10)
        # Solar input voltage is an illustrative measured-node voltage model, not solar power.
        phase = (i / max(n-1, 1))
        daylight = max(0.0, math.sin(math.pi * phase))
        if scenario == "Night":
            solar_v = max(0.0, 0.025 + rng.normal(0, 0.008))
        elif scenario == "Cloudy":
            solar_v = max(0.0, 0.65 + 0.25*daylight + rng.normal(0, 0.035))
        else:
            solar_v = max(0.0, 1.15 + 0.45*daylight + rng.normal(0, 0.04))
        # Battery voltage is a bounded illustrative state trajectory, not an SOC estimate.
        if scenario == "Night":
            battery_v = 3.78 - 0.18*phase + 0.008*math.sin(i/18)
        else:
            battery_v = 3.68 + 0.16*phase + 0.012*math.sin(i/15)
        battery_v = float(np.clip(battery_v, 3.35, 4.15))
        temperature = 29.0 + 1.6*math.sin(i/35) + rng.normal(0, 0.12)
        humidity = 58.0 - 5.0*math.sin(i/42) + rng.normal(0, 0.45)
        is_moving = activity == "Movement" or (activity == "Intermittent movement" and (i//18)%3 == 1)
        if activity == "Resting":
            is_moving = False
        # ADXL345 axes in g: gravity vector plus small dynamic variation.
        ax = rng.normal(0.02, 0.025 if is_moving else 0.008)
        ay = rng.normal(-0.01, 0.025 if is_moving else 0.008)
        az = 1.0 + rng.normal(0, 0.035 if is_moving else 0.008)
        mag = acceleration_magnitude_g(ax, ay, az)
        lat, lon = _route_point(i, route)
        gps_speed = 0.0 if prev is None or not is_moving else (speed_kmh(*prev, lat, lon, 10) or 0.0)
        prev = (lat, lon)
        satellites = int(rng.integers(6, 11))
        hdop = round(float(rng.uniform(0.8, 2.0)), 2)
        if scenario == "Poor LoRa":
            rssi = float(rng.normal(-116, 3.5)); snr = float(rng.normal(-6, 2))
            receive_prob = 0.72
        else:
            rssi = float(rng.normal(-94, 3.0)); snr = float(rng.normal(7, 1.8))
            receive_prob = 0.97
        tx_total += 1
        seq = i + 1
        tx_times[seq] = ts.timestamp()
        received = rng.random() < receive_prob
        if received:
            rx_total += 1
            latency_s = float(rng.uniform(0.12, 0.85))
            rx_times[seq] = ts.timestamp() + latency_s
        rows.append({
            "timestamp": ts, "latitude": lat, "longitude": lon, "gps_speed_kmh": gps_speed,
            "satellites": satellites, "hdop": hdop, "temperature_c": temperature,
            "humidity_pct": humidity, "ax_g": ax, "ay_g": ay, "az_g": az,
            "accel_magnitude_g": mag, "solar_input_v": solar_v, "battery_v": battery_v,
            "rssi_dbm": rssi, "snr_db": snr, "tx_total": tx_total, "rx_total": rx_total,
            "packet_received": received,
        })
    df = pd.DataFrame(rows)
    pdr, loss = packet_metrics(tx_total, rx_total)
    latencies = [ (rx_times[k]-tx_times[k])*1000 for k in rx_times if k in tx_times ]
    avg_latency = float(np.mean(latencies)) if latencies else None
    return df, {"tx": tx_total, "rx": rx_total, "pdr": pdr, "loss": loss, "latency_ms": avg_latency}

def live_demo_stream(scenario, activity, seed=42, n=180):
    return generate_demo_data(n=n, scenario=scenario, activity=activity, seed=seed)
