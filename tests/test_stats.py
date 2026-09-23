"""Unit tests for the paired significance test in lib.stats."""

from __future__ import annotations

import math

import pandas as pd

from lib.stats import (
    ALPHA,
    _hodges_lehmann_shift,
    pair_speedups,
    statistical_significance,
)
from lib.types import EngineName


def _frame(times: list[list[float]], correct: list[bool]) -> pd.DataFrame:
    """A minimal results frame: only the columns compare()/pair_speedups() touch."""
    return pd.DataFrame({"Times": times, "Correct": correct})


def test_hodges_lehmann_shift_of_one_two_three_is_the_middle_value() -> None:
    # Walsh averages of [1, 2, 3]: 1, 1.5, 2, 2, 2.5, 3 -> median 2.
    assert _hodges_lehmann_shift(pd.Series([1.0, 2.0, 3.0])) == 2.0


def test_hodges_lehmann_shift_of_symmetric_values_is_zero() -> None:
    assert _hodges_lehmann_shift(pd.Series([-1.0, 0.0, 1.0])) == 0.0


def test_compare_reports_bfc_when_consistently_faster() -> None:
    bfc = _frame([[100.0]] * 15, [True] * 15)
    specs = _frame([[200.0]] * 15, [True] * 15)
    p_value, faster = statistical_significance(bfc, specs)
    assert p_value < ALPHA
    assert faster is EngineName.BFC


def test_compare_reports_specs_when_consistently_faster() -> None:
    bfc = _frame([[200.0]] * 15, [True] * 15)
    specs = _frame([[100.0]] * 15, [True] * 15)
    p_value, faster = statistical_significance(bfc, specs)
    assert p_value < ALPHA
    assert faster is EngineName.SPECS


def test_compare_reports_no_difference_for_symmetric_noise() -> None:
    # Every log-speedup has an equal-and-opposite twin, so the paired differences
    # are symmetric around zero: this should never reach significance.
    factors = [1.1, 1 / 1.1, 1.2, 1 / 1.2, 1.15, 1 / 1.15]
    bfc = _frame([[100.0]] * len(factors), [True] * len(factors))
    specs = _frame([[100.0 * f] for f in factors], [True] * len(factors))
    p_value, faster = statistical_significance(bfc, specs)
    assert p_value >= ALPHA
    assert faster is None


def test_compare_reports_nan_when_no_pair_is_shared_correct() -> None:
    bfc = _frame([[100.0]] * 5, [True] * 5)
    specs = _frame([[100.0]] * 5, [False] * 5)
    p_value, faster = statistical_significance(bfc, specs)
    assert math.isnan(p_value)
    assert faster is None


def test_pair_speedups_are_the_exact_mean_time_ratios() -> None:
    # SPECS mean time per run over BFC's: pair 1 -> 200/100=2.0, pair 2 -> 100/100=1.0,
    # pair 3 -> not shared correct, so NaN.
    bfc = _frame([[100.0, 100.0], [50.0, 150.0], [100.0]], [True, True, True])
    specs = _frame([[200.0, 200.0], [100.0, 100.0], [100.0]], [True, True, False])
    speedups = pair_speedups(bfc, specs)
    assert speedups[0] == 2.0
    assert speedups[1] == 1.0
    assert math.isnan(speedups[2])


def test_compare_p_value_matches_wilcoxon_on_the_same_log_speedups() -> None:
    # Six pairs with exact, hand-picked speedups; the expected p-value is scipy's own
    # wilcoxon() on the equivalent log-speedups, computed independently in this test,
    # so this checks compare()'s wiring (log + wilcoxon), not scipy's own correctness.
    from scipy.stats import wilcoxon

    ratios = [2.0, 0.5, 4.0, 1.5, 0.8, 3.0]
    bfc = _frame([[100.0]] * len(ratios), [True] * len(ratios))
    specs = _frame([[100.0 * r] for r in ratios], [True] * len(ratios))
    expected_p = float(wilcoxon([math.log(r) for r in ratios]).pvalue)
    p_value, _ = statistical_significance(bfc, specs)
    assert p_value == expected_p
    assert expected_p == 0.25  # pinned so a future scipy/logic change is caught


def test_compare_uses_hodges_lehmann_not_the_more_frequent_winner() -> None:
    """Regression test for the bug this fix replaced: an even 50/50 split of wins by
    count, where one side's wins are much larger, must resolve to the larger side
    (here BFC) via the Hodges-Lehmann shift, not whichever side happens to win the
    coin-flip median."""
    bfc_times, specs_times, correct = [], [], []
    for _ in range(30):
        bfc_times.append([100.0]); specs_times.append([800.0]); correct.append(True)  # BFC 8x faster
    for _ in range(30):
        bfc_times.append([100.0]); specs_times.append([96.0]); correct.append(True)  # SPECS ~4% faster
    bfc = _frame(bfc_times, correct)
    specs = _frame(specs_times, correct)
    p_value, faster = statistical_significance(bfc, specs)
    assert p_value < ALPHA
    assert faster is EngineName.BFC
