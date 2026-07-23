"""RetryAttempt: record of a single attempt (SAD 19.3 - Retry History)."""

from __future__ import annotations

from dataclasses import dataclass

from qa_servicenow_assistant.domain.value_objects.failure_classification import (
    FailureClassification,
)


@dataclass(frozen=True)
class RetryAttempt:
    """Immutable record of one attempt made by RetryEngine.execute()."""

    attempt_number: int
    succeeded: bool
    classification: FailureClassification | None = None
    error_message: str | None = None
