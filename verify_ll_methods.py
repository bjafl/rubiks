"""
Verifiserer alle LL-algoritmer fra megaminx-ll-metode{1-3,4}.md
mot Megaminx-simulatoren.
"""
from __future__ import annotations
import numpy as np
from megaminx import SOLVED_STATE
from megaminx.moves import apply_sequence
from megaminx.model import MegaminxState

# Top corner/edge indices (adjacent to U face)
TOP_CORNERS = list(range(5))   # corners 0–4
TOP_EDGES   = list(range(5))   # edges   0–4


def copy_state(s: MegaminxState) -> MegaminxState:
    return MegaminxState(s.corners.copy(), s.edges.copy())


def apply(moves_str: str, state: MegaminxState | None = None) -> MegaminxState:
    """Apply a space-separated move string to a solved state (or given state)."""
    if state is None:
        state = copy_state(SOLVED_STATE)
    tokens = moves_str.split()
    return apply_sequence(state, tokens)


def delta_corners(state: MegaminxState) -> dict:
    """Returns {slot: (original_piece, orientation)} for top corners that changed."""
    solved = SOLVED_STATE
    result = {}
    for i in TOP_CORNERS:
        orig_pos, orig_ori = solved.corners[i]
        new_pos,  new_ori  = state.corners[i]
        if orig_pos != new_pos or orig_ori != new_ori:
            result[i] = (int(new_pos), int(new_ori))
    return result


def delta_edges(state: MegaminxState) -> dict:
    """Returns changed slots for top edges."""
    solved = SOLVED_STATE
    result = {}
    for i in TOP_EDGES:
        orig_pos, orig_ori = solved.edges[i]
        new_pos,  new_ori  = state.edges[i]
        if orig_pos != new_pos or orig_ori != new_ori:
            result[i] = (int(new_pos), int(new_ori))
    return result


def non_top_moved(state: MegaminxState) -> bool:
    """True if any non-top piece was disturbed."""
    solved = SOLVED_STATE
    for i in range(5, 20):
        if not np.array_equal(state.corners[i], solved.corners[i]):
            return True
    for i in range(5, 30):
        if not np.array_equal(state.edges[i], solved.edges[i]):
            return True
    return False


def is_pure_co(state: MegaminxState) -> tuple[bool, list[int]]:
    """
    True if top corners are all back to correct position (permutation unchanged)
    but some are twisted. Returns (pure_co, [twist per top corner]).
    """
    solved = SOLVED_STATE
    twists = []
    for i in TOP_CORNERS:
        if state.corners[i, 0] != solved.corners[i, 0]:
            return False, []
        twists.append(int(state.corners[i, 1]))
    return True, twists


def is_pure_ep(state: MegaminxState) -> tuple[bool, str]:
    """
    True if top edge positions changed but orientations are 0 and corners untouched.
    Returns (pure_ep, cycle_description).
    """
    solved = SOLVED_STATE
    # Corners must be untouched
    for i in TOP_CORNERS:
        if not np.array_equal(state.corners[i], solved.corners[i]):
            return False, "corners moved"
    # Edges: build permutation mapping
    perm = []
    for i in TOP_EDGES:
        perm.append(int(state.edges[i, 0]))  # which piece is at slot i
        if state.edges[i, 1] != 0:
            return False, f"edge {i} flipped (ori={state.edges[i,1]})"
    # Describe cycle
    visited = [False] * 5
    cycles = []
    for start in range(5):
        if visited[start] or perm[start] == start:
            visited[start] = True
            continue
        cycle = [start]
        visited[start] = True
        cur = perm[start]
        while cur != start:
            cycle.append(cur)
            visited[cur] = True
            cur = perm[cur]
        cycles.append(cycle)
    if not cycles:
        return True, "identity"
    return True, " + ".join(f"({' '.join(str(x) for x in c)})" for c in cycles)


def check_alg(label: str, moves_str: str, expected: str):
    state = apply(moves_str)
    nt = non_top_moved(state)
    pure_co, twists = is_pure_co(state)
    pure_ep, ep_cycle = is_pure_ep(state)

    # CP check: top corners permuted (but may be twisted), edges intact
    edge_ok = all(np.array_equal(state.edges[i], SOLVED_STATE.edges[i]) for i in TOP_EDGES)
    edge_non_top_ok = all(np.array_equal(state.edges[i], SOLVED_STATE.edges[i]) for i in range(5, 30))

    corner_perm = [int(state.corners[i, 0]) for i in TOP_CORNERS]
    corner_ori  = [int(state.corners[i, 1]) for i in TOP_CORNERS]
    edge_perm   = [int(state.edges[i, 0]) for i in TOP_EDGES]
    edge_ori    = [int(state.edges[i, 1]) for i in TOP_EDGES]

    # Format output
    status_parts = []
    if nt:
        status_parts.append("⚠️  NON-TOP PIECES MOVED")

    if pure_ep:
        status_parts.append(f"EP: {ep_cycle}")
    elif pure_co:
        twist_str = " ".join(f"{t:+d}" for t in twists)
        nonzero = sum(1 for t in twists if t != 0)
        status_parts.append(f"CO: [{twist_str}]  ({nonzero} hjørner vridd)")
    else:
        # General case — show both
        perm_str = " ".join(f"{i}→{p}" for i, p in enumerate(corner_perm) if p != i)
        ori_str  = " ".join(f"{i}:{o:+d}" for i, o in enumerate(corner_ori) if o != 0)
        ep_str   = " ".join(f"{i}→{p}" for i, p in enumerate(edge_perm) if p != i)
        eo_str   = " ".join(f"{i}:{o:+d}" for i, o in enumerate(edge_ori) if o != 0)
        if perm_str:  status_parts.append(f"CP perm: {perm_str}")
        if ori_str:   status_parts.append(f"CP ori:  {ori_str}")
        if ep_str:    status_parts.append(f"EP perm: {ep_str}")
        if eo_str:    status_parts.append(f"EO:      {eo_str}")
        if not any([perm_str, ori_str, ep_str, eo_str]):
            status_parts.append("IDENTITY (ingen effekt)")

    ok = "✓" if not nt else "✗"
    print(f"  {ok} {label:<30} {moves_str[:45]:<45}  {' | '.join(status_parts)}")


