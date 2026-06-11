#!/usr/bin/env python3
"""
Generate EP and CP catalog JSON files from hardcoded verified algorithms.

These were found via bidirectional BFS (not pure DFS, which times out at depth 14+).
Run this script to regenerate ll_catalog/ep.json and ll_catalog/cp.json.

Usage:
    python3 scripts/gen_ep_cp_catalogs.py [--output-dir ll_catalog]
"""
from __future__ import annotations
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from megaminx.cube import SOLVED, apply_move
from megaminx.ll_catalog import (
    LL_CORNER_SLOTS, LL_EDGE_SLOTS, _make_ll_state, _apply_auf,
    enumerate_cases, EP_STAGE, CP_STAGE_CO_FIRST,
    Solution, Case, StageCatalog,
)

# ── EP algorithms (found via bidirectional BFS, max depth 17) ────────────────
# Each algorithm solves the corresponding canonical EP case while preserving CO.
# CP may change freely (handled by subsequent CP stage).
EP_ALGORITHMS: dict[int, str] = {
    0:  "R- U- F- U F R U- F R U R- U- F- U",       # 14t 3cyc
    1:  "U- F U F- R- U- R U F U- F- R- U R",        # 14t 3cyc
    2:  "R- U++ R U++ R- U R U-- R- U- R U-- R- U-- R U-- U",  # 17t 2x2
    3:  "U-- R- U- R U- R- U++ R U-- R- U++ R U++ R- U R",     # 16t 3cyc
    4:  "U-- R- U++ R U++ R- U R U-- R- U- R U- R- U++ R",     # 16t 3cyc
    5:  "R- U- R U-- R- U-- R U++ R- U-- R U R- U R U++",      # 16t 3cyc
    6:  "F- U- F R F- U++ F U++ F- U F R- U-- F- U-- F U",     # 17t 3cyc
    7:  "U- R- U- R U-- R- U-- R U-- U- R U R- U R U-- R- U- U",  # 19t 2x2
    8:  "R- U-- R U R- U R U++ R- U- R U-- R- U-- R U++",      # 16t 3cyc
    9:  "R- U++ F- U F R- U-- F- U F U R F- U-- F R U-",       # 17t 3cyc
    10: "U- U- R U R- U R U-- R- U- R- U++ R U++ R- U R",      # 17t 2x2
    11: "",  # 5-cycle — solved by AUF rotation alone (0 algorithm moves)
}

# ── CP algorithms (found via bidirectional BFS, max depth 18) ────────────────
# Each algorithm solves the corresponding canonical CP case while preserving CO AND EP.
CP_ALGORITHMS: dict[int, str] = {
    0:  "U U- R U-- R- U- R U-- R- U++ R- U- R U-- R- U-- R U",   # 18t 3cyc
    1:  "U- R- U++ R U++ R- U R U-- R U++ R- U R U++ R- U U-",    # 18t 3cyc
    2:  "U-- R U-- F- U- F U- F- U- R- U R U++ F U- R-",          # 16t 2x2
    3:  "F R U++ R- F U F- R F R- U- R F- U-- R- F-",             # 16t 3cyc
    4:  "R U++ R- F U F- R F R- U- R F- U-- R-",                  # 14t 3cyc
    5:  "F R U++ F R- U R F- R- F U- F- R U-- R- F-",             # 16t 3cyc
    6:  "U- R U-- R- U-- R U- R- U++ U R- U++ R U R- U++ R U--",  # 18t 3cyc
    7:  "R- U- F- U F U- F- U F U- F- U F R",                     # 14t 2x2
    8:  "R U++ F R- U R F- R- F U- F- R U-- R-",                  # 14t 3cyc
    9:  "U++ R- U-- R U- R- U-- R U- U-- R U R- U++ R U++ R- U",  # 18t 3cyc
    10: "F U-- F- U- F U F- U-- R- F U- F- U-- R U R- U++ R",     # 18t 2x2
    11: "",  # 5-cycle — solved by AUF rotation alone (0 algorithm moves)
}

MOVE_SET = ["R", "R-", "F", "F-", "U", "U-", "U++", "U--"]


def apply_moves(state, moves):
    for m in moves:
        state = apply_move(state, m)
    return state


def build_catalog(stage, alg_dict: dict[int, str], stage_name: str) -> StageCatalog:
    cases_list = enumerate_cases(stage)
    cases: list[Case] = []
    ok = 0

    for idx, (ll_co, ll_cp, ll_ep) in enumerate(cases_list):
        alg_str = alg_dict[idx]
        moves = alg_str.split() if alg_str else []
        solutions = [Solution(moves=moves, length=len(moves))] if moves else []

        auf_variants = []
        for k in range(5):
            auf_co, auf_cp, auf_ep = _apply_auf(ll_co, ll_cp, ll_ep, k)
            d: dict = {}
            if stage.solve_ep:
                d["ep"] = list(auf_ep)
            if stage.solve_cp:
                d["cp"] = list(auf_cp)
            auf_variants.append(d)

        canonical_state: dict = {}
        if stage.solve_ep:
            canonical_state["ep"] = list(ll_ep)
        if stage.solve_cp:
            canonical_state["cp"] = list(ll_cp)

        cases.append(Case(
            case_id=f"{stage_name}_{idx:03d}",
            canonical_state=canonical_state,
            auf_variants=auf_variants,
            solutions=solutions,
        ))

        # Verify
        start = _make_ll_state(ll_co, ll_cp, ll_ep)
        result = apply_moves(start, moves) if moves else start
        if stage.is_solved(result):
            ok += 1
        else:
            print(f"  FAIL: {stage_name}_{idx:03d}")

    print(f"  {stage_name.upper()}: {ok}/{len(cases_list)} verified")
    return StageCatalog(
        stage=stage_name,
        move_set=MOVE_SET,
        max_depth=20,
        cases=cases,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate EP and CP catalog JSON files")
    parser.add_argument("--output-dir", default="ll_catalog",
                        help="Output directory (default: ll_catalog/)")
    parser.add_argument("--verify-only", action="store_true",
                        help="Verify algorithms without saving files")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)

    print("Building EP catalog...")
    ep_cat = build_catalog(EP_STAGE, EP_ALGORITHMS, "ep")

    print("Building CP catalog...")
    cp_cat = build_catalog(CP_STAGE_CO_FIRST, CP_ALGORITHMS, "cp")

    if not args.verify_only:
        output_dir.mkdir(parents=True, exist_ok=True)
        ep_cat.save(output_dir / "ep.json")
        cp_cat.save(output_dir / "cp.json")
        print(f"\nSaved to {output_dir}/ep.json and {output_dir}/cp.json")


if __name__ == "__main__":
    main()
