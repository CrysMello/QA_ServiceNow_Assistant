"""Port for collecting URL/DOM/element data from a browser page.

Scope: read-only collection of the *current* page state, for later
consumption by Page Recognition and element/selector resolution modules
(not implemented yet - future prompts). This does NOT recognize/classify
the page against the Knowledge Base (Page Recognition) and does NOT decide
which selector to use for automation (Selector Resolver); it only reports
raw, observed facts.

The page parameter is intentionally typed as Any, mirroring
BrowserManagerPort.new_page(): the abstract contract must not leak a
Playwright-specific type (SAD 9.7).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from qa_servicenow_assistant.domain.value_objects.browser_snapshot import (
    BrowserSnapshot,
)


class BrowserDataCollectorPort(ABC):
    """Contract implemented by infrastructure adapters that collect a
    BrowserSnapshot from a live browser page."""

    @abstractmethod
    def collect(self, page: Any) -> BrowserSnapshot:
        """Collect URL, title, HTML and a bounded list of elements from
        page, publish a BrowserDataCollectedEvent (ADR-0012) and return the
        resulting BrowserSnapshot.

        Raises BrowserDataCollectionError if collection fails.
        """
        raise NotImplementedError
