# mcp_server/server.py
from __future__ import annotations
import numpy as np
from fastmcp import FastMCP
from megaminx.model import SOLVED_STATE, validate_state, is_solved
from megaminx.moves import apply_move, apply_sequence, FACE_NAMES, MOVE_TABLE, CORNER_FACES, EDGE_FACES
from megaminx.algorithms import list_algorithms, get_single_alg
from megaminx.solver import solve_path as _solve_path
from megaminx.utils import scramble, state_to_dict, dict_to_state, describe_state
from mcp_server.session import SessionState

SESSION = SessionState()
mcp = FastMCP("megaminx")


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
    fi = FACE_NAMES.index(face)
    t = MOVE_TABLE[fi]
    corner_slots = t["corner_cycle"]
    edge_slots = t["edge_cycle"]
    return {
        "face": face,
        "corners": [
            {"slot": ci, "piece": int(SESSION.state.corners[ci, 0]),
             "orientation": int(SESSION.state.corners[ci, 1])}
            for ci in corner_slots
        ],
        "edges": [
            {"slot": ei, "piece": int(SESSION.state.edges[ei, 0]),
             "orientation": int(SESSION.state.edges[ei, 1])}
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
    new_state = scramble(SESSION.state.copy(), n)
    SESSION.push(new_state)
    return tool_get_state()


def tool_set_state(state_dict: dict) -> dict:
    result = dict_to_state(state_dict, validate=True)
    if isinstance(result, dict):
        return {"valid": False, "errors": result["errors"]}
    SESSION.push(result)
    return {"valid": True, "errors": []}


def tool_set_layer_solved(layer: str) -> dict:
    """Set all pieces in a named layer (U_CAP or D_CAP) to their solved positions."""
    LAYER_CORNERS = {
        "U_CAP": [i for i, cf in enumerate(CORNER_FACES) if 0 in cf],
        "D_CAP": [i for i, cf in enumerate(CORNER_FACES) if 11 in cf],
    }
    LAYER_EDGES = {
        "U_CAP": [i for i, ef in enumerate(EDGE_FACES) if 0 in ef],
        "D_CAP": [i for i, ef in enumerate(EDGE_FACES) if 11 in ef],
    }
    if layer not in LAYER_CORNERS:
        raise ValueError(f"Unknown layer {layer!r}. Valid: {list(LAYER_CORNERS)}")
    new_state = SESSION.state.copy()
    for ci in LAYER_CORNERS[layer]:
        new_state.corners[ci] = SOLVED_STATE.corners[ci]
    for ei in LAYER_EDGES[layer]:
        new_state.edges[ei] = SOLVED_STATE.edges[ei]
    r = validate_state(new_state)
    if not r.valid:
        return {"valid": False, "errors": r.errors}
    SESSION.push(new_state)
    return {"valid": True, "errors": []}


def tool_scramble_substate(region: str) -> dict:
    """Scramble only the U or D cap pieces, keeping the rest unchanged."""
    import random
    LAYER_CORNERS = {
        "U_CAP": [i for i, cf in enumerate(CORNER_FACES) if 0 in cf],
        "D_CAP": [i for i, cf in enumerate(CORNER_FACES) if 11 in cf],
    }
    LAYER_EDGES = {
        "U_CAP": [i for i, ef in enumerate(EDGE_FACES) if 0 in ef],
        "D_CAP": [i for i, ef in enumerate(EDGE_FACES) if 11 in ef],
    }
    if region not in LAYER_CORNERS:
        raise ValueError(f"Unknown region {region!r}. Valid: {list(LAYER_CORNERS)}")
    face_move = "U" if region == "U_CAP" else "D"
    region_moves = [face_move, f"{face_move}-"]
    new_state = SESSION.state.copy()
    for ci in LAYER_CORNERS[region]:
        new_state.corners[ci] = SOLVED_STATE.corners[ci]
    for ei in LAYER_EDGES[region]:
        new_state.edges[ei] = SOLVED_STATE.edges[ei]
    for _ in range(10):
        m = random.choice(region_moves)
        new_state = apply_move(new_state, m)
    SESSION.push(new_state)
    return tool_get_state()


def tool_solve_path(
    to_state_dict: dict | None = None,
    move_set: list[str] | None = None,
    max_depth: int = 10,
) -> list[str] | None:
    to_state = SOLVED_STATE.copy() if not to_state_dict else dict_to_state(to_state_dict)
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

if __name__ == "__main__":
    mcp.run()
