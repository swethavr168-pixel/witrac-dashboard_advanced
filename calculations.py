"""Transparent calculations used by WiTrac. No arbitrary KPI values."""
import math
import numpy as np

def haversine_m(lat1, lon1, lat2, lon2):
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*r*math.asin(math.sqrt(a))

def speed_kmh(lat1, lon1, lat2, lon2, dt_s):
    if dt_s <= 0:
        return None
    return haversine_m(lat1, lon1, lat2, lon2) / dt_s * 3.6

def acceleration_magnitude_g(ax, ay, az):
    return math.sqrt(ax*ax + ay*ay + az*az)

def dynamic_acceleration_rms_g(samples):
    """RMS variation around the window mean; input rows are (ax, ay, az) in g."""
    a = np.asarray(samples, dtype=float)
    if len(a) < 2:
        return 0.0
    centered = a - a.mean(axis=0)
    return float(np.sqrt(np.mean(np.sum(centered**2, axis=1))))

def classify_movement(samples, threshold_g):
    rms = dynamic_acceleration_rms_g(samples)
    return ("MOVEMENT DETECTED" if rms >= threshold_g else "LOW MOVEMENT", rms)

def packet_metrics(tx_count, rx_count):
    if tx_count <= 0:
        return None, None
    received = min(max(int(rx_count), 0), int(tx_count))
    pdr = received / tx_count * 100.0
    return pdr, 100.0 - pdr

def mean_latency_ms(tx_times, rx_times):
    vals = []
    for seq, rx in rx_times.items():
        if seq in tx_times and rx >= tx_times[seq]:
            vals.append((rx - tx_times[seq]) * 1000.0)
    return float(np.mean(vals)) if vals else None

def adc_voltage(adc_v, divider_ratio):
    return adc_v * divider_ratio

def battery_status(voltage, low_v, good_v, high_v):
    if voltage is None:
        return "UNKNOWN"
    if voltage < low_v:
        return "LOW"
    if voltage < good_v:
        return "BATTERY GOOD NOT ASSERTED"
    if voltage <= high_v:
        return "WITHIN CONFIGURED RANGE"
    return "CHECK CONFIGURATION / OVERVOLTAGE"

def safe_ratio(numerator, denominator):
    return numerator / denominator if denominator else None
