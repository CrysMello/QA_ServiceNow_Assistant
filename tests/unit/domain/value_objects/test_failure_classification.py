"""Unit tests for the FailureClassification enum (SAD 19.2, 19.6)."""

from __future__ import annotations

from qa_servicenow_assistant.domain.value_objects.failure_classification import (
    FailureClassification,
)


def test_has_exactly_transient_and_permanent_members() -> None:
    assert {member.value for member in FailureClassification} == {"transient", "permanent"}


def test_is_a_str_enum() -> None:
    assert FailureClassification.TRANSIENT == "transient"
    assert FailureClassification.PERMANENT == "permanent"
