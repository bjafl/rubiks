"""
Stress tests for the Megaminx simulator.

Covers properties the unit tests don't reach:
- Random sequence closure (apply + inverse = identity)
- Group-theoretic invariants after arbitrary scrambles
- Named LL algorithm isolation (no non-top pieces disturbed)
- Algorithm orders and inverse relationships
- IDA* solver round-trip correctness
"""
from __future__ import annotations

import random
import numpy as np
import pytest

from megaminx.model import SOLVED_STATE, is_solved, validate_state
from megaminx.moves import apply_sequence, FACE_NAMES

# ── helpers ────────────────────────────────────────────────────────────────────

# All 48 quarter/half turns (72° and 144° in both directions)
_ALL_MOVES: list[str] = [
    f + s for f in FACE_NAMES for s in ("", "-", "++", "--")
]

_INVERT_SUFFIX: dict[str, str] = {"": "-", "-": "", "++": "--", "--": "++"}


def _invert_sequence(seq: list[str]) -> list[str]:
    """Return the inverse of a move sequence (reversed + each move inverted)."""
    result = []
    for move in reversed(seq):
        for suffix, inv in _INVERT_SUFFIX.items():
            if move.endswith(suffix) and (suffix or not any(
                move.endswith(s) for s in ("++", "--", "-")
            )):
                result.append(move[: len(move) - len(suffix)] + inv)
                break
    return result


def _invert_move(move: str) -> str:
    """Invert a single move token."""
    for suffix, inv in (("++", "--"), ("--", "++"), ("-", ""), ("", "-")):
        if move.endswith(suffix):
            return move[: len(move) - len(suffix)] + inv
    return move + "-"


def _invert_seq(seq: list[str]) -> list[str]:
    return [_invert_move(m) for m in reversed(seq)]


def _random_seq(rng: random.Random, length: int) -> list[str]:
    return [rng.choice(_ALL_MOVES) for _ in range(length)]


def _non_top_moved(state) -> bool:
    for i in range(5, 20):
        if not np.array_equal(state.corners[i], SOLVED_STATE.corners[i]):
            return True
    for i in range(5, 30):
        if not np.array_equal(state.edges[i], SOLVED_STATE.edges[i]):
            return True
    return False


def _apply(seq: list[str]):
    return apply_sequence(SOLVED_STATE.copy(), seq)


# ── named LL algorithms (verified correct) ─────────────────────────────────────

_LL_ALGS: dict[str, list[str]] = {
    "Sune":       ["FR", "U", "FR-", "U", "FR", "U--", "FR-"],
    "Anti-Sune":  ["FR-", "U-", "FR", "U-", "FR-", "U++", "FR"],
    "Niklas":     ["FR", "U-", "FL-", "U", "FR-", "U-", "FL", "U"],
    "Niklas-inv": ["U-", "FL-", "U", "FR", "U-", "FL", "U", "FR-"],
    "EP1":        ["FR++", "U--", "FR--", "U-", "FR++", "U--", "FR--"],
    "EP2":        ["FR++", "U++", "FR--", "U", "FR++", "U++", "FR--"],
    "CO9":        ["FR", "U++", "FR-", "U-", "FR", "U", "FR-", "U-", "FR", "U-", "FR-"],
    "CO10":       ["FR", "U", "FR-", "U", "FR", "U-", "FR-", "U", "FR", "U--", "FR-"],
}

# ── 1. Random sequence closure ─────────────────────────────────────────────────

@pytest.mark.parametrize("seed", range(20))
def test_random_sequence_inverse_identity(seed: int):
    """apply(seq) then apply(seq⁻¹) returns to solved state."""
    rng = random.Random(seed * 997 + 1)
    for _ in range(500):
        seq = _random_seq(rng, rng.randint(5, 30))
        state = _apply(seq)
        state = apply_sequence(state, _invert_seq(seq))
        assert is_solved(state), f"seq={seq[:6]}... not restored by inverse"


# ── 2. Group invariants preserved after random scrambles ───────────────────────

