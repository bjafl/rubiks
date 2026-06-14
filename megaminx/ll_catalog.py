"""
megaminx/ll_catalog.py — Last Layer (LL) cataloging and stage management

Defines LL piece slots, stage requirements (CO/EP/CP), and structures for
storing and querying case databases.
"""
from __future__ import annotations
from dataclasses import dataclass
import itertools
import json
from pathlib import Path

from megaminx.cube import MegaminxState, SOLVED, apply_move

# LL piece slots (corners and edges adjacent to the U face)
LL_CORNER_SLOTS: tuple[int, ...] = (6, 7, 9, 18, 19)
LL_EDGE_SLOTS: tuple[int, ...]   = (8, 11, 24, 28, 29)

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

    def to_dict(self) -> dict:
        return {
            "stage": self.stage,
            "move_set": self.move_set,
            "max_depth": self.max_depth,
            "cases": [
                {
                    "case_id": c.case_id,
                    "canonical_state": c.canonical_state,
                    "auf_variants": c.auf_variants,
                    "solutions": [
                        {"moves": s.moves, "length": s.length}
                        for s in c.solutions
                    ],
                }
                for c in self.cases
            ],
        }

    def save(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str | Path) -> "StageCatalog":
        with open(path) as f:
            data = json.load(f)
        cases = [
            Case(
                case_id=c["case_id"],
                canonical_state=c["canonical_state"],
                auf_variants=c["auf_variants"],
                solutions=[
                    Solution(moves=s["moves"], length=s["length"])
                    for s in c["solutions"]
                ],
            )
            for c in data["cases"]
        ]
        return cls(
            stage=data["stage"],
            move_set=data["move_set"],
            max_depth=data["max_depth"],
            cases=cases,
        )


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


# ─── State builder and DFS solution search ───────────────────────────────────

def _make_ll_state(ll_co: tuple, ll_cp: tuple, ll_ep: tuple) -> MegaminxState:
    """Build a MegaminxState with given LL values; all non-LL slots stay SOLVED."""
    co = list(SOLVED.co)
    cp = list(SOLVED.cp)
    ep = list(SOLVED.ep)
    for i, s in enumerate(LL_CORNER_SLOTS):
        co[s] = ll_co[i]
        cp[s] = ll_cp[i]
    for i, s in enumerate(LL_EDGE_SLOTS):
        ep[s] = ll_ep[i]
    return MegaminxState(tuple(cp), tuple(co), tuple(ep), SOLVED.eo)


def _find_solutions(
    start: MegaminxState,
    stage: LLStage,
    move_set: list[str],
    max_depth: int,
) -> list[Solution]:
    """Return all solutions (sorted shortest-first) via depth-limited DFS."""
    solutions: list[Solution] = []
    _dfs(start, stage, move_set, max_depth, [], solutions)
    solutions.sort(key=lambda s: s.length)
    return solutions


def _dfs(
    state: MegaminxState,
    stage: LLStage,
    move_set: list[str],
    depth_left: int,
    path: list[str],
    solutions: list[Solution],
) -> None:
    if stage.is_solved(state):
        solutions.append(Solution(moves=list(path), length=len(path)))
        return  # don't extend — solution already found at this depth
    if depth_left == 0:
        return
    last_face = path[-1].rstrip("0123456789-+'") if path else None
    for move in move_set:
        if move.rstrip("0123456789-+'") == last_face:
            continue  # no two moves on the same face in a row
        _dfs(apply_move(state, move), stage, move_set, depth_left - 1, path + [move], solutions)


# ─── CatalogBuilder ───────────────────────────────────────────────────────────

def _ll_to_state_dict(stage: LLStage, ll_co: tuple, ll_cp: tuple, ll_ep: tuple) -> dict:
    """Build a dict containing only the stage's component (for canonical_state / auf_variants)."""
    d: dict = {}
    if stage.solve_co:
        d["co"] = list(ll_co)
    if stage.solve_ep:
        d["ep"] = list(ll_ep)
    if stage.solve_cp:
        d["cp"] = list(ll_cp)
    return d


class CatalogBuilder:
    def __init__(self, stage: LLStage, move_set: list[str], max_depth: int) -> None:
        self.stage = stage
        self.move_set = move_set
        self.max_depth = max_depth

    def build(self) -> StageCatalog:
        canonical_list = enumerate_cases(self.stage)
        cases: list[Case] = []
        for idx, (ll_co, ll_cp, ll_ep) in enumerate(canonical_list):
            auf_variants = [
                _ll_to_state_dict(self.stage, *_apply_auf(ll_co, ll_cp, ll_ep, k))
                for k in range(5)
            ]
            start = _make_ll_state(ll_co, ll_cp, ll_ep)
            solutions = _find_solutions(start, self.stage, self.move_set, self.max_depth)
            cases.append(Case(
                case_id=f"{self.stage.name}_{idx:03d}",  # positional — stable only if enumerate_cases order is stable
                canonical_state=_ll_to_state_dict(self.stage, ll_co, ll_cp, ll_ep),
                auf_variants=auf_variants,
                solutions=solutions,
            ))
        return StageCatalog(
            stage=self.stage.name,
            move_set=self.move_set,
            max_depth=self.max_depth,
            cases=cases,
        )
