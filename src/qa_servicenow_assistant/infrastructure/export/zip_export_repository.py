"""ZIP-based implementation of ExportRepositoryPort (ADR-0014).

One ZIP archive per execution_id under ExportConfiguration.directory,
containing every referenced source file plus a manifest.json describing
them (RNF-011-style traceability precedent - same rationale as
CheckpointEngine/ReportingEngine's audit logging, applied to the archive
itself so the package is self-describing even detached from this
application).

Single-process CLI tool (SAD 29.2 - "Execucao via CLI"): no file locking
or concurrent-writer protection, matching the scope of the rest of this
codebase (e.g. JsonFileCheckpointRepository, FileReportRepository).
"""

from __future__ import annotations

import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from qa_servicenow_assistant.application.ports.export_repository_port import (
    ExportRepositoryPort,
)
from qa_servicenow_assistant.domain.exceptions.export import ExportPersistenceError
from qa_servicenow_assistant.domain.value_objects.configuration import (
    ExportConfiguration,
)
from qa_servicenow_assistant.domain.value_objects.export_item import ExportItem
from qa_servicenow_assistant.domain.value_objects.export_manifest import (
    ExportManifest,
    ExportManifestEntry,
)

_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9_-]")


class ZipExportRepository(ExportRepositoryPort):
    """execution_id is sanitized (non alnum/dash/underscore characters
    replaced with "_") before being used as the archive file name - same
    precedent as JsonFileCheckpointRepository/FileReportRepository."""

    def __init__(self, configuration: ExportConfiguration | None = None) -> None:
        self._directory = Path((configuration or ExportConfiguration()).directory)
        self._directory.mkdir(parents=True, exist_ok=True)

    def save(self, execution_id: str, items: Sequence[ExportItem]) -> tuple[Path, ExportManifest]:
        for item in items:
            if not Path(item.source_path).is_file():
                raise ExportPersistenceError(f"Source file not found: {item.source_path}")

        safe_name = _UNSAFE_FILENAME_CHARS.sub("_", execution_id)
        if safe_name in {"", ".", ".."}:
            raise ExportPersistenceError(f"Invalid execution_id for export: {execution_id!r}")
        archive_path = self._directory / f"{safe_name}.zip"
        exported_at = datetime.now(timezone.utc)

        entries: list[ExportManifestEntry] = []
        try:
            with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
                for index, item in enumerate(items):
                    source = Path(item.source_path)
                    archive_name = f"{index:02d}_{source.name}"
                    archive.write(source, arcname=archive_name)
                    entries.append(
                        ExportManifestEntry(
                            description=item.description,
                            archive_name=archive_name,
                            size_bytes=source.stat().st_size,
                        )
                    )

                manifest = ExportManifest(
                    execution_id=execution_id, entries=tuple(entries), exported_at=exported_at
                )
                archive.writestr("manifest.json", _manifest_to_json(manifest))
        except OSError as error:
            raise ExportPersistenceError(f"Failed to build export archive: {archive_path}") from error

        return archive_path, manifest


def _manifest_to_json(manifest: ExportManifest) -> str:
    payload = {
        "execution_id": manifest.execution_id,
        "exported_at": manifest.exported_at.isoformat(),
        "entries": [
            {
                "description": entry.description,
                "archive_name": entry.archive_name,
                "size_bytes": entry.size_bytes,
            }
            for entry in manifest.entries
        ],
    }
    return json.dumps(payload, indent=2)
