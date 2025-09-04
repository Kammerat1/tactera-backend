# tactera_backend/core/training_intensity.py

"""
Training intensity configuration and helpers.

Current base balance (can be tweaked later):
- Light:  XP ×0.75, Energy −10
- Normal: XP ×1.00, Energy −15
- Hard:   XP ×1.25, Energy −25

Energy modifiers for physio staff/facilities will be added later.
"""

from typing import Literal

Intensity = Literal["light", "normal", "hard"]

# Base multipliers/drains for now (no physio modifiers yet)
XP_MULTIPLIER = {
    "light": 0.75,
    "normal": 1.00,
    "hard": 1.25,
}

BASE_ENERGY_DRAIN = {
    "light": 10,
    "normal": 15,
    "hard": 25,
}

ALLOWED_INTENSITIES = set(XP_MULTIPLIER.keys())


def get_xp_multiplier(intensity: str) -> float:
    """Return the XP multiplier for the given intensity (defaults to normal)."""
    intensity = (intensity or "normal").lower()
    return XP_MULTIPLIER.get(intensity, 1.0)


def calculate_energy_drain(
    intensity: str,
    physio_staff_level: int = 0,
    physio_facility_level: int = 0,
) -> int:
    """
    Compute energy drain for a training session.
    For now, only base drain applies.
    Later, reduce drain based on staff/facility levels.
    """
    intensity = (intensity or "normal").lower()
    base = BASE_ENERGY_DRAIN.get(intensity, BASE_ENERGY_DRAIN["normal"])

    # TODO: when physio systems exist, reduce base e.g.:
    # staff_bonus = min(physio_staff_level, 3)  # cap effect
    # facility_bonus = min(physio_facility_level, 3)
    # reduction = staff_bonus + facility_bonus
    # return max(0, base - reduction)

    return base
