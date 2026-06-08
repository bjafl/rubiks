from __future__ import annotations
import re
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

# Edge length: distance between two adjacent vertices = 2/φ
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
_face_centers = [_RAW_VERTS[_FACE_VERTS_RAW[i]].mean(axis=0) for i in range(12)]
_face_order = sorted(range(12), key=lambda i: -_face_centers[i][1])
_FACE_VERTS_SORTED = [_FACE_VERTS_RAW[_face_order[i]] for i in range(12)]
_face_centers = [_RAW_VERTS[fv].mean(axis=0) for fv in _FACE_VERTS_SORTED]
_FACE_VERTS = [_sort_face_cw(fv, fc) for fv, fc in zip(_FACE_VERTS_SORTED, _face_centers)]

# WCA face names: U, then 5 upper-ring, then 5 lower-ring, then D
_u_neighbors = [i for i in range(1, 12) if any(v in _FACE_VERTS[0] for v in _FACE_VERTS[i])]
_d_neighbors = [i for i in range(1, 11) if any(v in _FACE_VERTS[11] for v in _FACE_VERTS[i])]

def _face_angle_around_y(fi: int) -> float:
    c = _face_centers[fi]
    return np.arctan2(c[2], c[0])

_u_ring = sorted(_u_neighbors, key=_face_angle_around_y)
_d_ring = sorted(_d_neighbors, key=_face_angle_around_y)

_WCA_U_RING = ["F", "FR", "BR", "BL", "FL"]
_WCA_D_RING = ["DFR", "DR", "DBR", "DBL", "DFL"]
FACE_NAMES = (
    ["U"]
    + [_WCA_U_RING[i] for i in range(5)]
    + [_WCA_D_RING[i] for i in range(5)]
    + ["D"]
)
_FACE_INDEX = {name: i for i, name in enumerate(FACE_NAMES)}

# --- Corner labeling (20 corners = vertices of dodecahedron) ---
_vert_to_faces: dict[int, list[int]] = {v: [] for v in range(20)}
for _fi, _fv in enumerate(_FACE_VERTS):
    for _v in _fv:
        _vert_to_faces[_v].append(_fi)

# Stable corner numbering: sort by sorted face-triple
_corner_order = sorted(range(20), key=lambda v: tuple(sorted(_vert_to_faces[v])))
CORNER_FACES: list[tuple[int, int, int]] = [
    tuple(sorted(_vert_to_faces[v])) for v in _corner_order  # type: ignore
]
_vert_to_corner = {v: i for i, v in enumerate(_corner_order)}

# --- Edge labeling (30 edges) ---
_raw_edges: list[tuple[int, int]] = []
for _i in range(20):
    for _j in range(_i + 1, 20):
        if _ADJ[_i, _j]:
            _raw_edges.append((_i, _j))

_raw_edges.sort(key=lambda e: tuple(sorted(
    frozenset(_vert_to_faces[e[0]]) & frozenset(_vert_to_faces[e[1]])
)))
EDGE_FACES: list[tuple[int, int]] = [
    tuple(sorted(frozenset(_vert_to_faces[e[0]]) & frozenset(_vert_to_faces[e[1]])))  # type: ignore
    for e in _raw_edges
]
_edge_key_to_idx = {ef: i for i, ef in enumerate(EDGE_FACES)}


def _build_move_table() -> dict[int, dict]:
    """Compute corner cycle and edge cycle for each face.

    Orientation deltas are all 0. On a megaminx, when a face rotates CW by 72°,
    each corner piece moves to the next slot on that face. The sticker that was
    facing the rotating face still faces the rotating face at the new slot, so
    orientation (relative to the piece's primary reference face) is preserved.
    This is the standard "position-based" orientation convention: orientation 0
    means the piece is untwisted in its current slot. Under this convention,
    a pure face rotation never introduces a twist — only permutation.
    """
    table = {}

    for fi, fv_ordered in enumerate(_FACE_VERTS):
        # Corner cycle: piece at slot k moves to slot k+1 (CW order)
        corner_cycle = [_vert_to_corner[v] for v in fv_ordered]

        # Orientation deltas are 0: face rotations don't twist pieces
        c_ori_delta = [0, 0, 0, 0, 0]

        # Edge cycle: edge between vertex k and k+1 moves to between k+1 and k+2
        edge_cycle = []
        for k in range(5):
            v1 = fv_ordered[k]
            v2 = fv_ordered[(k + 1) % 5]
            shared = tuple(sorted(frozenset(_vert_to_faces[v1]) & frozenset(_vert_to_faces[v2])))
            edge_cycle.append(_edge_key_to_idx[shared])

        # Edge orientation deltas are 0 for same reason
        e_ori_delta = [0, 0, 0, 0, 0]

        table[fi] = {
            "corner_cycle": corner_cycle,
            "c_ori_delta": c_ori_delta,
            "edge_cycle": edge_cycle,
            "e_ori_delta": e_ori_delta,
        }

    return table


MOVE_TABLE = _build_move_table()

_MOVE_RE = re.compile(r"^([A-Z]+)(\+\+|--|[+-]?)$")

def parse_move(move_str: str) -> tuple[int, int]:
    """Return (face_index, turns) where turns ∈ {1, 2, 3, 4}."""
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
    cc = t["corner_cycle"]
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
