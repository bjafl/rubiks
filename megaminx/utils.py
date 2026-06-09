from __future__ import annotations
import random
import numpy as np
from megaminx.model import MegaminxState, validate_state
from megaminx.moves import apply_move, ALL_MOVES


def scramble(state: MegaminxState, n: int) -> MegaminxState:
    """Apply n random moves to state. Returns new state."""
    last_face = None
    for _ in range(n):
        candidates = [m for m in ALL_MOVES if m.rstrip("+-") != last_face]
        move = random.choice(candidates)
        state = apply_move(state, move)
        last_face = move.rstrip("+-")
    return state


def state_to_dict(state: MegaminxState) -> dict:
    """Convert MegaminxState to dictionary representation."""
    return {
        "corners": [{"pos": int(state.corners[i, 0]), "ori": int(state.corners[i, 1])}
                    for i in range(20)],
        "edges":   [{"pos": int(state.edges[i, 0]),   "ori": int(state.edges[i, 1])}
                    for i in range(30)],
    }


def dict_to_state(d: dict, validate: bool = True) -> MegaminxState | dict:
    """Convert dictionary representation to MegaminxState.

    If validate=True and state is invalid, returns dict with valid=False and errors list.
    Otherwise returns MegaminxState.
    """
    corners = np.array([[c["pos"], c["ori"]] for c in d["corners"]], dtype=np.int8)
    edges   = np.array([[e["pos"], e["ori"]] for e in d["edges"]],   dtype=np.int8)
    state = MegaminxState(corners=corners, edges=edges)
    if validate:
        r = validate_state(state)
        if not r.valid:
            return {"valid": False, "errors": r.errors}
    return state


def describe_state(state: MegaminxState) -> str:
    """Return human-readable description of puzzle state."""
    from megaminx.model import is_solved
    if is_solved(state):
        return "State: SOLVED"

    misplaced_corners = sum(
        1 for i in range(20)
        if state.corners[i, 0] != i or state.corners[i, 1] != 0
    )
    misplaced_edges = sum(
        1 for i in range(30)
        if state.edges[i, 0] != i or state.edges[i, 1] != 0
    )
    twisted_corners = sum(1 for i in range(20) if state.corners[i, 1] != 0)
    flipped_edges   = sum(1 for i in range(30) if state.edges[i, 1] != 0)

    return (
        f"State: UNSOLVED — "
        f"{misplaced_corners}/20 corners misplaced ({twisted_corners} twisted), "
        f"{misplaced_edges}/30 edges misplaced ({flipped_edges} flipped)"
    )
