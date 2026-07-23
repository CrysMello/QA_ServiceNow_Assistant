"""Playwright-based implementation of FrameDetectorPort (SAD 18.3)."""

from __future__ import annotations

from typing import Any

from qa_servicenow_assistant.application.ports.frame_detector_port import (
    FrameDetectorPort,
)
from qa_servicenow_assistant.domain.exceptions.frame import FrameNotFoundError
from qa_servicenow_assistant.domain.value_objects.frame_descriptor import (
    FrameDescriptor,
)


class PlaywrightFrameDetector(FrameDetectorPort):
    """Detects frames via page.frames and page.main_frame."""

    def list_frames(self, page: Any) -> tuple[FrameDescriptor, ...]:
        main_frame = page.main_frame
        return tuple(
            FrameDescriptor(name=frame.name, url=frame.url, is_main_frame=frame is main_frame)
            for frame in page.frames
        )

    def select_frame(self, page: Any, descriptor: FrameDescriptor) -> Any:
        main_frame = page.main_frame
        for frame in page.frames:
            is_main = frame is main_frame
            if frame.name == descriptor.name and frame.url == descriptor.url and is_main == descriptor.is_main_frame:
                return frame
        raise FrameNotFoundError(
            f"Frame matching descriptor (name={descriptor.name!r}, url={descriptor.url!r}) "
            "is no longer available"
        )
