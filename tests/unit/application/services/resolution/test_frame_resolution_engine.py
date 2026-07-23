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
from qa_servicenow_assistant.domain.exceptions.frame import (
    FrameNotFoundError,
    FrameTimeoutError,
)
from qa_servicenow_assistant.domain.value_objects.frame_descriptor import (
    FrameDescriptor,
)

_MAIN = FrameDescriptor(name="", url="https://dev.service-now.com/home", is_main_frame=True)
_CONTENT = FrameDescriptor(name="content_frame", url="https://dev.service-now.com/embed", is_main_frame=False)
_FAKE_PAGE = object()
_FAKE_FRAME_HANDLE = object()


class FakeFrameDetector(FrameDetectorPort):
    def __init__(
        self,
        frames: tuple[FrameDescriptor, ...],
        wait_error: Exception | None = None,
    ) -> None:
        self._frames = frames
        self._wait_error = wait_error
        self.select_calls: list[FrameDescriptor] = []
        self.wait_calls: list[dict[str, Any]] = []

    def list_frames(self, page: Any) -> tuple[FrameDescriptor, ...]:
        return self._frames

    def wait_for_frame(
        self,
        page: Any,
        *,
        frame_name: str | None = None,
        url_pattern: str | None = None,
        timeout_ms: int,
    ) -> tuple[FrameDescriptor, ...]:
        self.wait_calls.append(
            {"frame_name": frame_name, "url_pattern": url_pattern, "timeout_ms": timeout_ms}
        )
        if self._wait_error is not None:
            raise self._wait_error
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


def test_resolve_uses_wait_for_frame_and_logs_debug_on_success() -> None:
    detector = FakeFrameDetector((_MAIN, _CONTENT))
    log_port = FakeLogPort()
    engine = FrameResolutionEngine(detector, log_port)

    handle = engine.resolve(_FAKE_PAGE, frame_name="content_frame", timeout_ms=2_000)

    assert handle is _FAKE_FRAME_HANDLE
    assert detector.wait_calls == [
        {"frame_name": "content_frame", "url_pattern": None, "timeout_ms": 2_000}
    ]
    assert detector.select_calls == [_CONTENT]
    assert len(log_port.debug_calls) == 1
    assert log_port.error_calls == []


def test_resolve_uses_default_timeout_when_not_specified() -> None:
    detector = FakeFrameDetector((_MAIN,))
    engine = FrameResolutionEngine(detector, FakeLogPort())

    engine.resolve(_FAKE_PAGE)

    assert detector.wait_calls[0]["timeout_ms"] > 0  # a sane positive default is used


def test_detection_failure_logs_error_with_diagnostics_and_reraises() -> None:
    detector = FakeFrameDetector((), wait_error=FrameTimeoutError("Timed out after 1000ms"))
    log_port = FakeLogPort()
    engine = FrameResolutionEngine(detector, log_port)

    with pytest.raises(FrameTimeoutError):
        engine.resolve(_FAKE_PAGE, frame_name="missing_frame", timeout_ms=1_000)

    assert len(log_port.error_calls) == 1
    message, context = log_port.error_calls[0]
    assert message == "Frame detection failed"
    assert context["operation"] == "wait_for_frame"
    assert context["frame_name"] == "missing_frame"
    assert context["timeout_ms"] == 1_000
    assert context["error_type"] == "FrameTimeoutError"
    assert detector.select_calls == []  # select_frame never reached


def test_resolution_failure_after_successful_detection_logs_and_reraises() -> None:
    # two frames sharing the same name -> AmbiguousFrameError from the pure resolver,
    # even though wait_for_frame itself succeeded.
    duplicate = FrameDescriptor(name="content_frame", url="https://dev.service-now.com/embed2", is_main_frame=False)
    detector = FakeFrameDetector((_MAIN, _CONTENT, duplicate))
    log_port = FakeLogPort()
    engine = FrameResolutionEngine(detector, log_port)

    from qa_servicenow_assistant.domain.exceptions.frame import AmbiguousFrameError

    with pytest.raises(AmbiguousFrameError):
        engine.resolve(_FAKE_PAGE, frame_name="content_frame")

    assert len(log_port.error_calls) == 1
    message, context = log_port.error_calls[0]
    assert message == "Frame resolution failed"
    assert context["operation"] == "resolve"
    assert context["error_type"] == "AmbiguousFrameError"
    assert detector.select_calls == []  # select_frame never reached


def test_access_failure_after_successful_resolution_logs_and_reraises() -> None:
    class VanishingFrameDetector(FakeFrameDetector):
        def select_frame(self, page: Any, descriptor: FrameDescriptor) -> Any:
            raise FrameNotFoundError("Frame vanished before handle could be obtained")

    detector = VanishingFrameDetector((_MAIN, _CONTENT))
    log_port = FakeLogPort()
    engine = FrameResolutionEngine(detector, log_port)

    with pytest.raises(FrameNotFoundError):
        engine.resolve(_FAKE_PAGE, frame_name="content_frame")

    assert len(log_port.error_calls) == 1
    message, context = log_port.error_calls[0]
    assert message == "Frame handle access failed"
    assert context["operation"] == "select_frame"


def test_resolve_without_criteria_returns_main_frame() -> None:
    detector = FakeFrameDetector((_MAIN, _CONTENT))
    engine = FrameResolutionEngine(detector, FakeLogPort())

    engine.resolve(_FAKE_PAGE)

    assert detector.select_calls == [_MAIN]
