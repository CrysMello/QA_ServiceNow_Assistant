"""Playwright-based implementation of AutomationExecutorPort (SAD 13.4,
13.5 passo 5-6: sincronizacao e execucao da acao).

Relies entirely on Playwright's own actionability wait (present, visible,
enabled, stable) built into every Locator action, bounded by timeout_ms -
no fixed/sleep-based waiting (RNF-010), same principle already applied by
Frame Resolver. selector.value is used as-is as the Playwright locator
string: SelectorResolver (SAD Cap. 17) already produces CSS selectors and
Playwright's own `text="..."` engine syntax, both of which page.locator()
accepts directly - no per-strategy translation is needed here.

select_option/upload_file accept a single value/path or a sequence of
them - Playwright's Locator.select_option()/set_input_files() already
support both natively (empirically verified against a real <select
multiple> and <input type="file" multiple>), so no extra branching is
needed here beyond widening the type.

Every raised exception embeds operation, selector (value + strategy) and
timeout_ms directly in its message (correction: "contexto suficiente
para retry externo") - this is what actually reaches an external Retry
Engine's RetryAttempt.error_message/logs (which only ever capture
str(error), never structured exception attributes - the same convention
every other exception in this codebase already follows), so enriching
the message itself, rather than adding unused structured fields, is what
makes that context available where it is actually consumed.
"""

from __future__ import annotations

from typing import Any, Callable, Sequence, Union

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

_OneOrMany = Union[str, Sequence[str]]


class PlaywrightAutomationExecutor(AutomationExecutorPort):
    def click(self, page: Any, selector: Selector, *, timeout_ms: int) -> None:
        self._act("click", page, selector, timeout_ms, lambda locator: locator.click(timeout=timeout_ms))

    def double_click(self, page: Any, selector: Selector, *, timeout_ms: int) -> None:
        self._act(
            "double_click", page, selector, timeout_ms,
            lambda locator: locator.dblclick(timeout=timeout_ms),
        )

    def fill(self, page: Any, selector: Selector, value: str, *, timeout_ms: int) -> None:
        self._act(
            "fill", page, selector, timeout_ms,
            lambda locator: locator.fill(value, timeout=timeout_ms),
        )

    def clear(self, page: Any, selector: Selector, *, timeout_ms: int) -> None:
        self._act("clear", page, selector, timeout_ms, lambda locator: locator.clear(timeout=timeout_ms))

    def select_option(self, page: Any, selector: Selector, value: _OneOrMany, *, timeout_ms: int) -> None:
        self._act(
            "select_option", page, selector, timeout_ms,
            lambda locator: locator.select_option(value, timeout=timeout_ms),
        )

    def check(self, page: Any, selector: Selector, *, timeout_ms: int) -> None:
        self._act("check", page, selector, timeout_ms, lambda locator: locator.check(timeout=timeout_ms))

    def uncheck(self, page: Any, selector: Selector, *, timeout_ms: int) -> None:
        self._act(
            "uncheck", page, selector, timeout_ms,
            lambda locator: locator.uncheck(timeout=timeout_ms),
        )

    def upload_file(self, page: Any, selector: Selector, file_path: _OneOrMany, *, timeout_ms: int) -> None:
        self._act(
            "upload_file", page, selector, timeout_ms,
            lambda locator: locator.set_input_files(file_path, timeout=timeout_ms),
        )

    def press_key(self, page: Any, selector: Selector, key: str, *, timeout_ms: int) -> None:
        self._act(
            "press_key", page, selector, timeout_ms,
            lambda locator: locator.press(key, timeout=timeout_ms),
        )

    def hover(self, page: Any, selector: Selector, *, timeout_ms: int) -> None:
        self._act("hover", page, selector, timeout_ms, lambda locator: locator.hover(timeout=timeout_ms))

    def wait_for(self, page: Any, selector: Selector, *, timeout_ms: int) -> None:
        self._act(
            "wait_for", page, selector, timeout_ms,
            lambda locator: locator.wait_for(timeout=timeout_ms),
        )

    def _act(
        self,
        operation: str,
        page: Any,
        selector: Selector,
        timeout_ms: int,
        action: Callable[[Any], None],
    ) -> None:
        locator = page.locator(selector.value)
        try:
            action(locator)
        except PlaywrightTimeoutError as error:
            raise ElementNotActionableError(
                f"[{operation}] element '{selector.value}' (strategy={selector.strategy}) "
                f"was not actionable within {timeout_ms}ms: {error}"
            ) from error
        except PlaywrightError as error:
            raise AutomationCommunicationError(
                f"[{operation}] failed to act on element '{selector.value}' "
                f"(strategy={selector.strategy}, timeout_ms={timeout_ms}): {error}"
            ) from error
