# tests/test_moves.py
import pytest
from megaminx.model import SOLVED_STATE, is_solved
from megaminx.moves import (
    apply_move, apply_sequence, get_geometry_data, FACE_NAMES, ALL_MOVES, parse_move
)
from megaminx.cube import FACES


def test_face_names_match_cube():
    assert FACE_NAMES == FACES


def test_face_names_count():
    assert len(FACE_NAMES) == 12


def test_all_moves_count():
    assert len(ALL_MOVES) == 24  # 12 faces × CW + CCW


def test_five_cw_turns_is_identity():
    for face in FACE_NAMES:
        state = SOLVED_STATE
        for _ in range(5):
            state = apply_move(state, face)
        assert is_solved(state), f"5× {face} did not return to solved"


def test_cw_then_ccw_is_identity():
    for face in FACE_NAMES:
        assert is_solved(apply_move(apply_move(SOLVED_STATE, face), face + "-"))


def test_double_move_equals_two_singles():
    for face in FACE_NAMES:
        s1 = apply_move(apply_move(SOLVED_STATE, face), face)
        s2 = apply_move(SOLVED_STATE, face + "++")
        assert s1 == s2


def test_apply_sequence_empty_is_identity():
    assert is_solved(apply_sequence(SOLVED_STATE, []))


def test_apply_sequence_u_and_inverse():
    assert is_solved(apply_sequence(SOLVED_STATE, ["U", "U-"]))


def test_result_state_is_valid():
    from megaminx.model import validate_state
    for move in ALL_MOVES:
        r = validate_state(apply_move(SOLVED_STATE, move))
        assert r.valid, f"Move {move!r} produced invalid state: {r.errors}"


def test_get_geometry_data_structure():
    g = get_geometry_data()
    for key in ["face_names", "face_vertices", "face_centers",
                "face_corner_cycles", "face_edge_cycles", "corner_faces", "edge_faces"]:
        assert key in g, f"Missing key: {key}"


def test_get_geometry_data_counts():
    g = get_geometry_data()
    assert len(g["face_names"]) == 12
    assert all(len(fv) == 5 for fv in g["face_vertices"])
    assert all(len(v) == 3 for fv in g["face_vertices"] for v in fv)
    assert all(len(cc) == 5 for cc in g["face_corner_cycles"])
    assert len(g["corner_faces"]) == 20
    assert all(len(cf) == 3 for cf in g["corner_faces"])
    assert len(g["edge_faces"]) == 30
    assert all(len(ef) == 2 for ef in g["edge_faces"])


def test_get_geometry_data_face_names_match():
    g = get_geometry_data()
    assert g["face_names"] == FACE_NAMES


def test_parse_move_legacy_notations():
    fi, turns = parse_move("R-")
    assert turns == 4
    fi2, turns2 = parse_move("R'")
    assert fi == fi2 and turns == turns2

    fi3, turns3 = parse_move("U++")
    assert turns3 == 2
    fi4, turns4 = parse_move("U2")
    assert fi3 == fi4 and turns3 == turns4
