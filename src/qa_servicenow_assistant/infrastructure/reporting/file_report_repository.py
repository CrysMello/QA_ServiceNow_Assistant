"""File-based implementation of ReportRepositoryPort (SAD 22.6 -
"Configuration Manager: Obter formato e diretorios").

Writes each report as a single file under ReportingConfiguration.directory.
Single-process CLI tool (SAD 29.2 - "Execucao via CLI"): no file locking
or concurrent-writer protection, matching the scope of the rest of this
codebase (e.g. JsonFileCheckpointRepository).
"""

from __future__ import annotations

import re
from pathlib import Path

from qa_servicenow_assistant.application.ports.report_repository_port import (
    ReportRepositoryPort,
)
from qa_servicenow_assistant.domain.exceptions.reporting import ReportPersistenceError
from qa_servicenow_assistant.domain.value_objects.configuration import (
    ReportingConfiguration,
)

_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9_.-]")


class FileReportRepository(ReportRepositoryPort):
    def __init__(self, configuration: ReportingConfiguration | None = None) -> None:
        self._directory = Path((configuration or ReportingConfiguration()).directory)
        self._directory.mkdir(parents=True, exist_ok=True)

    def save(self, content: str, file_name: str) -> Path:
        """file_name is sanitized (non alnum/dot/dash/underscore
        characters replaced with "_") so it can never be used to escape
        configuration.directory - same precedent as
        JsonFileCheckpointRepository. "." and ".." are rejected outright
        (the only single-segment names that traverse the filesystem tree
        even without a path separator)."""
        safe_name = _UNSAFE_FILENAME_CHARS.sub("_", file_name)
        if safe_name in {"", ".", ".."}:
            raise ReportPersistenceError(f"Invalid report file name: {file_name!r}")
        path = self._directory / safe_name
        try:
            path.write_text(content, encoding="utf-8")
        except OSError as error:
            raise ReportPersistenceError(f"Failed to write report file: {path}") from error
        return path
