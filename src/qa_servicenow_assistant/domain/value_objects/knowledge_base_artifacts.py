"""KnowledgeBaseArtifacts: the full set of parsed Knowledge Base files
(SAD 11.3 - Artefatos Gerenciados), as produced by an infrastructure
loader and consumed by KnowledgeBaseIndex. Purely a data bundle - no
behavior."""

from __future__ import annotations

from dataclasses import dataclass

from qa_servicenow_assistant.domain.entities.knowledge_element import KnowledgeElement
from qa_servicenow_assistant.domain.entities.knowledge_page import KnowledgePage
from qa_servicenow_assistant.domain.value_objects.knowledge_manifest import (
    KnowledgeManifest,
)
from qa_servicenow_assistant.domain.value_objects.knowledge_selector import (
    KnowledgeSelector,
)
from qa_servicenow_assistant.domain.value_objects.knowledge_workflow import (
    KnowledgeWorkflow,
)


@dataclass(frozen=True)
class KnowledgeBaseArtifacts:
    manifest: KnowledgeManifest
    pages: tuple[KnowledgePage, ...] = ()
    elements: tuple[KnowledgeElement, ...] = ()
    selectors: tuple[KnowledgeSelector, ...] = ()
    workflows: tuple[KnowledgeWorkflow, ...] = ()
