"""Integration test for PlaywrightBrowserManager using a real Chromium
browser (SAD 13.3).

Requires Playwright browser binaries to be installed locally
(`playwright install chromium`); this is an operational setup step, not a
new dependency (Playwright itself is already approved - SAD 2.5).
"""

from __future__ import annotations

from typing import Any

from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.domain.value_objects.configuration import (
    BrowserConfiguration,
)
from qa_servicenow_assistant.infrastructure.browser.playwright_browser_manager import (
    PlaywrightBrowserManager,
)


class RecordingLogPort(LogPort):
    """Minimal LogPort recording message text, for assertions."""

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


def test_real_browser_lifecycle_start_new_page_stop() -> None:
    configuration = BrowserConfiguration(headless=True, timeout_ms=10_000)
    log_port = RecordingLogPort()
    manager = PlaywrightBrowserManager(configuration, log_port)

    manager.start()
    try:
        assert manager.is_running() is True

        page = manager.new_page()
        page.set_content("<html><body><h1>QA ServiceNow Assistant</h1></body></html>")

        assert "QA ServiceNow Assistant" in page.content()
    finally:
        manager.stop()

    assert manager.is_running() is False
    assert "Browser started" in log_port.messages
    assert "Browser stopped" in log_port.messages


def test_start_twice_reuses_the_same_running_browser() -> None:
    manager = PlaywrightBrowserManager(BrowserConfiguration(), RecordingLogPort())

    manager.start()
    try:
        first_page = manager.new_page()
        manager.start()  # idempotent, must not launch a second browser
        second_page = manager.new_page()

        first_page.set_content("<p>first</p>")
        second_page.set_content("<p>second</p>")

        assert "first" in first_page.content()
        assert "second" in second_page.content()
    finally:
        manager.stop()
