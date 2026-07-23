"""Export Engine exceptions (ADR-0014 - no dedicated SAD chapter exists)."""

from __future__ import annotations

from qa_servicenow_assistant.domain.exceptions.base import QaServiceNowAssistantError


class ExportError(QaServiceNowAssistantError):
    """Base exception for export packaging/persistence failures."""


class InvalidExportRequestError(ExportError):
    """Raised when ExportEngine.export() is asked to package an
    inconsistent request: missing execution_id or no items. A
    caller-contract violation, not an operational failure - never caught
    internally, always propagates.
    """


class ExportPersistenceError(ExportError):
    """Raised by ExportRepositoryPort implementations when packaging
    fails (I/O error, or a referenced source file does not exist). Always
    chains the original error via `raise ... from error` when one exists.
    Caught by ExportEngine and turned into a structured ExportResult,
    consistent with the majority structured-result pattern used across
    this codebase.
    """
