"""A single recorded element observation (Module Specifications Cap. 8 -
Element Recorder: "Captura de elementos").

Scope note: this is runtime traceability (RNF-005 - Observabilidade), i.e.
an in-memory journal of which elements were noted during the current
execution and why - it is NOT a Knowledge Base authoring mechanism.
Producing/maintaining Knowledge Base artifacts remains the exclusive
responsibility of the external ServiceNow Knowledge Builder (SRS 1.3 -
Fora do Escopo). Nothing here is persisted to disk or fed back into any
Knowledge Base file.

Neither SAD nor Module Specifications specify the exact fields a
recording must carry (SAD has no "Element Recorder" chapter at all - see
Prompt 0 gap analysis). The fields below were chosen to satisfy RNF-011
(SRS - "toda execucao deve possuir identificador unico e trilha de
auditoria") and SAD 24.5's precedent for traceable records (correlacao
por execution_id).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from qa_servicenow_assistant.domain.value_objects.browser_snapshot import (
    CollectedElement,
)


@dataclass(frozen=True)
class RecordedElement:
    """An element observation tagged with execution/page context and a
    caller-supplied label.

    execution_id: mandatory (RNF-011). Identifies which execution this
        recording belongs to; must be supplied by the caller, since this
        module does not own execution lifecycle (that belongs to a future
        Workflow Engine / Application Controller). This is also the key
        used by ElementRecorder.records_for_execution() to isolate
        recordings between executions.
    label: a free-text TAG describing the ROLE/REASON this element was
        recorded in the current context - NOT an identifier of the
        element itself (see element_id for that). Examples:
        "primary_action_target" (the element the workflow is about to
        act on), "validation_target" (an element used to confirm an
        outcome), "form_field" (a field being filled as part of a larger
        form). There is no controlled vocabulary yet (known limitation);
        callers are free to choose any string, and records_for_label()
        lets consumers query by it later.
    page_url: the raw URL observed at recording time (from
        BrowserSnapshot.url / page.url).
    page_id: optional logical page identifier (e.g. a PageIdentifier.key
        or a KnowledgePage.key from Page Recognition), when the caller
        has already resolved one. None when no recognized page is known
        at recording time.
    """

    element: CollectedElement
    execution_id: str
    label: str
    page_url: str
    page_id: str | None = None
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def element_id(self) -> str | None:
        """Best-available identifier of the recorded element itself
        (id attribute, falling back to data-testid), surfaced as an
        explicit, first-class property instead of requiring callers to
        reach into element.attributes. None if neither attribute is set."""
        return self.element.attributes.get("id") or self.element.attributes.get("data_testid")
