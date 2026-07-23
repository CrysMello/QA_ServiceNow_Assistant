"""KnowledgeSelector: a validated locator catalogued by the Knowledge
Base, keyed by the element it targets (SAD 11.3 - "selectors.json ...
Disponibilizar locators validados").

Wraps the existing Selector value object (already used by
SelectorResolver/SAD Cap. 17) instead of adding an element-key field to
it directly, so Selector itself - consumed by already-implemented,
tested Selector Resolver logic with no notion of a KB element key -
remains unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass

from qa_servicenow_assistant.domain.value_objects.selector import Selector


@dataclass(frozen=True)
class KnowledgeSelector:
    element_key: str
    selector: Selector
