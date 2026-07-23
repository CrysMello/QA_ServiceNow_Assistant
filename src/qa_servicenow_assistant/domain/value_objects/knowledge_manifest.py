"""KnowledgeManifest: version and metadata of the Knowledge Base
(SAD 11.3 - "manifest.json ... Descrever versao e metadados da base")."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class KnowledgeManifest:
    version: str
    generated_at: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)
