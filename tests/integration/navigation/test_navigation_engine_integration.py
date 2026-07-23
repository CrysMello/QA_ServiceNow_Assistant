"""Integration test for NavigationEngine using a real Chromium browser
(via PlaywrightBrowserManager) and the real PlaywrightNavigationExecutor,
demonstrating compatibility across Browser Manager, Navigation Engine and
Log Engine.

A minimal stub NavigationValidationPort is used because Page Recognition
(the module that will implement it for real) is not built yet - this is
exactly the seam Dependency Inversion is meant to allow.
"""

from __future__ import annotations

from typing import Any

from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.application.ports.navigation_validation_port import (
    NavigationValidationPort,
)
from qa_servicenow_assistant.application.services.navigation.navigation_engine import (
    NavigationEngine,
)
from qa_servicenow_assistant.domain.value_objects.configuration import (
    BrowserConfiguration,
)
from qa_servicenow_assistant.domain.value_objects.page_identifier import (
    PageIdentifier,
)
from qa_servicenow_assistant.infrastructure.browser.playwright_browser_manager import (
    PlaywrightBrowserManager,
)
from qa_servicenow_assistant.infrastructure.browser.playwright_navigation_executor import (
    PlaywrightNavigationExecutor,
)

_TARGET_PAGE_URL = "data:text/html,<html><body><h1>Target Page</h1></body></html>"
_UNREACHABLE_URL = "https://10.255.255.1/"


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
        pass

    def error(self, message: str, **context: Any) -> None:
        self.messages.append(message)

    def critical(self, message: str, **context: Any) -> None:
        pass


class TitleMatchesValidator(NavigationValidationPort):
    """Minimal stand-in for the future Page Recognition module."""

    def __init__(self, expected_title: str) -> None:
        self._expected_title = expected_title

    def validate(self, page: Any, target: PageIdentifier) -> bool:
        return page.title() == self._expected_title


def test_real_navigation_to_target_page_succeeds() -> None:
    log_port = RecordingLogPort()
    browser_manager = PlaywrightBrowserManager(BrowserConfiguration(), log_port)
    engine = NavigationEngine(
        PlaywrightNavigationExecutor(),
        TitleMatchesValidator(expected_title=""),
        log_port,
    )

    browser_manager.start()
    try:
        page = browser_manager.new_page()
        result = engine.navigate(page, PageIdentifier(key="target_page"), _TARGET_PAGE_URL)
    finally:
        browser_manager.stop()

    assert result.success is True
    assert "Navigation started" in log_port.messages
    assert "Navigation completed" in log_port.messages


def test_real_navigation_timeout_is_reported_without_raising() -> None:
    log_port = RecordingLogPort()
    browser_manager = PlaywrightBrowserManager(BrowserConfiguration(), log_port)
    engine = NavigationEngine(
        PlaywrightNavigationExecutor(),
        TitleMatchesValidator(expected_title="unreachable"),
        log_port,
    )

    browser_manager.start()
    try:
        page = browser_manager.new_page()
        result = engine.navigate(
            page, PageIdentifier(key="unreachable"), _UNREACHABLE_URL, timeout_ms=1_500
        )
    finally:
        browser_manager.stop()

    assert result.success is False
    assert result.error_message is not None
    assert "Navigation failed" in log_port.messages
