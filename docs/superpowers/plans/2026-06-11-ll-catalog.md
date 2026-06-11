# LL Catalog — Case Enumeration and Solution Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `megaminx/ll_catalog.py` — a pipeline that enumerates all LL cases per stage (CO/EP/CP), reduces them to AUF-canonical equivalence classes, and exhaustively searches for all solving sequences up to a configurable depth.

**Architecture:** A `CatalogBuilder` class accepts an `LLStage` configuration (which components to solve/preserve), a move set, and a depth limit. It enumerates cases mathematically (no BFS), canonicalizes via ring-shift AUF, runs DFS per case, and serializes to JSON. A CLI script drives generation per stage.

**Tech Stack:** Python stdlib (`itertools`, `json`, `pathlib`, `argparse`, `dataclasses`); `megaminx.cube` (`MegaminxState`, `SOLVED`, `apply_move`, `LL_CORNER_SLOTS`/`LL_EDGE_SLOTS` constants).

**Critical note on AUF model:** AUF canonicalization uses a *ring-shift* model — `new[i] = old[(i-k) % 5]` — NOT the physical `apply_move(state, "U")`. This is verified by the spec's example: `[0,1,2,0,2]` → `[2,0,1,2,0]` after k=1. Using the actual U move gives different values because it adds orientation twists. The `_make_ll_state` / `apply_move` helpers are only used in the DFS, not in canonicalization.

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `megaminx/ll_catalog.py` | Create | All logic: constants, dataclasses, AUF, enumeration, DFS, `CatalogBuilder`, serialization |
| `tests/test_ll_catalog.py` | Create | Unit tests covering all functions and the pipeline |
| `scripts/gen_ll_catalog.py` | Create | CLI entry point |
| `.gitignore` | Modify | Add `ll_catalog/` |

---

### Task 1: Constants, Data Classes, and Pre-built Stage Instances

**Files:**
- Create: `megaminx/ll_catalog.py`
- Create: `tests/test_ll_catalog.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_ll_catalog.py
import pytest
from megaminx.ll_catalog import (
    LL_CORNER_SLOTS, LL_EDGE_SLOTS,
    LLStage, Solution, Case, StageCatalog,
    CO_STAGE, EP_STAGE, CP_STAGE_CO_FIRST, CP_STAGE_CO_LAST,
)


def test_ll_corner_slots():
    assert LL_CORNER_SLOTS == (0, 4, 7, 18, 19)
    assert len(LL_CORNER_SLOTS) == 5


def test_ll_edge_slots():
    assert LL_EDGE_SLOTS == (4, 8, 27, 28, 29)
    assert len(LL_EDGE_SLOTS) == 5


def test_co_stage_flags():
    assert CO_STAGE.solve_co is True
    assert CO_STAGE.solve_ep is False
    assert CO_STAGE.solve_cp is False
    assert CO_STAGE.require_co_solved is False
    assert CO_STAGE.require_ep_solved is False
    assert CO_STAGE.require_cp_solved is False


def test_ep_stage_flags():
    assert EP_STAGE.solve_ep is True
    assert EP_STAGE.require_co_solved is True
    assert EP_STAGE.solve_co is False
    assert EP_STAGE.solve_cp is False


def test_cp_stage_co_first_flags():
    assert CP_STAGE_CO_FIRST.solve_cp is True
    assert CP_STAGE_CO_FIRST.require_co_solved is True
    assert CP_STAGE_CO_FIRST.require_ep_solved is True


def test_cp_stage_co_last_flags():
    assert CP_STAGE_CO_LAST.solve_cp is True
    assert CP_STAGE_CO_LAST.require_co_solved is False
    assert CP_STAGE_CO_LAST.require_ep_solved is True


def test_solution_dataclass():
    s = Solution(moves=["R", "U", "R-"], length=3)
    assert s.moves == ["R", "U", "R-"]
    assert s.length == 3


def test_stage_catalog_dataclass():
    cat = StageCatalog(stage="co", move_set=["R", "U"], max_depth=5, cases=[])
    assert cat.stage == "co"
    assert cat.cases == []
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd /home/bjafl/source/rubiks
python -m pytest tests/test_ll_catalog.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'megaminx.ll_catalog'`

