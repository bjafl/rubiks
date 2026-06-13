# tests/test_cube.py
import pytest
from megaminx.cube import (
    FACES, CORNERS, EDGES, MOVES, SOLVED, MegaminxState,
    apply_move, apply_sequence,
)

def test_faces_count():
    assert len(FACES) == 12
    assert FACES[0] == "U" and FACES[6] == "D"

def test_corners_edges_count():
    assert len(CORNERS) == 20
    assert len(EDGES) == 30

def test_solved_is_identity():
    assert SOLVED.cp == tuple(range(20))
    assert SOLVED.co == (0,) * 20
    assert SOLVED.ep == tuple(range(30))
    assert SOLVED.eo == (0,) * 30

def test_moves_count():
    # 12 faces × 4 powers + 3 legacy aliases × 12 = 48 + 36 = 84
    assert len(MOVES) == 84

def test_face_order_5():
    """5 CW turns = identity for every face."""
    for f in FACES:
        state = SOLVED
        for _ in range(5):
            state = state.apply(f)
        assert state == SOLVED, f"5× {f} not identity"

def test_cw_then_ccw_identity():
    for f in FACES:
        assert SOLVED.apply(f).apply(f + "'") == SOLVED

def test_legacy_notation():
    for f in FACES:
        assert SOLVED.apply(f + "-") == SOLVED.apply(f + "'")
        assert SOLVED.apply(f + "++") == SOLVED.apply(f + "2")
        assert SOLVED.apply(f + "--") == SOLVED.apply(f + "2'")

def test_orientation_sum_invariants():
    import random
    rng = random.Random(42)
    state = SOLVED
    all_moves = [f + s for f in FACES for s in ("", "'")]
    for _ in range(500):
        state = state.apply(rng.choice(all_moves))
        assert sum(state.co) % 3 == 0
        assert sum(state.eo) % 2 == 0

def test_state_is_hashable():
    s = {SOLVED, SOLVED.apply("U")}
    assert len(s) == 2

def test_u_corner_indices():
    u_corners = [i for i, c in enumerate(CORNERS) if "U" in c]
    assert set(u_corners) == {13, 14, 15, 18, 19}

def test_u_edge_indices():
    u_edges = [i for i, e in enumerate(EDGES) if "U" in e]
    assert set(u_edges) == {18, 19, 22, 25, 26}

def test_apply_sequence():
    state = apply_sequence(SOLVED, ["U", "U'"])
    assert state == SOLVED

def test_sexy_move_order_6():
    state = SOLVED
    for _ in range(6):
        state = apply_sequence(state, ["R", "U", "R'", "U'"])
    assert state == SOLVED
