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
