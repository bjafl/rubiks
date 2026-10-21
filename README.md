# Megaminx Simulator

A Python library that simulates a Megaminx (dodecahedron puzzle), with an IDA* solver, named algorithm sets, and a FastMCP server so AI clients can inspect and manipulate puzzle state via natural language.

## Features

- **Accurate state model** — cubie representation (20 corners, 30 edges) with full group-theory validation
- **WCA move notation** — all 24 atomic moves (`U`, `F`, `R-`, `U++`, etc.)
- **Correct orientation tracking** — corner/edge orientations change properly under every move
- **IDA* solver** — find shortest path between any two states, optionally restricted to a named algorithm set
- **Named algorithms** — Sune, Anti-Sune, Sexy, Sledgehammer and more, organized into sets (CO, CP, LL, EO)
- **FastMCP server** — 14 tools for AI clients: apply moves, scramble, solve, explain, undo

## Project layout

```
megaminx/
  model.py        State dataclass, validation, is_solved
  moves.py        Dodecahedron geometry, move table, apply_move
  algorithms.py   Named algorithm sets
  heuristics.py   Admissible lower_bound for IDA*
  solver.py       IDA* solve_path(A → B)
  utils.py        scramble, state_to_dict, dict_to_state, describe_state
mcp_server/
  session.py      SessionState with undo stack
  server.py       FastMCP tools
tests/
  test_model.py
  test_moves.py
  test_algorithms.py
  test_heuristics.py
  test_solver.py
  test_utils.py
  test_session.py
  test_mcp.py
```

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest          # 55 tests
```

## Usage

```python
from megaminx import SOLVED_STATE, scramble, solve_path, apply_sequence, is_solved, describe_state

# Scramble
state = scramble(SOLVED_STATE.copy(), 30)
print(describe_state(state))
# State: UNSOLVED — 20/20 corners misplaced (8 twisted), 30/30 edges misplaced (12 flipped)

# Solve a near-solved state (3 moves away)
from megaminx.moves import apply_sequence as aseq
near = aseq(SOLVED_STATE.copy(), ["U", "F", "R-"])
solution = solve_path(near, SOLVED_STATE.copy(), max_depth=6)
print(solution)   # ['R', 'F-', 'U-']
```

### Apply algorithms

```python
from megaminx.algorithms import ALGORITHM_SETS, get_single_alg
from megaminx.moves import apply_sequence

sune = get_single_alg("SUNE")            # ["R", "U", "R-", "U", "R", "U++", "R-"]
state = apply_sequence(SOLVED_STATE.copy(), sune)
```

### Solve from A to B using a restricted move set

```python
from megaminx.algorithms import get_algorithm_set

solution = solve_path(
    state_a,
    state_b,
    move_set=["U", "U-", "R", "R-"],  # restrict search to these moves
    max_depth=12,
)
```

## MCP server

```bash
python -m mcp_server.server
```

### Available tools

| Tool | Description |
|---|---|
| `tool_get_state` | Current state (human-readable + cubie data) |
| `tool_is_solved` | Is the puzzle solved? |
| `tool_get_face` | Pieces on a named face |
| `tool_apply_move` | Apply one WCA move |
| `tool_apply_sequence` | Apply a list of moves |
| `tool_scramble` | Random scramble |
| `tool_set_state` | Set exact state (validated) |
| `tool_set_layer_solved` | Set U_CAP or D_CAP to solved |
| `tool_scramble_substate` | Scramble only U_CAP or D_CAP |
| `tool_solve_path` | IDA* from current state to target |
| `tool_apply_named_alg` | Apply a named algorithm (SUNE, SEXY, …) |
| `tool_explain_sequence` | State before/after each move + what changed |
| `tool_list_algorithms` | List available algorithm sets |
| `tool_undo` | Undo N moves |

## Move notation

Faces: `U  F  R  BR  BL  L  dR  dBR  B  dBL  dL  D`

| Suffix | Meaning |
|---|---|
| (none) or `+` | CW 72° |
| `++` | CW 144° |
| `-` | CCW 72° |
| `--` | CCW 144° |

## State model

```python
@dataclass
class MegaminxState:
    corners: np.ndarray  # shape (20, 2): [position, orientation]
    edges:   np.ndarray  # shape (30, 2): [position, orientation]
```

`validate_state` checks six group-theory constraints: corner and edge permutations are valid, orientations are in range, `Σ corner_ori ≡ 0 (mod 3)`, `Σ edge_ori ≡ 0 (mod 2)`, and parity(corners) = parity(edges).

## Dependencies

| Package | Purpose |
|---|---|
| `numpy >= 1.26` | State arrays and geometry |
| `fastmcp >= 2.0` | MCP server |
| `pydantic >= 2.0` | FastMCP internals |

Python 3.11+.

## License

MIT — see [LICENSE](LICENSE).
