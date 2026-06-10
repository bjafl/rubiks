# tests/test_model.py
import pytest
from megaminx.model import (
    MegaminxState, SOLVED_STATE, ValidationResult, validate_state, is_solved
)


def make_state(cp=None, co=None, ep=None, eo=None):
    cp = tuple(cp) if cp is not None else tuple(range(20))
    co = tuple(co) if co is not None else (0,) * 20
    ep = tuple(ep) if ep is not None else tuple(range(30))
    eo = tuple(eo) if eo is not None else (0,) * 30
    return MegaminxState(cp, co, ep, eo)


def test_solved_state_is_valid():
    r = validate_state(SOLVED_STATE)
    assert r.valid and r.errors == []


def test_is_solved_on_solved_state():
    assert is_solved(SOLVED_STATE)


def test_is_solved_false_on_permuted():
    s = make_state(cp=[1] + list(range(1, 20)))
    assert not is_solved(s)


def test_invalid_corner_permutation():
    r = validate_state(make_state(cp=[0] * 20))
    assert not r.valid
    assert any("corner" in e.lower() and "permutation" in e.lower() for e in r.errors)


def test_invalid_edge_permutation():
    r = validate_state(make_state(ep=[0] * 30))
    assert not r.valid
    assert any("edge" in e.lower() and "permutation" in e.lower() for e in r.errors)


def test_invalid_corner_orientation_range():
    r = validate_state(make_state(co=[0] * 19 + [3]))
    assert not r.valid
    assert any("orientation" in e.lower() for e in r.errors)


def test_invalid_edge_orientation_range():
    r = validate_state(make_state(eo=[0] * 29 + [2]))
    assert not r.valid


def test_invalid_corner_orientation_sum():
    r = validate_state(make_state(co=[0] * 19 + [1]))
    assert not r.valid
    assert any("mod 3" in e for e in r.errors)


def test_invalid_edge_orientation_sum():
    r = validate_state(make_state(eo=[0] * 29 + [1]))
    assert not r.valid
    assert any("mod 2" in e for e in r.errors)


def test_invalid_parity():
    cp = list(range(20))
    cp[0], cp[1] = cp[1], cp[0]
    r = validate_state(make_state(cp=cp))
    assert not r.valid
    assert any("parity" in e.lower() for e in r.errors)
