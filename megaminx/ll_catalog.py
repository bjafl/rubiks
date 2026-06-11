"""
megaminx/ll_catalog.py — Last Layer (LL) cataloging and stage management

Defines LL piece slots, stage requirements (CO/EP/CP), and structures for
storing and querying case databases.
"""
from __future__ import annotations
from dataclasses import dataclass
import itertools

from megaminx.cube import MegaminxState

# LL piece slots (corners and edges adjacent to the U face)
# Index 4 appears in both tuples — no conflict because cp/co and ep/eo are separate arrays.
LL_CORNER_SLOTS: tuple[int, ...] = (0, 4, 7, 18, 19)
LL_EDGE_SLOTS: tuple[int, ...]   = (4, 8, 27, 28, 29)

_LL_CORNER_SET = frozenset(LL_CORNER_SLOTS)
_LL_EDGE_SET   = frozenset(LL_EDGE_SLOTS)


@dataclass
class LLStage:
    name: str
    solve_co: bool
    solve_ep: bool
    solve_cp: bool
    require_co_solved: bool
    require_ep_solved: bool
    require_cp_solved: bool

    def is_solved(self, state: MegaminxState) -> bool:
        """True when state satisfies all solve/preserve conditions for this stage."""
        # Non-LL pieces must be untouched
        for i in range(20):
            if i not in _LL_CORNER_SET and (state.cp[i] != i or state.co[i] != 0):
                return False
        for i in range(30):
            if i not in _LL_EDGE_SET and (state.ep[i] != i or state.eo[i] != 0):
                return False
        # Components this stage solves
        if self.solve_co and any(state.co[s] != 0 for s in LL_CORNER_SLOTS):
            return False
        if self.solve_ep:
            if any(state.ep[s] != s for s in LL_EDGE_SLOTS):
                return False
            if any(state.eo[s] != 0 for s in LL_EDGE_SLOTS):
                return False
        if self.solve_cp and any(state.cp[s] != s for s in LL_CORNER_SLOTS):
            return False
        # Components prior stages solved — must be preserved
        if self.require_co_solved and any(state.co[s] != 0 for s in LL_CORNER_SLOTS):
            return False
        if self.require_ep_solved:
            if any(state.ep[s] != s for s in LL_EDGE_SLOTS):
                return False
            if any(state.eo[s] != 0 for s in LL_EDGE_SLOTS):
                return False
        if self.require_cp_solved and any(state.cp[s] != s for s in LL_CORNER_SLOTS):
            return False
        return True


# Pre-built stage instances for CO → EP → CP ordering
CO_STAGE = LLStage(
    name="co",
    solve_co=True,  solve_ep=False, solve_cp=False,
    require_co_solved=False, require_ep_solved=False, require_cp_solved=False,
)
EP_STAGE = LLStage(
    name="ep",
    solve_co=False, solve_ep=True,  solve_cp=False,
    require_co_solved=True, require_ep_solved=False, require_cp_solved=False,
)
# CO-first ordering: CP must preserve CO (restricts which CP algs are accepted)
CP_STAGE_CO_FIRST = LLStage(
    name="cp",
    solve_co=False, solve_ep=False, solve_cp=True,
    require_co_solved=True, require_ep_solved=True, require_cp_solved=False,
)
# CO-last ordering: CP runs before CO, no CO preservation required
CP_STAGE_CO_LAST = LLStage(
    name="cp",
    solve_co=False, solve_ep=False, solve_cp=True,
    require_co_solved=False, require_ep_solved=True, require_cp_solved=False,
)


@dataclass
class Solution:
    moves: list[str]
    length: int

    def __post_init__(self):
        assert self.length == len(self.moves), (
            f"Solution.length {self.length} != len(moves) {len(self.moves)}"
        )


@dataclass
class Case:
    case_id: str
    canonical_state: dict
    auf_variants: list[dict]
    solutions: list[Solution]


@dataclass
class StageCatalog:
    stage: str
    move_set: list[str]
    max_depth: int
    cases: list[Case]


# ─── AUF canonicalization (ring-shift model) ─────────────────────────────────

