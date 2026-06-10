# megaminx/moves.py
from __future__ import annotations
import re
import numpy as np

from megaminx.cube import (
    FACES, CORNERS, EDGES, MOVES as _CUBE_MOVES,
    MegaminxState, apply_move, apply_sequence,
)
from megaminx.model import SOLVED_STATE  # noqa: F401 (backward compat re-export)

# ─── Public API (re-exported from cube.py) ───────────────────────────────────

FACE_NAMES: list[str] = FACES
ALL_MOVES: list[str] = [f + s for f in FACE_NAMES for s in ("", "-")]

_FACE_INDEX: dict[str, int] = {name: i for i, name in enumerate(FACE_NAMES)}

# Corner/edge face-index lookup (using cube.py slot ordering)
CORNER_FACES: list[tuple[int, int, int]] = [
    tuple(_FACE_INDEX[f] for f in corner)   # type: ignore[misc]
    for corner in CORNERS
]
EDGE_FACES: list[tuple[int, int]] = [
    tuple(_FACE_INDEX[f] for f in edge)     # type: ignore[misc]
    for edge in EDGES
]

# ─── Move parser ─────────────────────────────────────────────────────────────

_MOVE_RE = re.compile(r"^([A-Z]+)(\+\+|--|2'|2|[+\-']?)$")
_SUFFIX_TURNS: dict[str, int] = {
    "": 1, "+": 1, "++": 2, "-": 4, "--": 3,
    "'": 4, "2": 2, "2'": 3,
}


def parse_move(move_str: str) -> tuple[int, int]:
    """Return (face_index, turns) where turns ∈ {1,2,3,4}."""
    m = _MOVE_RE.match(move_str.strip())
    if not m:
        raise ValueError(f"Invalid move: {move_str!r}")
    face_name, suffix = m.group(1), m.group(2)
    if face_name not in _FACE_INDEX:
        raise ValueError(f"Unknown face: {face_name!r}. Valid: {FACE_NAMES}")
    return _FACE_INDEX[face_name], _SUFFIX_TURNS[suffix]


# ─── Dodecahedron geometry (for viewer geometry.json generation only) ─────────

PHI = (1 + 5 ** 0.5) / 2

_RAW_VERTS = np.array([
    (-1,-1,-1), (-1,-1, 1), (-1, 1,-1), (-1, 1, 1),
    ( 1,-1,-1), ( 1,-1, 1), ( 1, 1,-1), ( 1, 1, 1),
    (0, -1/PHI, -PHI), (0, -1/PHI,  PHI),
    (0,  1/PHI, -PHI), (0,  1/PHI,  PHI),
    (-1/PHI, -PHI, 0), (-1/PHI,  PHI, 0),
    ( 1/PHI, -PHI, 0), ( 1/PHI,  PHI, 0),
    (-PHI, 0, -1/PHI), (-PHI, 0,  1/PHI),
    ( PHI, 0, -1/PHI), ( PHI, 0,  1/PHI),
], dtype=float)

_EDGE_LEN_SQ = (2 / PHI) ** 2
_TOL = 1e-6

_ADJ = np.zeros((20, 20), dtype=bool)
for _i in range(20):
    for _j in range(_i + 1, 20):
        diff = _RAW_VERTS[_i] - _RAW_VERTS[_j]
        if abs(float(np.dot(diff, diff)) - _EDGE_LEN_SQ) < _TOL:
            _ADJ[_i, _j] = _ADJ[_j, _i] = True

assert _ADJ.sum() // 2 == 30
assert (_ADJ.sum(axis=1) == 3).all()


def _find_faces() -> list[list[int]]:
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
                    mids = [w for w in range(20)
                            if _ADJ[x, w] and _ADJ[z, w] and w not in (u, v, x, z)]
                    for mid in mids:
                        faces.add(tuple(sorted([u, v, x, mid, z])))
    return [list(f) for f in faces]


def _sort_face_cw(face_verts: list[int], face_center: np.ndarray) -> list[int]:
    normal = face_center / np.linalg.norm(face_center)
    v0 = _RAW_VERTS[face_verts[0]] - face_center
    e1 = v0 / np.linalg.norm(v0)
    e2 = np.cross(normal, e1)
    angles = [np.arctan2(
        np.dot(_RAW_VERTS[vi] - face_center, e2),
        np.dot(_RAW_VERTS[vi] - face_center, e1),
    ) for vi in face_verts]
    return [face_verts[i] for i in np.argsort(angles)[::-1]]


_raw_geo_faces = _find_faces()
assert len(_raw_geo_faces) == 12
_geo_centers_raw = np.array([_RAW_VERTS[fv].mean(axis=0) for fv in _raw_geo_faces])


