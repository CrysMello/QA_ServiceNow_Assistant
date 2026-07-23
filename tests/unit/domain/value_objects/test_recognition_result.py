"""Unit tests for RecognitionResult / RecognitionConfidence."""

from __future__ import annotations

import pytest

from qa_servicenow_assistant.domain.entities.knowledge_page import KnowledgePage
from qa_servicenow_assistant.domain.value_objects.recognition_confidence import (
    RecognitionConfidence,
)
from qa_servicenow_assistant.domain.value_objects.recognition_result import (
    RecognitionResult,
)


@pytest.mark.parametrize(
    "confidence,expected",
    [
        (RecognitionConfidence.EXACT, True),
        (RecognitionConfidence.PARTIAL, True),
        (RecognitionConfidence.LOW, False),
        (RecognitionConfidence.UNKNOWN, False),
    ],
)
def test_is_recognized_matches_sad_15_5(confidence: RecognitionConfidence, expected: bool) -> None:
    result = RecognitionResult(observed_url="https://dev.service-now.com", confidence=confidence)

    assert result.is_recognized is expected


def test_defaults_have_no_matched_page() -> None:
    result = RecognitionResult(
        observed_url="https://dev.service-now.com", confidence=RecognitionConfidence.UNKNOWN
    )

    assert result.matched_page is None
    assert result.matched_criteria == ()


def test_holds_matched_page() -> None:
    page = KnowledgePage(key="home", url_pattern="/home")

    result = RecognitionResult(
        observed_url="https://dev.service-now.com/home",
        confidence=RecognitionConfidence.EXACT,
        matched_page=page,
        matched_criteria=("url",),
    )

    assert result.matched_page is page
