#!/usr/bin/env python3
"""
Analyze CO-algorithm pairs (with AUF between) that cancel CO effects.

For each pair (alg1, AUF_k, alg2), compose the sequence from SOLVED and check:
  - Does CO net to zero?
  - Are non-LL pieces clean at the endpoint?
  - What EP and CP permutations result?

This reveals which EP/CP effects can be generated for free by combining
existing CO algorithms — the building blocks for EP and CP stage algorithms.

Usage:
    python3 scripts/analyze_co_pairs.py
    python3 scripts/analyze_co_pairs.py --show-all
    python3 scripts/analyze_co_pairs.py --pure-ep     # only CO=0, CP=id cases
    python3 scripts/analyze_co_pairs.py --pure-cp     # only CO=0, EP=id cases
"""
from __future__ import annotations
import sys
import argparse
import itertools
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from megaminx.cube import SOLVED, apply_move
from megaminx.ll_catalog import (
    LL_CORNER_SLOTS, LL_EDGE_SLOTS, _LL_CORNER_SET, _LL_EDGE_SET,
)

# CO algorithms (canonical — each solves one CO case from SOLVED)
CO_ALGS: dict[str, list[str]] = {
    "co_002": ["F--"],
    "co_011": ["F"],
    "co_003": ["R-", "F-", "R", "F-", "R-", "F++", "R"],
    "co_008": ["R-", "F++", "R", "F++", "R-", "F", "R"],
    "co_010": ["R-", "F++", "R", "F", "R-", "F++", "R"],
    "co_000": ["R", "F++", "R-", "F", "R", "F++", "R-", "F"],
    "co_005": ["R-", "F-", "R", "F--", "R-", "F--", "R", "F--"],
    "co_006": ["R", "F--", "R-", "F--", "R", "F-", "R-", "F++"],
    "co_012": ["R-", "F-", "R", "F-", "R-", "F++", "R", "F--"],
    "co_014": ["R-", "F-", "R", "F--", "R-", "F--", "R", "F++"],
    "co_015": ["R-", "F--", "R", "F", "R-", "F", "R", "F++"],
    "co_001": ["F", "R-", "F--", "R", "F", "R-", "F", "R", "F-"],
    "co_004": ["F-", "R", "F", "R-", "F", "R", "F--", "R-", "F-"],
    "co_007": ["F", "R-", "F++", "R", "F++", "R-", "F", "R", "F-"],
    "co_013": ["F++", "R-", "F--", "R", "F", "R-", "F", "R", "F-"],
    "co_009": ["R-", "F-", "R", "F-", "R-", "F", "R", "F-", "R-", "F++", "R"],
}

AUF_MOVES: dict[int, list[str]] = {
    0: [],
    1: ["U"],
    2: ["U++"],
    3: ["U-"],
    4: ["U--"],
}

ID_CP = tuple(LL_CORNER_SLOTS)
ID_EP = tuple(LL_EDGE_SLOTS)


def apply_moves(state, moves):
    for m in moves:
        state = apply_move(state, m)
    return state


def ll_co(state):
    return tuple(state.co[s] for s in LL_CORNER_SLOTS)


def ll_ep(state):
    return tuple(state.ep[s] for s in LL_EDGE_SLOTS)


def ll_cp(state):
    return tuple(state.cp[s] for s in LL_CORNER_SLOTS)


def describe_perm(perm, identity):
    diffs = sum(1 for a, b in zip(perm, identity) if a != b)
    return {0: "id", 3: "3cyc", 4: "2x2", 5: "5cyc"}.get(diffs, f"{diffs}moved")


def nll_ok(state):
    return all(
        state.cp[i] == i and state.co[i] == 0 for i in range(20)
        if i not in _LL_CORNER_SET
    ) and all(
        state.ep[i] == i and state.eo[i] == 0 for i in range(30)
        if i not in _LL_EDGE_SET
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze CO-algorithm pairs with AUF between them")
    parser.add_argument("--show-all", action="store_true",
                        help="Print all CO-cancelling pairs (not just the best per type)")
    parser.add_argument("--pure-ep", action="store_true",
                        help="Show only cases where CP=id (pure EP effect)")
    parser.add_argument("--pure-cp", action="store_true",
                        help="Show only cases where EP=id (pure CP effect)")
    parser.add_argument("--nll-only", action="store_true", default=True,
                        help="Only count NLL-clean results (default: True)")
    args = parser.parse_args()

    results = []
    for (n1, a1), (n2, a2) in itertools.product(CO_ALGS.items(), repeat=2):
        for k, auf in AUF_MOVES.items():
            seq = a1 + auf + a2
            state = apply_moves(SOLVED, seq)
            co = ll_co(state)
            if not all(c == 0 for c in co):
                continue
            ep = ll_ep(state)
            cp = ll_cp(state)
            ep_desc = describe_perm(ep, ID_EP)
            cp_desc = describe_perm(cp, ID_CP)
            is_nll = nll_ok(state)
            results.append((len(seq), n1, k, n2, ep_desc, cp_desc, is_nll, seq))

    results.sort(key=lambda r: (r[0], r[4], r[5]))

    # Group by (EP-type, CP-type)
    seen: dict = {}
    for length, n1, k, n2, ep_desc, cp_desc, is_nll, seq in results:
        key = (ep_desc, cp_desc)
        if key not in seen:
            seen[key] = []
        seen[key].append((length, n1, k, n2, is_nll, seq))

    if args.pure_ep:
        seen = {k: v for k, v in seen.items() if k[1] == "id" and k[0] != "id"}
    elif args.pure_cp:
        seen = {k: v for k, v in seen.items() if k[0] == "id" and k[1] != "id"}

    print("=== CO-cancelling pairs: EP/CP effects ===\n")
    print(f"  {'EP':6s}  {'CP':6s}  {'entries':>7s}  {'shortest':>8s}  Example")
    print("  " + "-" * 65)

    for (ep_desc, cp_desc), entries in sorted(seen.items(), key=lambda x: (x[0][0], x[0][1])):
        nll_entries = [e for e in entries if e[4]]
        tag = ""
        if ep_desc == "id" and cp_desc != "id":
            tag = "  ← PURE CP"
        elif cp_desc == "id" and ep_desc != "id":
            tag = "  ← PURE EP"
        count = len(nll_entries) if args.nll_only else len(entries)
        best_entries = nll_entries if args.nll_only else entries
        if not best_entries:
            continue
        best = best_entries[0]
        print(f"  EP={ep_desc:5s}  CP={cp_desc:5s}  {count:>7d}  {best[0]:>8d}  "
              f"{best[1]}+U^{best[2]}+{best[3]}{tag}")

        if args.show_all:
            for length, n1, k, n2, is_nll, seq in best_entries:
                nll_str = "" if is_nll else " [NLL!]"
                print(f"    {length:2d}t  {' '.join(seq)}{nll_str}")
            print()

    print(f"\n=== Useful non-trivial cases (NLL=True, non-identity) ===\n")
    for (ep_desc, cp_desc), entries in sorted(seen.items()):
        nll_entries = [e for e in entries if e[4]]
        if not nll_entries or (ep_desc == "id" and cp_desc == "id"):
            continue
        best = nll_entries[0]
        tag = ""
        if ep_desc == "id":
            tag = "  ← PURE CP!"
        elif cp_desc == "id":
            tag = "  ← PURE EP!"
        print(f"  EP={ep_desc:5s}  CP={cp_desc:5s}  len={best[0]:2d}  "
              f"{best[1]}+U^{best[2]}+{best[3]}{tag}")
        print(f"    Moves: {' '.join(best[5])}")


if __name__ == "__main__":
    main()
