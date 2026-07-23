"""Integration test chaining Browser Manager, Browser Data Collector,
Page Recognition and Navigation Engine with a real Chromium browser.

KnowledgeRepository is backed by a simple in-test fake holding a couple of
KnowledgePage entries, since Knowledge Manager (the module that will
provide a real adapter) is not implemented yet (Prompt 18). This is
exactly the seam PageRecognitionEngine's port was designed for.
"""

from __future__ import annotations

from typing import Any, Sequence

from qa_servicenow_assistant.application.ports.knowledge_repository_port import (
    KnowledgeRepository,
)
from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.application.services.navigation.navigation_engine import (
    NavigationEngine,
)
from qa_servicenow_assistant.application.services.page_recognition.navigation_validation_adapter import (
    PageRecognitionNavigationValidator,
)
from qa_servicenow_assistant.application.services.page_recognition.page_recognition_engine import (
    PageRecognitionEngine,
)
from qa_servicenow_assistant.domain.entities.knowledge_page import KnowledgePage
from qa_servicenow_assistant.domain.value_objects.configuration import (
    BrowserConfiguration,
)
from qa_servicenow_assistant.domain.value_objects.page_identifier import (
    PageIdentifier,
)
from qa_servicenow_assistant.infrastructure.browser.playwright_browser_data_collector import (
    PlaywrightBrowserDataCollector,
)
from qa_servicenow_assistant.infrastructure.browser.playwright_browser_manager import (
    PlaywrightBrowserManager,
)
from qa_servicenow_assistant.infrastructure.browser.playwright_navigation_executor import (
    PlaywrightNavigationExecutor,
)
from qa_servicenow_assistant.infrastructure.event_bus.in_memory_event_bus import (
    InMemoryEventBus,
)

_TARGET_PAGE_URL = (
    "data:text/html,<html><head><title>Submit Test Case</title></head>"
    "<body><button id=\"submit-btn\" data-testid=\"submit\">Submit</button></body></html>"
)


class RecordingLogPort(LogPort):
    def __init__(self) -> None:
        self.messages: list[str] = []

    def bind(self, **context: Any) -> "RecordingLogPort":
        return self

    def trace(self, message: str, **context: Any) -> None:
        pass

    def debug(self, message: str, **context: Any) -> None:
        pass

    def info(self, message: str, **context: Any) -> None:
        self.messages.append(message)

    def warning(self, message: str, **context: Any) -> None:
        self.messages.append(message)

    def error(self, message: str, **context: Any) -> None:
        self.messages.append(message)

    def critical(self, message: str, **context: Any) -> None:
        pass


class InTestKnowledgeRepository(KnowledgeRepository):
    """Stand-in for the future Knowledge Manager adapter (Prompt 18)."""

    def __init__(self, pages: Sequence[KnowledgePage]) -> None:
        self._pages = pages

    def get_known_pages(self) -> Sequence[KnowledgePage]:
        return self._pages


def test_navigation_engine_recognizes_real_page_via_page_recognition() -> None:
    log_port = RecordingLogPort()
    browser_manager = PlaywrightBrowserManager(BrowserConfiguration(), log_port)
    data_collector = PlaywrightBrowserDataCollector(log_port, InMemoryEventBus(log_port))
    known_page = KnowledgePage(
        key="submit_test_case",
        url_pattern="Submit Test Case",  # data: URLs have no real path; match on embedded text instead
        title="Submit Test Case",
        required_element_keys=("submit-btn",),
    )
    recognition_engine = PageRecognitionEngine(InTestKnowledgeRepository([known_page]), log_port)
    validator = PageRecognitionNavigationValidator(recognition_engine, data_collector)
    navigation_engine = NavigationEngine(PlaywrightNavigationExecutor(), validator, log_port)

    browser_manager.start()
    try:
        page = browser_manager.new_page()
        result = navigation_engine.navigate(
            page, PageIdentifier(key="submit_test_case"), _TARGET_PAGE_URL
        )
    finally:
        browser_manager.stop()

    assert result.success is True
    assert "Page recognized" in log_port.messages
    assert "Navigation completed" in log_port.messages


def test_navigation_engine_reports_failure_when_target_key_does_not_match() -> None:
    log_port = RecordingLogPort()
    browser_manager = PlaywrightBrowserManager(BrowserConfiguration(), log_port)
    data_collector = PlaywrightBrowserDataCollector(log_port, InMemoryEventBus(log_port))
    known_page = KnowledgePage(
        key="submit_test_case",
        url_pattern="Submit Test Case",
        title="Submit Test Case",
        required_element_keys=("submit-btn",),
    )
    recognition_engine = PageRecognitionEngine(InTestKnowledgeRepository([known_page]), log_port)
    validator = PageRecognitionNavigationValidator(recognition_engine, data_collector)
    navigation_engine = NavigationEngine(PlaywrightNavigationExecutor(), validator, log_port)

    browser_manager.start()
    try:
        page = browser_manager.new_page()
        result = navigation_engine.navigate(
            page, PageIdentifier(key="a_completely_different_page"), _TARGET_PAGE_URL
        )
    finally:
        browser_manager.stop()

    assert result.success is False
    assert "Navigation failed" in log_port.messages
