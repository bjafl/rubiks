import numpy as np
from megaminx.model import SOLVED_STATE, validate_state, is_solved
from megaminx.utils import scramble, state_to_dict, dict_to_state, describe_state


def test_scramble_produces_valid_state():
    state = scramble(SOLVED_STATE.copy(), 20)
    r = validate_state(state)
    assert r.valid


def test_scramble_n0_is_identity():
    state = scramble(SOLVED_STATE.copy(), 0)
    assert is_solved(state)


def test_state_roundtrip():
    state = scramble(SOLVED_STATE.copy(), 10)
    d = state_to_dict(state)
    restored = dict_to_state(d)
    assert np.array_equal(state.corners, restored.corners)
    assert np.array_equal(state.edges, restored.edges)


def test_dict_to_state_validates():
    d = state_to_dict(SOLVED_STATE.copy())
    d["corners"][0]["pos"] = 99  # invalid
    result = dict_to_state(d, validate=True)
    assert isinstance(result, dict) and not result["valid"]


def test_describe_state_returns_string():
    desc = describe_state(SOLVED_STATE.copy())
    assert isinstance(desc, str) and len(desc) > 0
    assert "solved" in desc.lower()
