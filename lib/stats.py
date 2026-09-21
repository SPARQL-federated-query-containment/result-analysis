from __future__ import annotations

from collections.abc import Sequence

import pandas as pd
from scipy.stats import mannwhitneyu

from .datasets import Suite, suite_frames
from .types import EngineName, Outcome

ALPHA = 0.05


def pooled(suites: Sequence[Suite]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The BFC and SPECS frames of several suites stacked, still aligned pair for pair."""
    frames = [suite_frames(suite) for suite in suites]
    bfc = pd.concat([bfc for bfc, _ in frames], ignore_index=True)
    specs = pd.concat([specs for _, specs in frames], ignore_index=True)
    return bfc, specs


def correct_times(df: pd.DataFrame) -> list[float]:
    """Every timing, in ms, of the pairs the engine answered correctly."""
    return [
        float(time)
        for times, correct in zip(df["Times"], df["Correct"])
        if correct
        for time in times
    ]


def summary_table(bfc: pd.DataFrame, specs: pd.DataFrame) -> pd.DataFrame:
    """One row per engine: timing over its correct pairs, and how every pair ended."""
    rows = []
    for engine, df in ((EngineName.BFC, bfc), (EngineName.SPECS, specs)):
        times = pd.Series(correct_times(df), dtype=float)
        rows.append(
            {
                "Engine": engine.value,
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


def compare(bfc: pd.DataFrame, specs: pd.DataFrame) -> tuple[float, EngineName | None]:
    """Mann-Whitney p-value on the pairs both engines answered correctly, and the
    faster engine (lower median) when the difference is significant, else None."""
    both = bfc["Correct"] & specs["Correct"]
    bfc_times = pd.Series(correct_times(bfc[both]), dtype=float)
    specs_times = pd.Series(correct_times(specs[both]), dtype=float)
    if bfc_times.empty or specs_times.empty:
        return float("nan"), None
    p_value = float(mannwhitneyu(bfc_times, specs_times, alternative="two-sided").pvalue)
    if p_value >= ALPHA:
        return p_value, None
    return p_value, EngineName.BFC if bfc_times.median() < specs_times.median() else EngineName.SPECS


def matched_times_by_size(df: pd.DataFrame) -> dict[int, list[list[float]]]:
    """Per size, the timings of the statements the engine answers correctly at every size."""
    sizes = sorted(int(size) for size in df["Scale"].unique())
    if len(df) % len(sizes) != 0:
        raise ValueError("the sizes of a scale suite must hold the same statements")
    statements = pd.DataFrame(
        {
            "size": df["Scale"].astype(int),
            "statement": (df["Index"] - 1) % (len(df) // len(sizes)),
            "correct": df["Correct"],
            "times": df["Times"],
        }
    )
    solved = statements.groupby("statement")["correct"].all()
    kept = set(solved[solved].index)
    grouped: dict[int, list[list[float]]] = {size: [] for size in sizes}
    for size, statement, times in zip(statements["size"], statements["statement"], statements["times"]):
        if statement in kept:
            grouped[size].append([float(time) for time in times])
    return grouped
