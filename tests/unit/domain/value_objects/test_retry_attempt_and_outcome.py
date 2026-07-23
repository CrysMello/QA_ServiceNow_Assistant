"""Unit tests for RetryAttempt and RetryOutcome value objects (SAD 19.3)."""

from __future__ import annotations

import pytest

from qa_servicenow_assistant.domain.value_objects.failure_classification import (
    FailureClassification,
)
from qa_servicenow_assistant.domain.value_objects.retry_attempt import RetryAttempt
from qa_servicenow_assistant.domain.value_objects.retry_outcome import RetryOutcome


def test_retry_attempt_success_has_no_classification_or_error() -> None:
    attempt = RetryAttempt(attempt_number=1, succeeded=True)

    assert attempt.attempt_number == 1
    assert attempt.succeeded is True
    assert attempt.classification is None
    assert attempt.error_message is None


def test_retry_attempt_failure_carries_classification_and_error() -> None:
    attempt = RetryAttempt(
        attempt_number=2,
        succeeded=False,
        classification=FailureClassification.TRANSIENT,
        error_message="boom",
    )

    assert attempt.succeeded is False
    assert attempt.classification == FailureClassification.TRANSIENT
    assert attempt.error_message == "boom"


def test_retry_attempt_is_frozen() -> None:
    attempt = RetryAttempt(attempt_number=1, succeeded=True)

    with pytest.raises(AttributeError):
        attempt.succeeded = False  # type: ignore[misc]


def test_retry_outcome_success_carries_result() -> None:
    attempts = (RetryAttempt(attempt_number=1, succeeded=True),)

    outcome = RetryOutcome(succeeded=True, attempts=attempts, result="value")

    assert outcome.succeeded is True
    assert outcome.result == "value"
    assert outcome.final_error_message is None
    assert outcome.attempts == attempts


def test_retry_outcome_failure_carries_final_error_message() -> None:
    attempts = (
        RetryAttempt(
            attempt_number=1,
            succeeded=False,
            classification=FailureClassification.PERMANENT,
            error_message="fatal",
        ),
    )

    outcome = RetryOutcome(succeeded=False, attempts=attempts, final_error_message="fatal")

    assert outcome.succeeded is False
    assert outcome.result is None
    assert outcome.final_error_message == "fatal"


def test_retry_outcome_is_frozen() -> None:
    outcome = RetryOutcome(succeeded=True, attempts=())

    with pytest.raises(AttributeError):
        outcome.succeeded = False  # type: ignore[misc]
