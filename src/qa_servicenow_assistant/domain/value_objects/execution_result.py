"""ExecutionResult: consolidated execution information (SAD 22.4 -
Informacoes Consolidadas) submitted to the Reporting Engine.

Reporting Engine "nao implementa regras de negocio" (SAD 22.8) and has no
Workflow Engine, Retry Engine or Checkpoint Engine dependency of its own
(SAD 22.3 lists Workflow Engine as the real source of this data) - a
future Workflow Engine is responsible for assembling one of these per
completed execution and handing it to ReportingEngine.record_execution()/
generate_report(). retry_attempts and checkpoints_used are therefore
caller-supplied plain counts (not live references to RetryEngine/
CheckpointEngine instances), consistent with how RecordedElement and
Checkpoint take a caller-supplied execution_id instead of depending on
whatever module owns execution lifecycle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from qa_servicenow_assistant.domain.value_objects.evidence_reference import (
    EvidenceReference,
)
from qa_servicenow_assistant.domain.value_objects.execution_status import (
    ExecutionStatus,
)


@dataclass(frozen=True)
class ExecutionResult:
    execution_id: str
    workflow_id: str
    status: ExecutionStatus
    duration_ms: float
    evidence: tuple[EvidenceReference, ...] = ()
    log_summary: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    retry_attempts: int = 0
    checkpoints_used: int = 0
    completed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
