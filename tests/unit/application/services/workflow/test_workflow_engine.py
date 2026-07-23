"""Unit tests for WorkflowEngine (SAD Cap. 12).

Uses a fake LogPort plus REAL RetryEngine/CheckpointEngine/ReportingEngine
instances (each backed by a fake repository port), since their own
behavior is already covered by their dedicated test suites and using the
real classes here gives genuine confidence that WorkflowEngine wires them
correctly - the same "fakes at the infrastructure boundary" philosophy
used by every other engine's tests in this codebase.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import pytest

from qa_servicenow_assistant.application.ports.checkpoint_repository_port import (
    CheckpointRepositoryPort,
)
from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.application.ports.report_repository_port import (
    ReportRepositoryPort,
)
from qa_servicenow_assistant.application.services.checkpoint.checkpoint_engine import (
    CheckpointEngine,
)
from qa_servicenow_assistant.application.services.reporting.reporting_engine import (
    ReportingEngine,
)
from qa_servicenow_assistant.application.services.retry.retry_engine import RetryEngine
from qa_servicenow_assistant.application.services.workflow.workflow_engine import (
    WorkflowEngine,
)
from qa_servicenow_assistant.domain.exceptions.workflow import InvalidWorkflowError
from qa_servicenow_assistant.domain.services.failure_classifier import (
    FailureClassifier,
)
from qa_servicenow_assistant.domain.value_objects.checkpoint import Checkpoint
from qa_servicenow_assistant.domain.value_objects.configuration import (
    RetryConfiguration,
)
from qa_servicenow_assistant.domain.value_objects.failure_classification import (
    FailureClassification,
)
from qa_servicenow_assistant.domain.value_objects.execution_context import (
    ExecutionContext,
)
from qa_servicenow_assistant.domain.value_objects.workflow import Workflow
from qa_servicenow_assistant.domain.value_objects.workflow_state import WorkflowState
from qa_servicenow_assistant.domain.value_objects.workflow_step import WorkflowStep
from qa_servicenow_assistant.domain.value_objects.workflow_step_result import (
    WorkflowStepOutcome,
)


class FakeLogPort(LogPort):
    def __init__(self) -> None:
        self.info_calls: list[tuple[str, dict[str, Any]]] = []
        self.warning_calls: list[tuple[str, dict[str, Any]]] = []
        self.error_calls: list[tuple[str, dict[str, Any]]] = []

    def bind(self, **context: Any) -> "FakeLogPort":
        return self

    def trace(self, message: str, **context: Any) -> None:
        pass

    def debug(self, message: str, **context: Any) -> None:
        pass

    def info(self, message: str, **context: Any) -> None:
        self.info_calls.append((message, context))

    def warning(self, message: str, **context: Any) -> None:
        self.warning_calls.append((message, context))

    def error(self, message: str, **context: Any) -> None:
        self.error_calls.append((message, context))

    def critical(self, message: str, **context: Any) -> None:
        pass


class FakeCheckpointRepository(CheckpointRepositoryPort):
    def __init__(self) -> None:
        self._history: list[Checkpoint] = []

    def save(self, checkpoint: Checkpoint) -> None:
        self._history.append(checkpoint)

    def latest_for_execution(self, execution_id: str) -> Checkpoint | None:
        matches = [c for c in self._history if c.execution_id == execution_id]
        return matches[-1] if matches else None

    def history_for_execution(self, execution_id: str) -> tuple[Checkpoint, ...]:
        return tuple(c for c in self._history if c.execution_id == execution_id)

    def seed(self, checkpoint: Checkpoint) -> None:
        self._history.append(checkpoint)


class FakeReportRepository(ReportRepositoryPort):
    def __init__(self) -> None:
        self.saved: list[tuple[str, str]] = []

    def save(self, content: str, file_name: str) -> Path:
        self.saved.append((content, file_name))
        return Path("/fake") / file_name


def make_step(key: str, action=None, preconditions=(), postconditions=()) -> WorkflowStep:
    return WorkflowStep(
        key=key,
        description=key,
        action=action or (lambda ctx: ctx.data.setdefault("visited", []).append(key)),
        preconditions=preconditions,
        postconditions=postconditions,
    )


def make_context() -> ExecutionContext:
    return ExecutionContext(execution_id="exec-1", workflow_id="wf")


def test_executes_all_steps_in_order_and_completes() -> None:
    log_port = FakeLogPort()
    engine = WorkflowEngine(log_port)
    context = make_context()
    workflow = Workflow(key="wf", description="wf", steps=(make_step("a"), make_step("b"), make_step("c")))

    result = engine.execute(workflow, context)

    assert result.final_state == WorkflowState.COMPLETED
    assert context.data["visited"] == ["a", "b", "c"]
    assert [r.outcome for r in result.step_results] == [WorkflowStepOutcome.SUCCEEDED] * 3
    assert engine.history == (result,)


def test_raises_on_empty_workflow() -> None:
    engine = WorkflowEngine(FakeLogPort())

    with pytest.raises(InvalidWorkflowError):
        engine.execute(Workflow(key="wf", description="wf", steps=()), make_context())


def test_raises_on_duplicate_step_keys() -> None:
    engine = WorkflowEngine(FakeLogPort())
    workflow = Workflow(key="wf", description="wf", steps=(make_step("a"), make_step("a")))

    with pytest.raises(InvalidWorkflowError):
        engine.execute(workflow, make_context())


def test_precondition_failure_stops_workflow_before_action_runs() -> None:
    engine = WorkflowEngine(FakeLogPort())
    action_calls: list[str] = []
    step = make_step(
        "a",
        action=lambda ctx: action_calls.append("ran"),
        preconditions=(lambda ctx: False,),
    )
    workflow = Workflow(key="wf", description="wf", steps=(step,))

    result = engine.execute(workflow, make_context())

    assert result.final_state == WorkflowState.FAILED
    assert action_calls == []
    assert result.step_results[0].outcome == WorkflowStepOutcome.FAILED


def test_postcondition_failure_marks_step_failed() -> None:
    engine = WorkflowEngine(FakeLogPort())
    step = make_step("a", postconditions=(lambda ctx: False,))
    workflow = Workflow(key="wf", description="wf", steps=(step,))

    result = engine.execute(workflow, make_context())

    assert result.final_state == WorkflowState.FAILED
    assert "Postcondition failed" in result.error_message


def test_predicate_raising_is_treated_as_a_controlled_failure() -> None:
    engine = WorkflowEngine(FakeLogPort())

    def bad_precondition(ctx):
        raise ValueError("boom")

    step = make_step("a", preconditions=(bad_precondition,))
    workflow = Workflow(key="wf", description="wf", steps=(step,))

    result = engine.execute(workflow, make_context())

    assert result.final_state == WorkflowState.FAILED
    assert "boom" in result.error_message


def test_action_failure_without_retry_engine_stops_workflow() -> None:
    engine = WorkflowEngine(FakeLogPort())

    def failing_action(ctx):
        raise RuntimeError("action exploded")

    workflow = Workflow(key="wf", description="wf", steps=(make_step("a", action=failing_action),))

    result = engine.execute(workflow, make_context())

    assert result.final_state == WorkflowState.FAILED
    assert "action exploded" in result.error_message


def test_action_is_retried_via_injected_retry_engine_then_succeeds() -> None:
    log_port = FakeLogPort()
    classifier = FailureClassifier()
    classifier.register(ConnectionError, FailureClassification.TRANSIENT)
    retry_engine = RetryEngine(
        log_port,
        configuration=RetryConfiguration(max_attempts=3, backoff_strategy="none"),
        classifier=classifier,
        sleep=lambda seconds: None,
    )
    engine = WorkflowEngine(log_port, retry_engine=retry_engine)

    calls: list[int] = []

    def flaky_action(ctx):
        calls.append(1)
        if len(calls) < 2:
            raise ConnectionError("transient")

    workflow = Workflow(key="wf", description="wf", steps=(make_step("a", action=flaky_action),))

    result = engine.execute(workflow, make_context())

    assert result.final_state == WorkflowState.COMPLETED
    assert len(calls) == 2


def test_cancellation_stops_workflow_before_next_step() -> None:
    engine = WorkflowEngine(FakeLogPort())
    workflow = Workflow(key="wf", description="wf", steps=(make_step("a"), make_step("b")))

    result = engine.execute(workflow, make_context(), is_cancelled=lambda: True)

    assert result.final_state == WorkflowState.CANCELLED
    assert result.step_results == ()


def test_checkpoint_is_saved_after_each_successful_step() -> None:
    log_port = FakeLogPort()
    checkpoint_repository = FakeCheckpointRepository()
    checkpoint_engine = CheckpointEngine(checkpoint_repository, log_port)
    engine = WorkflowEngine(log_port, checkpoint_engine=checkpoint_engine)
    context = make_context()
    workflow = Workflow(key="wf", description="wf", steps=(make_step("a"), make_step("b")))

    engine.execute(workflow, context)

    history = checkpoint_repository.history_for_execution("exec-1")
    assert [c.last_completed_step for c in history] == ["a", "b"]


def test_resume_skips_already_completed_steps() -> None:
    log_port = FakeLogPort()
    checkpoint_repository = FakeCheckpointRepository()
    checkpoint_repository.seed(
        Checkpoint(execution_id="exec-1", workflow_id="wf", last_completed_step="a")
    )
    checkpoint_engine = CheckpointEngine(checkpoint_repository, log_port)
    engine = WorkflowEngine(log_port, checkpoint_engine=checkpoint_engine)
    context = make_context()
    workflow = Workflow(key="wf", description="wf", steps=(make_step("a"), make_step("b")))

    result = engine.execute(workflow, context, resume=True)

    assert result.final_state == WorkflowState.COMPLETED
    assert result.step_results[0].outcome == WorkflowStepOutcome.SKIPPED
    assert result.step_results[1].outcome == WorkflowStepOutcome.SUCCEEDED
    assert context.data["visited"] == ["b"]  # step "a" action never re-ran


def test_resume_without_prior_checkpoint_starts_from_the_beginning() -> None:
    log_port = FakeLogPort()
    checkpoint_engine = CheckpointEngine(FakeCheckpointRepository(), log_port)
    engine = WorkflowEngine(log_port, checkpoint_engine=checkpoint_engine)
    context = make_context()
    workflow = Workflow(key="wf", description="wf", steps=(make_step("a"),))

    result = engine.execute(workflow, context, resume=True)

    assert result.final_state == WorkflowState.COMPLETED
    assert result.step_results[0].outcome == WorkflowStepOutcome.SUCCEEDED


def test_reports_successful_execution() -> None:
    log_port = FakeLogPort()
    report_repository = FakeReportRepository()
    reporting_engine = ReportingEngine(report_repository, log_port)
    engine = WorkflowEngine(log_port, reporting_engine=reporting_engine)
    workflow = Workflow(key="wf", description="wf", steps=(make_step("a"),))

    engine.execute(workflow, make_context())

    assert len(reporting_engine.history) == 1
    execution_result = reporting_engine.history[0]
    assert execution_result.execution_id == "exec-1"
    assert execution_result.status.value == "success"


def test_reports_failed_execution_with_error_message() -> None:
    log_port = FakeLogPort()
    report_repository = FakeReportRepository()
    reporting_engine = ReportingEngine(report_repository, log_port)
    engine = WorkflowEngine(log_port, reporting_engine=reporting_engine)

    def failing_action(ctx):
        raise RuntimeError("kaboom")

    workflow = Workflow(key="wf", description="wf", steps=(make_step("a", action=failing_action),))

    engine.execute(workflow, make_context())

    execution_result = reporting_engine.history[0]
    assert execution_result.status.value == "failure"
    assert "kaboom" in execution_result.errors[0]


def test_reports_cancelled_execution() -> None:
    log_port = FakeLogPort()
    reporting_engine = ReportingEngine(FakeReportRepository(), log_port)
    engine = WorkflowEngine(log_port, reporting_engine=reporting_engine)
    workflow = Workflow(key="wf", description="wf", steps=(make_step("a"),))

    engine.execute(workflow, make_context(), is_cancelled=lambda: True)

    assert reporting_engine.history[0].status.value == "cancelled"
