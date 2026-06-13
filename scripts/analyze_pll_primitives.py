#!/usr/bin/env python3
"""
Analyze PLL coverage using CO-cancelling pairs as primitive generators.

Builds a generator database from all CO-algorithm pairs (with AUF between)
that cancel CO effects and leave non-LL pieces clean. Includes AUF variants
and inverses of each generator.

Then runs BFS to find how many of the 3600 PLL states (A₅×A₅ = EP×CP even
permutations, CO=0) are reachable within a given number of generator applications.

Key result (found 2026-06-11): all 3600 states reachable in ≤5 applications.

Usage:
    python3 scripts/analyze_pll_primitives.py
    python3 scripts/analyze_pll_primitives.py --max-depth 4
    python3 scripts/analyze_pll_primitives.py --show-generators
"""
from __future__ import annotations
import sys
import itertools
import argparse
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from megaminx.cube import SOLVED, apply_move
from megaminx.ll_catalog import (
    LL_CORNER_SLOTS, LL_EDGE_SLOTS, _LL_CORNER_SET, _LL_EDGE_SET,
    _make_ll_state, _perm_parity,
)

# CO algorithms + Fc1/Fc2 (pure EP generators that damage CO — included
# because CO-pair compositions can cancel their CO damage)
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
    "Fc1":   ["U", "R", "F", "R-", "F-", "U-"],
    "Fc2":   ["U", "F", "R", "F-", "R-", "U-"],
}

AUF_SEQS = [[], ["U"], ["U++"], ["U-"], ["U--"]]
INVERSE = {
    "R": "R-", "R-": "R",
    "F": "F-", "F-": "F",
    "F++": "F--", "F--": "F++",
    "U": "U-", "U-": "U",
    "U++": "U--", "U--": "U++",
}

ID_CP = tuple(LL_CORNER_SLOTS)
ID_EP = tuple(LL_EDGE_SLOTS)


def inv_seq(seq):
    return [INVERSE[m] for m in reversed(seq)]


def apply_moves(state, moves):
    for m in moves:
        state = apply_move(state, m)
    return state


def pll_fp(state):
    return (
        tuple(state.ep[s] for s in LL_EDGE_SLOTS),
        tuple(state.cp[s] for s in LL_CORNER_SLOTS),
    )


def nll_co_ok(state):
    """Check: non-LL pieces clean AND all LL corners have CO=0."""
    return all(
        state.cp[i] == i and state.co[i] == 0 for i in range(20)
        if i not in _LL_CORNER_SET
    ) and all(
        state.ep[i] == i and state.eo[i] == 0 for i in range(30)
        if i not in _LL_EDGE_SET
    ) and all(state.co[s] == 0 for s in LL_CORNER_SLOTS)


def describe_perm(perm, identity):
    diffs = sum(1 for a, b in zip(perm, identity) if a != b)
    return {0: "id", 3: "3cyc", 4: "2x2", 5: "5cyc"}.get(diffs, f"{diffs}moved")


