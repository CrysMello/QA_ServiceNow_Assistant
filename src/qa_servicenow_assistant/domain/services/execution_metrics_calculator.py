"""ExecutionMetricsCalculator: pure domain service computing aggregate
indicators over recorded executions (SAD 22.3 - "Metrics Calculator:
Calcular metricas e indicadores. Dependencias: Execution Collector";
SAD 22.7 - Metricas Produzidas).

No I/O here (SAD 8.7); ReportingEngine supplies the ExecutionResult
history it has collected so far (its own in-memory "Execution Collector").
"""

from __future__ import annotations

from typing import Sequence

from qa_servicenow_assistant.domain.value_objects.execution_metrics import (
    ExecutionMetrics,
)
from qa_servicenow_assistant.domain.value_objects.execution_result import (
    ExecutionResult,
)
from qa_servicenow_assistant.domain.value_objects.execution_status import (
    ExecutionStatus,
)


class ExecutionMetricsCalculator:
    def calculate(self, results: Sequence[ExecutionResult]) -> ExecutionMetrics:
        total = len(results)
        if total == 0:
            return ExecutionMetrics(
                total_executions=0,
                success_count=0,
                failure_count=0,
                cancelled_count=0,
                success_rate=0.0,
                failure_rate=0.0,
                average_duration_ms=0.0,
                total_retry_attempts=0,
                total_checkpoints_used=0,
                total_evidence_count=0,
            )

        success_count = sum(1 for r in results if r.status == ExecutionStatus.SUCCESS)
        failure_count = sum(1 for r in results if r.status == ExecutionStatus.FAILURE)
        cancelled_count = sum(1 for r in results if r.status == ExecutionStatus.CANCELLED)

        return ExecutionMetrics(
            total_executions=total,
            success_count=success_count,
            failure_count=failure_count,
            cancelled_count=cancelled_count,
            success_rate=success_count / total,
            failure_rate=failure_count / total,
            average_duration_ms=sum(r.duration_ms for r in results) / total,
            total_retry_attempts=sum(r.retry_attempts for r in results),
            total_checkpoints_used=sum(r.checkpoints_used for r in results),
            total_evidence_count=sum(len(r.evidence) for r in results),
        )
