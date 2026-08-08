"""
Checks that the model behaves the way the business rules say it should.

Run with:
    DOM_DATA="/path/to/DOM-data/input data" pytest -v

If no data is found the tests are skipped rather than failed, so the suite still
runs in a fresh clone.
"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import dom_model as dm


@pytest.fixture(scope="module")
def D():
    try:
        return dm.load_all(os.environ.get("DOM_DATA"))
    except FileNotFoundError:
        pytest.skip("data files not found - set DOM_DATA to the input folder")


@pytest.fixture(scope="module")
def staged(D):
    return dm.stage_A(D)


# ---------------------------------------------------------------- the data
def test_extract_is_already_filtered(D):
    """Every row should be full truckload with the delivery note still open."""
    assert set(D.orders["IsFTL"].str.strip().str.upper()) == {"Y"}
    assert set(D.orders["DeliveryNoteFlag"].str.strip().str.upper()) == {"N"}


def test_eight_distribution_centres(D):
    assert len(D.DCS) == 8


def test_pallet_lines_convert_to_cases(D):
    """A pallet line should be quantity times cases per pallet."""
    pl = D.orders[D.orders["ProductPlanningUnitOfMeasure"] == "PL"]
    if len(pl) == 0:
        pytest.skip("no pallet lines in this extract")
    expected = pl["OrderedQty_converted"] * pl["ProductCasesPerPallet"]
    assert np.allclose(pl["cases"], expected)


def test_every_lane_the_orders_need_exists(D):
    """Each DC must be able to quote every ship-to zip, or a move is impossible."""
    needed = {(d, int(z)) for d in D.DCS for z in D.orders["ZipCode"].unique()}
    assert len(needed - set(D.SHIP)) == 0


# ---------------------------------------------------------------- the funnel
def test_focus_and_clean_cover_every_order(D):
    assert len(D.FOCUS) + len(D.CLEAN_ORDERS) == len(D.HEAD)
    assert set(D.FOCUS) & set(D.CLEAN_ORDERS) == set()


def test_focus_count(D):
    """447 short of stock plus 25 with no dock slot."""
    assert len(D.FOCUS) == 472
    assert len(D.HEAD) == 1109


# ---------------------------------------------------------------- the rules
def test_c2_never_fills_more_than_ordered(D, staged):
    _, default = staged
    for g in list(D.FOCUS)[:200]:
        want = dict((s, dem) for s, dem, _, _ in D.LINES[g])
        for s, q, _, _ in default[g]["fills"]:
            assert q <= want[s] + 1e-9


def test_c3_window_is_never_more_than_one_day(D):
    """Availability over 5 days cannot beat availability on the tightest day."""
    P = {k: v.copy() for k, v in D.POOL0.items()}
    for (d, s) in list(P)[:300]:
        one = dm.avail(D, P, d, s, 0, window=0)
        five = dm.avail(D, P, d, s, 0, window=5)
        assert five <= one + 1e-9


def test_c4_gate_rejects_small_moves(D):
    assert dm.passes_gate(10, 10_000) == "fail_5pct"       # under 5 points
    assert dm.passes_gate(80, 1_000) == "fail_100cases"    # over 5 points, under 100 cases
    assert dm.passes_gate(500, 1_000) is None              # clears both


def test_c4_threshold_is_the_larger_of_the_two(D):
    g = D.FOCUS[0]
    ordered = D.HEAD[g]["ordered_cases"]
    assert dm.gate_lift(D, g) == max(0.05 * ordered, 100.0)


def test_c5_picks_split_correctly():
    """24 cases at 10 per pallet is 2 pallet picks and 4 case picks."""
    cp, pp = dm.picks([(1, 24.0, 5.0, 10.0)])
    assert (cp, pp) == (4.0, 2.0)


def test_c7_no_penalty_at_or_above_threshold(D):
    charged = [g for g in D.FOCUS if D.HEAD[g]["ppc"] > 0]
    if not charged:
        pytest.skip("no orders carry a penalty schedule")
    g = charged[0]
    full = {s: dem for s, dem, _, _ in D.LINES[g]}
    assert dm.penalty_of(D, g, full, sum(full.values())) == 0.0


def test_c7_penalty_is_positive_when_nothing_is_filled(D):
    charged = [g for g in D.FOCUS if D.HEAD[g]["ppc"] > 0
               and D.HEAD[g]["threshold_cases"] > 0]
    if not charged:
        pytest.skip("no orders carry a penalty schedule")
    g = charged[0]
    empty = {s: 0.0 for s, _, _, _ in D.LINES[g]}
    assert dm.penalty_of(D, g, empty, 0.0) > 0


# ---------------------------------------------------------------- the objective
def test_objective_is_revenue_minus_penalty_minus_shipping():
    rec = dict(revenue=1000.0, pen=100.0, ship=50.0)
    assert dm.objective(rec) == 850.0


def test_baseline_reproduces_the_known_number(D, staged):
    _, default = staged
    total = sum(dm.objective(default[g]) for g in D.FOCUS)
    assert abs(total - 44_365_994) < 1_000


def test_baseline_fill_rate(D, staged):
    _, default = staged
    ordered = sum(D.HEAD[g]["ordered_cases"] for g in D.FOCUS)
    filled = sum(default[g]["filled"] for g in D.FOCUS)
    assert 0.90 < filled / ordered < 0.91


def test_stage_a_moves_nothing(D, staged):
    _, default = staged
    assert all(not default[g]["diverted"] for g in default)
    assert all(default[g]["chosen_dc"] == D.HEAD[g]["default_dc"] for g in default)
