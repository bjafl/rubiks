"""
PLL catalog search for Megaminx LL.

After CO is solved, we need algorithms that solve EP + CP simultaneously.
This script:
1. Enumerates all (EP, CP) AUF-equivalence classes (combined normalization)
2. Searches for short DFS algorithms for each class
3. Reports structure and identifies useful primitives

Key insight: EP and CP cannot be solved independently on Megaminx
(any pure-LL alg that changes CP also changes EP). So PLL must handle both together.
"""

import sys
import os
import time
import itertools

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from megaminx.cube import SOLVED, apply_move
from megaminx.ll_catalog import (
    LL_CORNER_SLOTS, LL_EDGE_SLOTS, _LL_CORNER_SET, _LL_EDGE_SET,
    LLStage, _make_ll_state, _find_solutions, _apply_auf, auf_canonical,
    _perm_parity,
)

# ── PLL stage: solves EP and CP together, requires CO already solved ──────────

PLL_STAGE = LLStage(
    name="pll",
    solve_co=False,
    solve_ep=True,
    solve_cp=True,
    require_co_solved=True,
    require_ep_solved=False,
    require_cp_solved=False,
)

# ── Combined (EP, CP) case enumeration ────────────────────────────────────────

def enumerate_pll_cases() -> list[tuple]:
    """
    Enumerate all AUF-equivalence classes for combined (EP, CP) PLL states.
    Returns list of canonical (ll_co, ll_cp, ll_ep) tuples.
    CO is always (0,0,0,0,0); states are non-trivial (not fully solved).
    """
    identity_co = (0,) * 5
    identity_cp = tuple(LL_CORNER_SLOTS)
    identity_ep = tuple(LL_EDGE_SLOTS)

    seen: set = set()
    cases: list[tuple] = []

    # Even EP permutations
    even_ep = [ep for ep in itertools.permutations(LL_EDGE_SLOTS)
               if _perm_parity(ep, identity_ep) == 0]
    # Even CP permutations
    even_cp = [cp for cp in itertools.permutations(LL_CORNER_SLOTS)
               if _perm_parity(cp, identity_cp) == 0]

    for ep in even_ep:
        for cp in even_cp:
            if ep == identity_ep and cp == identity_cp:
                continue  # skip fully solved

            # AUF-normalize the combined (CO, CP, EP) — same ring-shift for all
            canonical = auf_canonical(identity_co, cp, ep)
            key = canonical  # full 3-tuple as key
            if key not in seen:
                seen.add(key)
                cases.append(canonical)

    return cases


# ── DFS search (reuses _find_solutions from ll_catalog) ───────────────────────

MOVE_SET = ["R", "R-", "F", "F-", "U", "U-", "U++", "U--"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def describe_perm(perm: tuple, identity: tuple, label: str) -> str:
    diffs = sum(1 for a, b in zip(perm, identity) if a != b)
    n_moved = diffs
    if n_moved == 0:
        return f"{label}=identity"
    elif n_moved == 3:
        return f"{label}=3cyc"
    elif n_moved == 5:
        return f"{label}=5cyc"
    elif n_moved == 4:
        return f"{label}=2x2swap"
    else:
        return f"{label}={n_moved}moved"


def fmt_state(ll_co, ll_cp, ll_ep) -> str:
    id_cp = tuple(LL_CORNER_SLOTS)
    id_ep = tuple(LL_EDGE_SLOTS)
    cp_desc = describe_perm(ll_cp, id_cp, "CP")
    ep_desc = describe_perm(ll_ep, id_ep, "EP")
    return f"{cp_desc}, {ep_desc}"


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    max_depth = int(sys.argv[1]) if len(sys.argv) > 1 else 12

    print("=== PLL case enumeration ===")
    t0 = time.time()
    cases = enumerate_pll_cases()
    print(f"Total PLL cases (AUF-normalized, CO=0): {len(cases)}")

    # Count by type
    id_cp = tuple(LL_CORNER_SLOTS)
    id_ep = tuple(LL_EDGE_SLOTS)

    by_type = {}
    for ll_co, ll_cp, ll_ep in cases:
        cp_desc = describe_perm(ll_cp, id_cp, "CP").split("=")[1]
        ep_desc = describe_perm(ll_ep, id_ep, "EP").split("=")[1]
        key = f"CP:{cp_desc} EP:{ep_desc}"
        by_type[key] = by_type.get(key, 0) + 1

    print("\nBreakdown by (CP type, EP type):")
    for k, v in sorted(by_type.items()):
        print(f"  {k}: {v} cases")

    print(f"\n=== DFS search (max depth {max_depth}) ===")
    print(f"Move set: {MOVE_SET}")
    print()

    solved_count = 0
    total = len(cases)
    results = []

    for i, (ll_co, ll_cp, ll_ep) in enumerate(cases):
        state = _make_ll_state(ll_co, ll_cp, ll_ep)
        t1 = time.time()
        solutions = _find_solutions(state, PLL_STAGE, MOVE_SET, max_depth)
        elapsed = time.time() - t1

        desc = fmt_state(ll_co, ll_cp, ll_ep)
        if solutions:
            best = solutions[0]
            print(f"  [{i+1:2d}/{total}] {desc:40s} → {best.length:2d} moves  {' '.join(best.moves)}  ({elapsed:.1f}s)")
            solved_count += 1
            results.append((best.length, desc, best.moves, ll_co, ll_cp, ll_ep))
        else:
            print(f"  [{i+1:2d}/{total}] {desc:40s} → NOT FOUND at depth {max_depth}  ({elapsed:.1f}s)")
        sys.stdout.flush()

    print(f"\n=== Summary ===")
    print(f"Solved: {solved_count}/{total}")
    if results:
        results.sort()
        lengths = [r[0] for r in results]
        print(f"Min length: {min(lengths)}")
        print(f"Max length: {max(lengths)}")
        print(f"Mean length: {sum(lengths)/len(lengths):.1f}")
        print("\nShortest 10 algorithms:")
        for length, desc, moves, _, _, _ in results[:10]:
            print(f"  {length:2d}  {desc:40s}  {' '.join(moves)}")
