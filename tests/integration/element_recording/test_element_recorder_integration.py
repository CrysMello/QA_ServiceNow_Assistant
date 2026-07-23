"""Integration test chaining Browser Manager, Browser Data Collector and
Element Recorder with a real Chromium browser.
"""

from __future__ import annotations

from typing import Any

from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.application.services.element_recording.element_recorder import (
    ElementRecorder,
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


def test_elements_collected_from_real_page_can_be_recorded() -> None:
    log_port = RecordingLogPort()
    event_bus = InMemoryEventBus(log_port)
    browser_manager = PlaywrightBrowserManager(BrowserConfiguration(), log_port)
    collector = PlaywrightBrowserDataCollector(log_port, event_bus)
    recorder = ElementRecorder(log_port)

    browser_manager.start()
    try:
        page = browser_manager.new_page()
        page.set_content(_SAMPLE_PAGE_HTML)
        snapshot = collector.collect(page)

        recorded = recorder.record_many(snapshot.elements, label="observed", page_url=snapshot.url)
    finally:
        browser_manager.stop()

    assert len(recorded) == len(snapshot.elements) == 2
    assert recorder.records == recorded
    tag_names = {record.element.tag_name for record in recorded}
    assert tag_names == {"button", "input"}
    assert "Element recorded" in log_port.messages
