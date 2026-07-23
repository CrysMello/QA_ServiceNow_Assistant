"""Reporting Engine exceptions (SAD Cap. 22)."""

from __future__ import annotations

from qa_servicenow_assistant.domain.exceptions.base import QaServiceNowAssistantError


class ReportingError(QaServiceNowAssistantError):
    """Base exception for report generation/persistence failures."""


class UnsupportedReportFormatError(ReportingError):
    """Raised when ReportingEngine.generate_report() is asked to use a
    format outside the supported set (currently {"json", "html"} - see
    ReportingConfiguration docstring: SAD 22.5 lists JSON/HTML/PDF/CSV/
    Console illustratively, but ConfigurationValidator already narrows
    this to {"html", "json"} per SRS Cap.7). A caller-contract violation,
    not an operational failure - never caught internally, always
    propagates.
    """


class ReportPersistenceError(ReportingError):
    """Raised by ReportRepositoryPort implementations when persisting a
    report fails (I/O error). Always chains the original error via
    `raise ... from error`. Caught by ReportingEngine and turned into a
    structured ReportGenerationResult, consistent with the majority
    structured-result pattern used across this codebase.
    """
