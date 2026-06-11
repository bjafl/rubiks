# LL Catalog — Case Enumeration and Solution Search Design

## Goal

Build a pipeline that enumerates all last-layer (LL) cases for each substep (CO, EP, CP), reduces them to equivalence classes via AUF-symmetry, and generates an exhaustive catalog of all solving sequences up to a configurable depth. Output is both a Python module and JSON files on disk.

## Scope

This spec covers **steps 1 and 2** of a larger LL optimizer pipeline:
1. Case enumeration with symmetry reduction (AUF-canonicalization)
2. Exhaustive solution search per case (DFS to `max_depth`)

Steps 3–5 (memorability annotation, set cover, statistics) are a separate future spec.

**Method context:** Designed for Petrus-based solve with EOLL-skip, so EO for LL edges is always 0 entering the LL stage. The stage definition system is order-agnostic — any ordering (CO→EP→CP or EP→CP→CO etc.) is supported by configuring `require_*` flags.

**Key constraint:** CP algorithms on Megaminx twist corners (+1 per piece in a 3-cycle). This means:
- In the traditional order **EP→CP→CO**, CP-stage has `require_co_solved=False` — CO is fixed last, after CP disturbs it.
- In the **CO→EP→CP** order, CP-stage sets `require_co_solved=True` — the DFS search will only collect CP algorithms that happen to preserve CO (more restrictive, but such algorithms exist).

---

## Architecture

### `LLStage`

Declares what a substep solves and what it must preserve:

```python
@dataclass
class LLStage:
    name: str                    # "co", "ep", "cp"
    solve_co: bool               # this stage fixes LL corner orientations
    solve_ep: bool               # this stage fixes LL edge permutation + orientation
    solve_cp: bool               # this stage fixes LL corner permutation
    require_co_solved: bool      # CO must already be solved in input state
    require_ep_solved: bool      # EP+EO must already be solved in input state
    require_cp_solved: bool      # CP must already be solved in input state
```

Pre-built stage instances for CO → EP → CP ordering:

| Stage | `solve_*` | `require_*` |
|-------|-----------|-------------|
| CO    | `solve_co=True` | none |
| EP    | `solve_ep=True` | `require_co_solved=True` |
| CP (CO first) | `solve_cp=True` | `require_co_solved=True, require_ep_solved=True` |
| CP (CO last)  | `solve_cp=True` | `require_ep_solved=True` |

### `CatalogBuilder`

```python
class CatalogBuilder:
    def __init__(self, stage: LLStage, move_set: list[str], max_depth: int): ...
    def build(self) -> StageCatalog: ...
```

Internal flow:
1. Enumerate all valid LL input states for this stage (mathematical, not BFS)
2. AUF-canonicalize → collect unique cases
3. DFS per case → collect all solutions up to `max_depth`
4. Return `StageCatalog`; serialize to JSON on disk

### Data classes

```python
@dataclass
class Solution:
    moves: list[str]       # e.g. ["R", "U++", "R-", "U-", "R", "U-", "R-"]
    length: int

@dataclass
class Case:
    case_id: str           # e.g. "co_003"
    canonical_state: dict  # {"co": [0,1,2,0,2]}
    auf_variants: list[dict]  # all 5 AUF forms (canonical + 4 rotations), explicit
    solutions: list[Solution]  # sorted shortest-first

@dataclass
class StageCatalog:
    stage: str
    move_set: list[str]
    max_depth: int
    cases: list[Case]
```

### Files

| File | Action | Responsibility |
|------|--------|---------------|
| `megaminx/ll_catalog.py` | Create | `LLStage`, `CatalogBuilder`, `Case`, `Solution`, `StageCatalog` |
| `tests/test_ll_catalog.py` | Create | Unit tests for enumeration, canonicalization, search |
| `scripts/gen_ll_catalog.py` | Create | CLI entry point |
| `ll_catalog/co.json` | Generated | CO catalog output |
| `ll_catalog/ep.json` | Generated | EP catalog output |
| `ll_catalog/cp.json` | Generated | CP catalog output |

`ll_catalog/` should be added to `.gitignore` (generated data).

---

## Section 1: Case Enumeration

### LL piece slots (from `cube.py`)

```python
LL_CORNER_SLOTS = (0, 4, 7, 18, 19)
LL_EDGE_SLOTS   = (4, 8, 27, 28, 29)
```

### Valid input states per stage

States are enumerated mathematically — no BFS needed:

**CO stage** — iterate over all `(a,b,c,d,e) ∈ {0,1,2}⁵` where `sum ≡ 0 mod 3`:
- 81 raw states (including identity). Exclude identity (all-zero) = 80 non-trivial.

**EP stage** (with EOLL-skip → EO is always 0) — iterate over all even permutations of `LL_EDGE_SLOTS`:
- 5!/2 = 60 states. Exclude identity = 59 non-trivial.

**CP stage** — iterate over all even permutations of `LL_CORNER_SLOTS`:
- 5!/2 = 60 states. Exclude identity = 59 non-trivial.
- Note: CP algorithms on Megaminx twist corners (+1 per piece per 3-cycle). For CO-first ordering, the catalog searches for CP algs that also preserve CO (more restrictive). For CO-last ordering, CP has no CO preservation requirement.

### AUF-canonicalization

A U-rotation by `k` steps permutes the 5 LL corners and 5 LL edges in ring order.
Two LL states are AUF-equivalent if one is a U^k rotation of the other for some k ∈ {0,1,2,3,4}.

