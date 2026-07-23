"""Outcome of resolving a locator for a single element (SAD Cap. 17)."""

from __future__ import annotations

from dataclasses import dataclass

from qa_servicenow_assistant.domain.value_objects.browser_snapshot import (
    CollectedElement,
)
from qa_servicenow_assistant.domain.value_objects.selector import Selector


@dataclass(frozen=True)
class SelectorResolution:
    """Immutable result of SelectorResolver.resolve()."""

    target: CollectedElement
    selector: Selector | None
    is_unique: bool
    is_visible: bool
    considered: tuple[Selector, ...] = ()

    @property
    def is_resolved(self) -> bool:
        return self.selector is not None
