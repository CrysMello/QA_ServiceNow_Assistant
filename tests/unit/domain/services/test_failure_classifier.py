"""Unit tests for FailureClassifier (SAD 19.2, 19.6)."""

from __future__ import annotations

from qa_servicenow_assistant.domain.exceptions.browser import (
    BrowserDataCollectionError,
    BrowserLaunchError,
    BrowserNotStartedError,
)
from qa_servicenow_assistant.domain.exceptions.frame import (
    AmbiguousFrameError,
    FrameAccessError,
    FrameDetectionError,
    FrameNotFoundError,
    FrameTimeoutError,
)
from qa_servicenow_assistant.domain.exceptions.navigation import (
    NavigationError,
    NavigationTimeoutError,
)
from qa_servicenow_assistant.domain.services.failure_classifier import (
    FailureClassifier,
)
from qa_servicenow_assistant.domain.value_objects.failure_classification import (
    FailureClassification,
)


def test_navigation_errors_are_transient() -> None:
    classifier = FailureClassifier()

    assert classifier.classify(NavigationError("x")) == FailureClassification.TRANSIENT
    assert classifier.classify(NavigationTimeoutError("x")) == FailureClassification.TRANSIENT


def test_browser_launch_and_collection_errors_are_transient() -> None:
    classifier = FailureClassifier()

    assert classifier.classify(BrowserLaunchError("x")) == FailureClassification.TRANSIENT
    assert classifier.classify(BrowserDataCollectionError("x")) == FailureClassification.TRANSIENT


def test_browser_not_started_is_permanent_despite_being_a_browser_error() -> None:
    classifier = FailureClassifier()

    assert classifier.classify(BrowserNotStartedError("x")) == FailureClassification.PERMANENT


def test_frame_errors_are_transient_by_default() -> None:
    classifier = FailureClassifier()

    assert classifier.classify(FrameNotFoundError("x")) == FailureClassification.TRANSIENT
    assert classifier.classify(FrameTimeoutError("x")) == FailureClassification.TRANSIENT
    assert classifier.classify(FrameDetectionError("x")) == FailureClassification.TRANSIENT
    assert classifier.classify(FrameAccessError("x")) == FailureClassification.TRANSIENT


def test_ambiguous_frame_error_is_permanent_despite_being_a_frame_error() -> None:
    classifier = FailureClassifier()

    assert classifier.classify(AmbiguousFrameError("x")) == FailureClassification.PERMANENT


def test_unknown_exception_type_defaults_to_permanent() -> None:
    classifier = FailureClassifier()

    assert classifier.classify(ValueError("unexpected")) == FailureClassification.PERMANENT
    assert classifier.classify(RuntimeError("unexpected")) == FailureClassification.PERMANENT


def test_register_adds_a_new_classification() -> None:
    classifier = FailureClassifier()

    class CustomError(Exception):
        pass

    assert classifier.classify(CustomError("x")) == FailureClassification.PERMANENT

    classifier.register(CustomError, FailureClassification.TRANSIENT)

    assert classifier.classify(CustomError("x")) == FailureClassification.TRANSIENT


def test_register_can_override_a_default_classification() -> None:
    classifier = FailureClassifier()

    classifier.register(NavigationError, FailureClassification.PERMANENT)

    assert classifier.classify(NavigationError("x")) == FailureClassification.PERMANENT
