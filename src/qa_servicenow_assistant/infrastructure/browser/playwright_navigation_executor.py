"""Playwright-based implementation of NavigationExecutorPort (SAD 14.5 -
estrategia "Load State")."""

from __future__ import annotations

from typing import Any

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from qa_servicenow_assistant.application.ports.navigation_executor_port import (
    NavigationExecutorPort,
)
from qa_servicenow_assistant.domain.exceptions.navigation import (
    NavigationError,
    NavigationTimeoutError,
)


class PlaywrightNavigationExecutor(NavigationExecutorPort):
    """Navigates a real Playwright page and waits for the load event."""

    def navigate(self, page: Any, url: str, timeout_ms: int) -> None:
        try:
            page.goto(url, timeout=timeout_ms, wait_until="load")
        except PlaywrightTimeoutError as error:
            raise NavigationTimeoutError(
                f"Timed out navigating to {url} after {timeout_ms}ms"
            ) from error
        except PlaywrightError as error:
            raise NavigationError(f"Failed to navigate to {url}: {error}") from error
