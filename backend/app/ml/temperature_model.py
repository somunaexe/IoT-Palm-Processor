"""Heuristic optimal-temperature advisor for palm fruit sterilization.

Fresh fruit bunches (FFB) are sterilized with saturated steam before
digestion/pressing. Two things drive what "optimal temperature" means here:

1. The chamber has to run on *saturated* steam. For saturated steam,
   temperature and pressure are locked together by the steam tables - if a
   measured temperature drifts far from the saturation point implied by the
   measured pressure, the steam is either superheated (poor heat transfer,
   so the lipase enzyme isn't fully deactivated despite a "hot" reading) or
   carrying trapped air (effective heating is lower than the thermometer
   suggests). So pressure, not the temperature reading itself, is what tells
   us the physically correct target.
2. Industry practice keeps FFB sterilization in roughly 125-145 degC. Below
   that, lipase survives and free fatty acid keeps climbing after harvest,
   degrading oil quality; above it, energy is wasted and the mesocarp is
   overcooked.

There's no labelled outcome data (oil yield / FFA level) to fit a regression
against yet, so this encodes the above as a rule-based estimate. It's kept as
a pure function so it can be swapped for a trained model later without
touching the service layer that calls it.
"""

import numpy as np

MIN_SAFE_TEMP_C = 125.0
MAX_SAFE_TEMP_C = 145.0

# Saturated steam table: gauge pressure (psi) -> saturation temperature (degC).
# Covers the ~20-80 psi range this line's pressure sensor reports, which is
# where the 125-145 degC sterilization window actually falls.
_PRESSURE_PSI = np.array([0, 10, 20, 30, 40, 50, 60, 80])
_SATURATION_TEMP_C = np.array([100.0, 115.2, 126.3, 134.4, 141.5, 147.6, 153.1, 162.6])

# Vibration stands in for digester/stripper mechanical load. A heavily loaded,
# more agitated batch mixes less evenly, so the target is nudged up to
# compensate for uneven heat penetration; a calm reading gets a small
# downward nudge since a gentler, better-mixed load needs less margin.
_VIBRATION_BASELINE = 1.5
_VIBRATION_GAIN_C = 2.0


def saturation_temperature(pressure_psi: float) -> float:
    """Ideal saturated-steam temperature for a given chamber pressure."""
    return float(np.interp(pressure_psi, _PRESSURE_PSI, _SATURATION_TEMP_C))


def recommend_optimal_temperature(pressure: float, vibration: float) -> float:
    """Recommended sterilizer temperature (degC) for these sensor readings."""
    target = saturation_temperature(pressure)
    target += (vibration - _VIBRATION_BASELINE) * _VIBRATION_GAIN_C

    return round(float(np.clip(target, MIN_SAFE_TEMP_C, MAX_SAFE_TEMP_C)), 2)


def recommend_action(current_temperature: float, optimal_temperature: float, tolerance: float = 2.0) -> str:
    """Compare a live temperature reading against the recommendation."""
    delta = current_temperature - optimal_temperature

    if delta < -tolerance:
        return "INCREASE_HEAT"
    if delta > tolerance:
        return "DECREASE_HEAT"
    return "MAINTAIN"
