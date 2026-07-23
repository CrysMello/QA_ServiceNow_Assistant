"""Playwright-based implementation of BrowserManagerPort (SAD 13.3).

Only browser lifecycle (launch, new page, stop) is handled here. Navigation,
DOM data collection and test-action execution belong to later modules
(Navigation Engine, Browser Data Collector, Automation Engine).
"""

from __future__ import annotations

from typing import Any, Callable

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page, sync_playwright

from qa_servicenow_assistant.application.ports.browser_manager_port import (
    BrowserManagerPort,
)
from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.domain.exceptions.browser import (
    BrowserLaunchError,
    BrowserNotStartedError,
)
from qa_servicenow_assistant.domain.value_objects.configuration import (
    BrowserConfiguration,
)


class PlaywrightBrowserManager(BrowserManagerPort):
    """Manages the lifecycle of a single Playwright (Chromium/Edge) browser.

    playwright_starter defaults to the real sync_playwright() factory but
    can be replaced (dependency injection) so unit tests do not need a real
    browser installation (RNF-007 - testabilidade).
    """

    def __init__(
        self,
        configuration: BrowserConfiguration,
        log_port: LogPort,
        *,
        playwright_starter: Callable[[], Any] = sync_playwright,
    ) -> None:
        self._configuration = configuration
        self._log_port = log_port
        self._playwright_starter = playwright_starter
        self._playwright: Any | None = None
        self._browser: Any | None = None

    def start(self) -> None:
        if self.is_running():
            self._log_port.debug("Browser already running; start() is a no-op")
            return

        playwright = self._playwright_starter().start()
        try:
            launch_kwargs: dict[str, Any] = {"headless": self._configuration.headless}
            if self._configuration.browser_type == "msedge":
                launch_kwargs["channel"] = "msedge"
            browser = playwright.chromium.launch(**launch_kwargs)
        except PlaywrightError as error:
            playwright.stop()
            raise BrowserLaunchError(
                "Failed to launch browser "
                f"(type={self._configuration.browser_type}): {error}"
            ) from error

        self._playwright = playwright
        self._browser = browser
        self._log_port.info(
            "Browser started",
            browser_type=self._configuration.browser_type,
            headless=self._configuration.headless,
        )

    def new_page(self) -> Page:
        if not self.is_running():
            raise BrowserNotStartedError("Cannot create a page before start() is called")

        page = self._browser.new_page(
            viewport={
                "width": self._configuration.viewport_width,
                "height": self._configuration.viewport_height,
            }
        )
        page.set_default_timeout(self._configuration.timeout_ms)
        self._log_port.debug("New browser page created")
        return page

    def stop(self) -> None:
        if not self.is_running():
            return

        self._browser.close()
        self._playwright.stop()
        self._browser = None
        self._playwright = None
        self._log_port.info("Browser stopped")

    def is_running(self) -> bool:
        return self._browser is not None
