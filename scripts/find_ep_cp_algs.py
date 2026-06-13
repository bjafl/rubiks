#!/usr/bin/env python3
"""
Find EP and CP algorithms via bidirectional BFS.

After the U↔F face rename (2026-06-13), the LL is around new "U" (physical top).
EP/CP algorithm strings in gen_ep_cp_catalogs.py are stale. This script finds
replacements using BDBFS and optionally patches the script in-place.

Usage:
    python3 scripts/find_ep_cp_algs.py              # find all, patch script
    python3 scripts/find_ep_cp_algs.py ep            # EP cases only
    python3 scripts/find_ep_cp_algs.py cp            # CP cases only
    python3 scripts/find_ep_cp_algs.py ep 3          # single case
    python3 scripts/find_ep_cp_algs.py --no-patch    # print only

Memory design (hash-chain reconstruction):
    fwd[h] = (parent_h, move)  — visited fwd states keyed by int hash of bytes(100)
    bwd[h] = (child_h, move)   — visited bwd states keyed by int hash of bytes(100)
    Frontiers store (int_hash, last_move) pairs only; MegaminxState is reconstructed
    on-demand by replaying parent-chain moves from the start/goal state.
    This keeps next_bwd frontier at ~1 GB (vs ~5 GB with bytes keys) when bwd has
    3.37M entries (depth 6 with 60 EP goals). The bwd expansion depth is capped via
    max_bwd_half (default 6 for EP) so bwd never exceeds ~1 GB in its visited dict;
    fwd expands to max_half (default 9) to cover the remaining distance.
"""
from __future__ import annotations
import sys
import gc
import time
import argparse
import itertools
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from megaminx.cube import SOLVED, apply_move, MegaminxState
from megaminx.ll_catalog import (
    LL_CORNER_SLOTS, LL_EDGE_SLOTS,
    EP_STAGE, CP_STAGE_CO_FIRST,
    enumerate_cases, _make_ll_state, _perm_parity,
)

# ─── Move set ────────────────────────────────────────────────────────────────

MOVE_SET = [sys.intern(m) for m in
            ["R", "R-", "R++", "R--", "F", "F-", "F++", "F--", "U", "U-", "U++", "U--"]]

INV: dict[str, str] = {
    sys.intern(k): sys.intern(v) for k, v in {
        "R": "R-", "R-": "R", "R++": "R--", "R--": "R++",
        "F": "F-", "F-": "F", "F++": "F--", "F--": "F++",
        "U": "U-", "U-": "U", "U++": "U--", "U--": "U++",
    }.items()
}


def _face(m: str) -> str:
    return m.rstrip("-+")


# ─── State → compact key ─────────────────────────────────────────────────────
#
# fwd/bwd dicts use Python's built-in hash() as integer key (~28 bytes/entry
# vs 133 bytes for bytes(100)), saving ~3GB at 27M entries. hash() uses
# SipHash in C — fast (~50ns/call). Collision probability ≈ N²/2^61 ≈ 3e-4
# for N=27M — low; verify() in the caller catches any false positive meeting.
# Frontiers store raw bytes for lossless state reconstruction.

def _bytes_key(s: MegaminxState) -> bytes:
    """100-byte frontier key: cp(20)+co(20)+ep(30)+eo(30)."""
    return bytes(s.cp) + bytes(s.co) + bytes(s.ep) + bytes(s.eo)


def _hash_bytes(b: bytes) -> int:
    return hash(b)


def _reconstruct_fwd_state(h: int, fwd: dict, start: MegaminxState) -> MegaminxState:
    """Replay moves from start to reach state with hash h."""
    moves: list[str] = []
    k = h
    while fwd[k][0] is not None:
        moves.append(fwd[k][1])
        k = fwd[k][0]
    moves.reverse()
    s = start
    for m in moves:
        s = apply_move(s, m)
    return s


