"""Navigation Engine (SAD Cap. 14).

Orchestrates page navigation: executes the navigation (via
NavigationExecutorPort), validates the resulting page (via
NavigationValidationPort), keeps an in-memory navigation history
(SAD 14.3 - History Manager) and logs every attempt.

Scope explicitly excluded from this module (SAD 14.6, 14.3): multi-tab/
multi-window handling and frame context switching (depend on Frame
Resolver, a later module), and the real page-matching algorithm (depends
on Page Recognition, a later module - only its abstract port is used
here). Contains no ServiceNow business rules (SAD 14.8).
"""

from __future__ import annotations

import time
from typing import Any

from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.application.ports.navigation_executor_port import (
    NavigationExecutorPort,
)
from qa_servicenow_assistant.application.ports.navigation_validation_port import (
    NavigationValidationPort,
)
from qa_servicenow_assistant.domain.exceptions.navigation import NavigationError
from qa_servicenow_assistant.domain.value_objects.configuration import (
    NavigationConfiguration,
)
from qa_servicenow_assistant.domain.value_objects.navigation_result import (
    NavigationResult,
)
from qa_servicenow_assistant.domain.value_objects.page_identifier import (
    PageIdentifier,
)


class NavigationEngine:
    """Coordinates navigation to a target page and validates the result.

    default timeout comes from NavigationConfiguration (SAD 14.3 - Timeout
    Manager depende do Configuration Manager); it can be overridden per
    call via the timeout_ms parameter of navigate().
    """

    def __init__(
        self,
        navigation_executor: NavigationExecutorPort,
        navigation_validator: NavigationValidationPort,
        log_port: LogPort,
        configuration: NavigationConfiguration | None = None,
    ) -> None:
        self._navigation_executor = navigation_executor
        self._navigation_validator = navigation_validator
        self._log_port = log_port
        self._configuration = configuration or NavigationConfiguration()
        self._history: list[NavigationResult] = []

    @property
    def history(self) -> tuple[NavigationResult, ...]:
        """Navigation attempts recorded so far, oldest first."""
        return tuple(self._history)

    def navigate(
        self,
        page: Any,
        target: PageIdentifier,
        url: str,
        *,
        timeout_ms: int | None = None,
    ) -> NavigationResult:
        """Navigate page to url and validate it matches target.

        Never raises for expected outcomes (timeout, navigation failure or
        validation mismatch) - all are reported as a NavigationResult with
        success=False, so callers can inspect and decide policy (e.g. a
        future Retry Engine) without exception-based control flow.
        """
        effective_timeout_ms = timeout_ms if timeout_ms is not None else self._configuration.timeout_ms
        started_at = time.monotonic()
        self._log_port.info("Navigation started", target=target.key, url=url)

        try:
            self._navigation_executor.navigate(page, url, effective_timeout_ms)
        except NavigationError as error:
            result = NavigationResult(
                target=target,
                url=url,
                success=False,
                duration_ms=self._elapsed_ms(started_at),
                error_message=str(error),
            )
            return self._record_and_log(result)

        is_valid = self._navigation_validator.validate(page, target)
        if not is_valid:
            result = NavigationResult(
                target=target,
                url=url,
                success=False,
                duration_ms=self._elapsed_ms(started_at),
                error_message=f"Page validation failed for target '{target.key}'",
            )
            return self._record_and_log(result)

        result = NavigationResult(
            target=target,
            url=url,
            success=True,
            duration_ms=self._elapsed_ms(started_at),
        )
        return self._record_and_log(result)

    def _record_and_log(self, result: NavigationResult) -> NavigationResult:
        self._history.append(result)
        if result.success:
            self._log_port.info(
                "Navigation completed",
                target=result.target.key,
                url=result.url,
                duration_ms=result.duration_ms,
            )
        else:
            self._log_port.error(
                "Navigation failed",
                target=result.target.key,
                url=result.url,
                error=result.error_message,
            )
        return result

    def _elapsed_ms(self, started_at: float) -> float:
        return (time.monotonic() - started_at) * 1000
