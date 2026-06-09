from __future__ import annotations
from collections import deque
from megaminx.model import MegaminxState, SOLVED_STATE


class SessionState:
    """Manages Megaminx puzzle state with undo history.

    Stores current state and maintains a bounded history stack for undo operations.
    """

    def __init__(self, max_history: int = 20) -> None:
        """Initialize session with solved state.

        Args:
            max_history: Maximum number of states to keep in undo stack (default 20)
        """
        self._state = SOLVED_STATE.copy()
        self._history: deque[MegaminxState] = deque(maxlen=max_history)

    @property
    def state(self) -> MegaminxState:
        """Get current puzzle state."""
        return self._state

    def push(self, new_state: MegaminxState) -> None:
        """Push new state onto stack, saving current state to history.

        Args:
            new_state: New MegaminxState to set as current
        """
        self._history.append(self._state.copy())
        self._state = new_state

    def undo(self, steps: int = 1) -> None:
        """Undo last n state changes by popping from history.

        No-op if history is empty. Only undoes available steps.

        Args:
            steps: Number of undo steps (default 1)
        """
        for _ in range(steps):
            if self._history:
                self._state = self._history.pop()

    def reset(self) -> None:
        """Reset to solved state and clear history."""
        self._state = SOLVED_STATE.copy()
        self._history.clear()
