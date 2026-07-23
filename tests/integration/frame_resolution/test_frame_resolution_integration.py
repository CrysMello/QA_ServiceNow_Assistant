"""Integration test chaining Browser Manager, Frame Resolver, Browser Data
Collector and Page Recognition with a real Chromium browser and a real
iframe - proving the resolved frame handle can be used directly wherever
a "page" is expected (SAD 9.7 opaque contract), since Playwright's Frame
exposes the same url/title/content/evaluate surface as Page.
"""

from __future__ import annotations

from typing import Any, Sequence

from qa_servicenow_assistant.application.ports.knowledge_repository_port import (
    KnowledgeRepository,
)
from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.application.services.resolution.frame_resolution_engine import (
    FrameResolutionEngine,
)
from qa_servicenow_assistant.application.services.page_recognition.page_recognition_engine import (
    PageRecognitionEngine,
)
from qa_servicenow_assistant.domain.entities.knowledge_page import KnowledgePage
from qa_servicenow_assistant.domain.exceptions.frame import FrameNotFoundError
from qa_servicenow_assistant.domain.value_objects.configuration import (
    BrowserConfiguration,
)
from qa_servicenow_assistant.infrastructure.browser.playwright_browser_data_collector import (
    PlaywrightBrowserDataCollector,
)
from qa_servicenow_assistant.infrastructure.browser.playwright_browser_manager import (
    PlaywrightBrowserManager,
)
from qa_servicenow_assistant.infrastructure.browser.playwright_frame_detector import (
    PlaywrightFrameDetector,
)
from qa_servicenow_assistant.infrastructure.event_bus.in_memory_event_bus import (
    InMemoryEventBus,
)

_MAIN_PAGE_HTML = """
<html><body>
    <h1>Main Page</h1>
    <iframe name="content_frame" srcdoc="&lt;html&gt;&lt;body&gt;&lt;button id=&quot;inner-btn&quot; data-testid=&quot;inner-submit&quot;&gt;Inner Submit&lt;/button&gt;&lt;/body&gt;&lt;/html&gt;"></iframe>
</body></html>
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
        self.messages.append(message)

    def critical(self, message: str, **context: Any) -> None:
        pass


class InTestKnowledgeRepository(KnowledgeRepository):
    def __init__(self, pages: Sequence[KnowledgePage]) -> None:
        self._pages = pages

    def get_known_pages(self) -> Sequence[KnowledgePage]:
        return self._pages


def test_resolved_frame_can_be_collected_and_recognized() -> None:
    log_port = RecordingLogPort()
    browser_manager = PlaywrightBrowserManager(BrowserConfiguration(), log_port)
    frame_engine = FrameResolutionEngine(PlaywrightFrameDetector(), log_port)
    collector = PlaywrightBrowserDataCollector(log_port, InMemoryEventBus(log_port))
    known_page = KnowledgePage(
        key="inner_frame_content", url_pattern="srcdoc", required_element_keys=("inner-submit",)
    )
    recognition_engine = PageRecognitionEngine(InTestKnowledgeRepository([known_page]), log_port)

    browser_manager.start()
    try:
        page = browser_manager.new_page()
        page.set_content(_MAIN_PAGE_HTML)
        page.wait_for_timeout(200)

        frame_handle = frame_engine.resolve(page, frame_name="content_frame")
        snapshot = collector.collect(frame_handle)
        recognition_result = recognition_engine.recognize(snapshot)
    finally:
        browser_manager.stop()

    assert any(element.attributes.get("data_testid") == "inner-submit" for element in snapshot.elements)
    assert recognition_result.is_recognized is True
    assert recognition_result.matched_page == known_page
    assert "Frame resolved" in log_port.messages


def test_resolving_unknown_frame_name_raises_and_is_logged() -> None:
    log_port = RecordingLogPort()
    browser_manager = PlaywrightBrowserManager(BrowserConfiguration(), log_port)
    frame_engine = FrameResolutionEngine(PlaywrightFrameDetector(), log_port)

    browser_manager.start()
    try:
        page = browser_manager.new_page()
        page.set_content(_MAIN_PAGE_HTML)
        page.wait_for_timeout(200)

        try:
            frame_engine.resolve(page, frame_name="does_not_exist")
            raised = False
        except FrameNotFoundError:
            raised = True
    finally:
        browser_manager.stop()

    assert raised is True
    assert "Frame resolution failed" in log_port.messages
