"""Checkpoint Engine (SAD Cap. 20).

Persists and restores workflow execution state (SAD 20.1) so a future
Workflow Engine/Retry Engine can resume automation after a failure,
planned interruption or new retry attempt instead of restarting a
workflow from scratch (SAD 20.6 - Situacoes de Uso).

Checkpoint Engine does not know WHAT a "workflow" or a "step" means
(SAD 20.8 - "O Checkpoint Engine nao contem regras de negocio") - callers
(future Workflow Engine) supply opaque execution_id/workflow_id/
last_completed_step identifiers and whatever temporary_data they need to
resume. This mirrors Retry Engine's own "does not know WHAT operation it
retries" design.

Integration with Retry Engine (SAD 19.7 - "Checkpoint Engine: Restaurar
estado antes da nova tentativa"; SAD 20.7 - "Retry Engine: Retomar
execucoes apos nova tentativa") is a documented, deliberate scope
boundary: RetryEngine.execute() does not call this class, and this class
does not call RetryEngine. Wiring the two together is a future Workflow
Engine's responsibility - not an oversight.
"""

from __future__ import annotations

from typing import Any

from qa_servicenow_assistant.application.ports.checkpoint_repository_port import (
    CheckpointRepositoryPort,
)
from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.domain.exceptions.checkpoint import (
    CheckpointPersistenceError,
    InvalidCheckpointStateError,
)
from qa_servicenow_assistant.domain.value_objects.checkpoint import Checkpoint
from qa_servicenow_assistant.domain.value_objects.checkpoint_restore_result import (
    CheckpointRestoreResult,
)
from qa_servicenow_assistant.domain.value_objects.checkpoint_save_result import (
    CheckpointSaveResult,
)
from qa_servicenow_assistant.domain.value_objects.page_identifier import (
    PageIdentifier,
)


class CheckpointEngine:
    """Application-facing entry point combining SAD 20.3's Checkpoint
    Manager (create/restore) and Recovery Manager (restoration flow)
    responsibilities behind a single "Engine" class, following the same
    shape as NavigationEngine/RetryEngine/PageRecognitionEngine. State
    Serializer is CheckpointSerializer (used internally by the
    repository); Checkpoint History is satisfied via LogPort, matching
    every other module's approach to auditing (Log Engine integration)
    rather than the Event Bus, which only Browser Data Collector uses
    (ADR-0012 - role complementar, nao orquestracao primaria)."""

    def __init__(self, repository: CheckpointRepositoryPort, log_port: LogPort) -> None:
        self._repository = repository
        self._log_port = log_port

    def save_checkpoint(
        self,
        *,
        execution_id: str,
        workflow_id: str,
        last_completed_step: str,
        page: PageIdentifier | None = None,
        temporary_data: dict[str, Any] | None = None,
        partial_result: str = "",
    ) -> CheckpointSaveResult:
        """Create and persist a checkpoint (SAD 20.5 - only ever called
        at a consistent state; SAD 20.8 - "Checkpoints devem ser criados
        apenas em estados consistentes").

        Raises InvalidCheckpointStateError if execution_id, workflow_id or
        last_completed_step is blank - a caller-contract violation, not an
        expected operational failure, so (unlike persistence failures) it
        is never converted into a failed CheckpointSaveResult.
        """
        if not execution_id or not workflow_id or not last_completed_step:
            raise InvalidCheckpointStateError(
                "execution_id, workflow_id and last_completed_step are "
                "required to save a consistent checkpoint"
            )

        checkpoint = Checkpoint(
            execution_id=execution_id,
            workflow_id=workflow_id,
            last_completed_step=last_completed_step,
            page=page,
            temporary_data=dict(temporary_data or {}),
            partial_result=partial_result,
        )

        try:
            self._repository.save(checkpoint)
        except CheckpointPersistenceError as error:
            self._log_port.error(
                "Checkpoint save failed",
                execution_id=execution_id,
                workflow_id=workflow_id,
                error=str(error),
            )
            return CheckpointSaveResult(success=False, checkpoint=None, error_message=str(error))

        self._log_port.info(
            "Checkpoint saved",
            execution_id=execution_id,
            workflow_id=workflow_id,
            last_completed_step=last_completed_step,
        )
        return CheckpointSaveResult(success=True, checkpoint=checkpoint)

    def restore_latest(self, execution_id: str) -> CheckpointRestoreResult:
        """SAD 20.5 - Fluxo de Recuperacao: locate the last valid
        checkpoint, validate context consistency, and report a result the
        caller uses to resume from the last completed step. Never raises
        for expected outcomes (nothing found, corrupted data, inconsistent
        context) - all are logged (SAD 20.8 - "Falhas de recuperacao
        devem ser registradas") and returned as a failed result.
        """
        try:
            checkpoint = self._repository.latest_for_execution(execution_id)
        except CheckpointPersistenceError as error:
            self._log_port.error(
                "Checkpoint restoration failed", execution_id=execution_id, error=str(error)
            )
            return CheckpointRestoreResult(success=False, checkpoint=None, error_message=str(error))

        if checkpoint is None:
            message = f"No checkpoint found for execution_id={execution_id}"
            self._log_port.warning("Checkpoint restoration found nothing", execution_id=execution_id)
            return CheckpointRestoreResult(success=False, checkpoint=None, error_message=message)

        if not checkpoint.workflow_id or not checkpoint.last_completed_step:
            message = f"Checkpoint for execution_id={execution_id} is inconsistent"
            self._log_port.error(
                "Checkpoint restoration failed", execution_id=execution_id, error=message
            )
            return CheckpointRestoreResult(success=False, checkpoint=None, error_message=message)

        self._log_port.info(
            "Checkpoint restored",
            execution_id=execution_id,
            workflow_id=checkpoint.workflow_id,
            last_completed_step=checkpoint.last_completed_step,
        )
        return CheckpointRestoreResult(success=True, checkpoint=checkpoint)

    def history(self, execution_id: str) -> tuple[Checkpoint, ...]:
        """All checkpoints saved for execution_id, oldest first (SAD 20.2
        - "Registrar historico de checkpoints"). Empty tuple both when
        none exist and when retrieval fails (logged either way)."""
        try:
            return self._repository.history_for_execution(execution_id)
        except CheckpointPersistenceError as error:
            self._log_port.error(
                "Checkpoint history retrieval failed", execution_id=execution_id, error=str(error)
            )
            return ()
