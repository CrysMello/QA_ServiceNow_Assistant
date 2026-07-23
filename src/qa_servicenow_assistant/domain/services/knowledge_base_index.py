"""KnowledgeBaseIndex: pure domain service building O(1)-lookup indexes
over loaded Knowledge Base artifacts (SAD 11.4 passo 5 - "Construir
indices internos para pesquisa"; SAD 11.6 - Estrategia de Cache:
"consultas subsequentes utilizam os indices internos, eliminando novas
leituras em disco").

No I/O here (SAD 8.7); built once from an already-loaded
KnowledgeBaseArtifacts instance. Implements the read side of SAD 11.5's
"Interfaces Disponibilizadas" (get_page/get_element/get_selector/
get_workflow/get_fingerprint) plus all_pages() for get_known_pages()
compatibility with the pre-existing KnowledgeRepository.get_known_pages().
"""

from __future__ import annotations

from qa_servicenow_assistant.domain.entities.knowledge_element import KnowledgeElement
from qa_servicenow_assistant.domain.entities.knowledge_page import KnowledgePage
from qa_servicenow_assistant.domain.value_objects.knowledge_base_artifacts import (
    KnowledgeBaseArtifacts,
)
from qa_servicenow_assistant.domain.value_objects.knowledge_workflow import (
    KnowledgeWorkflow,
)
from qa_servicenow_assistant.domain.value_objects.selector import Selector


class KnowledgeBaseIndex:
    def __init__(self, artifacts: KnowledgeBaseArtifacts) -> None:
        self._pages = tuple(artifacts.pages)
        self._pages_by_key = {page.key: page for page in artifacts.pages}
        self._elements_by_key = {element.key: element for element in artifacts.elements}
        self._selectors_by_element_key = {
            entry.element_key: entry.selector for entry in artifacts.selectors
        }
        self._workflows_by_key = {workflow.key: workflow for workflow in artifacts.workflows}

    def all_pages(self) -> tuple[KnowledgePage, ...]:
        return self._pages

    def get_page(self, key: str) -> KnowledgePage | None:
        return self._pages_by_key.get(key)

    def get_element(self, key: str) -> KnowledgeElement | None:
        return self._elements_by_key.get(key)

    def get_selector(self, element_key: str) -> Selector | None:
        return self._selectors_by_element_key.get(element_key)

    def get_workflow(self, key: str) -> KnowledgeWorkflow | None:
        return self._workflows_by_key.get(key)

    def get_fingerprint(self, page_key: str) -> str | None:
        page = self._pages_by_key.get(page_key)
        return page.fingerprint if page is not None else None
