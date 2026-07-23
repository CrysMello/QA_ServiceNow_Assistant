"""RetryOutcome: final result of RetryEngine.execute() (SAD Cap. 19)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from qa_servicenow_assistant.domain.value_objects.retry_attempt import RetryAttempt

T = TypeVar("T")


@dataclass(frozen=True)
class RetryOutcome(Generic[T]):
    """Immutable outcome of executing an operation under a retry policy.

    Never raised as an exception path for expected outcomes (permanent
    failure, attempts exhausted) - consistent with Navigation Engine,
    Page Recognition and Selector Resolver (SAD Cap. 19 has no equivalent
    to SAD 18.8's explicit exception mandate for Frame Resolver).
    """

    succeeded: bool
    attempts: tuple[RetryAttempt, ...]
    result: T | None = None
    final_error_message: str | None = None
