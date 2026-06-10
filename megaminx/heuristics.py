# megaminx/heuristics.py
from megaminx.cube import MegaminxState, SOLVED


def lower_bound(state: MegaminxState) -> int:
    """Lower bound: misplaced corners + edges, divided by 10."""
    misplaced = (
        sum(1 for i in range(20) if state.cp[i] != i or state.co[i] != 0) +
        sum(1 for i in range(30) if state.ep[i] != i or state.eo[i] != 0)
    )
    return misplaced // 10