@pytest.mark.parametrize("seed", range(10))
def test_orientation_sum_invariants(seed: int):
    """Σcorner_ori ≡ 0 mod 3 and Σedge_ori ≡ 0 mod 2 after any scramble."""
    rng = random.Random(seed * 31 + 7)
    for _ in range(1000):
        seq = _random_seq(rng, rng.randint(1, 40))
        state = _apply(seq)
        assert sum(int(x) for x in state.corners[:, 1]) % 3 == 0, "corner-ori sum not ≡ 0 mod 3"
        assert sum(int(x) for x in state.edges[:, 1]) % 2 == 0, "edge-ori sum not ≡ 0 mod 2"


@pytest.mark.parametrize("seed", range(5))
def test_parity_invariant(seed: int):
    """Parity of corner permutation equals parity of edge permutation at all times."""
    from megaminx.model import _perm_parity  # type: ignore[attr-defined]
    rng = random.Random(seed * 13 + 3)
    for _ in range(500):
        seq = _random_seq(rng, rng.randint(1, 20))
        state = _apply(seq)
        cp = _perm_parity(list(state.corners[:, 0].astype(int)))
        ep = _perm_parity(list(state.edges[:, 0].astype(int)))
        assert cp == ep, "parity invariant broken"


@pytest.mark.parametrize("seed", range(5))
def test_random_state_always_valid(seed: int):
    """validate_state reports no errors after arbitrary scrambles."""
    rng = random.Random(seed * 53 + 11)
    for _ in range(500):
        seq = _random_seq(rng, rng.randint(1, 50))
        state = _apply(seq)
        result = validate_state(state)
        assert result.valid, f"invalid state: {result.errors}  seq={seq[:6]}..."


# ── 3. LL algorithms preserve non-top pieces ──────────────────────────────────

@pytest.mark.parametrize("name,seq", _LL_ALGS.items())
def test_ll_alg_preserves_non_top_pieces(name: str, seq: list[str]):
    """Every named LL algorithm must leave non-top pieces untouched."""
    state = _apply(seq)
    assert not _non_top_moved(state), f"{name} moved non-top pieces"


# ── 4. Algorithm order and inverse relationships ───────────────────────────────

def test_sune_computed_inverse_is_identity():
    """Sune followed by its computed inverse = identity."""
    sune = _LL_ALGS["Sune"]
    state = _apply(sune)
    state = apply_sequence(state, _invert_seq(sune))
    assert is_solved(state), "Sune + Sune⁻¹ should be identity"


def test_anti_sune_computed_inverse_is_identity():
    """Anti-Sune followed by its computed inverse = identity."""
    anti = _LL_ALGS["Anti-Sune"]
    state = _apply(anti)
    state = apply_sequence(state, _invert_seq(anti))
    assert is_solved(state), "Anti-Sune + Anti-Sune⁻¹ should be identity"


def test_ep1_ep2_are_inverses():
    """EP1 followed by EP2 = identity."""
    state = _apply(_LL_ALGS["EP1"])
    state = apply_sequence(state, _LL_ALGS["EP2"])
    assert is_solved(state)


def test_niklas_inverse_correct():
    """Niklas followed by Niklas⁻¹ = identity."""
    state = _apply(_LL_ALGS["Niklas"])
    state = apply_sequence(state, _LL_ALGS["Niklas-inv"])
    assert is_solved(state)


def test_co9_order_3():
    """CO 9 has order 3 (applied three times = identity)."""
    state = SOLVED_STATE.copy()
    for _ in range(3):
        state = apply_sequence(state, _LL_ALGS["CO9"])
    assert is_solved(state), "CO9 × 3 should be identity"


def test_co10_order_3():
    """CO 10 has order 3."""
    state = SOLVED_STATE.copy()
    for _ in range(3):
        state = apply_sequence(state, _LL_ALGS["CO10"])
    assert is_solved(state), "CO10 × 3 should be identity"


def test_niklas_order():
    """Niklas has finite order (≤ 15 on Megaminx)."""
    state = SOLVED_STATE.copy()
    for n in range(1, 16):
        state = apply_sequence(state, _LL_ALGS["Niklas"])
        if is_solved(state):
            return  # found the order
    pytest.fail("Niklas did not return to identity within 15 applications")


