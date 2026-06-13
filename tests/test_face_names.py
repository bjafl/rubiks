# tests/test_face_names.py
"""Verifies FACE_NAMES match cube.py (WCA-correct) naming."""
import numpy as np
import pytest
from megaminx.moves import FACE_NAMES, _face_centers, _FACE_INDEX
from megaminx.cube import FACES


def c(name: str) -> np.ndarray:
    return _face_centers[_FACE_INDEX[name]]


def test_face_names_equal_cube_faces():
    assert FACE_NAMES == FACES


def test_all_12_wca_names_present():
    expected = {"U", "D", "F", "R", "BR", "BL", "L", "dR", "dBR", "B", "dBL", "dL"}
    assert set(FACE_NAMES) == expected


def test_u_highest_y():
    assert c("U")[1] == max(fc[1] for fc in _face_centers)


def test_d_lowest_y():
    assert c("D")[1] == min(fc[1] for fc in _face_centers)


def test_f_is_frontmost():
    """F: adjacent to U, closest to camera at (0, 5, 3) among U-ring faces."""
    import numpy as np
    camera = np.array([0.0, 5.0, 3.0])
    u_ring_names = ["F", "R", "BR", "BL", "L"]
    f_dist = np.linalg.norm(camera - c("F"))
    assert all(f_dist <= np.linalg.norm(camera - c(n)) for n in u_ring_names)


def test_r_is_rightmost():
    assert c("R")[0] > 1.0


def test_l_is_leftmost():
    assert c("L")[0] < -1.0


def test_br_is_back_right():
    assert c("BR")[2] > 1.0 and c("BR")[0] > 0


def test_bl_is_back_left():
    assert c("BL")[2] > 1.0 and c("BL")[0] < 0


def test_lower_faces_have_negative_y():
    for name in ["dR", "dBR", "B", "dBL", "dL"]:
        assert c(name)[1] <= 0, f"{name} should have non-positive Y (below or at equator)"


def test_opposite_pairs_sum_to_zero():
    """Antipodal face pairs sum to zero."""
    pairs = [("U", "B"), ("F", "D"), ("R", "dBL"), ("L", "dBR"),
             ("BR", "dL"), ("BL", "dR")]
    for a, b in pairs:
        s = c(a) + c(b)
        assert np.linalg.norm(s) < 1e-6, f"Pair {a}↔{b} not antipodal: sum={s}"
