"""Workflow Engine (SAD Cap. 12).

Orchestrates sequential execution of a Workflow's steps (SAD 12.2,
12.5): validates preconditions, runs each step's caller-supplied action
(through Retry Engine when one is injected - SAD 12.6/19.7), validates
postconditions, persists progress via Checkpoint Engine after each
completed step (SAD 12.6/20.7), and reports the final outcome via
Reporting Engine (SAD 12.6, 12.5 passo 8) - wiring together modules that
have, until now, been deliberately decoupled from each other exactly for
this purpose (see RetryEngine/CheckpointEngine/ReportingEngine module
docstrings).

Every collaborator besides LogPort is optional: a caller may run a
workflow with no retry policy, no checkpointing and no reporting wired in
(SAD 12.8 - "Cada workflow deve possuir responsabilidade unica").

Scope explicitly excluded from this module (SAD 12.8 - "O Workflow
Engine nao implementa acoes especificas do Playwright"): Automation
Engine does not exist yet (a later prompt) - step actions are entirely
caller-supplied callables (see WorkflowStep docstring), so this class has
no Playwright/browser dependency of its own. Building actual concrete
workflows (e.g. "create an incident") by composing steps around
Navigation Engine, Page Recognition, Selector Resolver, Knowledge
Manager, and eventually Automation Engine, is a future Application
Controller/CLI responsibility, not this engine's.

"Transition" (SAD 12.3) is linear ("next step in the tuple") - see
Workflow's docstring. WAITING (SAD 12.4) is defined for fidelity to the
lifecycle table but is not reachable by this synchronous implementation
(no async/event-wait concept exists elsewhere in this codebase) - a
documented, known limitation, not an oversight.
"""

from __future__ import annotations

import time
from typing import Callable

from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.application.services.checkpoint.checkpoint_engine import (
    CheckpointEngine,
)
from qa_servicenow_assistant.application.services.reporting.reporting_engine import (
    ReportingEngine,
)
from qa_servicenow_assistant.application.services.retry.retry_engine import RetryEngine
from qa_servicenow_assistant.domain.exceptions.workflow import InvalidWorkflowError
from qa_servicenow_assistant.domain.value_objects.execution_context import (
    ExecutionContext,
)
from qa_servicenow_assistant.domain.value_objects.execution_result import (
    ExecutionResult,
)
from qa_servicenow_assistant.domain.value_objects.execution_status import (
    ExecutionStatus,
)
from qa_servicenow_assistant.domain.value_objects.workflow import Workflow
from qa_servicenow_assistant.domain.value_objects.workflow_result import WorkflowResult
from qa_servicenow_assistant.domain.value_objects.workflow_state import WorkflowState
from qa_servicenow_assistant.domain.value_objects.workflow_step import WorkflowStep
from qa_servicenow_assistant.domain.value_objects.workflow_step_result import (
    WorkflowStepOutcome,
    WorkflowStepResult,
)

_FINAL_STATE_TO_EXECUTION_STATUS = {
    WorkflowState.COMPLETED: ExecutionStatus.SUCCESS,
    WorkflowState.CANCELLED: ExecutionStatus.CANCELLED,
}


