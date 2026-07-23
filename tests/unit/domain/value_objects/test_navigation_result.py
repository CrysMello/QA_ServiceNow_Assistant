"""Unit tests for NavigationResult."""

from __future__ import annotations

from qa_servicenow_assistant.domain.value_objects.navigation_result import (
    NavigationResult,
)
from qa_servicenow_assistant.domain.value_objects.page_identifier import (
    PageIdentifier,
)


def test_success_result_defaults_to_no_error_message() -> None:
    result = NavigationResult(
        target=PageIdentifier(key="home"), url="https://dev.service-now.com", success=True, duration_ms=12.5
    )

    assert result.error_message is None


def test_failed_result_carries_error_message() -> None:
    result = NavigationResult(
        target=PageIdentifier(key="home"),
        url="https://dev.service-now.com",
        success=False,
        duration_ms=5.0,
        error_message="timeout",
    )

    assert result.success is False
    assert result.error_message == "timeout"