- [ ] **Step 3: Create `megaminx/ll_catalog.py` with constants and data classes**

```python
# megaminx/ll_catalog.py
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import json

from megaminx.cube import MegaminxState, SOLVED, apply_move

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
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
python -m pytest tests/test_ll_catalog.py -v 2>&1 | head -30
```

Expected: all 8 tests pass.

- [ ] **Step 5: Commit**

```bash
git add megaminx/ll_catalog.py tests/test_ll_catalog.py
git commit -m "feat: add LLStage dataclasses, constants, and pre-built stage instances"
```

---

### Task 2: AUF Canonicalization

**Files:**
- Modify: `megaminx/ll_catalog.py`
- Modify: `tests/test_ll_catalog.py`

**Key design — ring-shift model:** AUF rotation by k means `new[i] = old[(i-k) % 5]` for all five LL values. This is a positional relabeling (not a physical U move). It applies identically to co, cp, and ep tuples.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_ll_catalog.py`:

```python
from megaminx.ll_catalog import _apply_auf, auf_canonical


def test_apply_auf_k0_is_identity():
    ll_co = (0, 1, 2, 0, 2)
    ll_cp = LL_CORNER_SLOTS
    ll_ep = LL_EDGE_SLOTS
    assert _apply_auf(ll_co, ll_cp, ll_ep, 0) == (ll_co, ll_cp, ll_ep)


def test_apply_auf_k1_spec_example():
    # Spec example: [0,1,2,0,2] → [2,0,1,2,0] after k=1
    ll_co = (0, 1, 2, 0, 2)
    result_co, _, _ = _apply_auf(ll_co, LL_CORNER_SLOTS, LL_EDGE_SLOTS, 1)
    assert result_co == (2, 0, 1, 2, 0)


def test_apply_auf_all_5_variants_spec():
    # Full spec example variants
    ll_co = (0, 1, 2, 0, 2)
    expected = [
        (0, 1, 2, 0, 2),
        (2, 0, 1, 2, 0),
        (0, 2, 0, 1, 2),
        (2, 0, 2, 0, 1),
        (1, 2, 0, 2, 0),
    ]
    for k in range(5):
        result_co, _, _ = _apply_auf(ll_co, LL_CORNER_SLOTS, LL_EDGE_SLOTS, k)
        assert result_co == expected[k], f"k={k}: got {result_co}, expected {expected[k]}"


def test_auf_canonical_is_minimum():
    ll_co = (0, 1, 2, 0, 2)
    ll_cp = LL_CORNER_SLOTS
    ll_ep = LL_EDGE_SLOTS
    canonical = auf_canonical(ll_co, ll_cp, ll_ep)
    for k in range(5):
        variant = _apply_auf(ll_co, ll_cp, ll_ep, k)
        assert canonical <= variant


def test_auf_canonical_stable():
    # Canonical is a fixed point: auf_canonical(canonical) == canonical
    ll_co = (0, 1, 2, 0, 2)
    canonical = auf_canonical(ll_co, LL_CORNER_SLOTS, LL_EDGE_SLOTS)
    assert auf_canonical(*canonical) == canonical


def test_auf_5_distinct_variants():
    # Non-trivial CO states have orbit size 5 (no period < 5)
    ll_co = (0, 1, 2, 0, 2)
    canonical = auf_canonical(ll_co, LL_CORNER_SLOTS, LL_EDGE_SLOTS)
    variants = {_apply_auf(*canonical, k) for k in range(5)}
    assert len(variants) == 5
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
python -m pytest tests/test_ll_catalog.py -k "auf" -v 2>&1 | head -20
```

Expected: `ImportError: cannot import name '_apply_auf'`

- [ ] **Step 3: Add AUF functions to `megaminx/ll_catalog.py`**

Add after the `StageCatalog` dataclass:

```python
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
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
python -m pytest tests/test_ll_catalog.py -k "auf" -v
```

Expected: all 6 AUF tests pass.

- [ ] **Step 5: Commit**

```bash
git add megaminx/ll_catalog.py tests/test_ll_catalog.py
git commit -m "feat: add AUF ring-shift canonicalization"
```

---

### Task 3: Case Enumeration

**Files:**
- Modify: `megaminx/ll_catalog.py`
- Modify: `tests/test_ll_catalog.py`

**Expected case counts (from spec):** CO → 16, EP → 5, CP → ~12 (Burnside: 60/5=12).

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_ll_catalog.py`:

