# Face Rename + Color Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename 5 lower-band face names (DFR→dR, DFL→dL, DB→B, DBR→dBR, DBL→dBL) and fix 4 swapped face colors (U↔F, BR↔dR, BL↔dL, D↔B) so the viewer GUI matches physical megaminx color convention.

**Architecture:** `megaminx/cube.py:NEIGHBORS` is the sole source of face names — CORNERS, EDGES, and all move tables derive from it at import time. Renaming the 5 NEIGHBORS keys (and their occurrences in neighbor lists) propagates automatically throughout the model. Colors live in `mcp_server/gen_geometry.py:FACE_COLORS`; `viewer/geometry.json` is regenerated output. Tests, docs, and one JS comment need manual updates.

**Tech Stack:** Python 3.x, pytest, JSON (`viewer/geometry.json` from `python -m mcp_server.gen_geometry`)

---

## Rename map

| Old | New |
|-----|-----|
| DFR | dR |
| DFL | dL |
| DB  | B  |
| DBR | dBR |
| DBL | dBL |

## Color fix (4 exact swaps)

| Face | Old color | New color |
|------|-----------|-----------|
| U    | `#FFFFFF` (white) | `#3498DB` (blue) |
| F    | `#3498DB` (blue)  | `#FFFFFF` (white) |
| BR   | `#1ABC9C` (turquoise) | `#9B59B6` (purple) |
| BL   | `#2ECC71` (green) | `#E91E8C` (pink) |
| dR   | `#9B59B6` (purple) | `#1ABC9C` (turquoise) |
| dL   | `#E91E8C` (pink) | `#2ECC71` (green) |
| D    | `#2C3E50` (dark navy) | `#D35400` (burnt orange) |
| B    | `#D35400` (burnt orange) | `#2C3E50` (dark navy/sort) |

## Files affected

| File | Change |
|------|--------|
| `megaminx/cube.py` | Rename 5 NEIGHBORS keys + all occurrences in neighbor lists |
| `mcp_server/gen_geometry.py` | Rename FACE_COLORS keys + fix 4 color swaps |
| `megaminx/moves.py` | Update 3 comment lines |
| `tests/test_face_names.py` | Update 3 test functions |
| `tests/test_gen_geometry.py` | Update 1 assertion |
| `tests/test_solver.py` | Update 1 move sequence |
| `tests/test_session.py` | Update 1 move sequence |
| `viewer/js/animator.js` | Update 1 JSDoc comment |
| `docs/megaminx-notasjon.md` | Update face table + opposite-pairs table + move example |
| `docs/megaminx-indekser.md` | Update all face name references in both table columns |
| `README.md` | Update face list + code examples (also fix pre-existing stale FR/FL names) |
| `viewer/geometry.json` | Regenerate (run `python -m mcp_server.gen_geometry`) |

---

### Task 1: Rename NEIGHBORS in cube.py

**Files:**
- Modify: `megaminx/cube.py:17-30`

- [ ] **Step 1: Confirm baseline tests pass**

```bash
cd /home/bjafl/source/rubiks && python -m pytest tests/ -q --tb=no 2>&1 | tail -3
```
Expected: `2 failed, 256 passed` (pre-existing viewer_server failures).

- [ ] **Step 2: Update NEIGHBORS dict**

Replace the entire NEIGHBORS block in `megaminx/cube.py`:

```python
NEIGHBORS: dict[str, list[str]] = {
    "U":   ["F", "L", "BL", "BR", "R"],
    "F":   ["U", "R", "dR", "dL", "L"],
    "R":   ["U", "BR", "dBR", "dR", "F"],
    "BR":  ["U", "BL", "B", "dBR", "R"],
    "BL":  ["U", "L", "dBL", "B", "BR"],
    "L":   ["U", "F", "dL", "dBL", "BL"],
    "D":   ["dL", "dR", "dBR", "B", "dBL"],
    "dR":  ["dL", "F", "R", "dBR", "D"],
    "dBR": ["dR", "R", "BR", "B", "D"],
    "B":   ["dBR", "BR", "BL", "dBL", "D"],
    "dBL": ["B", "BL", "L", "dL", "D"],
    "dL":  ["dBL", "L", "F", "dR", "D"],
}
```

