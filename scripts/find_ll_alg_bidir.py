#!/usr/bin/env python3
"""
Bidirectional BFS to find LL algorithms for a given stage and case index.

Solves pure-LL problems where non-LL pieces may be temporarily disturbed
but must be clean at the terminal state. Bidirectional BFS is dramatically
faster than DFS for depths 14+: O(2·8^(n/2)) vs O(8^n).

Usage:
    python3 scripts/find_ll_alg_bidir.py --stage ep --case 6
    python3 scripts/find_ll_alg_bidir.py --stage cp --case-idx 2 --max-half-depth 9
    python3 scripts/find_ll_alg_bidir.py --stage ep --all
    python3 scripts/find_ll_alg_bidir.py --stage cp --all --max-half-depth 9
"""
from __future__ import annotations
import sys
import time
import argparse
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from megaminx.cube import SOLVED, apply_move
from megaminx.ll_catalog import (
    _make_ll_state, enumerate_cases,
    EP_STAGE, CP_STAGE_CO_FIRST,
)

MOVES = ["R", "R-", "F", "F-", "U", "U-", "U++", "U--"]
INVERSE = {
    "R": "R-", "R-": "R",
    "F": "F-", "F-": "F",
    "U": "U-", "U-": "U",
    "U++": "U--", "U--": "U++",
}

STAGES = {
    "ep": EP_STAGE,
    "cp": CP_STAGE_CO_FIRST,
}


def apply_moves(state, moves):
    for m in moves:
        state = apply_move(state, m)
    return state


def bidir_bfs(start_state, stage, max_half_depth: int = 9, time_limit: float | None = None):
    """
    Bidirectional BFS: forward from start_state, backward from SOLVED.

    Returns the solution move list, or None if not found within limits.

    Both searches expand simultaneously. A solution is found when a state
    appears in both the forward and backward frontiers. The full path is
    reconstructed and verified with stage.is_solved() before returning.
    """
    t0 = time.time()

    # Forward: maps state → path from start_state
    fwd: dict = {start_state: []}
    fwd_q: deque = deque([(start_state, [])])

    # Backward: maps state → path from SOLVED (each step is a forward move;
    # to reconstruct the solution we reverse and invert this path)
    bwd: dict = {SOLVED: []}
    bwd_q: deque = deque([(SOLVED, [])])

    for half_depth in range(1, max_half_depth + 1):
        if time_limit and (time.time() - t0) > time_limit:
            return None

        # Expand forward one level
        while fwd_q and len(fwd_q[0][1]) < half_depth:
            state, path = fwd_q.popleft()
            last_face = path[-1].rstrip("-+") if path else None
            for m in MOVES:
                if m.rstrip("-+") == last_face:
                    continue
                new_state = apply_move(state, m)
                if new_state not in fwd:
                    new_path = path + [m]
                    fwd[new_state] = new_path
                    fwd_q.append((new_state, new_path))
                    if new_state in bwd:
                        candidate = new_path + [INVERSE[m2] for m2 in reversed(bwd[new_state])]
                        if stage.is_solved(apply_moves(start_state, candidate)):
                            return candidate

        # Expand backward one level
        while bwd_q and len(bwd_q[0][1]) < half_depth:
            state, path = bwd_q.popleft()
            last_face = path[-1].rstrip("-+") if path else None
            for m in MOVES:
                if m.rstrip("-+") == last_face:
                    continue
                new_state = apply_move(state, m)
                if new_state not in bwd:
                    new_path = path + [m]
                    bwd[new_state] = new_path
                    bwd_q.append((new_state, new_path))
                    if new_state in fwd:
                        candidate = fwd[new_state] + [INVERSE[m2] for m2 in reversed(new_path)]
                        if stage.is_solved(apply_moves(start_state, candidate)):
                            return candidate

        print(f"    half_depth={half_depth}: fwd={len(fwd)}, bwd={len(bwd)}", flush=True)

    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Bidirectional BFS for LL stage algorithms")
    parser.add_argument("--stage", choices=list(STAGES), required=True,
                        help="LL stage to solve (ep or cp)")
    parser.add_argument("--case", "--case-idx", dest="case_idx", type=int, default=None,
                        help="Case index to search (0-based). Use --all to search all cases.")
    parser.add_argument("--all", action="store_true",
                        help="Search all cases for the given stage")
    parser.add_argument("--max-half-depth", type=int, default=9,
                        help="Maximum half-depth for bidirectional BFS (default: 9, total depth = 2×)")
    parser.add_argument("--time-limit", type=float, default=None,
                        help="Time limit in seconds per case (default: no limit)")
    args = parser.parse_args()

    stage = STAGES[args.stage]
    cases = enumerate_cases(stage)
    n = len(cases)

    if args.all:
        indices = list(range(n))
    elif args.case_idx is not None:
        if not (0 <= args.case_idx < n):
            parser.error(f"--case must be in range 0..{n - 1}")
        indices = [args.case_idx]
    else:
        parser.error("Specify --case <idx> or --all")

    print(f"Stage: {args.stage.upper()}, {len(indices)} case(s), max half-depth={args.max_half_depth}")
    print()

    for idx in indices:
        ll_co, ll_cp, ll_ep = cases[idx]
        start = _make_ll_state(ll_co, ll_cp, ll_ep)
        print(f"{args.stage}_{idx:03d}:")
        t0 = time.time()
        result = bidir_bfs(start, stage, args.max_half_depth, args.time_limit)
        elapsed = time.time() - t0
        if result:
            print(f"  FOUND len={len(result)} ({elapsed:.1f}s): {' '.join(result)}")
            verified = stage.is_solved(apply_moves(start, result))
            print(f"  Verified: {verified}")
        else:
            print(f"  NOT FOUND at half-depth={args.max_half_depth} ({elapsed:.1f}s)")
        print()


if __name__ == "__main__":
    main()
