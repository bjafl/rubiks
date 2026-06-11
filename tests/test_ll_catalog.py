# tests/test_ll_catalog.py
import pytest
from megaminx.cube import SOLVED, apply_move, MegaminxState
from megaminx.ll_catalog import (
    LL_CORNER_SLOTS, LL_EDGE_SLOTS,
    LLStage, Solution, Case, StageCatalog,
    CO_STAGE, EP_STAGE, CP_STAGE_CO_FIRST, CP_STAGE_CO_LAST,
    _apply_auf, auf_canonical, enumerate_cases,
    _make_ll_state, _find_solutions,
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


# ─── AUF canonicalization tests ─────────────────────────────────────────────


def test_apply_auf_k0_is_identity():
    ll_co = (0, 1, 2, 0, 2)
    ll_cp = LL_CORNER_SLOTS
    ll_ep = LL_EDGE_SLOTS
    assert _apply_auf(ll_co, ll_cp, ll_ep, 0) == (ll_co, ll_cp, ll_ep)


def test_apply_auf_k1_spec_example():
    # Spec example: [0,1,2,0,2] → [2,0,1,2,0] after k=1
    ll_co = (0, 1, 2, 0, 2)
    result_co, _, _ = _apply_auf(ll_co, LL_CORNER_SLOTS, LL_EDGE_SLOTS, 1)
    assert result_co == (2, 0, 1, 2, 0)


def test_apply_auf_all_5_variants_spec():
    # Full spec example variants
    ll_co = (0, 1, 2, 0, 2)
    expected = [
        (0, 1, 2, 0, 2),
        (2, 0, 1, 2, 0),
        (0, 2, 0, 1, 2),
        (2, 0, 2, 0, 1),
        (1, 2, 0, 2, 0),
    ]
    for k in range(5):
        result_co, _, _ = _apply_auf(ll_co, LL_CORNER_SLOTS, LL_EDGE_SLOTS, k)
        assert result_co == expected[k], f"k={k}: got {result_co}, expected {expected[k]}"


def test_auf_canonical_is_minimum():
    ll_co = (0, 1, 2, 0, 2)
    ll_cp = LL_CORNER_SLOTS
    ll_ep = LL_EDGE_SLOTS
    canonical = auf_canonical(ll_co, ll_cp, ll_ep)
    for k in range(5):
        variant = _apply_auf(ll_co, ll_cp, ll_ep, k)
        assert canonical <= variant


def test_auf_canonical_stable():
    # Canonical is a fixed point: auf_canonical(canonical) == canonical
    ll_co = (0, 1, 2, 0, 2)
    canonical = auf_canonical(ll_co, LL_CORNER_SLOTS, LL_EDGE_SLOTS)
    assert auf_canonical(*canonical) == canonical


def test_auf_5_distinct_variants():
    # Non-trivial CO states have orbit size 5 (no period < 5)
    ll_co = (0, 1, 2, 0, 2)
    canonical = auf_canonical(ll_co, LL_CORNER_SLOTS, LL_EDGE_SLOTS)
    variants = {_apply_auf(*canonical, k) for k in range(5)}
    assert len(variants) == 5


# ─── Case enumeration tests ────────────────────────────────────────────────────


def test_co_case_count():
    cases = enumerate_cases(CO_STAGE)
    assert len(cases) == 16


def test_ep_case_count():
    cases = enumerate_cases(EP_STAGE)
    assert len(cases) == 12


def test_cp_case_count():
    cases = enumerate_cases(CP_STAGE_CO_FIRST)
    assert len(cases) == 12


def test_cases_are_canonical():
    # Every case returned by enumerate_cases must already be its own canonical
    for stage in (CO_STAGE, EP_STAGE, CP_STAGE_CO_FIRST):
        for case in enumerate_cases(stage):
            assert auf_canonical(*case) == case


def test_cases_are_distinct():
    for stage in (CO_STAGE, EP_STAGE, CP_STAGE_CO_FIRST):
        cases = enumerate_cases(stage)
        assert len(set(cases)) == len(cases)


def test_co_cases_exclude_identity():
    # CO=(0,0,0,0,0) must not appear in any AUF variant
    cases = enumerate_cases(CO_STAGE)
    identity_co = (0, 0, 0, 0, 0)
    for case in cases:
        for k in range(5):
            rotated_co, _, _ = _apply_auf(*case, k)
            assert rotated_co != identity_co


# ─── State builder and DFS solution search tests ─────────────────────────────


def test_make_ll_state_identity():
    state = _make_ll_state((0,)*5, LL_CORNER_SLOTS, LL_EDGE_SLOTS)
    assert state == SOLVED


def test_make_ll_state_co_only():
    co = (0, 1, 2, 0, 2)
    state = _make_ll_state(co, LL_CORNER_SLOTS, LL_EDGE_SLOTS)
    for i, s in enumerate(LL_CORNER_SLOTS):
        assert state.co[s] == co[i]
    for s in LL_CORNER_SLOTS:
        assert state.cp[s] == s
    for s in LL_EDGE_SLOTS:
        assert state.ep[s] == s


def test_is_solved_co_stage_detects_unoriented():
    co = (0, 1, 2, 0, 0)  # sum=3≡0, corner at slot 4 has co=1
    state = _make_ll_state(co, LL_CORNER_SLOTS, LL_EDGE_SLOTS)
    assert not CO_STAGE.is_solved(state)


def test_is_solved_co_stage_accepts_solved():
    state = _make_ll_state((0,)*5, LL_CORNER_SLOTS, LL_EDGE_SLOTS)
    assert CO_STAGE.is_solved(state)


def test_find_solutions_empty_for_solved():
    state = _make_ll_state((0,)*5, LL_CORNER_SLOTS, LL_EDGE_SLOTS)
    solutions = _find_solutions(state, CO_STAGE, ["R", "R-", "U", "U-"], 5)
    assert any(s.length == 0 for s in solutions)


def test_find_solutions_for_co_state():
    canonical = auf_canonical((0, 1, 2, 0, 2), LL_CORNER_SLOTS, LL_EDGE_SLOTS)
    ll_co, ll_cp, ll_ep = canonical
    state = _make_ll_state(ll_co, ll_cp, ll_ep)
    move_set = ["R", "R-", "U", "U-", "U++", "U--"]
    solutions = _find_solutions(state, CO_STAGE, move_set, max_depth=8)
    for sol in solutions:
        s = state
        for m in sol.moves:
            s = apply_move(s, m)
        assert CO_STAGE.is_solved(s)


def test_solutions_sorted_by_length():
    canonical = auf_canonical((0, 1, 2, 0, 2), LL_CORNER_SLOTS, LL_EDGE_SLOTS)
    ll_co, ll_cp, ll_ep = canonical
    state = _make_ll_state(ll_co, ll_cp, ll_ep)
    solutions = _find_solutions(state, CO_STAGE, ["R", "R-", "U", "U-", "U++", "U--"], 8)
    if len(solutions) >= 2:
        for i in range(len(solutions) - 1):
            assert solutions[i].length <= solutions[i + 1].length
