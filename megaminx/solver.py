# megaminx/solver.py
from __future__ import annotations
import numpy as np
from megaminx.model import MegaminxState
from megaminx.moves import apply_move, ALL_MOVES

_MAX_SEARCH_NODES = 500_000


def _diff_heuristic(state: MegaminxState, goal: MegaminxState) -> int:
    """Count misplaced corners/edges vs goal state, divided by 10."""
    misplaced = int(np.sum(state.corners != goal.corners)) + \
                int(np.sum(state.edges != goal.edges))
    return misplaced // 10


def solve_path(
    from_state: MegaminxState,
    to_state: MegaminxState,
    move_set: list[str] | None = None,
    max_depth: int = 12,
) -> list[str] | None:
    """
    IDA* search from from_state to to_state.
    Returns the move sequence or None if no solution found within max_depth.
    """
    moves = move_set if move_set is not None else ALL_MOVES

    def states_equal(a: MegaminxState, b: MegaminxState) -> bool:
        return np.array_equal(a.corners, b.corners) and np.array_equal(a.edges, b.edges)

    if states_equal(from_state, to_state):
        return []

    h = _diff_heuristic(from_state, to_state)
    if h > max_depth:
        return None

    bound = h
    path: list[str] = []
    node_count = [0]

    # Determine if same-face pruning is applicable (only when >1 distinct face in move_set)
    available_faces = {m.rstrip("+-") for m in moves}
    prune_same_face = len(available_faces) > 1

    def search(state: MegaminxState, g: int, bound: int) -> int | None:
        node_count[0] += 1
        if node_count[0] > _MAX_SEARCH_NODES:
            return -1  # signal: search space exceeded

        f = g + _diff_heuristic(state, to_state)
        if f > bound:
            return f
        if states_equal(state, to_state):
            return None  # found

        minimum = float("inf")
        last_face = path[-1].rstrip("+-") if path else None
        for move in moves:
            face = move.rstrip("+-")
            if prune_same_face and face == last_face:  # skip consecutive same-face moves
                continue
            new_state = apply_move(state, move)
            path.append(move)
            t = search(new_state, g + 1, bound)
            if t is None:
                return None  # found
            if t == -1:
                return -1   # exceeded
            if t < minimum:
                minimum = t
            path.pop()
        return minimum

    while bound <= max_depth:
        node_count[0] = 0
        t = search(from_state, 0, bound)
        if t is None:
            return list(path)
        if t == -1 or t == float("inf"):
            return None
        bound = t

    return None
