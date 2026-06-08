from megaminx.model import SOLVED_STATE
from megaminx.moves import apply_move
from megaminx.heuristics import lower_bound


def test_solved_state_lower_bound_is_zero():
    assert lower_bound(SOLVED_STATE) == 0


def test_one_move_lower_bound_is_at_least_one():
    state = apply_move(SOLVED_STATE.copy(), "U")
    assert lower_bound(state) >= 1


def test_lower_bound_never_exceeds_true_distance():
    """Admissibility check: 1-move state needs exactly 1 move."""
    state = apply_move(SOLVED_STATE.copy(), "F")
    # Lower bound must be ≤ 1 (the true distance is 1)
    assert lower_bound(state) <= 1