```python
from megaminx.ll_catalog import enumerate_cases


def test_co_case_count():
    cases = enumerate_cases(CO_STAGE)
    assert len(cases) == 16


def test_ep_case_count():
    cases = enumerate_cases(EP_STAGE)
    assert len(cases) == 5


def test_cp_case_count():
    cases = enumerate_cases(CP_STAGE_CO_FIRST)
    assert 10 <= len(cases) <= 14  # Burnside estimate: 60/5 = 12


def test_cases_are_canonical():
    # Every case returned by enumerate_cases must already be its own canonical
    for case in enumerate_cases(CO_STAGE):
        assert auf_canonical(*case) == case


def test_cases_are_distinct():
    cases = enumerate_cases(CO_STAGE)
    assert len(set(cases)) == len(cases)


def test_co_cases_exclude_identity():
    # CO=(0,0,0,0,0) must not appear in any AUF variant
    cases = enumerate_cases(CO_STAGE)
    identity_co = (0, 0, 0, 0, 0)
    for case in cases:
        ll_co, _, _ = case
        for k in range(5):
            rotated_co, _, _ = _apply_auf(*case, k)
            assert rotated_co != identity_co
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
python -m pytest tests/test_ll_catalog.py -k "case_count or cases_are or co_cases" -v 2>&1 | head -20
```

Expected: `ImportError: cannot import name 'enumerate_cases'`

- [ ] **Step 3: Add enumeration helpers to `megaminx/ll_catalog.py`**

Add after the AUF functions:

```python
# ─── Case enumeration ─────────────────────────────────────────────────────────
import itertools


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
    """Yield (ll_co, ll_cp, ll_ep) for all non-trivial CO states."""
    identity_cp = tuple(LL_CORNER_SLOTS)
    identity_ep = tuple(LL_EDGE_SLOTS)
    for co in itertools.product(range(3), repeat=5):
        if sum(co) % 3 == 0 and any(x != 0 for x in co):
            yield (co, identity_cp, identity_ep)


def _iter_ep_states():
    """Yield (ll_co, ll_cp, ll_ep) for all non-trivial even EP permutations."""
    identity_co = (0,) * 5
    identity_cp = tuple(LL_CORNER_SLOTS)
    identity_ep = tuple(LL_EDGE_SLOTS)
    for ep_perm in itertools.permutations(LL_EDGE_SLOTS):
        if ep_perm != identity_ep and _perm_parity(ep_perm, identity_ep) == 0:
            yield (identity_co, identity_cp, ep_perm)


def _iter_cp_states():
    """Yield (ll_co, ll_cp, ll_ep) for all non-trivial even CP permutations."""
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

    seen: set[tuple] = set()
    cases: list[tuple] = []
    for ll_co, ll_cp, ll_ep in raw_iter:
        key = auf_canonical(ll_co, ll_cp, ll_ep)
        if key not in seen:
            seen.add(key)
            cases.append(key)
    return cases
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
python -m pytest tests/test_ll_catalog.py -k "case_count or cases_are or co_cases" -v
```

Expected: all 6 enumeration tests pass.

- [ ] **Step 5: Commit**

```bash
git add megaminx/ll_catalog.py tests/test_ll_catalog.py
git commit -m "feat: add LL case enumeration with AUF-equivalence deduplication"
```

---

### Task 4: DFS Solution Search

**Files:**
- Modify: `megaminx/ll_catalog.py`
- Modify: `tests/test_ll_catalog.py`

