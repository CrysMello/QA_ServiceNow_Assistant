"""Unit tests for PageRecognizer (SAD 15.4/15.5)."""

from __future__ import annotations

from qa_servicenow_assistant.domain.entities.knowledge_page import KnowledgePage
from qa_servicenow_assistant.domain.services.page_fingerprint import (
    compute_fingerprint,
)
from qa_servicenow_assistant.domain.services.page_recognizer import PageRecognizer
from qa_servicenow_assistant.domain.value_objects.browser_snapshot import (
    BrowserSnapshot,
    CollectedElement,
)
from qa_servicenow_assistant.domain.value_objects.recognition_confidence import (
    RecognitionConfidence,
)

_SUBMIT_BUTTON = CollectedElement(
    tag_name="button", text="Submit", visible=True, attributes={"id": "submit-btn"}
)


def _snapshot(url: str, title: str, elements: tuple[CollectedElement, ...] = ()) -> BrowserSnapshot:
    return BrowserSnapshot(url=url, title=title, html="<html></html>", elements=elements)


def test_exact_match_when_all_applicable_criteria_agree() -> None:
    snapshot = _snapshot(
        url="https://dev.service-now.com/test_plan_list",
        title="Test Plans",
        elements=(_SUBMIT_BUTTON,),
    )
    page = KnowledgePage(
        key="test_plan_list",
        url_pattern="/test_plan_list",
        title="Test Plans",
        fingerprint=compute_fingerprint(snapshot),
        required_element_keys=("submit-btn",),
    )

    result = PageRecognizer().recognize(snapshot, [page])

    assert result.confidence == RecognitionConfidence.EXACT
    assert result.matched_page == page
    assert set(result.matched_criteria) == {"url", "title", "fingerprint", "required_elements"}


def test_partial_match_when_only_some_criteria_agree() -> None:
    snapshot = _snapshot(url="https://dev.service-now.com/test_plan_list", title="Wrong Title")
    page = KnowledgePage(key="test_plan_list", url_pattern="/test_plan_list", title="Test Plans")

    result = PageRecognizer().recognize(snapshot, [page])

    assert result.confidence == RecognitionConfidence.PARTIAL
    assert result.matched_page == page
    assert result.matched_criteria == ("url",)


def test_low_confidence_is_not_recognized() -> None:
    snapshot = _snapshot(url="https://dev.service-now.com/test_plan_list", title="Wrong Title")
    page = KnowledgePage(
        key="test_plan_list",
        url_pattern="/test_plan_list",
        title="Test Plans",
        required_element_keys=("missing-element",),
    )
    # applicable=3 (url, title, required_elements), matched=1 (url) -> ratio 0.33 -> LOW

    result = PageRecognizer().recognize(snapshot, [page])

    assert result.confidence == RecognitionConfidence.LOW
    assert result.matched_page is None  # LOW is "considerada nao reconhecida"


def test_unknown_when_no_known_pages() -> None:
    snapshot = _snapshot(url="https://dev.service-now.com/anything", title="Anything")

    result = PageRecognizer().recognize(snapshot, [])

    assert result.confidence == RecognitionConfidence.UNKNOWN
    assert result.matched_page is None


def test_unknown_when_url_does_not_match_any_page() -> None:
    snapshot = _snapshot(url="https://dev.service-now.com/unrelated_page", title="Unrelated")
    page = KnowledgePage(key="test_plan_list", url_pattern="/test_plan_list", title="Test Plans")

    result = PageRecognizer().recognize(snapshot, [page])

    assert result.confidence == RecognitionConfidence.UNKNOWN
    assert result.matched_page is None


def test_selects_best_scoring_candidate_among_several() -> None:
    snapshot = _snapshot(url="https://dev.service-now.com/test_plan_list", title="Test Plans")
    weak_candidate = KnowledgePage(key="weak", url_pattern="/test_plan_list")
    strong_candidate = KnowledgePage(key="strong", url_pattern="/test_plan_list", title="Test Plans")

    result = PageRecognizer().recognize(snapshot, [weak_candidate, strong_candidate])

    assert result.matched_page == strong_candidate


def test_fingerprint_mismatch_alone_does_not_prevent_recognition() -> None:
    snapshot = _snapshot(url="https://dev.service-now.com/test_plan_list", title="Test Plans")
    page = KnowledgePage(
        key="test_plan_list",
        url_pattern="/test_plan_list",
        title="Test Plans",
        fingerprint="some-fingerprint-that-will-never-match",
    )
    # applicable=3 (url, title, fingerprint), matched=2 (url, title) -> ratio 0.66 -> PARTIAL

    result = PageRecognizer().recognize(snapshot, [page])

    assert result.confidence == RecognitionConfidence.PARTIAL
    assert result.matched_page == page
    assert "fingerprint" not in result.matched_criteria


def test_page_with_only_url_pattern_can_reach_exact() -> None:
    snapshot = _snapshot(url="https://dev.service-now.com/home", title="Anything")
    page = KnowledgePage(key="home", url_pattern="/home")

    result = PageRecognizer().recognize(snapshot, [page])

    assert result.confidence == RecognitionConfidence.EXACT
    assert result.matched_page == page
