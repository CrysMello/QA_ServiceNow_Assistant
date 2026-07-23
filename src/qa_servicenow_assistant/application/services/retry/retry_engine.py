"""Retry Engine (SAD Cap. 19).

Executes an arbitrary zero-argument operation under a configurable retry
policy: classifies each failure (FailureClassifier), stops immediately on
permanent failures (SAD 19.8 - "falhas permanentes nao devem ser
repetidas"), waits according to the configured backoff strategy
(BackoffCalculator) between transient-failure retries, and logs every
attempt (SAD 19.2 - "registrar historico das tentativas").

Retry Engine does not know WHAT operation it retries - callers (future
Workflow Engine, Navigation Engine, Automation Engine) pass a callable.
This keeps it free of business rules (SAD 19.8) and reusable everywhere.

No checkpoint restoration is performed before a retry (SAD 19.7 lists
Checkpoint Engine as an integration point) - Checkpoint Engine does not
exist yet (a later prompt); this is a documented, deliberate scope
boundary, not an oversight.
"""

from __future__ import annotations

import time
from typing import Any, Callable, TypeVar

from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.domain.services.backoff_calculator import (
    BackoffCalculator,
)
from qa_servicenow_assistant.domain.services.failure_classifier import (
    FailureClassifier,
)
from qa_servicenow_assistant.domain.value_objects.configuration import (
    RetryConfiguration,
)
from qa_servicenow_assistant.domain.value_objects.failure_classification import (
    FailureClassification,
)
from qa_servicenow_assistant.domain.value_objects.retry_attempt import RetryAttempt
from qa_servicenow_assistant.domain.value_objects.retry_outcome import RetryOutcome

T = TypeVar("T")


class RetryEngine:
    """Runs operation() up to configuration.max_attempts times, retrying
    only on transient failures, with configured backoff between tries."""

    def __init__(
        self,
        log_port: LogPort,
        configuration: RetryConfiguration | None = None,
        classifier: FailureClassifier | None = None,
        backoff_calculator: BackoffCalculator | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._log_port = log_port
        self._configuration = configuration or RetryConfiguration()
        self._classifier = classifier or FailureClassifier()
        self._backoff_calculator = backoff_calculator or BackoffCalculator()
        self._sleep = sleep

    def execute(self, operation: Callable[[], T], *, operation_name: str) -> RetryOutcome[T]:
        max_attempts = self._configuration.max_attempts
        attempts: list[RetryAttempt] = []

        for attempt_number in range(1, max_attempts + 1):
            # Deliberate, narrow exception isolation boundary (same
            # pattern as InMemoryEventBus._invoke_handler): Retry Engine
            # is reusable across every future caller and cannot know in
            # advance which exception types a given operation may raise.
            # The failure is never discarded - it is classified, recorded
            # in `attempts`, and always logged before any decision is made.
            try:
                result = operation()
            except Exception as error:  # noqa: BLE001 - intentional isolation boundary
                classification = self._classifier.classify(error)
                attempts.append(
                    RetryAttempt(
                        attempt_number=attempt_number,
                        succeeded=False,
                        classification=classification,
                        error_message=str(error),
                    )
                )
                self._log_port.warning(
                    "Retry attempt failed",
                    operation=operation_name,
                    attempt_number=attempt_number,
                    max_attempts=max_attempts,
                    classification=classification.value,
                    error_type=type(error).__name__,
                    error=str(error),
                )

                if classification == FailureClassification.PERMANENT:
                    return self._give_up(operation_name, attempts, str(error), reason="permanent failure")

                if attempt_number == max_attempts:
                    return self._give_up(operation_name, attempts, str(error), reason="max attempts reached")

                self._wait_before_next_attempt(attempt_number)
            else:
                attempts.append(RetryAttempt(attempt_number=attempt_number, succeeded=True))
                if attempt_number > 1:
                    self._log_port.info(
                        "Retry succeeded",
                        operation=operation_name,
                        attempt_number=attempt_number,
                        max_attempts=max_attempts,
                    )
                return RetryOutcome(succeeded=True, attempts=tuple(attempts), result=result)

        # Unreachable: max_attempts >= 1 is guaranteed by
        # ConfigurationValidator, so the loop always returns above.
        return RetryOutcome(succeeded=False, attempts=tuple(attempts), final_error_message="No attempts executed")

    def _wait_before_next_attempt(self, attempt_number: int) -> None:
        delay_ms = self._backoff_calculator.compute_delay_ms(self._configuration, attempt_number)
        if delay_ms > 0:
            self._sleep(delay_ms / 1000)

    def _give_up(
        self,
        operation_name: str,
        attempts: list[RetryAttempt],
        error_message: str,
        *,
        reason: str,
    ) -> RetryOutcome[Any]:
        self._log_port.error(
            f"Retry stopped: {reason}",
            operation=operation_name,
            attempts_made=len(attempts),
        )
        return RetryOutcome(succeeded=False, attempts=tuple(attempts), final_error_message=error_message)
