"""Automation Engine (SAD Cap. 13).

Executes UI actions against an already-resolved Selector (SAD 13.2 -
"Consumir locators resolvidos pelo Selector Resolver"), logs every
attempt (SAD 13.5 passo 8 - "Registrar logs e metricas") and, like Frame
Resolver, logs and RE-RAISES on failure instead of returning a "failed"
result (SAD 13.8 - "Erros devem ser propagados como excecoes de
aplicacao padronizadas").

Deliberate scope boundaries, documented rather than silently absent:

- Element/locator RESOLUTION is not this module's job (SAD 13.2, 13.5
  passos 2-3): callers resolve a Selector via SelectorResolver/
  SelectorResolutionEngine (already implemented) before calling here.
  "Element Resolver" (SAD 7.3/13.3/13.5) has no dedicated Module
  Specifications chapter/prompt of its own in the official sequence -
  Selector Resolver is this codebase's realization of that
  responsibility.
- Retry (SAD 13.2, 13.3's "Retry Coordinator") is not performed here -
  Workflow Engine already wraps each step's action (which may call this
  engine) through Retry Engine (SAD 19.7) when one is configured;
  duplicating that here would retry at two layers at once.
- Evidence capture (SAD 13.2, 13.3's "Evidence Coordinator") is not
  performed here - Screenshot Engine does not exist yet (a later
  prompt), the same deliberate boundary already documented by Reporting
  Engine's EvidenceReference.
- Frame/page context selection (SAD 13.7, 13.8 - "dentro do contexto
  correto de pagina e frame") happens upstream via Frame Resolver; this
  engine receives whatever Page/Frame-like object the caller already
  resolved.

Correction (post-Prompt 20 review): select_option/upload_file accept a
single value/path or a sequence of them (single- and multi-select/
multi-file inputs); AutomationError is registered as TRANSIENT in
FailureClassifier's default registry, and every raised exception message
now embeds operation/selector/timeout_ms - both needed for an external
Retry Engine (Workflow Engine's, per step) to actually retry a
transient automation failure and to log it meaningfully when it does.
"""

from __future__ import annotations

from typing import Any, Callable, Sequence, Union

from qa_servicenow_assistant.application.ports.automation_executor_port import (
    AutomationExecutorPort,
)
from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.domain.exceptions.automation import AutomationError
from qa_servicenow_assistant.domain.value_objects.configuration import (
    BrowserConfiguration,
)
from qa_servicenow_assistant.domain.value_objects.selector import Selector

_OneOrMany = Union[str, Sequence[str]]


class AutomationEngine:
    """default timeout comes from BrowserConfiguration.timeout_ms (SAD
    21.3 - categoria Browser; no dedicated Automation config category
    exists in the SAD), overridable per call via timeout_ms."""

    def __init__(
        self,
        executor: AutomationExecutorPort,
        log_port: LogPort,
        configuration: BrowserConfiguration | None = None,
    ) -> None:
        self._executor = executor
        self._log_port = log_port
        self._configuration = configuration or BrowserConfiguration()

    def click(self, page: Any, selector: Selector, *, timeout_ms: int | None = None) -> None:
        self._run("click", page, selector, timeout_ms, self._executor.click)

    def double_click(self, page: Any, selector: Selector, *, timeout_ms: int | None = None) -> None:
        self._run("double_click", page, selector, timeout_ms, self._executor.double_click)

    def fill(self, page: Any, selector: Selector, value: str, *, timeout_ms: int | None = None) -> None:
        self._run(
            "fill", page, selector, timeout_ms,
            lambda p, s, *, timeout_ms: self._executor.fill(p, s, value, timeout_ms=timeout_ms),
        )

    def clear(self, page: Any, selector: Selector, *, timeout_ms: int | None = None) -> None:
        self._run("clear", page, selector, timeout_ms, self._executor.clear)

    def select_option(
        self, page: Any, selector: Selector, value: _OneOrMany, *, timeout_ms: int | None = None
    ) -> None:
        self._run(
            "select_option", page, selector, timeout_ms,
            lambda p, s, *, timeout_ms: self._executor.select_option(p, s, value, timeout_ms=timeout_ms),
        )

    def check(self, page: Any, selector: Selector, *, timeout_ms: int | None = None) -> None:
        self._run("check", page, selector, timeout_ms, self._executor.check)

    def uncheck(self, page: Any, selector: Selector, *, timeout_ms: int | None = None) -> None:
        self._run("uncheck", page, selector, timeout_ms, self._executor.uncheck)

    def upload_file(
        self, page: Any, selector: Selector, file_path: _OneOrMany, *, timeout_ms: int | None = None
    ) -> None:
        self._run(
            "upload_file", page, selector, timeout_ms,
            lambda p, s, *, timeout_ms: self._executor.upload_file(p, s, file_path, timeout_ms=timeout_ms),
        )

    def press_key(self, page: Any, selector: Selector, key: str, *, timeout_ms: int | None = None) -> None:
        self._run(
            "press_key", page, selector, timeout_ms,
            lambda p, s, *, timeout_ms: self._executor.press_key(p, s, key, timeout_ms=timeout_ms),
        )

    def hover(self, page: Any, selector: Selector, *, timeout_ms: int | None = None) -> None:
        self._run("hover", page, selector, timeout_ms, self._executor.hover)

    def wait_for(self, page: Any, selector: Selector, *, timeout_ms: int | None = None) -> None:
        self._run("wait_for", page, selector, timeout_ms, self._executor.wait_for)

    def _run(
        self,
        operation: str,
        page: Any,
        selector: Selector,
        timeout_ms: int | None,
        action: Callable[..., None],
    ) -> None:
        effective_timeout_ms = timeout_ms if timeout_ms is not None else self._configuration.timeout_ms
        self._log_port.debug(
            "Automation action started",
            operation=operation,
            selector=selector.value,
            strategy=selector.strategy,
            timeout_ms=effective_timeout_ms,
        )
        try:
            action(page, selector, timeout_ms=effective_timeout_ms)
        except AutomationError as error:
            self._log_port.error(
                "Automation action failed",
                operation=operation,
                selector=selector.value,
                error_type=type(error).__name__,
                error=str(error),
            )
            raise
        self._log_port.info(
            "Automation action completed", operation=operation, selector=selector.value
        )
