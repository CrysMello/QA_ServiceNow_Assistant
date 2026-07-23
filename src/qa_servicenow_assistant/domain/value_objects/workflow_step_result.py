"""Per-step outcome record kept in a WorkflowResult (SAD Cap. 12)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class WorkflowStepOutcome(str, Enum):
    SUCCEEDED = "succeeded"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass(frozen=True)
class WorkflowStepResult:
    """detail carries either an error explanation (outcome=FAILED) or a
    skip reason (outcome=SKIPPED, e.g. "already completed, resumed from
    checkpoint") - None when outcome=SUCCEEDED."""

    step_key: str
    outcome: WorkflowStepOutcome
    detail: str | None = None
