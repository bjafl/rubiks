"""
megaminx/cube.py — WCA-correct Megaminx model

Sole handwritten data: NEIGHBORS (dodecahedron adjacency with consistent
rotation direction). All move tables are generated from sticker simulation
and verified automatically.

WCA convention: CW from outside each face.
U CW from above: F → L → BL → BR → R.
"""
from __future__ import annotations
from dataclasses import dataclass
import random

# ─── Handwritten data ────────────────────────────────────────────────────────

NEIGHBORS: dict[str, list[str]] = {
    "U":   ["F", "R", "dR", "dL", "L"],
    "F":   ["U", "L", "BL", "BR", "R"],
    "R":   ["F", "BR", "dBR", "dR", "U"],
    "BR":  ["F", "BL", "B", "dBR", "R"],
    "BL":  ["F", "L", "dBL", "B", "BR"],
    "L":   ["F", "U", "dL", "dBL", "BL"],
    "D":   ["dL", "dR", "dBR", "B", "dBL"],
    "dR":  ["dL", "U", "R", "dBR", "D"],
    "dBR": ["dR", "R", "BR", "B", "D"],
    "B":   ["dBR", "BR", "BL", "dBL", "D"],
    "dBL": ["B", "BL", "L", "dL", "D"],
    "dL":  ["dBL", "L", "U", "dR", "D"],
}
FACES: list[str] = list(NEIGHBORS)

# ─── Consistency check ───────────────────────────────────────────────────────

def _check_orientation() -> None:
    for f, ns in NEIGHBORS.items():
        for i, g in enumerate(ns):
            x, y = ns[i - 1], ns[(i + 1) % 5]
            gs = NEIGHBORS[g]
            j = gs.index(f)
            assert gs[j - 1] == y and gs[(j + 1) % 5] == x, (f, g)

_check_orientation()

# ─── Generate corners (20) and edges (30) ────────────────────────────────────

def _vertex_cycle(corner: frozenset) -> tuple:
    edges: dict = {}
    for g in corner:
        rest = [x for x in corner if x != g]
        ns = NEIGHBORS[g]
        a, b = rest
        if ns[(ns.index(a) + 1) % 5] == b:
            edges[a] = b
        else:
            edges[b] = a
    start = min(corner)
    return (start, edges[start], edges[edges[start]])

_corner_sets = {
    frozenset((f, ns[i], ns[(i + 1) % 5]))
    for f, ns in NEIGHBORS.items()
    for i in range(5)
}
CORNERS: list[tuple[str, str, str]] = sorted(_vertex_cycle(c) for c in _corner_sets)
EDGES: list[tuple[str, str]] = sorted(
    {tuple(sorted((f, n))) for f, ns in NEIGHBORS.items() for n in ns}
)
assert len(CORNERS) == 20 and len(EDGES) == 30

_C_INDEX = {frozenset(c): i for i, c in enumerate(CORNERS)}
_E_INDEX = {frozenset(e): i for i, e in enumerate(EDGES)}

# ─── Sticker-level move generation ───────────────────────────────────────────

def _sticker_move(face: str) -> dict:
    ns = NEIGHBORS[face]
    sigma = {ns[i]: ns[(i + 1) % 5] for i in range(5)} | {face: face}
    perm = {}
    for ci, cyc in enumerate(CORNERS):
        if face in cyc:
            dest = _C_INDEX[frozenset(sigma[g] for g in cyc)]
            for g in cyc:
                perm[("c", dest, sigma[g])] = ("c", ci, g)
    for ei, pair in enumerate(EDGES):
        if face in pair:
            dest = _E_INDEX[frozenset(sigma[g] for g in pair)]
            for g in pair:
                perm[("e", dest, sigma[g])] = ("e", ei, g)
    return perm


def _apply_stickers(state: dict, perm: dict) -> dict:
    new = dict(state)
    for dest, src in perm.items():
        new[dest] = state[src]
    return new


_SOLVED_STICKERS: dict = {
    ("c", i, g): ("c", i, g) for i, c in enumerate(CORNERS) for g in c
}
_SOLVED_STICKERS |= {
    ("e", i, g): ("e", i, g) for i, e in enumerate(EDGES) for g in e
}


def _extract(stk: dict) -> tuple:
    cp, co = [0] * 20, [0] * 20
    for i, cyc in enumerate(CORNERS):
        piece = stk[("c", i, cyc[0])][1]
        cp[i] = piece
        ref = ("c", piece, CORNERS[piece][0])
        co[i] = next(k for k in range(3) if stk[("c", i, cyc[k])] == ref)
    ep, eo = [0] * 30, [0] * 30
    for i, pair in enumerate(EDGES):
        piece = stk[("e", i, pair[0])][1]
        ep[i] = piece
        ref = ("e", piece, EDGES[piece][0])
        eo[i] = 0 if stk[("e", i, pair[0])] == ref else 1
    return tuple(cp), tuple(co), tuple(ep), tuple(eo)

