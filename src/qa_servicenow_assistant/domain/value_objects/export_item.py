"""ExportItem: reference to an already-existing local file to include in
an export package (ADR-0014 - Export Engine scope).

Export Engine does not produce artifacts itself and does not depend
directly on Reporting Engine, Screenshot Engine or Log Engine - the
caller (future Workflow Engine) supplies the paths of files those modules
already wrote to disk, the same caller-supplied-DTO precedent used by
EvidenceReference (Reporting Engine) and Checkpoint (Checkpoint Engine).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExportItem:
    """description: what this file is (e.g. "execution_report",
    "final_screenshot"). source_path: where it currently lives on disk."""

    description: str
    source_path: Path