def _reconstruct_bwd_state(h: int, bwd: dict, goal_by_hash: dict) -> MegaminxState:
    """Replay inverse moves from the root goal to reach state with hash h.

    bwd[ph] = (sh, m) means apply_move(ph_state, m) = sh_state.
    Chain from h to goal gives moves [m1, ..., md]; reconstruction applies
    INV[md], ..., INV[m1] starting from the goal state.
    """
    moves: list[str] = []
    k = h
    while bwd[k][0] is not None:
        moves.append(bwd[k][1])
        k = bwd[k][0]
    s = goal_by_hash[k]
    for m in reversed(moves):
        s = apply_move(s, INV[m])
    return s


# ─── EP goal states ───────────────────────────────────────────────────────────

def _ep_goals() -> list[MegaminxState]:
    """All EP-solved states: LL edges home, CO=0, even-parity CP, non-LL=identity."""
    ll_co = (0,) * 5
    ll_ep = LL_EDGE_SLOTS
    goals = []
    for cp in itertools.permutations(LL_CORNER_SLOTS):
        if _perm_parity(cp, LL_CORNER_SLOTS) != 0:
            continue
        s = _make_ll_state(ll_co, cp, ll_ep)
        if EP_STAGE.is_solved(s):
            goals.append(s)
    return goals


# ─── Bidirectional BFS ───────────────────────────────────────────────────────

def bdbfs(
    start: MegaminxState,
    goals: list[MegaminxState],
    max_half: int = 9,
    max_bwd_half: int | None = None,
    verbose: bool = True,
    label: str = "",
) -> list[str] | None:
    """
    Bidirectional BFS with int-hash keys and hash-only frontiers.

    fwd/bwd dicts: {int_hash → (parent_hash, move)} — compact integer keys (~28 B/entry)
    Frontiers: list of (int_hash, last_move) — states reconstructed via parent-chain
    replays (O(depth) apply_move calls, ~50% slower but avoids the 5-8 GB peak that
    bytes-in-frontier causes when bwd has 60 goal states reaching depth 7).

    max_bwd_half caps the backward expansion depth. When bwd is capped at depth K,
    fwd is allowed to expand beyond K, finding solutions of length up to fwd_depth + K.
    This prevents bwd (60 goals × ~8^7 states = 26.9M entries = 7.5 GB) from OOM
    while still finding any algorithm whose midpoint falls within the explored region.
    """
    start_bk = _bytes_key(start)
    start_h = _hash_bytes(start_bk)

    goal_hs = [_hash_bytes(_bytes_key(g)) for g in goals]
    goal_by_hash: dict[int, MegaminxState] = dict(zip(goal_hs, goals))

    fwd: dict[int, tuple] = {start_h: (None, None)}
    bwd: dict[int, tuple] = {h: (None, None) for h in goal_hs}

    if start_h in bwd:
        return []

    _max_bwd = max_bwd_half if max_bwd_half is not None else max_half

    # Frontiers: (int_hash, last_move_or_None) — no bytes stored
    fwd_front: list[tuple[int, str | None]] = [(start_h, None)]
    bwd_front: list[tuple[int, str | None]] = [(h, None) for h in goal_hs]

    for half_d in range(1, max_half + 1):
        t0 = time.time()

        # ── Expand forward ──
        next_fwd: list[tuple[int, str | None]] = []
        for sh, last in fwd_front:
            s = _reconstruct_fwd_state(sh, fwd, start)
            last_face = _face(last) if last else None
            last_inv = INV[last] if last else None
            for m in MOVE_SET:
                if _face(m) == last_face:
                    continue
                if m == last_inv:
                    continue
                ns = apply_move(s, m)
                nh = _hash_bytes(_bytes_key(ns))
                if nh not in fwd:
                    fwd[nh] = (sh, sys.intern(m))
                    next_fwd.append((nh, m))
                    if nh in bwd:
                        path = _reconstruct(fwd, bwd, nh)
                        if verbose:
                            print(f"  {label} found depth {len(path)}: {' '.join(path)}")
                        return path
        fwd_front = next_fwd
        if not fwd_front:
            break

        if verbose:
            print(f"  {label} half={half_d} fwd={len(fwd):,} bwd={len(bwd):,} "
                  f"({time.time()-t0:.1f}s)", flush=True)

        if half_d >= _max_bwd or not bwd_front:
            continue  # bwd capped — keep expanding fwd only

        # ── Expand backward ──
        next_bwd: list[tuple[int, str | None]] = []
        for sh, last in bwd_front:
            s = _reconstruct_bwd_state(sh, bwd, goal_by_hash)
            last_face = _face(last) if last else None
            for m in MOVE_SET:
                if _face(m) == last_face:
                    continue
                ps = apply_move(s, INV[m])
                ph = _hash_bytes(_bytes_key(ps))
                if ph not in bwd:
                    bwd[ph] = (sh, sys.intern(m))  # from ph, apply m → sh
                    next_bwd.append((ph, INV[m]))
                    if ph in fwd:
                        path = _reconstruct(fwd, bwd, ph)
                        if verbose:
                            print(f"  {label} found depth {len(path)}: {' '.join(path)}")
                        return path
        bwd_front = next_bwd

    return None


