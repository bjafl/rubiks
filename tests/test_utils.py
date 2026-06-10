# tests/test_utils.py
from megaminx.model import SOLVED_STATE, validate_state, is_solved
from megaminx.utils import scramble, state_to_dict, dict_to_state, describe_state


def test_scramble_produces_valid_state():
    state = scramble(SOLVED_STATE, 20)
    assert validate_state(state).valid


def test_scramble_n0_is_identity():
    assert is_solved(scramble(SOLVED_STATE, 0))


def test_state_roundtrip():
    state = scramble(SOLVED_STATE, 10)
    d = state_to_dict(state)
    restored = dict_to_state(d)
    assert state == restored


def test_dict_to_state_validates():
    d = state_to_dict(SOLVED_STATE)
    d["corners"][0]["pos"] = 99
    result = dict_to_state(d, validate=True)
    assert isinstance(result, dict) and not result["valid"]


def test_describe_state_returns_string():
    desc = describe_state(SOLVED_STATE)
    assert "solved" in desc.lower()
