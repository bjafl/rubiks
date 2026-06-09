# Megaminx 3D Viewer — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an interactive 3D Megaminx viewer (Three.js browser client) served by a Python HTTP+WebSocket server, with MCP tools that control the viewer in real-time.

**Architecture:** `mcp_server/viewer_server.py` serves static files (HTTP, threaded) and WebSocket (asyncio) on localhost. MCP tools in `server.py` POST JSON commands to the viewer server's REST API (`POST /api/command`). The browser receives state snapshots via WebSocket and renders them in Three.js with per-step color updates.

**Tech Stack:** Python 3.11+, `websockets` library (already installed), `http.server` (stdlib), Three.js r169 via CDN importmap, native ES modules (no bundler).

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `megaminx/algorithms.py` | Modify | Add CO9, CO10, NIKLAS, EP1/EP2 + `get_library()` |
| `megaminx/moves.py` | Modify | Add public `get_geometry_data()` |
| `mcp_server/viewer_state.py` | Create | `ViewerState` dataclass + `parse_sequence()` |
| `mcp_server/gen_geometry.py` | Create | Writes `viewer/geometry.json` from moves.py data |
| `viewer/geometry.json` | Generate | 3D geometry + face/piece mappings for browser |
| `mcp_server/viewer_server.py` | Create | HTTP static + WebSocket + REST API |
| `mcp_server/server.py` | Modify | Add 7 MCP viewer tools (POST to viewer_server) |
| `viewer/index.html` | Create | Layout C shell |
| `viewer/js/scene.js` | Create | Three.js scene, camera, renderer, OrbitControls |
| `viewer/js/megaminx.js` | Create | Dodecahedron geometry, sticker coloring |
| `viewer/js/svg.js` | Create | Top-down SVG renderer (state → DOM element) |
| `viewer/js/controls.js` | Create | Play/pause/step/speed/progress UI |
| `viewer/js/library.js` | Create | Algorithm list + freetext input |
| `viewer/js/main.js` | Create | App entry: WebSocket + dispatch to modules |
| `tests/test_viewer_state.py` | Create | ViewerState unit tests |
| `tests/test_gen_geometry.py` | Create | Geometry JSON structure tests |

---

### Task 1: Expand algorithms.py with full LL algorithm set

**Files:**
- Modify: `megaminx/algorithms.py`
- Test: `tests/test_algorithms.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_algorithms.py`:

```python
from megaminx.algorithms import get_library, SINGLE_ALGS, LIBRARY_ORDER

def test_single_algs_has_co9():
    assert "CO9" in SINGLE_ALGS
    assert SINGLE_ALGS["CO9"] == [
        "FR", "U++", "FR-", "U-", "FR", "U", "FR-", "U-", "FR", "U-", "FR-"
    ]

def test_single_algs_has_co10():
    assert "CO10" in SINGLE_ALGS
    assert SINGLE_ALGS["CO10"] == [
        "FR", "U", "FR-", "U", "FR", "U-", "FR-", "U", "FR", "U--", "FR-"
    ]

def test_single_algs_has_niklas():
    assert "NIKLAS" in SINGLE_ALGS
    assert "NIKLAS_INV" in SINGLE_ALGS

def test_single_algs_has_ep():
    assert "EP1" in SINGLE_ALGS
    assert "EP2" in SINGLE_ALGS

def test_get_library_returns_ordered_list():
    lib = get_library()
    assert isinstance(lib, list)
    assert len(lib) >= 8
    names = [e["name"] for e in lib]
    assert "CO9" in names
    assert "CO10" in names
    assert "SUNE" in names
    assert "NIKLAS" in names

def test_get_library_entries_have_moves():
    for entry in get_library():
        assert "name" in entry
        assert "moves" in entry
        assert isinstance(entry["moves"], list)
        assert len(entry["moves"]) > 0

def test_library_order_constant():
    assert LIBRARY_ORDER[0] == "CO9"
    assert LIBRARY_ORDER[1] == "CO10"
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd /home/bjafl/source/rubiks
source .venv/bin/activate
pytest tests/test_algorithms.py::test_single_algs_has_co9 -v
```

Expected: FAIL with `KeyError` or `AssertionError`.

- [ ] **Step 3: Expand algorithms.py**

Replace the `SINGLE_ALGS` dict and add `LIBRARY_ORDER` + `get_library()`:

```python
SINGLE_ALGS: dict[str, list[str]] = {
    "CO9":        ["FR", "U++", "FR-", "U-", "FR", "U", "FR-", "U-", "FR", "U-", "FR-"],
    "CO10":       ["FR", "U", "FR-", "U", "FR", "U-", "FR-", "U", "FR", "U--", "FR-"],
    "SUNE":       ["FR", "U", "FR-", "U", "FR", "U--", "FR-"],
    "ANTI_SUNE":  ["FR-", "U-", "FR", "U-", "FR-", "U++", "FR"],
    "NIKLAS":     ["FR", "U-", "FL-", "U", "FR-", "U-", "FL", "U"],
    "NIKLAS_INV": ["U-", "FL-", "U", "FR", "U-", "FL", "U", "FR-"],
    "EP1":        ["FR++", "U--", "FR--", "U-", "FR++", "U--", "FR--"],
    "EP2":        ["FR++", "U++", "FR--", "U", "FR++", "U++", "FR--"],
    "SEXY":       ["FR", "U", "FR-", "U-"],
    "SLEDGE":     ["FR-", "F", "FR", "F-"],
}

LIBRARY_ORDER = [
    "CO9", "CO10", "SUNE", "ANTI_SUNE", "NIKLAS", "NIKLAS_INV", "EP1", "EP2",
]


def get_library() -> list[dict]:
    """Return algorithms in display order for the viewer library."""
    return [{"name": n, "moves": SINGLE_ALGS[n]} for n in LIBRARY_ORDER]
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_algorithms.py -v
```

Expected: all algorithm tests PASS.

- [ ] **Step 5: Commit**

```bash
git add megaminx/algorithms.py tests/test_algorithms.py
git commit -m "feat(algorithms): add CO9/CO10/Niklas/EP1/EP2 + get_library()"
```

---

### Task 2: Add public geometry accessor to moves.py

**Files:**
- Modify: `megaminx/moves.py`
- Test: `tests/test_moves.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_moves.py`:

