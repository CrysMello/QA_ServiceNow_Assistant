"""Unit tests for JsonReportFormatter (SAD 22.5)."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from qa_servicenow_assistant.domain.services.json_report_formatter import (
    JsonReportFormatter,
)
from qa_servicenow_assistant.domain.value_objects.evidence_reference import (
    EvidenceReference,
)
from qa_servicenow_assistant.domain.value_objects.execution_result import (
    ExecutionResult,
)
from qa_servicenow_assistant.domain.value_objects.execution_status import (
    ExecutionStatus,
)


def test_format_produces_valid_json_with_all_fields() -> None:
    formatter = JsonReportFormatter()
    result = ExecutionResult(
        execution_id="exec-1",
        workflow_id="workflow-1",
        status=ExecutionStatus.FAILURE,
        duration_ms=1234.5,
        evidence=(EvidenceReference("validation_failure", "screenshots/exec-1/step2.png"),),
        log_summary=("Navigated to incident form", "Validation failed"),
        errors=("Element not found: #short_description",),
        retry_attempts=2,
        checkpoints_used=1,
        completed_at=datetime(2026, 7, 22, 10, 0, 0, tzinfo=timezone.utc),
    )

    content = formatter.format(result)
    data = json.loads(content)

    assert data["execution_id"] == "exec-1"
    assert data["workflow_id"] == "workflow-1"
    assert data["status"] == "failure"
    assert data["duration_ms"] == 1234.5
    assert data["evidence"] == [
        {"description": "validation_failure", "path": "screenshots/exec-1/step2.png"}
    ]
    assert data["log_summary"] == ["Navigated to incident form", "Validation failed"]
    assert data["errors"] == ["Element not found: #short_description"]
    assert data["retry_attempts"] == 2
    assert data["checkpoints_used"] == 1
    assert data["completed_at"] == "2026-07-22T10:00:00+00:00"


def test_format_handles_empty_collections() -> None:
    formatter = JsonReportFormatter()
    result = ExecutionResult(
        execution_id="exec-1",
        workflow_id="workflow-1",
        status=ExecutionStatus.SUCCESS,
        duration_ms=100.0,
    )

    data = json.loads(formatter.format(result))

    assert data["evidence"] == []
    assert data["log_summary"] == []
    assert data["errors"] == []
