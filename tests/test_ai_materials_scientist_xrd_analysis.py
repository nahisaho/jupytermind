"""Tests for the XRD peak detection and d-spacing module (DES-AIMS-090 / REQ-AIMS-090)."""

from __future__ import annotations

import numpy as np
import pytest


def _reference_fixture() -> dict:
    two_theta = np.linspace(10, 80, 3500)
    sigma = 0.1
    centers = [28.42, 47.27, 56.09]
    intensity = sum(np.exp(-0.5 * ((two_theta - c) / sigma) ** 2) for c in centers)
    return {
        "two_theta": two_theta.tolist(),
        "intensity": intensity.tolist(),
        "wavelength": 1.5406,
        "height": 0.5,
        "distance": 50,
    }


# @id TEST-AIMS-993
# @verifies REQ-AIMS-090
def test_TEST_AIMS_993_detects_three_peaks_and_matches_bragg_d_spacings():
    from ai_materials_scientist.xrd_analysis import index_xrd_peaks

    result = index_xrd_peaks(**_reference_fixture())

    expected_angles = [28.42526436124607, 47.27064875678766, 56.09316947699343]
    expected_d_spacings = [3.137408344884631, 1.9213600835334028, 1.6382763480941835]

    assert result["peak_angles"] == pytest.approx(expected_angles, abs=1e-6)
    assert result["d_spacings"] == pytest.approx(expected_d_spacings, abs=1e-6)


# @id TEST-AIMS-994
# @verifies REQ-AIMS-090
def test_TEST_AIMS_994_rejects_mismatched_lengths():
    from ai_materials_scientist.xrd_analysis import index_xrd_peaks

    with pytest.raises(ValueError, match="two_theta"):
        index_xrd_peaks(two_theta=[10.0, 20.0, 30.0], intensity=[1.0, 2.0])


# @id TEST-AIMS-995
# @verifies REQ-AIMS-090
def test_TEST_AIMS_995_rejects_fewer_than_three_entries():
    from ai_materials_scientist.xrd_analysis import index_xrd_peaks

    with pytest.raises(ValueError, match="two_theta"):
        index_xrd_peaks(two_theta=[10.0, 20.0], intensity=[1.0, 2.0])


# @id TEST-AIMS-996
# @verifies REQ-AIMS-090
def test_TEST_AIMS_996_rejects_non_ascending_two_theta():
    from ai_materials_scientist.xrd_analysis import index_xrd_peaks

    with pytest.raises(ValueError, match="must be ascending"):
        index_xrd_peaks(two_theta=[10.0, 30.0, 20.0], intensity=[1.0, 2.0, 1.0])


# @id TEST-AIMS-997
# @verifies REQ-AIMS-090
def test_TEST_AIMS_997_rejects_two_theta_outside_open_interval():
    from ai_materials_scientist.xrd_analysis import index_xrd_peaks

    with pytest.raises(ValueError, match="two_theta"):
        index_xrd_peaks(two_theta=[0.0, 10.0, 20.0], intensity=[1.0, 2.0, 1.0])

    with pytest.raises(ValueError, match="two_theta"):
        index_xrd_peaks(two_theta=[10.0, 20.0, 180.0], intensity=[1.0, 2.0, 1.0])


# @id TEST-AIMS-998
# @verifies REQ-AIMS-090
def test_TEST_AIMS_998_rejects_negative_intensity():
    from ai_materials_scientist.xrd_analysis import index_xrd_peaks

    with pytest.raises(ValueError, match="must be non-negative"):
        index_xrd_peaks(two_theta=[10.0, 20.0, 30.0], intensity=[1.0, -2.0, 1.0])


# @id TEST-AIMS-999
# @verifies REQ-AIMS-090
def test_TEST_AIMS_999_rejects_non_positive_wavelength():
    from ai_materials_scientist.xrd_analysis import index_xrd_peaks

    with pytest.raises(ValueError, match="must be positive"):
        index_xrd_peaks(two_theta=[10.0, 20.0, 30.0], intensity=[1.0, 2.0, 1.0], wavelength=0)
