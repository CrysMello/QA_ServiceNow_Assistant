"""Unit tests for KnowledgeManager (SAD Cap. 11).

Uses a fake KnowledgeRepository and a fake LogPort (same pattern used
throughout this codebase), since the real infrastructure adapter
(JsonKnowledgeRepository) is exercised separately by its own unit tests
and by the integration test.
"""

from __future__ import annotations

from typing import Any, Sequence

from qa_servicenow_assistant.application.ports.knowledge_repository_port import (
    KnowledgeRepository,
)
from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.application.services.knowledge.knowledge_manager import (
    KnowledgeManager,
)
from qa_servicenow_assistant.domain.entities.knowledge_element import KnowledgeElement
from qa_servicenow_assistant.domain.entities.knowledge_page import KnowledgePage
from qa_servicenow_assistant.domain.value_objects.knowledge_workflow import (
    KnowledgeWorkflow,
)
from qa_servicenow_assistant.domain.value_objects.selector import Selector


class FakeLogPort(LogPort):
    def __init__(self) -> None:
        self.debug_calls: list[tuple[str, dict[str, Any]]] = []

    def bind(self, **context: Any) -> "FakeLogPort":
        return self

    def trace(self, message: str, **context: Any) -> None:
        pass

    def debug(self, message: str, **context: Any) -> None:
        self.debug_calls.append((message, context))

    def info(self, message: str, **context: Any) -> None:
        pass

    def warning(self, message: str, **context: Any) -> None:
        pass

    def error(self, message: str, **context: Any) -> None:
        pass

    def critical(self, message: str, **context: Any) -> None:
        pass


class FakeKnowledgeRepository(KnowledgeRepository):
    def __init__(self) -> None:
        self.page = KnowledgePage(key="incident_form", url_pattern="/incident.do")
        self.element = KnowledgeElement(key="submit_button", page_key="incident_form", description="Submit")
        self.selector = Selector(strategy="id", value="#submit", priority=3)
        self.workflow = KnowledgeWorkflow(key="create_incident", description="Create incident")
        self.fingerprint = "fp-1"
        self.version_is_valid = True

    def get_known_pages(self) -> Sequence[KnowledgePage]:
        return (self.page,)

    def get_page(self, key: str):
        return self.page if key == self.page.key else None

    def get_element(self, key: str):
        return self.element if key == self.element.key else None

    def get_selector(self, element_key: str):
        return self.selector if element_key == self.element.key else None

    def get_workflow(self, key: str):
        return self.workflow if key == self.workflow.key else None

    def get_fingerprint(self, page_key: str):
        return self.fingerprint if page_key == self.page.key else None

    def validate_version(self) -> bool:
        return self.version_is_valid


def test_get_known_pages_delegates_and_logs() -> None:
    repository = FakeKnowledgeRepository()
    log_port = FakeLogPort()
    manager = KnowledgeManager(repository, log_port)

    pages = manager.get_known_pages()

    assert pages == (repository.page,)
    assert len(log_port.debug_calls) == 1


def test_get_page_found_and_not_found() -> None:
    manager = KnowledgeManager(FakeKnowledgeRepository(), FakeLogPort())

    assert manager.get_page("incident_form") is not None
    assert manager.get_page("unknown") is None


def test_get_element_delegates() -> None:
    manager = KnowledgeManager(FakeKnowledgeRepository(), FakeLogPort())

    element = manager.get_element("submit_button")

    assert element is not None
    assert element.page_key == "incident_form"


def test_get_selector_delegates() -> None:
    manager = KnowledgeManager(FakeKnowledgeRepository(), FakeLogPort())

    selector = manager.get_selector("submit_button")

    assert selector is not None
    assert selector.value == "#submit"


def test_get_workflow_delegates() -> None:
    manager = KnowledgeManager(FakeKnowledgeRepository(), FakeLogPort())

    assert manager.get_workflow("create_incident") is not None
    assert manager.get_workflow("unknown") is None


def test_get_fingerprint_delegates() -> None:
    manager = KnowledgeManager(FakeKnowledgeRepository(), FakeLogPort())

    assert manager.get_fingerprint("incident_form") == "fp-1"
    assert manager.get_fingerprint("unknown") is None


def test_validate_version_delegates() -> None:
    repository = FakeKnowledgeRepository()
    repository.version_is_valid = False
    manager = KnowledgeManager(repository, FakeLogPort())

    assert manager.validate_version() is False


def test_knowledge_manager_is_itself_a_knowledge_repository() -> None:
    manager = KnowledgeManager(FakeKnowledgeRepository(), FakeLogPort())

    assert isinstance(manager, KnowledgeRepository)
