"""Port for accessing the Knowledge Base (SAD 8.5 - KnowledgeRepository).

Scope note: this port is intentionally minimal - only get_known_pages(),
which is all Page Recognition needs. Knowledge Manager (a much later
module, Prompt 18) owns the real Knowledge Base schema (manifest, pages,
elements, selectors, workflows, fingerprints - SAD 11.3/11.5) and will
extend this ABC with further methods (get_element, get_selector,
get_workflow, validate_version, etc.), the same way LogPort was extended
between the Configuration Manager and Log Engine prompts (ADR-0013). No
concrete adapter is implemented here; until Knowledge Manager exists,
callers must inject a test double or an interim adapter.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from qa_servicenow_assistant.domain.entities.knowledge_page import KnowledgePage


class KnowledgeRepository(ABC):
    """Contract for read-only access to the Knowledge Base."""

    @abstractmethod
    def get_known_pages(self) -> Sequence[KnowledgePage]:
        """Return all known page entries available for recognition matching."""
        raise NotImplementedError
