# tests/test_mcp.py
import pytest
import numpy as np
from megaminx.model import SOLVED_STATE, is_solved
from megaminx.utils import state_to_dict

from mcp_server.session import SessionState
from mcp_server import server as srv

@pytest.fixture(autouse=True)
def fresh_session():
    srv.SESSION.reset()

def test_get_state_returns_dict():
    result = srv.tool_get_state()
    assert "corners" in result and "edges" in result
    assert result["solved"] is True

def test_is_solved_true_on_fresh():
    assert srv.tool_is_solved() is True

def test_apply_move_changes_state():
    srv.tool_apply_move("U")
    assert srv.tool_is_solved() is False

def test_apply_move_invalid_raises():
    with pytest.raises(ValueError):
        srv.tool_apply_move("BOGUS")

def test_apply_sequence_and_inverse():
    srv.tool_apply_sequence(["U", "F", "FR"])
    srv.tool_apply_sequence(["FR-", "F-", "U-"])
    assert srv.tool_is_solved() is True

def test_undo():
    srv.tool_apply_move("U")
    srv.tool_undo()
    assert srv.tool_is_solved() is True

def test_scramble_produces_valid_state():
    srv.tool_scramble(20)
    from megaminx.model import validate_state
    state_dict = srv.tool_get_state()
    from megaminx.utils import dict_to_state
    state = dict_to_state(state_dict)
    assert validate_state(state).valid

def test_set_state_valid():
    solved_dict = state_to_dict(SOLVED_STATE)
    result = srv.tool_set_state(solved_dict)
    assert result["valid"] is True

def test_set_state_invalid_rejected():
    bad = state_to_dict(SOLVED_STATE)
    bad["corners"][0]["pos"] = 99
    result = srv.tool_set_state(bad)
    assert result["valid"] is False
    assert len(result["errors"]) > 0
    assert srv.tool_is_solved() is True  # state unchanged

def test_solve_path_one_move():
    srv.tool_apply_move("U")
    result = srv.tool_solve_path({}, max_depth=5)
    assert result is not None
    assert isinstance(result, list)

def test_explain_sequence():
    result = srv.tool_explain_sequence(["U", "F"])
    assert len(result) == 2
    assert "move" in result[0] and "before" in result[0] and "after" in result[0]

def test_list_algorithms():
    result = srv.tool_list_algorithms()
    assert "CO_ALGS" in result

def test_apply_named_alg():
    srv.tool_apply_named_alg("SUNE")
    assert srv.tool_is_solved() is False

def test_get_face():
    result = srv.tool_get_face("U")
    assert isinstance(result, dict)
    assert "face" in result
