"""
megaminx/ll_catalog.py — Last Layer (LL) cataloging and stage management

Defines LL piece slots, stage requirements (CO/EP/CP), and structures for
storing and querying case databases.
"""
from __future__ import annotations
from dataclasses import dataclass

from megaminx.cube import MegaminxState

# LL piece slots (corners and edges adjacent to the U face)
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
