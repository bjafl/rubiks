#!/usr/bin/env python3
"""
Generate EP and CP catalog JSON files from hardcoded verified algorithms.

These were found via bidirectional BFS (not pure DFS, which times out at depth 14+).
Run this script to regenerate ll_catalog/ep.json and ll_catalog/cp.json.

NOTE: After the U↔F face rename (2026-06-13), the LL moved from the physical front
face to the physical top face. The EP and CP algorithm strings (EP_ALGORITHMS,
CP_ALGORITHMS) below were originally tuned for the old LL and are no longer valid —
they now produce empty solution lists for all non-trivial cases. The CO catalog
(co.json) was regenerated correctly via CatalogBuilder and is unaffected.

To fix: run a bidirectional BFS over the new LL state space (LL_EDGE_SLOTS=(18,19,22,25,26),
LL_CORNER_SLOTS=(13,14,15,18,19)) to find replacement algorithms for EP_ALGORITHMS[0..10]
and CP_ALGORITHMS[0..10], then re-run this script.

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
    0:  "U- F- U- F R F- R- U R F R- U",
    1:  "R++ U-- F U- F- U F- R- F R U++ R--",
    2:  "",  # NOT FOUND
    3:  "",  # NOT FOUND
    4:  "",  # NOT FOUND
    5:  "",  # NOT FOUND
    6:  "",  # NOT FOUND
    7:  "",  # NOT FOUND
    8:  "",  # NOT FOUND
    9:  "",  # NOT FOUND
    10: "",  # NOT FOUND
    11:  "",  # identity — solved by AUF rotation alone
}

# ── CP algorithms (found via bidirectional BFS, max depth 18) ────────────────
# Each algorithm solves the corresponding canonical CP case while preserving CO AND EP.
CP_ALGORITHMS: dict[int, str] = {
    0:  "R U++ F- U-- R U++ R- F R U-- R--",
    1:  "R++ U++ R- F- R U-- R- U++ F U-- R-",
    2:  "F-- R-- F U-- R++ F-- R-- F U++ F- R++ F-- U-- F- U++ F",
    3:  "R- U R++ U F- U- F R-- F- U F U-- R",
    4:  "U R U R- F- R U- R- U F U--",
    5:  "R- U++ F- U- F R++ F- U F U- R-- U- R",
    6:  "F++ U- F++ R F-- U F++ U- R- U F",
    7:  "U++ F U F-- R F R- U- R F- R- F R- U++ R U",
    8:  "U++ F- U- R U R- F R U- R- U-",
    9:  "F- U- R U F- U- F R- F- U F++",
    10: "",  # NOT FOUND
    11:  "",  # identity — solved by AUF rotation alone
}

MOVE_SET = ["R", "R-", "F", "F-", "F++", "F--", "U", "U-", "U++", "U--"]


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

        # Verify — drop solutions that don't actually solve the case
        start = _make_ll_state(ll_co, ll_cp, ll_ep)
        result = apply_moves(start, moves) if moves else start
        if stage.is_solved(result):
            ok += 1
        else:
            if moves:
                print(f"  FAIL (solution dropped): {stage_name}_{idx:03d}")
            cases[-1] = Case(
                case_id=cases[-1].case_id,
                canonical_state=cases[-1].canonical_state,
                auf_variants=cases[-1].auf_variants,
                solutions=[],
            )

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
