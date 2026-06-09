import pytest
from mcp_server.viewer_state import ViewerState, parse_sequence


def test_initial_state_is_solved():
    vs = ViewerState()
    snap = vs.state_snapshot()
    assert snap["type"] == "state"
    assert snap["moveIndex"] == 0
    assert snap["totalMoves"] == 0
    assert snap["algName"] is None
    for i, (piece, ori) in enumerate(snap["corners"]):
        assert piece == i and ori == 0
    for i, (piece, ori) in enumerate(snap["edges"]):
        assert piece == i and ori == 0


def test_load_sequence_resets_to_solved():
    vs = ViewerState()
    vs.load_sequence(["U", "U-"], alg_name=None)
    snap = vs.state_snapshot()
    assert snap["totalMoves"] == 2
    assert snap["moveIndex"] == 0
    for i, (piece, _) in enumerate(snap["corners"]):
        assert piece == i  # not yet moved


def test_step_forward_advances_index():
    vs = ViewerState()
    vs.load_sequence(["U", "R"], alg_name="test")
    vs.step_forward()
    snap = vs.state_snapshot()
    assert snap["moveIndex"] == 1
    assert snap["currentMove"] == "U"


def test_step_forward_at_end_returns_false():
    vs = ViewerState()
    vs.load_sequence(["U"])
    vs.step_forward()
    assert vs.step_forward() is False


def test_step_backward_reverses():
    vs = ViewerState()
    vs.load_sequence(["U", "R"])
    vs.step_forward()
    vs.step_forward()
    vs.step_backward()
    assert vs.state_snapshot()["moveIndex"] == 1


def test_step_backward_at_start_returns_false():
    vs = ViewerState()
    vs.load_sequence(["U"])
    assert vs.step_backward() is False


def test_rewind_to_rebuilds_state():
    vs = ViewerState()
    vs.load_sequence(["U", "U", "U", "U", "U"])  # 5× U = identity
    vs.rewind_to(5)
    snap = vs.state_snapshot()
    assert snap["moveIndex"] == 5
    for i, (piece, ori) in enumerate(snap["corners"]):
        assert piece == i and ori == 0


def test_rewind_to_clamps():
    vs = ViewerState()
    vs.load_sequence(["U"])
    vs.rewind_to(999)
    assert vs.move_index == 1
    vs.rewind_to(-5)
    assert vs.move_index == 0


def test_reset_clears_everything():
    vs = ViewerState()
    vs.load_sequence(["U", "R"], alg_name="X")
    vs.step_forward()
    vs.reset()
    snap = vs.state_snapshot()
    assert snap["totalMoves"] == 0
    assert snap["moveIndex"] == 0
    assert snap["algName"] is None


def test_parse_sequence_valid():
    assert parse_sequence("R U++ R- U-") == ["R", "U++", "R-", "U-"]


def test_parse_sequence_strips_whitespace():
    assert parse_sequence("  U   R-  ") == ["U", "R-"]


def test_parse_sequence_rejects_bad_move():
    with pytest.raises(ValueError):
        parse_sequence("R XYZ U")


def test_state_snapshot_current_move_none_at_start():
    vs = ViewerState()
    vs.load_sequence(["U"])
    assert vs.state_snapshot()["currentMove"] is None


def test_state_snapshot_current_move_after_step():
    vs = ViewerState()
    vs.load_sequence(["U", "R-"])
    vs.step_forward()
    assert vs.state_snapshot()["currentMove"] == "U"