- [ ] **Step 3: Run tests and note failures**

```bash
cd /home/bjafl/source/rubiks && python -m pytest tests/ -q --tb=line 2>&1 | tail -20
```
Expected: failures in `test_face_names.py`, `test_gen_geometry.py`, `test_solver.py`, `test_session.py`.

---

### Task 2: Fix tests

**Files:**
- Modify: `tests/test_face_names.py:18,54,60-61`
- Modify: `tests/test_gen_geometry.py:52`
- Modify: `tests/test_solver.py:34`
- Modify: `tests/test_session.py:29`

- [ ] **Step 1: Update test_face_names.py — three functions**

`test_all_12_wca_names_present` (line 18):
```python
def test_all_12_wca_names_present():
    expected = {"U", "D", "F", "R", "BR", "BL", "L", "dR", "dBR", "B", "dBL", "dL"}
    assert set(FACE_NAMES) == expected
```

`test_lower_faces_have_negative_y` (line 54):
```python
def test_lower_faces_have_negative_y():
    for name in ["dR", "dBR", "B", "dBL", "dL"]:
        assert c(name)[1] <= 0, f"{name} should have non-positive Y (below or at equator)"
```

`test_opposite_pairs_sum_to_zero` (lines 60-61):
```python
    pairs = [("U", "D"), ("F", "B"), ("R", "dBL"), ("L", "dBR"),
             ("BR", "dL"), ("BL", "dR")]
```

- [ ] **Step 2: Update test_gen_geometry.py line 52**

```python
    assert g["faceNames"][-1] == "dL"
```

- [ ] **Step 3: Update test_solver.py line 34**

```python
    scrambled = apply_sequence(SOLVED_STATE, ["U", "F", "R", "L", "dBL"])
```

- [ ] **Step 4: Update test_session.py line 29**

```python
    for move in ["U", "F", "R", "dR", "D"]:
```

- [ ] **Step 5: Run tests — all should pass (minus pre-existing 2)**

```bash
cd /home/bjafl/source/rubiks && python -m pytest tests/ -q --tb=short 2>&1 | tail -5
```
Expected: `2 failed, 256 passed` (same pre-existing failures, no new failures).

---

### Task 3: Fix colors in gen_geometry.py + regenerate geometry.json

**Files:**
- Modify: `mcp_server/gen_geometry.py:7-20`
- Regenerate: `viewer/geometry.json`

- [ ] **Step 1: Replace FACE_COLORS in gen_geometry.py**

```python
FACE_COLORS: dict[str, str] = {
    "U":   "#3498DB",
    "F":   "#FFFFFF",
    "R":   "#E74C3C",
    "L":   "#F39C12",
    "BL":  "#E91E8C",
    "BR":  "#9B59B6",
    "D":   "#D35400",
    "dR":  "#1ABC9C",
    "dBR": "#F1C40F",
    "B":   "#2C3E50",
    "dBL": "#95A5A6",
    "dL":  "#2ECC71",
}
```

- [ ] **Step 2: Regenerate geometry.json**

```bash
cd /home/bjafl/source/rubiks && python -m mcp_server.gen_geometry
```
Expected output: `Written: .../viewer/geometry.json  (N KB)`

- [ ] **Step 3: Verify geometry.json has new names and colors**

```bash
python3 -c "
import json
g = json.load(open('viewer/geometry.json'))
print('faceNames:', g['faceNames'])
print('U color:', g['faceColors']['U'])
print('F color:', g['faceColors']['F'])
print('BR color:', g['faceColors']['BR'])
print('dR color:', g['faceColors']['dR'])
print('D color:', g['faceColors']['D'])
print('B color:', g['faceColors']['B'])
"
```
Expected:
```
faceNames: ['U', 'F', 'R', 'BR', 'BL', 'L', 'D', 'dR', 'dBR', 'B', 'dBL', 'dL']
U color: #3498DB
F color: #FFFFFF
BR color: #9B59B6
dR color: #1ABC9C
D color: #D35400
B color: #2C3E50
```

