from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import numpy as np
import pandas as pd
from pydantic import TypeAdapter, ValidationError
from returns.io import IOFailure, IOResult, IOSuccess

from .types import (
    ContainmentResult,
    EngineName,
    Operator,
    Outcome,
    PairResult,
    QueryFamily,
    ResultFile,
    Verdict,
)

_SCALE_SUFFIX = re.compile(r"^(?P<family>.+)_(?P<scale>\d+)$")

RESULTS_PATH = Path("./results")


class Suite(StrEnum):
    BRANCHING = "branching"
    BRANCHING_SCALE = "branching-scale"
    OPERATORS = "operators"
    OPERATORS_SCALE = "operators-scale"
    STAR = "star"
    STAR_SCALE = "star-scale"
    UCFQ = "ucfq"
    UCFQ_SCALE = "ucfq-scale"

REGULAR_SUITES: tuple[Suite, ...] = (
    Suite.BRANCHING,
    Suite.OPERATORS,
    Suite.STAR,
    Suite.UCFQ,
)
SCALE_SUITES: tuple[Suite, ...] = (
    Suite.BRANCHING_SCALE,
    Suite.OPERATORS_SCALE,
    Suite.STAR_SCALE,
    Suite.UCFQ_SCALE,
)


def suite_frames(suite: Suite) -> IOResult[tuple[pd.DataFrame, pd.DataFrame], str]:
    """The BFC and SPECS frames of a suite."""
    return IOResult.do(
        (bfc, specs)
        for bfc in result_dataframe(suite, EngineName.BFC)
        for specs in result_dataframe(suite, EngineName.SPECS)
    )


def result_dataframe(suite: Suite, solver: EngineName) -> IOResult[pd.DataFrame, str]:
    return _load_result_file(suite, solver).bind(_build)


def _load_result_file(suite: Suite, solver: EngineName) -> IOResult[ResultFile, str]:
    file = RESULTS_PATH.joinpath(f"{solver}.{suite}.json")
    with open(file, "r") as f:
        try:
            data = TypeAdapter(ResultFile).validate_python(json.load(f))
        except ValidationError as e:
            return IOFailure(str(e))
    return IOSuccess(data)


@dataclass(frozen=True)
class _ExperimentTemplate:
    index: int
    query_family: QueryFamily
    scale: int | None
    operator: Operator


def _parse_template(key: str) -> _ExperimentTemplate:
    index, query, operator = key.split("-", 2)
    scale_match = _SCALE_SUFFIX.match(query)
    if scale_match is None:
        return _ExperimentTemplate(int(index), QueryFamily(query), None, Operator(operator))
    return _ExperimentTemplate(
        int(index),
        QueryFamily(scale_match.group("family")),
        int(scale_match.group("scale")),
        Operator(operator),
    )


@dataclass(frozen=True)
class _Execution:
    outcome: Outcome
    verdict: ContainmentResult
    expected: Verdict
    times: list[np.float32]
    timeout: bool
    error: bool
    correct: bool
    incorrect: bool
    out_of_memory: bool


def _generate_execution(value: PairResult) -> _Execution:
    outcome, verdict, expected = value["outcome"], value["verdict"], value["expected"]
    if value["outcome"] == Outcome.TIMEOUT:
        return _Execution(outcome, verdict, expected, [], True, False, False, False, False)
    if value["outcome"] == Outcome.ERROR:
        return _Execution(outcome, verdict, expected, [], False, True, False, False, False)
    return _Execution(
        outcome,
        verdict,
        expected,
        [np.float32(t) for t in value["ms"]],
        False,
        False,
        outcome == Outcome.CORRECT,
        outcome == Outcome.INCORRECT,
        outcome == Outcome.OUT_OF_MEMORY,
    )


def _build(data: ResultFile) -> IOResult[pd.DataFrame, str]:
    results: dict[str, PairResult] = data["results"]
    pairs: list[str] = []
    indexes: list[int] = []
    query_families: list[QueryFamily] = []
    scales: list[int | None] = []
    operators: list[Operator] = []
    outcomes: list[Outcome] = []
    verdicts: list[ContainmentResult] = []
    expecteds: list[Verdict] = []
    times: list[list[np.float32]] = []
    timeouts: list[bool] = []
    errors: list[bool] = []
    correct: list[bool] = []
    incorrect: list[bool] = []
    out_of_memory: list[bool] = []

    for key, value in results.items():
        pairs.append(key)
        template = _parse_template(key)
        indexes.append(template.index)
        query_families.append(template.query_family)
        scales.append(template.scale)
        operators.append(template.operator)

        execution = _generate_execution(value)
        outcomes.append(execution.outcome)
        verdicts.append(execution.verdict)
        expecteds.append(execution.expected)
        times.append(execution.times)
        timeouts.append(execution.timeout)
        errors.append(execution.error)
        correct.append(execution.correct)
        incorrect.append(execution.incorrect)
        out_of_memory.append(execution.out_of_memory)

    return IOSuccess(pd.DataFrame(
        {
            "Pairs": pairs,
            "Index": indexes,
            "QueryFamily": query_families,
            "Scale": scales,
            "Operator": operators,
            "Outcome": outcomes,
            "Verdict": verdicts,
            "Expected": expecteds,
            "Times": times,
            "Timeouts": timeouts,
            "Errors": errors,
            "Correct": correct,
            "Incorrect": incorrect,
            "OutOfMemory": out_of_memory,
        }
    ))
