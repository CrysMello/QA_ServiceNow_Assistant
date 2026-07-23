"""Unit tests for FrameDescriptor."""

from __future__ import annotations

from qa_servicenow_assistant.domain.value_objects.frame_descriptor import (
    FrameDescriptor,
)


def test_holds_name_url_and_is_main_frame() -> None:
    descriptor = FrameDescriptor(name="content_frame", url="https://dev.service-now.com/frame", is_main_frame=False)

    assert descriptor.name == "content_frame"
    assert descriptor.url == "https://dev.service-now.com/frame"
    assert descriptor.is_main_frame is False


def test_equal_by_value() -> None:
    first = FrameDescriptor(name="a", url="https://x", is_main_frame=True)
    second = FrameDescriptor(name="a", url="https://x", is_main_frame=True)

    assert first == second
