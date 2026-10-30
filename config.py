"""WiTrac configuration. Replace hardware pins, calibration and thresholds with measured values."""
from dataclasses import dataclass

@dataclass
class Settings:
    tag_id: str = "WTR-IST-001"
    species: str = "Indian Star Tortoise"
    # Demonstration route only. These are fictional test coordinates, not a real animal location.
    route: tuple = (
        (13.0827, 80.2707), (13.0832, 80.2714), (13.0840, 80.2720),
        (13.0847, 80.2728), (13.0854, 80.2733), (13.0860, 80.2741),
        (13.0866, 80.2750), (13.0872, 80.2756), (13.0878, 80.2763),
        (13.0884, 80.2770), (13.0890, 80.2776), (13.0896, 80.2782),
    )
    # Example values ONLY: replace with the actual battery datasheet and BQ25570 resistor settings.
    battery_low_v: float = 3.40
    battery_good_v: float = 3.60
    battery_high_v: float = 4.20
    # Set to the real divider ratio R1/R2 only after measuring the hardware.
    adc_divider_ratio: float = 2.0
    adc_reference_v: float = 3.3
    # Set actual calibrated movement threshold after collecting stationary/moving data.
    movement_delta_threshold_g: float = 0.12
    movement_window_samples: int = 8
    # Set this to the configured BQ25570 VBAT_OK pin logic and polarity.
    vbat_ok_active_high: bool = True

SETTINGS = Settings()
