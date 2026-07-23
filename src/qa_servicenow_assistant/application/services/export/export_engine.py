"""Export Engine (ADR-0014 - no dedicated SAD chapter exists; Module
Specifications Cap. 16 - "Exportacao dos artefatos").

Packages artifacts already produced by other modules (Reporting Engine
reports, evidence files, log excerpts) into a single local archive per
execution. Export Engine does not generate artifacts itself and does not
implement business rules, mirroring every other engine's "nao implementa
regras de negocio" constraint. It has no direct dependency on Reporting
Engine, Screenshot Engine or Log Engine - the caller (future Workflow
Engine) supplies an ExportRequest listing which already-existing files to
package (see ExportItem docstring).

No integration with any external system (e.g. ServiceNow Test Management)
is implemented - ADR-0014 explicitly scoped this out pending a real API
contract.
"""

from __future__ import annotations

from qa_servicenow_assistant.application.ports.export_repository_port import (
    ExportRepositoryPort,
)
from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.domain.exceptions.export import (
    ExportPersistenceError,
    InvalidExportRequestError,
)
from qa_servicenow_assistant.domain.value_objects.export_request import ExportRequest
from qa_servicenow_assistant.domain.value_objects.export_result import ExportResult


class ExportEngine:
    def __init__(self, repository: ExportRepositoryPort, log_port: LogPort) -> None:
        self._repository = repository
        self._log_port = log_port

    def export(self, request: ExportRequest) -> ExportResult:
        """Package request.items into a single archive (ADR-0014).

        Raises InvalidExportRequestError if execution_id is blank or
        items is empty - a caller-contract violation, not an operational
        failure. Never raises for expected failures (I/O errors, a
        referenced source file missing); those are logged and returned as
        a failed ExportResult, consistent with Checkpoint Engine and
        Reporting Engine.
        """
        if not request.execution_id:
            raise InvalidExportRequestError("execution_id is required to export artifacts")
        if not request.items:
            raise InvalidExportRequestError("at least one item is required to export artifacts")

        try:
            archive_path, manifest = self._repository.save(request.execution_id, request.items)
        except ExportPersistenceError as error:
            self._log_port.error(
                "Export failed", execution_id=request.execution_id, error=str(error)
            )
            return ExportResult(success=False, archive_path=None, manifest=None, error_message=str(error))

        self._log_port.info(
            "Export completed",
            execution_id=request.execution_id,
            archive_path=str(archive_path),
            item_count=len(manifest.entries),
        )
        return ExportResult(success=True, archive_path=archive_path, manifest=manifest)
