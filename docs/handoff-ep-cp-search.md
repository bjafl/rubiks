# Handoff: EP/CP Algorithm Search

**Date:** 2026-06-13  
**Branch:** main  
**Context:** After the U↔F face rename, all old EP/CP algorithm strings in
`scripts/gen_ep_cp_catalogs.py` became invalid. The goal is to find replacement
algorithms and regenerate `ll_catalog/ep.json` and `ll_catalog/cp.json`.

---

## Current Status

| Stage | Cases | Status |
|-------|-------|--------|
| EP    | 0, 1  | ✅ Found and verified |
| EP    | 2–10  | ❌ NOT FOUND — search pending |
| CP    | 0–9, 11 | ✅ Pre-existing, re-verified correct |
| CP    | 10    | ❌ NOT FOUND — old algorithm fails verification |

---

## How to Run the Search

Run **one case at a time** to avoid memory pressure. Each run is safe to kill and restart.

```bash
# EP cases — run each individually
python3 scripts/find_ep_cp_algs.py ep 2  --max-half 9 --no-patch
python3 scripts/find_ep_cp_algs.py ep 3  --max-half 9 --no-patch
python3 scripts/find_ep_cp_algs.py ep 4  --max-half 9 --no-patch
# ... through ep 10
python3 scripts/find_ep_cp_algs.py cp 10 --max-half 9 --no-patch
```

Drop `--no-patch` to have the script auto-patch `gen_ep_cp_catalogs.py` when an
algorithm is found. Or patch manually from the output line:

```
ep_003: R U F- ... [len=12, ok=True]
```

---

## Memory Profile (Safe Baseline)

The asymmetric BDBFS with `max_bwd_half=6` (hardcoded in `find_ep_algs()`)
keeps peak RAM at approximately:

- fwd dict at depth 8–9: ~5 GB (28.5M entries × 172 bytes/entry)
- bwd dict at depth 6: ~0.94 GB (3.37M entries × 60 goals)
- next_bwd frontier: ~1 GB (hash-only: int+tuple vs bytes(100))
- **Total peak: ~7 GB** — safe on a 16 GB machine

CP cases use `max_bwd_half=None` (symmetric) because CP has only 1 goal state,
so bwd grows at 8× (moves) not 60× (goals). No asymmetry needed.

---

## Time Estimates

| Case type | Expected length | Approx time |
|-----------|----------------|-------------|
| EP with 12-move solution | 12 moves | ~6 min |
| EP with 14-move solution | 14 moves | ~17 min |
| CP 10 (unknown) | 16–18 moves | ~14–30 min |

If a case times out at `--max-half 9`, try `--max-half 10` (much slower; ~7× longer).

---

## After Finding All Algorithms

1. Verify all are patched into `gen_ep_cp_catalogs.py` (no `NOT FOUND` entries remain)
2. Regenerate the catalogs:
   ```bash
   python3 scripts/gen_ep_cp_catalogs.py --verify-only  # sanity check first
   python3 scripts/gen_ep_cp_catalogs.py                 # writes ll_catalog/ep.json, ll_catalog/cp.json
   ```
3. Run the solver end-to-end to confirm LL solving works again:
   ```bash
   python3 -m pytest tests/ -x -q
   ```
4. Commit: `feat(megaminx): complete EP/CP catalogs after U↔F rename`

---

## Architecture Notes

**`scripts/find_ep_cp_algs.py`** — Main search script (committed on 2026-06-13)

- `bdbfs(start, goals, max_half, max_bwd_half)` — core bidirectional BFS
- Frontiers: `list[tuple[int, str]]` — `(int_hash, last_move)` pairs
- Visited dicts: `dict[int, tuple[int|None, str]]` — `hash → (parent_hash, move)`
- State reconstruction: `_reconstruct_fwd_state(h, fwd, start)` replays parent-chain;
  `_reconstruct_bwd_state(h, bwd, goal_by_hash)` replays inverse moves from goal
- `find_ep_algs()` passes `max_bwd_half=6` to cap bwd at 3.37M entries
- `find_cp_algs()` uses `max_bwd_half=None` (symmetric, 1 goal state)

**`scripts/gen_ep_cp_catalogs.py`** — Algorithm source-of-truth; run to regenerate JSON catalogs

**`ll_catalog/ep.json`, `ll_catalog/cp.json`** — Generated output (stale until search completes)
