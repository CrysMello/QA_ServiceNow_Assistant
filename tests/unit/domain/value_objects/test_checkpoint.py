"""Unit tests for the Checkpoint value object (SAD 20.4)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from qa_servicenow_assistant.domain.value_objects.checkpoint import Checkpoint


def test_defaults_are_applied() -> None:
    checkpoint = Checkpoint(
        execution_id="exec-1", workflow_id="workflow-1", last_completed_step="start"
    )

    assert checkpoint.page is None
    assert checkpoint.temporary_data == {}
    assert checkpoint.partial_result == ""
    assert isinstance(checkpoint.created_at, datetime)
    assert checkpoint.created_at.tzinfo is not None


def test_is_frozen() -> None:
    checkpoint = Checkpoint(
        execution_id="exec-1", workflow_id="workflow-1", last_completed_step="start"
    )

    with pytest.raises(AttributeError):
        checkpoint.last_completed_step = "other"  # type: ignore[misc]


def test_explicit_created_at_is_kept() -> None:
    timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)

    checkpoint = Checkpoint(
        execution_id="exec-1",
        workflow_id="workflow-1",
        last_completed_step="start",
        created_at=timestamp,
    )

    assert checkpoint.created_at == timestamp