def _cw_ring_order(
    pole_geo: int, ref_geo: int, ring: list[int],
) -> list[int]:
    """Sort ring face indices by CW angle as viewed from outside the pole face."""
    pole_c = _geo_centers_raw[pole_geo]
    normal = pole_c / np.linalg.norm(pole_c)
    ref_c = _geo_centers_raw[ref_geo]
    ref_proj = ref_c - pole_c
    ref_proj = ref_proj - np.dot(ref_proj, normal) * normal
    ref_proj = ref_proj / np.linalg.norm(ref_proj)

    def angle(j: int) -> float:
        d = _geo_centers_raw[j] - pole_c
        d = d - np.dot(d, normal) * normal
        if np.linalg.norm(d) < 1e-9:
            return 0.0
        d = d / np.linalg.norm(d)
        cross = np.cross(ref_proj, d)
        # CW from outside = CCW in right-hand frame around outward normal
        return float(np.arctan2(float(np.dot(cross, normal)), float(np.dot(ref_proj, d)))) % (2 * np.pi)

    return sorted(ring, key=angle)


def _geo_adj(j1: int, j2: int) -> bool:
    return len(set(_raw_geo_faces[j1]) & set(_raw_geo_faces[j2])) == 2


def _match_geo_to_cube() -> tuple[list[list[int]], list[np.ndarray]]:
    """Return (face_verts_list, face_centers) ordered to match FACES."""
    from megaminx.cube import FACES as _F, NEIGHBORS as _NB

    # U = face with highest y; D = antipodal face (center ≈ -U_center)
    u_geo = int(np.argmax(_geo_centers_raw[:, 1]))
    d_geo = int(np.argmin(np.linalg.norm(_geo_centers_raw + _geo_centers_raw[u_geo], axis=1)))

    # U-ring: 5 faces adjacent to U, sorted CW from F
    u_adj = [j for j in range(12) if _geo_adj(u_geo, j)]
    f_geo = min(u_adj, key=lambda j: float(_geo_centers_raw[j][2]))
    u_ring_cw = _cw_ring_order(u_geo, f_geo, u_adj)
    # NEIGHBORS["U"] = F, L, BL, BR, R in CW order from outside U
    u_name_to_geo: dict[str, int] = {_NB["U"][i]: u_ring_cw[i] for i in range(5)}

    # D-ring: 5 faces adjacent to D, sorted CW from DFL
    d_adj = [j for j in range(12) if _geo_adj(d_geo, j)]
    # DFL is adjacent to both F and L
    dfl_geo = next(
        j for j in d_adj
        if _geo_adj(j, u_name_to_geo["F"]) and _geo_adj(j, u_name_to_geo["L"])
    )
    d_ring_cw = _cw_ring_order(d_geo, dfl_geo, d_adj)
    # NEIGHBORS["D"] = DFL, DFR, DBR, DB, DBL in CW order from outside D
    d_name_to_geo: dict[str, int] = {_NB["D"][i]: d_ring_cw[i] for i in range(5)}

    name_to_geo: dict[str, int] = {"U": u_geo, "D": d_geo, **u_name_to_geo, **d_name_to_geo}
    geo_order = [name_to_geo[name] for name in _F]

    verts = [_sort_face_cw(_raw_geo_faces[i], _geo_centers_raw[i]) for i in geo_order]
    centers = [_geo_centers_raw[i] for i in geo_order]
    return verts, centers


_FACE_VERTS, _face_centers = _match_geo_to_cube()


def _extract_face_cycle(face_name: str, move_perm: tuple, n: int) -> list[int]:
    """Extract ordered 5-cycle indices from a permutation tuple."""
    moved = [i for i in range(n) if move_perm[i] != i]
    if not moved:
        return []
    start = min(moved)
    cycle = [start]
    cur = move_perm[start]
    while cur != start:
        cycle.append(cur)
        cur = move_perm[cur]
    return cycle


def get_geometry_data() -> dict:
    """Return dodecahedron geometry using cube.py face/corner/edge ordering."""
    face_corner_cycles = []
    face_edge_cycles   = []
    for fi, face_name in enumerate(FACE_NAMES):
        m = _CUBE_MOVES[face_name]
        face_corner_cycles.append(_extract_face_cycle(face_name, m.cp, 20))
        face_edge_cycles.append(_extract_face_cycle(face_name, m.ep, 30))

    return {
        "face_names":        list(FACE_NAMES),
        "face_vertices":     [[_RAW_VERTS[v].tolist() for v in fv] for fv in _FACE_VERTS],
        "face_centers":      [c.tolist() for c in _face_centers],
        "face_corner_cycles": face_corner_cycles,
        "face_edge_cycles":   face_edge_cycles,
        "corner_faces":      [list(cf) for cf in CORNER_FACES],
        "edge_faces":        [list(ef) for ef in EDGE_FACES],
    }