**Design:** `_make_ll_state` builds a full `MegaminxState` with the given LL values (non-LL slots stay SOLVED). `_dfs` uses depth-limited recursion with face-consecutive-move pruning. A found solution is not extended further (stop at first hit on each path).

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_ll_catalog.py`:

```python
from megaminx.cube import MegaminxState, SOLVED
from megaminx.ll_catalog import _make_ll_state, _find_solutions


def test_make_ll_state_identity():
    state = _make_ll_state((0,)*5, LL_CORNER_SLOTS, LL_EDGE_SLOTS)
    assert state == SOLVED


def test_make_ll_state_co_only():
    co = (0, 1, 2, 0, 2)
    state = _make_ll_state(co, LL_CORNER_SLOTS, LL_EDGE_SLOTS)
    for i, s in enumerate(LL_CORNER_SLOTS):
        assert state.co[s] == co[i]
    for s in LL_CORNER_SLOTS:
        assert state.cp[s] == s  # CP identity
    for s in LL_EDGE_SLOTS:
        assert state.ep[s] == s  # EP identity


def test_is_solved_co_stage_detects_unoriented():
    co = (0, 1, 0, 0, 0)  # sum=1, invalid — but for is_solved test we use valid
    co = (0, 1, 2, 0, 0)  # sum=3≡0 — corner at slot 4 has co=1
    state = _make_ll_state(co, LL_CORNER_SLOTS, LL_EDGE_SLOTS)
    assert not CO_STAGE.is_solved(state)


def test_is_solved_co_stage_accepts_solved():
    state = _make_ll_state((0,)*5, LL_CORNER_SLOTS, LL_EDGE_SLOTS)
    assert CO_STAGE.is_solved(state)


def test_find_solutions_empty_for_solved():
    # Solved state needs 0-move solution (empty path)
    state = _make_ll_state((0,)*5, LL_CORNER_SLOTS, LL_EDGE_SLOTS)
    solutions = _find_solutions(state, CO_STAGE, ["R", "R-", "U", "U-"], 5)
    assert any(s.length == 0 for s in solutions)


def test_find_solutions_for_co_state():
    # CO state (0,1,2,0,2) — canonical form is known
    canonical = auf_canonical((0,1,2,0,2), LL_CORNER_SLOTS, LL_EDGE_SLOTS)
    ll_co, ll_cp, ll_ep = canonical
    state = _make_ll_state(ll_co, ll_cp, ll_ep)
    move_set = ["R", "R-", "U", "U-", "U++", "U--"]
    solutions = _find_solutions(state, CO_STAGE, move_set, max_depth=8)
    # Every solution must actually solve the state
    for sol in solutions:
        s = state
        for m in sol.moves:
            s = apply_move(s, m)
        assert CO_STAGE.is_solved(s)


def test_solutions_sorted_by_length():
    canonical = auf_canonical((0,1,2,0,2), LL_CORNER_SLOTS, LL_EDGE_SLOTS)
    ll_co, ll_cp, ll_ep = canonical
    state = _make_ll_state(ll_co, ll_cp, ll_ep)
    solutions = _find_solutions(state, CO_STAGE, ["R","R-","U","U-","U++","U--"], 8)
    if len(solutions) >= 2:
        for i in range(len(solutions) - 1):
            assert solutions[i].length <= solutions[i + 1].length
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
python -m pytest tests/test_ll_catalog.py -k "make_ll or is_solved or find_solutions or solutions_sorted" -v 2>&1 | head -20
```

Expected: `ImportError: cannot import name '_make_ll_state'`

- [ ] **Step 3: Add DFS functions to `megaminx/ll_catalog.py`**

Add after the enumeration section:

```python
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
    last_face = path[-1].rstrip("-+") if path else None
    for move in move_set:
        if move.rstrip("-+") == last_face:
            continue  # no two moves on the same face in a row
        _dfs(apply_move(state, move), stage, move_set, depth_left - 1, path + [move], solutions)
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
python -m pytest tests/test_ll_catalog.py -k "make_ll or is_solved or find_solutions or solutions_sorted" -v
```

Expected: all 8 DFS tests pass.

- [ ] **Step 5: Commit**

```bash
git add megaminx/ll_catalog.py tests/test_ll_catalog.py
git commit -m "feat: add LL state builder and depth-limited DFS solution search"
```

---

### Task 5: CatalogBuilder

**Files:**
- Modify: `megaminx/ll_catalog.py`
- Modify: `tests/test_ll_catalog.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_ll_catalog.py`:

```python
from megaminx.ll_catalog import CatalogBuilder


