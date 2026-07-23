"""Playwright-based implementation of FrameDetectorPort (SAD 18.3).

Exception translation: every Playwright-native failure is caught and
re-raised as a FrameError subclass, chaining the original via
`raise ... from error` (never a bare re-raise of playwright.sync_api.Error).

Condition-based waiting (RNF-010): wait_for_frame() never uses
time.sleep() or page.wait_for_timeout() as its mechanism. It relies on
Playwright's own event system (page.expect_event("framenavigated", ...)),
confirmed empirically (see correction notes) to be the point at which a
newly attached frame's name/url properties are actually populated -
"frameattached" fires too early, while both are still empty strings.
"""

from __future__ import annotations

from typing import Any

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from qa_servicenow_assistant.application.ports.frame_detector_port import (
    FrameDetectorPort,
)
from qa_servicenow_assistant.domain.exceptions.frame import (
    FrameAccessError,
    FrameDetectionError,
    FrameNotFoundError,
    FrameTimeoutError,
)
from qa_servicenow_assistant.domain.value_objects.frame_descriptor import (
    FrameDescriptor,
)


class PlaywrightFrameDetector(FrameDetectorPort):
    """Detects frames via page.frames/page.main_frame and waits for new
    ones via the "framenavigated" event."""

    def list_frames(self, page: Any) -> tuple[FrameDescriptor, ...]:
        try:
            main_frame = page.main_frame
            return tuple(
                FrameDescriptor(name=frame.name, url=frame.url, is_main_frame=frame is main_frame)
                for frame in page.frames
            )
        except PlaywrightError as error:
            raise FrameDetectionError(f"Failed to list frames: {error}") from error

    def wait_for_frame(
        self,
        page: Any,
        *,
        frame_name: str | None = None,
        url_pattern: str | None = None,
        timeout_ms: int,
    ) -> tuple[FrameDescriptor, ...]:
        if frame_name is None and url_pattern is None:
            return self.list_frames(page)

        current = self.list_frames(page)
        if any(self._descriptor_matches(descriptor, frame_name, url_pattern) for descriptor in current):
            return current

        try:
            with page.expect_event(
                "framenavigated",
                predicate=lambda frame: self._live_frame_matches(frame, frame_name, url_pattern),
                timeout=timeout_ms,
            ):
                pass
        except PlaywrightTimeoutError as error:
            raise FrameTimeoutError(
                f"Timed out after {timeout_ms}ms waiting for frame "
                f"(name={frame_name!r}, url_pattern={url_pattern!r})"
            ) from error
        except PlaywrightError as error:
            raise FrameDetectionError(
                f"Failed while waiting for frame (name={frame_name!r}, url_pattern={url_pattern!r}): {error}"
            ) from error

        return self.list_frames(page)

    def select_frame(self, page: Any, descriptor: FrameDescriptor) -> Any:
        try:
            main_frame = page.main_frame
            for frame in page.frames:
                is_main = frame is main_frame
                if frame.name == descriptor.name and frame.url == descriptor.url and is_main == descriptor.is_main_frame:
                    return frame
        except PlaywrightError as error:
            raise FrameAccessError(
                "Failed to access frame while selecting descriptor "
                f"(name={descriptor.name!r}, url={descriptor.url!r}): {error}"
            ) from error

        raise FrameNotFoundError(
            f"Frame matching descriptor (name={descriptor.name!r}, url={descriptor.url!r}) "
            "is no longer available"
        )

    def _descriptor_matches(
        self, descriptor: FrameDescriptor, frame_name: str | None, url_pattern: str | None
    ) -> bool:
        if frame_name is not None:
            return descriptor.name == frame_name
        return url_pattern in descriptor.url  # type: ignore[operator]

    def _live_frame_matches(self, frame: Any, frame_name: str | None, url_pattern: str | None) -> bool:
        if frame_name is not None:
            return frame.name == frame_name
        return url_pattern in frame.url  # type: ignore[operator]
