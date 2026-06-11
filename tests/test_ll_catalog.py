# tests/test_ll_catalog.py
import pytest
from megaminx.ll_catalog import (
    LL_CORNER_SLOTS, LL_EDGE_SLOTS,
    LLStage, Solution, Case, StageCatalog,
    CO_STAGE, EP_STAGE, CP_STAGE_CO_FIRST, CP_STAGE_CO_LAST,
)


def test_ll_corner_slots():
    assert LL_CORNER_SLOTS == (0, 4, 7, 18, 19)
    assert len(LL_CORNER_SLOTS) == 5


def test_ll_edge_slots():
    assert LL_EDGE_SLOTS == (4, 8, 27, 28, 29)
    assert len(LL_EDGE_SLOTS) == 5


def test_co_stage_flags():
    assert CO_STAGE.solve_co is True
    assert CO_STAGE.solve_ep is False
    assert CO_STAGE.solve_cp is False
    assert CO_STAGE.require_co_solved is False
    assert CO_STAGE.require_ep_solved is False
    assert CO_STAGE.require_cp_solved is False


def test_ep_stage_flags():
    assert EP_STAGE.solve_ep is True
    assert EP_STAGE.require_co_solved is True
    assert EP_STAGE.solve_co is False
    assert EP_STAGE.solve_cp is False


def test_cp_stage_co_first_flags():
    assert CP_STAGE_CO_FIRST.solve_cp is True
    assert CP_STAGE_CO_FIRST.require_co_solved is True
    assert CP_STAGE_CO_FIRST.require_ep_solved is True


def test_cp_stage_co_last_flags():
    assert CP_STAGE_CO_LAST.solve_cp is True
    assert CP_STAGE_CO_LAST.require_co_solved is False
    assert CP_STAGE_CO_LAST.require_ep_solved is True


def test_solution_dataclass():
    s = Solution(moves=["R", "U", "R-"], length=3)
    assert s.moves == ["R", "U", "R-"]
    assert s.length == 3


def test_stage_catalog_dataclass():
    cat = StageCatalog(stage="co", move_set=["R", "U"], max_depth=5, cases=[])
    assert cat.stage == "co"
    assert cat.cases == []


# ─── Behaviour tests for is_solved ──────────────────────────────────────────

from megaminx.cube import SOLVED, apply_move, MegaminxState


def test_is_solved_accepts_solved_state_all_stages():
    for stage in [CO_STAGE, EP_STAGE, CP_STAGE_CO_FIRST, CP_STAGE_CO_LAST]:
        assert stage.is_solved(SOLVED), f"{stage.name} should accept SOLVED state"


def test_is_solved_co_stage_rejects_after_u_move():
    # U disturbs LL corner orientations — CO_STAGE must reject
    state_after_u = apply_move(SOLVED, "U")
    assert not CO_STAGE.is_solved(state_after_u)


def test_is_solved_co_stage_accepts_permuted_cp():
    # CO_STAGE only checks CO, not CP — a state with CO=0 but scrambled CP should pass
    # Build state: swap two LL corner pieces but keep orientations 0
    cp = list(SOLVED.cp)
    # Swap slots 0 and 4 (both LL corners)
    cp[0], cp[4] = cp[4], cp[0]
    state = MegaminxState(tuple(cp), SOLVED.co, SOLVED.ep, SOLVED.eo)
    assert CO_STAGE.is_solved(state)


def test_is_solved_cp_stage_rejects_permuted_cp():
    # CP_STAGE_CO_FIRST must reject scrambled CP
    cp = list(SOLVED.cp)
    cp[0], cp[4] = cp[4], cp[0]
    state = MegaminxState(tuple(cp), SOLVED.co, SOLVED.ep, SOLVED.eo)
    assert not CP_STAGE_CO_FIRST.is_solved(state)


def test_is_solved_rejects_disturbed_non_ll():
    # Any stage must reject a state where non-LL pieces moved (e.g. D face turn)
    state_after_d = apply_move(SOLVED, "D")
    for stage in [CO_STAGE, EP_STAGE, CP_STAGE_CO_FIRST, CP_STAGE_CO_LAST]:
        assert not stage.is_solved(state_after_d), f"{stage.name} should reject D-moved state"