def test_catalog_builder_co_case_count():
    # Use small move set and depth for speed; just verify case count
    builder = CatalogBuilder(CO_STAGE, ["R", "R-", "U", "U-"], max_depth=1)
    catalog = builder.build()
    assert catalog.stage == "co"
    assert len(catalog.cases) == 16


def test_catalog_builder_case_has_5_auf_variants():
    builder = CatalogBuilder(CO_STAGE, ["R", "R-", "U", "U-"], max_depth=1)
    catalog = builder.build()
    for case in catalog.cases:
        assert len(case.auf_variants) == 5


def test_catalog_builder_canonical_in_auf_variants():
    # The canonical state must be auf_variants[0]
    builder = CatalogBuilder(CO_STAGE, ["R", "R-", "U", "U-"], max_depth=1)
    catalog = builder.build()
    for case in catalog.cases:
        assert case.auf_variants[0] == case.canonical_state


def test_catalog_builder_case_ids_unique():
    builder = CatalogBuilder(CO_STAGE, ["R", "R-", "U", "U-"], max_depth=1)
    catalog = builder.build()
    ids = [c.case_id for c in catalog.cases]
    assert len(ids) == len(set(ids))


def test_catalog_builder_solutions_solve_case():
    # Every solution must bring the canonical start state to is_solved
    move_set = ["R", "R-", "U", "U-", "U++", "U--"]
    builder = CatalogBuilder(CO_STAGE, move_set, max_depth=7)
    catalog = builder.build()
    for case in catalog.cases:
        ll_co = tuple(case.canonical_state["co"])
        state = _make_ll_state(ll_co, LL_CORNER_SLOTS, LL_EDGE_SLOTS)
        for sol in case.solutions:
            s = state
            for m in sol.moves:
                s = apply_move(s, m)
            assert CO_STAGE.is_solved(s), f"Solution {sol.moves} failed for {case.case_id}"


def test_catalog_builder_solutions_preserve_nll():
    # No solution should disturb non-LL pieces (⟨R,U⟩ is LL-only by construction)
    move_set = ["R", "R-", "U", "U-"]
    builder = CatalogBuilder(CO_STAGE, move_set, max_depth=7)
    catalog = builder.build()
    for case in catalog.cases:
        ll_co = tuple(case.canonical_state["co"])
        state = _make_ll_state(ll_co, LL_CORNER_SLOTS, LL_EDGE_SLOTS)
        for sol in case.solutions:
            s = state
            for m in sol.moves:
                s = apply_move(s, m)
            for i in range(20):
                if i not in _LL_CORNER_SET:
                    assert s.cp[i] == i and s.co[i] == 0
            for i in range(30):
                if i not in _LL_EDGE_SET:
                    assert s.ep[i] == i and s.eo[i] == 0
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
python -m pytest tests/test_ll_catalog.py -k "catalog_builder" -v 2>&1 | head -20
```

Expected: `ImportError: cannot import name 'CatalogBuilder'`

- [ ] **Step 3: Add `CatalogBuilder` to `megaminx/ll_catalog.py`**

Add a `_ll_to_state_dict` helper and the class after the DFS section:

```python
# ─── CatalogBuilder ───────────────────────────────────────────────────────────

