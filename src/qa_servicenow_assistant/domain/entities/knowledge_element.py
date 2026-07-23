"""KnowledgeElement entity (SAD 11.3 - "elements.json ... Catalogar
elementos da interface").

Distinct from CollectedElement (Browser Data Collector, runtime DOM
observation) and RecordedElement (Element Recorder, runtime traceability
journal): this is an authored Knowledge Base entry produced by the
external ServiceNow Knowledge Builder, describing an element expected to
exist on a given known page. attributes is a plain dict, same precedent
as CollectedElement.attributes (ergonomic lookup; not truly immutable for
that field).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class KnowledgeElement:
    key: str
    page_key: str
    description: str
    attributes: dict[str, str] = field(default_factory=dict)
