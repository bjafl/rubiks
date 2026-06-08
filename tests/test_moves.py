import numpy as np
import pytest
from megaminx.model import SOLVED_STATE, is_solved
from megaminx.moves import apply_move, apply_sequence, FACE_NAMES, ALL_MOVES

def test_face_names_count():
    assert len(FACE_NAMES) == 12

def test_all_moves_count():
    # 12 faces × CW and CCW = 24 atomic moves
    assert len(ALL_MOVES) == 24

def test_five_cw_turns_is_identity():
    """5 × 72° = 360° = identity for every face."""
    for face in FACE_NAMES:
        state = SOLVED_STATE.copy()
        for _ in range(5):
            state = apply_move(state, face)
        assert is_solved(state), f"5× {face} did not return to solved"

def test_cw_then_ccw_is_identity():
    """CW + CCW = identity for every face."""
    for face in FACE_NAMES:
        state = SOLVED_STATE.copy()
        state = apply_move(state, face)
        state = apply_move(state, face + "-")
        assert is_solved(state), f"{face} then {face}- did not return to solved"

def test_double_move_equals_two_singles():
    for face in FACE_NAMES:
        s1 = apply_move(apply_move(SOLVED_STATE.copy(), face), face)
        s2 = apply_move(SOLVED_STATE.copy(), face + "++")
        assert np.array_equal(s1.corners, s2.corners)
        assert np.array_equal(s1.edges, s2.edges)

def test_apply_sequence_empty_is_identity():
    state = apply_sequence(SOLVED_STATE.copy(), [])
    assert is_solved(state)

def test_apply_sequence_u_and_inverse():
    state = apply_sequence(SOLVED_STATE.copy(), ["U", "U-"])
    assert is_solved(state)

def test_result_state_is_valid():
    """Every single-move result must pass validate_state."""
    from megaminx.model import validate_state
    for move in ALL_MOVES:
        result = apply_move(SOLVED_STATE.copy(), move)
        r = validate_state(result)
        assert r.valid, f"Move {move!r} produced invalid state: {r.errors}"
