"""Unit tests for FrameResolver (SAD Cap. 18)."""

from __future__ import annotations

import pytest

from qa_servicenow_assistant.domain.exceptions.frame import (
    AmbiguousFrameError,
    FrameNotFoundError,
)
from qa_servicenow_assistant.domain.services.frame_resolver import FrameResolver
from qa_servicenow_assistant.domain.value_objects.frame_descriptor import (
    FrameDescriptor,
)

_MAIN = FrameDescriptor(name="", url="https://dev.service-now.com/home", is_main_frame=True)
_CONTENT = FrameDescriptor(name="content_frame", url="https://dev.service-now.com/embed", is_main_frame=False)
_OTHER = FrameDescriptor(name="other_frame", url="https://dev.service-now.com/other", is_main_frame=False)


def test_resolves_by_frame_name() -> None:
    result = FrameResolver().resolve([_MAIN, _CONTENT, _OTHER], frame_name="content_frame")

    assert result == _CONTENT


def test_raises_not_found_when_name_has_no_match() -> None:
    with pytest.raises(FrameNotFoundError, match="missing_frame"):
        FrameResolver().resolve([_MAIN, _CONTENT], frame_name="missing_frame")


def test_raises_ambiguous_when_name_matches_multiple_frames() -> None:
    duplicate = FrameDescriptor(name="content_frame", url="https://dev.service-now.com/embed2", is_main_frame=False)

    with pytest.raises(AmbiguousFrameError, match="content_frame"):
        FrameResolver().resolve([_MAIN, _CONTENT, duplicate], frame_name="content_frame")


def test_resolves_by_url_pattern() -> None:
    result = FrameResolver().resolve([_MAIN, _CONTENT, _OTHER], url_pattern="/embed")

    assert result == _CONTENT


def test_raises_not_found_when_url_pattern_has_no_match() -> None:
    with pytest.raises(FrameNotFoundError):
        FrameResolver().resolve([_MAIN, _CONTENT], url_pattern="/does-not-exist")


def test_frame_name_takes_precedence_over_url_pattern() -> None:
    result = FrameResolver().resolve(
        [_MAIN, _CONTENT, _OTHER], frame_name="other_frame", url_pattern="/embed"
    )

    assert result == _OTHER


def test_defaults_to_main_frame_when_no_criteria_given() -> None:
    result = FrameResolver().resolve([_MAIN, _CONTENT, _OTHER])

    assert result == _MAIN


def test_raises_not_found_when_no_main_frame_and_no_criteria() -> None:
    with pytest.raises(FrameNotFoundError):
        FrameResolver().resolve([_CONTENT, _OTHER])


def test_raises_not_found_for_empty_frame_list() -> None:
    with pytest.raises(FrameNotFoundError):
        FrameResolver().resolve([])
