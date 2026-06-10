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

# WCA face names in y-sorted order (U at top, D at bottom)
_u_neighbors = [i for i in range(1, 12) if any(v in _FACE_VERTS[0] for v in _FACE_VERTS[i])]
_d_neighbors = [i for i in range(1, 11) if any(v in _FACE_VERTS[11] for v in _FACE_VERTS[i])]

def _face_angle_around_y(fi: int) -> float:
    c = _face_centers[fi]
    return np.arctan2(c[2], c[0])

_u_ring = sorted(_u_neighbors, key=_face_angle_around_y)
_d_ring = sorted(_d_neighbors, key=_face_angle_around_y)

_WCA_U_RING = ["F", "L", "R", "DL", "BR"]
_WCA_D_RING = ["DR", "BL", "UR", "UL", "B"]
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


def _rotate_vector(v: np.ndarray, axis: np.ndarray, angle: float) -> np.ndarray:
    """Rodrigues' rotation formula."""
    axis = axis / np.linalg.norm(axis)
    return (v * np.cos(angle)
            + np.cross(axis, v) * np.sin(angle)
            + axis * np.dot(axis, v) * (1 - np.cos(angle)))


def _compute_corner_cw_signs() -> list[int]:
    """For each corner, determine the cyclic CW order of its 3 faces (viewed from outside).

    Returns +1 if CW goes face[0]→face[1]→face[2] (ascending sorted index),
            -1 if CW goes face[0]→face[2]→face[1] (descending for non-primary).
    The sign determines whether orientation delta = best or = (3-best)%3.
    """
    signs = []
    for ci, v in enumerate(_corner_order):
        corner_dir = _RAW_VERTS[v] / np.linalg.norm(_RAW_VERTS[v])
        faces = CORNER_FACES[ci]
        normals = [_face_centers[f] / np.linalg.norm(_face_centers[f]) for f in faces]
        projs = [n - corner_dir * np.dot(n, corner_dir) for n in normals]
        e1 = projs[0] / np.linalg.norm(projs[0])
        e2 = np.cross(corner_dir, e1)
        # Signed angle from face[0] to face[1] in the plane (positive = CCW from outside)
        angle_f1 = np.arctan2(float(np.dot(projs[1], e2)), float(np.dot(projs[1], e1)))
        signs.append(1 if angle_f1 < 0 else -1)
    return signs


_CORNER_CW_SIGN = _compute_corner_cw_signs()


def _build_move_table() -> dict[int, dict]:
    """Compute corner cycle, edge cycle, and orientation deltas for each face.

    CW from outside = -angle around the outward face normal (right-hand rule).
    Corner orientation: primary direction = outward normal of face[0] (lowest-indexed face).
    The delta accounts for the cyclic CW order at each destination corner.
    Edge orientation: 0 if primary direction preserved, 1 if flipped.
    """
    angle = -2 * np.pi / 5  # CW from outside = CCW in right-hand frame
    table = {}

    for fi, fv_ordered in enumerate(_FACE_VERTS):
        center = _face_centers[fi]
        normal = center / np.linalg.norm(center)

        corner_cycle = [_vert_to_corner[v] for v in fv_ordered]

        c_ori_delta = []
        for k, v in enumerate(fv_ordered):
            ci = _vert_to_corner[v]
            face_indices = list(CORNER_FACES[ci])
            primary_dir = _face_centers[face_indices[0]] / np.linalg.norm(_face_centers[face_indices[0]])
            rotated_primary = _rotate_vector(primary_dir, normal, angle)

            new_v = fv_ordered[(k + 1) % 5]
            new_ci = _vert_to_corner[new_v]
            new_faces = list(CORNER_FACES[new_ci])
            new_face_normals = [
                _face_centers[f] / np.linalg.norm(_face_centers[f])
                for f in new_faces
            ]
            dots = [float(np.dot(rotated_primary, nfn)) for nfn in new_face_normals]
            best = int(np.argmax(dots))
            # CW sign determines whether ascending or descending sorted order is CW
            delta = best if _CORNER_CW_SIGN[new_ci] == 1 else (3 - best) % 3
            c_ori_delta.append(delta)

        edge_cycle = []
        for k in range(5):
            v1 = fv_ordered[k]
            v2 = fv_ordered[(k + 1) % 5]
            shared = tuple(sorted(frozenset(_vert_to_faces[v1]) & frozenset(_vert_to_faces[v2])))
            edge_cycle.append(_edge_key_to_idx[shared])

        e_ori_delta = []
        for k in range(5):
            src_ei = edge_cycle[k]
            f_pair = list(EDGE_FACES[src_ei])
            primary_dir = _face_centers[f_pair[0]] / np.linalg.norm(_face_centers[f_pair[0]])
            rotated_primary = _rotate_vector(primary_dir, normal, angle)

            dst_ei = edge_cycle[(k + 1) % 5]
            new_f_pair = list(EDGE_FACES[dst_ei])
            new_primary_dir = _face_centers[new_f_pair[0]] / np.linalg.norm(_face_centers[new_f_pair[0]])
            dot = float(np.dot(rotated_primary, new_primary_dir))
            e_ori_delta.append(0 if dot > 0 else 1)

        table[fi] = {
            "corner_cycle": corner_cycle,
            "c_ori_delta": c_ori_delta,
            "edge_cycle": edge_cycle,
            "e_ori_delta": e_ori_delta,
        }

    return table


MOVE_TABLE = _build_move_table()

_MOVE_RE = re.compile(r"^([A-Z]+)(\+\+|--|2'|2|[+\-']?)$")

_SUFFIX_TURNS: dict[str, int] = {
    "": 1, "+": 1, "++": 2, "-": 4, "--": 3,
    "'": 4, "2": 2, "2'": 3,
}

def parse_move(move_str: str) -> tuple[int, int]:
    """Return (face_index, turns) where turns ∈ {1, 2, 3, 4}.

    Accepts both simulator suffixes (++/--/-) and SSE/WCA suffixes (2/2'/').
    """
    m = _MOVE_RE.match(move_str.strip())
    if not m:
        raise ValueError(f"Invalid move: {move_str!r}")
    face_name, suffix = m.group(1), m.group(2)
    if face_name not in _FACE_INDEX:
        raise ValueError(f"Unknown face: {face_name!r}. Valid: {FACE_NAMES}")
    fi = _FACE_INDEX[face_name]
    turns = _SUFFIX_TURNS[suffix]
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


def get_geometry_data() -> dict:
    """Return dodecahedron geometry and piece-slot mappings as plain Python types."""
    return {
        "face_names":        list(FACE_NAMES),
        "face_vertices":     [[_RAW_VERTS[v].tolist() for v in fv] for fv in _FACE_VERTS],
        "face_centers":      [c.tolist() for c in _face_centers],
        "face_corner_cycles": [list(MOVE_TABLE[fi]["corner_cycle"]) for fi in range(12)],
        "face_edge_cycles":   [list(MOVE_TABLE[fi]["edge_cycle"])   for fi in range(12)],
        "corner_faces":      [list(cf) for cf in CORNER_FACES],
        "edge_faces":        [list(ef) for ef in EDGE_FACES],
    }
