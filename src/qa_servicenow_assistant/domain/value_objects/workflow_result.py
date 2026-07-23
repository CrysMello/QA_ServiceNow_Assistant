"""Outcome of WorkflowEngine.execute() (SAD Cap. 12)."""

from __future__ import annotations

from dataclasses import dataclass

from qa_servicenow_assistant.domain.value_objects.workflow_state import WorkflowState
from qa_servicenow_assistant.domain.value_objects.workflow_step_result import (
    WorkflowStepResult,
)


@dataclass(frozen=True)
class WorkflowResult:
    """Never raised for expected failures (a step's precondition,
    action or postcondition failing) - consistent with the majority
    structured-result pattern used across this codebase.
    InvalidWorkflowError is the exception, reserved for caller-contract
    violations (an empty workflow or duplicate step keys)."""

    execution_id: str
    workflow_key: str
    final_state: WorkflowState
    step_results: tuple[WorkflowStepResult, ...]
    error_message: str | None = None
