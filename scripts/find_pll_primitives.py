"""
Search for PLL primitives: pure-LL algorithms that are useful building blocks
for solving the combined CP+EP permutation stage after CO is solved.

Strategy:
1. BFS from SOLVED with pure-LL-preserving moves up to depth N
2. Collect all (EP, CP) fingerprints reachable, grouped by depth
3. Identify short algorithms for each unique (EP, CP) class
4. Report corner 3-cycles, edge 3-cycles, and combined patterns
"""

import sys
import os
import time
from collections import defaultdict
from itertools import product

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from megaminx.cube import SOLVED, apply_move
from megaminx.ll_catalog import (
    LL_CORNER_SLOTS, LL_EDGE_SLOTS, _LL_CORNER_SET, _LL_EDGE_SET,
    _make_ll_state, auf_canonical,
)

# ── Move set ──────────────────────────────────────────────────────────────────

MOVES = ["R", "R-", "F", "F-", "U", "U-", "U++", "U--"]
INVERSE = {"R": "R-", "R-": "R", "F": "F-", "F-": "F",
           "U": "U-", "U-": "U", "U++": "U--", "U--": "U++"}

# ── State fingerprinting ──────────────────────────────────────────────────────

def ll_fingerprint(state):
    """Return (CO, EP, CP) tuple for LL slots only."""
    co = tuple(state.co[s] for s in LL_CORNER_SLOTS)
    ep = tuple(state.ep[s] for s in LL_EDGE_SLOTS)
    cp = tuple(state.cp[s] for s in LL_CORNER_SLOTS)
    return (co, ep, cp)


def is_nll_preserved(state):
    """True if all non-LL pieces are in their solved positions."""
    for i in range(20):
        if i not in _LL_CORNER_SET:
            if state.cp[i] != i or state.co[i] != 0:
                return False
    for i in range(30):
        if i not in _LL_EDGE_SET:
            if state.ep[i] != i or state.eo[i] != 0:
                return False
    return True


SOLVED_FP = ll_fingerprint(SOLVED)
SOLVED_CO = SOLVED_FP[0]
SOLVED_EP = SOLVED_FP[1]
SOLVED_CP = SOLVED_FP[2]


def co_solved(fp):
    return fp[0] == SOLVED_CO


def ep_solved(fp):
    return fp[1] == SOLVED_EP


def cp_solved(fp):
    return fp[2] == SOLVED_CP


def is_3cycle_ep(ep):
    """True if EP is a pure 3-cycle (exactly 3 slots differ from solved)."""
    diffs = [i for i, (s, ref) in enumerate(zip(ep, SOLVED_EP)) if s != ref]
    if len(diffs) != 3:
        return False
    # Verify it's actually a 3-cycle (not two 2-cycles)
    a, b, c = diffs
    return (ep[a] == SOLVED_EP[b] and ep[b] == SOLVED_EP[c] and ep[c] == SOLVED_EP[a]) or \
           (ep[a] == SOLVED_EP[c] and ep[c] == SOLVED_EP[b] and ep[b] == SOLVED_EP[a])


def is_3cycle_cp(cp):
    """True if CP is a pure 3-cycle (exactly 3 slots differ from solved)."""
    diffs = [i for i, (s, ref) in enumerate(zip(cp, SOLVED_CP)) if s != ref]
    if len(diffs) != 3:
        return False
    a, b, c = diffs
    return (cp[a] == SOLVED_CP[b] and cp[b] == SOLVED_CP[c] and cp[c] == SOLVED_CP[a]) or \
           (cp[a] == SOLVED_CP[c] and cp[c] == SOLVED_CP[b] and cp[b] == SOLVED_CP[a])


def is_double_2swap_ep(ep):
    diffs = [i for i, (s, ref) in enumerate(zip(ep, SOLVED_EP)) if s != ref]
    return len(diffs) == 4


def is_double_2swap_cp(cp):
    diffs = [i for i, (s, ref) in enumerate(zip(cp, SOLVED_CP)) if s != ref]
    return len(diffs) == 4


# ── BFS ───────────────────────────────────────────────────────────────────────

