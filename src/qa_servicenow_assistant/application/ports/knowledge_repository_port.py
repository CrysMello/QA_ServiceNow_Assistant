"""Port for accessing the Knowledge Base (SAD 8.5 - KnowledgeRepository;
SAD 11.5 - Interfaces Disponibilizadas).

Extended by Knowledge Manager (Prompt 18) with the operations SAD 11.5
lists beyond get_known_pages() (which Page Recognition already depended
on since Prompt 8) - the same incremental-extension precedent used for
LogPort between the Configuration Manager and Log Engine prompts
(ADR-0013). Implementers written before this extension (test fakes in
Page Recognition/Frame Resolver integration tests) must now provide the
new methods too; trivial "nothing to return" stand-ins are sufficient
where a test never exercises them, exactly like FakeLogPort adopting
trace/critical/bind at the time LogPort grew those methods.

Single-item lookups return None when the key is unknown - a controlled,
non-crashing outcome (SAD 11.7 - "Elemento nao encontrado -> Retornar
erro controlado ao consumidor"), not an exception. See
domain/exceptions/knowledge_base.py for the exceptions this port's real
implementations DO raise (loading/initialization failures only).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from qa_servicenow_assistant.domain.entities.knowledge_element import KnowledgeElement
from qa_servicenow_assistant.domain.entities.knowledge_page import KnowledgePage
from qa_servicenow_assistant.domain.value_objects.knowledge_workflow import (
    KnowledgeWorkflow,
)
from qa_servicenow_assistant.domain.value_objects.selector import Selector


class KnowledgeRepository(ABC):
    """Contract for read-only access to the Knowledge Base (SAD 11.8 -
    "Os arquivos sao tratados como somente leitura")."""

    @abstractmethod
    def get_known_pages(self) -> Sequence[KnowledgePage]:
        """Return all known page entries available for recognition matching."""
        raise NotImplementedError

    @abstractmethod
    def get_page(self, key: str) -> KnowledgePage | None:
        """Recupera uma pagina pelo identificador (SAD 11.5 - get_page())."""
        raise NotImplementedError

    @abstractmethod
    def get_element(self, key: str) -> KnowledgeElement | None:
        """Obtem um elemento da interface (SAD 11.5 - get_element())."""
        raise NotImplementedError

    @abstractmethod
    def get_selector(self, element_key: str) -> Selector | None:
        """Retorna o locator recomendado (SAD 11.5 - get_selector())."""
        raise NotImplementedError

    @abstractmethod
    def get_workflow(self, key: str) -> KnowledgeWorkflow | None:
        """Recupera um workflow conhecido (SAD 11.5 - get_workflow())."""
        raise NotImplementedError

    @abstractmethod
    def get_fingerprint(self, page_key: str) -> str | None:
        """Obtem a assinatura de uma pagina (SAD 11.5 - get_fingerprint())."""
        raise NotImplementedError

    @abstractmethod
    def validate_version(self) -> bool:
        """Verifica compatibilidade da base (SAD 11.5 - validate_version())."""
        raise NotImplementedError
