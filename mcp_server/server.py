# mcp_server/server.py
from __future__ import annotations
from fastmcp import FastMCP
from megaminx.cube import FACES, CORNERS, EDGES, MegaminxState, SOLVED, MOVES as CUBE_MOVES
from megaminx.model import SOLVED_STATE, validate_state, is_solved
from megaminx.moves import apply_move, apply_sequence, FACE_NAMES, CORNER_FACES, EDGE_FACES
from megaminx.algorithms import list_algorithms, get_single_alg
from megaminx.solver import solve_path as _solve_path
from megaminx.utils import scramble, state_to_dict, dict_to_state, describe_state
from mcp_server.session import SessionState

SESSION = SessionState()
mcp = FastMCP("megaminx")

_LAYER_CORNERS = {
    "U_CAP": [i for i, c in enumerate(CORNERS) if "U" in c],
    "D_CAP": [i for i, c in enumerate(CORNERS) if "D" in c],
}
_LAYER_EDGES = {
    "U_CAP": [i for i, e in enumerate(EDGES) if "U" in e],
    "D_CAP": [i for i, e in enumerate(EDGES) if "D" in e],
}

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
    snap = _viewer_post({"type": "get_state"})
    return (
        f"Algorithm: {snap['algName'] or '(custom)'}\n"
        f"Move: {snap['moveIndex']} / {snap['totalMoves']}\n"
        f"Current move: {snap['currentMove'] or '-'}"
    )


def tool_get_state() -> dict:
    d = state_to_dict(SESSION.state)
    d["solved"] = bool(is_solved(SESSION.state))
    d["description"] = describe_state(SESSION.state)
    return d


def tool_is_solved() -> bool:
    return bool(is_solved(SESSION.state))


def tool_get_face(face: str) -> dict:
    if face not in FACE_NAMES:
        raise ValueError(f"Unknown face {face!r}. Valid: {FACE_NAMES}")
    m = CUBE_MOVES[face]  # one CW turn
    corner_slots = [i for i in range(20) if m.cp[i] != i]
    edge_slots   = [i for i in range(30) if m.ep[i] != i]
    return {
        "face": face,
        "corners": [
            {"slot": ci, "piece": SESSION.state.cp[ci],
             "orientation": SESSION.state.co[ci]}
            for ci in corner_slots
        ],
        "edges": [
            {"slot": ei, "piece": SESSION.state.ep[ei],
             "orientation": SESSION.state.eo[ei]}
            for ei in edge_slots
        ],
    }


def tool_apply_move(move: str) -> dict:
    new_state = apply_move(SESSION.state, move)  # raises ValueError on bad move
    SESSION.push(new_state)
    return tool_get_state()


def tool_apply_sequence(moves: list[str]) -> dict:
    state = SESSION.state
    for m in moves:
        state = apply_move(state, m)
    SESSION.push(state)
    return tool_get_state()


def tool_scramble(n: int = 30) -> dict:
    new_state = scramble(SESSION.state, n)
    SESSION.push(new_state)
    return tool_get_state()


def tool_set_state(state_dict: dict) -> dict:
    result = dict_to_state(state_dict, validate=True)
    if isinstance(result, dict):
        return {"valid": False, "errors": result["errors"]}
    SESSION.push(result)
    return {"valid": True, "errors": []}


def tool_set_layer_solved(layer: str) -> dict:
    if layer not in _LAYER_CORNERS:
        raise ValueError(f"Unknown layer {layer!r}. Valid: {list(_LAYER_CORNERS)}")
    cp = list(SESSION.state.cp)
    co = list(SESSION.state.co)
    ep = list(SESSION.state.ep)
    eo = list(SESSION.state.eo)
    for ci in _LAYER_CORNERS[layer]:
        cp[ci] = ci
        co[ci] = 0
    for ei in _LAYER_EDGES[layer]:
        ep[ei] = ei
        eo[ei] = 0
    new_state = MegaminxState(tuple(cp), tuple(co), tuple(ep), tuple(eo))
    r = validate_state(new_state)
    if not r.valid:
        return {"valid": False, "errors": r.errors}
    SESSION.push(new_state)
    return {"valid": True, "errors": []}


def tool_scramble_substate(region: str) -> dict:
    import random
    if region not in _LAYER_CORNERS:
        raise ValueError(f"Unknown region {region!r}. Valid: {list(_LAYER_CORNERS)}")
    face_move = "U" if region == "U_CAP" else "D"
    region_moves = [face_move, face_move + "-"]
    cp = list(SESSION.state.cp)
    co = list(SESSION.state.co)
    ep = list(SESSION.state.ep)
    eo = list(SESSION.state.eo)
    for ci in _LAYER_CORNERS[region]:
        cp[ci] = ci; co[ci] = 0
    for ei in _LAYER_EDGES[region]:
        ep[ei] = ei; eo[ei] = 0
    state = MegaminxState(tuple(cp), tuple(co), tuple(ep), tuple(eo))
    for _ in range(10):
        state = apply_move(state, random.choice(region_moves))
    SESSION.push(state)
    return tool_get_state()


def tool_solve_path(
    to_state_dict: dict | None = None,
    move_set: list[str] | None = None,
    max_depth: int = 10,
) -> list[str] | None:
    to_state = SOLVED if not to_state_dict else dict_to_state(to_state_dict)
    if isinstance(to_state, dict):
        raise ValueError(f"Invalid target state: {to_state['errors']}")
    return _solve_path(SESSION.state, to_state, move_set=move_set, max_depth=max_depth)


def tool_apply_named_alg(name: str) -> dict:
    seq = get_single_alg(name)  # KeyError if unknown
    return tool_apply_sequence(seq)


def tool_explain_sequence(moves: list[str]) -> list[dict]:
    steps = []
    state = SESSION.state
    for m in moves:
        before = state_to_dict(state)
        new_state = apply_move(state, m)
        after = state_to_dict(new_state)
        changed_corners = [i for i in range(20) if before["corners"][i] != after["corners"][i]]
        changed_edges = [i for i in range(30) if before["edges"][i] != after["edges"][i]]
        steps.append({
            "move": m,
            "before": before,
            "after": after,
            "changed_corners": changed_corners,
            "changed_edges": changed_edges,
            "description": (
                f"Move {m}: {len(changed_corners)} corners and "
                f"{len(changed_edges)} edges changed."
            ),
        })
        state = new_state
    return steps


def tool_list_algorithms() -> dict:
    return list_algorithms()


def tool_undo(steps: int = 1) -> dict:
    SESSION.undo(steps)
    return tool_get_state()


# Register tools with FastMCP
mcp.tool()(tool_get_state)
mcp.tool()(tool_is_solved)
mcp.tool()(tool_get_face)
mcp.tool()(tool_apply_move)
mcp.tool()(tool_apply_sequence)
mcp.tool()(tool_scramble)
mcp.tool()(tool_set_state)
mcp.tool()(tool_set_layer_solved)
mcp.tool()(tool_scramble_substate)
mcp.tool()(tool_solve_path)
mcp.tool()(tool_apply_named_alg)
mcp.tool()(tool_explain_sequence)
mcp.tool()(tool_list_algorithms)
mcp.tool()(tool_undo)
mcp.tool()(tool_viewer_load_algorithm)
mcp.tool()(tool_viewer_animate_sequence)
mcp.tool()(tool_viewer_step_forward)
mcp.tool()(tool_viewer_step_backward)
mcp.tool()(tool_viewer_goto_move)
mcp.tool()(tool_viewer_reset)
mcp.tool()(tool_viewer_show_state)

if __name__ == "__main__":
    mcp.run()