def section(title: str):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print('='*80)


# ─────────────────────────────────────────────────────────────────
# METODE 1 + 3: EP, CP, CO
# ─────────────────────────────────────────────────────────────────
section("METODE 1+3 — EP (kantpermutasjon)")
check_alg("EP 1", "R++ U-- R-- U- R++ U-- R--", "3-sykel kanter mot klokken")
check_alg("EP 1⁻¹", "R++ U++ R-- U R++ U++ R--", "3-sykel kanter med klokken")

section("METODE 1+3 — CP / Niklas (hjørnepermutasjon)")
check_alg("Niklas", "L U- BR- U L- U- BR U", "3-sykel hjørner, +1 twist")
check_alg("Niklas⁻¹", "U- BR- U L U- BR U L-", "invers 3-sykel hjørner")

section("METODE 1+3 — CO (hjørneorientering)")
check_alg("Sune", "R U R- U R U-- R-", "+1 til 3 hjørner")
check_alg("Anti-Sune", "R- U- R U- R- U++ R", "+2 til 3 hjørner")

# ─────────────────────────────────────────────────────────────────
# METODE 4: OCLL — alle 16
# ─────────────────────────────────────────────────────────────────
section("METODE 4 — OCLL (alle 16, skal være pure CO)")

ocll = [
    ("CO 1",  "R U R- U R U R- U-- R U- R-"),
    ("CO 2",  "F R U++ R- U- R U- R- F-"),
    ("CO 3",  "R U++ R- U R U++ R-"),
    ("CO 4",  "R U R- U R U R- U-- R U- R-"),  # same as CO 1 per our notes
    ("CO 5",  "R U R- U R U-- R-"),             # Sune (U-- variant)
    ("CO 6",  "R- U- R U- R- U++ R"),           # Anti-Sune (U++ variant)
    ("CO 7",  "R U++ R- U- R U- R-"),
    ("CO 8",  "R U R- U++ R U++ R-"),
    ("CO 9",  "R U++ R- U- R U R- U- R U- R-"),
    ("CO 10", "R U R- U R U- R- U R U-- R-"),
    ("CO 11", "R U R- U R U R- U- R U-- R-"),
    ("CO 12", "R U-- R- U-- R U++ R- U-- R U- R-"),
    ("CO 13", "R U++ R-- U- R++ U- R-- U++ R"),
    ("CO 14", "R- U-- R++ U R-- U R++ U-- R-"),
    ("CO 15", "R U R- U++ R U-- R- U R U-- R-"),
    ("CO 16", "R U++ R- U- R U++ R- U-- R U- R-"),
]

for label, moves in ocll:
    check_alg(label, moves, "pure CO")

# ─────────────────────────────────────────────────────────────────
# METODE 4: EP — alle 5
# ─────────────────────────────────────────────────────────────────
section("METODE 4 — EP-algoritmer (alle 5)")

ep_algs = [
    ("EP 1",  "R++ U-- R-- U- R++ U-- R--"),
    ("EP 2",  "R++ U++ R-- U  R++ U++ R--"),
    ("EP 3",  "R U R- F- R U R- U- R- F R++ U- R-"),
    ("EP 4",  "R U R- U R- U- R++ U- R- U R- U R U++"),
    ("EP 5",  "BR L U++ BR- U L- BR U- L U++ BR- U++ L-"),
]

for label, moves in ep_algs:
    check_alg(label, moves, "pure EP")

# ─────────────────────────────────────────────────────────────────
# EKSTRA: Verifiser at EP 1 og EP 2 er inverse av hverandre
# ─────────────────────────────────────────────────────────────────
section("EKSTRA — EP 1 og EP 2 er inverse?")
s1 = apply("R++ U-- R-- U- R++ U-- R--")
s2 = apply("R++ U++ R-- U R++ U++ R--", s1)
identity = np.array_equal(s2.corners, SOLVED_STATE.corners) and np.array_equal(s2.edges, SOLVED_STATE.edges)
print(f"  {'✓' if identity else '✗'} EP1 ∘ EP2 = identitet: {identity}")

section("EKSTRA — Niklas ∘ Niklas⁻¹ = identitet?")
s1 = apply("L U- BR- U L- U- BR U")
s2 = apply("U- BR- U L U- BR U L-", s1)
identity = np.array_equal(s2.corners, SOLVED_STATE.corners) and np.array_equal(s2.edges, SOLVED_STATE.edges)
print(f"  {'✓' if identity else '✗'} Niklas ∘ Niklas⁻¹ = identitet: {identity}")

section("EKSTRA — Sune³ = identitet?")
s = copy_state(SOLVED_STATE)
for _ in range(3):
    s = apply("R U R- U R U-- R-", s)
identity = np.array_equal(s.corners, SOLVED_STATE.corners) and np.array_equal(s.edges, SOLVED_STATE.edges)
print(f"  {'✓' if identity else '✗'} Sune³ = identitet: {identity}")

print("\n")
