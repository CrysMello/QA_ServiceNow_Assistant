"""A single recorded element observation (Module Specifications Cap. 8 -
Element Recorder: "Captura de elementos").

Scope note: this is runtime traceability (RNF-005 - Observabilidade), i.e.
an in-memory journal of which elements were noted during the current
execution and why - it is NOT a Knowledge Base authoring mechanism.
Producing/maintaining Knowledge Base artifacts remains the exclusive
responsibility of the external ServiceNow Knowledge Builder (SRS 1.3 -
Fora do Escopo). Nothing here is persisted to disk or fed back into any
Knowledge Base file.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from qa_servicenow_assistant.domain.value_objects.browser_snapshot import (
    CollectedElement,
)


@dataclass(frozen=True)
class RecordedElement:
    """An element observation tagged with a caller-supplied label and the
    page it was observed on."""

    element: CollectedElement
    label: str
    page_url: str
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