```python
from megaminx.moves import get_geometry_data, FACE_NAMES

def test_get_geometry_data_structure():
    g = get_geometry_data()
    for key in ["face_names", "face_vertices", "face_centers",
                "face_corner_cycles", "face_edge_cycles", "corner_faces", "edge_faces"]:
        assert key in g, f"Missing key: {key}"

def test_get_geometry_data_counts():
    g = get_geometry_data()
    assert len(g["face_names"]) == 12
    assert len(g["face_vertices"]) == 12
    assert all(len(fv) == 5 for fv in g["face_vertices"])
    assert all(len(v) == 3 for fv in g["face_vertices"] for v in fv)
    assert len(g["face_corner_cycles"]) == 12
    assert all(len(cc) == 5 for cc in g["face_corner_cycles"])
    assert len(g["corner_faces"]) == 20
    assert all(len(cf) == 3 for cf in g["corner_faces"])
    assert len(g["edge_faces"]) == 30
    assert all(len(ef) == 2 for ef in g["edge_faces"])

def test_get_geometry_data_face_names_match():
    g = get_geometry_data()
    assert g["face_names"] == FACE_NAMES
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_moves.py::test_get_geometry_data_structure -v
```

Expected: FAIL with `ImportError`.

- [ ] **Step 3: Add function to moves.py**

Append to `megaminx/moves.py` (after `ALL_MOVES = ...`):

```python
def get_geometry_data() -> dict:
    """Return dodecahedron geometry and piece-slot mappings as plain Python types."""
    return {
        "face_names":        list(FACE_NAMES),
        "face_vertices":     [[_RAW_VERTS[v].tolist() for v in fv] for fv in _FACE_VERTS],
        "face_centers":      [c.tolist() for c in _face_centers],
        "face_corner_cycles": [list(MOVE_TABLE[fi]["corner_cycle"]) for fi in range(12)],
        "face_edge_cycles":   [list(MOVE_TABLE[fi]["edge_cycle"])   for fi in range(12)],
        "corner_faces":      [list(cf) for cf in CORNER_FACES],
        "edge_faces":        [list(ef) for ef in EDGE_FACES],
    }
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_moves.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add megaminx/moves.py tests/test_moves.py
git commit -m "feat(moves): add public get_geometry_data() for viewer"
```

---

### Task 3: Create mcp_server/viewer_state.py

**Files:**
- Create: `mcp_server/viewer_state.py`
- Create: `tests/test_viewer_state.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_viewer_state.py
import pytest
from mcp_server.viewer_state import ViewerState, parse_sequence


def test_initial_state_is_solved():
    vs = ViewerState()
    snap = vs.state_snapshot()
    assert snap["type"] == "state"
    assert snap["moveIndex"] == 0
    assert snap["totalMoves"] == 0
    assert snap["algName"] is None
    for i, (piece, ori) in enumerate(snap["corners"]):
        assert piece == i and ori == 0
    for i, (piece, ori) in enumerate(snap["edges"]):
        assert piece == i and ori == 0


def test_load_sequence_resets_to_solved():
    vs = ViewerState()
    vs.load_sequence(["U", "U-"], alg_name=None)
    snap = vs.state_snapshot()
    assert snap["totalMoves"] == 2
    assert snap["moveIndex"] == 0
    for i, (piece, _) in enumerate(snap["corners"]):
        assert piece == i  # not yet moved


def test_step_forward_advances_index():
    vs = ViewerState()
    vs.load_sequence(["U", "FR"], alg_name="test")
    vs.step_forward()
    snap = vs.state_snapshot()
    assert snap["moveIndex"] == 1
    assert snap["currentMove"] == "U"


def test_step_forward_at_end_returns_false():
    vs = ViewerState()
    vs.load_sequence(["U"])
    vs.step_forward()
    assert vs.step_forward() is False


def test_step_backward_reverses():
    vs = ViewerState()
    vs.load_sequence(["U", "FR"])
    vs.step_forward()
    vs.step_forward()
    vs.step_backward()
    assert vs.state_snapshot()["moveIndex"] == 1


def test_step_backward_at_start_returns_false():
    vs = ViewerState()
    vs.load_sequence(["U"])
    assert vs.step_backward() is False


def test_rewind_to_rebuilds_state():
    vs = ViewerState()
    vs.load_sequence(["U", "U", "U", "U", "U"])  # 5× U = identity
    vs.rewind_to(5)
    snap = vs.state_snapshot()
    assert snap["moveIndex"] == 5
    for i, (piece, ori) in enumerate(snap["corners"]):
        assert piece == i and ori == 0


def test_rewind_to_clamps():
    vs = ViewerState()
    vs.load_sequence(["U"])
    vs.rewind_to(999)
    assert vs.move_index == 1
    vs.rewind_to(-5)
    assert vs.move_index == 0


def test_reset_clears_everything():
    vs = ViewerState()
    vs.load_sequence(["U", "FR"], alg_name="X")
    vs.step_forward()
    vs.reset()
    snap = vs.state_snapshot()
    assert snap["totalMoves"] == 0
    assert snap["moveIndex"] == 0
    assert snap["algName"] is None


def test_parse_sequence_valid():
    assert parse_sequence("FR U++ FR- U-") == ["FR", "U++", "FR-", "U-"]


def test_parse_sequence_strips_whitespace():
    assert parse_sequence("  U   FR-  ") == ["U", "FR-"]


def test_parse_sequence_rejects_bad_move():
    with pytest.raises(ValueError):
        parse_sequence("FR XYZ U")


def test_state_snapshot_current_move_none_at_start():
    vs = ViewerState()
    vs.load_sequence(["U"])
    assert vs.state_snapshot()["currentMove"] is None


def test_state_snapshot_current_move_after_step():
    vs = ViewerState()
    vs.load_sequence(["U", "FR-"])
    vs.step_forward()
    assert vs.state_snapshot()["currentMove"] == "U"
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_viewer_state.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement viewer_state.py**

```python
# mcp_server/viewer_state.py
from __future__ import annotations
import asyncio
import json
from dataclasses import dataclass, field
from megaminx.model import SOLVED_STATE
from megaminx.moves import apply_move, parse_move


def parse_sequence(text: str) -> list[str]:
    """Parse space-separated move string in project notation. Raises ValueError on bad move."""
    moves = text.strip().split()
    if not moves:
        raise ValueError("Empty sequence")
    for m in moves:
        parse_move(m)
    return moves


