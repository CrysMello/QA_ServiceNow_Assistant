"""Unit tests for PageRecognitionEngine."""

from __future__ import annotations

from typing import Any, Sequence

from qa_servicenow_assistant.application.ports.knowledge_repository_port import (
    KnowledgeRepository,
)
from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.application.services.page_recognition.page_recognition_engine import (
    PageRecognitionEngine,
)
from qa_servicenow_assistant.domain.entities.knowledge_page import KnowledgePage
from qa_servicenow_assistant.domain.value_objects.browser_snapshot import (
    BrowserSnapshot,
)


class FakeKnowledgeRepository(KnowledgeRepository):
    """Only get_known_pages() is exercised by these tests - the other
    KnowledgeRepository methods (added by Knowledge Manager, Prompt 18)
    are trivial stand-ins, same precedent as FakeLogPort adopting
    trace/critical/bind when LogPort grew those methods (ADR-0013)."""

    def __init__(self, pages: Sequence[KnowledgePage] = ()) -> None:
        self._pages = pages
        self.call_count = 0

    def get_known_pages(self) -> Sequence[KnowledgePage]:
        self.call_count += 1
        return self._pages

    def get_page(self, key: str):
        return None

    def get_element(self, key: str):
        return None

    def get_selector(self, element_key: str):
        return None

    def get_workflow(self, key: str):
        return None

    def get_fingerprint(self, page_key: str):
        return None

    def validate_version(self) -> bool:
        return True


class FakeLogPort(LogPort):
    def __init__(self) -> None:
        self.info_calls: list[tuple[str, dict[str, Any]]] = []
        self.warning_calls: list[tuple[str, dict[str, Any]]] = []

    def bind(self, **context: Any) -> "FakeLogPort":
        return self

    def trace(self, message: str, **context: Any) -> None:
        pass

    def debug(self, message: str, **context: Any) -> None:
        pass

    def info(self, message: str, **context: Any) -> None:
        self.info_calls.append((message, context))

    def warning(self, message: str, **context: Any) -> None:
        self.warning_calls.append((message, context))

    def error(self, message: str, **context: Any) -> None:
        pass

    def critical(self, message: str, **context: Any) -> None:
        pass


def _snapshot(url: str = "https://dev.service-now.com/home", title: str = "Home") -> BrowserSnapshot:
    return BrowserSnapshot(url=url, title=title, html="<html></html>")


def test_recognize_queries_repository_and_delegates_to_recognizer() -> None:
    page = KnowledgePage(key="home", url_pattern="/home")
    repository = FakeKnowledgeRepository(pages=[page])
    engine = PageRecognitionEngine(repository, FakeLogPort())

    result = engine.recognize(_snapshot())

    assert repository.call_count == 1
    assert result.matched_page == page


def test_recognized_page_logs_info() -> None:
    page = KnowledgePage(key="home", url_pattern="/home")
    log_port = FakeLogPort()
    engine = PageRecognitionEngine(FakeKnowledgeRepository(pages=[page]), log_port)

    engine.recognize(_snapshot())

    assert len(log_port.info_calls) == 1
    message, context = log_port.info_calls[0]
    assert message == "Page recognized"
    assert context["matched_page"] == "home"
    assert log_port.warning_calls == []


def test_unrecognized_page_logs_warning() -> None:
    log_port = FakeLogPort()
    engine = PageRecognitionEngine(FakeKnowledgeRepository(pages=[]), log_port)

    engine.recognize(_snapshot())

    assert len(log_port.warning_calls) == 1
    message, context = log_port.warning_calls[0]
    assert message == "Page not recognized"
    assert context["url"] == "https://dev.service-now.com/home"
    assert log_port.info_calls == []