- [ ] **Step 4: Run full test suite**

```bash
cd /home/bjafl/source/rubiks && python -m pytest tests/ -q --tb=short 2>&1 | tail -5
```
Expected: `2 failed, 256 passed`.

---

### Task 4: Update comments (moves.py and animator.js)

**Files:**
- Modify: `megaminx/moves.py:161-169` (comment lines)
- Modify: `viewer/js/animator.js:40` (JSDoc comment)

- [ ] **Step 1: Update moves.py comment block**

Find and replace the three comment lines around line 161:

Old:
```python
    # D-ring: 5 faces adjacent to D, sorted CW from DFL
    # DFL is adjacent to both F and L
    # NEIGHBORS["D"] = DFL, DFR, DBR, DB, DBL in CW order from outside D
```

New:
```python
    # D-ring: 5 faces adjacent to D, sorted CW from dL
    # dL is adjacent to both F and L
    # NEIGHBORS["D"] = dL, dR, dBR, B, dBL in CW order from outside D
```

- [ ] **Step 2: Update animator.js JSDoc comment (line 40)**

Old:
```javascript
   * @param {string}   moveName   — e.g. "R", "U-", "BR++", "DFR2'"
```

New:
```javascript
   * @param {string}   moveName   — e.g. "R", "U-", "BR++", "dR2'"
```

---

### Task 5: Update docs

**Files:**
- Modify: `docs/megaminx-notasjon.md`
- Modify: `docs/megaminx-indekser.md`
- Modify: `README.md`

- [ ] **Step 1: Update megaminx-notasjon.md — face table (lines 17-31)**

Replace the two-column Fasadenavn table with a single-column table (model now matches community):

```markdown
## Fasadenavn

| Navn | Plassering (referansestilling) |
|---|---|
| U | Topp |
| F | Mot deg, øvre band |
| R | Høyre for F, øvre band |
| L | Venstre for F, øvre band |
| BR | Bak til høyre, øvre band |
| BL | Bak til venstre, øvre band |
| dR | Nede til høyre foran, nedre band (berører F og R) |
| dL | Nede til venstre foran, nedre band (berører F og L) |
| B | Rett bak, nedre band |
| dBR | Bak til høyre, nedre band |
| dBL | Bak til venstre, nedre band |
| D | Bunn |

Merk at dR/dL ikke ligger på samme høyde som F — de sitter *nede* foran og deler F sin nedre høyre/venstre kant. Det er forskyvningen mellom bandene som gjør at nedre band trenger egne navn i stedet for et «midtnivå».
```

- [ ] **Step 2: Update megaminx-notasjon.md — motstående fasader table (lines 38-46)**

```markdown
### Motstående fasader

| Fasade | Motstående |
|---|---|
| U | D |
| F | B |
| R | dBL |
| L | dBR |
| BR | dL |
| BL | dR |
```

- [ ] **Step 3: Update megaminx-notasjon.md — move example (lines 67-69)**

Old:
```
Kanter:  F/R → R/U → BR/R → DBR/R → DR/R → (tilbake til F/R)
Hjørner: DR/F/R → F/U/R → BR/R/U → BR/DBR/R → DBR/DR/R → ...
```

New:
```
Kanter:  F/R → R/U → BR/R → dBR/R → dR/R → (tilbake til F/R)
Hjørner: dR/F/R → F/U/R → BR/R/U → BR/dBR/R → dBR/dR/R → ...
```

- [ ] **Step 4: Update megaminx-indekser.md — intro line (line 11)**

Old:
```
Community-navn i parentes der de avviker: DFR = DR, DFL = DL, DB = B.
```

New:
```
Modell- og community-navn er nå identiske (navnene ble synkronisert 2026-06-11).
```

- [ ] **Step 5: Update megaminx-indekser.md — all old face names in tables**

