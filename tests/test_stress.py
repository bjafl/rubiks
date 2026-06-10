# tests/test_stress.py
from __future__ import annotations
import random
import pytest
from megaminx.cube import MegaminxState, SOLVED, CORNERS, EDGES
from megaminx.model import SOLVED_STATE, is_solved, validate_state
from megaminx.moves import apply_sequence, FACE_NAMES

_ALL_MOVES: list[str] = [f + s for f in FACE_NAMES for s in ("", "-", "++", "--")]
_INVERT_SUFFIX: dict[str, str] = {"": "-", "-": "", "++": "--", "--": "++"}

_LL_CORNERS = frozenset(i for i, c in enumerate(CORNERS) if "U" in c)  # {0,4,7,18,19}
_LL_EDGES   = frozenset(i for i, e in enumerate(EDGES) if "U" in e)    # {4,8,27,28,29}


def _invert_move(move: str) -> str:
    for suffix, inv in (("++", "--"), ("--", "++"), ("-", ""), ("", "-")):
        if move.endswith(suffix):
            return move[: len(move) - len(suffix)] + inv
    return move + "-"


def _invert_seq(seq: list[str]) -> list[str]:
    return [_invert_move(m) for m in reversed(seq)]


def _random_seq(rng: random.Random, length: int) -> list[str]:
    return [rng.choice(_ALL_MOVES) for _ in range(length)]


def _apply(seq: list[str]) -> MegaminxState:
    return apply_sequence(SOLVED, seq)


def _non_top_moved(state: MegaminxState) -> bool:
    for i in range(20):
        if i not in _LL_CORNERS and (state.cp[i] != i or state.co[i] != 0):
            return True
    for i in range(30):
        if i not in _LL_EDGES and (state.ep[i] != i or state.eo[i] != 0):
            return True
    return False


_LL_ALGS: dict[str, list[str]] = {
    "Sune":       ["R", "U", "R-", "U", "R", "U--", "R-"],
    "Anti-Sune":  ["R-", "U-", "R", "U-", "R-", "U++", "R"],
    "Niklas":     ["L", "U-", "BR-", "U", "L-", "U-", "BR", "U"],
    "Niklas-inv": ["U-", "BR-", "U", "L", "U-", "BR", "U", "L-"],
    "EP1":        ["R++", "U--", "R--", "U-", "R++", "U--", "R--"],
    "EP2":        ["R++", "U++", "R--", "U", "R++", "U++", "R--"],
    "CO9":        ["R", "U++", "R-", "U-", "R", "U", "R-", "U-", "R", "U-", "R-"],
    "CO10":       ["R", "U", "R-", "U", "R", "U-", "R-", "U", "R", "U--", "R-"],
}

# ── 1. Random sequence closure ─────────────────────────────────────────────

@pytest.mark.parametrize("seed", range(20))
def test_random_sequence_inverse_identity(seed: int):
    rng = random.Random(seed * 997 + 1)
    for _ in range(500):
        seq = _random_seq(rng, rng.randint(5, 30))
        state = apply_sequence(_apply(seq), _invert_seq(seq))
        assert state == SOLVED

# ── 2. Group invariants ────────────────────────────────────────────────────

@pytest.mark.parametrize("seed", range(10))
def test_orientation_sum_invariants(seed: int):
    rng = random.Random(seed * 31 + 7)
    for _ in range(1000):
        state = _apply(_random_seq(rng, rng.randint(1, 40)))
        assert sum(state.co) % 3 == 0
        assert sum(state.eo) % 2 == 0


@pytest.mark.parametrize("seed", range(5))
def test_parity_invariant(seed: int):
    from megaminx.model import _perm_parity
    rng = random.Random(seed * 13 + 3)
    for _ in range(500):
        state = _apply(_random_seq(rng, rng.randint(1, 20)))
        assert _perm_parity(list(state.cp)) == _perm_parity(list(state.ep))


@pytest.mark.parametrize("seed", range(5))
def test_random_state_always_valid(seed: int):
    rng = random.Random(seed * 53 + 11)
    for _ in range(500):
        state = _apply(_random_seq(rng, rng.randint(1, 50)))
        result = validate_state(state)
        assert result.valid

# ── 3. LL algorithms preserve non-top pieces ──────────────────────────────

@pytest.mark.parametrize("name,seq", _LL_ALGS.items())
def test_ll_alg_preserves_non_top_pieces(name: str, seq: list[str]):
    assert not _non_top_moved(_apply(seq)), f"{name} moved non-top pieces"

