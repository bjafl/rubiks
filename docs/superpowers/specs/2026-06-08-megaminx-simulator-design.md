# Megaminx Simulator — Design Spec

**Dato:** 2026-06-08
**Prosjekt:** `/home/bjafl/source/rubiks/`
**Status:** Godkjent av bruker

---

## Oversikt

Python-bibliotek som simulerer en Megaminx (dodekaeder-puslespill med 12 femkantede flater). Formål: utforskning av puzzle-struktur, algoritmetesting, partial solving og et MCP-grensesnitt slik at AI-klienter kan forstå og manipulere puzzle-state via naturlig språk.

---

## Prosjektstruktur

```
rubiks/
  megaminx/
    __init__.py
    model.py        # MegaminxState, cubie-definisjoner, validate_state
    moves.py        # Move-tabell, WCA-parsing, apply_move
    algorithms.py   # Navngitte algoritmesett (CO, CP, LL, T-perm, etc.)
    solver.py       # IDA* path-finding mellom states
    heuristics.py   # Admissibel heuristikk (pattern database subset)
    utils.py        # Scramble-generator, state-beskrivelse, pretty-print
  mcp_server/
    __init__.py
    server.py       # FastMCP tools
    session.py      # Aktiv state + undo-stack per sesjon
  tests/
    test_model.py
    test_moves.py
    test_solver.py
    test_mcp.py
  pyproject.toml
  .gitignore
```

---

## State-modell (`model.py`)

### Cubie-representasjon

En Megaminx består av:
- **12 sentre** — faste, definerer fargen per flate (indeksert 0–11)
- **20 hjørner** — hvert berører 3 flater; har `position` (0–19) og `orientation` (0–2)
- **30 kanter** — hvert berører 2 flater; har `position` (0–29) og `orientation` (0–1)

```python
@dataclass
class MegaminxState:
    corners: np.ndarray  # shape (20, 2) — kolonne 0: pos, kolonne 1: ori
    edges:   np.ndarray  # shape (30, 2) — kolonne 0: pos, kolonne 1: ori

SOLVED_STATE = MegaminxState(
    corners=np.array([[i, 0] for i in range(20)]),
    edges=np.array([[i, 0] for i in range(30)]),
)
```

`is_solved(state)` sammenligner mot `SOLVED_STATE`.

### Validering

`validate_state(state) -> ValidationResult` kalles av alle set-operasjoner.

| Sjekk | Krav |
|---|---|
| Permutasjon — hjørner | Posisjoner er en permutasjon av 0–19 |
| Permutasjon — kanter | Posisjoner er en permutasjon av 0–29 |
| Orientering range | Corner-ori ∈ {0,1,2}; edge-ori ∈ {0,1} |
| Corner-orienteringssum | Σ corner-ori ≡ 0 (mod 3) |
| Edge-orienteringssum | Σ edge-ori ≡ 0 (mod 2) |
| Paritetskonsistens | Paritet(corner-perm) = Paritet(edge-perm) |

```python
@dataclass
class ValidationResult:
    valid: bool
    errors: list[str]
```

Ugyldige states avvises med meningsfulle feilmeldinger.

---

## Move-notasjon (`moves.py`)

### WCA-notasjon

12 flater: `U, F, R, L, BR, BL, DR, DL, B, DBR, DBL, D`

Suffiks:
- (ingen) eller `+` → CW 72°
- `++` → CW 144° (= 2× CW)
- `-` → CCW 72°
- `--` → CCW 144° (= 2× CCW, = `++` invers)

Totalt 24 unike atomære trekk (12 flater × CW/CCW).

### Intern representasjon

Hvert trekk er forhåndsberegnet som:
- 5-sykkel av hjørneposisjoner
- 5-sykkel av kanteposisjoner
- Orienterings-delta per berørt brikke

`apply_move(state, move_str) -> MegaminxState` — returnerer ny state uten mutasjon (immutabel).

---

## Solver (`solver.py` + `heuristics.py`)

### Fokus: path-finding mellom states

Full optimal løsning fra tilfeldig scramble er upraktisk (tilstandsrom ~10⁶⁸). Designet fokuserer på:

```python
def solve_path(
    from_state: MegaminxState,
    to_state:   MegaminxState,
    move_set:   list[str] | None = None,   # None = alle 24 WCA-trekk
    max_depth:  int = 12,
) -> list[str] | None
```