def _ll_to_state_dict(stage: LLStage, ll_co: tuple, ll_cp: tuple, ll_ep: tuple) -> dict:
    """Build canonical_state / auf_variant dict containing only the stage's component."""
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
                case_id=f"{self.stage.name}_{idx:03d}",
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
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
python -m pytest tests/test_ll_catalog.py -k "catalog_builder" -v
```

The `test_catalog_builder_solutions_solve_case` and `test_catalog_builder_solutions_preserve_nll` tests use `max_depth=7` and may take ~30 seconds. Expected: all 6 builder tests pass.

- [ ] **Step 5: Run full test suite to check no regressions**

```bash
python -m pytest tests/ -v --tb=short 2>&1 | tail -20
```

Expected: all previous tests still pass.

- [ ] **Step 6: Commit**

```bash
git add megaminx/ll_catalog.py tests/test_ll_catalog.py
git commit -m "feat: add CatalogBuilder assembling cases with AUF variants and DFS solutions"
```

---

### Task 6: Serialization, CLI, and .gitignore

**Files:**
- Modify: `megaminx/ll_catalog.py` — add `to_dict`, `save`, `load` to `StageCatalog`
- Create: `scripts/gen_ll_catalog.py`
- Modify: `.gitignore`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_ll_catalog.py`:

```python
import json
import tempfile
from pathlib import Path
from megaminx.ll_catalog import StageCatalog, CatalogBuilder, CO_STAGE


def test_catalog_to_dict_schema():
    builder = CatalogBuilder(CO_STAGE, ["R", "R-", "U", "U-"], max_depth=1)
    catalog = builder.build()
    d = catalog.to_dict()
    assert d["stage"] == "co"
    assert isinstance(d["move_set"], list)
    assert isinstance(d["max_depth"], int)
    assert isinstance(d["cases"], list)
    first = d["cases"][0]
    assert "case_id" in first
    assert "canonical_state" in first
    assert "auf_variants" in first
    assert len(first["auf_variants"]) == 5
    assert "solutions" in first
    # solutions is a list of {"moves": [...], "length": int}
    for sol in first["solutions"]:
        assert "moves" in sol and "length" in sol


def test_catalog_save_and_load_roundtrip():
    builder = CatalogBuilder(CO_STAGE, ["R", "R-", "U", "U-"], max_depth=1)
    original = builder.build()
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "co.json"
        original.save(path)
        loaded = StageCatalog.load(path)
    assert loaded.stage == original.stage
    assert loaded.move_set == original.move_set
    assert loaded.max_depth == original.max_depth
    assert len(loaded.cases) == len(original.cases)
    for orig_case, load_case in zip(original.cases, loaded.cases):
        assert orig_case.case_id == load_case.case_id
        assert orig_case.canonical_state == load_case.canonical_state
        assert orig_case.auf_variants == load_case.auf_variants
        assert len(orig_case.solutions) == len(load_case.solutions)
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
python -m pytest tests/test_ll_catalog.py -k "to_dict or roundtrip" -v 2>&1 | head -20
```

Expected: `AttributeError: 'StageCatalog' object has no attribute 'to_dict'`

- [ ] **Step 3: Add serialization methods to `StageCatalog` in `megaminx/ll_catalog.py`**

Replace the `StageCatalog` dataclass definition with:

```python
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
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
python -m pytest tests/test_ll_catalog.py -k "to_dict or roundtrip" -v
```

Expected: both pass.

- [ ] **Step 5: Create `scripts/gen_ll_catalog.py`**

First create the directory:

```bash
mkdir -p /home/bjafl/source/rubiks/scripts
```

Then create the file:

