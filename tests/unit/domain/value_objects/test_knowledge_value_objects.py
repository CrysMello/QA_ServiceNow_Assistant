"""Unit tests for the new Knowledge Manager value objects/entities (SAD Cap. 11)."""

from __future__ import annotations

import pytest

from qa_servicenow_assistant.domain.entities.knowledge_element import KnowledgeElement
from qa_servicenow_assistant.domain.value_objects.knowledge_base_artifacts import (
    KnowledgeBaseArtifacts,
)
from qa_servicenow_assistant.domain.value_objects.knowledge_manifest import (
    KnowledgeManifest,
)
from qa_servicenow_assistant.domain.value_objects.knowledge_selector import (
    KnowledgeSelector,
)
from qa_servicenow_assistant.domain.value_objects.knowledge_workflow import (
    KnowledgeWorkflow,
)
from qa_servicenow_assistant.domain.value_objects.selector import Selector


def test_knowledge_manifest_defaults() -> None:
    manifest = KnowledgeManifest(version="1.0")

    assert manifest.generated_at is None
    assert manifest.metadata == {}


def test_knowledge_manifest_is_frozen() -> None:
    manifest = KnowledgeManifest(version="1.0")

    with pytest.raises(AttributeError):
        manifest.version = "2.0"  # type: ignore[misc]


def test_knowledge_element_defaults() -> None:
    element = KnowledgeElement(key="submit_button", page_key="incident_form", description="Submit")

    assert element.attributes == {}


def test_knowledge_workflow_defaults() -> None:
    workflow = KnowledgeWorkflow(key="create_incident", description="Creates an incident")

    assert workflow.step_keys == ()


def test_knowledge_selector_wraps_selector() -> None:
    selector = Selector(strategy="id", value="#submit", priority=3)
    wrapper = KnowledgeSelector(element_key="submit_button", selector=selector)

    assert wrapper.element_key == "submit_button"
    assert wrapper.selector is selector


def test_knowledge_base_artifacts_defaults_to_empty_collections() -> None:
    artifacts = KnowledgeBaseArtifacts(manifest=KnowledgeManifest(version="1.0"))

    assert artifacts.pages == ()
    assert artifacts.elements == ()
    assert artifacts.selectors == ()
    assert artifacts.workflows == ()
