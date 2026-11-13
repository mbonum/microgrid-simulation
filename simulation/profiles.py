"""Simple synthetic load/generation profiles (no external data needed)."""
from __future__ import annotations

import math


def solar_profile(hour: float, peak_kw: float = 5.0) -> float:
    """Approximate solar generation curve peaking at noon."""
    if hour < 6 or hour > 20:
        return 0.0
    angle = math.pi * (hour - 6) / 14
    return peak_kw * math.sin(angle) ** 2


def residential_load(hour: float, base_kw: float = 0.3) -> float:
    """Rough residential consumption with morning and evening peaks."""
    morning = 0.5 * math.exp(-0.5 * ((hour - 7.5) / 1.0) ** 2)
    evening = 1.0 * math.exp(-0.5 * ((hour - 19.5) / 1.5) ** 2)
    return base_kw + morning + evening


def commercial_load(hour: float, base_kw: float = 1.0) -> float:
    """Flat business-hours load profile."""
    if 8 <= hour <= 18:
        return base_kw * 1.5
    return base_kw * 0.4
