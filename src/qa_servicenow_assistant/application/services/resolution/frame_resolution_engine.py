"""Frame Resolution Engine (SAD Cap. 18).

Orchestrates: detect available frames (FrameDetectorPort), resolve the
target one (FrameResolver domain service), select its live handle
(FrameDetectorPort) and log the outcome (SAD 18.2 - "registrar erros
relacionados a resolucao de frames").

Unlike SelectorResolutionEngine/PageRecognitionEngine/NavigationEngine,
this engine logs and RE-RAISES on failure instead of returning a
"not resolved" result - SAD 18.8 explicitly requires exception-based
failure propagation for Frame Resolver.
"""

from __future__ import annotations

from typing import Any

from qa_servicenow_assistant.application.ports.frame_detector_port import (
    FrameDetectorPort,
)
from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.domain.exceptions.frame import FrameError
from qa_servicenow_assistant.domain.services.frame_resolver import FrameResolver


class FrameResolutionEngine:
    """Resolves and returns the live frame handle matching the given
    criteria, raising on failure (SAD 18.8)."""

    def __init__(
        self,
        frame_detector: FrameDetectorPort,
        log_port: LogPort,
        resolver: FrameResolver | None = None,
    ) -> None:
        self._frame_detector = frame_detector
        self._log_port = log_port
        self._resolver = resolver or FrameResolver()

    def resolve(
        self,
        page: Any,
        *,
        frame_name: str | None = None,
        url_pattern: str | None = None,
    ) -> Any:
        available_frames = self._frame_detector.list_frames(page)

        try:
            descriptor = self._resolver.resolve(
                available_frames, frame_name=frame_name, url_pattern=url_pattern
            )
        except FrameError as error:
            self._log_port.error(
                "Frame resolution failed",
                frame_name=frame_name,
                url_pattern=url_pattern,
                available_frames=[frame.name or frame.url for frame in available_frames],
                error=str(error),
            )
            raise

        frame_handle = self._frame_detector.select_frame(page, descriptor)
        self._log_port.debug(
            "Frame resolved",
            frame_name=descriptor.name,
            url=descriptor.url,
            is_main_frame=descriptor.is_main_frame,
        )
        return frame_handle
