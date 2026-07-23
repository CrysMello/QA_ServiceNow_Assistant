"""Frame Resolution Engine (SAD Cap. 18).

Orchestrates: wait for a matching frame to become available
(FrameDetectorPort.wait_for_frame - condition-based, RNF-010), resolve
the target one among what's available (FrameResolver domain service),
obtain its live handle (FrameDetectorPort.select_frame) and log the
outcome (SAD 18.2 - "registrar erros relacionados a resolucao de
frames").

Unlike SelectorResolutionEngine/PageRecognitionEngine/NavigationEngine,
this engine logs and RE-RAISES on failure instead of returning a
"not resolved" result - SAD 18.8 explicitly requires exception-based
failure propagation for Frame Resolver. No retry is performed here; that
remains the Retry Engine's responsibility (a later prompt).
"""

from __future__ import annotations

from typing import Any

from qa_servicenow_assistant.application.ports.frame_detector_port import (
    FrameDetectorPort,
)
from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.domain.exceptions.frame import FrameError
from qa_servicenow_assistant.domain.services.frame_resolver import FrameResolver
from qa_servicenow_assistant.domain.value_objects.frame_descriptor import (
    FrameDescriptor,
)

_DEFAULT_TIMEOUT_MS = 5_000


class FrameResolutionEngine:
    """Resolves and returns the live frame handle matching the given
    criteria, waiting (condition-based) for it to appear and raising on
    failure (SAD 18.8)."""

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
        timeout_ms: int = _DEFAULT_TIMEOUT_MS,
    ) -> Any:
        available_frames = self._detect_frames(page, frame_name, url_pattern, timeout_ms)
        descriptor = self._select_descriptor(available_frames, frame_name, url_pattern)
        frame_handle = self._obtain_handle(page, descriptor)

        self._log_port.debug(
            "Frame resolved",
            frame_name=descriptor.name,
            url=descriptor.url,
            is_main_frame=descriptor.is_main_frame,
        )
        return frame_handle

    def _detect_frames(
        self, page: Any, frame_name: str | None, url_pattern: str | None, timeout_ms: int
    ) -> tuple[FrameDescriptor, ...]:
        try:
            return self._frame_detector.wait_for_frame(
                page, frame_name=frame_name, url_pattern=url_pattern, timeout_ms=timeout_ms
            )
        except FrameError as error:
            self._log_port.error(
                "Frame detection failed",
                operation="wait_for_frame",
                frame_name=frame_name,
                url_pattern=url_pattern,
                timeout_ms=timeout_ms,
                error_type=type(error).__name__,
                error=str(error),
            )
            raise

    def _select_descriptor(
        self,
        available_frames: tuple[FrameDescriptor, ...],
        frame_name: str | None,
        url_pattern: str | None,
    ) -> FrameDescriptor:
        try:
            return self._resolver.resolve(
                available_frames, frame_name=frame_name, url_pattern=url_pattern
            )
        except FrameError as error:
            self._log_port.error(
                "Frame resolution failed",
                operation="resolve",
                frame_name=frame_name,
                url_pattern=url_pattern,
                available_frames=[frame.name or frame.url for frame in available_frames],
                error_type=type(error).__name__,
                error=str(error),
            )
            raise

    def _obtain_handle(self, page: Any, descriptor: FrameDescriptor) -> Any:
        try:
            return self._frame_detector.select_frame(page, descriptor)
        except FrameError as error:
            self._log_port.error(
                "Frame handle access failed",
                operation="select_frame",
                frame_name=descriptor.name,
                url=descriptor.url,
                error_type=type(error).__name__,
                error=str(error),
            )
            raise