Perform these string replacements in order (longer names first to avoid partial matches):

1. `DBR` → `dBR`
2. `DBL` → `dBL`
3. `DFR` → `dR`
4. `DFL` → `dL`
5. `DB` → `B` (standalone — only where it is a complete face name token)

Note: In the table, face names appear within `/`-separated strings like `BL/DB/BR`. Replace `DB` with `B` only where it is bounded by `/`, `|`, or space — not inside `DBR`/`DBL` (already handled above).

Verify the result:
```bash
grep -n "DFR\|DFL\|\bDB\b\|DBR\|DBL" docs/megaminx-indekser.md
```
Expected: no output.

- [ ] **Step 6: Update README.md — face list (line 113)**

Old:
```
Faces: `U  F  FR  BR  BL  FL  DFR  DR  DBR  DBL  DFL  D`
```

New:
```
Faces: `U  F  R  BR  BL  L  dR  dBR  B  dBL  dL  D`
```

- [ ] **Step 7: Update README.md — code examples (lines 8, 58-60, 69, 81)**

Line 8:
```
- **WCA move notation** — all 24 atomic moves (`U`, `F`, `R-`, `U++`, etc.)
```

Lines 58-60:
```python
near = aseq(SOLVED_STATE.copy(), ["U", "F", "R-"])
solution = solve_path(near, SOLVED_STATE.copy(), max_depth=6)
print(solution)   # ['R', 'F-', 'U-']
```

Line 69:
```python
sune = get_single_alg("SUNE")            # ["R", "U", "R-", "U", "R", "U++", "R-"]
```

Lines 81-82:
```python
    move_set=["U", "U-", "R", "R-"],  # restrict search to these moves
```

---

### Task 6: Commit lower-band rename

- [ ] **Step 1: Run full test suite one final time**

```bash
cd /home/bjafl/source/rubiks && python -m pytest tests/ -q --tb=short 2>&1 | tail -5
```
Expected: `2 failed, 256 passed` (same pre-existing failures only).

- [ ] **Step 2: Stage and commit**