def test_ep1_order():
    """EP1 has order 15: edges form a 3-cycle (order 3), corners form a 5-cycle (order 5); lcm=15."""
    state = SOLVED_STATE.copy()
    for _ in range(15):
        state = apply_sequence(state, _LL_ALGS["EP1"])
    assert is_solved(state), "EP1 × 15 should be identity"


# ── 5. Niklas is pure CP (no edge movement) ───────────────────────────────────

def test_niklas_is_pure_cp():
    """Niklas must not move any top edges."""
    state = _apply(_LL_ALGS["Niklas"])
    for i in range(5):
        assert np.array_equal(state.edges[i], SOLVED_STATE.edges[i]), \
            f"Niklas moved top edge slot {i}"


def test_niklas_inv_is_pure_cp():
    state = _apply(_LL_ALGS["Niklas-inv"])
    for i in range(5):
        assert np.array_equal(state.edges[i], SOLVED_STATE.edges[i]), \
            f"Niklas-inv moved top edge slot {i}"


# ── 6. Sune/Anti-Sune correctness checks ──────────────────────────────────────

def test_sune_correct_co_effect():
    """Sune must orient exactly 3 top corners (each +1), and leave non-top intact."""
    state = _apply(_LL_ALGS["Sune"])
    assert not _non_top_moved(state), "Sune moved non-top pieces"
    corner_ori = [int(state.corners[i, 1]) for i in range(5)]
    nonzero = sum(1 for o in corner_ori if o != 0)
    assert nonzero == 3, f"Sune should twist exactly 3 top corners; got {nonzero}: {corner_ori}"
    assert all(o in (0, 1) for o in corner_ori), f"Sune twists should be +1; got {corner_ori}"


def test_anti_sune_correct_co_effect():
    """Anti-Sune must orient exactly 3 top corners (each +2), and leave non-top intact."""
    state = _apply(_LL_ALGS["Anti-Sune"])
    assert not _non_top_moved(state), "Anti-Sune moved non-top pieces"
    corner_ori = [int(state.corners[i, 1]) for i in range(5)]
    nonzero = sum(1 for o in corner_ori if o != 0)
    assert nonzero == 3, f"Anti-Sune should twist exactly 3 top corners; got {nonzero}: {corner_ori}"
    assert all(o in (0, 2) for o in corner_ori), f"Anti-Sune twists should be +2; got {corner_ori}"


# ── 7. IDA* solver round-trip ─────────────────────────────────────────────────

# Restrict scramble + solver to a small subset to keep test time reasonable.
# 6 faces × 4 suffixes but only U-ring (top layer) moves to stay shallow.
_SHALLOW_MOVES = [f + s for f in ["U", "F", "FR", "FL"] for s in ("", "-", "++", "--")]


@pytest.mark.parametrize("seed", range(30))
def test_solver_roundtrip(seed: int):
    """Scramble with 3–5 shallow moves, solve with IDA*, verify solved state."""
    from megaminx.solver import solve_path

    rng = random.Random(seed * 137 + 41)
    length = rng.randint(3, 5)
    scramble = [rng.choice(_SHALLOW_MOVES) for _ in range(length)]

    scrambled = _apply(scramble)
    assert not is_solved(scrambled), "scramble produced solved state (seed collision)"

    solution = solve_path(scrambled, SOLVED_STATE.copy(), move_set=_SHALLOW_MOVES, max_depth=10)
    assert solution is not None, f"IDA* found no solution for scramble {scramble}"

    result = apply_sequence(scrambled.copy(), solution)
    assert is_solved(result), f"Applying solution {solution} to scramble {scramble} did not solve"


# ── 8. Composed scramble: invariants hold at every step ────────────────────────

def test_invariants_hold_incrementally():
    """Apply 200 random moves one at a time; verify invariants after each."""
    rng = random.Random(42)
    state = SOLVED_STATE.copy()
    for _ in range(200):
        move = rng.choice(_ALL_MOVES)
        state = apply_sequence(state, [move])
        c_sum = sum(int(x) for x in state.corners[:, 1])
        e_sum = sum(int(x) for x in state.edges[:, 1])
        assert c_sum % 3 == 0, f"after {move}: corner-ori sum {c_sum} not ≡ 0 mod 3"
        assert e_sum % 2 == 0, f"after {move}: edge-ori sum {e_sum} not ≡ 0 mod 2"
