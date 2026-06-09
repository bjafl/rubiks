# tests/test_solver.py
import pytest
from megaminx.model import SOLVED_STATE, is_solved
from megaminx.moves import apply_move, apply_sequence
from megaminx.solver import solve_path

def test_solve_path_already_solved():
    result = solve_path(SOLVED_STATE.copy(), SOLVED_STATE.copy())
    assert result == []

def test_solve_one_move():
    scrambled = apply_move(SOLVED_STATE.copy(), "U")
    solution = solve_path(scrambled, SOLVED_STATE.copy(), max_depth=5)
    assert solution is not None
    result = apply_sequence(scrambled, solution)
    assert is_solved(result)

def test_solve_two_moves():
    scrambled = apply_sequence(SOLVED_STATE.copy(), ["F", "R"])
    solution = solve_path(scrambled, SOLVED_STATE.copy(), max_depth=5)
    assert solution is not None
    result = apply_sequence(scrambled, solution)
    assert is_solved(result)

def test_solve_three_moves():
    scrambled = apply_sequence(SOLVED_STATE.copy(), ["U", "F", "R-"])
    solution = solve_path(scrambled, SOLVED_STATE.copy(), max_depth=6)
    assert solution is not None
    assert len(solution) <= 6
    result = apply_sequence(scrambled, solution)
    assert is_solved(result)

def test_solve_returns_none_when_too_deep():
    scrambled = apply_sequence(SOLVED_STATE.copy(), ["U", "F", "R", "L", "DL"])
    result = solve_path(scrambled, SOLVED_STATE.copy(), max_depth=2)
    # max_depth=2 is too shallow for a 5-move scramble
    assert result is None

def test_solve_with_restricted_move_set():
    """solve_path with only U moves can solve a U-only scramble."""
    scrambled = apply_sequence(SOLVED_STATE.copy(), ["U", "U", "U"])
    solution = solve_path(scrambled, SOLVED_STATE.copy(), move_set=["U", "U-"], max_depth=5)
    assert solution is not None
    result = apply_sequence(scrambled, solution)
    assert is_solved(result)

def test_solve_path_a_to_b():
    """Find path between two non-solved states."""
    state_a = apply_move(SOLVED_STATE.copy(), "U")
    state_b = apply_move(SOLVED_STATE.copy(), "F")
    solution = solve_path(state_a, state_b, max_depth=6)
    assert solution is not None
    result = apply_sequence(state_a, solution)
    import numpy as np
    assert np.array_equal(result.corners, state_b.corners)
    assert np.array_equal(result.edges, state_b.edges)
