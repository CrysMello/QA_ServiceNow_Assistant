"""Unit tests for PlaywrightFrameDetector, using fake page/frame objects.

wait_for_frame's "a frame actually appears after the wait starts" and
"times out for real" behaviors are covered end-to-end against real
Playwright in the integration suite; here we cover the Python-side
wiring and exception translation using fakes that mimic the exact
Playwright surface used (page.frames, page.main_frame, page.expect_event).
"""

from __future__ import annotations

from typing import Any

import pytest
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from qa_servicenow_assistant.domain.exceptions.frame import (
    FrameAccessError,
    FrameDetectionError,
    FrameNotFoundError,
    FrameTimeoutError,
)
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


class RaisingFrame:
    """A frame whose property access raises, to test translation."""

    @property
    def name(self) -> str:
        raise PlaywrightError("boom - name access failed")

    @property
    def url(self) -> str:
        raise PlaywrightError("boom - url access failed")


class FakeExpectEventContext:
    def __init__(self, error_to_raise: Exception | None = None) -> None:
        self._error_to_raise = error_to_raise

    def __enter__(self) -> "FakeExpectEventContext":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        if self._error_to_raise is not None:
            raise self._error_to_raise
        return False


class FakePage:
    """frame_sequence models successive `.frames` reads: each element is
    the snapshot returned by the Nth access (the last element repeats for
    any further access), letting tests simulate a frame that "appears"
    between the pre-check and the post-wait re-query."""

    def __init__(
        self,
        frame_sequence: list[list[Any]],
        main_frame: Any,
        expect_event_error: Exception | None = None,
    ) -> None:
        self._frame_sequence = frame_sequence
        self._call_index = 0
        self.main_frame = main_frame
        self._expect_event_error = expect_event_error
        self.expect_event_calls: list[tuple[str, int]] = []

    @property
    def frames(self) -> list[Any]:
        index = min(self._call_index, len(self._frame_sequence) - 1)
        self._call_index += 1
        return self._frame_sequence[index]

    def expect_event(self, event: str, predicate: Any = None, timeout: int | None = None) -> FakeExpectEventContext:
        self.expect_event_calls.append((event, timeout))
        return FakeExpectEventContext(self._expect_event_error)


class RaisingPage:
    """A page whose .frames/.main_frame access raises."""

    @property
    def main_frame(self) -> Any:
        raise PlaywrightError("boom - main_frame access failed")

    @property
    def frames(self) -> list[Any]:
        raise PlaywrightError("boom - frames access failed")


@pytest.fixture
def detector() -> PlaywrightFrameDetector:
    return PlaywrightFrameDetector()


# --- list_frames -----------------------------------------------------

def test_list_frames_marks_main_frame_correctly(detector: PlaywrightFrameDetector) -> None:
    main = FakeFrame(name="", url="https://dev.service-now.com/home")
    content = FakeFrame(name="content_frame", url="https://dev.service-now.com/embed")
    page = FakePage(frame_sequence=[[main, content]], main_frame=main)

    descriptors = detector.list_frames(page)

    assert descriptors == (
        FrameDescriptor(name="", url="https://dev.service-now.com/home", is_main_frame=True),
        FrameDescriptor(name="content_frame", url="https://dev.service-now.com/embed", is_main_frame=False),
    )


def test_list_frames_translates_playwright_error_and_chains_it(detector: PlaywrightFrameDetector) -> None:
    with pytest.raises(FrameDetectionError) as exc_info:
        detector.list_frames(RaisingPage())

    assert isinstance(exc_info.value.__cause__, PlaywrightError)


# --- select_frame ------------------------------------------------------

def test_select_frame_returns_matching_live_handle(detector: PlaywrightFrameDetector) -> None:
    main = FakeFrame(name="", url="https://dev.service-now.com/home")
    content = FakeFrame(name="content_frame", url="https://dev.service-now.com/embed")
    page = FakePage(frame_sequence=[[main, content]], main_frame=main)
    descriptor = FrameDescriptor(name="content_frame", url="https://dev.service-now.com/embed", is_main_frame=False)

    selected = detector.select_frame(page, descriptor)

    assert selected is content


def test_select_frame_raises_not_found_when_frame_no_longer_present(detector: PlaywrightFrameDetector) -> None:
    main = FakeFrame(name="", url="https://dev.service-now.com/home")
    page = FakePage(frame_sequence=[[main]], main_frame=main)
    descriptor = FrameDescriptor(name="content_frame", url="https://dev.service-now.com/embed", is_main_frame=False)

    with pytest.raises(FrameNotFoundError):
        detector.select_frame(page, descriptor)