@dataclass
class ViewerState:
    megaminx: object = field(default_factory=lambda: SOLVED_STATE.copy())
    sequence: list[str] = field(default_factory=list)
    move_index: int = 0
    alg_name: str | None = None
    ws_clients: set = field(default_factory=set, repr=False)

    def state_snapshot(self) -> dict:
        return {
            "type": "state",
            "corners": [
                [int(self.megaminx.corners[i, 0]), int(self.megaminx.corners[i, 1])]
                for i in range(20)
            ],
            "edges": [
                [int(self.megaminx.edges[i, 0]), int(self.megaminx.edges[i, 1])]
                for i in range(30)
            ],
            "moveIndex":   self.move_index,
            "totalMoves":  len(self.sequence),
            "currentMove": self.sequence[self.move_index - 1] if self.move_index > 0 else None,
            "algName":     self.alg_name,
        }

    def load_sequence(self, moves: list[str], alg_name: str | None = None) -> None:
        self.megaminx  = SOLVED_STATE.copy()
        self.sequence  = list(moves)
        self.move_index = 0
        self.alg_name  = alg_name

    def step_forward(self) -> bool:
        if self.move_index >= len(self.sequence):
            return False
        self.megaminx = apply_move(self.megaminx, self.sequence[self.move_index])
        self.move_index += 1
        return True

    def step_backward(self) -> bool:
        if self.move_index <= 0:
            return False
        self.move_index -= 1
        self.megaminx = SOLVED_STATE.copy()
        for m in self.sequence[: self.move_index]:
            self.megaminx = apply_move(self.megaminx, m)
        return True

    def rewind_to(self, n: int) -> None:
        n = max(0, min(n, len(self.sequence)))
        self.megaminx = SOLVED_STATE.copy()
        for m in self.sequence[:n]:
            self.megaminx = apply_move(self.megaminx, m)
        self.move_index = n

    def reset(self) -> None:
        self.megaminx   = SOLVED_STATE.copy()
        self.sequence   = []
        self.move_index = 0
        self.alg_name   = None

    async def broadcast(self, msg: dict) -> None:
        if not self.ws_clients:
            return
        dead: set = set()
        payload = json.dumps(msg)
        for ws in list(self.ws_clients):
            try:
                await ws.send(payload)
            except Exception:
                dead.add(ws)
        self.ws_clients -= dead
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_viewer_state.py -v
```

Expected: all 14 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add mcp_server/viewer_state.py tests/test_viewer_state.py
git commit -m "feat(viewer): ViewerState + parse_sequence with full test suite"
```

---

### Task 4: Generate viewer/geometry.json

**Files:**
- Create: `mcp_server/gen_geometry.py`
- Generate: `viewer/geometry.json`
- Create: `tests/test_gen_geometry.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_gen_geometry.py
import json
from pathlib import Path

GEOMETRY_PATH = Path(__file__).parent.parent / "viewer" / "geometry.json"


def test_geometry_file_exists():
    assert GEOMETRY_PATH.exists(), "Run: python -m mcp_server.gen_geometry"


def test_geometry_top_level_keys():
    g = json.loads(GEOMETRY_PATH.read_text())
    for key in ["faceNames", "faceColors", "faceVertices", "faceCenters",
                "faceCornerCycles", "faceEdgeCycles", "cornerFaces", "edgeFaces"]:
        assert key in g, f"Missing key: {key}"


def test_geometry_face_count():
    g = json.loads(GEOMETRY_PATH.read_text())
    assert len(g["faceNames"]) == 12
    assert len(g["faceVertices"]) == 12
    assert len(g["faceCenters"]) == 12


def test_geometry_face_vertices_shape():
    g = json.loads(GEOMETRY_PATH.read_text())
    for fv in g["faceVertices"]:
        assert len(fv) == 5
        for v in fv:
            assert len(v) == 3


def test_geometry_corner_counts():
    g = json.loads(GEOMETRY_PATH.read_text())
    assert len(g["cornerFaces"]) == 20
    assert all(len(cf) == 3 for cf in g["cornerFaces"])
    assert len(g["faceCornerCycles"]) == 12
    assert all(len(cc) == 5 for cc in g["faceCornerCycles"])


def test_geometry_edge_counts():
    g = json.loads(GEOMETRY_PATH.read_text())
    assert len(g["edgeFaces"]) == 30
    assert all(len(ef) == 2 for ef in g["edgeFaces"])
    assert all(len(ec) == 5 for ec in g["faceEdgeCycles"])


def test_geometry_u_is_first():
    g = json.loads(GEOMETRY_PATH.read_text())
    assert g["faceNames"][0] == "U"
    assert g["faceNames"][-1] == "D"


def test_geometry_colors_all_present():
    g = json.loads(GEOMETRY_PATH.read_text())
    for name in g["faceNames"]:
        assert name in g["faceColors"]
        color = g["faceColors"][name]
        assert color.startswith("#") and len(color) == 7
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_gen_geometry.py::test_geometry_file_exists -v
```

