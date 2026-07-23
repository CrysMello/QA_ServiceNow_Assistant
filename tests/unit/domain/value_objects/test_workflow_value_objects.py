"""Unit tests for the Workflow Engine value objects (SAD Cap. 12)."""

from __future__ import annotations

import pytest

from qa_servicenow_assistant.domain.value_objects.execution_context import (
    ExecutionContext,
)
from qa_servicenow_assistant.domain.value_objects.workflow import Workflow
from qa_servicenow_assistant.domain.value_objects.workflow_result import WorkflowResult
from qa_servicenow_assistant.domain.value_objects.workflow_state import WorkflowState
from qa_servicenow_assistant.domain.value_objects.workflow_step import WorkflowStep
from qa_servicenow_assistant.domain.value_objects.workflow_step_result import (
    WorkflowStepOutcome,
    WorkflowStepResult,
)


def test_execution_context_defaults_to_empty_data() -> None:
    context = ExecutionContext(execution_id="exec-1", workflow_id="workflow-1")

    assert context.data == {}


def test_execution_context_is_mutable() -> None:
    context = ExecutionContext(execution_id="exec-1", workflow_id="workflow-1")

    context.data["incident_number"] = "INC0010001"

    assert context.data["incident_number"] == "INC0010001"


def test_workflow_step_defaults() -> None:
    step = WorkflowStep(key="fill_form", description="Fill the form", action=lambda ctx: None)

    assert step.preconditions == ()
    assert step.postconditions == ()


def test_workflow_step_is_frozen() -> None:
    step = WorkflowStep(key="fill_form", description="Fill the form", action=lambda ctx: None)

    with pytest.raises(AttributeError):
        step.key = "other"  # type: ignore[misc]


def test_workflow_holds_ordered_steps() -> None:
    step_a = WorkflowStep(key="a", description="A", action=lambda ctx: None)
    step_b = WorkflowStep(key="b", description="B", action=lambda ctx: None)

    workflow = Workflow(key="wf", description="Workflow", steps=(step_a, step_b))

    assert workflow.steps == (step_a, step_b)


def test_workflow_step_result_defaults() -> None:
    result = WorkflowStepResult(step_key="a", outcome=WorkflowStepOutcome.SUCCEEDED)

    assert result.detail is None


def test_workflow_result_is_frozen() -> None:
    result = WorkflowResult(
        execution_id="exec-1",
        workflow_key="wf",
        final_state=WorkflowState.COMPLETED,
        step_results=(),
    )

    with pytest.raises(AttributeError):
        result.final_state = WorkflowState.FAILED  # type: ignore[misc]