def bfs_pure_ll(max_depth: int):
    """
    BFS from SOLVED, collecting pure-LL states with their shortest algorithm.
    Returns dict: fingerprint → (moves_list, depth)
    """
    # fingerprint → (moves, depth)
    seen = {SOLVED_FP: ([], 0)}
    frontier = [(SOLVED, [], SOLVED_FP)]

    for depth in range(1, max_depth + 1):
        next_frontier = []
        new_count = 0
        for state, moves, fp in frontier:
            for m in MOVES:
                # avoid trivial redundancy: don't undo last move
                if moves and m == INVERSE.get(moves[-1]):
                    continue
                new_state = apply_move(state, m)
                if not is_nll_preserved(new_state):
                    continue
                new_fp = ll_fingerprint(new_state)
                if new_fp not in seen:
                    new_moves = moves + [m]
                    seen[new_fp] = (new_moves, depth)
                    next_frontier.append((new_state, new_moves, new_fp))
                    new_count += 1
        print(f"  depth {depth}: +{new_count} new states, total {len(seen)}", flush=True)
        frontier = next_frontier
        if not frontier:
            break

    return seen


# ── Analysis ──────────────────────────────────────────────────────────────────

def analyze(seen):
    print("\n=== Classification ===")

    co0_states = {fp: v for fp, v in seen.items() if co_solved(fp)}
    print(f"\nCO=0 states: {len(co0_states)}")

    # EP 3-cycles with CO=0
    ep3_co0 = {fp: v for fp, v in co0_states.items()
               if is_3cycle_ep(fp[1]) and not cp_solved(fp)}
    print(f"  EP 3-cycle, CO=0: {len(ep3_co0)}")
    if ep3_co0:
        by_depth = defaultdict(list)
        for fp, (mv, d) in ep3_co0.items():
            by_depth[d].append((fp, mv))
        for d in sorted(by_depth):
            print(f"    depth {d}: {len(by_depth[d])} cases")
            for fp, mv in sorted(by_depth[d], key=lambda x: len(x[1]))[:3]:
                print(f"      EP={fp[1]}, CP={fp[2]}, alg: {' '.join(mv)}")

    # CP 3-cycles with CO=0
    cp3_co0 = {fp: v for fp, v in co0_states.items()
               if is_3cycle_cp(fp[2]) and not ep_solved(fp)}
    print(f"  CP 3-cycle, CO=0: {len(cp3_co0)}")
    if cp3_co0:
        by_depth = defaultdict(list)
        for fp, (mv, d) in cp3_co0.items():
            by_depth[d].append((fp, mv))
        for d in sorted(by_depth):
            print(f"    depth {d}: {len(by_depth[d])} cases")
            for fp, mv in sorted(by_depth[d], key=lambda x: len(x[1]))[:3]:
                print(f"      CP={fp[2]}, EP={fp[1]}, alg: {' '.join(mv)}")

    # Both EP and CP 3-cycles with CO=0 (simultaneous)
    both3_co0 = {fp: v for fp, v in co0_states.items()
                 if is_3cycle_ep(fp[1]) and is_3cycle_cp(fp[2])}
    print(f"  EP 3-cycle + CP 3-cycle, CO=0: {len(both3_co0)}")
    if both3_co0:
        by_depth = defaultdict(list)
        for fp, (mv, d) in both3_co0.items():
            by_depth[d].append((fp, mv))
        for d in sorted(by_depth):
            print(f"    depth {d}: {len(by_depth[d])} cases")
            for fp, mv in sorted(by_depth[d], key=lambda x: len(x[1]))[:5]:
                print(f"      EP={fp[1]}, CP={fp[2]}, alg: {' '.join(mv)}")

    # PLL-complete: CO=0, EP=solved, CP=solved  (should be identity only)
    pll_complete = {fp: v for fp, v in co0_states.items()
                    if ep_solved(fp) and cp_solved(fp)}
    print(f"\n  Full PLL solved (CO=EP=CP=0): {len(pll_complete)}")
    for fp, (mv, d) in list(pll_complete.items())[:5]:
        print(f"    depth {d}: {' '.join(mv) if mv else '(identity)'}")

    # States with any CO=0, EP=solved (CP still scrambled)
    ep_solved_co0 = {fp: v for fp, v in co0_states.items()
                     if ep_solved(fp) and not cp_solved(fp)}
    print(f"\n  CO=0, EP=solved, CP≠solved: {len(ep_solved_co0)}")
    if ep_solved_co0:
        by_depth = defaultdict(list)
        for fp, (mv, d) in ep_solved_co0.items():
            by_depth[d].append((fp, mv))
        for d in sorted(by_depth):
            print(f"    depth {d}: {len(by_depth[d])} states")
            for fp, mv in sorted(by_depth[d], key=lambda x: len(x[1]))[:3]:
                print(f"      CP={fp[2]}, alg: {' '.join(mv)}")

    return ep3_co0, cp3_co0, both3_co0