Expected: FAIL (file doesn't exist).

- [ ] **Step 3: Create gen_geometry.py and viewer/ directory**

```bash
mkdir -p /home/bjafl/source/rubiks/viewer/js
```

```python
# mcp_server/gen_geometry.py
"""Generate viewer/geometry.json from moves.py dodecahedron geometry data.

Run: python -m mcp_server.gen_geometry
"""
from __future__ import annotations
import json
from pathlib import Path
from megaminx.moves import get_geometry_data

FACE_COLORS: dict[str, str] = {
    "U":   "#FFFFFF",
    "F":   "#3498DB",
    "FR":  "#E74C3C",
    "BR":  "#F39C12",
    "BL":  "#E91E8C",
    "FL":  "#2ECC71",
    "DFR": "#9B59B6",
    "DR":  "#F1C40F",
    "DBR": "#1ABC9C",
    "DBL": "#95A5A6",
    "DFL": "#D35400",
    "D":   "#2C3E50",
}

OUTPUT = Path(__file__).parent.parent / "viewer" / "geometry.json"


def main() -> None:
    raw = get_geometry_data()
    out = {
        "faceNames":        raw["face_names"],
        "faceColors":       {name: FACE_COLORS[name] for name in raw["face_names"]},
        "faceVertices":     raw["face_vertices"],
        "faceCenters":      raw["face_centers"],
        "faceCornerCycles": raw["face_corner_cycles"],
        "faceEdgeCycles":   raw["face_edge_cycles"],
        "cornerFaces":      raw["corner_faces"],
        "edgeFaces":        raw["edge_faces"],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(out, indent=2))
    print(f"Written: {OUTPUT}  ({OUTPUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the generator**

```bash
cd /home/bjafl/source/rubiks
source .venv/bin/activate
python -m mcp_server.gen_geometry
```

Expected: `Written: .../viewer/geometry.json  (X KB)`

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_gen_geometry.py -v
```

Expected: all 8 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add mcp_server/gen_geometry.py viewer/geometry.json tests/test_gen_geometry.py
git commit -m "feat(viewer): gen_geometry.py + viewer/geometry.json"
```

---

### Task 5: Create viewer_server.py

**Files:**
- Create: `mcp_server/viewer_server.py`
- Create: `tests/test_viewer_server.py`

Three parts in one process:
1. HTTP thread (port 8766): static files from `viewer/` + `POST /api/command`
2. WebSocket asyncio server (port 8765): browser connections
3. Module-level `VIEWER_STATE` + `_WS_LOOP` shared between both

- [ ] **Step 1: Write failing tests**

```python
# tests/test_viewer_server.py
import json
import threading
import time
import urllib.request
import urllib.error
import pytest


@pytest.fixture(scope="module")
def running_server():
    from mcp_server import viewer_server as vs
    t = threading.Thread(target=vs.run, daemon=True)
    t.start()
    time.sleep(0.6)
    yield vs


def test_http_serves_index(running_server):
    resp = urllib.request.urlopen("http://localhost:8766/")
    assert resp.status == 200
    html = resp.read().decode()
    assert "<html" in html.lower()


def test_http_serves_geometry(running_server):
    resp = urllib.request.urlopen("http://localhost:8766/geometry.json")
    assert resp.status == 200
    data = json.loads(resp.read())
    assert "faceNames" in data


def _post_cmd(cmd: dict) -> dict:
    body = json.dumps(cmd).encode()
    req = urllib.request.Request(
        "http://localhost:8766/api/command",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())


def test_api_reset(running_server):
    result = _post_cmd({"type": "reset"})
    assert result["ok"] is True


def test_api_load_algorithm(running_server):
    from mcp_server.viewer_server import VIEWER_STATE
    _post_cmd({"type": "load_algorithm", "name": "CO9"})
    assert VIEWER_STATE.alg_name == "CO9"
    assert len(VIEWER_STATE.sequence) == 11


def test_api_step_forward(running_server):
    from mcp_server.viewer_server import VIEWER_STATE
    _post_cmd({"type": "load_algorithm", "name": "CO9"})
    before = VIEWER_STATE.move_index
    _post_cmd({"type": "step_forward"})
    assert VIEWER_STATE.move_index == before + 1


def test_api_unknown_command_returns_400(running_server):
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        _post_cmd({"type": "bogus_command"})
    assert exc_info.value.code == 400
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_viewer_server.py::test_http_serves_index -v
```

Expected: FAIL with `ModuleNotFoundError` or `ConnectionRefusedError`.

- [ ] **Step 3: Implement viewer_server.py**

```python
# mcp_server/viewer_server.py
"""HTTP static file server + WebSocket server + REST API for the Megaminx viewer.

Run standalone:  python -m mcp_server.viewer_server
HTTP port: 8766  (static files + /api/command)
WS port:   8765
"""
from __future__ import annotations
import asyncio
import json
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import websockets
from websockets.server import WebSocketServerProtocol

from megaminx.algorithms import SINGLE_ALGS, get_library
from mcp_server.viewer_state import ViewerState, parse_sequence

VIEWER_DIR = Path(__file__).parent.parent / "viewer"
HTTP_PORT  = 8766
WS_PORT    = 8765

VIEWER_STATE: ViewerState = ViewerState()
_WS_LOOP: asyncio.AbstractEventLoop | None = None


# ── WebSocket ─────────────────────────────────────────────────────────────────

async def _ws_handler(websocket: WebSocketServerProtocol) -> None:
    VIEWER_STATE.ws_clients.add(websocket)
    await websocket.send(json.dumps(VIEWER_STATE.state_snapshot()))
    try:
        async for raw in websocket:
            msg = json.loads(raw)
            if msg.get("type") == "step":
                if msg["dir"] == "fwd":
                    VIEWER_STATE.step_forward()
                else:
                    VIEWER_STATE.step_backward()
                await VIEWER_STATE.broadcast(VIEWER_STATE.state_snapshot())
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        VIEWER_STATE.ws_clients.discard(websocket)


async def _run_ws() -> None:
    global _WS_LOOP
    _WS_LOOP = asyncio.get_running_loop()
    async with websockets.serve(_ws_handler, "localhost", WS_PORT):
        await asyncio.Future()


# ── Command dispatch ──────────────────────────────────────────────────────────

def _handle_command(cmd: dict) -> dict:
    t = cmd.get("type")
    if t == "load_algorithm":
        name = cmd["name"]
        if name not in SINGLE_ALGS:
            raise KeyError(f"Unknown algorithm: {name!r}")
        VIEWER_STATE.load_sequence(SINGLE_ALGS[name], alg_name=name)
        _broadcast_sync({"type": "loaded", "algName": name, "moves": VIEWER_STATE.sequence})
        _broadcast_sync(VIEWER_STATE.state_snapshot())
    elif t == "animate_sequence":
        moves = parse_sequence(cmd["sequence"])
        VIEWER_STATE.load_sequence(moves, alg_name=None)
        _broadcast_sync({"type": "loaded", "algName": None, "moves": moves})
        _broadcast_sync(VIEWER_STATE.state_snapshot())
    elif t == "step_forward":
        VIEWER_STATE.step_forward()
        _broadcast_sync(VIEWER_STATE.state_snapshot())
    elif t == "step_backward":
        VIEWER_STATE.step_backward()
        _broadcast_sync(VIEWER_STATE.state_snapshot())
    elif t == "goto_move":
        VIEWER_STATE.rewind_to(int(cmd["n"]))
        _broadcast_sync(VIEWER_STATE.state_snapshot())
    elif t == "reset":
        VIEWER_STATE.reset()
        _broadcast_sync({"type": "reset"})
    elif t == "get_library":
        return {"ok": True, "library": get_library()}
    else:
        raise ValueError(f"Unknown command type: {t!r}")
    return {"ok": True}


def _broadcast_sync(msg: dict) -> None:
    if _WS_LOOP and not _WS_LOOP.is_closed():
        future = asyncio.run_coroutine_threadsafe(VIEWER_STATE.broadcast(msg), _WS_LOOP)
        try:
            future.result(timeout=2.0)
        except Exception:
            pass


# ── HTTP ──────────────────────────────────────────────────────────────────────

class _HTTPHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(VIEWER_DIR), **kwargs)

    def do_POST(self) -> None:
        if self.path != "/api/command":
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length))
            result = _handle_command(body)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        except (ValueError, KeyError) as exc:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": str(exc)}).encode())

    def log_message(self, *_args) -> None:
        pass


def _run_http() -> None:
    server = HTTPServer(("localhost", HTTP_PORT), _HTTPHandler)
    server.serve_forever()


# ── Entry point ───────────────────────────────────────────────────────────────

def run() -> None:
    """Start HTTP thread + WebSocket asyncio server. Blocks until interrupted."""
    http_thread = threading.Thread(target=_run_http, daemon=True)
    http_thread.start()
    print(f"Viewer:  http://localhost:{HTTP_PORT}/")
    print(f"WS:      ws://localhost:{WS_PORT}/")
    asyncio.run(_run_ws())


if __name__ == "__main__":
    run()
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_viewer_server.py -v
```

Expected: all 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add mcp_server/viewer_server.py tests/test_viewer_server.py
git commit -m "feat(viewer): HTTP+WebSocket server with REST command API"
```

---

### Task 6: Add MCP viewer tools to server.py

**Files:**
- Modify: `mcp_server/server.py`
- Modify: `tests/test_mcp.py`

MCP tools POST JSON to viewer server via `urllib.request` (stdlib).

- [ ] **Step 1: Write failing tests**

Add to `tests/test_mcp.py` (after existing imports/fixtures):

