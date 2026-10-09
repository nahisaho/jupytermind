"""XRD peak detection and Bragg's-law d-spacing module (DES-AIMS-090 / REQ-AIMS-090)."""

from __future__ import annotations

import math

from scipy.signal import find_peaks


def _validate(two_theta, intensity, wavelength) -> None:
    if len(two_theta) != len(intensity):
        raise ValueError("two_theta/intensity: must be equal-length lists")
    if len(two_theta) < 3:
        raise ValueError("two_theta/intensity: must have at least 3 entries")
    for value in two_theta:
        if not math.isfinite(value) or not (0 < value < 180):
            raise ValueError("two_theta: must be finite degrees within the open interval (0, 180)")
    for earlier, later in zip(two_theta, two_theta[1:]):
        if not later > earlier:
            raise ValueError("two_theta: must be ascending")
    for value in intensity:
        if not math.isfinite(value) or value < 0:
            raise ValueError("intensity: must be non-negative")
    if not (math.isfinite(wavelength) and wavelength > 0):
        raise ValueError("wavelength: must be positive")


# @id CODE-AIMS-917
# @implements REQ-AIMS-090
# @design DES-AIMS-090
def index_xrd_peaks(
    two_theta,
    intensity,
    wavelength: float = 1.5406,
    height=None,
    distance=1,
) -> dict[str, list[float]]:
    """Detect XRD peaks and compute their Bragg-law d-spacings."""
    _validate(two_theta, intensity, wavelength)

    peak_indices, _ = find_peaks(intensity, height=height, distance=distance)

    peak_angles = [two_theta[index] for index in peak_indices]
    d_spacings = [wavelength / (2 * math.sin(math.radians(angle / 2))) for angle in peak_angles]

    return {"peak_angles": peak_angles, "d_spacings": d_spacings}
