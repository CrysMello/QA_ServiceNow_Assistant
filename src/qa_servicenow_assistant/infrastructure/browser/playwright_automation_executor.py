"""Playwright-based implementation of AutomationExecutorPort (SAD 13.4,
13.5 passo 5-6: sincronizacao e execucao da acao).

Relies entirely on Playwright's own actionability wait (present, visible,
enabled, stable) built into every Locator action, bounded by timeout_ms -
no fixed/sleep-based waiting (RNF-010), same principle already applied by
Frame Resolver. selector.value is used as-is as the Playwright locator
string: SelectorResolver (SAD Cap. 17) already produces CSS selectors and
Playwright's own `text="..."` engine syntax, both of which page.locator()
accepts directly - no per-strategy translation is needed here.
"""

from __future__ import annotations

from typing import Any, Callable

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from qa_servicenow_assistant.application.ports.automation_executor_port import (
    AutomationExecutorPort,
)
from qa_servicenow_assistant.domain.exceptions.automation import (
    AutomationCommunicationError,
    ElementNotActionableError,
)
from qa_servicenow_assistant.domain.value_objects.selector import Selector


class PlaywrightAutomationExecutor(AutomationExecutorPort):
    def click(self, page: Any, selector: Selector, *, timeout_ms: int) -> None:
        self._act(page, selector, lambda locator: locator.click(timeout=timeout_ms))

    def double_click(self, page: Any, selector: Selector, *, timeout_ms: int) -> None:
        self._act(page, selector, lambda locator: locator.dblclick(timeout=timeout_ms))

    def fill(self, page: Any, selector: Selector, value: str, *, timeout_ms: int) -> None:
        self._act(page, selector, lambda locator: locator.fill(value, timeout=timeout_ms))

    def clear(self, page: Any, selector: Selector, *, timeout_ms: int) -> None:
        self._act(page, selector, lambda locator: locator.clear(timeout=timeout_ms))

    def select_option(self, page: Any, selector: Selector, value: str, *, timeout_ms: int) -> None:
        self._act(page, selector, lambda locator: locator.select_option(value, timeout=timeout_ms))

    def check(self, page: Any, selector: Selector, *, timeout_ms: int) -> None:
        self._act(page, selector, lambda locator: locator.check(timeout=timeout_ms))

    def uncheck(self, page: Any, selector: Selector, *, timeout_ms: int) -> None:
        self._act(page, selector, lambda locator: locator.uncheck(timeout=timeout_ms))

    def upload_file(self, page: Any, selector: Selector, file_path: str, *, timeout_ms: int) -> None:
        self._act(page, selector, lambda locator: locator.set_input_files(file_path, timeout=timeout_ms))

    def press_key(self, page: Any, selector: Selector, key: str, *, timeout_ms: int) -> None:
        self._act(page, selector, lambda locator: locator.press(key, timeout=timeout_ms))

    def hover(self, page: Any, selector: Selector, *, timeout_ms: int) -> None:
        self._act(page, selector, lambda locator: locator.hover(timeout=timeout_ms))

    def wait_for(self, page: Any, selector: Selector, *, timeout_ms: int) -> None:
        self._act(page, selector, lambda locator: locator.wait_for(timeout=timeout_ms))

    def _act(self, page: Any, selector: Selector, action: Callable[[Any], None]) -> None:
        locator = page.locator(selector.value)
        try:
            action(locator)
        except PlaywrightTimeoutError as error:
            raise ElementNotActionableError(
                f"Element '{selector.value}' was not actionable in time: {error}"
            ) from error
        except PlaywrightError as error:
            raise AutomationCommunicationError(
                f"Failed to act on element '{selector.value}': {error}"
            ) from error
