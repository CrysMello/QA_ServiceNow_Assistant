"""Unit tests for PlaywrightNavigationExecutor, using a fake page."""

from __future__ import annotations

from typing import Any

import pytest
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from qa_servicenow_assistant.domain.exceptions.navigation import (
    NavigationError,
    NavigationTimeoutError,
)
from qa_servicenow_assistant.infrastructure.browser.playwright_navigation_executor import (
    PlaywrightNavigationExecutor,
)


class FakePage:
    def __init__(self, error_to_raise: Exception | None = None) -> None:
        self.goto_calls: list[dict[str, Any]] = []
        self._error_to_raise = error_to_raise

    def goto(self, url: str, timeout: int, wait_until: str) -> None:
        self.goto_calls.append({"url": url, "timeout": timeout, "wait_until": wait_until})
        if self._error_to_raise is not None:
            raise self._error_to_raise


@pytest.fixture
def executor() -> PlaywrightNavigationExecutor:
    return PlaywrightNavigationExecutor()


def test_navigate_calls_goto_with_expected_arguments(executor: PlaywrightNavigationExecutor) -> None:
    page = FakePage()

    executor.navigate(page, "https://dev.service-now.com", 15_000)

    assert page.goto_calls == [
        {"url": "https://dev.service-now.com", "timeout": 15_000, "wait_until": "load"}
    ]


def test_navigate_wraps_timeout_error(executor: PlaywrightNavigationExecutor) -> None:
    page = FakePage(error_to_raise=PlaywrightTimeoutError("Timeout 5000ms exceeded"))

    with pytest.raises(NavigationTimeoutError, match="5000ms"):
        executor.navigate(page, "https://dev.service-now.com", 5_000)


def test_navigate_wraps_generic_playwright_error(executor: PlaywrightNavigationExecutor) -> None:
    page = FakePage(error_to_raise=PlaywrightError("net::ERR_CONNECTION_REFUSED"))

    with pytest.raises(NavigationError, match="ERR_CONNECTION_REFUSED"):
        executor.navigate(page, "https://dev.service-now.com", 5_000)
