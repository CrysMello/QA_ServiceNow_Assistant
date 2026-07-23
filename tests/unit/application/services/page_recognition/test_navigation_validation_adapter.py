"""Unit tests for PageRecognitionNavigationValidator."""

from __future__ import annotations

from typing import Any, Sequence

from qa_servicenow_assistant.application.ports.browser_data_collector_port import (
    BrowserDataCollectorPort,
)
from qa_servicenow_assistant.application.ports.knowledge_repository_port import (
    KnowledgeRepository,
)
from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.application.services.page_recognition.navigation_validation_adapter import (
    PageRecognitionNavigationValidator,
)
from qa_servicenow_assistant.application.services.page_recognition.page_recognition_engine import (
    PageRecognitionEngine,
)
from qa_servicenow_assistant.domain.entities.knowledge_page import KnowledgePage
from qa_servicenow_assistant.domain.value_objects.browser_snapshot import (
    BrowserSnapshot,
)
from qa_servicenow_assistant.domain.value_objects.page_identifier import (
    PageIdentifier,
)


class FakeKnowledgeRepository(KnowledgeRepository):
    def __init__(self, pages: Sequence[KnowledgePage]) -> None:
        self._pages = pages

    def get_known_pages(self) -> Sequence[KnowledgePage]:
        return self._pages


class FakeBrowserDataCollector(BrowserDataCollectorPort):
    def __init__(self, snapshot: BrowserSnapshot) -> None:
        self._snapshot = snapshot
        self.collect_calls: list[Any] = []

    def collect(self, page: Any) -> BrowserSnapshot:
        self.collect_calls.append(page)
        return self._snapshot


class FakeLogPort(LogPort):
    def bind(self, **context: Any) -> "FakeLogPort":
        return self

    def trace(self, message: str, **context: Any) -> None:
        pass

    def debug(self, message: str, **context: Any) -> None:
        pass

    def info(self, message: str, **context: Any) -> None:
        pass

    def warning(self, message: str, **context: Any) -> None:
        pass

    def error(self, message: str, **context: Any) -> None:
        pass

    def critical(self, message: str, **context: Any) -> None:
        pass


_FAKE_PAGE = object()


def test_returns_true_when_recognized_page_matches_target() -> None:
    snapshot = BrowserSnapshot(url="https://dev.service-now.com/home", title="Home", html="<html></html>")
    known_page = KnowledgePage(key="home", url_pattern="/home")
    engine = PageRecognitionEngine(FakeKnowledgeRepository([known_page]), FakeLogPort())
    collector = FakeBrowserDataCollector(snapshot)
    validator = PageRecognitionNavigationValidator(engine, collector)

    assert validator.validate(_FAKE_PAGE, PageIdentifier(key="home")) is True
    assert collector.collect_calls == [_FAKE_PAGE]


def test_returns_false_when_recognized_page_does_not_match_target() -> None:
    snapshot = BrowserSnapshot(url="https://dev.service-now.com/home", title="Home", html="<html></html>")
    known_page = KnowledgePage(key="home", url_pattern="/home")
    engine = PageRecognitionEngine(FakeKnowledgeRepository([known_page]), FakeLogPort())
    validator = PageRecognitionNavigationValidator(engine, FakeBrowserDataCollector(snapshot))

    assert validator.validate(_FAKE_PAGE, PageIdentifier(key="test_plan_list")) is False


def test_returns_false_when_page_is_not_recognized_at_all() -> None:
    snapshot = BrowserSnapshot(url="https://dev.service-now.com/unknown", title="?", html="<html></html>")
    engine = PageRecognitionEngine(FakeKnowledgeRepository([]), FakeLogPort())
    validator = PageRecognitionNavigationValidator(engine, FakeBrowserDataCollector(snapshot))

    assert validator.validate(_FAKE_PAGE, PageIdentifier(key="home")) is False
