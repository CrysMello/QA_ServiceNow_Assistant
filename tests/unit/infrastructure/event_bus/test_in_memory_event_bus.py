"""Unit tests for InMemoryEventBus (ADR-0007, ADR-0012)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.domain.events.domain_event import DomainEvent
from qa_servicenow_assistant.infrastructure.event_bus.in_memory_event_bus import (
    InMemoryEventBus,
)


@dataclass(frozen=True)
class SampleEvent(DomainEvent):
    payload: str = ""


@dataclass(frozen=True)
class OtherEvent(DomainEvent):
    payload: str = ""


class FakeLogPort(LogPort):
    """Test double for LogPort recording every call for assertions."""

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


@pytest.fixture
def log_port() -> FakeLogPort:
    return FakeLogPort()


@pytest.fixture
def event_bus(log_port: FakeLogPort) -> InMemoryEventBus:
    return InMemoryEventBus(log_port)


def test_subscribed_handler_receives_published_event(event_bus: InMemoryEventBus) -> None:
    received: list[SampleEvent] = []
    event_bus.subscribe(SampleEvent, received.append)

    event = SampleEvent(payload="hello")
    event_bus.publish(event)

    assert received == [event]


def test_publish_without_subscribers_does_not_raise(event_bus: InMemoryEventBus) -> None:
    event_bus.publish(SampleEvent(payload="no one listening"))


def test_multiple_handlers_all_receive_the_event(event_bus: InMemoryEventBus) -> None:
    first_calls: list[SampleEvent] = []
    second_calls: list[SampleEvent] = []
    event_bus.subscribe(SampleEvent, first_calls.append)
    event_bus.subscribe(SampleEvent, second_calls.append)

    event = SampleEvent(payload="broadcast")
    event_bus.publish(event)

    assert first_calls == [event]
    assert second_calls == [event]


def test_handlers_are_isolated_by_exact_event_type(event_bus: InMemoryEventBus) -> None:
    sample_calls: list[DomainEvent] = []
    other_calls: list[DomainEvent] = []
    event_bus.subscribe(SampleEvent, sample_calls.append)
    event_bus.subscribe(OtherEvent, other_calls.append)

    event_bus.publish(SampleEvent(payload="only for sample"))

    assert len(sample_calls) == 1
    assert other_calls == []


def test_base_type_subscriber_does_not_receive_subclass_events(
    event_bus: InMemoryEventBus,
) -> None:
    """Exact-type matching is a documented design choice (see EventBusPort)."""
    base_calls: list[DomainEvent] = []
    event_bus.subscribe(DomainEvent, base_calls.append)

    event_bus.publish(SampleEvent(payload="subclass event"))

    assert base_calls == []


def test_unsubscribe_with_the_same_handler_reference_stops_delivery(
    event_bus: InMemoryEventBus,
) -> None:
    received: list[SampleEvent] = []

    def handler(event: SampleEvent) -> None:
        received.append(event)

    event_bus.subscribe(SampleEvent, handler)
    event_bus.unsubscribe(SampleEvent, handler)
    event_bus.publish(SampleEvent(payload="should not be received"))

    assert received == []


def test_unsubscribe_unknown_handler_does_not_raise(event_bus: InMemoryEventBus) -> None:
    def handler(event: SampleEvent) -> None:
        pass

    event_bus.unsubscribe(SampleEvent, handler)  # never subscribed


def test_handler_exception_is_isolated_and_logged(
    event_bus: InMemoryEventBus, log_port: FakeLogPort
) -> None:
    def failing_handler(event: SampleEvent) -> None:
        raise ValueError("boom")

    succeeded: list[SampleEvent] = []
    event_bus.subscribe(SampleEvent, failing_handler)
    event_bus.subscribe(SampleEvent, succeeded.append)

    event_bus.publish(SampleEvent(payload="triggers failure"))

    assert succeeded  # the second handler still ran despite the first failing
    assert len(log_port.error_calls) == 1
    message, context = log_port.error_calls[0]
    assert "exception" in message.lower()
    assert context["event_type"] == "SampleEvent"
    assert "boom" in context["error"]


def test_publish_logs_a_debug_summary(event_bus: InMemoryEventBus, log_port: FakeLogPort) -> None:
    event_bus.subscribe(SampleEvent, lambda event: None)

    event_bus.publish(SampleEvent(payload="tracked"))

    assert len(log_port.debug_calls) == 1
    message, context = log_port.debug_calls[0]
    assert context["event_type"] == "SampleEvent"
    assert context["subscriber_count"] == 1
