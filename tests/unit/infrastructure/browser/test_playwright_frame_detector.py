"""Unit tests for PlaywrightFrameDetector, using fake page/frame objects."""

from __future__ import annotations

import pytest

from qa_servicenow_assistant.domain.exceptions.frame import FrameNotFoundError
from qa_servicenow_assistant.domain.value_objects.frame_descriptor import (
    FrameDescriptor,
)
from qa_servicenow_assistant.infrastructure.browser.playwright_frame_detector import (
    PlaywrightFrameDetector,
)


class FakeFrame:
    def __init__(self, name: str, url: str) -> None:
        self.name = name
        self.url = url


class FakePage:
    def __init__(self, frames: list[FakeFrame], main_frame: FakeFrame) -> None:
        self.frames = frames
        self.main_frame = main_frame


@pytest.fixture
def detector() -> PlaywrightFrameDetector:
    return PlaywrightFrameDetector()


def test_list_frames_marks_main_frame_correctly(detector: PlaywrightFrameDetector) -> None:
    main = FakeFrame(name="", url="https://dev.service-now.com/home")
    content = FakeFrame(name="content_frame", url="https://dev.service-now.com/embed")
    page = FakePage(frames=[main, content], main_frame=main)

    descriptors = detector.list_frames(page)

    assert descriptors == (
        FrameDescriptor(name="", url="https://dev.service-now.com/home", is_main_frame=True),
        FrameDescriptor(name="content_frame", url="https://dev.service-now.com/embed", is_main_frame=False),
    )


def test_select_frame_returns_matching_live_handle(detector: PlaywrightFrameDetector) -> None:
    main = FakeFrame(name="", url="https://dev.service-now.com/home")
    content = FakeFrame(name="content_frame", url="https://dev.service-now.com/embed")
    page = FakePage(frames=[main, content], main_frame=main)
    descriptor = FrameDescriptor(name="content_frame", url="https://dev.service-now.com/embed", is_main_frame=False)

    selected = detector.select_frame(page, descriptor)

    assert selected is content


def test_select_frame_raises_when_frame_no_longer_present(detector: PlaywrightFrameDetector) -> None:
    main = FakeFrame(name="", url="https://dev.service-now.com/home")
    page = FakePage(frames=[main], main_frame=main)
    descriptor = FrameDescriptor(name="content_frame", url="https://dev.service-now.com/embed", is_main_frame=False)

    with pytest.raises(FrameNotFoundError):
        detector.select_frame(page, descriptor)
