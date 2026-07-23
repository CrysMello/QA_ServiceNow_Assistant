"""Knowledge Manager (SAD Cap. 11).

Application-layer facade centralizing Knowledge Base access (SAD 11.2 -
"Fornecer APIs de consulta para a Application Layer"): every query is
delegated to an injected KnowledgeRepository (the real loading, parsing,
validation and indexing work already happened in that repository's own
construction - e.g. JsonKnowledgeRepository, SAD 10.3's "Knowledge
Adapter") and logged at debug level (SAD 11.2's "centralizar... consulta
dos artefatos" via the same Log Engine integration every other module in
this codebase uses for its own audit trail).

KnowledgeManager itself implements KnowledgeRepository (Decorator
pattern), so it can be injected anywhere a KnowledgeRepository is
expected - including PageRecognitionEngine, which has only ever depended
on the port, never on a concrete adapter (SAD 11.8 - "Os consumidores
utilizam exclusivamente interfaces publicas").

No business rules here (SAD 11.8 - "Nenhuma regra de negocio deve ser
implementada neste componente"): KnowledgeManager never interprets what a
page/element/selector/workflow MEANS, only looks them up and hands back
whatever the repository returned.
"""

from __future__ import annotations

from typing import Sequence

from qa_servicenow_assistant.application.ports.knowledge_repository_port import (
    KnowledgeRepository,
)
from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.domain.entities.knowledge_element import KnowledgeElement
from qa_servicenow_assistant.domain.entities.knowledge_page import KnowledgePage
from qa_servicenow_assistant.domain.value_objects.knowledge_workflow import (
    KnowledgeWorkflow,
)
from qa_servicenow_assistant.domain.value_objects.selector import Selector


class KnowledgeManager(KnowledgeRepository):
    def __init__(self, repository: KnowledgeRepository, log_port: LogPort) -> None:
        self._repository = repository
        self._log_port = log_port

    def get_known_pages(self) -> Sequence[KnowledgePage]:
        pages = self._repository.get_known_pages()
        self._log_port.debug("Knowledge Base query: get_known_pages", result_count=len(pages))
        return pages

    def get_page(self, key: str) -> KnowledgePage | None:
        result = self._repository.get_page(key)
        self._log_port.debug("Knowledge Base query: get_page", key=key, found=result is not None)
        return result

    def get_element(self, key: str) -> KnowledgeElement | None:
        result = self._repository.get_element(key)
        self._log_port.debug("Knowledge Base query: get_element", key=key, found=result is not None)
        return result

    def get_selector(self, element_key: str) -> Selector | None:
        result = self._repository.get_selector(element_key)
        self._log_port.debug(
            "Knowledge Base query: get_selector", element_key=element_key, found=result is not None
        )
        return result

    def get_workflow(self, key: str) -> KnowledgeWorkflow | None:
        result = self._repository.get_workflow(key)
        self._log_port.debug("Knowledge Base query: get_workflow", key=key, found=result is not None)
        return result

    def get_fingerprint(self, page_key: str) -> str | None:
        result = self._repository.get_fingerprint(page_key)
        self._log_port.debug(
            "Knowledge Base query: get_fingerprint", page_key=page_key, found=result is not None
        )
        return result

    def validate_version(self) -> bool:
        return self._repository.validate_version()
