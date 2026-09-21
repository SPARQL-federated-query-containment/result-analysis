from __future__ import annotations

from enum import StrEnum
from typing import Literal, TypedDict


class EngineName(StrEnum):
    BFC = "bfc"
    SPECS = "specs"


class Operator(StrEnum):
    """The permutation applied to derive one side of a pair from the other."""

    ADD_FRESH_VARIABLE_CLAUSE_AT_CONTACTED_MEMBER_TO_SUB = (
        "add_fresh_variable_clause_at_contacted_member_to_sub"
    )
    ADD_FRESH_VARIABLE_CLAUSE_AT_NEW_MEMBER_TO_SUB = (
        "add_fresh_variable_clause_at_new_member_to_sub"
    )
    ADD_MEMBER_TO_SUPER = "add_member_to_super"
    ADD_SHARED_VARIABLE_CLAUSE_TO_SUB = "add_shared_variable_clause_to_sub"
    ASSIGN_FEDERATION = "assign_federation"
    BIND_LOCAL_VARIABLE = "bind_local_variable"
    DROP_HEAD_VARIABLE = "drop_head_variable"
    DROP_VARIABLE_FROM_SUPER = "drop_variable_from_super"
    IDENTITY = "identity"
    RELAX_CLAUSE = "relax_clause"
    RENAME_LOCAL_VARIABLE = "rename_local_variable"
    RENAME_MEMBER = "rename_member"
    REORDER_BODY = "reorder_body"
    SWAP_CONSTANT = "swap_constant"
    WIDEN_VIRTUAL_MEMBER = "widen_virtual_member"

    @property
    def label(self) -> str:
        return _OPERATOR_LABELS[self]


_OPERATOR_LABELS: dict[Operator, str] = {
    Operator.ADD_FRESH_VARIABLE_CLAUSE_AT_CONTACTED_MEMBER_TO_SUB: "Add fresh-variable clause at contacted member (sub)",
    Operator.ADD_FRESH_VARIABLE_CLAUSE_AT_NEW_MEMBER_TO_SUB: "Add fresh-variable clause at new member (sub)",
    Operator.ADD_MEMBER_TO_SUPER: "Add member to super",
    Operator.ADD_SHARED_VARIABLE_CLAUSE_TO_SUB: "Add shared-variable clause (sub)",
    Operator.ASSIGN_FEDERATION: "Assign federation",
    Operator.BIND_LOCAL_VARIABLE: "Bind local variable",
    Operator.DROP_HEAD_VARIABLE: "Drop head variable",
    Operator.DROP_VARIABLE_FROM_SUPER: "Drop variable from super",
    Operator.IDENTITY: "Identity",
    Operator.RELAX_CLAUSE: "Relax clause",
    Operator.RENAME_LOCAL_VARIABLE: "Rename local variable",
    Operator.RENAME_MEMBER: "Rename member",
    Operator.REORDER_BODY: "Reorder body",
    Operator.SWAP_CONSTANT: "Swap constant",
    Operator.WIDEN_VIRTUAL_MEMBER: "Widen virtual member",
}


class QueryFamily(StrEnum):
    """The base query a pair is drawn from"""

    BRANCHING = "branching"
    BRANCHING_LOCAL = "branching_local"
    CHAIN = "chain"
    CHAIN_LOCAL = "chain_local"
    STAR = "star"
    STAR_LOCAL = "star_local"
    UCFQ = "ucfq"
    SERVICE_S2 = "service_S2"
    SERVICE_S4 = "service_S4"
    SERVICE_S5 = "service_S5"
    SERVICE_S11 = "service_S11"
    SERVICE_S12 = "service_S12"
    AUTO_QC_NOP_Q0A = "auto_qc_nop_Q0a"
    AUTO_QC_NOP_Q0B = "auto_qc_nop_Q0b"
    AUTO_QC_NOP_Q0C = "auto_qc_nop_Q0c"
    AUTO_QC_NOP_Q1A = "auto_qc_nop_Q1a"
    AUTO_QC_NOP_Q7A = "auto_qc_nop_Q7a"
    AUTO_QC_NOP_Q7B = "auto_qc_nop_Q7b"
    AUTO_QC_NOP_Q8A = "auto_qc_nop_Q8a"
    AUTO_QC_PROJ_Q17B = "auto_qc_proj_Q17b"
    AUTO_QC_PROJ_Q18A = "auto_qc_proj_Q18a"
    AUTO_QC_PROJ_Q19C = "auto_qc_proj_Q19c"
    AUTO_QC_PROJ_Q21B = "auto_qc_proj_Q21b"

    @property
    def label(self) -> str:
        return _QUERY_FAMILY_LABELS[self]


