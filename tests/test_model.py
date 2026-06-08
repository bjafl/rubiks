import numpy as np
import pytest
from megaminx.model import (
    MegaminxState, SOLVED_STATE, ValidationResult, validate_state, is_solved
)


def make_state(c_pos=None, c_ori=None, e_pos=None, e_ori=None):
    c_pos = c_pos if c_pos is not None else list(range(20))
    c_ori = c_ori if c_ori is not None else [0] * 20
    e_pos = e_pos if e_pos is not None else list(range(30))
    e_ori = e_ori if e_ori is not None else [0] * 30
    return MegaminxState(
        corners=np.array(list(zip(c_pos, c_ori)), dtype=np.int8),
        edges=np.array(list(zip(e_pos, e_ori)), dtype=np.int8),
    )


def test_solved_state_is_valid():
    r = validate_state(SOLVED_STATE)
    assert r.valid and r.errors == []


def test_is_solved_on_solved_state():
    assert is_solved(SOLVED_STATE)


def test_is_solved_false_on_permuted():
    s = make_state(c_pos=[1] + list(range(1, 20)))  # duplicate pos 1, missing 0
    assert not is_solved(s)


def test_invalid_corner_permutation():
    c_pos = [0] * 20  # all zeros — not a permutation
    r = validate_state(make_state(c_pos=c_pos))
    assert not r.valid
    assert any("corner" in e.lower() and "permutation" in e.lower() for e in r.errors)


def test_invalid_edge_permutation():
    e_pos = [0] * 30
    r = validate_state(make_state(e_pos=e_pos))
    assert not r.valid
    assert any("edge" in e.lower() and "permutation" in e.lower() for e in r.errors)


def test_invalid_corner_orientation_range():
    c_ori = [0] * 19 + [3]  # 3 is out of range
    r = validate_state(make_state(c_ori=c_ori))
    assert not r.valid
    assert any("orientation" in e.lower() for e in r.errors)


def test_invalid_edge_orientation_range():
    e_ori = [0] * 29 + [2]
    r = validate_state(make_state(e_ori=e_ori))
    assert not r.valid


def test_invalid_corner_orientation_sum():
    # Twist one corner by 1 — sum becomes 1 (not divisible by 3)
    c_ori = [0] * 19 + [1]
    r = validate_state(make_state(c_ori=c_ori))
    assert not r.valid
    assert any("mod 3" in e for e in r.errors)


def test_invalid_edge_orientation_sum():
    e_ori = [0] * 29 + [1]
    r = validate_state(make_state(e_ori=e_ori))
    assert not r.valid
    assert any("mod 2" in e for e in r.errors)


def test_invalid_parity():
    # Swap two corners (odd perm) but keep edges even → parity mismatch
    c_pos = list(range(20))
    c_pos[0], c_pos[1] = c_pos[1], c_pos[0]
    r = validate_state(make_state(c_pos=c_pos))
    assert not r.valid
    assert any("parity" in e.lower() for e in r.errors)
