"""SelectorResolver: pure domain service implementing SAD Cap. 17
(Selector Resolver).

Priority reconciliation (documented decision): SAD 17.3 defines Knowledge
Base > ARIA > CSS > XPath > Texto > Fallback. AI Coding Standards Anexo B
defines a finer list: data-testid > id > aria > role > CSS > XPath. Both
are followed by treating SAD's "CSS" tier as a broad category that
data-testid/id/class attribute selectors belong to syntactically, and
applying the Coding Standards' finer ordering within and around it. Final
order used here: knowledge_base > data_testid > id > aria > css > text.

Known gap: XPath (SAD 17.3 tier 4) is NOT generated. BrowserSnapshot /
CollectedElement (Browser Data Collector, Prompt 6) capture a FLAT list of
elements with no parent/child DOM hierarchy, so a meaningful *relative*
XPath cannot be derived from the data available to this service. A
fabricated XPath would be worse than none. This can be revisited if
Browser Data Collector is extended to capture structural relationships.

No I/O: does not query the Knowledge Base itself (a caller-supplied
registered_selector stands in for it - see resolve()) and does not touch
Playwright/live DOM. Validates uniqueness only against the elements
already present in the given BrowserSnapshot (SAD 17.4 passo 4).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from qa_servicenow_assistant.domain.value_objects.browser_snapshot import (
    BrowserSnapshot,
    CollectedElement,
)
from qa_servicenow_assistant.domain.value_objects.selector import Selector
from qa_servicenow_assistant.domain.value_objects.selector_resolution import (
    SelectorResolution,
)


@dataclass(frozen=True)
class _Candidate:
    selector: Selector
    matches: Callable[[CollectedElement], bool]


class SelectorResolver:
    """Selects the best-priority, snapshot-unique locator for a target
    element (SAD 17.4/17.6)."""

    def resolve(
        self,
        target: CollectedElement,
        snapshot: BrowserSnapshot,
        *,
        registered_selector: str | None = None,
    ) -> SelectorResolution:
        candidates = self._generate_candidates(target, registered_selector)
        considered = tuple(candidate.selector for candidate in candidates)

        for candidate in candidates:
            if self._count_matches(candidate, snapshot) == 1:
                return SelectorResolution(
                    target=target,
                    selector=candidate.selector,
                    is_unique=True,
                    is_visible=target.visible,
                    considered=considered,
                )

        fallback_selector = candidates[0].selector if candidates else None
        return SelectorResolution(
            target=target,
            selector=fallback_selector,
            is_unique=False,
            is_visible=target.visible,
            considered=considered,
        )

    def _generate_candidates(
        self, target: CollectedElement, registered_selector: str | None
    ) -> tuple[_Candidate, ...]:
        candidates: list[_Candidate] = []

        if registered_selector:
            candidates.append(
                _Candidate(
                    selector=Selector(strategy="knowledge_base", value=registered_selector, priority=1),
                    matches=lambda element: element is target,
                )
            )

        data_testid = target.attributes.get("data_testid")
        if data_testid:
            candidates.append(
                _Candidate(
                    selector=Selector(
                        strategy="data_testid", value=f'[data-testid="{data_testid}"]', priority=2
                    ),
                    matches=lambda element, v=data_testid: element.attributes.get("data_testid") == v,
                )
            )

        element_id = target.attributes.get("id")
        if element_id:
            candidates.append(
                _Candidate(
                    selector=Selector(strategy="id", value=f"#{element_id}", priority=3),
                    matches=lambda element, v=element_id: element.attributes.get("id") == v,
                )
            )

        aria_label = target.attributes.get("aria_label")
        role = target.attributes.get("role")
        if aria_label:
            candidates.append(
                _Candidate(
                    selector=Selector(
                        strategy="aria", value=f'[aria-label="{aria_label}"]', priority=4
                    ),
                    matches=lambda element, v=aria_label: element.attributes.get("aria_label") == v,
                )
            )
        elif role:
            candidates.append(
                _Candidate(
                    selector=Selector(strategy="aria", value=f'[role="{role}"]', priority=4),
                    matches=lambda element, v=role: element.attributes.get("role") == v,
                )
            )

        css_name = target.attributes.get("name")
        if css_name:
            tag_name = target.tag_name
            candidates.append(
                _Candidate(
                    selector=Selector(
                        strategy="css", value=f'{tag_name}[name="{css_name}"]', priority=5
                    ),
                    matches=lambda element, v=css_name, tag=tag_name: (
                        element.tag_name == tag and element.attributes.get("name") == v
                    ),
                )
            )

        if target.text:
            candidates.append(
                _Candidate(
                    selector=Selector(strategy="text", value=f'text="{target.text}"', priority=7),
                    matches=lambda element, v=target.text: element.text == v,
                )
            )

        return tuple(sorted(candidates, key=lambda candidate: candidate.selector.priority))

    def _count_matches(self, candidate: _Candidate, snapshot: BrowserSnapshot) -> int:
        return sum(1 for element in snapshot.elements if candidate.matches(element))