def _reconstruct(
    fwd: dict[int, tuple],
    bwd: dict[int, tuple],
    meeting: int,
) -> list[str]:
    fwd_moves: list[str] = []
    k = meeting
    while fwd[k][0] is not None:
        fwd_moves.append(fwd[k][1])
        k = fwd[k][0]
    fwd_moves.reverse()

    bwd_moves: list[str] = []
    k = meeting
    while bwd[k][0] is not None:
        bwd_moves.append(bwd[k][1])
        k = bwd[k][0]

    return fwd_moves + bwd_moves


# ─── Algorithm finder ────────────────────────────────────────────────────────

def verify(moves: list[str], start: MegaminxState, stage) -> bool:
    s = start
    for m in moves:
        s = apply_move(s, m)
    return stage.is_solved(s)


def find_ep_algs(case_indices: list[int], max_half: int, verbose: bool) -> dict[int, str]:
    ep_goals = _ep_goals()
    print(f"EP goals: {len(ep_goals)} states (EP solved, CO=0, any even-parity CP)")
    cases = enumerate_cases(EP_STAGE)
    results: dict[int, str] = {}

    for idx in case_indices:
        if idx >= len(cases):
            print(f"  EP case {idx}: out of range (max {len(cases)-1})")
            continue
        ll_co, ll_cp, ll_ep = cases[idx]
        start = _make_ll_state(ll_co, ll_cp, ll_ep)

        if EP_STAGE.is_solved(start):
            print(f"  EP case {idx}: already solved (identity case)")
            results[idx] = ""
            continue

        print(f"EP case {idx}: ep={ll_ep}", flush=True)
        t = time.time()
        # Cap bwd at depth 6 (60 goals → 3.37M bwd entries = 0.94 GB safe limit).
        # Any ≤14-move solution has a midpoint at (fwd=8, bwd=6) on its path.
        path = bdbfs(start, ep_goals, max_half=max_half, max_bwd_half=6,
                     verbose=verbose, label=f"ep_{idx:03d}")

        if path is None:
            print(f"  ep_{idx:03d}: NOT FOUND within depth {2*max_half}")
        else:
            alg = " ".join(path)
            ok = verify(path, start, EP_STAGE)
            print(f"  ep_{idx:03d}: {alg}  [len={len(path)}, ok={ok}, {time.time()-t:.1f}s]")
            if ok:
                results[idx] = alg
        gc.collect()  # free BFS dicts before next case

    return results


def find_cp_algs(case_indices: list[int], max_half: int, verbose: bool) -> dict[int, str]:
    cases = enumerate_cases(CP_STAGE_CO_FIRST)
    results: dict[int, str] = {}

    for idx in case_indices:
        if idx >= len(cases):
            print(f"  CP case {idx}: out of range (max {len(cases)-1})")
            continue
        ll_co, ll_cp, ll_ep = cases[idx]
        start = _make_ll_state(ll_co, ll_cp, ll_ep)

        if CP_STAGE_CO_FIRST.is_solved(start):
            print(f"  CP case {idx}: already solved (identity case)")
            results[idx] = ""
            continue

        print(f"CP case {idx}: cp={ll_cp}", flush=True)
        t = time.time()
        path = bdbfs(start, [SOLVED], max_half=max_half, verbose=verbose, label=f"cp_{idx:03d}")

        if path is None:
            print(f"  cp_{idx:03d}: NOT FOUND within depth {2*max_half}")
        else:
            alg = " ".join(path)
            ok = verify(path, start, CP_STAGE_CO_FIRST)
            print(f"  cp_{idx:03d}: {alg}  [len={len(path)}, ok={ok}, {time.time()-t:.1f}s]")
            if ok:
                results[idx] = alg
        gc.collect()

    return results


