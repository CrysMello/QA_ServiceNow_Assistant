"""Integration test for AutomationEngine using a real Chromium browser
(via PlaywrightBrowserManager) and the real PlaywrightAutomationExecutor,
exercising every SAD 13.4 operation against a real page, plus the
exception-based failure path (SAD 13.8) against a genuinely missing
element.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.application.services.automation.automation_engine import (
    AutomationEngine,
)
from qa_servicenow_assistant.domain.exceptions.automation import (
    ElementNotActionableError,
)
from qa_servicenow_assistant.domain.value_objects.configuration import (
    BrowserConfiguration,
)
from qa_servicenow_assistant.domain.value_objects.selector import Selector
from qa_servicenow_assistant.infrastructure.browser.playwright_automation_executor import (
    PlaywrightAutomationExecutor,
)
from qa_servicenow_assistant.infrastructure.browser.playwright_browser_manager import (
    PlaywrightBrowserManager,
)

_FORM_HTML = """
<html><body>
<button id="submit-btn" onclick="document.getElementById('result').innerText='clicked'">Submit</button>
<button id="dbl-btn" ondblclick="document.getElementById('dbl-result').innerText='dblclicked'">Target</button>
<input id="text-field" type="text" />
<select id="priority">
  <option value="low">Low</option>
  <option value="high">High</option>
</select>
<input id="agree" type="checkbox" />
<input id="file-input" type="file" />
<select id="tags" multiple>
  <option value="a">A</option>
  <option value="b">B</option>
  <option value="c">C</option>
</select>
<input id="multi-file-input" type="file" multiple />
<div id="hover-target" onmouseover="this.innerText='hovered'">Hover me</div>
<input id="key-field" type="text" />
<div id="result"></div>
<div id="dbl-result"></div>
</body></html>
"""


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
        pass

    def error(self, message: str, **context: Any) -> None:
        self.messages.append(message)

    def critical(self, message: str, **context: Any) -> None:
        pass


def selector(css: str) -> Selector:
    return Selector(strategy="css", value=css, priority=5)


def test_every_supported_operation_against_a_real_page(tmp_path: Path) -> None:
    log_port = RecordingLogPort()
    browser_manager = PlaywrightBrowserManager(BrowserConfiguration(), log_port)
    engine = AutomationEngine(PlaywrightAutomationExecutor(), log_port)

    upload_path = tmp_path / "evidence.txt"
    upload_path.write_text("evidence", encoding="utf-8")

    browser_manager.start()
    try:
        page = browser_manager.new_page()
        page.set_content(_FORM_HTML)

        engine.click(page, selector("#submit-btn"), timeout_ms=2_000)
        assert page.locator("#result").inner_text() == "clicked"

        engine.double_click(page, selector("#dbl-btn"), timeout_ms=2_000)
        assert page.locator("#dbl-result").inner_text() == "dblclicked"

        engine.fill(page, selector("#text-field"), "INC0010001", timeout_ms=2_000)
        assert page.locator("#text-field").input_value() == "INC0010001"

        engine.clear(page, selector("#text-field"), timeout_ms=2_000)
        assert page.locator("#text-field").input_value() == ""

        engine.select_option(page, selector("#priority"), "high", timeout_ms=2_000)
        assert page.locator("#priority").input_value() == "high"

        engine.check(page, selector("#agree"), timeout_ms=2_000)
        assert page.locator("#agree").is_checked() is True

        engine.uncheck(page, selector("#agree"), timeout_ms=2_000)
        assert page.locator("#agree").is_checked() is False

        engine.upload_file(page, selector("#file-input"), str(upload_path), timeout_ms=2_000)
        uploaded_count = page.locator("#file-input").evaluate("el => el.files.length")
        assert uploaded_count == 1

        engine.press_key(page, selector("#key-field"), "A", timeout_ms=2_000)
        assert page.locator("#key-field").input_value() == "A"

        engine.hover(page, selector("#hover-target"), timeout_ms=2_000)
        assert page.locator("#hover-target").inner_text() == "hovered"

        engine.wait_for(page, selector("#result"), timeout_ms=2_000)
    finally:
        browser_manager.stop()

    assert "Automation action failed" not in log_port.messages


def test_missing_element_raises_element_not_actionable_error() -> None:
    log_port = RecordingLogPort()
    browser_manager = PlaywrightBrowserManager(BrowserConfiguration(), log_port)
    engine = AutomationEngine(PlaywrightAutomationExecutor(), log_port)

    browser_manager.start()
    try:
        page = browser_manager.new_page()
        page.set_content(_FORM_HTML)

        with pytest.raises(ElementNotActionableError):
            engine.click(page, selector("#does-not-exist"), timeout_ms=500)
    finally:
        browser_manager.stop()

    assert "Automation action failed" in log_port.messages


def test_select_option_and_upload_file_accept_multiple_values(tmp_path: Path) -> None:
    log_port = RecordingLogPort()
    browser_manager = PlaywrightBrowserManager(BrowserConfiguration(), log_port)
    engine = AutomationEngine(PlaywrightAutomationExecutor(), log_port)

    first_file = tmp_path / "one.txt"
    first_file.write_text("1", encoding="utf-8")
    second_file = tmp_path / "two.txt"
    second_file.write_text("2", encoding="utf-8")

    browser_manager.start()
    try:
        page = browser_manager.new_page()
        page.set_content(_FORM_HTML)

        engine.select_option(page, selector("#tags"), ["a", "c"], timeout_ms=2_000)
        selected = page.locator("#tags").evaluate(
            "el => Array.from(el.selectedOptions).map(o => o.value)"
        )
        assert selected == ["a", "c"]

        engine.upload_file(
            page, selector("#multi-file-input"), [str(first_file), str(second_file)], timeout_ms=2_000
        )
        uploaded_names = page.locator("#multi-file-input").evaluate(
            "el => Array.from(el.files).map(f => f.name)"
        )
        assert uploaded_names == ["one.txt", "two.txt"]
    finally:
        browser_manager.stop()