def build_generator_db(show: bool = False) -> dict:
    """
    Build generator DB: maps PLL fingerprint → (label, move_count, sequence).

    For each CO-algorithm pair with AUF between them, check if the composition:
    1. Has CO=0 on all LL corners
    2. Leaves non-LL pieces clean
    3. Has non-trivial (EP, CP) fingerprint

    Also adds AUF prefix variants and inverses of each valid pair.
    """
    gen_db: dict = {}

    for (n1, a1), (n2, a2) in itertools.product(CO_ALGS.items(), repeat=2):
        for auf in AUF_SEQS:
            seq = a1 + auf + a2
            state = apply_moves(SOLVED, seq)
            if not nll_co_ok(state):
                continue
            fp = pll_fp(state)
            if fp[0] == ID_EP and fp[1] == ID_CP:
                continue  # identity

            label = f"{n1}+{len(auf)}auf+{n2}"
            if fp not in gen_db or len(seq) < gen_db[fp][1]:
                gen_db[fp] = (label, len(seq), seq)

            # AUF prefix variants
            for auf2 in AUF_SEQS:
                if not auf2:
                    continue
                seq2 = auf2 + seq
                state2 = apply_moves(SOLVED, seq2)
                if not nll_co_ok(state2):
                    continue
                fp2 = pll_fp(state2)
                if fp2[0] == ID_EP and fp2[1] == ID_CP:
                    continue
                lbl2 = f"auf+{label}"
                if fp2 not in gen_db or len(seq2) < gen_db[fp2][1]:
                    gen_db[fp2] = (lbl2, len(seq2), seq2)

            # Inverse
            seq_inv = inv_seq(seq)
            state_inv = apply_moves(SOLVED, seq_inv)
            if not nll_co_ok(state_inv):
                continue
            fp_inv = pll_fp(state_inv)
            if fp_inv[0] == ID_EP and fp_inv[1] == ID_CP:
                continue
            lbl_inv = f"({n1}+{n2})^-1"
            if fp_inv not in gen_db or len(seq_inv) < gen_db[fp_inv][1]:
                gen_db[fp_inv] = (lbl_inv, len(seq_inv), seq_inv)

            # AUF prefix + inverse
            for auf2 in AUF_SEQS:
                if not auf2:
                    continue
                seq2 = auf2 + seq_inv
                state2 = apply_moves(SOLVED, seq2)
                if not nll_co_ok(state2):
                    continue
                fp2 = pll_fp(state2)
                if fp2[0] == ID_EP and fp2[1] == ID_CP:
                    continue
                lbl2 = f"auf+({n1}+{n2})^-1"
                if fp2 not in gen_db or len(seq2) < gen_db[fp2][1]:
                    gen_db[fp2] = (lbl2, len(seq2), seq2)

    if show:
        print(f"Generator DB: {len(gen_db)} unique PLL fingerprints\n")
        ep_cp_counts: dict[str, int] = {}
        for ep, cp in gen_db:
            key = f"EP={describe_perm(ep, ID_EP):5s} CP={describe_perm(cp, ID_CP):5s}"
            ep_cp_counts[key] = ep_cp_counts.get(key, 0) + 1
        for k, v in sorted(ep_cp_counts.items()):
            print(f"  {k}: {v} generators")

    return gen_db


def count_all_pll_states() -> set:
    """Enumerate all 3600 PLL states (A₅×A₅, CO=0)."""
    ID_CO = (0,) * 5
    all_pll = set()
    for ep in itertools.permutations(ID_EP):
        if _perm_parity(ep, ID_EP) != 0:
            continue
        for cp in itertools.permutations(ID_CP):
            if _perm_parity(cp, ID_CP) != 0:
                continue
            if ep == ID_EP and cp == ID_CP:
                continue
            state = _make_ll_state(ID_CO, cp, ep)
            all_pll.add(pll_fp(state))
    return all_pll


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze PLL coverage using CO-pair generators")
    parser.add_argument("--max-depth", type=int, default=5,
                        help="Maximum BFS depth (number of generator applications, default: 5)")
    parser.add_argument("--show-generators", action="store_true",
                        help="Print generator DB summary before BFS")
    parser.add_argument("--show-missing", action="store_true",
                        help="After BFS, show which PLL types are not yet covered")
    args = parser.parse_args()

    print("Building generator database...")
    gen_db = build_generator_db(show=args.show_generators)
    print(f"  {len(gen_db)} unique PLL fingerprints as generators\n")

    print(f"Running BFS to depth {args.max_depth}...")
    ID_FP = (ID_EP, ID_CP)
    visited: dict = {ID_FP: (0, SOLVED)}
    queue: deque = deque([(SOLVED, 0)])

    while queue:
        state, depth = queue.popleft()
        if depth >= args.max_depth:
            continue
        for fp_g, (lbl, n, seq) in gen_db.items():
            new_state = apply_moves(state, seq)
            new_fp = pll_fp(new_state)
            if new_fp not in visited and nll_co_ok(new_state):
                visited[new_fp] = (depth + 1, new_state)
                queue.append((new_state, depth + 1))

    print(f"\nStates reachable: {len(visited) - 1} / 3599 (excluding identity)")
    by_depth: dict[int, int] = {}
    for fp, (d, _) in visited.items():
        by_depth[d] = by_depth.get(d, 0) + 1
    print(f"By depth: {dict(sorted(by_depth.items()))}")

    total_pll = 3600
    if len(visited) - 1 < total_pll - 1:
        print(f"\nNot all states reached. Computing missing states...")
        all_pll = count_all_pll_states()
        visited_pll = set(visited.keys()) - {ID_FP}
        missing = all_pll - visited_pll
        print(f"Missing: {len(missing)} states")

        if args.show_missing:
            miss_types: dict[str, int] = {}
            for ep, cp in missing:
                key = f"EP={describe_perm(ep, ID_EP):5s} CP={describe_perm(cp, ID_CP):5s}"
                miss_types[key] = miss_types.get(key, 0) + 1
            for k, v in sorted(miss_types.items()):
                print(f"  {k}: {v} missing")
    else:
        print("\nAll 3599 non-identity PLL states reachable!")


if __name__ == "__main__":
    main()