```python
import json
import threading
import time
import urllib.request
import urllib.error


@pytest.fixture(scope="module", autouse=True)
def viewer_server_for_mcp():
    from mcp_server import viewer_server as vs
    t = threading.Thread(target=vs.run, daemon=True)
    t.start()
    time.sleep(0.6)
    yield


def test_tool_viewer_load_algorithm():
    from mcp_server.server import tool_viewer_load_algorithm
    result = tool_viewer_load_algorithm("CO9")
    assert result["ok"] is True


def test_tool_viewer_load_algorithm_unknown_raises():
    from mcp_server.server import tool_viewer_load_algorithm
    with pytest.raises(ValueError, match="Unknown algorithm"):
        tool_viewer_load_algorithm("DOES_NOT_EXIST")


def test_tool_viewer_animate_sequence():
    from mcp_server.server import tool_viewer_animate_sequence
    result = tool_viewer_animate_sequence("FR U++ FR- U-")
    assert result["ok"] is True


def test_tool_viewer_step_forward():
    from mcp_server.server import tool_viewer_load_algorithm, tool_viewer_step_forward
    tool_viewer_load_algorithm("CO9")
    result = tool_viewer_step_forward()
    assert result["ok"] is True


def test_tool_viewer_reset():
    from mcp_server.server import tool_viewer_reset
    result = tool_viewer_reset()
    assert result["ok"] is True


def test_tool_viewer_show_state_returns_string():
    from mcp_server.server import tool_viewer_show_state
    result = tool_viewer_show_state()
    assert isinstance(result, str)
    assert "Move:" in result
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_mcp.py::test_tool_viewer_load_algorithm -v
```

Expected: FAIL with `ImportError`.

- [ ] **Step 3: Add viewer tools to server.py**

Add after the existing `SESSION = SessionState()` line:

```python
import json as _json
import urllib.request as _urlreq
import urllib.error as _urlerr

_VIEWER_API = "http://localhost:8766/api/command"


def _viewer_post(cmd: dict) -> dict:
    body = _json.dumps(cmd).encode()
    req = _urlreq.Request(
        _VIEWER_API,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        resp = _urlreq.urlopen(req, timeout=3.0)
        return _json.loads(resp.read())
    except _urlerr.HTTPError as exc:
        err = _json.loads(exc.read()).get("error", str(exc))
        raise ValueError(err) from exc
    except OSError as exc:
        raise RuntimeError(
            "Viewer server not running. Start with: python -m mcp_server.viewer_server"
        ) from exc


def tool_viewer_load_algorithm(name: str) -> dict:
    """Load a named algorithm into the viewer and reset to move 0."""
    return _viewer_post({"type": "load_algorithm", "name": name})


def tool_viewer_animate_sequence(sequence: str) -> dict:
    """Load a custom move sequence (space-separated project notation) into the viewer."""
    return _viewer_post({"type": "animate_sequence", "sequence": sequence})


def tool_viewer_step_forward() -> dict:
    """Advance the viewer by one move."""
    return _viewer_post({"type": "step_forward"})


def tool_viewer_step_backward() -> dict:
    """Reverse the viewer by one move."""
    return _viewer_post({"type": "step_backward"})


def tool_viewer_goto_move(n: int) -> dict:
    """Jump the viewer to move index n (0 = start)."""
    return _viewer_post({"type": "goto_move", "n": n})


def tool_viewer_reset() -> dict:
    """Reset the viewer to solved state."""
    return _viewer_post({"type": "reset"})


def tool_viewer_show_state() -> str:
    """Return a text description of the current viewer state."""
    from mcp_server.viewer_server import VIEWER_STATE
    snap = VIEWER_STATE.state_snapshot()
    return (
        f"Algorithm: {snap['algName'] or '(custom)'}\n"
        f"Move: {snap['moveIndex']} / {snap['totalMoves']}\n"
        f"Current move: {snap['currentMove'] or '-'}"
    )
```

Add these tool registrations after the existing `mcp.tool()` block:

```python
mcp.tool()(tool_viewer_load_algorithm)
mcp.tool()(tool_viewer_animate_sequence)
mcp.tool()(tool_viewer_step_forward)
mcp.tool()(tool_viewer_step_backward)
mcp.tool()(tool_viewer_goto_move)
mcp.tool()(tool_viewer_reset)
mcp.tool()(tool_viewer_show_state)
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_mcp.py -v
```

Expected: all viewer tool tests PASS.

- [ ] **Step 5: Commit**

```bash
git add mcp_server/server.py tests/test_mcp.py
git commit -m "feat(mcp): add 7 viewer tools (load_algorithm, animate_sequence, step, reset)"
```

---

### Task 7: viewer/index.html + viewer/js/ modules

**Files:**
- Create: `viewer/index.html`
- Create: `viewer/js/scene.js`
- Create: `viewer/js/megaminx.js`
- Create: `viewer/js/svg.js`
- Create: `viewer/js/controls.js`
- Create: `viewer/js/library.js`
- Create: `viewer/js/main.js`

No automated tests — verified manually in browser.

- [ ] **Step 1: Create viewer/index.html**

