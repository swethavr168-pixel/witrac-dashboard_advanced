"""Optional serial JSON adapter for a Raspberry Pi/ESP32 gateway.

Expected one JSON object per line, e.g.:
{"timestamp":"2026-10-30T10:00:00Z","tag_id":"WTR-IST-001",
 "latitude":13.08,"longitude":80.27,"gps_speed_kmh":0.2,"satellites":8,"hdop":1.1,
 "temperature_c":29.2,"humidity_pct":60.1,"ax_g":0.01,"ay_g":-0.02,"az_g":1.00,
 "solar_input_v":1.2,"battery_v":3.85,"vbat_ok":true,
 "rssi_dbm":-92,"snr_db":8.5,"tx_total":120,"rx_total":116,
 "tx_timestamp_ms":123456,"rx_timestamp_ms":123700}
Only include fields actually measured or computed by the gateway. Never fabricate missing fields.
"""
import json
import serial

def read_serial_records(port, baudrate=115200, timeout=2, max_lines=100):
    records = []
    with serial.Serial(port, baudrate=baudrate, timeout=timeout) as ser:
        for _ in range(max_lines):
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    records.append(obj)
            except json.JSONDecodeError:
                continue
    return records
