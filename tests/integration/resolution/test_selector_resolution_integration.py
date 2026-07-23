"""Integration test chaining Browser Manager, Browser Data Collector and
Selector Resolution Engine with a real Chromium browser, including a
real duplicate-id scenario to prove uniqueness detection against actual
DOM data (not just hand-built fakes).
"""

from __future__ import annotations

from typing import Any

from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.application.services.resolution.selector_resolution_engine import (
    SelectorResolutionEngine,
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

_PAGE_WITH_DUPLICATE_ID = """
<html>
<body>
    <button id="dup" data-testid="submit-primary">Submit</button>
    <button id="dup">Submit</button>
    <input name="username" type="text" />
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
        self.messages.append(message)

    def error(self, message: str, **context: Any) -> None:
        self.messages.append(message)

    def critical(self, message: str, **context: Any) -> None:
        pass


def test_resolves_unique_data_testid_despite_duplicate_ids_on_real_page() -> None:
    log_port = RecordingLogPort()
    browser_manager = PlaywrightBrowserManager(BrowserConfiguration(), log_port)
    collector = PlaywrightBrowserDataCollector(log_port, InMemoryEventBus(log_port))
    engine = SelectorResolutionEngine(log_port)

    browser_manager.start()
    try:
        page = browser_manager.new_page()
        page.set_content(_PAGE_WITH_DUPLICATE_ID)
        snapshot = collector.collect(page)

        target = next(
            element for element in snapshot.elements if element.attributes.get("data_testid") == "submit-primary"
        )
        result = engine.resolve(target, snapshot)
    finally:
        browser_manager.stop()

    assert result.selector.strategy == "data_testid"
    assert result.is_unique is True
    assert "Selector resolved" in log_port.messages  # exact match: no suffix for the unique case


def test_reports_non_unique_when_only_duplicate_id_is_available() -> None:
    log_port = RecordingLogPort()
    browser_manager = PlaywrightBrowserManager(BrowserConfiguration(), log_port)
    collector = PlaywrightBrowserDataCollector(log_port, InMemoryEventBus(log_port))
    engine = SelectorResolutionEngine(log_port)

    browser_manager.start()
    try:
        page = browser_manager.new_page()
        page.set_content(_PAGE_WITH_DUPLICATE_ID)
        snapshot = collector.collect(page)

        second_button = next(
            element
            for element in snapshot.elements
            if element.attributes.get("id") == "dup" and not element.attributes.get("data_testid")
        )
        result = engine.resolve(second_button, snapshot)
    finally:
        browser_manager.stop()

    # id is duplicated (2 buttons share it) and text is duplicated too
    # (both say "Submit") - no candidate is unique, so the resolver
    # returns the highest-priority candidate (id) best-effort.
    assert result.selector.strategy == "id"
    assert result.is_unique is False
    assert "Selector resolved but not confirmed unique in snapshot" in log_port.messages
