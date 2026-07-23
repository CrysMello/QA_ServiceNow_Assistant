"""Port for detecting and selecting browser frames (SAD 18.3 - Frame
Detector, "depende de Playwright").

The page/frame parameters and select_frame() return type are Any, per the
same rationale as BrowserManagerPort.new_page(): the abstract contract
must not leak a Playwright-specific type (SAD 9.7). The returned frame
handle exposes the same url/title/content/evaluate surface as a Page
(confirmed against real Playwright), so it can be passed directly to
BrowserDataCollectorPort.collect() or NavigationExecutorPort.navigate().
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from qa_servicenow_assistant.domain.value_objects.frame_descriptor import (
    FrameDescriptor,
)


class FrameDetectorPort(ABC):
    """Contract implemented by infrastructure adapters that detect and
    select frames on a live page."""

    @abstractmethod
    def list_frames(self, page: Any) -> tuple[FrameDescriptor, ...]:
        """Return descriptors for every frame currently present on page,
        including the main frame and any nested iframes."""
        raise NotImplementedError

    @abstractmethod
    def select_frame(self, page: Any, descriptor: FrameDescriptor) -> Any:
        """Return the opaque frame handle matching descriptor.

        Raises FrameNotFoundError if the described frame is no longer
        present (SAD 18.6 - "frame removido dinamicamente").
        """
        raise NotImplementedError