```bash
cd /home/bjafl/source/rubiks
git add megaminx/cube.py mcp_server/gen_geometry.py megaminx/moves.py \
        tests/test_face_names.py tests/test_gen_geometry.py \
        tests/test_solver.py tests/test_session.py \
        viewer/js/animator.js viewer/geometry.json \
        docs/megaminx-notasjon.md docs/megaminx-indekser.md README.md
git commit -m "$(cat <<'EOF'
refactor: rename lower-band faces to community convention + fix viewer colors

DFR→dR, DFL→dL, DB→B, DBR→dBR, DBL→dBL throughout codebase.
Fix 4 swapped faceColors (U↔F, BR↔dR, BL↔dL, D↔B) in gen_geometry.py
and regenerate geometry.json.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 3: Verify commit**

```bash
git log --oneline -3
git diff HEAD~1 --stat
```

---

## Part II: U↔F name swap

**Why:** In the 3D viewer the camera sits at (0, 5, +3). The face currently named "U" has its center at z=+0.724 — it faces the camera and appears as the *front* face. The face currently named "F" sits at z=−0.724 — it appears at the *top* of the viewport. This is inverted from WCA convention (U=top, F=front). No camera-only fix preserves both U/F and R/L orientation simultaneously. The correct fix is to swap the abstract names U↔F throughout the model and update every hardcoded algorithm string.

**Scope:**
| File | Change |
|------|--------|
| `megaminx/cube.py` | Swap U↔F in NEIGHBORS keys and all neighbor lists |
| `megaminx/moves.py` | Swap u_geo/f_geo assignment in `_match_geo_to_cube()` |
| `megaminx/ll_catalog.py` | Recompute LL_CORNER_SLOTS and LL_EDGE_SLOTS (now around new U = old F face) |
| `megaminx/algorithms.py` | Swap U↔F in all move sequences in ALGORITHM_SETS and SINGLE_ALGS |
| `scripts/gen_ep_cp_catalogs.py` | Swap U↔F in EP_ALGORITHMS and CP_ALGORITHMS (24 entries) |
| `scripts/analyze_co_pairs.py` | Swap U↔F in CO_ALGS (16 entries) |
| `scripts/analyze_pll_primitives.py` | Swap U↔F in CO_ALGS including Fc1/Fc2 (18 entries) |
| `ll_catalog/ep.json`, `ll_catalog/cp.json` | Regenerate after algorithm changes |

**Swap rule:** In every move token, replace simultaneously:
`U→F`, `U-→F-`, `U++→F++`, `U--→F--`, `F→U`, `F-→U-`, `F++→U++`, `F--→U--`.
Never replace sequentially (U→F then F→U = no-op).

---

### Task 7: Swap U↔F in NEIGHBORS + fix geometry in moves.py + recompute LL slots

**Files:**
- Modify: `megaminx/cube.py` (NEIGHBORS dict)
- Modify: `megaminx/moves.py:150-172` (`_match_geo_to_cube`)
- Modify: `megaminx/ll_catalog.py:17-18` (LL_CORNER_SLOTS, LL_EDGE_SLOTS)

- [ ] **Step 1: Replace NEIGHBORS in cube.py**

Replace the NEIGHBORS dict (result of Task 1's lower-band rename) with the U↔F-swapped version.
Both keys and all occurrences in neighbor lists are swapped simultaneously:

```python
NEIGHBORS: dict[str, list[str]] = {
    "U":   ["F", "R", "dR", "dL", "L"],
    "F":   ["U", "L", "BL", "BR", "R"],
    "R":   ["F", "BR", "dBR", "dR", "U"],
    "BR":  ["F", "BL", "B", "dBR", "R"],
    "BL":  ["F", "L", "dBL", "B", "BR"],
    "L":   ["F", "U", "dL", "dBL", "BL"],
    "D":   ["dL", "dR", "dBR", "B", "dBL"],
    "dR":  ["dL", "U", "R", "dBR", "D"],
    "dBR": ["dR", "R", "BR", "B", "D"],
    "B":   ["dBR", "BR", "BL", "dBL", "D"],
    "dBL": ["B", "BL", "L", "dL", "D"],
    "dL":  ["dBL", "L", "U", "dR", "D"],
}
```

- [ ] **Step 2: Update `_match_geo_to_cube` in moves.py**

The function currently computes `u_geo = argmax(Y)` (the highest-Y face, now called F) and derives `f_geo` from it. After the rename the roles swap: F = argmax(Y), U = F's min-Z neighbor.

Replace lines 150–172 of `megaminx/moves.py`:

Old:
```python
    # U = face with highest y; D = antipodal face (center ≈ -U_center)
    u_geo = int(np.argmax(_geo_centers_raw[:, 1]))
    d_geo = int(np.argmin(np.linalg.norm(_geo_centers_raw + _geo_centers_raw[u_geo], axis=1)))

    # U-ring: 5 faces adjacent to U, sorted CW from F
    u_adj = [j for j in range(12) if _geo_adj(u_geo, j)]
    f_geo = min(u_adj, key=lambda j: float(_geo_centers_raw[j][2]))
    u_ring_cw = _cw_ring_order(u_geo, f_geo, u_adj)
    # NEIGHBORS["U"] = F, L, BL, BR, R in CW order from outside U
    u_name_to_geo: dict[str, int] = {_NB["U"][i]: u_ring_cw[i] for i in range(5)}

    # D-ring: 5 faces adjacent to D, sorted CW from DFL
    d_adj = [j for j in range(12) if _geo_adj(d_geo, j)]
    # DFL is adjacent to both F and L
    dfl_geo = next(
        j for j in d_adj
        if _geo_adj(j, u_name_to_geo["F"]) and _geo_adj(j, u_name_to_geo["L"])
    )
    d_ring_cw = _cw_ring_order(d_geo, dfl_geo, d_adj)
    # NEIGHBORS["D"] = DFL, DFR, DBR, DB, DBL in CW order from outside D
    d_name_to_geo: dict[str, int] = {_NB["D"][i]: d_ring_cw[i] for i in range(5)}

    name_to_geo: dict[str, int] = {"U": u_geo, "D": d_geo, **u_name_to_geo, **d_name_to_geo}
