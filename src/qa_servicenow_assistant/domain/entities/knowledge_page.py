"""KnowledgePage entity (SAD 8.3 - "Pagina conhecida do ServiceNow").

This is a minimal read model of a single Knowledge Base page entry - only
what Page Recognition needs to compare against an observed BrowserSnapshot
(SAD 15.3 - Fontes de Identificacao). The full Knowledge Base schema
(manifest, elements, selectors, workflows, fingerprints files) belongs to
Knowledge Manager, a later module (Prompt 18); this entity will likely be
extended or superseded once that module defines the real read model.

Identity is the `key` field (matches PageIdentifier.key used by
Navigation Engine). Immutable, per SAD 8.7 ("objetos de dominio devem ser
imutaveis sempre que possivel").
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class KnowledgePage:
    """A single Knowledge Base page entry used for recognition matching."""

    key: str
    url_pattern: str
    title: str | None = None
    fingerprint: str | None = None
    required_element_keys: tuple[str, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)