```html
<!DOCTYPE html>
<html lang="no">
<head>
  <meta charset="UTF-8">
  <title>Megaminx Viewer</title>
  <script type="importmap">
  {
    "imports": {
      "three": "https://cdn.jsdelivr.net/npm/three@0.169.0/build/three.module.js",
      "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.169.0/examples/jsm/"
    }
  }
  </script>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    html, body { height: 100%; background: #0d1117; color: #e6edf3;
                 font-family: system-ui, sans-serif; overflow: hidden; }
    #app { display: flex; height: 100vh; }

    /* Left: 3D + controls */
    #left-pane { display: flex; flex-direction: column; flex: 1 1 65%; min-width: 0; }
    #canvas-container { flex: 1; position: relative; overflow: hidden; }
    #canvas-container canvas { display: block; width: 100% !important; height: 100% !important; }

    #controls-bar {
      flex: 0 0 auto; background: #161b22; border-top: 1px solid #30363d;
      padding: 8px 16px; display: flex; align-items: center; gap: 10px;
    }

    /* Right: SVG + library + freetext */
    #right-pane {
      flex: 0 0 260px; display: flex; flex-direction: column;
      border-left: 1px solid #30363d; background: #161b22; overflow: hidden;
    }
    #svg-panel {
      flex: 0 0 auto; padding: 10px; border-bottom: 1px solid #30363d;
      display: flex; align-items: center; justify-content: center; background: #0d1117;
    }
    #library-panel { flex: 1 1 0; overflow-y: auto; padding: 10px; }
    #library-panel h3 {
      font-size: 10px; text-transform: uppercase; letter-spacing: 1px;
      color: #8b949e; margin-bottom: 6px;
    }
    .alg-item {
      padding: 5px 8px; border-radius: 4px; cursor: pointer;
      font-size: 12px; color: #8b949e; user-select: none;
    }
    .alg-item:hover { background: #21262d; color: #e6edf3; }
    .alg-item.active { background: #1f3a5f; color: #58a6ff; }

    #freetext-panel { flex: 0 0 auto; padding: 10px; border-top: 1px solid #30363d; }
    #freetext-panel h3 {
      font-size: 10px; text-transform: uppercase; letter-spacing: 1px;
      color: #8b949e; margin-bottom: 6px;
    }
    #seq-input {
      width: 100%; background: #0d1117; border: 1px solid #30363d;
      border-radius: 4px; color: #58a6ff; font-family: monospace;
      font-size: 11px; padding: 5px 8px; resize: none;
    }
    #seq-input:focus { outline: none; border-color: #58a6ff; }
    #seq-submit {
      margin-top: 6px; width: 100%; background: #1f3a5f;
      border: 1px solid #58a6ff; border-radius: 4px;
      color: #58a6ff; font-size: 12px; padding: 5px 0; cursor: pointer;
    }
    #seq-submit:hover { background: #243f6a; }

    /* Controls */
    .ctrl-btn {
      background: #21262d; border: 1px solid #30363d; border-radius: 4px;
      color: #8b949e; font-size: 14px; padding: 4px 10px; cursor: pointer; line-height: 1;
    }
    .ctrl-btn:hover { color: #e6edf3; border-color: #58a6ff; }
    .ctrl-btn.play-btn { background: #1f3a5f; border-color: #58a6ff; color: #58a6ff; }

    #progress-wrap { flex: 1; display: flex; flex-direction: column; gap: 3px; }
    #progress-bar-bg { height: 4px; background: #30363d; border-radius: 2px; overflow: hidden; }
    #progress-bar-fill { height: 4px; background: #58a6ff; border-radius: 2px; width: 0%; }
    #progress-label { font-size: 10px; color: #8b949e; font-family: monospace; }
    #status-label {
      font-size: 11px; color: #58a6ff; font-family: monospace;
      white-space: nowrap; max-width: 180px; overflow: hidden; text-overflow: ellipsis;
    }
    #speed-label { font-size: 11px; color: #8b949e; white-space: nowrap; }
    #speed-slider { width: 70px; accent-color: #58a6ff; }
  </style>
</head>
<body>
<div id="app">
  <div id="left-pane">
    <div id="canvas-container"></div>
    <div id="controls-bar">
      <button class="ctrl-btn"      id="btn-first">⏮</button>
      <button class="ctrl-btn"      id="btn-back">◀</button>
      <button class="ctrl-btn play-btn" id="btn-play">▶</button>
      <button class="ctrl-btn"      id="btn-fwd">▶▶</button>
      <button class="ctrl-btn"      id="btn-last">⏭</button>
      <div id="progress-wrap">
        <div id="progress-bar-bg"><div id="progress-bar-fill"></div></div>
        <div id="progress-label">– / –</div>
      </div>
      <div id="status-label">–</div>
      <span id="speed-label">1.0×</span>
      <input id="speed-slider" type="range" min="3" max="30" value="10" step="1">
    </div>
  </div>
  <div id="right-pane">
    <div id="svg-panel">
      <svg id="topdown-svg" viewBox="-120 -120 240 200" width="220" height="180"></svg>
    </div>
    <div id="library-panel">
      <h3>Algoritmer</h3>
      <div id="alg-list"></div>
    </div>
    <div id="freetext-panel">
      <h3>Egendefinert</h3>
      <textarea id="seq-input" rows="2" placeholder="FR U++ FR- U-…"></textarea>
      <button id="seq-submit">▶ Animer</button>
    </div>
  </div>
</div>
<script type="module" src="js/main.js"></script>
</body>
</html>
```

- [ ] **Step 2: Create viewer/js/scene.js**

```js
// viewer/js/scene.js
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

export function createScene(container) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0d1117);

  const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 100);
  camera.position.set(0, 1.5, 5);

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.setPixelRatio(window.devicePixelRatio);
  container.appendChild(renderer.domElement);

  scene.add(new THREE.AmbientLight(0xffffff, 0.6));
  const dir = new THREE.DirectionalLight(0xffffff, 0.8);
  dir.position.set(5, 10, 7);
  scene.add(dir);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;

  (function loop() {
    requestAnimationFrame(loop);
    controls.update();
    renderer.render(scene, camera);
  })();

  window.addEventListener('resize', () => {
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
  });

  return { scene, camera, renderer, controls };
}
```

- [ ] **Step 3: Create viewer/js/megaminx.js**

```js
// viewer/js/megaminx.js
import * as THREE from 'three';

const STICKER_LIFT = 0.006;
const INNER_S = 0.42;
const MID_S   = 0.72;

/**
 * Build all Megaminx geometry. Returns { group, updateColors }.
 * updateColors(state) re-colors stickers from a WS state snapshot.
 */
export function buildMegaminx(geometry) {
  const group = new THREE.Group();
  // Per-face sticker mesh references
  const faceStickerMeshes = [];  // [fi] = { center, edges[5], corners[5] }

  for (let fi = 0; fi < 12; fi++) {
    const rawVerts = geometry.faceVertices[fi];
    const centerV  = new THREE.Vector3(...geometry.faceCenters[fi]);
    const normal   = centerV.clone().normalize();
    const verts    = rawVerts.map(v => new THREE.Vector3(...v));

    // Black face backing
    group.add(_buildFan(verts.map(v => centerV.clone().lerp(v, 0.97)), normal, 0x111111, 0));

    const innerV = verts.map(v => centerV.clone().lerp(v, INNER_S));
    const midV   = verts.map(v => centerV.clone().lerp(v, MID_S));

    // Center sticker (pentagon)
    const cMesh = _buildFan(innerV, normal, geometry.faceColors[geometry.faceNames[fi]], STICKER_LIFT);
    group.add(cMesh);

    const eMeshes = [];
    const coMeshes = [];

    for (let k = 0; k < 5; k++) {
      const k1 = (k + 1) % 5;
      const km = (k - 1 + 5) % 5;

      // Edge sticker (trapezoid)
      const eM = _buildQuad([midV[k], midV[k1], innerV[k1], innerV[k]], normal, 0x888888, STICKER_LIFT);
      group.add(eM);
      eMeshes.push(eM);

      // Corner sticker (pentagon)
      const halfNext = verts[k].clone().lerp(verts[k1], 0.5);
      const halfPrev = verts[k].clone().lerp(verts[km], 0.5);
      const coM = _buildFan([verts[k], halfNext, midV[k1], midV[k], halfPrev], normal, 0x888888, STICKER_LIFT);
      group.add(coM);
      coMeshes.push(coM);
    }

    faceStickerMeshes.push({ center: cMesh, edges: eMeshes, corners: coMeshes });
  }

  function updateColors(state) {
    const { corners, edges } = state;
    for (let fi = 0; fi < 12; fi++) {
      const { edges: eMeshes, corners: coMeshes } = faceStickerMeshes[fi];
      const cc = geometry.faceCornerCycles[fi];
      const ec = geometry.faceEdgeCycles[fi];

      for (let k = 0; k < 5; k++) {
        // Edge sticker
        const eslot  = ec[k];
        const epiece = edges[eslot][0];
        const eori   = edges[eslot][1];
        const eFaces = geometry.edgeFaces[eslot];
        const ki_e   = eFaces.indexOf(fi);
        const eColor = geometry.faceColors[geometry.faceNames[geometry.edgeFaces[epiece][(ki_e + eori) % 2]]];
        eMeshes[k].material.color.set(eColor);

        // Corner sticker
        const cslot  = cc[k];
        const cpiece = corners[cslot][0];
        const cori   = corners[cslot][1];
        const cFaces = geometry.cornerFaces[cslot];
        const ki_c   = cFaces.indexOf(fi);
        const cColor = geometry.faceColors[geometry.faceNames[geometry.cornerFaces[cpiece][(ki_c - cori + 3) % 3]]];
        coMeshes[k].material.color.set(cColor);
      }
    }
  }

  return { group, updateColors };
}

// ── Mesh helpers ──────────────────────────────────────────────────────────────

function _buildFan(verts, normal, color, lift) {
  const pos = [];
  for (let i = 1; i < verts.length - 1; i++) {
    pos.push(...verts[0].toArray(), ...verts[i].toArray(), ...verts[i + 1].toArray());
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.computeVertexNormals();
  const mat = new THREE.MeshLambertMaterial({ color, side: THREE.FrontSide });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.position.addScaledVector(normal, lift);
  return mesh;
}

function _buildQuad(v4, normal, color, lift) {
  const pos = [
    ...v4[0].toArray(), ...v4[1].toArray(), ...v4[2].toArray(),
    ...v4[0].toArray(), ...v4[2].toArray(), ...v4[3].toArray(),
  ];
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.computeVertexNormals();
  const mat = new THREE.MeshLambertMaterial({ color });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.position.addScaledVector(normal, lift);
  return mesh;
}
```

