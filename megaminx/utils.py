# megaminx/utils.py
from __future__ import annotations
import random
from megaminx.cube import MegaminxState, SOLVED, apply_move
from megaminx.moves import ALL_MOVES


def scramble(state: MegaminxState, n: int) -> MegaminxState:
    from megaminx.moves import parse_move
    last_fi: int | None = None
    for _ in range(n):
        candidates = [m for m in ALL_MOVES if parse_move(m)[0] != last_fi]
        move = random.choice(candidates)
        state = apply_move(state, move)
        last_fi = parse_move(move)[0]
    return state


def state_to_dict(state: MegaminxState) -> dict:
    return {
        "corners": [{"pos": state.cp[i], "ori": state.co[i]} for i in range(20)],
        "edges":   [{"pos": state.ep[i], "ori": state.eo[i]} for i in range(30)],
    }


def dict_to_state(d: dict, validate: bool = True) -> MegaminxState | dict:
    cp = tuple(c["pos"] for c in d["corners"])
    co = tuple(c["ori"] for c in d["corners"])
    ep = tuple(e["pos"] for e in d["edges"])
    eo = tuple(e["ori"] for e in d["edges"])
    state = MegaminxState(cp, co, ep, eo)
    if validate:
        from megaminx.model import validate_state
        r = validate_state(state)
        if not r.valid:
            return {"valid": False, "errors": r.errors}
    return state


def describe_state(state: MegaminxState) -> str:
    if state == SOLVED:
        return "State: SOLVED"
    misplaced_c = sum(1 for i in range(20) if state.cp[i] != i or state.co[i] != 0)
    misplaced_e = sum(1 for i in range(30) if state.ep[i] != i or state.eo[i] != 0)
    twisted_c   = sum(1 for i in range(20) if state.co[i] != 0)
    flipped_e   = sum(1 for i in range(30) if state.eo[i] != 0)
    return (
        f"State: UNSOLVED — "
        f"{misplaced_c}/20 corners misplaced ({twisted_c} twisted), "
        f"{misplaced_e}/30 edges misplaced ({flipped_e} flipped)"
    )
