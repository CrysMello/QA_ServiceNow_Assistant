"""Unit tests for ExecutionMetricsCalculator (SAD 22.7 - Metricas Produzidas)."""

from __future__ import annotations

from qa_servicenow_assistant.domain.services.execution_metrics_calculator import (
    ExecutionMetricsCalculator,
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


def make_result(**overrides: object) -> ExecutionResult:
    defaults: dict[str, object] = dict(
        execution_id="exec-1",
        workflow_id="workflow-1",
        status=ExecutionStatus.SUCCESS,
        duration_ms=1000.0,
    )
    defaults.update(overrides)
    return ExecutionResult(**defaults)  # type: ignore[arg-type]


def test_empty_sequence_returns_zeroed_metrics() -> None:
    calculator = ExecutionMetricsCalculator()

    metrics = calculator.calculate([])

    assert metrics.total_executions == 0
    assert metrics.success_rate == 0.0
    assert metrics.failure_rate == 0.0
    assert metrics.average_duration_ms == 0.0


def test_counts_and_rates_across_mixed_statuses() -> None:
    calculator = ExecutionMetricsCalculator()
    results = [
        make_result(execution_id="e1", status=ExecutionStatus.SUCCESS, duration_ms=1000.0),
        make_result(execution_id="e2", status=ExecutionStatus.SUCCESS, duration_ms=2000.0),
        make_result(execution_id="e3", status=ExecutionStatus.FAILURE, duration_ms=3000.0),
        make_result(execution_id="e4", status=ExecutionStatus.CANCELLED, duration_ms=4000.0),
    ]

    metrics = calculator.calculate(results)

    assert metrics.total_executions == 4
    assert metrics.success_count == 2
    assert metrics.failure_count == 1
    assert metrics.cancelled_count == 1
    assert metrics.success_rate == 0.5
    assert metrics.failure_rate == 0.25
    assert metrics.average_duration_ms == 2500.0


def test_sums_retries_checkpoints_and_evidence() -> None:
    calculator = ExecutionMetricsCalculator()
    results = [
        make_result(
            execution_id="e1",
            retry_attempts=2,
            checkpoints_used=1,
            evidence=(EvidenceReference("before", "a.png"), EvidenceReference("after", "b.png")),
        ),
        make_result(execution_id="e2", retry_attempts=3, checkpoints_used=0, evidence=()),
    ]

    metrics = calculator.calculate(results)

    assert metrics.total_retry_attempts == 5
    assert metrics.total_checkpoints_used == 1
    assert metrics.total_evidence_count == 2
