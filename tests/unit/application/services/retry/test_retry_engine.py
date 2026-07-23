"""Unit tests for RetryEngine (SAD Cap. 19).

Uses a fake LogPort (same pattern as NavigationEngine's tests) and an
injectable `sleep` callable so unit tests never incur real delays, even
when exercising the `linear`/`exponential` backoff policies.
"""

from __future__ import annotations

from typing import Any

import pytest

from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.application.services.retry.retry_engine import (
    RetryEngine,
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


class FakeLogPort(LogPort):
    def __init__(self) -> None:
        self.warning_calls: list[tuple[str, dict[str, Any]]] = []
        self.info_calls: list[tuple[str, dict[str, Any]]] = []
        self.error_calls: list[tuple[str, dict[str, Any]]] = []

    def bind(self, **context: Any) -> "FakeLogPort":
        return self

    def trace(self, message: str, **context: Any) -> None:
        pass

    def debug(self, message: str, **context: Any) -> None:
        pass

    def info(self, message: str, **context: Any) -> None:
        self.info_calls.append((message, context))

    def warning(self, message: str, **context: Any) -> None:
        self.warning_calls.append((message, context))

    def error(self, message: str, **context: Any) -> None:
        self.error_calls.append((message, context))

    def critical(self, message: str, **context: Any) -> None:
        pass


class TransientError(Exception):
    pass


class PermanentError(Exception):
    pass


def make_engine(
    *,
    max_attempts: int = 3,
    backoff_strategy: str = "none",
    base_delay_ms: int = 2_000,
    log_port: FakeLogPort | None = None,
) -> tuple[RetryEngine, FakeLogPort, list[float]]:
    log_port = log_port or FakeLogPort()
    classifier = FailureClassifier()
    classifier.register(TransientError, FailureClassification.TRANSIENT)
    classifier.register(PermanentError, FailureClassification.PERMANENT)

    sleeps: list[float] = []
    configuration = RetryConfiguration(
        max_attempts=max_attempts,
        backoff_strategy=backoff_strategy,
        base_delay_ms=base_delay_ms,
    )
    engine = RetryEngine(
        log_port=log_port,
        configuration=configuration,
        classifier=classifier,
        sleep=sleeps.append,
    )
    return engine, log_port, sleeps


def test_succeeds_on_first_attempt_without_retrying() -> None:
    engine, log_port, sleeps = make_engine()
    calls: list[int] = []

    def operation() -> str:
        calls.append(1)
        return "ok"

    outcome = engine.execute(operation, operation_name="op")

    assert outcome.succeeded is True
    assert outcome.result == "ok"
    assert len(calls) == 1
    assert len(outcome.attempts) == 1
    assert outcome.attempts[0].succeeded is True
    assert sleeps == []
    assert log_port.info_calls == []  # no "Retry succeeded" log on first-try success


def test_retries_transient_failure_then_succeeds() -> None:
    engine, log_port, sleeps = make_engine(max_attempts=3, backoff_strategy="fixed", base_delay_ms=1_000)
    calls: list[int] = []

    def operation() -> str:
        calls.append(1)
        if len(calls) < 2:
            raise TransientError("temporary glitch")
        return "recovered"

    outcome = engine.execute(operation, operation_name="op")

    assert outcome.succeeded is True
    assert outcome.result == "recovered"
    assert len(calls) == 2
    assert len(outcome.attempts) == 2
    assert outcome.attempts[0].succeeded is False
    assert outcome.attempts[0].classification == FailureClassification.TRANSIENT
    assert outcome.attempts[1].succeeded is True
    assert sleeps == [1.0]  # one wait between attempt 1 and 2
    assert len(log_port.warning_calls) == 1
    assert len(log_port.info_calls) == 1  # "Retry succeeded"


def test_stops_immediately_on_permanent_failure_without_exhausting_attempts() -> None:
    engine, log_port, sleeps = make_engine(max_attempts=5)
    calls: list[int] = []

    def operation() -> str:
        calls.append(1)
        raise PermanentError("fatal misconfiguration")

    outcome = engine.execute(operation, operation_name="op")

    assert outcome.succeeded is False
    assert outcome.result is None
    assert outcome.final_error_message == "fatal misconfiguration"
    assert len(calls) == 1  # never retried
    assert len(outcome.attempts) == 1
    assert outcome.attempts[0].classification == FailureClassification.PERMANENT
    assert sleeps == []
    assert len(log_port.error_calls) == 1


def test_gives_up_after_max_attempts_of_transient_failures() -> None:
    engine, log_port, sleeps = make_engine(max_attempts=3, backoff_strategy="none")
    calls: list[int] = []

    def operation() -> str:
        calls.append(1)
        raise TransientError("still broken")

    outcome = engine.execute(operation, operation_name="op")

    assert outcome.succeeded is False
    assert outcome.final_error_message == "still broken"
    assert len(calls) == 3
    assert len(outcome.attempts) == 3
    assert all(not attempt.succeeded for attempt in outcome.attempts)
    assert len(log_port.error_calls) == 1


def test_unknown_exception_defaults_to_permanent_and_stops() -> None:
    engine, _log_port, _sleeps = make_engine(max_attempts=5)
    calls: list[int] = []

    def operation() -> str:
        calls.append(1)
        raise ValueError("never registered")

    outcome = engine.execute(operation, operation_name="op")

    assert outcome.succeeded is False
    assert len(calls) == 1
    assert outcome.attempts[0].classification == FailureClassification.PERMANENT


def test_exponential_backoff_delays_grow_between_attempts() -> None:
    engine, _log_port, sleeps = make_engine(max_attempts=4, backoff_strategy="exponential", base_delay_ms=2_000)

    def operation() -> str:
        raise TransientError("always fails")

    engine.execute(operation, operation_name="op")

    # base=2000ms -> 2s, 4s, 8s between the 4 attempts (3 waits)
    assert sleeps == [2.0, 4.0, 8.0]
