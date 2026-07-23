"""ExportManifest: summary of what was packaged by ExportEngine.export()
(ADR-0014). Also embedded as manifest.json inside the archive itself by
ZipExportRepository, for traceability of the package's own contents."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class ExportManifestEntry:
    description: str
    archive_name: str
    size_bytes: int


@dataclass(frozen=True)
class ExportManifest:
    execution_id: str
    entries: tuple[ExportManifestEntry, ...]
    exported_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
