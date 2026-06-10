# mcp_server/session.py
from __future__ import annotations
from collections import deque
from megaminx.cube import MegaminxState, SOLVED


class SessionState:
    """Megaminx puzzle state with undo history."""

    def __init__(self, max_history: int = 20) -> None:
        self._state: MegaminxState = SOLVED
        self._history: deque[MegaminxState] = deque(maxlen=max_history)

    @property
    def state(self) -> MegaminxState:
        return self._state

    def push(self, new_state: MegaminxState) -> None:
        self._history.append(self._state)
        self._state = new_state

    def undo(self, steps: int = 1) -> None:
        for _ in range(steps):
            if self._history:
                self._state = self._history.pop()

    def reset(self) -> None:
        self._state = SOLVED
        self._history.clear()
