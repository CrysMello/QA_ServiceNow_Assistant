"""Workflow Engine exceptions (SAD Cap. 12)."""

from __future__ import annotations

from qa_servicenow_assistant.domain.exceptions.base import QaServiceNowAssistantError


class WorkflowError(QaServiceNowAssistantError):
    """Base exception for workflow orchestration failures."""


class InvalidWorkflowError(WorkflowError):
    """Raised when WorkflowEngine.execute() is asked to run a malformed
    Workflow: no steps, or duplicate step keys. A caller-contract
    violation, not an operational failure - never caught internally,
    always propagates. Step-level failures (precondition/action/
    postcondition) are NOT modeled as exceptions - see WorkflowResult.
    """