def test_select_frame_translates_playwright_error_and_chains_it(detector: PlaywrightFrameDetector) -> None:
    main = FakeFrame(name="", url="https://dev.service-now.com/home")
    page = FakePage(frame_sequence=[[main, RaisingFrame()]], main_frame=main)
    descriptor = FrameDescriptor(name="content_frame", url="https://dev.service-now.com/embed", is_main_frame=False)

    with pytest.raises(FrameAccessError) as exc_info:
        detector.select_frame(page, descriptor)

    assert isinstance(exc_info.value.__cause__, PlaywrightError)


# --- wait_for_frame ------------------------------------------------------

def test_wait_for_frame_without_criteria_returns_immediately(detector: PlaywrightFrameDetector) -> None:
    main = FakeFrame(name="", url="https://dev.service-now.com/home")
    page = FakePage(frame_sequence=[[main]], main_frame=main)

    result = detector.wait_for_frame(page, timeout_ms=1_000)

    assert result == (FrameDescriptor(name="", url="https://dev.service-now.com/home", is_main_frame=True),)
    assert page.expect_event_calls == []  # no wait needed


def test_wait_for_frame_returns_immediately_when_already_present(detector: PlaywrightFrameDetector) -> None:
    main = FakeFrame(name="", url="https://dev.service-now.com/home")
    content = FakeFrame(name="content_frame", url="https://dev.service-now.com/embed")
    page = FakePage(frame_sequence=[[main, content]], main_frame=main)

    result = detector.wait_for_frame(page, frame_name="content_frame", timeout_ms=1_000)

    assert any(descriptor.name == "content_frame" for descriptor in result)
    assert page.expect_event_calls == []  # already present, no wait needed


def test_wait_for_frame_waits_then_finds_frame_via_event(detector: PlaywrightFrameDetector) -> None:
    main = FakeFrame(name="", url="https://dev.service-now.com/home")
    content = FakeFrame(name="content_frame", url="https://dev.service-now.com/embed")
    page = FakePage(frame_sequence=[[main], [main, content]], main_frame=main)

    result = detector.wait_for_frame(page, frame_name="content_frame", timeout_ms=1_000)

    assert page.expect_event_calls == [("framenavigated", 1_000)]
    assert any(descriptor.name == "content_frame" for descriptor in result)


def test_wait_for_frame_by_url_pattern(detector: PlaywrightFrameDetector) -> None:
    main = FakeFrame(name="", url="https://dev.service-now.com/home")
    content = FakeFrame(name="content_frame", url="https://dev.service-now.com/embed")
    page = FakePage(frame_sequence=[[main], [main, content]], main_frame=main)

    result = detector.wait_for_frame(page, url_pattern="/embed", timeout_ms=1_000)

    assert any("/embed" in descriptor.url for descriptor in result)


def test_wait_for_frame_raises_timeout_error_when_criterion_never_matches(
    detector: PlaywrightFrameDetector,
) -> None:
    main = FakeFrame(name="", url="https://dev.service-now.com/home")
    page = FakePage(
        frame_sequence=[[main]],
        main_frame=main,
        expect_event_error=PlaywrightTimeoutError("Timeout 1000ms exceeded"),
    )

    with pytest.raises(FrameTimeoutError, match="1000ms") as exc_info:
        detector.wait_for_frame(page, frame_name="never_appears", timeout_ms=1_000)

    assert isinstance(exc_info.value.__cause__, PlaywrightTimeoutError)


def test_wait_for_frame_never_falls_back_to_main_frame_on_timeout(
    detector: PlaywrightFrameDetector,
) -> None:
    main = FakeFrame(name="", url="https://dev.service-now.com/home")
    page = FakePage(
        frame_sequence=[[main]],
        main_frame=main,
        expect_event_error=PlaywrightTimeoutError("Timeout exceeded"),
    )

    with pytest.raises(FrameTimeoutError):
        detector.wait_for_frame(page, frame_name="never_appears", timeout_ms=1_000)
    # if it had fallen back silently, this would have returned a result
    # instead of raising - the assertion above is the actual proof.


def test_wait_for_frame_translates_non_timeout_playwright_error_during_wait(
    detector: PlaywrightFrameDetector,
) -> None:
    main = FakeFrame(name="", url="https://dev.service-now.com/home")
    page = FakePage(
        frame_sequence=[[main]],
        main_frame=main,
        expect_event_error=PlaywrightError("target closed"),
    )

    with pytest.raises(FrameDetectionError) as exc_info:
        detector.wait_for_frame(page, frame_name="content_frame", timeout_ms=1_000)

    assert isinstance(exc_info.value.__cause__, PlaywrightError)
    assert not isinstance(exc_info.value.__cause__, PlaywrightTimeoutError)
