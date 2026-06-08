# megaminx/heuristics.py
# Admissible heuristic: counts misplaced pieces in a subset.
# Uses the first 8 corners and first 10 edges as the pattern subset.
import numpy as np
from megaminx.model import MegaminxState

_CORNER_SUBSET = list(range(20))  # all corners
_EDGE_SUBSET = list(range(30))    # all edges


def lower_bound(state: MegaminxState) -> int:
    """
    Admissible lower bound on the number of moves to solve.
    Counts misplaced pieces in the chosen subset, divided by 10
    (at most 10 pieces can be fixed per move: 5 corners + 5 edges).
    """
    misplaced = 0
    for i in _CORNER_SUBSET:
        if state.corners[i, 0] != i or state.corners[i, 1] != 0:
            misplaced += 1
    for i in _EDGE_SUBSET:
        if state.edges[i, 0] != i or state.edges[i, 1] != 0:
            misplaced += 1
    return misplaced // 10