- **`move_set=None`** og lav `max_depth`: egnet for nær-løste states.
- **`move_set=CO_ALGS`** (8–12 algoritmer): søkerommet krympes drastisk; IDA* er praktisk.
- Returnerer `None` med advarsel dersom søkerommet er for stort (estimert fra `len(move_set)^max_depth`).

### Algoritme

IDA* med admissibel heuristikk:
- Heuristikk: antall feilplasserte brikker i en valgt delmengde (pattern-database for hjørnene i én lag).
- Pruning: ingen to påfølgende trekk på samme flate; ingen trekk som er umiddelbar invers av forrige.

---

## Algoritmer (`algorithms.py`)

Forhåndsdefinerte navngitte algoritmesett:

| Navn | Beskrivelse |
|---|---|
| `CO_ALGS` | Corner Orientation — algoritmer som kun påvirker hjørneorientering |
| `CP_ALGS` | Corner Permutation |
| `LL_ALGS` | Last Layer — kombinert sett |
| `T_PERM`, `U_PERM`, ... | Enkeltalgoritmer fra standard Megaminx-metode |

Hvert sett er en `list[list[str]]` (liste av move-sekvenser). Brukes direkte som `move_set` i `solve_path`.

---

## MCP-server (`mcp_server/server.py`)

Bygget med **FastMCP**. Én aktiv `MegaminxState` per sesjon med undo-stack (siste 20 states).

### Tools

| Tool | Signatur | Beskrivelse |
|---|---|---|
| `get_state` | `() -> dict` | Nåværende state (human-readable + intern repr) |
| `is_solved` | `() -> bool` | Er puzzlet løst? |
| `get_face` | `(face: str) -> dict` | Farger på én flate |
| `apply_move` | `(move: str) -> dict` | Utfør ett WCA-trekk, returner ny state |
| `apply_sequence` | `(moves: list[str]) -> dict` | Utfør move-sekvens |
| `scramble` | `(n: int = 30) -> list[str]` | Tilfeldig scramble, returner sekvensen |
| `set_state` | `(state_dict: dict) -> ValidationResult` | Sett eksakt state; validerer før aksept |
| `set_layer_solved` | `(layer: str) -> ValidationResult` | Sett ett lag til løst, resten urørt; validerer |
| `scramble_substate` | `(region: str) -> list[str]` | Scramble kun LL/CO/etc. |
| `solve_path` | `(to_state: dict, move_set?: str, max_depth?: int) -> list[str] \| null` | Finn vei fra nåværende → target |
| `apply_named_alg` | `(name: str) -> dict` | Bruk navngitt algoritme |
| `explain_sequence` | `(moves: list[str]) -> list[dict]` | State før/etter hvert trekk + tekstbeskrivelse av effekt |
| `list_algorithms` | `() -> dict` | List tilgjengelige navngitte algoritmesett |
| `undo` | `(steps: int = 1) -> dict` | Gå tilbake N states |

### Validering i set-operasjoner

`set_state` og `set_layer_solved` kaller `validate_state()` og returnerer `ValidationResult` med feilmeldinger ved ugyldig input. Ingen state-endring skjer ved ugyldig input.

---

## Avhengigheter

```toml
[project]
requires-python = ">=3.11"

[project.dependencies]
numpy = ">=1.26"
fastmcp = ">=2.0"
pydantic = ">=2.0"

[project.optional-dependencies]
dev = ["pytest", "pytest-cov", "ruff", "mypy"]
```

---

## Testing

| Testfil | Dekker |
|---|---|
| `test_model.py` | `validate_state` — gyldige og ugyldige states, alle 6 feiltyper |
| `test_moves.py` | `apply_move` — alle 24 trekk; 4× samme trekk → solved; invers-par |
| `test_solver.py` | `solve_path` — løser kjente 1–5-trekk problemer; returnerer None ved for dypt søk |
| `test_mcp.py` | MCP-tools via FastMCP test-klient; validering avviser ugyldig input |

---

## Ikke i scope (v1)

- GUI / visuell rendering
- Full optimal solve fra tilfeldig scramble
- Nettbasert API
- Støtte for andre puzzles (Pyraminx, Skewb, etc.)