```

New:
```python
    # F = face with highest y (faces camera at z=+3); U = F's min-Z neighbor (top of viewport)
    f_geo = int(np.argmax(_geo_centers_raw[:, 1]))
    d_geo = int(np.argmin(np.linalg.norm(_geo_centers_raw + _geo_centers_raw[f_geo], axis=1)))

    # F-ring: 5 faces adjacent to F, sorted CW from U
    f_adj = [j for j in range(12) if _geo_adj(f_geo, j)]
    u_geo = min(f_adj, key=lambda j: float(_geo_centers_raw[j][2]))
    f_ring_cw = _cw_ring_order(f_geo, u_geo, f_adj)
    # NEIGHBORS["F"] = U, L, BL, BR, R in CW order from outside F
    f_name_to_geo: dict[str, int] = {_NB["F"][i]: f_ring_cw[i] for i in range(5)}

    # D-ring: 5 faces adjacent to D, sorted CW from dL
    d_adj = [j for j in range(12) if _geo_adj(d_geo, j)]
    # dL is adjacent to both U and L
    dl_geo = next(
        j for j in d_adj
        if _geo_adj(j, f_name_to_geo["U"]) and _geo_adj(j, f_name_to_geo["L"])
    )
    d_ring_cw = _cw_ring_order(d_geo, dl_geo, d_adj)
    # NEIGHBORS["D"] = dL, dR, dBR, B, dBL in CW order from outside D
    d_name_to_geo: dict[str, int] = {_NB["D"][i]: d_ring_cw[i] for i in range(5)}

    name_to_geo: dict[str, int] = {"F": f_geo, "D": d_geo, **f_name_to_geo, **d_name_to_geo}
```

- [ ] **Step 3: Recompute LL slot constants**

After updating cube.py and moves.py, run this script to find the new slot indices for U's adjacent corners/edges:

```bash
cd /home/bjafl/source/rubiks && python3 -c "
from megaminx.cube import CORNERS, EDGES, FACES
u_idx = FACES.index('U')
ll_corner = tuple(sorted(i for i, c in enumerate(CORNERS) if u_idx in c))
ll_edge   = tuple(sorted(i for i, e in enumerate(EDGES)   if u_idx in e))
print('LL_CORNER_SLOTS:', ll_corner)
print('LL_EDGE_SLOTS:  ', ll_edge)
"
```

Update `megaminx/ll_catalog.py` lines 17–18 with the printed values:

```python
LL_CORNER_SLOTS: tuple[int, ...] = (<values from script>)
LL_EDGE_SLOTS: tuple[int, ...]   = (<values from script>)
```

- [ ] **Step 4: Smoke test**

```bash
cd /home/bjafl/source/rubiks && python -m pytest tests/ -q --tb=short 2>&1 | tail -10
```

Expected: failures in algorithm/CO/EP/CP tests (algorithm strings still use old U). Note which tests fail — those are fixed in Task 8.

---

### Task 8: Swap U↔F in all hardcoded algorithm strings

**Files:**
- Modify: `megaminx/algorithms.py`
- Modify: `scripts/gen_ep_cp_catalogs.py`
- Modify: `scripts/analyze_co_pairs.py`
- Modify: `scripts/analyze_pll_primitives.py`

Apply rule: replace `U`→`F`, `U-`→`F-`, `U++`→`F++`, `U--`→`F--` and simultaneously `F`→`U`, `F-`→`U-`, `F++`→`U++`, `F--`→`U--` in all move token strings.

- [ ] **Step 1: Update `megaminx/algorithms.py` — ALGORITHM_SETS and SINGLE_ALGS**

Replace the entire contents of ALGORITHM_SETS and SINGLE_ALGS:

```python
ALGORITHM_SETS: dict[str, list[list[str]]] = {
    # Corner Orientation algorithms
    "CO_ALGS": [
        ["R", "F", "R-", "F", "R", "F--", "R-"],          # Sune
        ["R-", "F-", "R", "F-", "R-", "F++", "R"],         # Anti-Sune
        ["R", "F++", "R-", "F-", "R", "F-", "R-"],         # Double Sune variant
    ],
    # Corner Permutation algorithms
    "CP_ALGS": [
        ["R-", "F", "L", "F-", "R", "F", "L-", "F-"],     # Niklas: 3-cycle
        ["F", "L", "F-", "R-", "F", "L-", "F-", "R"],     # Niklas⁻¹: inverse 3-cycle
    ],
    # Last Layer combined
    "LL_ALGS": [
        ["R", "F", "R-", "F-"],                             # Sexy move
        ["R-", "U", "R", "U-"],                             # Sledgehammer
        ["U", "R", "F-", "R-", "F-", "R", "F", "R-", "U-"],  # T-perm
    ],
    # Edge orientation
    "EO_ALGS": [
        ["U", "R", "F", "R-", "F-", "U-"],                 # OLL edge flip
    ],
}

