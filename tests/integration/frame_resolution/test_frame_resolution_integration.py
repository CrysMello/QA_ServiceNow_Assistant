"""Integration test chaining Browser Manager, Frame Resolver, Browser Data
Collector and Page Recognition with a real Chromium browser and a real,
DELAYED iframe - proving Frame Resolver's own condition-based wait
mechanism (RNF-010), not any fixed sleep, is what makes resolution work.

No test in this file uses page.wait_for_timeout() or time.sleep() to
paper over frame-loading timing. The iframe is injected via a browser-side
setTimeout (page.evaluate() returns immediately; the callback fires later,
inside the browser, independently of Python), and
FrameResolutionEngine.resolve() is what blocks - synchronously, via
Playwright's native "framenavigated" event - until the frame actually
appears or the timeout elapses.
"""

from __future__ import annotations

import time
from typing import Any, Sequence

import pytest

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
from qa_servicenow_assistant.domain.exceptions.frame import FrameTimeoutError
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

_MAIN_PAGE_HTML = "<html><body><h1>Main Page</h1></body></html>"

_INJECT_DELAYED_IFRAME_SCRIPT = """
() => {
    setTimeout(() => {
        const iframe = document.createElement('iframe');
        iframe.name = 'content_frame';
        iframe.srcdoc = '<html><body><button id="inner-btn" data-testid="inner-submit">Inner Submit</button></body></html>';
        document.body.appendChild(iframe);
    }, 300);
}
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
    """Stand-in predating the real Knowledge Manager adapter
    (JsonKnowledgeRepository, Prompt 18) - kept here since these tests
    only need get_known_pages(); the other KnowledgeRepository methods
    are trivial stand-ins so this class still satisfies the (now larger)
    ABC."""

    def __init__(self, pages: Sequence[KnowledgePage]) -> None:
        self._pages = pages

    def get_known_pages(self) -> Sequence[KnowledgePage]:
        return self._pages

    def get_page(self, key: str):
        return None

    def get_element(self, key: str):
        return None

    def get_selector(self, element_key: str):
        return None

    def get_workflow(self, key: str):
        return None

    def get_fingerprint(self, page_key: str):
        return None

    def validate_version(self) -> bool:
        return True


def test_resolve_waits_for_a_frame_that_appears_after_a_delay_and_then_collects_it() -> None:
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
        # Schedules the iframe ~300ms in the future, browser-side. This
        # call returns immediately - it does NOT block for 300ms.
        page.evaluate(_INJECT_DELAYED_IFRAME_SCRIPT)

        started_at = time.monotonic()
        # The iframe does not exist yet at this point. resolve() must
        # block via condition-based waiting until it appears.
        frame_handle = frame_engine.resolve(page, frame_name="content_frame", timeout_ms=5_000)
        elapsed_ms = (time.monotonic() - started_at) * 1000

        snapshot = collector.collect(frame_handle)
        recognition_result = recognition_engine.recognize(snapshot)
    finally:
        browser_manager.stop()

    # Proves this was a condition-based wait, not a full/fixed wait: it
    # returned close to the ~300ms the iframe actually took to appear,
    # nowhere near the 5000ms timeout budget.
    assert elapsed_ms < 2_000

    assert any(element.attributes.get("data_testid") == "inner-submit" for element in snapshot.elements)
    assert recognition_result.is_recognized is True
    assert recognition_result.matched_page == known_page
    assert "Frame resolved" in log_port.messages


def test_resolving_a_frame_name_that_never_appears_times_out_without_fallback() -> None:
    log_port = RecordingLogPort()
    browser_manager = PlaywrightBrowserManager(BrowserConfiguration(), log_port)
    frame_engine = FrameResolutionEngine(PlaywrightFrameDetector(), log_port)

    browser_manager.start()
    try:
        page = browser_manager.new_page()
        page.set_content(_MAIN_PAGE_HTML)
        # No iframe is ever injected.

        with pytest.raises(FrameTimeoutError):
            frame_engine.resolve(page, frame_name="does_not_exist", timeout_ms=800)
    finally:
        browser_manager.stop()

    assert "Frame resolution failed" not in log_port.messages  # failed earlier, at detection
    assert "Frame detection failed" in log_port.messages
