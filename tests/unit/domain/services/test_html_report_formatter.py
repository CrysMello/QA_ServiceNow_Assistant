"""Unit tests for HtmlReportFormatter (SAD 22.5)."""

from __future__ import annotations

from qa_servicenow_assistant.domain.services.html_report_formatter import (
    HtmlReportFormatter,
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


def test_format_embeds_core_fields() -> None:
    formatter = HtmlReportFormatter()
    result = ExecutionResult(
        execution_id="exec-1",
        workflow_id="workflow-1",
        status=ExecutionStatus.SUCCESS,
        duration_ms=1500.0,
        evidence=(EvidenceReference("before_submit", "a.png"),),
        log_summary=("step completed",),
        errors=(),
    )

    html = formatter.format(result)

    assert "exec-1" in html
    assert "workflow-1" in html
    assert "success" in html
    assert "1500.0" in html
    assert "before_submit" in html
    assert "a.png" in html
    assert "step completed" in html
    assert "<li>(none)</li>" in html  # empty errors section


def test_format_escapes_html_special_characters_in_data() -> None:
    formatter = HtmlReportFormatter()
    result = ExecutionResult(
        execution_id="exec-<script>1",
        workflow_id="workflow-1",
        status=ExecutionStatus.FAILURE,
        duration_ms=0.0,
        errors=("<script>alert('xss')</script>",),
    )

    html = formatter.format(result)

    assert "<script>alert" not in html
    assert "&lt;script&gt;" in html


def test_format_produces_well_formed_html_document() -> None:
    formatter = HtmlReportFormatter()
    result = ExecutionResult(
        execution_id="exec-1",
        workflow_id="workflow-1",
        status=ExecutionStatus.SUCCESS,
        duration_ms=0.0,
    )

    html = formatter.format(result)

    assert html.startswith("<!doctype html>")
    assert "<html" in html
    assert "</html>" in html
