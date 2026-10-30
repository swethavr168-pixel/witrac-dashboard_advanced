# WiTrac Advanced Dashboard

A Streamlit dashboard for the Indian Star Tortoise demonstration tag. It supports deterministic simulation and an optional serial JSON gateway adapter.

## Run locally
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Modes
- **Simulation:** deterministic scenario-driven demonstration values. The route is fictional and labelled as simulated.
- **Hardware:** reads JSON Lines from a serial-connected gateway. See `hardware.py` for the expected schema. Missing fields are not silently invented.

## Before hardware use
1. Confirm exact solar measurement node and ADC front-end.
2. Measure/record battery type, cell count, capacity and permitted voltage range from the cell datasheet.
3. Set BQ25570 VBAT_OK resistor thresholds and output polarity to match the actual circuit.
4. Calibrate ESP32 ADC and voltage-divider ratio using a multimeter.
5. Calibrate ADXL345 offsets, scale and movement threshold from stationary and controlled-motion data.
6. Confirm NEO-6M GPS output fields and fix validity.
7. Confirm LoRa packet sequence accounting, transmit/receive timestamps and clock synchronization.
8. Ensure all hardware records include units and timestamps.

## Engineering limitations
- Voltage alone is not a reliable battery state-of-charge percentage.
- Solar power requires voltage and current; this dashboard intentionally does not invent current or watts.
- Energy requires integrating measured power over time.
- RSSI and SNR must come from received packet metadata.
- Packet delivery ratio requires matching transmit/receive sequence accounting over the same window.
- Movement classification is a simple calibrated activity indicator, not species-specific behaviour recognition.
- GPS route coordinates are fictional demo waypoints near Chennai, not a real tortoise location.
