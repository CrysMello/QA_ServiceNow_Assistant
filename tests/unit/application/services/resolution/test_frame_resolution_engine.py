"""Unit tests for FrameResolutionEngine."""

from __future__ import annotations

from typing import Any

import pytest

from qa_servicenow_assistant.application.ports.frame_detector_port import (
    FrameDetectorPort,
)
from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.application.services.resolution.frame_resolution_engine import (
    FrameResolutionEngine,
)
from qa_servicenow_assistant.domain.exceptions.frame import FrameNotFoundError
from qa_servicenow_assistant.domain.value_objects.frame_descriptor import (
    FrameDescriptor,
)

_MAIN = FrameDescriptor(name="", url="https://dev.service-now.com/home", is_main_frame=True)
_CONTENT = FrameDescriptor(name="content_frame", url="https://dev.service-now.com/embed", is_main_frame=False)
_FAKE_PAGE = object()
_FAKE_FRAME_HANDLE = object()


class FakeFrameDetector(FrameDetectorPort):
    def __init__(self, frames: tuple[FrameDescriptor, ...]) -> None:
        self._frames = frames
        self.select_calls: list[FrameDescriptor] = []

    def list_frames(self, page: Any) -> tuple[FrameDescriptor, ...]:
        return self._frames

    def select_frame(self, page: Any, descriptor: FrameDescriptor) -> Any:
        self.select_calls.append(descriptor)
        return _FAKE_FRAME_HANDLE


class FakeLogPort(LogPort):
    def __init__(self) -> None:
        self.debug_calls: list[tuple[str, dict[str, Any]]] = []
        self.error_calls: list[tuple[str, dict[str, Any]]] = []

    def bind(self, **context: Any) -> "FakeLogPort":
        return self

    def trace(self, message: str, **context: Any) -> None:
        pass

    def debug(self, message: str, **context: Any) -> None:
        self.debug_calls.append((message, context))

    def info(self, message: str, **context: Any) -> None:
        pass

    def warning(self, message: str, **context: Any) -> None:
        pass

    def error(self, message: str, **context: Any) -> None:
        self.error_calls.append((message, context))

    def critical(self, message: str, **context: Any) -> None:
        pass


def test_resolve_returns_selected_frame_handle_and_logs_debug() -> None:
    detector = FakeFrameDetector((_MAIN, _CONTENT))
    log_port = FakeLogPort()
    engine = FrameResolutionEngine(detector, log_port)

    handle = engine.resolve(_FAKE_PAGE, frame_name="content_frame")

    assert handle is _FAKE_FRAME_HANDLE
    assert detector.select_calls == [_CONTENT]
    assert len(log_port.debug_calls) == 1
    assert log_port.error_calls == []


def test_resolve_failure_logs_error_and_reraises() -> None:
    detector = FakeFrameDetector((_MAIN,))
    log_port = FakeLogPort()
    engine = FrameResolutionEngine(detector, log_port)

    with pytest.raises(FrameNotFoundError):
        engine.resolve(_FAKE_PAGE, frame_name="missing_frame")

    assert len(log_port.error_calls) == 1
    message, context = log_port.error_calls[0]
    assert message == "Frame resolution failed"
    assert context["frame_name"] == "missing_frame"
    assert detector.select_calls == []  # select_frame never called after resolution failure


def test_resolve_without_criteria_returns_main_frame() -> None:
    detector = FakeFrameDetector((_MAIN, _CONTENT))
    engine = FrameResolutionEngine(detector, FakeLogPort())

    engine.resolve(_FAKE_PAGE)

    assert detector.select_calls == [_MAIN]
