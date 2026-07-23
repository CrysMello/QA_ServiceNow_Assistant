"""Unit tests for the ExecutionResult value object (SAD 22.4)."""

from __future__ import annotations

from datetime import datetime

import pytest

from qa_servicenow_assistant.domain.value_objects.execution_result import (
    ExecutionResult,
)
from qa_servicenow_assistant.domain.value_objects.execution_status import (
    ExecutionStatus,
)


def test_defaults_are_applied() -> None:
    result = ExecutionResult(
        execution_id="exec-1",
        workflow_id="workflow-1",
        status=ExecutionStatus.SUCCESS,
        duration_ms=100.0,
    )

    assert result.evidence == ()
    assert result.log_summary == ()
    assert result.errors == ()
    assert result.retry_attempts == 0
    assert result.checkpoints_used == 0
    assert isinstance(result.completed_at, datetime)


def test_is_frozen() -> None:
    result = ExecutionResult(
        execution_id="exec-1",
        workflow_id="workflow-1",
        status=ExecutionStatus.SUCCESS,
        duration_ms=100.0,
    )

    with pytest.raises(AttributeError):
        result.status = ExecutionStatus.FAILURE  # type: ignore[misc]
