"""Integration test for Knowledge Manager using the real
JsonKnowledgeRepository against a real filesystem Knowledge Base
(tmp_path), wired through KnowledgeManager and fed into a real
PageRecognitionEngine + NavigationEngine + a real Chromium browser -
demonstrating that KnowledgeManager is a drop-in replacement for the
InTestKnowledgeRepository fake every other Page Recognition test uses
(SAD 11.8 - "Os consumidores utilizam exclusivamente interfaces
publicas").
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.application.services.knowledge.knowledge_manager import (
    KnowledgeManager,
)
from qa_servicenow_assistant.application.services.navigation.navigation_engine import (
    NavigationEngine,
)
from qa_servicenow_assistant.application.services.page_recognition.navigation_validation_adapter import (
    PageRecognitionNavigationValidator,
)
from qa_servicenow_assistant.application.services.page_recognition.page_recognition_engine import (
    PageRecognitionEngine,
)
from qa_servicenow_assistant.domain.value_objects.configuration import (
    BrowserConfiguration,
)
from qa_servicenow_assistant.domain.value_objects.page_identifier import (
    PageIdentifier,
)
from qa_servicenow_assistant.infrastructure.browser.playwright_browser_data_collector import (
    PlaywrightBrowserDataCollector,
)
from qa_servicenow_assistant.infrastructure.browser.playwright_browser_manager import (
    PlaywrightBrowserManager,
)
from qa_servicenow_assistant.infrastructure.browser.playwright_navigation_executor import (
    PlaywrightNavigationExecutor,
)
from qa_servicenow_assistant.infrastructure.event_bus.in_memory_event_bus import (
    InMemoryEventBus,
)
from qa_servicenow_assistant.infrastructure.persistence.json_knowledge_repository import (
    JsonKnowledgeRepository,
)

_TARGET_PAGE_URL = (
    "data:text/html,<html><head><title>Submit Test Case</title></head>"
    "<body><button id=\"submit-btn\" data-testid=\"submit\">Submit</button></body></html>"
)


class RecordingLogPort(LogPort):
    def __init__(self) -> None:
        self.messages: list[str] = []

    def bind(self, **context: Any) -> "RecordingLogPort":
        return self

    def trace(self, message: str, **context: Any) -> None:
        pass

    def debug(self, message: str, **context: Any) -> None:
        self.messages.append(message)

    def info(self, message: str, **context: Any) -> None:
        self.messages.append(message)

    def warning(self, message: str, **context: Any) -> None:
        self.messages.append(message)

    def error(self, message: str, **context: Any) -> None:
        self.messages.append(message)

    def critical(self, message: str, **context: Any) -> None:
        pass


def _write_knowledge_base(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "manifest.json").write_text(json.dumps({"version": "1.0"}), encoding="utf-8")
    (directory / "pages.json").write_text(
        json.dumps(
            [
                {
                    "key": "submit_test_case",
                    # data: URLs have no real path; match on embedded text instead,
                    # same approach as the pre-existing Page Recognition integration test.
                    "url_pattern": "Submit Test Case",
                    "title": "Submit Test Case",
                    "required_element_keys": ["submit-btn"],
                }
            ]
        ),
        encoding="utf-8",
    )


def test_real_json_knowledge_repository_drives_real_page_recognition(tmp_path: Path) -> None:
    _write_knowledge_base(tmp_path)
    log_port = RecordingLogPort()

    json_repository = JsonKnowledgeRepository(tmp_path, log_port)
    knowledge_manager = KnowledgeManager(json_repository, log_port)

    browser_manager = PlaywrightBrowserManager(BrowserConfiguration(), log_port)
    data_collector = PlaywrightBrowserDataCollector(log_port, InMemoryEventBus(log_port))
    recognition_engine = PageRecognitionEngine(knowledge_manager, log_port)
    validator = PageRecognitionNavigationValidator(recognition_engine, data_collector)
    navigation_engine = NavigationEngine(PlaywrightNavigationExecutor(), validator, log_port)

    browser_manager.start()
    try:
        page = browser_manager.new_page()
        result = navigation_engine.navigate(
            page, PageIdentifier(key="submit_test_case"), _TARGET_PAGE_URL
        )
    finally:
        browser_manager.stop()

    assert result.success is True
    assert "Knowledge Base loaded" in log_port.messages
    assert "Page recognized" in log_port.messages
    assert "Navigation completed" in log_port.messages


def test_knowledge_manager_lookups_work_against_the_real_loaded_base(tmp_path: Path) -> None:
    _write_knowledge_base(tmp_path)
    log_port = RecordingLogPort()

    knowledge_manager = KnowledgeManager(JsonKnowledgeRepository(tmp_path, log_port), log_port)

    page = knowledge_manager.get_page("submit_test_case")
    assert page is not None
    assert page.title == "Submit Test Case"
    assert knowledge_manager.get_page("unknown") is None
    assert knowledge_manager.validate_version() is True
