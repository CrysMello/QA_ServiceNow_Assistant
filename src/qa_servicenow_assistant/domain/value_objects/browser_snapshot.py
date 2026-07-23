"""Immutable snapshot of a browser page at a point in time.

Produced by the Browser Data Collector (SAD 15.4, passo 1: "Obter
informacoes da pagina atual") for later consumption by Page Recognition
and element/selector resolution. This is a read-only, in-memory fact about
what is currently rendered - it is NOT a Knowledge Base artifact and is
never persisted as one; producing/maintaining the Knowledge Base itself
remains the exclusive responsibility of the external ServiceNow Knowledge
Builder (SRS 1.3 - Fora do Escopo).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class CollectedElement:
    """A single element observed on the page at collection time.

    attributes is a plain dict (not a tuple of pairs) for ergonomic
    lookup (element.attributes["id"]); as a consequence instances of this
    class are not hashable despite being frozen (frozen here means
    "cannot be mutated after construction", not "safe to use as a set/dict
    key" - nothing in this codebase relies on hashing these objects).
    """

    tag_name: str
    text: str
    visible: bool
    attributes: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class BrowserSnapshot:
    """Immutable, in-memory snapshot of a single browser page."""

    url: str
    title: str
    html: str
    elements: tuple[CollectedElement, ...] = ()
    collected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
