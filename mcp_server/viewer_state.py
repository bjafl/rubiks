# mcp_server/viewer_state.py
from __future__ import annotations
import json
from dataclasses import dataclass, field
from megaminx.cube import MegaminxState, SOLVED
from megaminx.moves import apply_move, parse_move


def parse_sequence(text: str) -> list[str]:
    moves = text.strip().replace("(", "").replace(")", "").split()
    if not moves:
        raise ValueError("Empty sequence")
    for m in moves:
        parse_move(m)
    return moves


@dataclass
class ViewerState:
    megaminx: MegaminxState = field(default_factory=lambda: SOLVED)
    sequence: list[str] = field(default_factory=list)
    move_index: int = 0
    alg_name: str | None = None
    ws_clients: set = field(default_factory=set, repr=False)

    def state_snapshot(self) -> dict:
        return {
            "type": "state",
            "corners": [[self.megaminx.cp[i], self.megaminx.co[i]] for i in range(20)],
            "edges":   [[self.megaminx.ep[i], self.megaminx.eo[i]] for i in range(30)],
            "moveIndex":   self.move_index,
            "totalMoves":  len(self.sequence),
            "currentMove": self.sequence[self.move_index - 1] if self.move_index > 0 else None,
            "algName":     self.alg_name,
        }

    def load_sequence(self, moves: list[str], alg_name: str | None = None) -> None:
        self.megaminx   = SOLVED
        self.sequence   = list(moves)
        self.move_index = 0
        self.alg_name   = alg_name

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
        self.megaminx = SOLVED
        for m in self.sequence[:self.move_index]:
            self.megaminx = apply_move(self.megaminx, m)
        return True

    def rewind_to(self, n: int) -> None:
        n = max(0, min(n, len(self.sequence)))
        self.megaminx = SOLVED
        for m in self.sequence[:n]:
            self.megaminx = apply_move(self.megaminx, m)
        self.move_index = n

    def reset(self) -> None:
        self.megaminx   = SOLVED
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