def _apply_auf(
    ll_co: tuple, ll_cp: tuple, ll_ep: tuple, k: int
) -> tuple[tuple, tuple, tuple]:
    """Ring-shift all three LL tuples by k positions.

    new[i] = old[(i - k) % 5] — pure positional relabeling, no orientation twist.
    """
    n = 5
    shifted_co = tuple(ll_co[(i - k) % n] for i in range(n))
    shifted_cp = tuple(ll_cp[(i - k) % n] for i in range(n))
    shifted_ep = tuple(ll_ep[(i - k) % n] for i in range(n))
    return shifted_co, shifted_cp, shifted_ep


def auf_canonical(
    ll_co: tuple, ll_cp: tuple, ll_ep: tuple
) -> tuple[tuple, tuple, tuple]:
    """Return the lexicographically smallest AUF variant as the canonical key."""
    variants = [_apply_auf(ll_co, ll_cp, ll_ep, k) for k in range(5)]
    return min(variants)


# ─── Case enumeration ─────────────────────────────────────────────────────────


def _perm_parity(perm: tuple, identity: tuple) -> int:
    """Return 0 for even permutations, 1 for odd."""
    n = len(perm)
    idx = {v: i for i, v in enumerate(identity)}
    local = [idx[v] for v in perm]
    visited = [False] * n
    par = 0
    for i in range(n):
        if not visited[i]:
            c, j = 0, i
            while not visited[j]:
                visited[j], j, c = True, local[j], c + 1
            par ^= (c + 1) % 2
    return par


def _iter_co_states():
    """Yield all non-trivial (sum≡0 mod 3) CO states as (ll_co, identity_cp, identity_ep)."""
    identity_cp = tuple(LL_CORNER_SLOTS)
    identity_ep = tuple(LL_EDGE_SLOTS)
    for co in itertools.product(range(3), repeat=5):
        if sum(co) % 3 == 0 and any(x != 0 for x in co):
            yield (co, identity_cp, identity_ep)


def _iter_ep_states():
    """Yield all non-trivial even EP permutations as (identity_co, identity_cp, ll_ep)."""
    identity_co = (0,) * 5
    identity_cp = tuple(LL_CORNER_SLOTS)
    identity_ep = tuple(LL_EDGE_SLOTS)
    for ep_perm in itertools.permutations(LL_EDGE_SLOTS):
        if ep_perm != identity_ep and _perm_parity(ep_perm, identity_ep) == 0:
            yield (identity_co, identity_cp, ep_perm)


def _iter_cp_states():
    """Yield all non-trivial even CP permutations as (identity_co, ll_cp, identity_ep)."""
    identity_co = (0,) * 5
    identity_cp = tuple(LL_CORNER_SLOTS)
    identity_ep = tuple(LL_EDGE_SLOTS)
    for cp_perm in itertools.permutations(LL_CORNER_SLOTS):
        if cp_perm != identity_cp and _perm_parity(cp_perm, identity_cp) == 0:
            yield (identity_co, cp_perm, identity_ep)


def enumerate_cases(stage: LLStage) -> list[tuple]:
    """Return canonical (ll_co, ll_cp, ll_ep) for each unique AUF-equivalence class."""
    if stage.solve_co:
        raw_iter = _iter_co_states()
    elif stage.solve_ep:
        raw_iter = _iter_ep_states()
    elif stage.solve_cp:
        raw_iter = _iter_cp_states()
    else:
        raise ValueError("Stage must solve at least one component")

    identity_co = (0,) * 5
    identity_cp = tuple(LL_CORNER_SLOTS)
    identity_ep = tuple(LL_EDGE_SLOTS)
    n = 5

    seen: set = set()
    cases: list[tuple] = []
    for ll_co, ll_cp, ll_ep in raw_iter:
        if stage.solve_co:
            key = min(tuple(ll_co[(i - k) % n] for i in range(n)) for k in range(n))
            canonical = (key, identity_cp, identity_ep)
        elif stage.solve_ep:
            key = min(tuple(ll_ep[(i - k) % n] for i in range(n)) for k in range(n))
            canonical = (identity_co, identity_cp, key)
        else:
            key = min(tuple(ll_cp[(i - k) % n] for i in range(n)) for k in range(n))
            canonical = (identity_co, key, identity_ep)

        if key not in seen:
            seen.add(key)
            cases.append(canonical)
    return cases
