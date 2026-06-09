"""Verifies FACE_NAMES match WCA Megaminx convention using geometry."""
import numpy as np
import pytest
from megaminx.moves import FACE_NAMES, _face_centers, _FACE_INDEX


def c(name: str) -> np.ndarray:
    return _face_centers[_FACE_INDEX[name]]


def test_all_12_wca_names_present():
    expected = {"U", "D", "F", "B", "R", "L", "UL", "UR", "BL", "BR", "DL", "DR"}
    assert set(FACE_NAMES) == expected, (
        f"Wrong names: {set(FACE_NAMES) - expected} present, {expected - set(FACE_NAMES)} missing"
    )


def test_u_highest_y():
    assert _FACE_INDEX["U"] == 0
    assert c("U")[1] == max(fc[1] for fc in _face_centers)


def test_d_lowest_y():
    assert _FACE_INDEX["D"] == 11
    assert c("D")[1] == min(fc[1] for fc in _face_centers)


def test_f_is_frontmost_of_u_ring():
    """F: adjacent to U, most negative z (toward solver)."""
    assert c("F")[2] < 0


def test_r_is_right_side():
    """R: x- direction (solver's right), z≈0."""
    assert c("R")[0] < -1.0


def test_l_is_left_side():
    """L: x+ direction (solver's left), z≈0."""
    assert c("L")[0] > 1.0


def test_ul_is_back_left():
    """UL: U-adjacent, back (z+) and left (x+)."""
    assert c("UL")[2] > 1.0
    assert c("UL")[0] > 0


def test_ur_is_back_right():
    """UR: U-adjacent, back (z+) and right (x-)."""
    assert c("UR")[2] > 1.0
    assert c("UR")[0] < 0


def test_b_is_backmost_of_d_ring():
    """B: opposite of F, most positive z."""
    assert c("B")[2] > 0


def test_opposite_pairs_sum_to_zero():
    """WCA opposite pairs: U↔D, F↔B, R↔BL, L↔BR, UL↔DR, UR↔DL."""
    pairs = [("U", "D"), ("F", "B"), ("R", "BL"), ("L", "BR"), ("UL", "DR"), ("UR", "DL")]
    for a, b in pairs:
        s = c(a) + c(b)
        assert np.linalg.norm(s) < 1e-6, f"Pair {a}↔{b} not antipodal: sum={s}"
