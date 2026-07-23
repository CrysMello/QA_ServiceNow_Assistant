"""Unit tests for KnowledgeBaseIndex (SAD 11.4 passo 5, 11.5, 11.6)."""

from __future__ import annotations

from qa_servicenow_assistant.domain.entities.knowledge_element import KnowledgeElement
from qa_servicenow_assistant.domain.entities.knowledge_page import KnowledgePage
from qa_servicenow_assistant.domain.services.knowledge_base_index import (
    KnowledgeBaseIndex,
)
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


def make_index() -> KnowledgeBaseIndex:
    page = KnowledgePage(key="incident_form", url_pattern="/incident.do", fingerprint="fp-1")
    element = KnowledgeElement(key="submit_button", page_key="incident_form", description="Submit")
    selector = KnowledgeSelector(
        element_key="submit_button", selector=Selector(strategy="id", value="#submit", priority=3)
    )
    workflow = KnowledgeWorkflow(key="create_incident", description="Create an incident")
    artifacts = KnowledgeBaseArtifacts(
        manifest=KnowledgeManifest(version="1.0"),
        pages=(page,),
        elements=(element,),
        selectors=(selector,),
        workflows=(workflow,),
    )
    return KnowledgeBaseIndex(artifacts)


def test_all_pages_returns_every_page() -> None:
    index = make_index()

    assert [page.key for page in index.all_pages()] == ["incident_form"]


def test_get_page_found_and_not_found() -> None:
    index = make_index()

    assert index.get_page("incident_form") is not None
    assert index.get_page("unknown") is None


def test_get_element_found_and_not_found() -> None:
    index = make_index()

    element = index.get_element("submit_button")
    assert element is not None
    assert element.page_key == "incident_form"
    assert index.get_element("unknown") is None


def test_get_selector_found_and_not_found() -> None:
    index = make_index()

    selector = index.get_selector("submit_button")
    assert selector is not None
    assert selector.value == "#submit"
    assert index.get_selector("unknown") is None


def test_get_workflow_found_and_not_found() -> None:
    index = make_index()

    assert index.get_workflow("create_incident") is not None
    assert index.get_workflow("unknown") is None


def test_get_fingerprint_returns_the_page_fingerprint() -> None:
    index = make_index()

    assert index.get_fingerprint("incident_form") == "fp-1"
    assert index.get_fingerprint("unknown") is None


def test_empty_artifacts_produce_empty_lookups() -> None:
    index = KnowledgeBaseIndex(KnowledgeBaseArtifacts(manifest=KnowledgeManifest(version="1.0")))

    assert index.all_pages() == ()
    assert index.get_page("x") is None
    assert index.get_element("x") is None
    assert index.get_selector("x") is None
    assert index.get_workflow("x") is None
    assert index.get_fingerprint("x") is None