SINGLE_ALGS: dict[str, list[str]] = {
    "CO9":        ["R", "F++", "R-", "F-", "R", "F", "R-", "F-", "R", "F-", "R-"],
    "CO10":       ["R", "F", "R-", "F", "R", "F-", "R-", "F", "R", "F--", "R-"],
    "SUNE":       ["R", "F", "R-", "F", "R", "F--", "R-"],
    "ANTI_SUNE":  ["R-", "F-", "R", "F-", "R-", "F++", "R"],
    "NIKLAS":     ["R-", "F", "L", "F-", "R", "F", "L-", "F-"],
    "NIKLAS_INV": ["F", "L", "F-", "R-", "F", "L-", "F-", "R"],
    "EP1":        ["R++", "F--", "R--", "F-", "R++", "F--", "R--"],
    "EP2":        ["R++", "F++", "R--", "F", "R++", "F++", "R--"],
    "SEXY":       ["R", "F", "R-", "F-"],
    "SLEDGE":     ["R-", "U", "R", "U-"],
}
```

- [ ] **Step 2: Update `scripts/gen_ep_cp_catalogs.py` — EP_ALGORITHMS**

Replace EP_ALGORITHMS dict:

```python
EP_ALGORITHMS: dict[int, str] = {
    0:  "R- F- U- F U R F- U R F R- F- U- F",
    1:  "F- U F U- R- F- R F U F- U- R- F R",
    2:  "R- F++ R F++ R- F R F-- R- F- R F-- R- F-- R F-- F",
    3:  "F-- R- F- R F- R- F++ R F-- R- F++ R F++ R- F R",
    4:  "F-- R- F++ R F++ R- F R F-- R- F- R F- R- F++ R",
    5:  "R- F- R F-- R- F-- R F++ R- F-- R F R- F R F++",
    6:  "U- F- U R U- F++ U F++ U- F U R- F-- U- F-- U F",
    7:  "F- R- F- R F-- R- F-- R F-- F- R F R- F R F-- R- F- F",
    8:  "R- F-- R F R- F R F++ R- F- R F-- R- F-- R F++",
    9:  "R- F++ U- F U R- F-- U- F U F R U- F R F-",
    10: "F- F- R F R- F R F-- R- F- R- F++ R F++ R- F R",
    11: "",  # 5-cycle — solved by AUF rotation alone
}
```

- [ ] **Step 3: Update `scripts/gen_ep_cp_catalogs.py` — CP_ALGORITHMS**

Replace CP_ALGORITHMS dict:

```python
CP_ALGORITHMS: dict[int, str] = {
    0:  "F F- R F-- R- F- R F-- R- F++ R- F- R F-- R- F-- R F",
    1:  "F- R- F++ R F++ R- F R F-- R F++ R- F R F++ R- F F-",
    2:  "F-- R F-- U- F- U F- U- F- R- F R F++ U F- R-",
    3:  "U R F++ R- U F U- R U R- F- R U- F-- R- U-",
    4:  "R F++ R- U F U- R U R- F- R U- F-- R-",
    5:  "U R F++ U R- F R U- R- U F- U- R F-- R- U-",
    6:  "F- R F-- R- F-- R F- R- F++ F R- F++ R F R- F++ R F--",
    7:  "R- F- U- F U F- U- F U F- U- F U R",
    8:  "R F++ U R- F R U- R- U F- U- R F-- R-",
    9:  "F++ R- F-- R F- R- F-- R F- F-- R F R- F++ R F++ R- F",
    10: "U F-- U- F- U F U- F-- R- U F- U- F-- R F R- F++ R",
    11: "",  # 5-cycle — solved by AUF rotation alone
}
```

- [ ] **Step 4: Update `scripts/analyze_co_pairs.py` — CO_ALGS**

Replace CO_ALGS dict (16 entries — all U→F, no F moves in CO algs except Fc variants):

```python
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
```

- [ ] **Step 5: Update `scripts/analyze_pll_primitives.py` — CO_ALGS**

Same 16 entries as Step 4, plus Fc1/Fc2 (which have F moves too):

```python
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
```

- [ ] **Step 6: Run tests**

```bash
cd /home/bjafl/source/rubiks && python -m pytest tests/ -q --tb=short 2>&1 | tail -10
```

Expected: `2 failed, 256 passed` (same pre-existing failures only). If new failures appear, they will be in tests that hardcode specific algorithm strings — fix them to match the new U↔F convention.

---

### Task 9: Regenerate JSON catalogs and commit U↔F rename

**Files:**
- Regenerate: `ll_catalog/ep.json`, `ll_catalog/cp.json`
- Regenerate: `viewer/geometry.json`

- [ ] **Step 1: Regenerate EP and CP catalogs**

```bash
cd /home/bjafl/source/rubiks && python3 scripts/gen_ep_cp_catalogs.py
```

Expected:
```
Building EP catalog...
  EP: 12/12 verified