# ── Fc1 known algorithm analysis ──────────────────────────────────────────────

def analyze_fc1(seen):
    print("\n=== Fc1 / Fc2 analysis ===")
    fc1 = ["F", "R", "U", "R-", "U-", "F-"]
    fc2 = ["F", "U", "R", "U-", "R-", "F-"]

    for name, moves in [("Fc1", fc1), ("Fc2", fc2)]:
        state = SOLVED
        for m in moves:
            state = apply_move(state, m)
        fp = ll_fingerprint(state)
        nll_ok = is_nll_preserved(state)
        print(f"\n{name}: {' '.join(moves)}")
        print(f"  CO: {fp[0]}")
        print(f"  EP: {fp[1]}")
        print(f"  CP: {fp[2]}")
        print(f"  non-LL preserved: {nll_ok}")
        print(f"  EP 3-cycle: {is_3cycle_ep(fp[1])}")
        print(f"  CP unchanged: {cp_solved(fp)}")


# ── AUF-normalized CP class analysis ─────────────────────────────────────────

def auf_normalize_cp(fp):
    """Normalize under U rotations for CP and EP simultaneously."""
    co, ep, cp = fp
    # Treat as (co, ep, cp) triple and find lex-minimum under U-rotation
    # Using auf_canonical from ll_catalog
    return auf_canonical(co, cp, ep)  # note: auf_canonical takes (co, cp, ep)


def count_pll_classes(seen):
    """Count distinct PLL classes (CO=0) under AUF equivalence."""
    print("\n=== PLL case counting (CO=0, AUF-normalized) ===")
    co0 = {fp: v for fp, v in seen.items() if co_solved(fp)}
    print(f"Total CO=0 states: {len(co0)}")

    # Group by AUF class
    classes = defaultdict(list)
    for fp, v in co0.items():
        # Normalize: apply AUF to both EP and CP simultaneously
        # auf_canonical takes (co, cp, ep) → normalized
        normed = auf_canonical(fp[0], fp[2], fp[1])  # (co, cp_norm, ep_norm)
        classes[normed].append((fp, v))

    print(f"AUF-normalized PLL classes: {len(classes)}")

    # Analyze class structure
    by_type = defaultdict(int)
    for normed, members in classes.items():
        _, cp, ep = normed
        cp_type = "cp3" if is_3cycle_cp(cp) else ("cp22" if is_double_2swap_cp(cp) else ("cp5" if cp != SOLVED_CP else "cp0"))
        ep_type = "ep3" if is_3cycle_ep(ep) else ("ep22" if is_double_2swap_ep(ep) else ("ep5" if ep != SOLVED_EP else "ep0"))
        label = f"{cp_type}+{ep_type}"
        by_type[label] += 1

    print("Class types (CP_type + EP_type):")
    for label, count in sorted(by_type.items()):
        print(f"  {label}: {count} classes")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    max_depth = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    print(f"BFS: pure-LL states with ⟨R,F,U⟩, max depth {max_depth}")
    print(f"(move set: {MOVES})")

    t0 = time.time()
    seen = bfs_pure_ll(max_depth)
    print(f"\nTotal pure-LL states found: {len(seen)}  ({time.time()-t0:.1f}s)")

    analyze_fc1(seen)
    analyze(seen)
    count_pll_classes(seen)
