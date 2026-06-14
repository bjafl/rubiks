# tests/test_session.py
from megaminx.model import SOLVED_STATE, is_solved
from megaminx.moves import apply_move
from mcp_server.session import SessionState


def test_initial_state_is_solved():
    s = SessionState()
    assert is_solved(s.state)


def test_push_state_and_undo():
    s = SessionState()
    before = s.state
    s.push(apply_move(s.state, "U"))
    assert not is_solved(s.state)
    s.undo()
    assert s.state == before


def test_undo_past_initial_is_noop():
    s = SessionState()
    s.undo()
    assert is_solved(s.state)


def test_undo_stack_max_size():
    s = SessionState(max_history=3)
    for move in ["U", "F", "R", "BR", "D"]:
        s.push(apply_move(s.state, move))
    for _ in range(10):
        s.undo()
    # Should not crash
    assert is_solved(s.state) or not is_solved(s.state)
