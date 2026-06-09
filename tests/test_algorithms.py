# tests/test_algorithms.py
from megaminx.algorithms import ALGORITHM_SETS, list_algorithms, get_algorithm_set
from megaminx.algorithms import get_library, SINGLE_ALGS, LIBRARY_ORDER
from megaminx.model import SOLVED_STATE, validate_state, is_solved
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


def test_single_algs_has_co9():
    assert "CO9" in SINGLE_ALGS
    assert SINGLE_ALGS["CO9"] == [
        "FR", "U++", "FR-", "U-", "FR", "U", "FR-", "U-", "FR", "U-", "FR-"
    ]

def test_single_algs_has_co10():
    assert "CO10" in SINGLE_ALGS
    assert SINGLE_ALGS["CO10"] == [
        "FR", "U", "FR-", "U", "FR", "U-", "FR-", "U", "FR", "U--", "FR-"
    ]

def test_single_algs_has_niklas():
    assert "NIKLAS" in SINGLE_ALGS
    assert "NIKLAS_INV" in SINGLE_ALGS

def test_single_algs_has_ep():
    assert "EP1" in SINGLE_ALGS
    assert "EP2" in SINGLE_ALGS

def test_get_library_returns_ordered_list():
    lib = get_library()
    assert isinstance(lib, list)
    assert len(lib) >= 8
    names = [e["name"] for e in lib]
    assert "CO9" in names
    assert "CO10" in names
    assert "SUNE" in names
    assert "NIKLAS" in names

def test_get_library_entries_have_moves():
    for entry in get_library():
        assert "name" in entry
        assert "moves" in entry
        assert isinstance(entry["moves"], list)
        assert len(entry["moves"]) > 0

def test_library_order_constant():
    assert LIBRARY_ORDER[0] == "CO9"
    assert LIBRARY_ORDER[1] == "CO10"


def test_niklas_and_inv_cancel():
    """NIKLAS followed by NIKLAS_INV should return to solved state."""
    state = apply_sequence(SOLVED_STATE.copy(), SINGLE_ALGS["NIKLAS"])
    state = apply_sequence(state, SINGLE_ALGS["NIKLAS_INV"])
    assert is_solved(state), "NIKLAS + NIKLAS_INV should return to solved"


def test_ep1_and_ep2_cancel():
    """EP1 followed by EP2 should return to solved state."""
    state = apply_sequence(SOLVED_STATE.copy(), SINGLE_ALGS["EP1"])
    state = apply_sequence(state, SINGLE_ALGS["EP2"])
    assert is_solved(state), "EP1 + EP2 should return to solved"


def test_get_library_moves_are_copies():
    """Mutating get_library() entries must not corrupt SINGLE_ALGS."""
    original = list(SINGLE_ALGS["CO9"])
    lib = get_library()
    entry = next(e for e in lib if e["name"] == "CO9")
    entry["moves"].append("EXTRA")
    assert SINGLE_ALGS["CO9"] == original, "get_library() must return copies, not references"