class WorkflowEngine:
    def __init__(
        self,
        log_port: LogPort,
        retry_engine: RetryEngine | None = None,
        checkpoint_engine: CheckpointEngine | None = None,
        reporting_engine: ReportingEngine | None = None,
    ) -> None:
        self._log_port = log_port
        self._retry_engine = retry_engine
        self._checkpoint_engine = checkpoint_engine
        self._reporting_engine = reporting_engine
        self._history: list[WorkflowResult] = []

    @property
    def history(self) -> tuple[WorkflowResult, ...]:
        """Workflow executions recorded so far, oldest first."""
        return tuple(self._history)

    def execute(
        self,
        workflow: Workflow,
        context: ExecutionContext,
        *,
        resume: bool = False,
        is_cancelled: Callable[[], bool] | None = None,
    ) -> WorkflowResult:
        """Run every step of workflow in order.

        Raises InvalidWorkflowError if workflow has no steps or duplicate
        step keys - a caller-contract violation. Never raises for
        expected failures (a step's precondition/action/postcondition
        failing, or cancellation); those end the run early and are
        reported via a WorkflowResult with final_state != COMPLETED,
        consistent with Navigation Engine, Retry Engine, Checkpoint
        Engine, Reporting Engine and Export Engine.
        """
        self._validate(workflow)

        started_at = time.monotonic()
        self._log_port.info(
            "Workflow started", execution_id=context.execution_id, workflow=workflow.key
        )

        start_index = self._resolve_start_index(workflow, context, resume)
        step_results: list[WorkflowStepResult] = [
            WorkflowStepResult(
                step_key=step.key,
                outcome=WorkflowStepOutcome.SKIPPED,
                detail="Already completed (resumed from checkpoint)",
            )
            for step in workflow.steps[:start_index]
        ]

        state = WorkflowState.RUNNING
        error_message: str | None = None
        total_retry_attempts = 0
        checkpoints_used = 0

        for step in workflow.steps[start_index:]:
            if is_cancelled is not None and is_cancelled():
                state = WorkflowState.CANCELLED
                error_message = f"Cancelled before step '{step.key}'"
                break

            ok, detail = self._evaluate_all(step.preconditions, context)
            if not ok:
                state = WorkflowState.FAILED
                error_message = f"Precondition failed for step '{step.key}': {detail}"
                step_results.append(
                    WorkflowStepResult(step.key, WorkflowStepOutcome.FAILED, error_message)
                )
                self._log_port.error(
                    "Workflow step precondition failed",
                    execution_id=context.execution_id,
                    step=step.key,
                    error=detail,
                )
                break

            succeeded, action_error, retries = self._run_action(step, context)
            total_retry_attempts += retries
            if not succeeded:
                state = WorkflowState.FAILED
                error_message = f"Step '{step.key}' failed: {action_error}"
                step_results.append(
                    WorkflowStepResult(step.key, WorkflowStepOutcome.FAILED, action_error)
                )
                self._log_port.error(
                    "Workflow step failed",
                    execution_id=context.execution_id,
                    step=step.key,
                    error=action_error,
                )
                break

            ok, detail = self._evaluate_all(step.postconditions, context)
            if not ok:
                state = WorkflowState.FAILED
                error_message = f"Postcondition failed for step '{step.key}': {detail}"
                step_results.append(
                    WorkflowStepResult(step.key, WorkflowStepOutcome.FAILED, error_message)
                )
                self._log_port.error(
                    "Workflow step postcondition failed",
                    execution_id=context.execution_id,
                    step=step.key,
                    error=detail,
                )
                break

            step_results.append(WorkflowStepResult(step.key, WorkflowStepOutcome.SUCCEEDED))
            self._log_port.info(
                "Workflow step completed", execution_id=context.execution_id, step=step.key
            )

            if self._checkpoint_engine is not None:
                save_result = self._checkpoint_engine.save_checkpoint(
                    execution_id=context.execution_id,
                    workflow_id=workflow.key,
                    last_completed_step=step.key,
                )
                if save_result.success:
                    checkpoints_used += 1
        else:
            state = WorkflowState.COMPLETED

        duration_ms = self._elapsed_ms(started_at)
        result = WorkflowResult(
            execution_id=context.execution_id,
            workflow_key=workflow.key,
            final_state=state,
            step_results=tuple(step_results),
            error_message=error_message,
        )
        self._history.append(result)

        self._log_final_state(result, duration_ms)
        self._report(result, duration_ms, total_retry_attempts, checkpoints_used)
        return result

    def _validate(self, workflow: Workflow) -> None:
        if not workflow.steps:
            raise InvalidWorkflowError(f"Workflow '{workflow.key}' has no steps")
        step_keys = [step.key for step in workflow.steps]
        if len(step_keys) != len(set(step_keys)):
            raise InvalidWorkflowError(f"Workflow '{workflow.key}' has duplicate step keys")

    def _resolve_start_index(
        self, workflow: Workflow, context: ExecutionContext, resume: bool
    ) -> int:
        if not resume or self._checkpoint_engine is None:
            return 0

        restore_result = self._checkpoint_engine.restore_latest(context.execution_id)
        if not restore_result.success or restore_result.checkpoint is None:
            self._log_port.debug(
                "No checkpoint to resume from", execution_id=context.execution_id
            )
            return 0

        last_completed_step = restore_result.checkpoint.last_completed_step
        step_keys = [step.key for step in workflow.steps]
        if last_completed_step not in step_keys:
            self._log_port.warning(
                "Checkpoint references an unknown step, starting from the beginning",
                execution_id=context.execution_id,
                last_completed_step=last_completed_step,
            )
            return 0

        self._log_port.info(
            "Resuming workflow from checkpoint",
            execution_id=context.execution_id,
            last_completed_step=last_completed_step,
        )
        return step_keys.index(last_completed_step) + 1

    def _evaluate_all(
        self,
        predicates: tuple[Callable[[ExecutionContext], bool], ...],
        context: ExecutionContext,
    ) -> tuple[bool, str | None]:
        for predicate in predicates:
            ok, error = self._evaluate_predicate(predicate, context)
            if not ok:
                return False, error or "condition returned False"
        return True, None

    def _evaluate_predicate(
        self, predicate: Callable[[ExecutionContext], bool], context: ExecutionContext
    ) -> tuple[bool, str | None]:
        # Deliberate, narrow exception isolation boundary (same pattern as
        # InMemoryEventBus._invoke_handler, RetryEngine.execute): Workflow
        # Engine is reusable across every future workflow and cannot know
        # in advance which exception types a caller-supplied
        # precondition/postcondition may raise.
        try:
            return bool(predicate(context)), None
        except Exception as error:  # noqa: BLE001 - intentional isolation boundary
            return False, str(error)

    def _run_action(
        self, step: WorkflowStep, context: ExecutionContext
    ) -> tuple[bool, str | None, int]:
        """Returns (succeeded, error_message, retry_attempts_beyond_the_first)."""
        if self._retry_engine is not None:
            outcome = self._retry_engine.execute(
                lambda: step.action(context), operation_name=step.key
            )
            retries = max(0, len(outcome.attempts) - 1)
            return outcome.succeeded, outcome.final_error_message, retries

        # Same isolation boundary rationale as _evaluate_predicate above,
        # needed here only when no RetryEngine was injected (RetryEngine
        # already applies its own boundary internally otherwise).
        try:
            step.action(context)
            return True, None, 0
        except Exception as error:  # noqa: BLE001 - intentional isolation boundary
            return False, str(error), 0

    def _log_final_state(self, result: WorkflowResult, duration_ms: float) -> None:
        if result.final_state == WorkflowState.COMPLETED:
            self._log_port.info(
                "Workflow completed",
                execution_id=result.execution_id,
                workflow=result.workflow_key,
                duration_ms=duration_ms,
            )
        else:
            self._log_port.error(
                "Workflow ended without completing",
                execution_id=result.execution_id,
                workflow=result.workflow_key,
                final_state=result.final_state.value,
                error=result.error_message,
                duration_ms=duration_ms,
            )

    def _report(
        self,
        result: WorkflowResult,
        duration_ms: float,
        retry_attempts: int,
        checkpoints_used: int,
    ) -> None:
        if self._reporting_engine is None:
            return

        status = _FINAL_STATE_TO_EXECUTION_STATUS.get(result.final_state, ExecutionStatus.FAILURE)
        errors = tuple(
            step_result.detail
            for step_result in result.step_results
            if step_result.outcome == WorkflowStepOutcome.FAILED and step_result.detail
        )
        execution_result = ExecutionResult(
            execution_id=result.execution_id,
            workflow_id=result.workflow_key,
            status=status,
            duration_ms=duration_ms,
            errors=errors,
            retry_attempts=retry_attempts,
            checkpoints_used=checkpoints_used,
        )
        self._reporting_engine.generate_report(execution_result)

    def _elapsed_ms(self, started_at: float) -> float:
        return (time.monotonic() - started_at) * 1000
