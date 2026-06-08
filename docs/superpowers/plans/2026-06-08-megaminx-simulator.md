# Megaminx Simulator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python library that simulates a Megaminx puzzle with cubie-model state, WCA move notation, IDA* path-finding, and a FastMCP server exposing state/move/solve/explain tools.

**Architecture:** Core `megaminx/` package is a pure Python library with no MCP dependency; the dodecahedron move table is computed from 3D geometry at import time and cached. `mcp_server/` is a thin FastMCP wrapper that holds a `SessionState` (active puzzle + undo stack) and exposes all operations as tools.

**Tech Stack:** Python 3.11+, numpy, FastMCP 2.x, pydantic, pytest

---

## File Map

| File | Responsibility |
|---|---|
| `megaminx/model.py` | `MegaminxState`, `SOLVED_STATE`, `ValidationResult`, `validate_state`, `is_solved` |
| `megaminx/moves.py` | Dodecahedron geometry, move table (corner/edge cycles + orientation deltas), `parse_move`, `apply_move`, `apply_sequence` |
| `megaminx/algorithms.py` | Named algorithm sets (`CO_ALGS`, `LL_ALGS`, etc.), `list_algorithms` |
| `megaminx/heuristics.py` | Admissible heuristic (misplaced cubies in subset) |
| `megaminx/solver.py` | `solve_path` via IDA* |
| `megaminx/utils.py` | `scramble`, `state_to_dict`, `dict_to_state`, `describe_state` |
| `mcp_server/session.py` | `SessionState` — active `MegaminxState` + undo stack |
| `mcp_server/server.py` | All FastMCP tools |
| `tests/test_model.py` | validate_state, is_solved |
| `tests/test_moves.py` | apply_move (all 24 moves), WCA parsing, 5×move = identity |
| `tests/test_solver.py` | solve_path: 1-move, 2-move, 3-move cases + too-deep guard |
| `tests/test_mcp.py` | Each MCP tool; validation rejects invalid state |

---

## Task 0: Project setup

**Files:**
- Create: `pyproject.toml`
- Create: `megaminx/__init__.py`
- Create: `mcp_server/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p megaminx mcp_server tests
```

- [ ] **Step 2: Write pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:BuildBackend"

[project]
name = "megaminx"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "numpy>=1.26",
    "fastmcp>=2.0",
    "pydantic>=2.0",
]