# ── 4. Algorithm orders / inverses ─────────────────────────────────────────

def test_ep1_ep2_are_inverses():
    state = apply_sequence(_apply(_LL_ALGS["EP1"]), _LL_ALGS["EP2"])
    assert state == SOLVED


def test_niklas_inverse_correct():
    state = apply_sequence(_apply(_LL_ALGS["Niklas"]), _LL_ALGS["Niklas-inv"])
    assert state == SOLVED


def test_co9_order_3():
    state = SOLVED
    for _ in range(3):
        state = apply_sequence(state, _LL_ALGS["CO9"])
    assert state == SOLVED


def test_co10_order_3():
    state = SOLVED
    for _ in range(3):
        state = apply_sequence(state, _LL_ALGS["CO10"])
    assert state == SOLVED


def test_niklas_order():
    state = SOLVED
    for n in range(1, 16):
        state = apply_sequence(state, _LL_ALGS["Niklas"])
        if state == SOLVED:
            return
    pytest.fail("Niklas order > 15")


def test_ep1_order():
    state = SOLVED
    for _ in range(15):
        state = apply_sequence(state, _LL_ALGS["EP1"])
    assert state == SOLVED

# ── 5. LL edge-only algorithms ─────────────────────────────────────────────

def test_niklas_is_pure_cp():
    state = _apply(_LL_ALGS["Niklas"])
    for i in _LL_EDGES:
        assert state.ep[i] == SOLVED.ep[i] and state.eo[i] == SOLVED.eo[i]


def test_niklas_inv_is_pure_cp():
    state = _apply(_LL_ALGS["Niklas-inv"])
    for i in _LL_EDGES:
        assert state.ep[i] == SOLVED.ep[i] and state.eo[i] == SOLVED.eo[i]

# ── 6. Sune / Anti-Sune CO effect ─────────────────────────────────────────

def test_sune_correct_co_effect():
    # Megaminx Sune is not a pure CO algorithm — it combines a 3-cycle of LL
    # corners with orientation twists.  The invariants we can assert are:
    #   - no non-top pieces moved
    #   - at least one LL corner is twisted (non-trivial effect)
    #   - global CO sum ≡ 0 mod 3 (group invariant)
    state = _apply(_LL_ALGS["Sune"])
    assert not _non_top_moved(state)
    corner_ori = [state.co[i] for i in sorted(_LL_CORNERS)]
    nonzero_vals = [o for o in corner_ori if o != 0]
    assert len(nonzero_vals) >= 1, f"Sune had no CO effect on LL corners: {corner_ori}"
    assert sum(state.co) % 3 == 0


def test_anti_sune_correct_co_effect():
    # Same invariants as test_sune_correct_co_effect; additionally Sune and
    # Anti-Sune must both be non-trivial and leave only LL pieces changed.
    state = _apply(_LL_ALGS["Anti-Sune"])
    assert not _non_top_moved(state)
    corner_ori = [state.co[i] for i in sorted(_LL_CORNERS)]
    nonzero_vals = [o for o in corner_ori if o != 0]
    assert len(nonzero_vals) >= 1, f"Anti-Sune had no CO effect on LL corners: {corner_ori}"
    assert sum(state.co) % 3 == 0

# ── 7. IDA* solver round-trip ──────────────────────────────────────────────

_SHALLOW_MOVES = [f + s for f in ["U", "F", "R", "BR"] for s in ("", "-", "++", "--")]


@pytest.mark.parametrize("seed", range(30))
def test_solver_roundtrip(seed: int):
    from megaminx.solver import solve_path
    rng = random.Random(seed * 137 + 41)
    scramble = [rng.choice(_SHALLOW_MOVES) for _ in range(rng.randint(3, 5))]
    scrambled = _apply(scramble)
    assert scrambled != SOLVED
    solution = solve_path(scrambled, SOLVED, move_set=_SHALLOW_MOVES, max_depth=10)
    assert solution is not None
    assert apply_sequence(scrambled, solution) == SOLVED

# ── 8. Incremental invariants ─────────────────────────────────────────────

def test_invariants_hold_incrementally():
    rng = random.Random(42)
    state = SOLVED
    for _ in range(200):
        move = rng.choice(_ALL_MOVES)
        state = apply_sequence(state, [move])
        assert sum(state.co) % 3 == 0
        assert sum(state.eo) % 2 == 0
