# megaminx/solver.py
from __future__ import annotations
from megaminx.cube import MegaminxState, SOLVED, apply_move
from megaminx.moves import ALL_MOVES

_MAX_SEARCH_NODES = 500_000


def _heuristic(state: MegaminxState, goal: MegaminxState) -> int:
    misplaced = (
        sum(1 for i in range(20) if state.cp[i] != goal.cp[i] or state.co[i] != goal.co[i]) +
        sum(1 for i in range(30) if state.ep[i] != goal.ep[i] or state.eo[i] != goal.eo[i])
    )
    return misplaced // 10


def solve_path(
    from_state: MegaminxState,
    to_state: MegaminxState,
    move_set: list[str] | None = None,
    max_depth: int = 12,
) -> list[str] | None:
    moves = move_set if move_set is not None else ALL_MOVES
    if from_state == to_state:
        return []

    h = _heuristic(from_state, to_state)
    if h > max_depth:
        return None

    bound = h
    path: list[str] = []
    node_count = [0]
    available_faces = {m.rstrip("'-") for m in moves}
    prune_same_face = len(available_faces) > 1

    def search(state: MegaminxState, g: int, bound: int) -> int | None:
        node_count[0] += 1
        if node_count[0] > _MAX_SEARCH_NODES:
            return -1
        f = g + _heuristic(state, to_state)
        if f > bound:
            return f
        if state == to_state:
            return None
        minimum: float = float("inf")
        last_face = path[-1].rstrip("'-") if path else None
        for move in moves:
            face = move.rstrip("'-")
            if prune_same_face and face == last_face:
                continue
            new_state = apply_move(state, move)
            path.append(move)
            t = search(new_state, g + 1, bound)
            if t is None:
                return None
            if t == -1:
                return -1
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