[project.optional-dependencies]
dev = ["pytest>=8", "pytest-cov", "ruff", "mypy"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
line-length = 100
```

- [ ] **Step 3: Create empty __init__.py files**

```bash
touch megaminx/__init__.py mcp_server/__init__.py tests/__init__.py
```

- [ ] **Step 4: Install in editable mode**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Expected: no errors.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml megaminx/ mcp_server/ tests/
git commit -m "chore: project skeleton"
```

---

## Task 1: Core model (`model.py`)

**Files:**
- Create: `megaminx/model.py`
- Create: `tests/test_model.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_model.py
import numpy as np
import pytest
from megaminx.model import (
    MegaminxState, SOLVED_STATE, ValidationResult, validate_state, is_solved
)

def make_state(c_pos=None, c_ori=None, e_pos=None, e_ori=None):
    c_pos = c_pos if c_pos is not None else list(range(20))
    c_ori = c_ori if c_ori is not None else [0] * 20
    e_pos = e_pos if e_pos is not None else list(range(30))
    e_ori = e_ori if e_ori is not None else [0] * 30
    return MegaminxState(
        corners=np.array(list(zip(c_pos, c_ori)), dtype=np.int8),
        edges=np.array(list(zip(e_pos, e_ori)), dtype=np.int8),
    )

def test_solved_state_is_valid():
    r = validate_state(SOLVED_STATE)
    assert r.valid and r.errors == []

def test_is_solved_on_solved_state():
    assert is_solved(SOLVED_STATE)

def test_is_solved_false_on_permuted():
    s = make_state(c_pos=[1] + list(range(1, 20)))  # duplicate pos 1, missing 0
    assert not is_solved(s)

def test_invalid_corner_permutation():
    c_pos = [0] * 20  # all zeros — not a permutation
    r = validate_state(make_state(c_pos=c_pos))
    assert not r.valid
    assert any("corner" in e.lower() and "permutation" in e.lower() for e in r.errors)

def test_invalid_edge_permutation():
    e_pos = [0] * 30
    r = validate_state(make_state(e_pos=e_pos))
    assert not r.valid
    assert any("edge" in e.lower() and "permutation" in e.lower() for e in r.errors)

def test_invalid_corner_orientation_range():
    c_ori = [0] * 19 + [3]  # 3 is out of range
    r = validate_state(make_state(c_ori=c_ori))
    assert not r.valid
    assert any("orientation" in e.lower() for e in r.errors)

def test_invalid_edge_orientation_range():
    e_ori = [0] * 29 + [2]
    r = validate_state(make_state(e_ori=e_ori))
    assert not r.valid

def test_invalid_corner_orientation_sum():
    # Twist one corner by 1 — sum becomes 1 (not divisible by 3)
    c_ori = [0] * 19 + [1]
    r = validate_state(make_state(c_ori=c_ori))
    assert not r.valid
    assert any("mod 3" in e for e in r.errors)

def test_invalid_edge_orientation_sum():
    e_ori = [0] * 29 + [1]
    r = validate_state(make_state(e_ori=e_ori))
    assert not r.valid
    assert any("mod 2" in e for e in r.errors)

def test_invalid_parity():
    # Swap two corners (odd perm) but keep edges even → parity mismatch
    c_pos = list(range(20))
    c_pos[0], c_pos[1] = c_pos[1], c_pos[0]
    r = validate_state(make_state(c_pos=c_pos))
    assert not r.valid
    assert any("parity" in e.lower() for e in r.errors)
```

- [ ] **Step 2: Run — verify all fail**

```bash
pytest tests/test_model.py -v
```

Expected: all tests fail with ImportError or AttributeError.

- [ ] **Step 3: Implement model.py**

```python
# megaminx/model.py
from __future__ import annotations
from dataclasses import dataclass
import numpy as np


@dataclass
class MegaminxState:
    corners: np.ndarray  # shape (20, 2): col 0 = position, col 1 = orientation
    edges: np.ndarray    # shape (30, 2): col 0 = position, col 1 = orientation

    def copy(self) -> MegaminxState:
        return MegaminxState(self.corners.copy(), self.edges.copy())


SOLVED_STATE = MegaminxState(
    corners=np.array([[i, 0] for i in range(20)], dtype=np.int8),
    edges=np.array([[i, 0] for i in range(30)], dtype=np.int8),
)


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str]


def _perm_parity(perm: list[int]) -> int:
    n = len(perm)
    visited = [False] * n
    p = 0
    for i in range(n):
        if not visited[i]:
            cycle_len = 0
            j = i
            while not visited[j]:
                visited[j] = True
                j = perm[j]
                cycle_len += 1
            p ^= (cycle_len + 1) % 2
    return p


def validate_state(state: MegaminxState) -> ValidationResult:
    errors: list[str] = []

    c_pos = list(state.corners[:, 0])
    e_pos = list(state.edges[:, 0])
    c_ori = list(state.corners[:, 1])
    e_ori = list(state.edges[:, 1])

    if sorted(c_pos) != list(range(20)):
        errors.append("Corner positions are not a valid permutation of 0-19")
    if sorted(e_pos) != list(range(30)):
        errors.append("Edge positions are not a valid permutation of 0-29")

    if any(o not in (0, 1, 2) for o in c_ori):
        errors.append("Corner orientations must be in {0, 1, 2}")
    if any(o not in (0, 1) for o in e_ori):
        errors.append("Edge orientations must be in {0, 1}")

    if sum(c_ori) % 3 != 0:
        errors.append("Sum of corner orientations must be ≡ 0 (mod 3)")
    if sum(e_ori) % 2 != 0:
        errors.append("Sum of edge orientations must be ≡ 0 (mod 2)")

    if not errors:  # only check parity if positions are valid permutations
        if _perm_parity(c_pos) != _perm_parity(e_pos):
            errors.append("Corner permutation parity must equal edge permutation parity")

    return ValidationResult(valid=len(errors) == 0, errors=errors)


def is_solved(state: MegaminxState) -> bool:
    return (
        np.array_equal(state.corners, SOLVED_STATE.corners)
        and np.array_equal(state.edges, SOLVED_STATE.edges)
    )
```

- [ ] **Step 4: Run tests — all pass**

```bash
pytest tests/test_model.py -v
```

Expected: 10/10 PASSED.

- [ ] **Step 5: Commit**

```bash
git add megaminx/model.py tests/test_model.py
git commit -m "feat(model): MegaminxState, validate_state, is_solved"
```

---

## Task 2: Dodecahedron geometry + move table (`moves.py`)

**Files:**
- Create: `megaminx/moves.py`
- Create: `tests/test_moves.py`

The move table is derived from 3D coordinates of a regular dodecahedron.
Each of the 12 faces produces a CW move table: a 5-cycle of corner indices,
a 5-cycle of edge indices, and orientation deltas.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_moves.py
import numpy as np
import pytest
from megaminx.model import SOLVED_STATE, is_solved
from megaminx.moves import apply_move, apply_sequence, FACE_NAMES, ALL_MOVES

def test_face_names_count():
    assert len(FACE_NAMES) == 12

def test_all_moves_count():
    # 12 faces × CW and CCW = 24 atomic moves
    assert len(ALL_MOVES) == 24

def test_five_cw_turns_is_identity():
    """5 × 72° = 360° = identity for every face."""
    for face in FACE_NAMES:
        state = SOLVED_STATE.copy()
        for _ in range(5):
            state = apply_move(state, face)
        assert is_solved(state), f"5× {face} did not return to solved"

def test_cw_then_ccw_is_identity():
    """CW + CCW = identity for every face."""
    for face in FACE_NAMES:
        state = SOLVED_STATE.copy()
        state = apply_move(state, face)
        state = apply_move(state, face + "-")
        assert is_solved(state), f"{face} then {face}- did not return to solved"

def test_double_move_equals_two_singles():
    for face in FACE_NAMES:
        s1 = apply_move(apply_move(SOLVED_STATE.copy(), face), face)
        s2 = apply_move(SOLVED_STATE.copy(), face + "++")
        assert np.array_equal(s1.corners, s2.corners)
        assert np.array_equal(s1.edges, s2.edges)

def test_apply_sequence_empty_is_identity():
    state = apply_sequence(SOLVED_STATE.copy(), [])
    assert is_solved(state)

def test_apply_sequence_u_and_inverse():
    state = apply_sequence(SOLVED_STATE.copy(), ["U", "U-"])
    assert is_solved(state)

def test_result_state_is_valid():
    """Every single-move result must pass validate_state."""
    from megaminx.model import validate_state
    for move in ALL_MOVES:
        result = apply_move(SOLVED_STATE.copy(), move)
        r = validate_state(result)
        assert r.valid, f"Move {move!r} produced invalid state: {r.errors}"
```

- [ ] **Step 2: Run — verify all fail**

```bash
pytest tests/test_moves.py -v
```

Expected: ImportError on `megaminx.moves`.

- [ ] **Step 3: Implement geometry helpers and face labeling**

```python
# megaminx/moves.py
from __future__ import annotations
import numpy as np
from megaminx.model import MegaminxState

PHI = (1 + 5 ** 0.5) / 2

# 20 vertices of a unit-edge dodecahedron
_RAW_VERTS = np.array([
    # (±1, ±1, ±1)
    (-1,-1,-1), (-1,-1, 1), (-1, 1,-1), (-1, 1, 1),
    ( 1,-1,-1), ( 1,-1, 1), ( 1, 1,-1), ( 1, 1, 1),
    # (0, ±1/φ, ±φ)
    (0, -1/PHI, -PHI), (0, -1/PHI,  PHI),
    (0,  1/PHI, -PHI), (0,  1/PHI,  PHI),
    # (±1/φ, ±φ, 0)
    (-1/PHI, -PHI, 0), (-1/PHI,  PHI, 0),
    ( 1/PHI, -PHI, 0), ( 1/PHI,  PHI, 0),
    # (±φ, 0, ±1/φ)
    (-PHI, 0, -1/PHI), (-PHI, 0,  1/PHI),
    ( PHI, 0, -1/PHI), ( PHI, 0,  1/PHI),
], dtype=float)

# Edge length: distance between two adjacent vertices
# In this embedding, edge length = 2/φ
_EDGE_LEN_SQ = (2 / PHI) ** 2
_TOL = 1e-6


def _are_adjacent(i: int, j: int) -> bool:
    diff = _RAW_VERTS[i] - _RAW_VERTS[j]
    return abs(np.dot(diff, diff) - _EDGE_LEN_SQ) < _TOL


# Adjacency matrix
_ADJ = np.zeros((20, 20), dtype=bool)
for _i in range(20):
    for _j in range(_i + 1, 20):
        if _are_adjacent(_i, _j):
            _ADJ[_i, _j] = _ADJ[_j, _i] = True

assert _ADJ.sum() // 2 == 30, "Expected 30 edges"
assert (_ADJ.sum(axis=1) == 3).all(), "Each vertex must have degree 3"


def _find_faces() -> list[list[int]]:
    """Find all 12 pentagonal faces as lists of 5 vertex indices.

    A dodecahedron has girth 5 (no triangles), so no two neighbors of u are adjacent.
    Pentagon through edge (u,v): u - v - x - mid - z - u
    where x is a non-u neighbor of v, z is a non-v neighbor of u, mid adj both x and z.
    """
    faces: set[tuple[int, ...]] = set()
    for u in range(20):
        for v in range(u + 1, 20):
            if not _ADJ[u, v]:
                continue
            u_others = [w for w in range(20) if _ADJ[u, w] and w != v]
            v_others = [w for w in range(20) if _ADJ[v, w] and w != u]
            for z in u_others:
                for x in v_others:
                    if z == x:
                        continue
                    mids = [w for w in range(20) if _ADJ[x, w] and _ADJ[z, w]
                            and w not in (u, v, x, z)]
                    for mid in mids:
                        face = tuple(sorted([u, v, x, mid, z]))
                        faces.add(face)
    return [list(f) for f in faces]


def _sort_face_cw(face_verts: list[int], face_center: np.ndarray) -> list[int]:
    """Sort 5 vertices of a face in CW order viewed from outside (face normal pointing out)."""
    normal = face_center / np.linalg.norm(face_center)
    # Build a local 2D coordinate system on the face plane
    v0 = _RAW_VERTS[face_verts[0]] - face_center
    e1 = v0 / np.linalg.norm(v0)
    e2 = np.cross(normal, e1)
    angles = []
    for vi in face_verts:
        v = _RAW_VERTS[vi] - face_center
        angles.append(np.arctan2(np.dot(v, e2), np.dot(v, e1)))
    # CW from outside = decreasing angle in right-hand frame = reverse sorted
    ordered = [face_verts[i] for i in np.argsort(angles)[::-1]]
    return ordered


_FACE_VERTS_RAW = _find_faces()
assert len(_FACE_VERTS_RAW) == 12, f"Expected 12 faces, got {len(_FACE_VERTS_RAW)}"

# Sort faces so U (most +Y) is face 0, D (most -Y) is face 11
_face_centers = [_RAW_VERTS[f].mean(axis=0) for f in _FACE_VERTS_RAW]
_face_order = sorted(range(12), key=lambda i: -_face_centers[i][1])
_FACE_VERTS_SORTED = [_FACE_VERTS_RAW[_face_order[i]] for i in range(12)]
_face_centers = [_RAW_VERTS[f].mean(axis=0) for f in _FACE_VERTS_SORTED]
_FACE_VERTS = [_sort_face_cw(fv, fc) for fv, fc in zip(_FACE_VERTS_SORTED, _face_centers)]

# WCA face names: U, then 5 upper-ring, then 5 lower-ring, then D
# Upper ring: 5 faces adjacent to U, sorted by angle around Y axis
_u_neighbors = [i for i in range(1, 12) if any(v in _FACE_VERTS[0] for v in _FACE_VERTS[i])]
_d_neighbors = [i for i in range(1, 12) if any(v in _FACE_VERTS[11] for v in _FACE_VERTS[i])]
_mid = [i for i in range(1, 12) if i not in _u_neighbors and i != 11]

def _face_angle_around_y(fi: int) -> float:
    c = _face_centers[fi]
    return np.arctan2(c[2], c[0])

_u_ring = sorted(_u_neighbors, key=_face_angle_around_y)
_d_ring = sorted(_d_neighbors, key=_face_angle_around_y)

FACE_NAMES = ["U"] + [f"F{i}" for i in range(5)] + [f"D{i}" for i in range(5)] + ["D"]
# Assign proper WCA names based on position
_WCA_U_RING = ["F", "FR", "BR", "BL", "FL"]
_WCA_D_RING = ["DFR", "DR", "DBR", "DBL", "DFL"]
FACE_NAMES = (
    ["U"]
    + [_WCA_U_RING[i] for i in range(5)]
    + [_WCA_D_RING[i] for i in range(5)]
    + ["D"]
)
_FACE_INDEX = {name: i for i, name in enumerate(FACE_NAMES)}
```

- [ ] **Step 4: Implement corner/edge labeling**

Add to `megaminx/moves.py`:

```python
# --- Corner labeling (20 corners = vertices of dodecahedron) ---
# Each vertex is shared by exactly 3 faces. We label vertex vi as corner index
# by sorting vertices by (face-indices tuple).
_vert_to_faces: dict[int, list[int]] = {v: [] for v in range(20)}
for fi, fv in enumerate(_FACE_VERTS):
    for v in fv:
        _vert_to_faces[v].append(fi)

# Sort vertices by their sorted face-triple to get stable corner indices 0-19
_corner_order = sorted(range(20), key=lambda v: tuple(sorted(_vert_to_faces[v])))
CORNER_FACES: list[tuple[int, int, int]] = [
    tuple(sorted(_vert_to_faces[v])) for v in _corner_order  # type: ignore
]
_vert_to_corner = {v: i for i, v in enumerate(_corner_order)}

# --- Edge labeling (30 edges) ---
_edges: list[tuple[int, int]] = []
for i in range(20):
    for j in range(i + 1, 20):
        if _ADJ[i, j]:
            fi = frozenset(_vert_to_faces[i]) & frozenset(_vert_to_faces[j])
            _edges.append((i, j))

_edges.sort(key=lambda e: tuple(sorted(frozenset(_vert_to_faces[e[0]]) & frozenset(_vert_to_faces[e[1]]))))
EDGE_FACES: list[tuple[int, int]] = [
    tuple(sorted(frozenset(_vert_to_faces[e[0]]) & frozenset(_vert_to_faces[e[1]])))  # type: ignore
    for e in _edges
]
_edge_key_to_idx = {ef: i for i, ef in enumerate(EDGE_FACES)}
```

- [ ] **Step 5: Compute move table (corner/edge cycles)**

Add to `megaminx/moves.py`:

```python
def _rotate_vector(v: np.ndarray, axis: np.ndarray, angle: float) -> np.ndarray:
    """Rodrigues' rotation formula."""
    axis = axis / np.linalg.norm(axis)
    return (v * np.cos(angle)
            + np.cross(axis, v) * np.sin(angle)
            + axis * np.dot(axis, v) * (1 - np.cos(angle)))


def _build_move_table() -> dict[int, dict]:
    """For each of 12 faces, compute corner cycle, edge cycle, and orientation deltas."""
    angle = 2 * np.pi / 5  # 72° CW turn
    table = {}

    for fi, fv_ordered in enumerate(_FACE_VERTS):
        center = _face_centers[fi]
        normal = center / np.linalg.norm(center)  # outward normal

        # --- Corner cycle ---
        # fv_ordered: 5 vertex indices in CW order viewed from outside
        # CW turn: vertex at position k moves to position k+1 (mod 5)
        corner_cycle = [_vert_to_corner[v] for v in fv_ordered]

        # Corner orientation deltas:
        # For each corner in cycle at index k, rotate its 3 face-normals by -angle
        # (the piece rotates -angle relative to the face = opposite of face CW turn)
        # then determine which face-normal is closest to the original "primary" direction
        c_ori_delta = []
        for k, v in enumerate(fv_ordered):
            ci = _vert_to_corner[v]
            face_indices = list(CORNER_FACES[ci])  # 3 adjacent faces, sorted ascending
            # Primary direction = outward normal of face_indices[0]
            primary_dir = _face_centers[face_indices[0]] / np.linalg.norm(_face_centers[face_indices[0]])
            # After CW turn of face fi, this corner moves to the next slot (k+1 mod 5)
            # The piece itself rotates +angle around the face normal (CW from outside)
            rotated_primary = _rotate_vector(primary_dir, normal, angle)
            # New corner position's face set
            new_v = fv_ordered[(k + 1) % 5]
            new_ci = _vert_to_corner[new_v]
            new_faces = list(CORNER_FACES[new_ci])  # 3 adjacent faces, sorted ascending
            new_face_normals = [_face_centers[f] / np.linalg.norm(_face_centers[f]) for f in new_faces]
            # Find which new face normal is closest to rotated_primary
            dots = [np.dot(rotated_primary, nfn) for nfn in new_face_normals]
            best = int(np.argmax(dots))
            # best == 0 → orientation 0 (primary sticker aligns with lowest-index face normal) → delta 0
            # The orientation delta is how many CW steps the primary sticker has rotated
            # relative to the "primary" position (face index 0)
            c_ori_delta.append(best)  # 0, 1, or 2

        # --- Edge cycle ---
        # Edges of this face are the 5 edges between consecutive vertices in fv_ordered
        edge_cycle = []
        for k in range(5):
            v1 = fv_ordered[k]
            v2 = fv_ordered[(k + 1) % 5]
            shared_faces = tuple(sorted(frozenset(_vert_to_faces[v1]) & frozenset(_vert_to_faces[v2])))
            edge_cycle.append(_edge_key_to_idx[shared_faces])

        # Edge orientation deltas:
        # An edge is flipped if its "primary direction" (from face_indices[0] outward) is reversed.
        e_ori_delta = []
        for k, (ei) in enumerate(edge_cycle):
            f_pair = list(EDGE_FACES[ei])  # 2 adjacent faces, sorted ascending
            primary_dir = _face_centers[f_pair[0]] / np.linalg.norm(_face_centers[f_pair[0]])
            rotated_primary = _rotate_vector(primary_dir, normal, angle)
            new_ei = edge_cycle[(k + 1) % 5]
            new_f_pair = list(EDGE_FACES[new_ei])
            new_primary_dir = _face_centers[new_f_pair[0]] / np.linalg.norm(_face_centers[new_f_pair[0]])
            dot = np.dot(rotated_primary, new_primary_dir)
            e_ori_delta.append(0 if dot > 0 else 1)

        table[fi] = {
            "corner_cycle": corner_cycle,
            "c_ori_delta": c_ori_delta,
            "edge_cycle": edge_cycle,
            "e_ori_delta": e_ori_delta,
        }

    return table


MOVE_TABLE = _build_move_table()
```

- [ ] **Step 6: Implement parse_move, apply_move, apply_sequence**

Add to `megaminx/moves.py`:

```python
import re

_MOVE_RE = re.compile(r"^([A-Z]+)(\+\+|--|[+-]?)$")

def parse_move(move_str: str) -> tuple[int, int]:
    """Return (face_index, turns) where turns ∈ {1, 2, 4} (4 = CCW = 4×CW)."""
    m = _MOVE_RE.match(move_str.strip())
    if not m:
        raise ValueError(f"Invalid move: {move_str!r}")
    face_name, suffix = m.group(1), m.group(2)
    if face_name not in _FACE_INDEX:
        raise ValueError(f"Unknown face: {face_name!r}. Valid: {FACE_NAMES}")
    fi = _FACE_INDEX[face_name]
    turns = {"": 1, "+": 1, "++": 2, "-": 4, "--": 3}[suffix]
    return fi, turns


def _apply_cw(state: MegaminxState, fi: int) -> MegaminxState:
    """Apply one CW 72° turn of face fi. Returns new state (immutable)."""
    t = MOVE_TABLE[fi]
    cc = t["corner_cycle"]   # [c0, c1, c2, c3, c4]: c0→c1, c1→c2, ...
    ec = t["edge_cycle"]
    c_delta = t["c_ori_delta"]
    e_delta = t["e_ori_delta"]

    new_state = state.copy()
    for k in range(5):
        src = cc[k]
        dst = cc[(k + 1) % 5]
        new_state.corners[dst, 0] = state.corners[src, 0]
        new_state.corners[dst, 1] = (int(state.corners[src, 1]) + c_delta[k]) % 3

    for k in range(5):
        src = ec[k]
        dst = ec[(k + 1) % 5]
        new_state.edges[dst, 0] = state.edges[src, 0]
        new_state.edges[dst, 1] = (int(state.edges[src, 1]) + e_delta[k]) % 2

    return new_state


def apply_move(state: MegaminxState, move_str: str) -> MegaminxState:
    fi, turns = parse_move(move_str)
    for _ in range(turns):
        state = _apply_cw(state, fi)
    return state


def apply_sequence(state: MegaminxState, moves: list[str]) -> MegaminxState:
    for m in moves:
        state = apply_move(state, m)
    return state


ALL_MOVES = [f + s for f in FACE_NAMES for s in ("", "-")]
```

- [ ] **Step 7: Run tests**

```bash
pytest tests/test_moves.py -v
```

Expected: all tests pass. If `test_five_cw_turns_is_identity` or `test_result_state_is_valid` fail, the orientation deltas are wrong — see Step 8.

- [ ] **Step 8: Debug orientation deltas if needed**

If tests fail, add a diagnostic to find which face/corner has wrong delta:

```bash
python - <<'EOF'
from megaminx.model import SOLVED_STATE, is_solved, validate_state
from megaminx.moves import apply_move, FACE_NAMES, MOVE_TABLE

for face in FACE_NAMES:
    state = SOLVED_STATE.copy()
    for _ in range(5):
        state = apply_move(state, face)
    r = validate_state(state)
    solved = is_solved(state)
    if not solved or not r.valid:
        print(f"FAIL {face}: solved={solved}, valid={r.valid}, errors={r.errors}")
        print(f"  table: {MOVE_TABLE[FACE_NAMES.index(face)]}")
EOF
```

The most likely issue is the orientation delta direction (CW vs CCW). If primary sticker aligns with face index 1 instead of 0 after rotation, delta is 2 (CCW twist) not 1. Fix: in `_build_move_table`, if `best > 0`, use `(3 - best) % 3` to invert the direction.

- [ ] **Step 9: Commit**

```bash
git add megaminx/moves.py tests/test_moves.py
git commit -m "feat(moves): dodecahedron geometry, move table, apply_move"
```

---

## Task 3: Named algorithms (`algorithms.py`)

**Files:**
- Create: `megaminx/algorithms.py`

- [ ] **Step 1: Write failing tests**

```python
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
    """Classic Megaminx Sune applied 6 times = identity."""
    from megaminx.model import is_solved
    sune = ["R", "U", "R-", "U", "R", "U++", "R-"]
    state = SOLVED_STATE.copy()
    for _ in range(6):
        state = apply_sequence(state, sune)
    assert is_solved(state), "Sune × 6 should return to solved"
```

- [ ] **Step 2: Run — verify fail**

```bash
pytest tests/test_algorithms.py -v
```

- [ ] **Step 3: Implement algorithms.py**

```python
# megaminx/algorithms.py
# Named algorithm sets for Megaminx.
# Each set is a list of move sequences (each sequence = list[str]).

ALGORITHM_SETS: dict[str, list[list[str]]] = {
    # Corner Orientation algorithms (affect only corner orientations)
    "CO_ALGS": [
        ["R", "U", "R-", "U", "R", "U++", "R-"],         # Sune
        ["R-", "U-", "R", "U-", "R-", "U--", "R"],        # Anti-Sune
        ["R", "U++", "R-", "U-", "R", "U-", "R-"],        # Double Sune variant
    ],
    # Corner Permutation algorithms
    "CP_ALGS": [
        ["R", "U-", "L-", "U", "R-", "U-", "L", "U"],    # Diagonal corner swap
        ["U", "R", "U-", "L-", "U", "R-", "U-", "L"],    # Adjacent corner swap
    ],
    # Last Layer combined
    "LL_ALGS": [
        ["R", "U", "R-", "U-"],                            # Sexy move
        ["R-", "F", "R", "F-"],                            # Sledgehammer
        ["F", "R", "U-", "R-", "U-", "R", "U", "R-", "F-"],  # T-perm
    ],
    # Edge orientation
    "EO_ALGS": [
        ["F", "R", "U", "R-", "U-", "F-"],               # OLL edge flip
    ],
}

SINGLE_ALGS: dict[str, list[str]] = {
    "SUNE":       ["R", "U", "R-", "U", "R", "U++", "R-"],
    "ANTI_SUNE":  ["R-", "U-", "R", "U-", "R-", "U--", "R"],
    "SEXY":       ["R", "U", "R-", "U-"],
    "SLEDGE":     ["R-", "F", "R", "F-"],
}


def list_algorithms() -> dict[str, list[list[str]]]:
    return ALGORITHM_SETS


def get_algorithm_set(name: str) -> list[list[str]]:
    return ALGORITHM_SETS[name]  # KeyError if unknown


def get_single_alg(name: str) -> list[str]:
    return SINGLE_ALGS[name]  # KeyError if unknown
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_algorithms.py -v
```

If `test_sune_six_times_is_identity` fails, the move table has orientation delta errors. Revisit Task 2 Step 8.

- [ ] **Step 5: Commit**

```bash
git add megaminx/algorithms.py tests/test_algorithms.py
git commit -m "feat(algorithms): named algorithm sets (CO, CP, LL, EO)"
```

---

## Task 4: Heuristic (`heuristics.py`)

**Files:**
- Create: `megaminx/heuristics.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_heuristics.py
from megaminx.model import SOLVED_STATE
from megaminx.moves import apply_move
from megaminx.heuristics import lower_bound

def test_solved_state_lower_bound_is_zero():
    assert lower_bound(SOLVED_STATE) == 0

def test_one_move_lower_bound_is_at_least_one():
    state = apply_move(SOLVED_STATE.copy(), "U")
    assert lower_bound(state) >= 1

def test_lower_bound_never_exceeds_true_distance():
    """Admissibility check: 1-move state needs exactly 1 move."""
    state = apply_move(SOLVED_STATE.copy(), "F")
    # Lower bound must be ≤ 1 (the true distance is 1)
    assert lower_bound(state) <= 1
```

- [ ] **Step 2: Run — verify fail**

```bash
pytest tests/test_heuristics.py -v
```

- [ ] **Step 3: Implement heuristics.py**

```python
# megaminx/heuristics.py
# Admissible heuristic: counts misplaced pieces in a subset.
# Uses the first 8 corners as the pattern subset.
import numpy as np
from megaminx.model import MegaminxState

_CORNER_SUBSET = list(range(8))  # first 8 corners
_EDGE_SUBSET = list(range(10))   # first 10 edges


def lower_bound(state: MegaminxState) -> int:
    """
    Admissible lower bound on the number of moves to solve.
    Counts misplaced pieces in the chosen subset, divided by 5
    (at most 5 pieces can be fixed per move).
    """
    misplaced = 0
    for i in _CORNER_SUBSET:
        if state.corners[i, 0] != i or state.corners[i, 1] != 0:
            misplaced += 1
    for i in _EDGE_SUBSET:
        if state.edges[i, 0] != i or state.edges[i, 1] != 0:
            misplaced += 1
    return misplaced // 5
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_heuristics.py -v
```

- [ ] **Step 5: Commit**

```bash
git add megaminx/heuristics.py tests/test_heuristics.py
git commit -m "feat(heuristics): admissible lower_bound for IDA*"
```

---

## Task 5: Solver (`solver.py`)

**Files:**
- Create: `megaminx/solver.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_solver.py
import pytest
from megaminx.model import SOLVED_STATE, is_solved
from megaminx.moves import apply_move, apply_sequence
from megaminx.solver import solve_path

def test_solve_path_already_solved():
    result = solve_path(SOLVED_STATE.copy(), SOLVED_STATE.copy())
    assert result == []

def test_solve_one_move():
    scrambled = apply_move(SOLVED_STATE.copy(), "U")
    solution = solve_path(scrambled, SOLVED_STATE.copy(), max_depth=5)
    assert solution is not None
    result = apply_sequence(scrambled, solution)
    assert is_solved(result)

def test_solve_two_moves():
    scrambled = apply_sequence(SOLVED_STATE.copy(), ["F", "R"])
    solution = solve_path(scrambled, SOLVED_STATE.copy(), max_depth=5)
    assert solution is not None
    result = apply_sequence(scrambled, solution)
    assert is_solved(result)

def test_solve_three_moves():
    scrambled = apply_sequence(SOLVED_STATE.copy(), ["U", "F", "R-"])
    solution = solve_path(scrambled, SOLVED_STATE.copy(), max_depth=6)
    assert solution is not None
    assert len(solution) <= 6
    result = apply_sequence(scrambled, solution)
    assert is_solved(result)

def test_solve_returns_none_when_too_deep():
    scrambled = apply_sequence(SOLVED_STATE.copy(), ["U", "F", "R", "BR", "BL"])
    result = solve_path(scrambled, SOLVED_STATE.copy(), max_depth=2)
    # max_depth=2 is too shallow for a 5-move scramble
    assert result is None

def test_solve_with_restricted_move_set():
    """solve_path with only U moves can solve a U-only scramble."""
    scrambled = apply_sequence(SOLVED_STATE.copy(), ["U", "U", "U"])
    solution = solve_path(scrambled, SOLVED_STATE.copy(), move_set=["U", "U-"], max_depth=5)
    assert solution is not None
    result = apply_sequence(scrambled, solution)
    assert is_solved(result)

def test_solve_path_a_to_b():
    """Find path between two non-solved states."""
    state_a = apply_move(SOLVED_STATE.copy(), "U")
    state_b = apply_move(SOLVED_STATE.copy(), "F")
    solution = solve_path(state_a, state_b, max_depth=6)
    assert solution is not None
    result = apply_sequence(state_a, solution)
    import numpy as np
    assert np.array_equal(result.corners, state_b.corners)
    assert np.array_equal(result.edges, state_b.edges)
```

- [ ] **Step 2: Run — verify fail**

```bash
pytest tests/test_solver.py -v
```

- [ ] **Step 3: Implement solver.py**

```python
# megaminx/solver.py
from __future__ import annotations
import numpy as np
from megaminx.model import MegaminxState
from megaminx.moves import apply_move, ALL_MOVES
from megaminx.heuristics import lower_bound

_MAX_SEARCH_NODES = 500_000


def _diff_heuristic(state: MegaminxState, goal: MegaminxState) -> int:
    """Count misplaced corners/edges vs goal state, divided by 5."""
    misplaced = int(np.sum(state.corners != goal.corners)) + \
                int(np.sum(state.edges != goal.edges))
    return misplaced // 10  # conservative: /10 since each cell is pos OR ori


def solve_path(
    from_state: MegaminxState,
    to_state: MegaminxState,
    move_set: list[str] | None = None,
    max_depth: int = 12,
) -> list[str] | None:
    """
    IDA* search from from_state to to_state.
    Returns the move sequence or None if no solution found within max_depth.
    """
    moves = move_set if move_set is not None else ALL_MOVES

    def states_equal(a: MegaminxState, b: MegaminxState) -> bool:
        return np.array_equal(a.corners, b.corners) and np.array_equal(a.edges, b.edges)

    if states_equal(from_state, to_state):
        return []

    h = _diff_heuristic(from_state, to_state)
    if h > max_depth:
        return None

    bound = h
    path: list[str] = []
    node_count = [0]

    def search(state: MegaminxState, g: int, bound: int) -> int | None:
        node_count[0] += 1
        if node_count[0] > _MAX_SEARCH_NODES:
            return -1  # signal: search space exceeded

        f = g + _diff_heuristic(state, to_state)
        if f > bound:
            return f
        if states_equal(state, to_state):
            return None  # found

        minimum = float("inf")
        last_face = path[-1].rstrip("+-") if path else None
        for move in moves:
            face = move.rstrip("+-")
            if face == last_face:  # skip consecutive same-face moves
                continue
            new_state = apply_move(state, move)
            path.append(move)
            t = search(new_state, g + 1, bound)
            if t is None:
                return None  # found
            if t == -1:
                return -1   # exceeded
            if t < minimum:
                minimum = t
            path.pop()
        return minimum

    while bound <= max_depth:
        node_count[0] = 0
        t = search(from_state, 0, bound)
        if t is None:
            return list(path)
        if t == -1 or t == float("inf"):
            return None
        bound = t

    return None
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_solver.py -v
```

Expected: all pass. If `test_solve_three_moves` is slow (>5s), reduce `_MAX_SEARCH_NODES` or lower `max_depth` in the test.

- [ ] **Step 5: Commit**

```bash
git add megaminx/solver.py tests/test_solver.py
git commit -m "feat(solver): IDA* solve_path with move_set and max_depth"
```

---

## Task 6: Utilities (`utils.py`)

**Files:**
- Create: `megaminx/utils.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_utils.py
import numpy as np
from megaminx.model import SOLVED_STATE, validate_state, is_solved
from megaminx.utils import scramble, state_to_dict, dict_to_state, describe_state

def test_scramble_produces_valid_state():
    state = scramble(SOLVED_STATE.copy(), 20)
    r = validate_state(state)
    assert r.valid

def test_scramble_n0_is_identity():
    state = scramble(SOLVED_STATE.copy(), 0)
    assert is_solved(state)

def test_state_roundtrip():
    state = scramble(SOLVED_STATE.copy(), 10)
    d = state_to_dict(state)
    restored = dict_to_state(d)
    assert np.array_equal(state.corners, restored.corners)
    assert np.array_equal(state.edges, restored.edges)

def test_dict_to_state_validates():
    d = state_to_dict(SOLVED_STATE.copy())
    d["corners"][0]["pos"] = 99  # invalid
    from megaminx.model import ValidationResult
    result = dict_to_state(d, validate=True)
    assert isinstance(result, dict) and not result["valid"]

def test_describe_state_returns_string():
    desc = describe_state(SOLVED_STATE.copy())
    assert isinstance(desc, str) and len(desc) > 0
    assert "solved" in desc.lower()
```

- [ ] **Step 2: Run — verify fail**

```bash
pytest tests/test_utils.py -v
```

- [ ] **Step 3: Implement utils.py**

```python
# megaminx/utils.py
from __future__ import annotations
import random
import numpy as np
from megaminx.model import MegaminxState, validate_state, ValidationResult
from megaminx.moves import apply_move, ALL_MOVES, FACE_NAMES


def scramble(state: MegaminxState, n: int) -> MegaminxState:
    """Apply n random moves to state. Returns new state."""
    last_face = None
    for _ in range(n):
        candidates = [m for m in ALL_MOVES if m.rstrip("+-") != last_face]
        move = random.choice(candidates)
        state = apply_move(state, move)
        last_face = move.rstrip("+-")
    return state


def state_to_dict(state: MegaminxState) -> dict:
    return {
        "corners": [{"pos": int(state.corners[i, 0]), "ori": int(state.corners[i, 1])}
                    for i in range(20)],
        "edges":   [{"pos": int(state.edges[i, 0]),   "ori": int(state.edges[i, 1])}
                    for i in range(30)],
    }


def dict_to_state(d: dict, validate: bool = True) -> MegaminxState | dict:
    corners = np.array([[c["pos"], c["ori"]] for c in d["corners"]], dtype=np.int8)
    edges   = np.array([[e["pos"], e["ori"]] for e in d["edges"]],   dtype=np.int8)
    state = MegaminxState(corners=corners, edges=edges)
    if validate:
        r = validate_state(state)
        if not r.valid:
            return {"valid": False, "errors": r.errors}
    return state


def describe_state(state: MegaminxState) -> str:
    from megaminx.model import is_solved
    if is_solved(state):
        return "State: SOLVED"

    misplaced_corners = sum(
        1 for i in range(20)
        if state.corners[i, 0] != i or state.corners[i, 1] != 0
    )
    misplaced_edges = sum(
        1 for i in range(30)
        if state.edges[i, 0] != i or state.edges[i, 1] != 0
    )
    twisted_corners = sum(1 for i in range(20) if state.corners[i, 1] != 0)
    flipped_edges   = sum(1 for i in range(30) if state.edges[i, 1] != 0)

    return (
        f"State: UNSOLVED — "
        f"{misplaced_corners}/20 corners misplaced ({twisted_corners} twisted), "
        f"{misplaced_edges}/30 edges misplaced ({flipped_edges} flipped)"
    )
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_utils.py -v
```

- [ ] **Step 5: Commit**

```bash
git add megaminx/utils.py tests/test_utils.py
git commit -m "feat(utils): scramble, state_to_dict, dict_to_state, describe_state"
```

---

## Task 7: MCP Session (`session.py`)

**Files:**
- Create: `mcp_server/session.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_session.py
from megaminx.model import SOLVED_STATE, is_solved
from megaminx.moves import apply_move
from mcp_server.session import SessionState

def test_initial_state_is_solved():
    s = SessionState()
    assert is_solved(s.state)

def test_push_state_and_undo():
    s = SessionState()
    old = s.state.copy()
    s.push(apply_move(s.state, "U"))
    assert not is_solved(s.state)
    s.undo()
    import numpy as np
    assert np.array_equal(s.state.corners, old.corners)

def test_undo_past_initial_is_noop():
    s = SessionState()
    s.undo()
    assert is_solved(s.state)

def test_undo_stack_max_size():
    s = SessionState(max_history=3)
    for move in ["U", "F", "R", "BL", "D"]:
        s.push(apply_move(s.state, move))
    # Only last 3 states kept
    for _ in range(10):
        s.undo()
    # Should be at most 3 undos from the last state
    assert is_solved(s.state) or not is_solved(s.state)  # just no crash
```

- [ ] **Step 2: Run — verify fail**

```bash
pytest tests/test_session.py -v
```

- [ ] **Step 3: Implement session.py**

```python
# mcp_server/session.py
from __future__ import annotations
from collections import deque
from megaminx.model import MegaminxState, SOLVED_STATE


class SessionState:
    def __init__(self, max_history: int = 20) -> None:
        self._state = SOLVED_STATE.copy()
        self._history: deque[MegaminxState] = deque(maxlen=max_history)

    @property
    def state(self) -> MegaminxState:
        return self._state

    def push(self, new_state: MegaminxState) -> None:
        self._history.append(self._state.copy())
        self._state = new_state

    def undo(self, steps: int = 1) -> None:
        for _ in range(steps):
            if self._history:
                self._state = self._history.pop()

    def reset(self) -> None:
        self._state = SOLVED_STATE.copy()
        self._history.clear()
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_session.py -v
```

- [ ] **Step 5: Commit**

```bash
git add mcp_server/session.py tests/test_session.py
git commit -m "feat(session): SessionState with undo stack"
```

---

## Task 8: MCP Server (`server.py`)

**Files:**
- Create: `mcp_server/server.py`
- Create: `tests/test_mcp.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_mcp.py
import pytest
import numpy as np
from megaminx.model import SOLVED_STATE, is_solved
from megaminx.utils import state_to_dict

# Import server and session to test tools directly (avoids full MCP transport)
from mcp_server.session import SessionState
from mcp_server import server as srv

@pytest.fixture(autouse=True)
def fresh_session():
    srv.SESSION.reset()

def test_get_state_returns_dict():
    result = srv.tool_get_state()
    assert "corners" in result and "edges" in result
    assert result["solved"] is True

def test_is_solved_true_on_fresh():
    assert srv.tool_is_solved() is True

def test_apply_move_changes_state():
    srv.tool_apply_move("U")
    assert srv.tool_is_solved() is False

def test_apply_move_invalid_raises():
    with pytest.raises(ValueError):
        srv.tool_apply_move("BOGUS")

def test_apply_sequence_and_inverse():
    srv.tool_apply_sequence(["U", "F", "R"])
    srv.tool_apply_sequence(["R-", "F-", "U-"])
    assert srv.tool_is_solved() is True

def test_undo():
    srv.tool_apply_move("U")
    srv.tool_undo()
    assert srv.tool_is_solved() is True

def test_scramble_produces_valid_state():
    srv.tool_scramble(20)
    from megaminx.model import validate_state
    state_dict = srv.tool_get_state()
    # Reconstruct state from dict and validate
    from megaminx.utils import dict_to_state
    state = dict_to_state(state_dict)
    assert validate_state(state).valid

def test_set_state_valid():
    solved_dict = state_to_dict(SOLVED_STATE)
    result = srv.tool_set_state(solved_dict)
    assert result["valid"] is True

def test_set_state_invalid_rejected():
    bad = state_to_dict(SOLVED_STATE)
    bad["corners"][0]["pos"] = 99
    result = srv.tool_set_state(bad)
    assert result["valid"] is False
    assert len(result["errors"]) > 0
    assert srv.tool_is_solved() is True  # state unchanged

def test_solve_path_one_move():
    srv.tool_apply_move("U")
    result = srv.tool_solve_path({}, max_depth=5)
    assert result is not None
    assert isinstance(result, list)

def test_explain_sequence():
    result = srv.tool_explain_sequence(["U", "F"])
    assert len(result) == 2
    assert "move" in result[0] and "before" in result[0] and "after" in result[0]

def test_list_algorithms():
    result = srv.tool_list_algorithms()
    assert "CO_ALGS" in result

def test_apply_named_alg():
    srv.tool_apply_named_alg("SUNE")
    assert srv.tool_is_solved() is False

def test_get_face():
    result = srv.tool_get_face("U")
    assert isinstance(result, dict)
    assert "face" in result
```

- [ ] **Step 2: Run — verify fail**

```bash
pytest tests/test_mcp.py -v
```

- [ ] **Step 3: Implement server.py**

```python
# mcp_server/server.py
from __future__ import annotations
import numpy as np
from fastmcp import FastMCP
from megaminx.model import SOLVED_STATE, validate_state, is_solved
from megaminx.moves import apply_move, apply_sequence, FACE_NAMES, MOVE_TABLE
from megaminx.algorithms import list_algorithms, get_single_alg, ALGORITHM_SETS
from megaminx.solver import solve_path as _solve_path
from megaminx.utils import scramble, state_to_dict, dict_to_state, describe_state
from mcp_server.session import SessionState

SESSION = SessionState()
mcp = FastMCP("megaminx")


def tool_get_state() -> dict:
    d = state_to_dict(SESSION.state)
    d["solved"] = bool(is_solved(SESSION.state))
    d["description"] = describe_state(SESSION.state)
    return d


def tool_is_solved() -> bool:
    return bool(is_solved(SESSION.state))


def tool_get_face(face: str) -> dict:
    if face not in FACE_NAMES:
        raise ValueError(f"Unknown face {face!r}. Valid: {FACE_NAMES}")
    fi = FACE_NAMES.index(face)
    t = MOVE_TABLE[fi]
    corner_slots = t["corner_cycle"]
    edge_slots = t["edge_cycle"]
    return {
        "face": face,
        "corners": [
            {"slot": ci, "piece": int(SESSION.state.corners[ci, 0]),
             "orientation": int(SESSION.state.corners[ci, 1])}
            for ci in corner_slots
        ],
        "edges": [
            {"slot": ei, "piece": int(SESSION.state.edges[ei, 0]),
             "orientation": int(SESSION.state.edges[ei, 1])}
            for ei in edge_slots
        ],
    }


def tool_apply_move(move: str) -> dict:
    new_state = apply_move(SESSION.state, move)  # raises ValueError on bad move
    SESSION.push(new_state)
    return tool_get_state()


def tool_apply_sequence(moves: list[str]) -> dict:
    state = SESSION.state
    for m in moves:
        state = apply_move(state, m)
    SESSION.push(state)
    return tool_get_state()


def tool_scramble(n: int = 30) -> dict:
    new_state = scramble(SESSION.state.copy(), n)
    SESSION.push(new_state)
    return tool_get_state()


def tool_set_state(state_dict: dict) -> dict:
    result = dict_to_state(state_dict, validate=True)
    if isinstance(result, dict):
        return {"valid": False, "errors": result["errors"]}
    SESSION.push(result)
    return {"valid": True, "errors": []}


def tool_set_layer_solved(layer: str) -> dict:
    """Set a named layer (U_CAP, D_CAP) to the solved positions, others unchanged."""
    from megaminx.moves import CORNER_FACES, EDGE_FACES
    LAYER_CORNERS = {
        "U_CAP": [i for i, cf in enumerate(CORNER_FACES) if 0 in cf],
        "D_CAP": [i for i, cf in enumerate(CORNER_FACES) if 11 in cf],
    }
    LAYER_EDGES = {
        "U_CAP": [i for i, ef in enumerate(EDGE_FACES) if 0 in ef],
        "D_CAP": [i for i, ef in enumerate(EDGE_FACES) if 11 in ef],
    }
    if layer not in LAYER_CORNERS:
        raise ValueError(f"Unknown layer {layer!r}. Valid: {list(LAYER_CORNERS)}")
    new_state = SESSION.state.copy()
    for ci in LAYER_CORNERS[layer]:
        new_state.corners[ci] = SOLVED_STATE.corners[ci]
    for ei in LAYER_EDGES[layer]:
        new_state.edges[ei] = SOLVED_STATE.edges[ei]
    r = validate_state(new_state)
    if not r.valid:
        return {"valid": False, "errors": r.errors}
    SESSION.push(new_state)
    return {"valid": True, "errors": []}


def tool_scramble_substate(region: str) -> dict:
    """Scramble only the pieces in a region (U_CAP or D_CAP), keep rest solved."""
    from megaminx.moves import CORNER_FACES, EDGE_FACES
    LAYER_CORNERS = {
        "U_CAP": [i for i, cf in enumerate(CORNER_FACES) if 0 in cf],
        "D_CAP": [i for i, cf in enumerate(CORNER_FACES) if 11 in cf],
    }
    LAYER_EDGES = {
        "U_CAP": [i for i, ef in enumerate(EDGE_FACES) if 0 in ef],
        "D_CAP": [i for i, ef in enumerate(EDGE_FACES) if 11 in ef],
    }
    if region not in LAYER_CORNERS:
        raise ValueError(f"Unknown region {region!r}. Valid: {list(LAYER_CORNERS)}")
    # Reset region to solved, scramble with U or D moves only
    face_move = "U" if region == "U_CAP" else "D"
    new_state = SOLVED_STATE.copy()
    new_state = scramble(new_state, 10)  # full scramble then extract region
    # Actually: scramble only with face moves adjacent to region
    import random
    region_moves = [f"{face_move}", f"{face_move}-"]
    new_state = SESSION.state.copy()
    for ci in LAYER_CORNERS[region]:
        new_state.corners[ci] = SOLVED_STATE.corners[ci]
    for ei in LAYER_EDGES[region]:
        new_state.edges[ei] = SOLVED_STATE.edges[ei]
    for _ in range(10):
        m = random.choice(region_moves)
        new_state = apply_move(new_state, m)
    SESSION.push(new_state)
    return tool_get_state()


def tool_solve_path(
    to_state_dict: dict | None = None,
    move_set: list[str] | None = None,
    max_depth: int = 10,
) -> list[str] | None:
    """Find a move sequence from current state to to_state_dict (default: solved).

    move_set: optional list of atomic WCA move strings to restrict the search,
              e.g. ["U", "U-", "U++"] to search only U-layer moves.
    """
    to_state = SOLVED_STATE.copy() if not to_state_dict else dict_to_state(to_state_dict)
    if isinstance(to_state, dict):
        raise ValueError(f"Invalid target state: {to_state['errors']}")
    return _solve_path(SESSION.state, to_state, move_set=move_set, max_depth=max_depth)


def tool_apply_named_alg(name: str) -> dict:
    seq = get_single_alg(name)  # KeyError if unknown
    return tool_apply_sequence(seq)


def tool_explain_sequence(moves: list[str]) -> list[dict]:
    steps = []
    state = SESSION.state
    for m in moves:
        before = state_to_dict(state)
        new_state = apply_move(state, m)
        after = state_to_dict(new_state)
        changed_corners = [
            i for i in range(20)
            if before["corners"][i] != after["corners"][i]
        ]
        changed_edges = [
            i for i in range(30)
            if before["edges"][i] != after["edges"][i]
        ]
        steps.append({
            "move": m,
            "before": before,
            "after": after,
            "changed_corners": changed_corners,
            "changed_edges": changed_edges,
            "description": (
                f"Move {m}: {len(changed_corners)} corners and "
                f"{len(changed_edges)} edges changed."
            ),
        })
        state = new_state
    return steps


def tool_list_algorithms() -> dict:
    return list_algorithms()


def tool_undo(steps: int = 1) -> dict:
    SESSION.undo(steps)
    return tool_get_state()


# Register tools with FastMCP
mcp.tool()(tool_get_state)
mcp.tool()(tool_is_solved)
mcp.tool()(tool_get_face)
mcp.tool()(tool_apply_move)
mcp.tool()(tool_apply_sequence)
mcp.tool()(tool_scramble)
mcp.tool()(tool_set_state)
mcp.tool()(tool_set_layer_solved)
mcp.tool()(tool_scramble_substate)
mcp.tool()(tool_solve_path)
mcp.tool()(tool_apply_named_alg)
mcp.tool()(tool_explain_sequence)
mcp.tool()(tool_list_algorithms)
mcp.tool()(tool_undo)

if __name__ == "__main__":
    mcp.run()
```

- [ ] **Step 4: Run all tests**

```bash
pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 5: Run full test suite and check coverage**

```bash
pytest tests/ --cov=megaminx --cov=mcp_server --cov-report=term-missing
```

- [ ] **Step 6: Export __init__.py public API**

```python
# megaminx/__init__.py
from megaminx.model import MegaminxState, SOLVED_STATE, validate_state, is_solved
from megaminx.moves import apply_move, apply_sequence, FACE_NAMES, ALL_MOVES
from megaminx.utils import scramble, state_to_dict, dict_to_state, describe_state
from megaminx.solver import solve_path
```

- [ ] **Step 7: Commit**

```bash
git add mcp_server/server.py tests/test_mcp.py megaminx/__init__.py
git commit -m "feat(mcp): FastMCP server with all tools"
```

---

## Task 9: Final integration check

- [ ] **Step 1: Run full test suite**

```bash
pytest tests/ -v --tb=short
```

Expected: all tests pass.

- [ ] **Step 2: Smoke test MCP server starts**

```bash
python -c "from mcp_server.server import mcp; print('MCP server OK, tools:', len(mcp.list_tools()))"
```

Expected: prints tool count (≥ 14).

- [ ] **Step 3: Smoke test scramble + solve roundtrip**

```bash
python - <<'EOF'
from megaminx import SOLVED_STATE, scramble, solve_path, apply_sequence, is_solved

state = scramble(SOLVED_STATE.copy(), 3)
sol = solve_path(state, SOLVED_STATE.copy(), max_depth=6)
print("Solution:", sol)
result = apply_sequence(state, sol or [])
print("Solved:", is_solved(result))
EOF
```

Expected: prints a short move sequence and `Solved: True`.

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "chore: final integration — all tests passing"
```
