"""
Verifiserer alle LL-algoritmer fra megaminx-ll-metode{1-3,4}.md
mot Megaminx-simulatoren.
"""
from __future__ import annotations
from megaminx.cube import SOLVED, MegaminxState, CORNERS, EDGES
from megaminx.moves import apply_sequence

# Top corner/edge indices (adjacent to U face)
TOP_CORNERS = [i for i, c in enumerate(CORNERS) if "U" in c]   # [0, 4, 7, 18, 19]
TOP_EDGES   = [i for i, e in enumerate(EDGES)   if "U" in e]   # [4, 8, 27, 28, 29]


def apply(moves_str: str, state: MegaminxState | None = None) -> MegaminxState:
    """Apply a space-separated move string to a solved state (or given state)."""
    if state is None:
        state = SOLVED
    return apply_sequence(state, moves_str.split())


def delta_corners(state: MegaminxState) -> dict:
    result = {}
    for i in TOP_CORNERS:
        if state.cp[i] != SOLVED.cp[i] or state.co[i] != SOLVED.co[i]:
            result[i] = (state.cp[i], state.co[i])
    return result


def delta_edges(state: MegaminxState) -> dict:
    result = {}
    for i in TOP_EDGES:
        if state.ep[i] != SOLVED.ep[i] or state.eo[i] != SOLVED.eo[i]:
            result[i] = (state.ep[i], state.eo[i])
    return result


def non_top_moved(state: MegaminxState) -> bool:
    ll_c = frozenset(TOP_CORNERS)
    ll_e = frozenset(TOP_EDGES)
    for i in range(20):
        if i not in ll_c and (state.cp[i] != i or state.co[i] != 0):
            return True
    for i in range(30):
        if i not in ll_e and (state.ep[i] != i or state.eo[i] != 0):
            return True
    return False


def is_pure_co(state: MegaminxState) -> tuple[bool, list[int]]:
    twists = []
    for i in TOP_CORNERS:
        if state.cp[i] != SOLVED.cp[i]:
            return False, []
        twists.append(state.co[i])
    return True, twists


def is_pure_ep(state: MegaminxState) -> tuple[bool, str]:
    for i in TOP_CORNERS:
        if state.cp[i] != SOLVED.cp[i] or state.co[i] != SOLVED.co[i]:
            return False, "corners moved"
    perm = [state.ep[i] for i in TOP_EDGES]
    for i in TOP_EDGES:
        if state.eo[i] != 0:
            return False, f"edge slot {i} flipped"
    visited = [False] * 5
    cycles = []
    for start in range(5):
        if visited[start] or perm[start] == TOP_EDGES[start]:
            visited[start] = True
            continue
        cycle = [start]
        visited[start] = True
        cur = TOP_EDGES.index(perm[start]) if perm[start] in TOP_EDGES else -1
        while cur != start and cur >= 0:
            cycle.append(cur)
            visited[cur] = True
            next_val = perm[cur]
            cur = TOP_EDGES.index(next_val) if next_val in TOP_EDGES else -1
        cycles.append(cycle)
    if not cycles:
        return True, "identity"
    return True, " + ".join(f"({' '.join(str(x) for x in c)})" for c in cycles)


def check_alg(label: str, moves_str: str, expected: str):
    state = apply(moves_str)
    nt = non_top_moved(state)
    pure_co, twists = is_pure_co(state)
    pure_ep, ep_cycle = is_pure_ep(state)

    corner_perm = [state.cp[i] for i in TOP_CORNERS]
    corner_ori  = [state.co[i] for i in TOP_CORNERS]
    edge_perm   = [state.ep[i] for i in TOP_EDGES]
    edge_ori    = [state.eo[i] for i in TOP_EDGES]

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
        perm_str = " ".join(
            f"{TOP_CORNERS[k]}→{p}" for k, (i, p) in enumerate(zip(TOP_CORNERS, corner_perm)) if p != i
        )
        ori_str = " ".join(
            f"{i}:{o:+d}" for i, o in zip(TOP_CORNERS, corner_ori) if o != 0
        )
        ep_str = " ".join(
            f"{TOP_EDGES[k]}→{p}" for k, (i, p) in enumerate(zip(TOP_EDGES, edge_perm)) if p != i
        )
        eo_str = " ".join(
            f"{i}:{o:+d}" for i, o in zip(TOP_EDGES, edge_ori) if o != 0
        )
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
    ("CO 4",  "R U R- U R U R- U-- R U- R-"),
    ("CO 5",  "R U R- U R U-- R-"),
    ("CO 6",  "R- U- R U- R- U++ R"),
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
# EKSTRA
# ─────────────────────────────────────────────────────────────────
section("EKSTRA — EP 1 og EP 2 er inverse?")
s1 = apply("R++ U-- R-- U- R++ U-- R--")
s2 = apply("R++ U++ R-- U R++ U++ R--", s1)
identity = (s2 == SOLVED)
print(f"  {'✓' if identity else '✗'} EP1 ∘ EP2 = identitet: {identity}")

section("EKSTRA — Niklas ∘ Niklas⁻¹ = identitet?")
s1 = apply("L U- BR- U L- U- BR U")
s2 = apply("U- BR- U L U- BR U L-", s1)
identity = (s2 == SOLVED)
print(f"  {'✓' if identity else '✗'} Niklas ∘ Niklas⁻¹ = identitet: {identity}")

section("EKSTRA — Sune³ = identitet?")
s = SOLVED
for _ in range(3):
    s = apply("R U R- U R U-- R-", s)
identity = (s == SOLVED)
print(f"  {'✓' if identity else '✗'} Sune³ = identitet: {identity}")

print("\n")
