"""Integration test for PlaywrightBrowserDataCollector using a real
Chromium browser (via PlaywrightBrowserManager) and a real InMemoryEventBus,
demonstrating compatibility across the Browser Manager, Browser Data
Collector, Event Bus and Log Engine modules.
"""

from __future__ import annotations

from typing import Any

from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.domain.events.browser_data_collected_event import (
    BrowserDataCollectedEvent,
)
from qa_servicenow_assistant.domain.value_objects.configuration import (
    BrowserConfiguration,
)
from qa_servicenow_assistant.infrastructure.browser.playwright_browser_data_collector import (
    PlaywrightBrowserDataCollector,
)
from qa_servicenow_assistant.infrastructure.browser.playwright_browser_manager import (
    PlaywrightBrowserManager,
)
from qa_servicenow_assistant.infrastructure.event_bus.in_memory_event_bus import (
    InMemoryEventBus,
)

_SAMPLE_PAGE_HTML = """
<html>
<head><title>Test Page</title></head>
<body>
    <button id="submit-btn" data-testid="submit">Submit</button>
    <input name="username" type="text" />
    <a href="#" aria-label="Home link">Home</a>
</body>
</html>
"""


class RecordingLogPort(LogPort):
    def __init__(self) -> None:
        self.messages: list[str] = []

    def bind(self, **context: Any) -> "RecordingLogPort":
        return self

    def trace(self, message: str, **context: Any) -> None:
        pass

    def debug(self, message: str, **context: Any) -> None:
        self.messages.append(message)

    def info(self, message: str, **context: Any) -> None:
        self.messages.append(message)

    def warning(self, message: str, **context: Any) -> None:
        pass

    def error(self, message: str, **context: Any) -> None:
        pass

    def critical(self, message: str, **context: Any) -> None:
        pass


def test_collect_from_real_page_publishes_event_via_real_event_bus() -> None:
    log_port = RecordingLogPort()
    event_bus = InMemoryEventBus(log_port)
    received_events: list[BrowserDataCollectedEvent] = []
    event_bus.subscribe(BrowserDataCollectedEvent, received_events.append)

    browser_manager = PlaywrightBrowserManager(BrowserConfiguration(), log_port)
    collector = PlaywrightBrowserDataCollector(log_port, event_bus)

    browser_manager.start()
    try:
        page = browser_manager.new_page()
        page.set_content(_SAMPLE_PAGE_HTML)

        snapshot = collector.collect(page)
    finally:
        browser_manager.stop()

    assert snapshot.title == "Test Page"
    assert len(snapshot.elements) == 3

    tag_names = {element.tag_name for element in snapshot.elements}
    assert tag_names == {"button", "input", "a"}

    submit_button = next(
        element for element in snapshot.elements if element.attributes.get("data_testid") == "submit"
    )
    assert submit_button.text == "Submit"
    assert submit_button.visible is True

    assert len(received_events) == 1
    assert received_events[0].title == "Test Page"
    assert received_events[0].element_count == 3