# ─── State representation ────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class MegaminxState:
    cp: tuple  # 20: piece index at corner slot i
    co: tuple  # 20: orientation mod 3 (ref = first face in CORNERS[i])
    ep: tuple  # 30: piece index at edge slot i
    eo: tuple  # 30: flip mod 2 (ref = first face in EDGES[i])

    def then(self, t: "MegaminxState") -> "MegaminxState":
        """Group composition: apply self, then t."""
        return MegaminxState(
            tuple(self.cp[m] for m in t.cp),
            tuple((self.co[t.cp[i]] + t.co[i]) % 3 for i in range(20)),
            tuple(self.ep[m] for m in t.ep),
            tuple((self.eo[t.ep[i]] + t.eo[i]) % 2 for i in range(30)),
        )

    def apply(self, move: str) -> "MegaminxState":
        return self.then(MOVES[move])

    def alg(self, sequence: str) -> "MegaminxState":
        result = self
        for token in sequence.split():
            result = result.then(MOVES[token])
        return result

    def inverse(self) -> "MegaminxState":
        cp = [0] * 20
        co = [0] * 20
        for i, p in enumerate(self.cp):
            cp[p] = i
            co[p] = (-self.co[i]) % 3
        ep = [0] * 30
        eo = [0] * 30
        for i, p in enumerate(self.ep):
            ep[p] = i
            eo[p] = self.eo[i]
        return MegaminxState(tuple(cp), tuple(co), tuple(ep), tuple(eo))

    @property
    def is_solved(self) -> bool:
        return self == SOLVED

    def corner_at(self, *faces: str) -> tuple[tuple, int]:
        i = next(i for i, c in enumerate(CORNERS) if set(c) == set(faces))
        return CORNERS[self.cp[i]], self.co[i]

    def edge_at(self, *faces: str) -> tuple[tuple, int]:
        i = next(i for i, e in enumerate(EDGES) if set(e) == set(faces))
        return EDGES[self.ep[i]], self.eo[i]

    def diff(self) -> str:
        lines = []
        for i in range(20):
            if self.cp[i] != i or self.co[i]:
                lines.append(
                    f"  C {'/'.join(CORNERS[i]):<12} <- "
                    f"{'/'.join(CORNERS[self.cp[i]]):<12} co={self.co[i]}"
                )
        for i in range(30):
            if self.ep[i] != i or self.eo[i]:
                lines.append(
                    f"  E {'/'.join(EDGES[i]):<10} <- "
                    f"{'/'.join(EDGES[self.ep[i]]):<10} eo={self.eo[i]}"
                )
        return "\n".join(lines) or "  solved"

    @staticmethod
    def scramble(n: int = 70, seed: int | None = None) -> tuple["MegaminxState", str]:
        rng = random.Random(seed)
        names = [f + s for f in FACES for s in ("", "'")]
        seq = " ".join(rng.choice(names) for _ in range(n))
        return SOLVED.alg(seq), seq


SOLVED = MegaminxState(
    tuple(range(20)), (0,) * 20,
    tuple(range(30)), (0,) * 30,
)

# ─── Build MOVES from sticker simulation ─────────────────────────────────────

MOVES: dict[str, MegaminxState] = {}
for _f in FACES:
    _perm = _sticker_move(_f)
    _stk = _SOLVED_STICKERS
    for _power, _suffix in enumerate(["", "2", "2'", "'"], start=1):
        _stk = _apply_stickers(_stk, _perm)
        _cp, _co, _ep, _eo = _extract(_stk)
        MOVES[_f + _suffix] = MegaminxState(_cp, _co, _ep, _eo)
    assert _apply_stickers(_stk, _perm) == _SOLVED_STICKERS  # order 5

# Legacy notation aliases
for _f in list(FACES):
    MOVES[_f + "-"]  = MOVES[_f + "'"]
    MOVES[_f + "++"] = MOVES[_f + "2"]
    MOVES[_f + "--"] = MOVES[_f + "2'"]

# ─── Convenience functions ────────────────────────────────────────────────────

def apply_move(state: MegaminxState, move_str: str) -> MegaminxState:
    try:
        return state.then(MOVES[move_str])
    except KeyError:
        raise ValueError(f"Unknown move: {move_str!r}. Valid faces: {FACES}")


def apply_sequence(state: MegaminxState, moves: list[str]) -> MegaminxState:
    for m in moves:
        state = apply_move(state, m)
    return state
