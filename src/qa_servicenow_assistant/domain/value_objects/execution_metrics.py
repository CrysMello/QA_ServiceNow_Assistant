"""ExecutionMetrics: aggregate indicators produced by
ExecutionMetricsCalculator (SAD 22.7 - Metricas Produzidas)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionMetrics:
    total_executions: int
    success_count: int
    failure_count: int
    cancelled_count: int
    success_rate: float
    failure_rate: float
    average_duration_ms: float
    total_retry_attempts: int
    total_checkpoints_used: int
    total_evidence_count: int