Building CP catalog...
  CP: 12/12 verified

Saved to ll_catalog/ep.json and ll_catalog/cp.json
```

If any FAIL lines appear, the algorithm for that case is wrong — the U↔F swap was not applied correctly to that entry. Cross-check the affected entry in Step 2 or Step 3 of Task 8.

- [ ] **Step 2: Regenerate geometry.json**

```bash
cd /home/bjafl/source/rubiks && python -m mcp_server.gen_geometry
```

- [ ] **Step 3: Run full test suite**

```bash
cd /home/bjafl/source/rubiks && python -m pytest tests/ -q --tb=short 2>&1 | tail -5
```

Expected: `2 failed, 256 passed`.

- [ ] **Step 4: Stage and commit**

```bash
cd /home/bjafl/source/rubiks
git add megaminx/cube.py megaminx/moves.py megaminx/ll_catalog.py \
        megaminx/algorithms.py \
        scripts/gen_ep_cp_catalogs.py \
        scripts/analyze_co_pairs.py \
        scripts/analyze_pll_primitives.py \
        ll_catalog/ep.json ll_catalog/cp.json \
        viewer/geometry.json
git commit -m "$(cat <<'EOF'
refactor: swap U↔F face names to match WCA viewer orientation

Camera sits at (0, 5, +3) — the face formerly called 'U' (z=+0.724)
faced the camera and appeared as the front face; 'F' (z=−0.724) appeared
at the top of the viewport. Swapping the abstract names fixes the visual
convention so U=top, F=front matches WCA Megaminx notation.

All algorithm strings (CO/EP/CP catalogs, named algorithms, analysis
scripts) updated by simultaneously replacing U↔F in every move token.
LL_CORNER_SLOTS and LL_EDGE_SLOTS recomputed for new U (old F face).
Geometry matching code in moves.py updated accordingly.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 5: Verify**

```bash
git log --oneline -3
```
