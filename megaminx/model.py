# megaminx/model.py
from __future__ import annotations
from dataclasses import dataclass

from megaminx.cube import MegaminxState, SOLVED  # re-export

SOLVED_STATE: MegaminxState = SOLVED


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str]


def _perm_parity(perm: list[int]) -> int:
    n = len(perm)
    visited = [False] * n
    p = 0
    for i in range(n):
        if not visited[i]:
            cycle_len = 0
            j = i
            while not visited[j]:
                visited[j] = True
                j = perm[j]
                cycle_len += 1
            p ^= (cycle_len + 1) % 2
    return p


def validate_state(state: MegaminxState) -> ValidationResult:
    errors: list[str] = []

    c_pos = list(state.cp)
    e_pos = list(state.ep)
    c_ori = list(state.co)
    e_ori = list(state.eo)

    if sorted(c_pos) != list(range(20)):
        errors.append("Corner positions are not a valid permutation of 0-19")
    if sorted(e_pos) != list(range(30)):
        errors.append("Edge positions are not a valid permutation of 0-29")

    if any(o not in (0, 1, 2) for o in c_ori):
        errors.append("Corner orientations must be in {0, 1, 2}")
    if any(o not in (0, 1) for o in e_ori):
        errors.append("Edge orientations must be in {0, 1}")

    if sum(c_ori) % 3 != 0:
        errors.append("Sum of corner orientations must be ≡ 0 (mod 3)")
    if sum(e_ori) % 2 != 0:
        errors.append("Sum of edge orientations must be ≡ 0 (mod 2)")

    if not errors:
        if _perm_parity(c_pos) != _perm_parity(e_pos):
            errors.append("Corner permutation parity must equal edge permutation parity")

    return ValidationResult(valid=len(errors) == 0, errors=errors)


def is_solved(state: MegaminxState) -> bool:
    return state.is_solved
