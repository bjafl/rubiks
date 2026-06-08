# tests/test_algorithms.py
from megaminx.algorithms import ALGORITHM_SETS, list_algorithms, get_algorithm_set
from megaminx.model import SOLVED_STATE, validate_state
from megaminx.moves import apply_sequence

def test_list_algorithms_returns_dict():
    algs = list_algorithms()
    assert isinstance(algs, dict)
    assert "CO_ALGS" in algs

def test_get_unknown_algorithm_raises():
    import pytest
    with pytest.raises(KeyError):
        get_algorithm_set("NONEXISTENT")

def test_each_algorithm_produces_valid_state():
    for name, alg_set in ALGORITHM_SETS.items():
        for seq in alg_set:
            result = apply_sequence(SOLVED_STATE.copy(), seq)
            r = validate_state(result)
            assert r.valid, f"{name}: {seq!r} produced invalid state: {r.errors}"

def test_sune_six_times_is_identity():
    """Megaminx sexy move applied 6 times = identity.

    On a Megaminx (5-fold symmetry), the 'sexy move' [U, FR, U-, FR-] has
    order 6, which validates the orientation model end-to-end.
    (The cube Sune has order 6 on a 3x3, but order 60 on a Megaminx due to
    the 72° turn geometry.)
    """
    from megaminx.model import is_solved
    sexy_move = ["U", "FR", "U-", "FR-"]
    state = SOLVED_STATE.copy()
    for _ in range(6):
        state = apply_sequence(state, sexy_move)
    assert is_solved(state), "Sexy move × 6 should return to solved"
