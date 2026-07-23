"""Unit tests for PlaywrightAutomationExecutor, using a fake page/locator
(same pattern as test_playwright_navigation_executor.py)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from qa_servicenow_assistant.domain.exceptions.automation import (
    AutomationCommunicationError,
    ElementNotActionableError,
    InvalidUploadFileError,
)
from qa_servicenow_assistant.domain.value_objects.selector import Selector
from qa_servicenow_assistant.infrastructure.browser.playwright_automation_executor import (
    PlaywrightAutomationExecutor,
)


class FakeLocator:
    def __init__(self, error_to_raise: Exception | None = None) -> None:
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []
        self._error_to_raise = error_to_raise

    def _record(self, name: str, *args: Any, **kwargs: Any) -> None:
        self.calls.append((name, args, kwargs))
        if self._error_to_raise is not None:
            raise self._error_to_raise

    def click(self, **kwargs: Any) -> None:
        self._record("click", **kwargs)

    def dblclick(self, **kwargs: Any) -> None:
        self._record("dblclick", **kwargs)

    def fill(self, value: str, **kwargs: Any) -> None:
        self._record("fill", value, **kwargs)

    def clear(self, **kwargs: Any) -> None:
        self._record("clear", **kwargs)

    def select_option(self, value: str, **kwargs: Any) -> None:
        self._record("select_option", value, **kwargs)

    def check(self, **kwargs: Any) -> None:
        self._record("check", **kwargs)

    def uncheck(self, **kwargs: Any) -> None:
        self._record("uncheck", **kwargs)

    def set_input_files(self, file_path: str, **kwargs: Any) -> None:
        self._record("set_input_files", file_path, **kwargs)

    def press(self, key: str, **kwargs: Any) -> None:
        self._record("press", key, **kwargs)

    def hover(self, **kwargs: Any) -> None:
        self._record("hover", **kwargs)

    def wait_for(self, **kwargs: Any) -> None:
        self._record("wait_for", **kwargs)


class FakePage:
    def __init__(self, locator: FakeLocator) -> None:
        self._locator = locator
        self.locator_calls: list[str] = []

    def locator(self, value: str) -> FakeLocator:
        self.locator_calls.append(value)
        return self._locator


@pytest.fixture
def executor() -> PlaywrightAutomationExecutor:
    return PlaywrightAutomationExecutor()


def make_selector(value: str = "#submit") -> Selector:
    return Selector(strategy="id", value=value, priority=3)


def test_click_calls_locator_with_selector_and_timeout(executor: PlaywrightAutomationExecutor) -> None:
    locator = FakeLocator()
    page = FakePage(locator)

    executor.click(page, make_selector(), timeout_ms=5_000)

    assert page.locator_calls == ["#submit"]
    assert locator.calls == [("click", (), {"timeout": 5_000})]


def test_fill_passes_value_through(executor: PlaywrightAutomationExecutor) -> None:
    locator = FakeLocator()
    page = FakePage(locator)

    executor.fill(page, make_selector(), "INC0010001", timeout_ms=5_000)

    assert locator.calls == [("fill", ("INC0010001",), {"timeout": 5_000})]


def test_select_option_passes_value_through(executor: PlaywrightAutomationExecutor) -> None:
    locator = FakeLocator()
    page = FakePage(locator)

    executor.select_option(page, make_selector(), "high", timeout_ms=5_000)

    assert locator.calls == [("select_option", ("high",), {"timeout": 5_000})]


def test_select_option_accepts_multiple_values(executor: PlaywrightAutomationExecutor) -> None:
    locator = FakeLocator()
    page = FakePage(locator)

    executor.select_option(page, make_selector(), ["low", "high"], timeout_ms=5_000)

    assert locator.calls == [("select_option", (["low", "high"],), {"timeout": 5_000})]


def test_upload_file_passes_path_through(executor: PlaywrightAutomationExecutor, tmp_path: Path) -> None:
    evidence = tmp_path / "evidence.png"
    evidence.write_bytes(b"fake-png-bytes")
    locator = FakeLocator()
    page = FakePage(locator)

    executor.upload_file(page, make_selector(), str(evidence), timeout_ms=5_000)

    assert locator.calls == [("set_input_files", (str(evidence),), {"timeout": 5_000})]


def test_upload_file_accepts_multiple_paths(executor: PlaywrightAutomationExecutor, tmp_path: Path) -> None:
    first = tmp_path / "a.png"
    second = tmp_path / "b.png"
    first.write_bytes(b"1")
    second.write_bytes(b"2")
    locator = FakeLocator()
    page = FakePage(locator)

    executor.upload_file(page, make_selector(), [str(first), str(second)], timeout_ms=5_000)

    assert locator.calls == [
        ("set_input_files", ([str(first), str(second)],), {"timeout": 5_000})
    ]


@pytest.mark.parametrize("bad_path", [None, "", [], ()])
def test_upload_file_rejects_missing_or_empty_path_without_calling_playwright(
    executor: PlaywrightAutomationExecutor, bad_path: Any
) -> None:
    locator = FakeLocator()
    page = FakePage(locator)

    with pytest.raises(InvalidUploadFileError):
        executor.upload_file(page, make_selector(), bad_path, timeout_ms=5_000)

    assert locator.calls == []  # Playwright is never touched
    assert page.locator_calls == []  # not even page.locator() is called


def test_upload_file_rejects_nonexistent_path_without_calling_playwright(
    executor: PlaywrightAutomationExecutor, tmp_path: Path
) -> None:
    locator = FakeLocator()
    page = FakePage(locator)
    missing = tmp_path / "does_not_exist.png"

    with pytest.raises(InvalidUploadFileError, match="not found"):
        executor.upload_file(page, make_selector(), str(missing), timeout_ms=5_000)

    assert locator.calls == []


def test_upload_file_rejects_if_any_path_in_a_sequence_is_missing(
    executor: PlaywrightAutomationExecutor, tmp_path: Path
) -> None:
    existing = tmp_path / "exists.png"
    existing.write_bytes(b"1")
    missing = tmp_path / "does_not_exist.png"
    locator = FakeLocator()
    page = FakePage(locator)

    with pytest.raises(InvalidUploadFileError):
        executor.upload_file(page, make_selector(), [str(existing), str(missing)], timeout_ms=5_000)

    assert locator.calls == []


def test_upload_file_rejects_empty_string_entry_within_a_sequence(
    executor: PlaywrightAutomationExecutor, tmp_path: Path
) -> None:
    existing = tmp_path / "exists.png"
    existing.write_bytes(b"1")
    locator = FakeLocator()
    page = FakePage(locator)

    with pytest.raises(InvalidUploadFileError):
        executor.upload_file(page, make_selector(), [str(existing), ""], timeout_ms=5_000)

    assert locator.calls == []


def test_press_key_passes_key_through(executor: PlaywrightAutomationExecutor) -> None:
    locator = FakeLocator()
    page = FakePage(locator)

    executor.press_key(page, make_selector(), "Enter", timeout_ms=5_000)

    assert locator.calls == [("press", ("Enter",), {"timeout": 5_000})]


@pytest.mark.parametrize(
    "method, args",
    [
        ("double_click", ()),
        ("clear", ()),
        ("check", ()),
        ("uncheck", ()),
        ("hover", ()),
        ("wait_for", ()),
    ],
)
def test_simple_operations_call_expected_locator_method(
    executor: PlaywrightAutomationExecutor, method: str, args: tuple[Any, ...]
) -> None:
    locator = FakeLocator()
    page = FakePage(locator)

    getattr(executor, method)(page, make_selector(), *args, timeout_ms=5_000)

    assert len(locator.calls) == 1


def test_timeout_error_is_wrapped_as_element_not_actionable(executor: PlaywrightAutomationExecutor) -> None:
    locator = FakeLocator(error_to_raise=PlaywrightTimeoutError("Timeout 500ms exceeded"))
    page = FakePage(locator)

    with pytest.raises(ElementNotActionableError, match="500ms"):
        executor.click(page, make_selector(), timeout_ms=500)


def test_generic_playwright_error_is_wrapped_as_communication_error(
    executor: PlaywrightAutomationExecutor,
) -> None:
    locator = FakeLocator(error_to_raise=PlaywrightError("Target page, context or browser has been closed"))
    page = FakePage(locator)

    with pytest.raises(AutomationCommunicationError, match="closed"):
        executor.click(page, make_selector(), timeout_ms=500)


def test_element_not_actionable_error_carries_operation_selector_and_timeout_context(
    executor: PlaywrightAutomationExecutor,
) -> None:
    locator = FakeLocator(error_to_raise=PlaywrightTimeoutError("Timeout 500ms exceeded"))
    page = FakePage(locator)

    with pytest.raises(ElementNotActionableError) as excinfo:
        executor.fill(page, make_selector("#short_description"), "value", timeout_ms=500)

    message = str(excinfo.value)
    assert "operation=fill" in message
    assert 'selector="#short_description"' in message
    assert "strategy=id" in message
    assert "timeout_ms=500" in message


def test_communication_error_carries_operation_selector_and_timeout_context(
    executor: PlaywrightAutomationExecutor,
) -> None:
    locator = FakeLocator(error_to_raise=PlaywrightError("Target page, context or browser has been closed"))
    page = FakePage(locator)

    with pytest.raises(AutomationCommunicationError) as excinfo:
        executor.check(page, make_selector("#agree"), timeout_ms=500)

    message = str(excinfo.value)
    assert "operation=check" in message
    assert 'selector="#agree"' in message
    assert "strategy=id" in message
    assert "timeout_ms=500" in message
