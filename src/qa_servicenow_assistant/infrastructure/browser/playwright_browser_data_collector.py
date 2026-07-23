"""Playwright-based implementation of BrowserDataCollectorPort.

Collects URL, title, full HTML and a bounded list of candidate elements
(matched by id/data-testid/aria-label/role plus common interactive tags)
from the current page, and publishes a BrowserDataCollectedEvent summary
on the Event Bus (ADR-0012 - complementary, cross-cutting notification).
"""

from __future__ import annotations

from typing import Any

from playwright.sync_api import Error as PlaywrightError

from qa_servicenow_assistant.application.ports.browser_data_collector_port import (
    BrowserDataCollectorPort,
)
from qa_servicenow_assistant.application.ports.event_bus_port import EventBusPort
from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.domain.events.browser_data_collected_event import (
    BrowserDataCollectedEvent,
)
from qa_servicenow_assistant.domain.exceptions.browser import (
    BrowserDataCollectionError,
)
from qa_servicenow_assistant.domain.value_objects.browser_snapshot import (
    BrowserSnapshot,
    CollectedElement,
)

_DEFAULT_MAX_ELEMENTS = 200

_ELEMENT_SELECTOR = "[id], [data-testid], [aria-label], [role], input, button, a, select, textarea"

_COLLECT_ELEMENTS_SCRIPT = """
({ selector, maxElements }) => {
    const nodes = Array.from(document.querySelectorAll(selector)).slice(0, maxElements);
    return nodes.map((el) => {
        const rect = el.getBoundingClientRect();
        return {
            tagName: el.tagName.toLowerCase(),
            text: (el.innerText || el.value || "").trim().slice(0, 200),
            visible: rect.width > 0 && rect.height > 0,
            attributes: {
                id: el.getAttribute("id") || "",
                class: el.getAttribute("class") || "",
                name: el.getAttribute("name") || "",
                type: el.getAttribute("type") || "",
                role: el.getAttribute("role") || "",
                aria_label: el.getAttribute("aria-label") || "",
                data_testid: el.getAttribute("data-testid") || "",
            },
        };
    });
}
"""


class PlaywrightBrowserDataCollector(BrowserDataCollectorPort):
    """Collects a BrowserSnapshot from a real Playwright page.

    Both log_port and event_bus are required (not optional): logging and
    event publication are core, explicitly stated responsibilities of this
    module (Module Specifications Cap. 5), not optional decorations.
    """

    def __init__(
        self,
        log_port: LogPort,
        event_bus: EventBusPort,
        *,
        max_elements: int = _DEFAULT_MAX_ELEMENTS,
    ) -> None:
        self._log_port = log_port
        self._event_bus = event_bus
        self._max_elements = max_elements

    def collect(self, page: Any) -> BrowserSnapshot:
        try:
            url = page.url
            title = page.title()
            html = page.content()
            raw_elements = page.evaluate(
                _COLLECT_ELEMENTS_SCRIPT,
                {"selector": _ELEMENT_SELECTOR, "maxElements": self._max_elements},
            )
        except PlaywrightError as error:
            raise BrowserDataCollectionError(
                f"Failed to collect browser data: {error}"
            ) from error

        elements = self._to_collected_elements(raw_elements)
        snapshot = BrowserSnapshot(url=url, title=title, html=html, elements=elements)

        self._log_port.debug(
            "Browser data collected",
            url=url,
            title=title,
            element_count=len(elements),
        )
        self._event_bus.publish(
            BrowserDataCollectedEvent(url=url, title=title, element_count=len(elements))
        )
        return snapshot

    def _to_collected_elements(
        self, raw_elements: list[dict[str, Any]]
    ) -> tuple[CollectedElement, ...]:
        bounded_raw_elements = raw_elements[: self._max_elements]
        return tuple(
            CollectedElement(
                tag_name=item["tagName"],
                text=item["text"],
                visible=item["visible"],
                attributes=dict(item["attributes"]),
            )
            for item in bounded_raw_elements
        )
