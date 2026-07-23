"""Port for detecting and selecting browser frames (SAD 18.3 - Frame
Detector, "depende de Playwright").

The page/frame parameters and select_frame() return type are Any, per the
same rationale as BrowserManagerPort.new_page(): the abstract contract
must not leak a Playwright-specific type (SAD 9.7). The returned frame
handle exposes the same url/title/content/evaluate surface as a Page
(confirmed against real Playwright), so it can be passed directly to
BrowserDataCollectorPort.collect() or NavigationExecutorPort.navigate().

Every method here must translate Playwright-native failures into the
FrameError hierarchy (domain/exceptions/frame.py) before they leave the
adapter - concrete adapters must never let a raw playwright.sync_api.Error
escape (correction applied after architectural review).
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
        including the main frame and any nested iframes.

        Raises FrameDetectionError if the underlying browser
        communication fails.
        """
        raise NotImplementedError

    @abstractmethod
    def wait_for_frame(
        self,
        page: Any,
        *,
        frame_name: str | None = None,
        url_pattern: str | None = None,
        timeout_ms: int,
    ) -> tuple[FrameDescriptor, ...]:
        """Condition-based wait (RNF-010): block until at least one frame
        matching frame_name/url_pattern is present on page, then return
        the full current frame list (ambiguity among matches is decided
        by the caller, e.g. FrameResolver). If neither frame_name nor
        url_pattern is given, returns immediately without waiting (the
        main-frame fallback needs no wait).

        Must never use a fixed sleep as its primary mechanism, must never
        wait indefinitely, and must never fall back silently to the main
        frame when an explicit criterion is given.

        Raises FrameTimeoutError if no matching frame appears within
        timeout_ms. Raises FrameDetectionError for any other Playwright
        failure during the wait.
        """
        raise NotImplementedError

    @abstractmethod
    def select_frame(self, page: Any, descriptor: FrameDescriptor) -> Any:
        """Return the opaque frame handle matching descriptor.

        Raises FrameNotFoundError if the described frame is no longer
        present (SAD 18.6 - "frame removido dinamicamente"). Raises
        FrameAccessError if reading frame properties or the frame list
        fails due to a Playwright infrastructure error.
        """
        raise NotImplementedError
