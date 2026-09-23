from __future__ import annotations

import math
import statistics
from collections.abc import Sequence

import pandas as pd
from returns.io import IOFailure, IOResult, IOSuccess
from returns.result import Failure, Success
from scipy.stats import wilcoxon

from .datasets import Suite, suite_frames
from .types import EngineName, Operator, Outcome

# Bonferroni correction: this evaluation reports 11 significance tests (the overview's
# all/regular/scale tables, and one per suite in pair_comparison), so each test uses
# alpha/11 to keep the overall false-positive rate across all of them at 5%.
SIGNIFICANCE_TESTS = 11
ALPHA = 0.05 / SIGNIFICANCE_TESTS


def pooled(suites: Sequence[Suite]) -> IOResult[tuple[pd.DataFrame, pd.DataFrame], str]:
    """The BFC and SPECS frames of several suites stacked, still aligned pair for pair."""
    bfc_frames: list[pd.DataFrame] = []
    specs_frames: list[pd.DataFrame] = []
    for suite in suites:
        match suite_frames(suite):
            case IOSuccess(Success((bfc, specs))):
                bfc_frames.append(bfc)
                specs_frames.append(specs)
            case IOFailure(Failure(message)):
                return IOFailure(message)
    return IOSuccess(
        (
            pd.concat(bfc_frames, ignore_index=True),
            pd.concat(specs_frames, ignore_index=True),
        )
    )


def correct_times(df: pd.DataFrame) -> list[float]:
    """Every timing, in ms, of the pairs the engine answered correctly."""
    resp: list[float] = []
    for times, correct in zip(df["Times"], df["Correct"]):
        if not correct:
            continue
        for time in times:
            resp.append(float(time))
    return resp


def summary_table(bfc: pd.DataFrame, specs: pd.DataFrame) -> pd.DataFrame:
    """One row per engine: timing over its correct pairs, and how every pair ended."""
    rows = []
    for engine, df in ((EngineName.BFC, bfc), (EngineName.SPECS, specs)):
        times = pd.Series(correct_times(df), dtype=float)
        rows.append(
            {
                "Engine": engine.value.upper(),
                "Mean (ms)": times.mean(),
                "Median (ms)": times.median(),
                "Correct": int(df["Correct"].sum()),
                "Unknown": int((df["Outcome"] == Outcome.UNKNOWN).sum()),
                "Incorrect": int(df["Incorrect"].sum()),
                "Timeouts": int(df["Timeouts"].sum()),
                "Errors": int(df["Errors"].sum()),
                "OutOfMemory": int(df["OutOfMemory"].sum()),
            }
        )
    return pd.DataFrame(rows)


def _hodges_lehmann_shift(values: pd.Series) -> float:
    """The Hodges-Lehmann estimator of `values`: the median of every pair's average
    (a value may pair with itself). This is the standard companion statistic to the
    Wilcoxon signed-rank test; its sign says which direction a significant result
    points in."""
    data = [float(v) for v in values]
    walsh_averages = [
        (data[i] + data[j]) / 2 for i in range(len(data)) for j in range(i, len(data))
    ]
    return statistics.median(walsh_averages)


def statistical_significance(bfc: pd.DataFrame, specs: pd.DataFrame) -> tuple[float, EngineName | None]:
    """Statistical significance using Wilcoxon signed-rank test on the log of the per-pair speedups (see
    `pair_speedups`), over the pairs both engines answered correctly, and the
    faster engine when the difference is significant, else None."""
    log_speedups = pair_speedups(bfc, specs).dropna().map(math.log)
    if log_speedups.empty:
        return float("nan"), None
    p_value = float(wilcoxon(log_speedups).pvalue)
    if p_value >= ALPHA:
        return p_value, None
    shift = _hodges_lehmann_shift(log_speedups)
    return p_value, EngineName.BFC if shift > 0 else EngineName.SPECS


def statistical_significance_verdict(p_value: float, faster: EngineName | None) -> str:
    """The result of `statistical_significance` as a sentence."""
    if math.isnan(p_value):
        return "Cannot compare: an engine has no correct pair."
    p_text = f"= {p_value:.4g}"
    test = (
        f"Wilcoxon signed-rank test with Hodges-Lehmann direction "
        f"(Bonferroni-corrected α = {ALPHA:.4g} for {SIGNIFICANCE_TESTS} tests)"
    )
    if faster is None:
        return f"{test}: p {p_text}, no statistically significant difference."
    return f"{test}: p {p_text}, statistically significant, **{faster.value.upper()} is faster**."


def correct_times_by_operator(df: pd.DataFrame) -> dict[Operator, list[float]]:
    """Every timing, in ms, of the pairs the engine answered correctly, per operator."""
    return {
        operator: correct_times(df[df["Operator"] == operator]) for operator in Operator
    }


def outcomes_by_operator(df: pd.DataFrame) -> pd.DataFrame:
    """How many pairs of each operator ended in each outcome."""
    counts = pd.crosstab(df["Operator"], df["Outcome"])
    return counts.reindex(index=list(Operator), columns=list(Outcome), fill_value=0)


def _pair_speedup(item: tuple[list[float], list[float], bool]) -> float:
    b_times, s_times, ok = item
    if not ok:
        return float("nan")
    avg1 = sum(s_times) / len(s_times)
    avg2 = sum(b_times) / len(b_times)
    return avg1 / avg2


def pair_speedups(bfc: pd.DataFrame, specs: pd.DataFrame) -> pd.Series:
    """Per pair, SPECS mean time per run over BFC's, so a value above 1 means BFC is
    faster. NaN unless both engines answered the pair correctly."""
    series = bfc["Correct"] & specs["Correct"]
    return pd.Series(
        list(map(_pair_speedup, zip(bfc["Times"], specs["Times"], series))),
        index=bfc.index,
        dtype=float,
    )


def operator_table(bfc: pd.DataFrame, specs: pd.DataFrame) -> pd.DataFrame:
    """An overview of each operator's performance, across every suite."""
    rows = []
    for operator in Operator:
        wanted = bfc["Operator"] == operator
        b, s = bfc[wanted], specs[wanted]
        speedup = pair_speedups(b, s).mean()
        rows.append(
            {
                "Operator": operator.label,
                "Pairs": len(b),
                "BFC correct": int(b["Correct"].sum()),
                "SPECS correct": int(s["Correct"].sum()),
                "BFC median (ms)": pd.Series(correct_times(b), dtype=float).median(),
                "SPECS median (ms)": pd.Series(correct_times(s), dtype=float).median(),
                "Average speedup of BFC over SPECS": speedup,
            }
        )
    return pd.DataFrame(rows)


def matched_times_by_size(df: pd.DataFrame) -> dict[int, list[list[float]]]:
    """Per size, the timings of the cases (the same containment claim, tested again
    at a different size) the engine answers correctly at every size."""
    sizes = sorted(int(size) for size in df["Scale"].unique())
    if len(df) % len(sizes) != 0:
        raise ValueError("the sizes of a scale suite must hold the same cases")
    cases = pd.DataFrame(
        {
            "size": df["Scale"].astype(int),
            "case": (df["Index"] - 1) % (len(df) // len(sizes)),
            "correct": df["Correct"],
            "times": df["Times"],
        }
    )
    solved = cases.groupby("case")["correct"].all()
    kept = set(solved[solved].index)
    grouped: dict[int, list[list[float]]] = {size: [] for size in sizes}
    for size, case, times in zip(cases["size"], cases["case"], cases["times"]):
        if case in kept:
            grouped[size].append([float(time) for time in times])
    return grouped
