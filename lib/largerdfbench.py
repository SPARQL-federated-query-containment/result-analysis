"""LargeRDFBench (Saleem et al., 2018) execution times, for comparison against
BFC/SPECS. See results/largerdfbench/README.md for provenance."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from returns.io import IOFailure, IOResult
from returns.result import Failure, Result, Success

from .types import (
    LargeRDFBenchCategory,
    LargeRDFBenchSourceSelection,
    LargeRDFBenchSystem,
)

RESULTS_PATH = Path("results/largerdfbench/Results-final.xlsx")

_SHEET_NAMES: dict[LargeRDFBenchSourceSelection, str] = {
    LargeRDFBenchSourceSelection.AUTOMATIC: "Runtimes_SPARQL1.0",
    LargeRDFBenchSourceSelection.EXPLICIT_SERVICE: "Runtimes_SPARQL1.1",
}

# Column order matches each sheet's own header row.
_AUTOMATIC_SYSTEMS = [
    LargeRDFBenchSystem.FEDX_COLD,
    LargeRDFBenchSystem.FEDX_CACHED,
    LargeRDFBenchSystem.SPLENDID,
    LargeRDFBenchSystem.ANAPSID,
    LargeRDFBenchSystem.FEDX_HIBISCUS,
    LargeRDFBenchSystem.SPLENDID_HIBISCUS,
]
_EXPLICIT_SERVICE_SYSTEMS = [LargeRDFBenchSystem.FEDX_CACHED, LargeRDFBenchSystem.ANAPSID]

_QUERIES: dict[LargeRDFBenchCategory, list[str]] = {
    LargeRDFBenchCategory.SIMPLE: [f"S{i}" for i in range(1, 15)],
    LargeRDFBenchCategory.COMPLEX: [f"C{i}" for i in range(1, 11)],
    LargeRDFBenchCategory.LARGE: [f"L{i}" for i in range(1, 9)],
}
# The explicit-SERVICE sheet labels the same 8 Large queries B1..B8, not L1..L8.
_LARGE_QUERIES_EXPLICIT_SERVICE = [f"B{i}" for i in range(1, 9)]

# A cell is bare "TO"/"RE"/"ZR", a bare number, or a number with a completeness
# percentage, e.g. "123735 (2.73 %)".
_CELL = re.compile(r"^(TO|RE|ZR|\d+)\s*(?:\(([\d.]+)\s*%\))?$")


def _parse_cell(cell: object) -> Result[tuple[float | None, bool], str]:
    """Time in ms (None for TO/RE/ZR), and complete unless a percentage is shown.
    Fails only on an unrecognised format."""
    if isinstance(cell, (int, float)) and not pd.isna(cell):
        return Success((float(cell), True))
    match = _CELL.match(str(cell).strip())
    if not match:
        return Failure(f"unrecognised LargeRDFBench cell: {cell!r}")
    number, percent = match.groups()
    if number in ("TO", "RE", "ZR"):
        return Success((None, False))
    return Success((float(number), percent is None))


def _build(path: Path) -> Result[pd.DataFrame, str]:
    sheets = {
        selection: pd.read_excel(path, sheet_name=sheet_name, header=None)
        for selection, sheet_name in _SHEET_NAMES.items()
    }
    rows: list[dict[str, object]] = []
    for category, queries in _QUERIES.items():
        selections = (
            (LargeRDFBenchSourceSelection.AUTOMATIC, _AUTOMATIC_SYSTEMS, queries),
            (
                LargeRDFBenchSourceSelection.EXPLICIT_SERVICE,
                _EXPLICIT_SERVICE_SYSTEMS,
                _LARGE_QUERIES_EXPLICIT_SERVICE
                if category == LargeRDFBenchCategory.LARGE
                else queries,
            ),
        )
        for selection, systems, sheet_queries in selections:
            frame = sheets[selection]
            wanted = frame[frame[0].isin(sheet_queries)].set_index(0)
            for query, sheet_query in zip(queries, sheet_queries):
                for column, system in enumerate(systems, start=1):
                    match _parse_cell(wanted.loc[sheet_query, column]):
                        case Failure(message):
                            return Failure(message)
                        case Success((time_ms, complete)):
                            rows.append(
                                {
                                    "Category": category,
                                    "SourceSelection": selection,
                                    "System": system,
                                    "Query": query,
                                    "Time (ms)": time_ms,
                                    "Complete": complete,
                                }
                            )
    return Success(pd.DataFrame(rows))


def execution_times(path: Path = RESULTS_PATH) -> IOResult[pd.DataFrame, str]:
    """Every (category, source selection, system, query) cell of the raw evaluation
    spreadsheet, tidy: one row per cell. Columns: Category, SourceSelection, System,
    Query, Time (ms) (NaN for a timeout or runtime error), Complete (bool)."""
    try:
        result = _build(path)
    except FileNotFoundError as e:
        return IOFailure(str(e))
    return IOResult.from_result(result)