- [ ] **Step 4: Create viewer/js/svg.js**

The SVG renderer builds DOM elements via `createElementNS` to avoid string injection patterns.

```js
// viewer/js/svg.js
const SVG_NS = 'http://www.w3.org/2000/svg';

/**
 * Update the top-down SVG element in place.
 * Shows U face + 5 neighboring face centers around it.
 */
export function updateTopdownSvg(svgEl, state, geometry) {
  // Clear existing children safely via DOM API
  while (svgEl.firstChild) {
    svgEl.removeChild(svgEl.lastChild);
  }

  const faceNames  = geometry.faceNames;
  const faceColors = geometry.faceColors;
  const R = 55;   // U pentagon radius
  const D = 88;   // neighbor distance

  // Find the 5 upper-ring neighbor face indices from U's corner cycles
  const neighborSet = new Set();
  for (const slot of geometry.faceCornerCycles[0]) {
    for (const f of geometry.cornerFaces[slot]) {
      if (f !== 0 && f < 6) neighborSet.add(f);
    }
  }
  const neighbors = [...neighborSet].slice(0, 5);

  function addPolygon(points, fill, stroke = '#222', strokeWidth = '1') {
    const el = document.createElementNS(SVG_NS, 'polygon');
    el.setAttribute('points', points.map(p => p.map(x => x.toFixed(2)).join(',')).join(' '));
    el.setAttribute('fill', fill);
    el.setAttribute('stroke', stroke);
    el.setAttribute('stroke-width', strokeWidth);
    svgEl.appendChild(el);
  }

  function pentagonPoints(cx, cy, r, rotDeg = 0) {
    return Array.from({ length: 5 }, (_, i) => {
      const a = (i * 72 - 90 + rotDeg) * Math.PI / 180;
      return [cx + r * Math.cos(a), cy + r * Math.sin(a)];
    });
  }

  // U face (large pentagon)
  addPolygon(pentagonPoints(0, 0, R), faceColors['U']);
  // U center sticker (inner pentagon)
  addPolygon(pentagonPoints(0, 0, R * INNER_SCALE()), _getCenterColor(0, state, geometry), 'none', '0');

  // 5 neighbors
  for (let k = 0; k < 5; k++) {
    const angle = (k * 72 - 90) * Math.PI / 180;
    const nx = D * Math.cos(angle);
    const ny = D * Math.sin(angle);
    const fi = neighbors[k] ?? (k + 1);
    addPolygon(pentagonPoints(nx, ny, R * 0.65, k * 72), faceColors[faceNames[fi]]);
  }
}

function INNER_SCALE() { return 0.42; }

function _getCenterColor(fi, _state, geometry) {
  // Center pieces never move — always show home face color
  return geometry.faceColors[geometry.faceNames[fi]];
}
```

- [ ] **Step 5: Create viewer/js/controls.js**

```js
// viewer/js/controls.js

export function initControls({ onFirst, onBack, onPlay, onFwd, onLast, onSpeedChange }) {
  document.getElementById('btn-first').addEventListener('click', onFirst);
  document.getElementById('btn-back').addEventListener('click', onBack);
  document.getElementById('btn-play').addEventListener('click', onPlay);
  document.getElementById('btn-fwd').addEventListener('click', onFwd);
  document.getElementById('btn-last').addEventListener('click', onLast);

  const slider = document.getElementById('speed-slider');
  const speedLbl = document.getElementById('speed-label');
  slider.addEventListener('input', () => {
    const val = (slider.value / 10).toFixed(1);
    speedLbl.textContent = `${val}×`;
    onSpeedChange(parseFloat(val));
  });

  return {
    setPlaying(playing) {
      document.getElementById('btn-play').textContent = playing ? '⏸' : '▶';
    },
    updateProgress(moveIndex, totalMoves, currentMove, algName) {
      const pct = totalMoves > 0 ? (moveIndex / totalMoves) * 100 : 0;
      document.getElementById('progress-bar-fill').style.width = `${pct}%`;
      document.getElementById('progress-label').textContent = `${moveIndex} / ${totalMoves}`;
      const parts = [algName, currentMove].filter(Boolean);
      document.getElementById('status-label').textContent = parts.join('  ') || '–';
    },
  };
}
```

- [ ] **Step 6: Create viewer/js/library.js**

```js
// viewer/js/library.js

export function initLibrary({ onLoadAlg, onAnimateSeq }) {
  fetch('/api/command', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ type: 'get_library' }),
  })
    .then(r => r.json())
    .then(data => {
      if (!data.library) return;
      const list = document.getElementById('alg-list');
      for (const { name } of data.library) {
        const el = document.createElement('div');
        el.className = 'alg-item';
        el.textContent = name;
        el.dataset.name = name;
        el.addEventListener('click', () => {
          document.querySelectorAll('.alg-item').forEach(e => e.classList.remove('active'));
          el.classList.add('active');
          onLoadAlg(name);
        });
        list.appendChild(el);
      }
    });

  document.getElementById('seq-submit').addEventListener('click', () => {
    const seq = document.getElementById('seq-input').value.trim();
    if (!seq) return;
    document.querySelectorAll('.alg-item').forEach(e => e.classList.remove('active'));
    onAnimateSeq(seq);
  });

  document.getElementById('seq-input').addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      document.getElementById('seq-submit').click();
    }
  });
}
```

