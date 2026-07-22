"""Unit tests for DomainEvent (base type for the Event Bus)."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass
from datetime import datetime, timezone

import pytest

from qa_servicenow_assistant.domain.events.domain_event import DomainEvent


def test_occurred_at_is_set_automatically() -> None:
    before = datetime.now(timezone.utc)

    event = DomainEvent()

    after = datetime.now(timezone.utc)
    assert before <= event.occurred_at <= after


def test_domain_event_is_immutable() -> None:
    event = DomainEvent()

    with pytest.raises(FrozenInstanceError):
        event.occurred_at = datetime.now(timezone.utc)  # type: ignore[misc]


def test_subclasses_can_add_their_own_fields() -> None:
    @dataclass(frozen=True)
    class SampleEvent(DomainEvent):
        payload: str = ""

    event = SampleEvent(payload="hello")

    assert event.payload == "hello"
    assert isinstance(event.occurred_at, datetime)