```python
#!/usr/bin/env python3
"""Generate LL catalog JSON files for a given stage."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from megaminx.ll_catalog import (
    CatalogBuilder,
    CO_STAGE, EP_STAGE, CP_STAGE_CO_FIRST, CP_STAGE_CO_LAST,
)

STAGES = {
    "co":         CO_STAGE,
    "ep":         EP_STAGE,
    "cp":         CP_STAGE_CO_FIRST,
    "cp-co-last": CP_STAGE_CO_LAST,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate LL catalog JSON")
    parser.add_argument("--stage", choices=list(STAGES), required=True,
                        help="Which stage to generate (co | ep | cp | cp-co-last)")
    parser.add_argument("--moves", required=True,
                        help="Comma-separated move list, e.g. R,R-,R++,R--,U,U-")
    parser.add_argument("--max-depth", type=int, required=True,
                        help="Maximum solution depth to search")
    parser.add_argument("--output-dir", default="ll_catalog",
                        help="Directory for output JSON (default: ll_catalog/)")
    args = parser.parse_args()

    stage = STAGES[args.stage]
    move_set = [m.strip() for m in args.moves.split(",") if m.strip()]
    output_dir = Path(args.output_dir)

    print(f"Building {args.stage} catalog "
          f"(max_depth={args.max_depth}, {len(move_set)} moves)…")
    builder = CatalogBuilder(stage, move_set, args.max_depth)
    catalog = builder.build()

    out_path = output_dir / f"{args.stage}.json"
    catalog.save(out_path)
    print(f"✓  {len(catalog.cases)} cases → {out_path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Verify CLI works**

```bash
cd /home/bjafl/source/rubiks
python scripts/gen_ll_catalog.py --stage co --moves "R,R-,U,U-" --max-depth 5 --output-dir /tmp/ll_test
```

Expected output:
```
Building co catalog (max_depth=5, 4 moves)…
✓  16 cases → /tmp/ll_test/co.json
```

Then spot-check JSON:
```bash
python -c "
import json
d = json.load(open('/tmp/ll_test/co.json'))
print('stage:', d['stage'])
print('cases:', len(d['cases']))
c = d['cases'][0]
print('first case_id:', c['case_id'])
print('auf_variants count:', len(c['auf_variants']))
print('canonical_state:', c['canonical_state'])
"
```

Expected: stage=co, 16 cases, 5 auf_variants per case, canonical_state has "co" key.

- [ ] **Step 7: Add `ll_catalog/` to `.gitignore`**

Open `.gitignore` and add:

```
# Generated LL catalog data (run scripts/gen_ll_catalog.py to regenerate)
ll_catalog/
```

- [ ] **Step 8: Run full test suite**

```bash
python -m pytest tests/ -v --tb=short 2>&1 | tail -30
```

Expected: all tests pass.

- [ ] **Step 9: Commit**

```bash
git add megaminx/ll_catalog.py scripts/gen_ll_catalog.py .gitignore tests/test_ll_catalog.py
git commit -m "feat: add StageCatalog serialization and gen_ll_catalog.py CLI"
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] `LLStage` with 6 boolean flags — Task 1
- [x] Pre-built stages CO, EP, CP_CO_FIRST, CP_CO_LAST — Task 1
- [x] `Solution`, `Case`, `StageCatalog` dataclasses — Task 1
- [x] AUF canonicalization via ring-shift — Task 2
- [x] CO enumeration: 3⁵ with sum≡0 mod 3, exclude identity — Task 3
- [x] EP enumeration: even permutations of LL_EDGE_SLOTS, exclude identity — Task 3
- [x] CP enumeration: even permutations of LL_CORNER_SLOTS, exclude identity — Task 3
- [x] `LLStage.is_solved`: checks solve/require flags + non-LL intact — Task 4
- [x] DFS with face-consecutive pruning — Task 4
- [x] `CatalogBuilder.build()` → assembles Case with 5 auf_variants + sorted solutions — Task 5
- [x] `case_id` format `co_003` etc. — Task 5
- [x] JSON serialization/deserialization — Task 6
- [x] CLI `scripts/gen_ll_catalog.py` — Task 6
- [x] `.gitignore` for `ll_catalog/` — Task 6

**Spec tests covered:**
| Spec test | Task |
|-----------|------|
| `test_co_case_count` (16) | 3 |
| `test_ep_case_count` (5) | 3 |
| `test_auf_canonical_stable` | 2 |
| `test_auf_5_variants` | 2 |
| `test_solutions_solve_case` | 5 |
| `test_solutions_preserve_nll` | 5 |
| `test_solutions_sorted_by_length` | 4 |
| `test_catalog_roundtrip` | 6 |
