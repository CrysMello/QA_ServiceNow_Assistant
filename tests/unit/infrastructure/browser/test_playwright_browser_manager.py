"""Unit tests for PlaywrightBrowserManager (SAD 13.3), using fakes for the
Playwright driver so no real browser installation is required.
"""

from __future__ import annotations

from typing import Any

import pytest
from playwright.sync_api import Error as PlaywrightError

from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.domain.exceptions.browser import (
    BrowserLaunchError,
    BrowserNotStartedError,
)
from qa_servicenow_assistant.domain.value_objects.configuration import (
    BrowserConfiguration,
)
from qa_servicenow_assistant.infrastructure.browser.playwright_browser_manager import (
    PlaywrightBrowserManager,
)


class FakePage:
    def __init__(self) -> None:
        self.default_timeout: int | None = None

    def set_default_timeout(self, timeout_ms: int) -> None:
        self.default_timeout = timeout_ms


class FakeBrowser:
    def __init__(self) -> None:
        self.closed = False
        self.new_page_calls: list[dict[str, Any]] = []

    def new_page(self, **kwargs: Any) -> FakePage:
        self.new_page_calls.append(kwargs)
        return FakePage()

    def close(self) -> None:
        self.closed = True


class FakeChromium:
    def __init__(self, error_to_raise: Exception | None = None) -> None:
        self.launch_calls: list[dict[str, Any]] = []
        self.browser = FakeBrowser()
        self._error_to_raise = error_to_raise

    def launch(self, **kwargs: Any) -> FakeBrowser:
        self.launch_calls.append(kwargs)
        if self._error_to_raise is not None:
            raise self._error_to_raise
        return self.browser


class FakePlaywright:
    def __init__(self, chromium: FakeChromium) -> None:
        self.chromium = chromium
        self.stopped = False

    def stop(self) -> None:
        self.stopped = True


class FakePlaywrightContextManager:
    """Mimics the object returned by sync_playwright(), which exposes start()."""

    def __init__(self, playwright: FakePlaywright) -> None:
        self.playwright = playwright
        self.start_call_count = 0

    def start(self) -> FakePlaywright:
        self.start_call_count += 1
        return self.playwright


class FakeLogPort(LogPort):
    def __init__(self) -> None:
        self.debug_calls: list[tuple[str, dict[str, Any]]] = []
        self.info_calls: list[tuple[str, dict[str, Any]]] = []

    def bind(self, **context: Any) -> "FakeLogPort":
        return self

    def trace(self, message: str, **context: Any) -> None:
        pass

    def debug(self, message: str, **context: Any) -> None:
        self.debug_calls.append((message, context))

    def info(self, message: str, **context: Any) -> None:
        self.info_calls.append((message, context))

    def warning(self, message: str, **context: Any) -> None:
        pass

    def error(self, message: str, **context: Any) -> None:
        pass

    def critical(self, message: str, **context: Any) -> None:
        pass


def _make_manager(
    chromium: FakeChromium, configuration: BrowserConfiguration | None = None
) -> tuple[PlaywrightBrowserManager, FakePlaywrightContextManager, FakeLogPort]:
    playwright = FakePlaywright(chromium)
    context_manager = FakePlaywrightContextManager(playwright)
    log_port = FakeLogPort()
    manager = PlaywrightBrowserManager(
        configuration or BrowserConfiguration(),
        log_port,
        playwright_starter=lambda: context_manager,
    )
    return manager, context_manager, log_port


def test_start_launches_chromium_with_headless_config() -> None:
    chromium = FakeChromium()
    manager, _, _ = _make_manager(chromium, BrowserConfiguration(headless=False))

    manager.start()

    assert chromium.launch_calls == [{"headless": False}]
    assert manager.is_running() is True


def test_start_with_msedge_browser_type_passes_channel() -> None:
    chromium = FakeChromium()
    manager, _, _ = _make_manager(chromium, BrowserConfiguration(browser_type="msedge"))

    manager.start()

    assert chromium.launch_calls == [{"headless": True, "channel": "msedge"}]


def test_start_is_idempotent() -> None:
    chromium = FakeChromium()
    manager, context_manager, log_port = _make_manager(chromium)

    manager.start()
    manager.start()

    assert context_manager.start_call_count == 1
    assert len(chromium.launch_calls) == 1
    assert any("no-op" in message for message, _ in log_port.debug_calls)


def test_start_wraps_launch_failure_into_browser_launch_error() -> None:
    chromium = FakeChromium(error_to_raise=PlaywrightError("executable not found"))
    manager, context_manager, _ = _make_manager(chromium)

    with pytest.raises(BrowserLaunchError, match="executable not found"):
        manager.start()

    assert manager.is_running() is False
    assert context_manager.playwright.stopped is True  # partial state cleaned up


def test_new_page_before_start_raises() -> None:
    chromium = FakeChromium()
    manager, _, _ = _make_manager(chromium)

    with pytest.raises(BrowserNotStartedError):
        manager.new_page()


def test_new_page_creates_page_with_configured_viewport_and_timeout() -> None:
    chromium = FakeChromium()
    configuration = BrowserConfiguration(
        viewport_width=1280, viewport_height=720, timeout_ms=15_000
    )
    manager, _, _ = _make_manager(chromium, configuration)
    manager.start()

    page = manager.new_page()

    assert chromium.browser.new_page_calls == [
        {"viewport": {"width": 1280, "height": 720}}
    ]
    assert page.default_timeout == 15_000


def test_stop_closes_browser_and_playwright() -> None:
    chromium = FakeChromium()
    manager, context_manager, _ = _make_manager(chromium)
    manager.start()

    manager.stop()

    assert chromium.browser.closed is True
    assert context_manager.playwright.stopped is True
    assert manager.is_running() is False


def test_stop_when_not_running_is_noop() -> None:
    chromium = FakeChromium()
    manager, _, _ = _make_manager(chromium)

    manager.stop()  # must not raise

    assert manager.is_running() is False


def test_is_running_reflects_state() -> None:
    chromium = FakeChromium()
    manager, _, _ = _make_manager(chromium)

    assert manager.is_running() is False
    manager.start()
    assert manager.is_running() is True
    manager.stop()
    assert manager.is_running() is False