- [ ] **Step 7: Create viewer/js/main.js**

```js
// viewer/js/main.js
import { createScene }      from './scene.js';
import { buildMegaminx }    from './megaminx.js';
import { updateTopdownSvg } from './svg.js';
import { initControls }     from './controls.js';
import { initLibrary }      from './library.js';

const WS_URL = 'ws://localhost:8765';

async function main() {
  const geometry = await (await fetch('/geometry.json')).json();

  const container = document.getElementById('canvas-container');
  const { scene }             = createScene(container);
  const { group, updateColors } = buildMegaminx(geometry);
  scene.add(group);

  let lastState = null;
  let isPlaying = false;
  let speed     = 1.0;
  let playTimer = null;

  function sendCmd(cmd) {
    fetch('/api/command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cmd),
    }).catch(console.error);
  }

  function stopPlay() {
    isPlaying = false;
    ctrlApi.setPlaying(false);
    if (playTimer) { clearTimeout(playTimer); playTimer = null; }
  }

  function scheduleNext() {
    playTimer = setTimeout(() => sendCmd({ type: 'step_forward' }), Math.max(120, 800 / speed));
  }

  const ctrlApi = initControls({
    onFirst:       () => sendCmd({ type: 'goto_move', n: 0 }),
    onBack:        () => { stopPlay(); sendCmd({ type: 'step_backward' }); },
    onPlay() {
      if (!lastState || lastState.totalMoves === 0) return;
      if (isPlaying) { stopPlay(); return; }
      if (lastState.moveIndex >= lastState.totalMoves) {
        sendCmd({ type: 'goto_move', n: 0 });
      }
      isPlaying = true;
      ctrlApi.setPlaying(true);
      scheduleNext();
    },
    onFwd:         () => { stopPlay(); sendCmd({ type: 'step_forward' }); },
    onLast:        () => lastState && sendCmd({ type: 'goto_move', n: lastState.totalMoves }),
    onSpeedChange: v => { speed = v; },
  });

  initLibrary({
    onLoadAlg:    name => { stopPlay(); sendCmd({ type: 'load_algorithm', name }); },
    onAnimateSeq: seq  => { stopPlay(); sendCmd({ type: 'animate_sequence', sequence: seq }); },
  });

  function onMessage(msg) {
    if (msg.type === 'state') {
      lastState = msg;
      updateColors(msg);
      const svgEl = document.getElementById('topdown-svg');
      if (svgEl) updateTopdownSvg(svgEl, msg, geometry);
      ctrlApi.updateProgress(msg.moveIndex, msg.totalMoves, msg.currentMove, msg.algName);
      if (isPlaying) {
        if (msg.moveIndex >= msg.totalMoves) stopPlay();
        else scheduleNext();
      }
    } else if (msg.type === 'loaded') {
      stopPlay();
      ctrlApi.updateProgress(0, msg.moves.length, null, msg.algName);
    } else if (msg.type === 'reset') {
      stopPlay();
      ctrlApi.updateProgress(0, 0, null, null);
    }
  }

  function connect() {
    const ws = new WebSocket(WS_URL);
    ws.onopen    = () => console.log('Megaminx viewer connected');
    ws.onclose   = () => setTimeout(connect, 2000);
    ws.onerror   = e  => console.error('WS error', e);
    ws.onmessage = e  => onMessage(JSON.parse(e.data));
  }
  connect();
}

main().catch(console.error);
```

- [ ] **Step 8: Start viewer server and verify in browser**

```bash
cd /home/bjafl/source/rubiks
source .venv/bin/activate
python -m mcp_server.viewer_server
```

Open `http://localhost:8766/` and verify:

1. Dark layout renders — left 3D pane + right panel
2. Browser console shows `Megaminx viewer connected`
3. Solved Megaminx visible (12 distinct colored face regions)
4. Algorithm list populated: CO9, CO10, Sune, Anti-Sune, Niklas, Niklas_Inv, EP1, EP2
5. Click **CO9** → progress shows `0 / 11`
6. Click ▶ (play) → cube steps through CO9 automatically
7. ◀ / ▶▶ → step backward/forward one move
8. ⏮ / ⏭ → jump to start/end
9. Speed slider changes playback speed (3-30 range, 1× default)
10. Top-down SVG panel updates on each state change
11. Type `FR U++ FR- U-` in freetext + Enter → viewer loads sequence `0 / 4`

If sticker colors on solved cube don't match face colors, the orientation formula in `megaminx.js` needs sign adjustment. Verify: reset → all face regions should match `geometry.faceColors`.

- [ ] **Step 9: Commit**

```bash
git add viewer/index.html viewer/js/
git commit -m "feat(viewer): Three.js client — scene, megaminx geometry, SVG, controls, library"
```

---

### Task 8: Final integration test + full test suite

**Files:**
- Run: all tests
- Verify: MCP tools → viewer → browser integration

- [ ] **Step 1: Run full test suite**

```bash
cd /home/bjafl/source/rubiks
source .venv/bin/activate
pytest tests/ -v --tb=short
```

Expected: all tests PASS. Should include 14 new `test_viewer_state` + 8 `test_gen_geometry` tests on top of the 146 existing tests.

- [ ] **Step 2: End-to-end MCP smoke test**

With `python -m mcp_server.viewer_server` running in another terminal:

```bash
python -c "
from mcp_server.server import (
    tool_viewer_reset,
    tool_viewer_load_algorithm,
    tool_viewer_step_forward,
    tool_viewer_goto_move,
    tool_viewer_show_state,
)
tool_viewer_reset()
tool_viewer_load_algorithm('CO9')
tool_viewer_step_forward()
tool_viewer_step_forward()
print(tool_viewer_show_state())
tool_viewer_goto_move(0)
print(tool_viewer_show_state())
print('All MCP viewer tools OK')
"
```

Expected output:
```
Algorithm: CO9
Move: 2 / 11
Current move: U++
Algorithm: CO9
Move: 0 / 11
Current move: -
All MCP viewer tools OK
```

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "test: full suite pass + MCP viewer integration verified"
```

---

## Running the viewer

```bash
# Start viewer server (keep running)
cd /home/bjafl/source/rubiks
source .venv/bin/activate
python -m mcp_server.viewer_server
# → HTTP:  http://localhost:8766/
# → WS:    ws://localhost:8765/

# In Claude Code (separate session), configure MCP:
# fastmcp run mcp_server/server.py
# Then Claude can call: tool_viewer_load_algorithm, tool_viewer_animate_sequence, etc.
```
