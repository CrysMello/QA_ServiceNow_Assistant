"""Integration test for RetryEngine wrapping a real PlaywrightNavigationExecutor
against an unreachable address (via PlaywrightBrowserManager), demonstrating
compatibility across Browser Manager, Navigation Engine's own executor port
and Retry Engine: a genuine NavigationTimeoutError raised by real Playwright
code is classified TRANSIENT and retried per policy, then reported as a
failed RetryOutcome once attempts are exhausted (never raised).
"""

from __future__ import annotations

from typing import Any

from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.application.services.retry.retry_engine import (
    RetryEngine,
)
from qa_servicenow_assistant.domain.value_objects.configuration import (
    BrowserConfiguration,
    RetryConfiguration,
)
from qa_servicenow_assistant.domain.value_objects.failure_classification import (
    FailureClassification,
)
from qa_servicenow_assistant.infrastructure.browser.playwright_browser_manager import (
    PlaywrightBrowserManager,
)
from qa_servicenow_assistant.infrastructure.browser.playwright_navigation_executor import (
    PlaywrightNavigationExecutor,
)

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
        self.messages.append(message)

    def error(self, message: str, **context: Any) -> None:
        self.messages.append(message)

    def critical(self, message: str, **context: Any) -> None:
        pass


def test_real_navigation_timeout_is_retried_then_reported_as_failed_outcome() -> None:
    log_port = RecordingLogPort()
    browser_manager = PlaywrightBrowserManager(BrowserConfiguration(), log_port)
    executor = PlaywrightNavigationExecutor()
    retry_engine = RetryEngine(
        log_port,
        configuration=RetryConfiguration(
            max_attempts=2, backoff_strategy="fixed", base_delay_ms=100
        ),
    )

    browser_manager.start()
    try:
        page = browser_manager.new_page()
        outcome = retry_engine.execute(
            lambda: executor.navigate(page, _UNREACHABLE_URL, timeout_ms=1_500),
            operation_name="navigate_to_unreachable_host",
        )
    finally:
        browser_manager.stop()

    assert outcome.succeeded is False
    assert outcome.result is None
    assert outcome.final_error_message is not None
    assert "Timed out" in outcome.final_error_message
    assert len(outcome.attempts) == 2
    assert all(not attempt.succeeded for attempt in outcome.attempts)
    assert all(
        attempt.classification == FailureClassification.TRANSIENT
        for attempt in outcome.attempts
    )
    assert "Retry attempt failed" in log_port.messages
    assert "Retry stopped: max attempts reached" in log_port.messages