_QUERY_FAMILY_LABELS: dict[QueryFamily, str] = {
    QueryFamily.BRANCHING: "Branching",
    QueryFamily.BRANCHING_LOCAL: "Branching (local)",
    QueryFamily.CHAIN: "Chain",
    QueryFamily.CHAIN_LOCAL: "Chain (local)",
    QueryFamily.STAR: "Star",
    QueryFamily.STAR_LOCAL: "Star (local)",
    QueryFamily.UCFQ: "UCFQ",
    QueryFamily.SERVICE_S2: "Service S2",
    QueryFamily.SERVICE_S4: "Service S4",
    QueryFamily.SERVICE_S5: "Service S5",
    QueryFamily.SERVICE_S11: "Service S11",
    QueryFamily.SERVICE_S12: "Service S12",
    QueryFamily.AUTO_QC_NOP_Q0A: "Auto QC nop Q0a",
    QueryFamily.AUTO_QC_NOP_Q0B: "Auto QC nop Q0b",
    QueryFamily.AUTO_QC_NOP_Q0C: "Auto QC nop Q0c",
    QueryFamily.AUTO_QC_NOP_Q1A: "Auto QC nop Q1a",
    QueryFamily.AUTO_QC_NOP_Q7A: "Auto QC nop Q7a",
    QueryFamily.AUTO_QC_NOP_Q7B: "Auto QC nop Q7b",
    QueryFamily.AUTO_QC_NOP_Q8A: "Auto QC nop Q8a",
    QueryFamily.AUTO_QC_PROJ_Q17B: "Auto QC proj Q17b",
    QueryFamily.AUTO_QC_PROJ_Q18A: "Auto QC proj Q18a",
    QueryFamily.AUTO_QC_PROJ_Q19C: "Auto QC proj Q19c",
    QueryFamily.AUTO_QC_PROJ_Q21B: "Auto QC proj Q21b",
}


class Verdict(StrEnum):
    CONTAINED = "contained"
    NOT_CONTAINED = "not contained"


class ContainmentResult(StrEnum):
    """Every value the `verdict` field can take across all PairResult variants."""

    CONTAINED = "contained"
    NOT_CONTAINED = "not contained"
    UNKNOWN = "unknown"
    TIMEOUT = "timeout"
    OUT_OF_MEMORY = "out of memory"
    ERROR = "error"


class Outcome(StrEnum):
    CORRECT = "correct"
    INCORRECT = "incorrect"
    ERROR = "error"
    UNKNOWN = "unknown"
    TIMEOUT = "timeout"
    OUT_OF_MEMORY = "out of memory"


TimedVerdict = Literal[
    ContainmentResult.CONTAINED,
    ContainmentResult.NOT_CONTAINED,
    ContainmentResult.UNKNOWN,
    ContainmentResult.OUT_OF_MEMORY,
]
TimedOutcome = Literal[
    Outcome.CORRECT,
    Outcome.INCORRECT,
    Outcome.UNKNOWN,
    Outcome.OUT_OF_MEMORY,
]


class TimedResult(TypedDict):
    expected: Verdict
    verdict: TimedVerdict
    outcome: TimedOutcome
    meanMs: float
    medianMs: float
    ms: list[float]


class TimedOutResult(TypedDict):
    expected: Verdict
    verdict: Literal[ContainmentResult.TIMEOUT]
    outcome: Literal[Outcome.TIMEOUT]


class ErroredResult(TypedDict):
    expected: Verdict
    verdict: Literal[ContainmentResult.ERROR]
    outcome: Literal[Outcome.ERROR]
    reason: str


PairResult = TimedResult | TimedOutResult | ErroredResult


class Env(TypedDict):
    platform: str
    cpu: str
    cpuCount: int
    memBytes: int
    bun: str
    docker: str
    specsImageId: str
    z3: str


class RunContext(TypedDict):
    engine: EngineName
    suite: str
    startedAt: str
    finishedAt: str
    repetitions: int
    warmup: int
    timeoutMs: int
    memoryMb: int
    env: Env


class Bucket(TypedDict):
    count: int
    ids: list[str]


class Aggregate(TypedDict, total=False):
    meanMs: float
    medianMs: float


class _SummaryRequired(TypedDict):
    total: int
    correct: int
    incorrect: Bucket
    unknown: Bucket
    timeout: Bucket
    outOfMemory: Bucket
    error: Bucket


class Summary(_SummaryRequired, total=False):
    meanMs: float
    medianMs: float
    bySize: dict[str, Aggregate]


class ResultFile(TypedDict):
    meta: RunContext
    summary: Summary
    results: dict[str, PairResult]