# ─── Patch gen_ep_cp_catalogs.py ─────────────────────────────────────────────

_EP_PATTERN = re.compile(
    r"(EP_ALGORITHMS: dict\[int, str\] = \{)(.*?)(\})",
    re.DOTALL,
)
_CP_PATTERN = re.compile(
    r"(CP_ALGORITHMS: dict\[int, str\] = \{)(.*?)(\})",
    re.DOTALL,
)

_GEN_SCRIPT = Path(__file__).parent / "gen_ep_cp_catalogs.py"


def _dict_repr(algs: dict[int, str], old_text: str) -> str:
    """Rebuild the dict body, preserving comments and inserting found algorithms."""
    lines = []
    for i in range(12):
        alg = algs.get(i)
        if alg is None:
            for line in old_text.splitlines():
                if line.strip().startswith(f"{i}:"):
                    lines.append(line)
                    break
            else:
                lines.append(f'    {i}:  "",  # NOT FOUND')
        elif alg == "":
            lines.append(f'    {i}:  "",  # identity — solved by AUF rotation alone')
        else:
            lines.append(f'    {i}:  "{alg}",')
    return "\n".join(lines)


def patch_script(ep_results: dict[int, str], cp_results: dict[int, str]) -> None:
    src = _GEN_SCRIPT.read_text()

    m = _EP_PATTERN.search(src)
    if m:
        new_body = _dict_repr(ep_results, m.group(2))
        src = src[: m.start(2)] + "\n" + new_body + "\n" + src[m.end(2):]
    else:
        print("WARNING: could not locate EP_ALGORITHMS in script")

    m2 = _CP_PATTERN.search(src)
    if m2:
        new_body = _dict_repr(cp_results, m2.group(2))
        src = src[: m2.start(2)] + "\n" + new_body + "\n" + src[m2.end(2):]
    else:
        print("WARNING: could not locate CP_ALGORITHMS in script")

    _GEN_SCRIPT.write_text(src)
    print(f"Patched {_GEN_SCRIPT}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", nargs="?", choices=["ep", "cp"], default=None,
                        help="Which stage to search (default: both)")
    parser.add_argument("case", nargs="?", type=int, default=None,
                        help="Single case index to search")
    parser.add_argument("--max-half", type=int, default=9,
                        help="Max BFS depth from each side (default 9 = 18 moves total)")
    parser.add_argument("--no-patch", action="store_true",
                        help="Print results only, do not modify gen_ep_cp_catalogs.py")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress per-level BFS progress")
    args = parser.parse_args()

    verbose = not args.quiet
    do_ep = args.stage in (None, "ep")
    do_cp = args.stage in (None, "cp")
    case_indices = list(range(12)) if args.case is None else [args.case]

    ep_results: dict[int, str] = {}
    cp_results: dict[int, str] = {}

    if do_ep:
        print(f"\n=== EP stage (cases {case_indices}) ===")
        ep_results = find_ep_algs(case_indices, args.max_half, verbose)
        print(f"EP found: {len(ep_results)}/12")

    if do_cp:
        print(f"\n=== CP stage (cases {case_indices}) ===")
        cp_results = find_cp_algs(case_indices, args.max_half, verbose)
        print(f"CP found: {len(cp_results)}/12")

    if not args.no_patch and (ep_results or cp_results):
        print("\n--- Patching gen_ep_cp_catalogs.py ---")
        patch_script(ep_results, cp_results)
        print("Re-run: python3 scripts/gen_ep_cp_catalogs.py")


if __name__ == "__main__":
    main()