```python
def auf_canonical(ll_co, ll_ep, ll_cp) -> tuple:
    variants = [apply_auf_rotation(ll_co, ll_ep, ll_cp, k) for k in range(5)]
    return min(variants)  # lexicographically smallest tuple = canonical representative
```

`apply_auf_rotation(k)` permutes indices in ring order:
- Corner ring order (from `NEIGHBORS["U"]`): F→L→BL→BR→R mapped to slots (18,4,0,7,19) 
- Edge ring order: same 5-fold cycle on LL_EDGE_SLOTS

**Expected case counts after AUF reduction:**

| Stage | Raw states | Expected cases |
|-------|-----------|----------------|
| CO | 81 | 16 (matches docs) |
| EP | 60 | 12 (Burnside: 60/5 = 12; identity orbit has size 5) |
| CP | 60 | ~12 (Burnside: 60/5 = 12) |

---

## Section 2: Solution Search

### Strategy: DFS to `max_depth`

For each case's canonical state, run a depth-limited DFS from that state toward the solved goal:

```python
def find_solutions(
    start: MegaminxState,
    stage: LLStage,
    move_set: list[str],
    max_depth: int,
) -> list[Solution]:
    solutions = []
    _dfs(start, stage, move_set, max_depth, path=[], solutions=solutions)
    return solutions

def _dfs(state, stage, moves, depth_left, path, solutions):
    if stage.is_solved(state):
        solutions.append(Solution(moves=list(path), length=len(path)))
        return  # don't descend further — solution found
    if depth_left == 0:
        return
    last_face = path[-1].rstrip("-+") if path else None
    for move in moves:
        if move.rstrip("-+") == last_face:
            continue  # pruning: no two moves on same face in a row
        new_state = apply_move(state, move)
        _dfs(new_state, stage, moves, depth_left - 1, path + [move], solutions)
```

### `stage.is_solved(state)`

Checks:
1. All components this stage solves are in solved position
2. All components required to be pre-solved are still intact (preservation check)
3. All non-LL pieces are solved (checked by comparing against `SOLVED` for non-LL indices)

For pure LL move sets (`⟨R, U⟩`), condition 3 is always satisfied and costs nothing. For wider sets (`⟨R, U, F⟩`), condition 3 filters sequences where non-LL pieces were disturbed.

### Pruning

- No two moves on the same face consecutively (shown above)
- Solutions are collected without duplicate-sequence detection; deduplication applied post-DFS

### Performance

| Stage | Cases | Moves in `⟨R, U⟩` | DFS depth 13 | Est. time |
|-------|-------|--------------------|--------------|-----------|
| CO | 16 | 8 | feasible | < 1 min |
| EP | 5 | 8 | feasible | < 10 sec |
| CP | ~12 | 8 | feasible | < 1 min |

`⟨R, U, F⟩` (12 moves) at depth 15: expected < 5 min total on a modern CPU.

---

## Output Format

### JSON schema (`ll_catalog/co.json`)

```json
{
  "stage": "co",
  "move_set": ["R", "R-", "R++", "R--", "U", "U-"],
  "max_depth": 13,
  "cases": [
    {
      "case_id": "co_003",
      "canonical_state": {"co": [0, 1, 2, 0, 2]},
      "auf_variants": [
        {"co": [0, 1, 2, 0, 2]},
        {"co": [2, 0, 1, 2, 0]},
        {"co": [0, 2, 0, 1, 2]},
        {"co": [2, 0, 2, 0, 1]},
        {"co": [1, 2, 0, 2, 0]}
      ],
      "solutions": [
        {"moves": ["R", "U++", "R-", "U-", "R", "U-", "R-"], "length": 7},
        {"moves": ["R", "U", "R-", "U", "R", "U--", "R-"], "length": 7}
      ]
    }
  ]
}
```

`auf_variants` always contains all 5 forms (k=0 is canonical), explicit in JSON so step 3+4+5 can use them without reimporting cube code.

### CLI

```bash
python scripts/gen_ll_catalog.py --stage co --moves "R,R-,R++,R--,U,U-" --max-depth 13
python scripts/gen_ll_catalog.py --stage ep --moves "R,R-,R++,R--,U,U-" --max-depth 13
python scripts/gen_ll_catalog.py --stage cp --moves "R,R-,R++,R--,U,U-" --max-depth 13
# Each writes to ll_catalog/<stage>.json
```

---

## Testing Strategy

| Test | What it verifies |
|------|-----------------|
| `test_co_case_count` | Exactly 16 CO cases after AUF reduction |
| `test_ep_case_count` | Exactly 12 EP cases |
| `test_auf_canonical_stable` | `auf_canonical(canonical)` returns same state |
| `test_auf_5_variants` | Every case has exactly 5 AUF variants |
| `test_solutions_solve_case` | Every solution in catalog applied to its case reaches solved |
| `test_solutions_preserve_nll` | Every solution leaves non-LL pieces untouched |
| `test_solutions_preserve_prior` | EP solutions preserve CO; CP solutions preserve CO+EP |
| `test_known_co9_in_catalog` | CO9 alg appears in its case's solution list |
| `test_known_sune_in_catalog` | Sune appears in CO catalog |
| `test_solutions_sorted_by_length` | `solutions[0].length <= solutions[-1].length` |
